import numpy as np
from os.path import join
import matplotlib.pyplot as plt
import pandas as pd
import sys
from utils import get_color_map_norm, read_band, mahalanobisR, plot_csv, band_size
import importlib

if len(sys.argv) != 2:
    print('Usage: python3 ' + sys.argv[0].lower() + ' location') 
    exit()
location = sys.argv[1].lower()
paths = importlib.import_module(location + '.paths')
config = importlib.import_module(location + '.config')

if __name__ == '__main__':

    product_directory = paths.product_directory
    #In order to show the images, we need an ordered dataset
    band_size = band_size()
    chunk_images = config.chunk_images_plot
    df_chunks = pd.read_csv(paths.csv_band, sep = ';', chunksize=band_size*chunk_images)

    cmap, norm = get_color_map_norm()

    for original_chunk in df_chunks:
        outliers = mahalanobisR(original_chunk)
        outliers_map = original_chunk.iloc[:,-1].values.copy()
        outliers_map[outliers] = 'outlier'
        
        for i in range(chunk_images):
            product = str(original_chunk.iloc[i*band_size,0])
            fig = plt.figure()
            plt.suptitle(product)
            original_plot = plot_csv(original_chunk.iloc[i*band_size:(i+1)*band_size,-1])
            sub1 = fig.add_subplot(2, 2, 1)
            sub1.imshow(original_plot,cmap=cmap, norm=norm)
            sub1.set_title("Original")
            outliers_plot = plot_csv(outliers_map[i*band_size:(i+1)*band_size])
            sub2 = fig.add_subplot(2, 2, 2)
            sub2.imshow(outliers_plot,cmap=cmap, norm=norm)
            sub2.set_title("Outliers detected")

            tci_path = join(product_directory,product,product+"_TCI.jp2")
            tci = read_band(tci_path)

            sub3 = fig.add_subplot(2, 2, 3)
            sub3.imshow(tci)
            sub3.set_title("True color image")

            clouds_plot = np.where(original_plot==7,1,0)
            sub4 = fig.add_subplot(2, 2, 4)
            sub4.imshow(clouds_plot)
            sub4.set_title("Clouds " + str(np.count_nonzero(clouds_plot) * 100 / band_size) + "%")

            plt.gcf().set_size_inches(22, 18)
            plt.show()