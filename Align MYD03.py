import readData as rd
import glob
import gdal
import numpy as np
from operator import and_
from operator import or_

MYD02HKM = rd.read_MYD02(4)

for MYD02 in MYD02HKM:
    year = MYD02['year']
    dofy = MYD02['dofy']
    hour = MYD02['hour']
    minute = MYD02['minute']
    sensorAzimuth, senAzFile = rd.read_MYD03(year, dofy, hour, minute, 'SensorAzimuth')
    sensorZenith, senZnFile = rd.read_MYD03(year, dofy, hour, minute, 'SensorZenith')
    solarAzimuth, solAzFile = rd.read_MYD03(year, dofy, hour, minute, 'SolarAzimuth')
    solarZenith, solZnFile = rd.read_MYD03(year, dofy, hour, minute, 'SolarZenith')

    if sensorAzimuth is None or sensorZenith is None or solarAzimuth is None or solarZenith is None:
        continue

    rd.alignRaster(MYD02['data'], sensorAzimuth,
                   'MYD03/MYD03_SensorAzimuth/{:04d}{:03d}{:02d}{:02d}.tif'
                   .format(year, dofy, hour, minute))
    rd.alignRaster(MYD02['data'], sensorZenith,
                   'MYD03/MYD03_SensorZenith/{:04d}{:03d}{:02d}{:02d}.tif'
                   .format(year, dofy, hour, minute))
    rd.alignRaster(MYD02['data'], solarAzimuth,
                   'MYD03/MYD03_SolarAzimuth/{:04d}{:03d}{:02d}{:02d}.tif'
                   .format(year, dofy, hour, minute))
    rd.alignRaster(MYD02['data'], solarZenith,
                   'MYD03/MYD03_SolarZenith/{:04d}{:03d}{:02d}{:02d}.tif'
                   .format(year, dofy, hour, minute))

MYD02HKM = rd.read_MYD02(4, 1)


for MYD02 in MYD02HKM:
    year = MYD02['year']
    dofy = MYD02['dofy']
    hour = MYD02['hour']
    minute = MYD02['minute']
    field_name_list = ['SensorAzimuth', 'SensorZenith', 'SolarAzimuth', 'SolarZenith']
    for field_name in field_name_list:
        file_list = \
            glob.glob(
                "MYD03/MYD03_{}/{:04d}{:03d}*.tif".format(field_name, year, dofy))
        if len(file_list) == 2:
            array0 = gdal.Open(file_list[0]).ReadAsArray()
            # array0 = np.ma.masked_where(array0 > -30000, array0)
            mask0 = (array0 > -20000)
            array1 = gdal.Open(file_list[1]).ReadAsArray()
            # array1 = np.ma.masked_where(array1 > -30000, array1)
            # mosaic = (array0 + array1)/2
            # mosaic = np.ma.array(array0.data + array1.data, mask=list(map(or_, array0.mask, array1.mask)))
            mask1 = (array1 > -20000)
            mosaic = array0 * mask0 + array1 * mask1 - ((mask0*1 + mask1*1) == 2) * (array0 + array1) / 2
            # rd.alignRaster(MYD02['data'], mosaic,
            #                'MYD03/MYD03_{}/{:04d}{:03d}{:02d}{:02d}_mosaic.tif'
            #                .format(field_name, year, dofy, hour, minute), scale_factor=0.01)
        else:
            mosaic = gdal.Open(file_list[0]).ReadAsArray()
            # rd.alignRaster(MYD02['data'], mosaic,
            #                'MYD03/MYD03_{}/{:04d}{:03d}{:02d}{:02d}.tif'
            #                .format(field_name, year, dofy, hour, minute), scale_factor=0.01)
        mosaic = mosaic * 0.01
        mosaic = np.ma.masked_where(mosaic > 200, mosaic)
        cols = mosaic.shape[0]
        rows = mosaic.shape[1]
        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create('MYD03/MYD03_{}/{:04d}{:03d}{:02d}{:02d}_mosaic.tif'
                                  .format(field_name, year, dofy, hour, minute),
                                  rows, cols, 1, gdal.GDT_Float32)
        outBand = outRaster.GetRasterBand(1)
        outBand.WriteArray(mosaic)
        outRaster.SetGeoTransform(MYD02['data'].GetGeoTransform())
        outRaster.SetProjection(MYD02['data'].GetProjection())
        outRaster.FlushCache()


del MYD02HKM


