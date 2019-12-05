import numpy as np
import readData2 as rd2
import matplotlib.pyplot as plt
import math
import argparse

omega = np.load("para_omega.npy")
g = np.load("para_g.npy")

# Rayleigh Optical Depth
tau_R = 0.09847234720729856


def retrieve_aod(dofy):
    mu_s = rd2.load(rd2.read_mu_s(dofy))
    mu_v = rd2.load(rd2.read_mu_v(dofy))
    P_a = rd2.load(rd2.read_P_a(dofy))
    toa = rd2.load(rd2.read_myd02(dofy))
    ray = rd2.load(rd2.read_ray(dofy))
    sur = rd2.load(rd2.read_myd09(dofy))
    g_ = g[dofy - 298]
    omega_ = omega[dofy - 298]
    rows, cols = np.shape(toa)

    def calculate_right(aod, i, j):
        numerator = math.pow(math.e, -(tau_R + aod) / mu_s[i, j]) * math.pow(math.e, -(tau_R + aod) / mu_v[i, j]) * sur[i, j]
        denominator = 1 - sur[i, j] * (0.92 * tau_R + (1 - g_) * aod) * math.pow(math.e, -(tau_R + aod))
        right = 2 * toa[i, j] - ray[i, j] - 0.2 * numerator / denominator
        right = 4 * mu_s[i, j] * mu_v[i, j] / (omega_ * P_a[i, j]) * right
        return right

    aod_mat = np.zeros((rows, cols))
    aod_num_list = np.linspace(0.0, 0.3, 61)
    for i in range(0, 666):
        if (i % 100 == 0):
            print("Now we are working on the row {} of the day {}...".format(i, dofy))
        for j in range(0, 1066):
            if sur[i, j] <= 0:
                aod_mat[i, j] = -100
                continue
            min_error = 10000000
            best_aod = -100
            for aod in aod_num_list:
                right = calculate_right(aod, i, j)
                error = math.fabs(right - aod)
                if error < min_error:
                    min_error = error
                    best_aod = aod
            aod_mat[i, j] = best_aod

    rd2.matrix_to_geo_tiff("AOD/AOD_2019_{:03d}.tif".format(dofy), aod_mat)
    return aod_mat


parser = argparse.ArgumentParser(description='AOD Retrieval')
parser.add_argument("--dofy", default=298, type=int, help="Day of the year")

args = parser.parse_args()
dofy = args.dofy

retrieve_aod(dofy)