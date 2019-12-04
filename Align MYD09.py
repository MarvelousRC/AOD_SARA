import readData2 as rd2
import glob
import gdal
import numpy as np

ref_raster = rd2.ref_raster


def alignRaster(base, to_trans, dest_path):
    """
    base and to_trans should both be GDAL objects
    """
    base_proj = base.GetProjection()
    base_geotrans = base.GetGeoTransform()
    height = base.RasterYSize
    width = base.RasterXSize

    dst = gdal.GetDriverByName('GTiff').Create(dest_path, width, height, 1, gdal.GDT_Float32)
    dst.SetGeoTransform(base_geotrans)
    dst.SetProjection(base_proj)

    gdal.ReprojectImage(to_trans, dst, to_trans.GetProjection(), base_proj, gdal.GRA_Bilinear)

    del dst

    return dest_path


for myd09 in glob.glob("MYD09_Project/2019*_Project_Clipped.tif"):
    # sur_ref = gdal.Open(myd09).ReadAsArray()*0.0001
    sur_ref = gdal.Open(myd09)
    path = myd09.split('/')[1]
    # rd2.matrix_to_geo_tiff('MYD09_Project/A{}'.format(path), sur_ref)
    aligned_path = alignRaster(ref_raster, sur_ref, 'MYD09_Project/A(10000){}'.format(path))
    sur_ref = gdal.Open(aligned_path).ReadAsArray() * 0.0001
    rd2.matrix_to_geo_tiff('MYD09_Project/A{}'.format(path), sur_ref)

