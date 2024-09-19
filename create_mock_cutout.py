"""
Module for creating mocks from the hdf5 files that we have. 
"""

import glob
import h5py
from h5py._hl.group import Group
import numpy as np

from select_magnitudes import ids_less_than_mag

def get_h5_group_properties(
        h5_group: Group, keys: list[str], ids: np.ndarray = None, id_column: str = None
        ) -> tuple[np.ndarray]:
    """
    Returns the galaxy properties which were specified. If a match_to_ids is specified then 
    """

    if id_column is None and ids is not None:
        raise AttributeError('If ids are given then id_column must also be given')

    if ids is not None and id_column is not None:
        local_ids = h5_group[id_column][:]
        overlap_ids = np.intersect1d(ids, local_ids)
        sub_idx = np.array([np.where(local_ids == overlap_id)[0][0] for overlap_id in overlap_ids])

    else:
        sub_idx = np.arange(len(h5_group[keys[0]]))

    data = []
    for key in keys:
        data.append(h5_group[key][:][sub_idx])
    return data


class MockLightCone:
    """
    A single mock light cone that is often of the form mock_00.hdf5.
    Converting reading in the hdf5 format and converting it to a reduced and more managable object.
    """

    def __init__(self, hdf5_name: str) -> None:
        self.file = h5py.File(hdf5_name, 'r')
        self.galaxies = self.file['galaxies']
        self.groups = self.file['groups']

    def get_galaxy_properties(self, keys: list[str], galaxy_ids: np.ndarray = None) -> tuple[np.ndarray]:
        """
        Returns the galaxy properties which were specified.
        """
        return get_h5_group_properties(self.galaxies, keys, galaxy_ids, 'id_galaxy_sky')

    def get_group_properties(self, keys: list[str], group_ids: np.ndarray = None) -> tuple[np.ndarray]:
        """
        Returns the group properties which were specified.
        """
        return get_h5_group_properties(self.groups, keys, group_ids, 'id_group_sky')

    def close_hdf5(self):
        """Closes the hdf5 file since we cannot use 'with' when we open it."""
        self.file.close()


def make_mock_catalog(
        mock_hdf5_files: list[str], galaxy_properties: list[str], group_properties: list[str],
        galaxy_ids: np.ndarray[int] = None, group_ids: np.ndarray[int] = None,
        prefix: str = 'mock') -> None:
    """
    Creates two .dat files for the groups and the galaxies with the given ids and properties.
    """
    galaxy_values = []
    group_values = []
    for hdf5_file in mock_hdf5_files:
        print(f'creating mock from {hdf5_file}')
        light_cone = MockLightCone(hdf5_file)
        galaxy_values.append(light_cone.get_galaxy_properties(galaxy_properties, galaxy_ids))
        group_values.append(light_cone.get_group_properties(group_properties, group_ids))
        light_cone.close_hdf5()

    # Write galaxies to file
    print('writing to file')
    with open(f'{prefix}.dat','w', encoding='utf-8') as file:
        for prop in galaxy_properties:
            file.write(f'{prop} ')
        file.write(' \n')
        for chunk in galaxy_values:
            inverse_chunk = np.array(chunk).T
            for row in inverse_chunk:
                for column in row:
                    file.write(f'{column} ')
                file.write(' \n')

    #write groups to file
    with open(f'{prefix}_group.dat', 'w', encoding='utf-8') as file:
        for prop in group_properties:
            file.write(f'{prop} ')
        file.write(' \n')
        for chunk in group_values:
            inverse_chunk = np.array(chunk).T
            for row in inverse_chunk:
                for column in row:
                    file.write(f'{column} ')
                file.write(' \n')

if __name__ == '__main__':
    SED_FILE = 'SED_sample_files/VST_filters.dat'
    MAG_LIM = 20
    magnitudes = ['u_VST_ap', 'g_VST_ap', 'r_VST_ap', 'i_VST_ap']
    galaxy_sky_ids = ids_less_than_mag(SED_FILE, 'r_VST_ap', 19)

    mock_files = np.sort(glob.glob('mock_data_hdf5/mock_??.hdf5'))
    galaxy_properties = ['id_galaxy_sky','ra', 'dec', 'zobs', 'zcos', 'zcmb']
    group_properties = ['id_group_sky', 'ra', 'dec', 'zobs', 'zcos','zcmb', 'mvir']

    make_mock_catalog(mock_files, galaxy_properties, group_properties, galaxy_ids=galaxy_sky_ids)
