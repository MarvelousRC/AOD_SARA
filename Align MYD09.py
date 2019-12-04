import readData2 as rd2
import glob
import gdal
import numpy as np

for myd09 in glob.glob("MYD09_Project/2019*_Project_Clipped.tif"):
    sur_ref = gdal.Open(myd09).ReadAsArray()*0.0001
    path = myd09.split('/')[1]
    rd2.matrix_to_geo_tiff('MYD09_Project/A{}'.format(path), sur_ref)