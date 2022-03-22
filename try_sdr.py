import functools
import os

import numpy
import pygeoprocessing
import pygeoprocessing.routing
from natcap.invest.sdr import sdr
from natcap.invest.sdr import sdr_core
from osgeo import osr

TFA = 4
DEM = numpy.array([[5, 4, 3, 2, 1]], dtype=numpy.uint8)
USLE = numpy.array([[3, 2, 1, 1.5, -1]], dtype=numpy.float32)
# SDR = numpy.array([[0.7, 0.5, 0.3, 1, -1]], dtype=numpy.float32)  # old one

# here we're trying SDR that's monotonically increasing as we go downstream.
SDR = numpy.array([[0.3, 0.5, 0.7, 1, -1]], dtype=numpy.float32)
#EROSIVITY = numpy.array([[ ]], dtype=numpy.float32)
#ERODIBILITY = numpy.array([[ ]], dtype=numpy.float32)
LULC = numpy.array([[1, 2, 3, 4, -1]], dtype=numpy.float32)


SRS = osr.SpatialReference()
SRS.ImportFromEPSG(4326)

#E_PRIME = numpy.array([[ , , , ]], dtype=numpy.float32)
#F = numpy.array([[ , , , ]], dtype=numpy.float32)
RASTER = functools.partial(
    pygeoprocessing.numpy_array_to_raster,
    target_nodata=-1,
    pixel_size=(1, -1),
    origin=(0, 0),
    projection_wkt=SRS.ExportToWkt())

WORKSPACE = 'sdr-debugging'
if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)

#biophysical_table_path = os.path.join(WORKSPACE, 'biophysical.csv')
#with open(biophysical_table_path, 'w') as table:
#    table.write('lucode,usle_c,usle_p')
#    table.write('1,,')
#    table.write('2,,')
#    table.write('3,,')
#    table.write('4,,')

dem_path = os.path.join(WORKSPACE, 'dem.tif')
usle_path = os.path.join(WORKSPACE, 'usle.tif')
sdr_path = os.path.join(WORKSPACE, 'sdr.tif')
RASTER(base_array=DEM, target_path=dem_path)
RASTER(base_array=USLE, target_path=usle_path)
RASTER(base_array=SDR, target_path=sdr_path)

# ARGS = {
#     'workspace_dir': WORKSPACE,
#     'dem_path': dem_path,
#     'erosivity_path': erosivity_path,
#     'erodibility_path': erodibility_path,
#     'lulc_path': lulc_path,
#     'watersheds_path': None,
#     'biophysical_table_path':
#
# }

flow_dir_path = os.path.join(WORKSPACE, 'flow_dir.tif')
pygeoprocessing.routing.flow_dir_mfd(
    (dem_path, 1), flow_dir_path)

flow_accum_path = os.path.join(WORKSPACE, 'flow_accum.tif')
pygeoprocessing.routing.flow_accumulation_mfd(
    (flow_dir_path, 1), flow_accum_path)

streams_path = os.path.join(WORKSPACE, 'streams.tif')
pygeoprocessing.routing.extract_streams_mfd(
    (flow_accum_path, 1),
    (flow_dir_path, 1),
    TFA,
    streams_path)



# calculate_ic
# ic_path = os.path.join(workspace, 'ic.tif')
# sdr._calculate_ic(
#     d_up_path,
#     d_dn_path,
#     ic_path
# )


# make SDR
#sdr_path = os.path.join(WORKSPACE, 'sdr.tif')
#sdr._calculate_sdr(
#    1, # k_param
#    1, # ic_0_param
#    0.8, # sdr_max
#    ic_path,
#    streams_path,
#    sdr_path
#)

# make e_prime
e_prime_path = os.path.join(WORKSPACE, 'e_prime.tif')
sdr._calculate_e_prime(
    usle_path, sdr_path, e_prime_path)

sed_deposition_path = os.path.join(WORKSPACE, 'sed_deposition.tif')
f_path = os.path.join(WORKSPACE, 'f.tif')  # TODO: add to target_path_list
sdr_core.calculate_sediment_deposition(
    flow_dir_path, e_prime_path, f_path, sdr_path, sed_deposition_path
)

sed_export_path = os.path.join(WORKSPACE, 'sed_export.tif')
sdr._calculate_sed_export(
    usle_path, sdr_path, sed_export_path)

dr_path = os.path.join(WORKSPACE, 'dr.tif')

numpy.set_printoptions(formatter={'float': '{: 0.8f}'.format})
for label, raster in (('sdr', sdr_path),
                      ('usle', usle_path),
                      ('e_prime', e_prime_path),
                      ('f', f_path),

                      # I hacked a dr raster into the model so we could check
                      # that our calculations were correct.  I'm leaving this
                      # commented out in case we're using vanilla SDR.
                      #('dr', dr_path),
                      ('sed_dep "r"', sed_deposition_path),
                      ('sed_export', sed_export_path),
                     ):
    array = pygeoprocessing.raster_to_numpy_array(raster).astype(numpy.float32)
    print(f'{label:20} {array}')
