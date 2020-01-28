# Product downloading and preparing
There are many ways for downloading products, I used [this one](https://scihub.copernicus.eu/twiki/do/view/SciHubUserGuide/BatchScripting#dhusget_script)

Teatinos example: `./dhusget.sh -T S2MSI2A -o product -u <user> -p <password> -c -4.565015623289649,36.67363863337091:-4.324076496929096,36.78092223486466 -l <n_products>`

Pantano example: `./dhusget.sh -T S2MSI2A -o product -u <user> -p <password> -c -4.298420941807371,37.247079674117586:-4.283083381680252,37.26017567959012 -l <n_products>`

After downloading some products, you need to prepare them as program input.

1. Move all of them to an empty folder.
2. Use `prepare_products.sh path/to/products/`.
3. Modify `location/paths.py` paths.


# Pre-classification using QGIS

We need to pre-classify all products, I use QGIS for that.

1. Install QGIS and SCP plugin, you can follow [this tutorial](https://semiautomaticclassificationmanual.readthedocs.io/en/master/installation_ubuntu.html).
2. Execute `generate_script_QGIS.py`, that generates `location/QGIS/automatic_classification.txt`.
3. Open [training window in QGIS](https://semiautomaticclassificationmanual.readthedocs.io/en/master/scp_dock.html#training-input) and import `location/QGIS/clas.scp`, then check all class boxes.
4. Open [batch in QGIS](https://semiautomaticclassificationmanual.readthedocs.io/en/master/main_interface_window.html#batch) and import `automatic_classification.txt`.
5. Run.

# Execution

You can modify input arguments at `/location/config.py` 

``` bash
#either teatinos or pantano are avaiable
location=teatinos
python3 -W ignore generate_dataset_multiprocessing.py $location && python3 detect_outliers_dataset.py $location && python3 classifier.py $location && python3 prediction.py $location
```

# Add new location

For those who want to make an advanced use of the program, it is possible to add new locations. Currently, Sentinel-2 provide coverage over [these areas](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/revisit-coverage). This process is similar to explained above, but familiarity with [geoJSON](https://geojson.org/) and geographic coordinate systems is needed.

Now, create the location folder:
``` bash
location=example
mkdir -p $location/QGIS $location/geojson
cp pantano/paths.py $location
cp pantano/config.py $location
cp pantano/QGIS/clas.scp $location/QGIS
```

It is needed the polygon of the area that you want to classify in geoJSON format. [This page](http://geojson.io) allows interactive creation of geoJSONs, if your shape is not a rectangle, you need another geoJSON representing a rectangle that covers your first shape (this is necessary due to bands' different spatial resolution, in order to avoid data loss). Save them in `$location/geojson/`.

Finally, modify `$location/paths.py` parameters.

# Change classification classes

If you want other classes than default ones, you can change them using a different `location/QGIS/clas.scp`. [This tutorial](https://fromgistors.blogspot.com/2016/09/semi-automatic-classification-pluginv5.html?spref=yml) shows how to create a custom .scf file using QGIS.

Preclassification images have to be classified using that file. 
Finally, modify 'classes' dictionary in `location/config.py`.
