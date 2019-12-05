import numpy as np
import gdal
import pandas as pd
import glob
import math


def read_myd02(dofy):
    return gdal.Open('MYD02/TOA_{:03d}.tif'.format(dofy))


def read_myd02_cell(dofy, x, y):
    """
    :param dofy:
    :param x: Column number (not geo coords)
    :param y: Row number (not geo coord)
    :return:
    """
    return read_myd02(dofy).ReadAsArray()[x, y]


ref_raster = read_myd02(300)
(y_res, x_res) = np.shape(ref_raster.ReadAsArray())


def read_myd03(dofy):
    openfiles = {}
    field_name_list = ['SensorAzimuth', 'SensorZenith', 'SolarAzimuth', 'SolarZenith']
    for field in field_name_list:
        file_list = glob.glob('MYD03/MYD03_{}/2019{:03d}*_mosaic.tif'.format(field, dofy))
        openfiles[field] = gdal.Open(file_list[0])
    return openfiles


def read_myd09(dofy):
    return gdal.Open('MYD09_Project/A2019{}_Project_Clipped.tif'.format(dofy))


def read_mu_s(dofy):
    return gdal.Open('MYD03/µ_s_{:03d}.tif'.format(dofy))


def read_mu_v(dofy):
    return gdal.Open('MYD03/µ_v_{:03d}.tif'.format(dofy))


def read_P_a(dofy):
    return gdal.Open('Rayleigh_Reflectance/P_a_2019{:03d}.tif'.format(dofy))


def read_ray(dofy):
    return gdal.Open('Rayleigh_Reflectance/2019{:03d}.tif'.format(dofy))


def read_aod(dofy):
    return gdal.Open('AOD/AOD_2019_{:03d}.tif'.format(dofy)) 


def Rayleigh_Reflectance(dofy):
    myd03 = read_myd03(dofy)
    sensorAzimuth = to_radian(myd03['SensorAzimuth'].ReadAsArray())
    sensorZenith = to_radian(myd03['SensorZenith'].ReadAsArray())
    solarAzimuth = to_radian(myd03['SolarAzimuth'].ReadAsArray())
    solarZenith = to_radian(myd03['SolarZenith'].ReadAsArray())

    d2 = 2 * math.pi * dofy / 365
    d2 = 0.033 * math.cos(d2) + 1
    d2 = 1 / d2
    print("d^2 = ", d2)
    ESUN = 1850
    print('ESUN = ', ESUN)
    # µ_v = pd.DataFrame(np.cos(solarZenith.values / 180 * math.pi / 100))
    µ_s = np.cos(solarZenith)
    µ_v = np.cos(sensorZenith)

    # phi = sensorZenith - solarAzimuth - math.pi
    phi = sensorAzimuth - solarAzimuth - math.pi
    cos_phi = np.cos(phi)
    cos_Theta = -np.cos(solarZenith) * np.cos(sensorZenith) + np.sin(solarZenith) * np.sin(sensorZenith) * cos_phi
    P_R = 3 * 0.9587256 / (5 - 0.9587256) * (1 + cos_Theta * cos_Theta)
    matrix_to_geo_tiff('Rayleigh_Reflectance/P_a_2019{:03d}.tif'.format(dofy), P_R, ref_raster)
    wavelen = 0.550
    tau_r = 0.008569 * math.pow(wavelen, -4) * (1 + 0.0113 * math.pow(wavelen, -2) + 0.0013 * math.pow(wavelen, -4))
    # matrix_to_geo_tiff('Rayleigh_Reflectance/tau_R_2019{:03d}.tif'.format(dofy), tau_r, ref_raster)
    print("Rayleigh Optical Depth", tau_r)
    M = 1 / µ_v + 1 / µ_s
    rho_Ray = P_R * (1 - np.power(math.e, - M * tau_r)) / (4 * (µ_s + µ_v))
    matrix_to_geo_tiff('Rayleigh_Reflectance/2019{:03d}.tif'.format(dofy), rho_Ray, ref_raster)
    return rho_Ray


def matrix_to_geo_tiff(filepath, matrices, reference=ref_raster, gdal_type=gdal.GDT_Float32):
    # (y_res, x_res) = matrices.shape

    driver = gdal.GetDriverByName('GTiff')
    image = driver.Create(filepath, x_res, y_res, 1, gdal_type)
    image.SetGeoTransform(reference.GetGeoTransform())
    image.SetProjection(reference.GetProjection())
    band = image.GetRasterBand(1)
    band.WriteArray(matrices)
    image.FlushCache()
    return


def world2Pixel(x, y, geo_transform=ref_raster.GetGeoTransform()):
    """
    retrieve cell index based on the x and y coordinates
    """
    ul_x = geo_transform[0]
    ul_y = geo_transform[3]
    x_dist = geo_transform[1]
    y_dist = geo_transform[5]
    rtn_x = geo_transform[2]
    rtn_y = geo_transform[4]
    pixel = int((x - ul_x) / x_dist)
    line = -int((ul_y - y) / y_dist)
    return pixel, line


def to_radian(data):
    return data / 180 * math.pi / 100


def load(gdal_data):
    return gdal_data.ReadAsArray()
