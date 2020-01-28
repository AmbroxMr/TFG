import pandas as pd
from utils import mahalanobisR, count_products, Progress_bar, band_size
import sys
from os.path import exists, join
from os import mkdir, rmdir, remove, listdir
import shutil
import multiprocessing
import importlib

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')


def process(df_chunk,id_chunk,csv, semaphore, tmp, progress_bar, chunk_images):
    outliers = mahalanobisR(df_chunk, progress_bar = False)
    df_chunk = df_chunk.drop(df_chunk[outliers].index)
    df_chunk.to_csv(tmp + csv + '_' + str(id_chunk),index=False,sep=';',header= False)
    progress_bar.update(n=chunk_images)
    semaphore.release()


if __name__ == '__main__':
    
    if not(exists(paths.dataset_outliers_free_directory)):
        mkdir(paths.dataset_outliers_free_directory)

    csv_in_out = {
                paths.csv_index : paths.csv_index_no_outliers,
                paths.csv_band : paths.csv_band_no_outliers
                }

    chunk_images = config.chunk_images_outliers
    n_processes = config.n_processes_outliers
    tmp = paths.tmp
    if not(exists(tmp)):
        mkdir(tmp)
    job_list = []
    semaphore = multiprocessing.Semaphore(n_processes)

    print("Detecting outliers...")
    progress_bar = Progress_bar(length=(count_products()*len(csv_in_out.keys())))
    for (input_csv, output_csv) in csv_in_out.items():
        
        with open(input_csv,'rb') as infile:
            with open(output_csv,'wb') as outfile:
                outfile.write(infile.readline() + b'\n')

        df_chunks = pd.read_csv(input_csv, sep = ';', chunksize=band_size()*chunk_images)        
        for id_chunk,df in enumerate(df_chunks):
            if input_csv == paths.csv_index:
                csv_id = 'i'
            else:
                csv_id = 'b'
            job = multiprocessing.Process(target=process, args=(df,id_chunk,csv_id, semaphore, tmp, progress_bar,chunk_images))
            job_list.append(job)
            semaphore.acquire()
            job.start()
    for j in job_list:
        j.join()
    
    

    csv_index = open(paths.csv_index_no_outliers, 'wb+')
    csv_bands = open(paths.csv_band_no_outliers, 'wb+')
    tmp_files = sorted(listdir(tmp))
    for tmp_filename in tmp_files:
        tmp_path = join(tmp,tmp_filename)
        with open(tmp_path,'rb') as tmp_file:
            if tmp_filename[0] == 'i':
                shutil.copyfileobj(tmp_file, csv_index)
            else:
                shutil.copyfileobj(tmp_file, csv_bands)
        remove(tmp_path)
    rmdir(tmp)
    csv_index.close()
    csv_bands.close()
    