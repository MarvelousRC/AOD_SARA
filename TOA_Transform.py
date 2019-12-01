import readData as rd

MYD02HKM = rd.read_MYD02(4, 1)
MYD02HKM_para = rd.read_parameters_from_MYD02_HDF()
MYD02HKM = rd.preprocess_MYD02(MYD02HKM, MYD02HKM_para)
del MYD02HKM
del MYD02HKM_para

