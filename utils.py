import numpy as np
import rasterio
from shapely.geometry import shape
from shapely.ops import transform
from rasterio import mask
import pyproj
import sys
from functools import partial
from sentinelsat.sentinel import read_geojson
from multiprocessing import Lock, Value
from tqdm import tqdm
from os.path import join
from scipy.spatial.distance import mahalanobis
import scipy as sp
import os
from matplotlib import colors
import importlib
from math import isnan

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

def project_shape(geom, scs = 'epsg:4326', dcs = 'epsg:32630'):
    """ Project a shape from a source coordinate system to another one.
    The source coordinate system can be obtain with `rasterio` as illustrated next:

    >>> import rasterio
    >>> print(rasterio.open('example.jp2').crs)

    This is useful when the geometry has its points in "normal" coordinate reference systems while the geoTiff/jp2 data
    is expressed in other coordinate system.

    :param geom: Geometry, e.g., [{'type': 'Polygon', 'coordinates': [[(1,2), (3,4), (5,6), (7,8), (9,10)]]}]
    :param scs: Source coordinate system.
    :param dcs: Destination coordinate system.
    """

    project = partial(
        pyproj.transform,
        pyproj.Proj(init=scs),
        pyproj.Proj(init=dcs))

    return transform(project, shape(geom))

def compute_cloud_percentage(cld):

    is_cloud = (cld >= config.cld_prob)
    cloud_percentage = np.count_nonzero(is_cloud) * 100 / band_size()
    return is_cloud, cloud_percentage


def read_band(filename, get_coordinates=False ):
    """ Crop the file `filename` with a polygon mask.
    Images with spatial resolution = 10m are cropped by real shape of chosen location.
    Images with spatial resolution = 20m or 60m cover a rectangle bigger than chosen location avoiding data loss. 
    Tranformed to reflectance dividing by 10000, only for Sentinel-2 bands.
    :param filename: Input filename (jp2, tif). 
    """

    if any(band in filename for band in ['B02', 'B03', 'B04', 'B08','classification','TCI']):
        spatial_resolution = 10
        geojson = paths.main_geojson
    elif any(band in filename for band in ['B01', 'B09']):
        spatial_resolution = 60
        geojson = paths.rectangle_geojson
    else:
        spatial_resolution = 20
        geojson = paths.rectangle_geojson

    footprint = read_geojson(geojson)

    # load the raster, mask it by the polygon and crop it
    with rasterio.open(filename) as src:
        shape = project_shape(footprint['features'][0]['geometry'], dcs=src.crs)
        out_image, out_transform = mask.mask(src, shapes=[shape], crop=True)

    if any(band in filename for band in ['CLD','classification']): 
        out_image = out_image[0,:,:]
    elif 'TCI' in filename:
        out_image = np.rollaxis(out_image,0,3)
    else:
        out_image = out_image[0,:,:]/10000

    out_image[np.isnan(out_image)|np.isinf(out_image)] = 0
    
    if spatial_resolution == 20:
        out_image = crop_aux(np.repeat(np.repeat(out_image, 2, axis=0), 2, axis=1),paths.slices20)
    elif spatial_resolution == 60:
        out_image = crop_aux(np.repeat(np.repeat(out_image, 6, axis=0), 6, axis=1),paths.slices60)

    if get_coordinates:
        out_image = (out_image, out_transform)

    return out_image

def crop_aux(image,slices):
    xmin = slices[0]
    xmax = slices[1]
    ymin = slices[2]
    ymax = slices[3]
    return image[xmin:xmax,ymin:ymax]

def count_products():
    return len(os.listdir(paths.product_directory))

def get_aux_band():
    product = os.listdir(paths.product_directory)[0]
    aux_band_path = join(paths.product_directory,product,"classification.tif")
    aux_band = read_band(aux_band_path)
    return aux_band, np.amin(aux_band)

def band_size():
    aux_band, nodata_value = get_aux_band()
    return np.count_nonzero(aux_band != nodata_value)

def mahalanobisR(df,progress_bar=True):
    [keys, classes] = zip(*[(key, class_properties["name"]) for key, class_properties in config.classes.items()])
    data = df.iloc[:,3:-1]
    IC = np.zeros((len(classes),data.shape[1],data.shape[1]))
    mean = np.zeros((len(classes),data.shape[1]))
    for i, class_name in enumerate(classes):
        if not((class_name == 'unclassified') or (class_name == 'cloud')):
            IC[i,:,:] = data[df.CLASS==class_name].cov().values
            IC[i,:,:] = sp.linalg.inv(IC[i,:,:])
            mean[i,:] = data[df.CLASS==class_name].mean().values
    m = np.zeros(df.shape[0])
    m_class = [[] for _ in range(len(classes))]
    if progress_bar:
        pb = tqdm(total=df.shape[0])
    for i in range(df.shape[0]):
        row_class = classes.index(df.iloc[i,-1])
        if (row_class == 'unclassified') or (row_class == 'cloud'):
            m[i] = 0
        else:
            m[i] = mahalanobis(data.values[i,:],mean[row_class,:],IC[row_class,:,:]) ** 2
            m_class[row_class].append(m[i])
        if progress_bar:
            pb.update()
    cutoffs = [np.nanpercentile(m_class[classes.index(class_)], config.classes[key]["percentile"]) for key, class_ in zip(keys, classes)]
    cutoffs = [0 if isnan(x) else x for x in cutoffs]
    outliers = [m[row]>=cutoffs[classes.index(df.iloc[row,-1])] for row in range(len(m))]
    return outliers

def get_color_map_norm():
    bounds=np.arange(-0.5,len(config.classes)+2.5,1)
    colors_list = [class_properties["color"] for _, class_properties in config.classes.items()]
    colors_list.insert(0,config.outlier_color)
    colors_list.insert(0,config.nadata_color)
    cmap = colors.ListedColormap(colors_list)
    norm = colors.BoundaryNorm(bounds, cmap.N)  
    return cmap, norm

def plot_csv(mapping, cloud_product=''):
    aux_band, nodata_value = get_aux_band()
    for i, key in enumerate(config.classes):
        mapping = np.where(mapping==config.classes[key]["name"],i+2,mapping)
    mapping = np.where(mapping=='outlier',1,mapping)
    counter = 0
    out = np.zeros(aux_band.shape)
    for c in range(aux_band.shape[1]):
        for r in range(aux_band.shape[0]):
            if((aux_band[r,c]!=nodata_value)):
                out[r,c] = mapping[counter]
                counter+=1
    if cloud_product != '':
        cld_path = join(paths.product_directory,cloud_product, cloud_product + "_CLD.jp2")
        CLD = read_band(cld_path)
        out = np.where((CLD>=30) & (aux_band > 0),7,out)
    return out

def add_clouds(class_vector,cloud_product):
    aux_band, nodata_value = get_aux_band()
    cld_path = join(paths.product_directory,cloud_product, cloud_product + "_CLD.jp2")
    CLD = read_band(cld_path)
    CLD = np.where(aux_band!=nodata_value,CLD,np.nan).flatten()
    CLD = CLD[~np.isnan(CLD)]
    class_vector = np.where(CLD>config.cld_prob,"cloud",class_vector)
    return class_vector
    

class Progress_bar():
    def __init__(self, length):
        self.__actual = Value('i',0)
        self.__progress_bar = tqdm(total=length)
        self.__lock = Lock()
        self.__length = length

    def update(self, n=1):
        with self.__lock:
            self.__actual.value += n
            self.__progress_bar.update(self.__actual.value)
            if self.__actual.value >= self.__length:
                self.__progress_bar.close()

class Counter(object):
    def __init__(self, initval=0):
        self.val = Value('i', initval)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    def value(self):
        with self.lock:
            return self.val.value
