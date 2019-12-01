import readData as rd
import glob
import gdal
import numpy as np

for myd09 in glob.glob("MYD09_Project/2019*_Project_Clipped.tif"):
    reference = gdal.Open('MYD02/TOA_300.tif')
    sur_ref = gdal.Open(myd09)
    path = myd09.split('/')[1]
    rd.alignRaster(reference, sur_ref, 'MYD09_Project/A{}'.format(path))