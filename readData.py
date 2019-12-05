"""
Last Modified: Nov 30th, 2019
This python file define the procedures where we input data.

Author: WEIYE CHEN
    GitHub: @MarvelousRC
    MS Student in Geography
    Department of Geography and Geographic Information Science
    University of Illinois at Urbana-Champaign
"""

import gdal
import pandas as pd
import matplotlib.pyplot as plt
import glob
from matplotlib.ticker import PercentFormatter
import numpy as np
import math
import cartopy.crs as ccrs
from pyhdf.SD import SD, SDC
import seaborn as sns


def read_MYD02(band=4, mode=0):
    def whatever():
        print(file)
        info = file.split('.')
        year = info[1][1:5]
        dayofyear = info[1][5:8]
        hour = info[2][0:2]
        minute = info[2][2:4]
        # collection = info[3]
        data_dict.append({
            'year': int(year),
            'dofy': int(dayofyear),
            'hour': int(hour),
            'minute': int(minute),
            # 'collection': collection,
            'data': gdal.Open(file, gdal.GA_ReadOnly)
        })

    data_dict = []
    if band < 2 or band > 6:
        return
    band = band - 2
    if mode == 0:
        for file in glob.glob("MYD02HKM/Selection/MYD02HKM*EV_500_RefSB_" + str(int(band)) + "-EV_500_RefSB.tif"):
            whatever()
        data_dict = sorted(data_dict, key=lambda i: (i['year'], i['dofy'], i['hour'], i['minute']))
        return data_dict
    elif mode == 1:
        for file in glob.glob("MYD02_Mosaic/MYD02HKM.A*.tif"):
            whatever()
        data_dict = sorted(data_dict, key=lambda i: (i['year'], i['dofy'], i['hour'], i['minute']))
        return data_dict


def read_MYD03(year, dofy, hour, minute, field_name):
    for file in glob.glob(
            "MYD03/MYD03.A{}{:03d}.{:02d}{:02d}*.{}-{}.tif".format(year, dofy, hour, minute, field_name, field_name)):
        print(file)
        if file != '':
            return gdal.Open(file, gdal.GA_ReadOnly), file
    return None, None


def read_MYD03_processed(year, dofy, hour, minute, field_name):
    for file in glob.glob(
            "MYD03/MYD03_{}/{:04d}{:03d}{:02d}{:02d}*.tif".format(year, dofy, hour, minute, field_name)):
        print(file)
        if file != '':
            return gdal.Open(file, gdal.GA_ReadOnly), file
    return


def read_MYD09(year, dofy):
    for file in glob.glob("MYD09GA/{:04d}{:03d}*.tif_clipped.tif".format(year, dofy)):
        if file != '':
            return gdal.Open(file, gdal.GA_ReadOnly), file


def alignRaster(base, to_trans, dest_path, scale_factor=1):
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


def read_parameters_from_MYD02_HDF():
    data_dict = []
    for file in glob.glob("MYD02HKM_hdf/*.hdf"):
        print(file)
        info = file.split('.')
        year = info[1][1:5]
        dayofyear = info[1][5:8]
        hour = info[2][0:2]
        minute = info[2][2:4]
        collection = info[3]
        hdf = SD(file, SDC.READ)
        EV_500_RefSB = hdf.select('EV_500_RefSB')
        EV_500_RefSB_attrs = EV_500_RefSB.attributes(full=1)
        reflectance_scales = EV_500_RefSB_attrs['reflectance_scales'][0]
        reflectance_offsets = EV_500_RefSB_attrs['reflectance_offsets'][0]
        radiance_scales = EV_500_RefSB_attrs['radiance_scales'][0]
        radiance_offsets = EV_500_RefSB_attrs['radiance_offsets'][0]
        units = EV_500_RefSB_attrs['reflectance_units'][0]
        data_dict.append({
            'year': int(year),
            'dofy': int(dayofyear),
            'hour': int(hour),
            'minute': int(minute),
            'collection': collection,
            'refScales': reflectance_scales,
            'refOffsets': reflectance_offsets,
            'radScales': radiance_scales,
            'radOffset': radiance_offsets,
            'units': units
        })
    data_dict = sorted(data_dict, key=lambda i: (i['year'], i['dofy'], i['hour'], i['minute']))
    return data_dict


def show_histogram(data, name='', masked=False):
    if masked:
        ravel = np.ma.masked_values(data, 0).ravel()
        ravel = np.ma.masked_where(ravel < 0, ravel)
    else:
        ravel = data.ravel()
    sns.distplot(ravel, bins=200, hist=True, kde=False, color='darkblue', kde_kws={'linewidth': 3}).set_title(name)


def show_descriptives(data):
    # print(pd.DataFrame(data.values.ravel()).describe())
    print(pd.DataFrame(data.ravel()).describe())


def search_data(data, year, dofy, h, m=None, collection=None, approximationMode=None):
    def criteria(element):
        if approximationMode is None:
            a = (element['year'] == year and element['dofy'] == dofy and element['hour'] == h)
            if m is not None:
                a = a and element['minute'] == m
            if collection is not None:
                a = a and element['collection'] == collection
            return a
        elif approximationMode == 1:
            return

    return [element for element in data if criteria(element)]


def matrix_to_geo_tiff(filepath, matrices, gdal_type=gdal.GDT_Float64, transform=None, projection=None, nodata=None):
    (y_res, x_res) = matrices.shape
    driver = gdal.GetDriverByName('GTiff')
    image = driver.Create(filepath, x_res, y_res, 1, gdal.GDT_Float32)
    if transform is not None:
        image.SetGeoTransform(transform)
    if projection is not None:
        image.SetProjection(projection)
    band = image.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(matrices)
    image.FlushCache()
    # del image
    return


def preprocess_MYD02(tif_array_dict, para_array_dict):
    """
    Use the returned dict array to replace the tif_array_dict
    """
    i = 0
    j = 0
    processed_dict = []
    while i < len(tif_array_dict) and j < len(para_array_dict):
        if tif_array_dict[i]['year'] < para_array_dict[j]['year']:
            i += 1
            continue
        elif tif_array_dict[i]['year'] > para_array_dict[j]['year']:
            j += 1
            continue
        if tif_array_dict[i]['dofy'] < para_array_dict[j]['dofy']:
            i += 1
            continue
        elif tif_array_dict[i]['dofy'] > para_array_dict[j]['dofy']:
            j += 1
            continue
        if tif_array_dict[i]['hour'] < para_array_dict[j]['hour']:
            i += 1
            continue
        elif tif_array_dict[i]['hour'] > para_array_dict[j]['hour']:
            j += 1
            continue
        if tif_array_dict[i]['minute'] < para_array_dict[j]['minute']:
            i += 1
            continue
        elif tif_array_dict[i]['minute'] > para_array_dict[j]['minute']:
            j += 1
            continue
        proj = tif_array_dict[i]['data'].GetProjection()
        geotrans = tif_array_dict[i]['data'].GetGeoTransform()
        data = tif_array_dict[i]['data'].ReadAsArray()
        data = para_array_dict[j]['refScales'] * (data - para_array_dict[j]['refOffsets'])
        data = np.ma.masked_where(data < 0, data, False)
        tif_array_dict[i]['data'] = data
        matrix_to_geo_tiff("MYD02/TOA_{}.tif".format(tif_array_dict[i]['dofy']), data, transform=geotrans, projection=proj)
        processed_dict.append(tif_array_dict[i])
        i += 1
        j += 1
    return processed_dict


def to_radian(data):
    return data / 180 * math.pi / 100


# a = gdal.Open('MYD02HKM_hdf.A2019299.mosaic.061.2019326204732.pssgmcrpgs_000501393006.EV_500_RefSB_1-EV_500_RefSB.tif').ReadAsArray()
# show_descriptives(a)
# a = 3.134991493425332e-05 * a
# show_descriptives(a)
# a = read_MYD02(4)

"""""""""""""""""""""""""""""""""""""""""""""
RETIRED FUNCTIONS
As of 20191122
"""""""""""""""""""""""""""""""""""""""""""""


def load_data(FILEPATH):
    ds = gdal.Open(FILEPATH)
    return ds


# Opens the data HDF file and returns as a dataframe
def read_dataset(SUBDATASET_NAME, FILEPATH):
    dataset = load_data(FILEPATH)
    path = ''
    for sub, description in dataset.GetSubDatasets():
        if description.endswith(SUBDATASET_NAME):
            path = sub
            break
    if path == '':
        print(SUBDATASET_NAME + ' not found')
        return
    subdataset = gdal.Open(path)
    subdataset = subdataset.ReadAsArray()
    # subdataset = pd.DataFrame(subdataset)
    return subdataset


def openSubDataset(data_list, num):
    if num >= len(data_list):
        print('The index is out of range.')
        return
    subdataset = gdal.Open(data_list[num][0])
    subdataset = subdataset.ReadAsArray()
    # subdataset = pd.DataFrame(subdataset)
    return subdataset


def get_subdatasets(data, subdataset_name):
    return


def read_data(data_type, LUT_mode=False):
    """"""
    pathName = data_type
    data_dict = []
    num = 0
    if LUT_mode:
        for file in glob.glob('LUT/' + data_type + '*.hdf'):
            data = load_data(file)
            data_dict.append({
                'type': data_type,
                'dataset_list': data.GetSubDatasets()
            })
        return data_dict

    for file in glob.glob(pathName + "/" + pathName + "*.hdf"):
        print(file)
        info = file.split('.')
        year = info[1][1:5]
        dayofyear = info[1][5:8]
        hour = info[2][0:2]
        minute = info[2][2:4]
        collection = info[3]
        dataset = load_data(file)
        data_dict.append({
            'id': num,
            'type': data_type,
            'year': int(year),
            'dofy': int(dayofyear),
            'hour': int(hour),
            'minute': int(minute),
            'collection': collection,
            'dataset_list': dataset.GetSubDatasets()
        })
        num += 1
    return data_dict


"""
def read_data2(file_name):
    hdf = SD(file_name, SDC.READ)
    hdf_attrs = hdf.attributes(full=1)
    datasets_dict = hdf.datasets()
    EV_500_RefSB = hdf.select('EV_500_RefSB')
    EV_500_RefSB_data = EV_500_RefSB[0, :, :].astype(np.double)
    EV_500_RefSB_attrs = EV_500_RefSB.attributes(full=1)

    reflectance_scales = EV_500_RefSB_attrs['reflectance_scales'][0]
    reflectance_offsets = EV_500_RefSB_attrs['reflectance_offsets'][0]
    radiance_scales = EV_500_RefSB_attrs['radiance_scales'][0]
    radiance_offsets = EV_500_RefSB_attrs['radiance_offsets'][0]
    # units = EV_500_RefSB_attrs['reflectance_units'][0]

    reflectance = reflectance_scales * (EV_500_RefSB_data - reflectance_offsets)

    lon = hdf.select('Longitude')
    lat = hdf.select('Latitude')
    lon_data = lon[:].astype(np.double)
    lat_data = lat[:].astype(np.double)

    return reflectance, lon_data, lat_data
    # lon_center = lon_data.flatten()[int(lon_data.flatten().size/2)]
    # lat_center = lat_data.flatten()[int(lat_data.flatten().size/2)]
    #
    # orth = ccrs.Orthographic(central_longitude=lon_center,
    #                          central_latitude=lat_center,
    #                          globe=None)
    # ax = plt.axes(projection=orth)
    #
    # p = plt.scatter(lon_data, lat_data, c=EV_500_RefSB_data, s=1, cmap=plt.cm.jet,
    #                 edgecolors=None, linewidth=0, transform=ccrs.PlateCarree())

    # Gridline with draw_labels=True doesn't work on Ortho projection.
    # ax.gridlines(draw_labels=True)
    # ax.gridlines()
    # ax.coastlines()
    # cb = plt.colorbar(p)
    # cb.set_label(units, fontsize=8)
    #
    # plt.show()


def read_data3(data_type):
    pathName = data_type
    data_dict = []
    num = 0

    if data_type == 'MYD02HKM_hdf':
        for file in glob.glob(pathName + "/" + pathName + "*.hdf"):
            print(file)
            info = file.split('.')
            year = info[1][1:5]
            dayofyear = info[1][5:8]
            hour = info[2][0:2]
            minute = info[2][2:4]
            collection = info[3]
            data, lon, lat = read_data2(file)
            data_dict.append({
                'id': num,
                'type': data_type,
                'year': int(year),
                'dofy': int(dayofyear),
                'hour': int(hour),
                'minute': int(minute),
                'collection': collection,
                'data': data,
                'lon': lon,
                'lat': lat
            })
            num += 1
    elif data_type == 'MYD09GA':
        for file in glob.glob(pathName + "/" + pathName + "*.hdf"):
            print(file)
            info = file.split('.')
            year = info[1][1:5]
            dayofyear = info[1][5:8]
            data, lon, lat = read_data2(file)
            data_dict.append(
                dict(id=num, type=data_type, year=int(year), dofy=int(dayofyear), data=data, lon=lon, lat=lat))
            num += 1
    return data_dict


def matrix_to_geo_tiff(filepath, matrices, gdal_type=gdal.GDT_CFloat64, transform=None, projection=None, nodata=None, GCP=None):
    (y_res, x_res) = matrices.shape
    driver = gdal.GetDriverByName('GTiff')
    image = driver.Create(filepath, x_res, y_res, 1, gdal_type)
    if transform is not None:
        image.SetGeoTransform(transform)
    if projection is not None:
        image.SetProjection(projection)
    if GCP is not None:
        image.SetGCPs(GCP, '')
    band = image.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(matrices)
    band.FlushCache()
    del image
    return


def resample_integral_multiple(data, scale):
    # data = data.values
    original_shape = np.shape(data)
    new_shape = (original_shape[0] * 2, original_shape[1] * 2)
    new_values = np.ones(new_shape)
    for i in range(new_shape[0]):
        for j in range(new_shape[1]):
            new_values[i][j] = data[int(i / 2)][int(j / 2)]
    # new_values = pd.DataFrame(new_values)
    return new_values
"""


def generateGCPs(lat, lon):
    GCP_list = []
    n_row, n_col = np.shape(lat)

    for i in range(0, n_row - 1):
        GCPPixel = i * 2 + 1
        for j in range(0, n_col - 1):
            lon_gap = lon[i + 1][j] - lon[i][j]
            lat_gap = lat[i][j + 1] - lat[i][j]
            GCPLine = j * 2 + 1
            GCPX = lon[i][j] + lon_gap / 4
            GCPY = lat[i][j] + lat_gap / 4
            gcp = gdal.GCP(GCPX, GCPY, 0, GCPPixel, GCPLine)
            GCP_list.append(gcp)
    return GCP_list
