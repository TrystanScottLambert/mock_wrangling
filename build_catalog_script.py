"""
Script for making mock catalog.
"""

import os
import glob
import numpy as np
from read_filters import FilterData
from select_magnitudes import ids_less_than_mag, select_magnitudes_with_ids
from create_mock_cutout import make_mock_catalog, combine_mag_gal_cats
from mock_file_types import FilterList


# If need be create a full table of the filters that you want.

print('Creating the full magnitude table')
DIRECTORY = "/scratch/pawsey0119/clagos/Stingray/output/medi-SURFS/Shark-TreeFixed-ReincPSO-kappa0p002/deep-optical-final/split/"


#DIRECTORY = 'SED_sample_files/'
filters = FilterList(['FUV_GALEX', 'NUV_GALEX','u_VST','g_VST','r_VST','i_VST','Z_VISTA','Y_VISTA','J_VISTA',\
           'H_VISTA','K_VISTA','W1_WISE','W2_WISE','W3_WISE','W4_WISE','P100_Herschel',\
            'P160_Herschel','S250_Herschel','S350_Herschel','S500_Herschel'])
data = FilterData(DIRECTORY, filters)
data.write_to_ascii("filter_catalog.dat")


print('Applying the magnitude fit')
MAG_LIM = 25.
galaxy_sky_ids = ids_less_than_mag('filter_catalog.dat', "Z_VISTA_ap", MAG_LIM)
mock_files = np.sort(glob.glob(f"{DIRECTORY}mock_??.hdf5"))
gal_properties = ["id_galaxy_sky", "ra", "dec", "zobs", "zcos", "zcmb"]
grp_properties = ["id_group_sky", "ra", "dec", "zobs", "zcos", "zcmb", "mvir"]

print('Creating the mock catalog')
print('\t  - CREATING MOCK GALAXIES AND MOCK GROUPS')
make_mock_catalog(mock_files, gal_properties, grp_properties, galaxy_ids=galaxy_sky_ids)

print('\t -GETTING FILTER DATA')
select_magnitudes_with_ids('filter_catalog.dat', galaxy_sky_ids, "magnitudes.dat")

print('\t -COMBINING GALAXY DATA AND MAGNITUDE DATA')
combine_mag_gal_cats("mock_galaxies.dat", "magnitudes.dat", "mock_galaxies.dat")
os.remove('magnitudes.dat')
