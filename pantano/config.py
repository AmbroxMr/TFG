from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB 
from sklearn.ensemble import RandomForestClassifier
from mlxtend.classifier import EnsembleVoteClassifier

#Multiprocessing
n_processes_generate_dataset = 10 #generate_dataset_multiprocessing.py n_process

chunk_images_outliers = 10 #n_images that will be loaded as a chunk in detect_outliers_dataset.py, 
                           # a high value causes high use of ram, but better results detecting outliers 
                           
n_processes_outliers = 3 #detect_outliers_dataset.py n_process


#Minimum probability for clouds to stay in cloud mask (%)
cld_prob = 30


#Plotting
chunk_images_plot = 5 #outliers_plot.py n_images that will be shown in a row
nadata_color = 'black'
outlier_color = 'white'


#Training
chunk_images_train = 5 #size of a chunk in images, a high value causes high use of ram
data_train_porcentage = 70 #percentage of data that will be used for training


#Prediction
n_process_prediction = 2 #prediction.py n_process


#Classifier used
clf1 = KNeighborsClassifier(n_neighbors=4, n_jobs=20)
clf2 = RandomForestClassifier(random_state=1, n_jobs=20, n_estimators=100)
clf3 = GaussianNB()
classifier = EnsembleVoteClassifier(clfs=[clf1, clf2, clf3])


#Classification classes and given values, modify this only if you made your own pre-classification in QGIS (QGIS output)

##Percentil of class that is inlier (mahalanobis).
##100 means that there is no outliers in that class, 0 excludes that class in classification. 
##Intermediate values means the percentage of outliers in each class, using mahalanobis' distance.
##i.e. built_percentile = 70 means that 30% of that class will be detected as outlier.

classes = { 
    0:{"name":"unclassified","color":"red","percentile":0},
    3:{"name":"vegetation","color":"green","percentile":50},
    2:{"name":"bare_soil","color":"yellow","percentile":50},
    1:{"name":"water","color":"blue","percentile":50},
    4:{"name":"built","color":"purple","percentile":50},
          }

##Cloud is a reserved class, don't modify
classes[-1] = {"name":"cloud","color":"gray","percentile":0}