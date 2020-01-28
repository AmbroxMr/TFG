import sys
import pandas as pd
from utils import band_size
import warnings
from sklearn.preprocessing import LabelEncoder
import joblib
from os import  mkdir
from os.path import exists
import importlib

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

if __name__ == '__main__':

    if not(exists(paths.classifier_directory)):
        mkdir(paths.classifier_directory)

    warnings.simplefilter('ignore')
    RANDOM_SEED = 42
    n_images_chunk = config.chunk_images_train

    dic_datasets = {paths.csv_band_no_outliers:paths.classifier_band,
                    paths.csv_index_no_outliers:paths.classifier_index}

    sclf = config.classifier

    le = LabelEncoder()
    classes = [class_properties["name"] for _,class_properties in config.classes.items()]
    le.fit(classes)

    chunk_size = band_size()*n_images_chunk
    print('Training classifier..., chunksize = ' + str(chunk_size) + ' rows')
    counter = 0
    for (path_dataset, filename) in dic_datasets.items():
        chunks_dataset_no_outliers = pd.read_csv(path_dataset, sep = ';', chunksize=chunk_size)
        for chunk in chunks_dataset_no_outliers:
            chunk.sample(frac=1).head(int(len(chunk)*config.data_train_porcentage/100)) #Using random % of data 
            data = chunk.iloc[:,3:-1].values
            target = chunk.iloc[:,-1].values
            target = le.transform(target)
            sclf.fit(data, target)
            counter = counter + 1
            print(str(counter) + ' dataset chunks fitted')
        joblib.dump(sclf, filename)



