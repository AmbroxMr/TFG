import numpy as np
from os import mkdir, rmdir, remove, listdir
from os.path import join, exists
from shapely.ops import transform
from functools import partial
import pyproj
import sys
from shapely.geometry import Point
import shutil
import multiprocessing as multiprocessing
from utils import get_aux_band, compute_cloud_percentage, read_band, Progress_bar
import importlib

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

def process(product,semaphore,progress_bar,tmp):

    green_path = join(product_directory,product,product + "_B03.jp2")
    GREEN = read_band(green_path)

    narrownir_path = join(product_directory,product,product + "_B8A.jp2")
    NARROWNIR = read_band(narrownir_path)

    coastal_path = join(product_directory,product,product + "_B01.jp2")
    COASTAL = read_band(coastal_path)

    blue_path = join(product_directory,product,product + "_B02.jp2")
    BLUE = read_band(blue_path)

    red_path = join(product_directory,product,product + "_B04.jp2")
    RED = read_band(red_path)

    rededge5_path = join(product_directory,product,product + "_B05.jp2")
    REDEDGE5 = read_band(rededge5_path)

    rededge6_path = join(product_directory,product,product + "_B06.jp2")
    REDEDGE6 = read_band(rededge6_path)

    rededge7_path = join(product_directory,product,product + "_B07.jp2")
    REDEDGE7 = read_band(rededge7_path)

    nir_path = join(product_directory,product,product + "_B08.jp2")
    NIR = read_band(nir_path)

    water_path = join(product_directory,product,product + "_B09.jp2")
    WATER = read_band(water_path)

    swir_path = join(product_directory,product,product + "_B11.jp2")
    SWIR = read_band(swir_path)

    swir12_path = join(product_directory,product,product + "_B12.jp2")
    SWIR12 = read_band(swir12_path)

    classification_path = join(product_directory,product,"classification.tif")
    CLASSIFICATION, coordinates = read_band(classification_path, get_coordinates=True)

    #Compute indexes
    ndvi = (NIR - RED) / (NIR + RED)
    slavi = (WATER/(REDEDGE5 + SWIR12))
    gvmi = (WATER+0.1 -(SWIR12+0.02))/(WATER + 0.1 + SWIR12 + 0.02)
    ndwi = (GREEN - NIR) / (GREEN + NIR)
    bsi = ((SWIR+RED)-(NIR + BLUE))/((SWIR+RED)+(NIR+BLUE))
    npcri = (RED - BLUE) / (RED + BLUE)
    
    for band in [ndvi,slavi,gvmi,ndwi,bsi,npcri]:
        band[np.isnan(band)|np.isinf(band)] = 0

    aux_band, nodata_value = get_aux_band()
    rows, columns = aux_band.shape

    project = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:32630'),
        pyproj.Proj(init='epsg:4326'))

    #Compute epsg:4326 coordinates of top-left and right-bottom pixels
    initial_long, initial_lat = transform(project, Point(coordinates * (0, 0))).bounds[0:2]
    final_long, final_lat = transform(project, Point(coordinates * (CLASSIFICATION.shape[1]-1, CLASSIFICATION.shape[0]-1))).bounds[0:2]
    pixel_lat = (final_lat-initial_lat)/rows
    pixel_long = (final_long-initial_long)/columns
    longitude = initial_long

    cld_path = join(product_directory,product, product + "_CLD.jp2")
    CLD = read_band(cld_path) 

    cloud_map, cloud_percentage = compute_cloud_percentage(CLD)

    csv_index = open(join(tmp,str(product)+'_ind.csv'), 'wb+')
    csv_bands = open(join(tmp,str(product)+'_ban.csv'), 'wb+')

    #For all pixels that are avaiable in any 10m image
    for c in range(columns):
        latitude = initial_lat
        for r in range(rows):
            if CLASSIFICATION[r,c] != nodata_value:
                if cloud_map[r,c] == 1:
                    class_pixel = 'cloud'
                else:
                    class_pixel = config.classes[CLASSIFICATION[r,c]]["name"]
                #Write CSV of bands and indexes
                csv_index.write(b'%s;%.10f;%.10f;%.6f;%.6f;%.6f;%.6f;%.6f;%.6f;%s\n' % (product.encode('UTF-8'),latitude,longitude,ndvi[r,c],slavi[r,c],gvmi[r,c],ndwi[r,c],bsi[r,c],npcri[r,c],class_pixel.encode('UTF-8')))
                csv_bands.write(b'%s;%.10f;%.10f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%.4f;%s\n' % (product.encode('UTF-8'),latitude,longitude,COASTAL[r,c],BLUE[r,c],GREEN[r,c],RED[r,c],REDEDGE5[r,c],REDEDGE6[r,c],REDEDGE7[r,c],NIR[r,c],NARROWNIR[r,c],WATER[r,c],SWIR[r,c],SWIR12[r,c],class_pixel.encode('UTF-8')))
            latitude += pixel_lat
        longitude += pixel_long
    progress_bar.update()

    semaphore.release()
    csv_index.close()
    csv_bands.close()

if __name__ == '__main__':

    print("Mapping products to csv...")

    n_processes = config.n_processes_generate_dataset
    product_directory = paths.product_directory
    tmp = paths.tmp
    if not(exists(tmp)):
        mkdir(tmp)
    if not(exists(paths.dataset_directory)):
        mkdir(paths.dataset_directory)

    products= listdir(product_directory)
    semaphore = multiprocessing.Semaphore(n_processes)
    progress_bar = Progress_bar(len(products))
    job_list = []
    for product in products:
        semaphore.acquire()
        job = multiprocessing.Process(target=process, args=(product,semaphore,progress_bar, tmp))
        job_list.append(job)
        job.start()
    for j in job_list:
        j.join()

    csv_index = open(paths.csv_index, 'wb+')
    csv_bands = open(paths.csv_band, 'wb+')
    csv_index.write(b'DATE;LONGITUDE;LATITUDE;NDVI;SLAVI;GVMI;NDWI;BSI;NPCRI;CLASS\n')
    csv_bands.write(b'DATE;LONGITUDE;LATITUDE;B01;B02;B03;B04;B05;B06;B07;B08;B8A;B09;B11;B12;CLASS\n')

    tmp_files = sorted(listdir(tmp))
    for tmp_file in tmp_files:
        tmp_path = join(tmp,tmp_file)
        with open(tmp_path,'rb') as tmp_file:
            if 'ind' in tmp_path:
                shutil.copyfileobj(tmp_file, csv_index)
            else:
                shutil.copyfileobj(tmp_file, csv_bands)
        remove(tmp_path)
    csv_index.close()
    csv_bands.close()
    rmdir(tmp)
