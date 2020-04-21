#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /path/to/products/"
    exit 1
fi

for filename in $1/*.zip; do
    unzip -qq $filename -d $1/tmp
    date=$(basename $filename |  cut -f 3 -d _ | cut -f 1 -d T)
    mkdir -p $1/$date

    # Create cropped and reflectance folders
    mkdir -p $1/$date/cropped $1/$date/rt

    # Extract bands that are going to be used
    
    ##10m spatial resolution
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R10m/*B02* $1/$date/$date\_B02.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R10m/*B03* $1/$date/$date\_B03.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R10m/*B04* $1/$date/$date\_B04.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R10m/*B08* $1/$date/$date\_B08.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R10m/*TCI* $1/$date/$date\_TCI.jp2

    ##20m spatial resolution
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B05* $1/$date/$date\_B05.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B06* $1/$date/$date\_B06.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B07* $1/$date/$date\_B07.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B8A* $1/$date/$date\_B8A.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B11* $1/$date/$date\_B11.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R20m/*B12* $1/$date/$date\_B12.jp2

    ##60m spatial resolution
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R60m/*B01* $1/$date/$date\_B01.jp2
    mv $1/tmp/*/GRANULE/*/IMG_DATA/R60m/*B09* $1/$date/$date\_B09.jp2

    #  Extract cloud mask
    mv $1/tmp/*/GRANULE/*/QI_DATA/MSK_CLDPRB_20m.jp2 $1/$date/$date\_CLD.jp2

    # Extract metadata file
    mv $1/tmp/*/MTD_MSIL* $1/$date/$date\_MTD_MSIL.xml
    rm -rf $1/tmp $filename
done
