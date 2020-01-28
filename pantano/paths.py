from os.path import join, dirname, realpath, split

location = 'pantano'

#Paths you should modify
product_directory = '/home/pealma/Satellite/Sentinel2/2A/pantano/PRODUCT/result/' #Directory that contains `prepare_product.sh` output
output_directory = '/home/anmabur/fotos_tmp_' + location #Directory where output will be generated

#Paths you shouldn't modify
working_directory = split(dirname(realpath(__file__)))[0]
location_directory = join(working_directory,location)
geojson_directory = join(location_directory,'geojson/')
dataset_directory = join(location_directory,'dataset/')
dataset_outliers_free_directory = join(dataset_directory,'outliers-free/')
qgis_directory = join(location_directory,'QGIS/')
classifier_directory = join(location_directory,'classifier/')
tmp = join(location_directory,'tmp/')

script_qgis = join(qgis_directory,'automatic_classification.txt')
csv_band = join(dataset_directory,'band2A.csv')
csv_index = join(dataset_directory,'index2A.csv')
csv_band_no_outliers = join(dataset_outliers_free_directory,'band2A.csv')
csv_index_no_outliers = join(dataset_outliers_free_directory,'index2A.csv')
output_classification_csv = join(output_directory,'final_classification.csv')
output_area_csv = join(output_directory,'data_area.csv')
classifier_band = join(classifier_directory,'classifier_band.sav')
classifier_index = join(classifier_directory,'classifier_index.sav')

#Modify only if a new location is being added (explained in README)
main_geojson = join(location_directory,'geojson/pantano.geojson') #Path to your main-shape geoJSON
rectangle_geojson = main_geojson #If main_geojson is a rectangle, this is equal to main_geojson. If not, this is the rectangle-shape geoJSON
slices20 = [None,None,None,None] #This necessary if you get shape error. It means that 20-m spatial resolution bands will be cropped in order to match with 10-m spatial resolution bands. If not neccesary, use [None,None,None,None]
slices60 = [None,None,1,-1] #Similar to slices20, but for 60-m spatial resolution bands.
qgis_coordinates_rectangle = ['374460.019','4129799.97','398179.635','4117880.50'] #This will be used by generate_script_GQIS.py for generating pre-classification images. Top-left and bottom-right coordinates of a rectangle that covers at least  rectangle_geojson area in EPSG:32630 coordinate system.  
