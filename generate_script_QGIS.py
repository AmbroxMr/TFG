from os import listdir
from os.path import join, exists
import sys
import importlib

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

if __name__ == '__main__':
    products = sorted(listdir(paths.product_directory))
    script_qgis = open(paths.script_qgis,'w+')
    for product in products:
        if not exists(join(paths.product_directory,product,'classification.tif')):
            full_product_path = join(paths.product_directory,product)
            script_qgis.write(
            """
!working_dir!;'º'
 
add_new_bandset;
select_bandset;band_set : 2

#Loads rasters into band set 2
create_bandset;raster_path_list : '!working_dir!/@B02.jp2, !working_dir!/@B03.jp2, !working_dir!/@B04.jp2 , !working_dir!/@B05.jp2 , !working_dir!/@B06.jp2 , !working_dir!/@B07.jp2 , !working_dir!/@B08.jp2 , !working_dir!/@B8A.jp2,  !working_dir!/@B11.jp2 , !working_dir!/@B12.jp2  ';center_wavelength : 'band';wavelength_unit : 1;multiplicative_factor : '1';additive_factor : '0'

!working_dir!;'º'

#Clips rasters
clip_multiple_rasters;band_set : 2;output_dir : '!working_dir!/cropped';use_vector : 0;vector_path : 'null';use_vector_field : 0;vector_field : 'null';ul_x : '^';ul_y : '€';lr_x : '·';lr_y : '¬';nodata_value : 0;output_name_prefix : 'clip'


remove_bandset;band_set : 2

!working_dir!;'º'

#Converts rasters to reflectance
sentinel2_conversion;input_dir : '!working_dir!/cropped/';mtd_safl1c_file_path : '!working_dir!/@MTD_MSIL.xml';apply_dos1 : 1;dos1_only_blue_green : 1;use_nodata : 0;nodata_value : 0;create_bandset : 0;output_dir : '!working_dir!/rt';band_set : 1


add_new_bandset;
select_bandset;band_set : 2

!working_dir!;'º'

create_bandset;raster_path_list : '!working_dir!/rt/RT_ clip_@B02.tif, !working_dir!/rt/RT_ clip_@B03.tif, !working_dir!/rt/RT_ clip_@B04.tif, !working_dir!/rt/RT_ clip_@B05.tif, !working_dir!/rt/RT_ clip_@B06.tif, !working_dir!/rt/RT_ clip_@B07.tif, !working_dir!/rt/RT_ clip_@B08.tif, !working_dir!/rt/RT_ clip_@B8A.tif, !working_dir!/rt/RT_ clip_@B11.tif, !working_dir!/rt/RT_ clip_@B12.tif,';center_wavelength : '0.49,0.56,0.665,0.705,0.74,0.783,0.842,0.865,1.61,2.19';wavelength_unit : 1;multiplicative_factor : '1';additive_factor : '0'
classification;band_set : 2;use_macroclass : 1;algorithm_name  : 'Spectral Angle Mapping';use_lcs : 1;use_lcs_algorithm : 1;use_lcs_only_overlap : 0;apply_mask : 0;mask_file_path : 'null';vector_output : 0;classification_report : 0;save_algorithm_files : 0;output_classification_path : '!working_dir!/classification.tif'

remove_bandset;band_set : 2

#############################################
""".replace('º',full_product_path).replace('@',product + '_').replace('^',paths.qgis_coordinates_rectangle[0]).replace('€',paths.qgis_coordinates_rectangle[1]).replace('·',paths.qgis_coordinates_rectangle[2]).replace('¬',paths.qgis_coordinates_rectangle[3]))