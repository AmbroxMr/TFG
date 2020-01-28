from os.path import join, exists
from os import  mkdir
import matplotlib.pyplot as plt
import sys
import pandas as pd
from utils import read_band, plot_csv, band_size, count_products
from sklearn.preprocessing import LabelEncoder
import joblib
from tqdm import tqdm
import numpy as np
from utils import add_clouds, get_color_map_norm, Progress_bar
import importlib
import multiprocessing

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

def process(product,semaphore,progress_bar, chunk_index, chunk_band, classifier_band, classifier_index, band_size):

    prediction_index = le.inverse_transform(classifier_index.predict(chunk_index.iloc[:,3:-1].values))
    prediction_band = le.inverse_transform(classifier_band.predict(chunk_band.iloc[:,3:-1].values))

    prediction_plot_index = plot_csv(prediction_index,cloud_product=product)
    prediction_plot_band = plot_csv(prediction_band,cloud_product=product)
    original_clas_plot = plot_csv(chunk_index.iloc[:,-1].values)

    fig = plt.figure()
    clouds_plot = np.where(original_clas_plot==7,1,0)
    cloud_percentage = np.count_nonzero(clouds_plot) * 100 / band_size
    plt.suptitle(product + ' (clouds: ' + str(cloud_percentage) + '%)')

    cmap, norm = get_color_map_norm()

    sub1 = fig.add_subplot(2, 2, 2)
    sub1.imshow(prediction_plot_band,cmap=cmap, norm=norm)
    sub1.set_title("Bands prediction")
    sub2 = fig.add_subplot(2, 2, 3)
    sub2.imshow(prediction_plot_index,cmap=cmap, norm=norm)
    sub2.set_title("Index prediction")

    tci_path = join(paths.product_directory,product,product + "_TCI.jp2")
    tci = read_band(tci_path)

    sub3 = fig.add_subplot(2, 2, 1)
    sub3.imshow(tci)
    sub3.set_title("True color image")

    sub4 = fig.add_subplot(2, 2, 4)
    sub4.imshow(original_clas_plot,cmap=cmap, norm=norm)
    sub4.set_title("Original QGIS classification")

    plt.gcf().set_size_inches(22, 18)
    plt.savefig(join(paths.output_directory , product + '.jpg'), dpi=600)
    plt.close('all')

    prediction_index = add_clouds(prediction_index,product)

    chunk_index =  chunk_index.assign(PREDICTED_CLASS=pd.Series(prediction_index).values)
    chunk_index[['DATE', 'LONGITUDE','LATITUDE','PREDICTED_CLASS']].to_csv(paths.output_classification_csv,header=None, sep =';', index = False, mode='a')

    waterarea = np.count_nonzero(prediction_index == 'water')/100
    with open(paths.output_area_csv, 'ab+') as area:
        area.write(b'%s;%.5f;%.2f\n' % (product.encode('UTF-8'),waterarea,cloud_percentage))

    progress_bar.update()
    semaphore.release()


if __name__ == '__main__':

    print("Generating predicted images...")

    out = paths.output_directory
    if not(exists(out)):
        mkdir(out)

    with open(paths.output_area_csv, 'wb+') as area:
        area.write(b'DATE;RESERVOIRAREA(ha);CLOUD(%)\n')

    with open(paths.output_classification_csv, 'w+') as data:
        data.write('DATE;LONGITUDE;LATITUDE;CLASS\n')
        
    le = LabelEncoder()
    classes = [class_properties["name"] for _,class_properties in config.classes.items()]
    le.fit(classes)

    band_size = band_size()

    chunks_index = pd.read_csv(paths.csv_index, sep = ';', chunksize=band_size)
    classifier_index = joblib.load(paths.classifier_index)

    chunks_band = pd.read_csv(paths.csv_band, sep = ';', chunksize=band_size)  
    classifier_band = joblib.load(paths.classifier_band)
    progress_bar = Progress_bar(length=count_products())

    job_list = []
    n_processes = config.n_process_prediction
    semaphore = multiprocessing.Semaphore(n_processes)


    for chunk_index, chunk_band in zip(chunks_index, chunks_band):

        product = str(chunk_index.iloc[0,0])

        semaphore.acquire()
        job = multiprocessing.Process(target=process, args=(product,semaphore,progress_bar, chunk_index, chunk_band, classifier_band, classifier_index, band_size))
        job_list.append(job)
        job.start()
    for j in job_list:
        j.join()