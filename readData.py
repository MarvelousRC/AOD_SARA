import gdal
import pandas as pd
import matplotlib.pyplot as plt
import glob
from matplotlib.ticker import PercentFormatter
import numpy as np
import math
import cartopy.crs as ccrs
from pyhdf.SD import SD, SDC


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


def read_data2(file_name):
    hdf = SD(file_name, SDC.READ)
    hdf_attrs = hdf.attributes(full=1)
    datasets_dict = hdf.datasets()
    EV_500_RefSB = hdf.select('EV_500_RefSB')
    EV_500_RefSB_data = EV_500_RefSB[0, :, :].astype(np.double)
    EV_500_RefSB_attrs = EV_500_RefSB.attributes(full=1)

    reflectance_scales = EV_500_RefSB_attrs['reflectance_scales'][0]
    reflectance_offsets = EV_500_RefSB_attrs['reflectance_offsets'][0]
    units = EV_500_RefSB_attrs['reflectance_units'][0]

    reflectance = reflectance_scales * (EV_500_RefSB_data - reflectance_offsets)

    lon = hdf.select('Longitude')
    lat = hdf.select('Latitude')
    lon_data = lon[:].astype(np.double)
    lat_data = lat[:].astype(np.double)

    lon_center = lon_data.flatten()[int(lon_data.flatten().size/2)]
    lat_center = lat_data.flatten()[int(lat_data.flatten().size/2)]

    orth = ccrs.Orthographic(central_longitude=lon_center,
                             central_latitude=lat_center,
                             globe=None)
    ax = plt.axes(projection=orth)

    p = plt.scatter(lon_data, lat_data, c=EV_500_RefSB_data, s=1, cmap=plt.cm.jet,
                    edgecolors=None, linewidth=0, transform=ccrs.PlateCarree())

    # Gridline with draw_labels=True doesn't work on Ortho projection.
    # ax.gridlines(draw_labels=True)
    # ax.gridlines()
    # ax.coastlines()
    cb = plt.colorbar(p)
    cb.set_label(units, fontsize=8)

    plt.show()



data = read_data2('MYD02HKM/MYD02HKM.A2019299.2125.061.2019300153403.psgscs_000501391352.hdf')


def show_histogram(data):
    """data should be a pandas Data Frame"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.hist(data.ravel(), bins=200, density=True)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    ax.set_title('A Histogram of the DN values')
    ax.set_xlabel('DN')
    ax.set_ylabel('Frequency')
    fig.show()


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


def to_radian(data):
    return data / 180 * math.pi / 100


# def interpolate_latlon(lat, lon, scale=2):
#


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


def matrix_to_geo_tiff(filepath, matrices, gdal_type=gdal.GDT_CFloat64, transform=None, projection=None, nodata=None, GCP=None):
    (y_res, x_res) = matrices.shape
    driver = gdal.GetDriverByName('GTiff')
    image = driver.Create(filepath, x_res, y_res, 1, gdal_type)
    if transform is not None:
        image.SetGeoTransform(transform)
    if projection is not None:
        image.SetProjection(projection)
    # if GCP is not None:
        # image.SetGCPs(GCP, '')
    band = image.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(matrices)
    band.FlushCache()
    del image
    return
