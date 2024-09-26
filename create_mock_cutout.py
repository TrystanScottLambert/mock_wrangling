"""
Module for creating mocks from the hdf5 files that we have. 
"""

import glob
import h5py
from h5py._hl.group import Group
import numpy as np
import pandas as pd

from select_magnitudes import ids_less_than_mag, select_magnitudes_with_ids


def get_h5_group_properties(
    h5_group: Group, keys: list[str], ids: np.ndarray = None, id_column: str = None
) -> tuple[np.ndarray]:
    """
    Returns the galaxy properties which were specified. If a match_to_ids is specified then
    """

    if id_column is None and ids is not None:
        raise AttributeError("If ids are given then id_column must also be given")

    if ids is not None and id_column is not None:
        local_ids = h5_group[id_column][:]
        overlap_ids = np.intersect1d(ids, local_ids)
        sub_idx = np.array(
            [np.where(local_ids == overlap_id)[0][0] for overlap_id in overlap_ids]
        )

    else:
        sub_idx = np.arange(len(h5_group[keys[0]]))

    if len(sub_idx) ==0:
        data = None
    else:
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
        self.file = h5py.File(hdf5_name, "r")
        self.galaxies = self.file["galaxies"]
        self.groups = self.file["groups"]

    def get_galaxy_properties(
        self, keys: list[str], galaxy_ids: np.ndarray = None
    ) -> tuple[np.ndarray]:
        """
        Returns the galaxy properties which were specified.
        """
        return get_h5_group_properties(self.galaxies, keys, galaxy_ids, "id_galaxy_sky")

    def get_group_properties(
        self, keys: list[str], group_ids: np.ndarray = None
    ) -> tuple[np.ndarray]:
        """
        Returns the group properties which were specified.
        """
        return get_h5_group_properties(self.groups, keys, group_ids, "id_group_sky")

    def close_hdf5(self):
        """Closes the hdf5 file since we cannot use 'with' when we open it."""
        self.file.close()


def make_mock_catalog(
    mock_hdf5_files: list[str],
    galaxy_properties: list[str],
    group_properties: list[str],
    galaxy_ids: np.ndarray[int] = None,
    group_ids: np.ndarray[int] = None,
    prefix: str = "mock",
) -> None:
    """
    Creates two .dat files for the groups and the galaxies with the given ids and properties.
    """
    galaxy_values = []
    group_values = []
    for hdf5_file in mock_hdf5_files:
        print(f"creating mock from {hdf5_file}")
        light_cone = MockLightCone(hdf5_file)
        galaxy_properties_data = light_cone.get_galaxy_properties(galaxy_properties, galaxy_ids)
        group_properties_data = light_cone.get_group_properties(group_properties, group_ids)
        if galaxy_properties_data is not None:
            galaxy_values.append(galaxy_properties_data)
        if group_properties_data is not None:
            group_values.append(group_properties_data)
        light_cone.close_hdf5()

    # Write galaxies to file
    print("writing to file")
    with open(f"{prefix}_galaxies.dat", "w", encoding="utf-8") as file:
        for prop in galaxy_properties:
            file.write(f"{prop} ")
        file.write(" \n")
        for chunk in galaxy_values:
            inverse_chunk = np.array(chunk).T
            for row in inverse_chunk:
                for column in row:
                    file.write(f"{column} ")
                file.write(" \n")

    # Write groups to file
    with open(f"{prefix}_group.dat", "w", encoding="utf-8") as file:
        for prop in group_properties:
            file.write(f"{prop} ")
        file.write(" \n")
        for chunk in group_values:
            inverse_chunk = np.array(chunk).T
            for row in inverse_chunk:
                for column in row:
                    file.write(f"{column} ")
                file.write(" \n")


def combine_mag_gal_cats(
    mock_galaxies_catalog: str, magnitude_catalog: str, outfile: str
) -> None:
    """
    Join the two catalogs together to combine the galaxy properties and their magnitudes.
    They must be the same size and have the same ids.
    """
    ids_mock_catalalog = np.loadtxt(mock_galaxies_catalog, usecols=0, skiprows=1)
    ids_magnitude_catalog = np.loadtxt(magnitude_catalog, usecols=0, skiprows=1)
    if len(ids_mock_catalalog) != len(ids_magnitude_catalog):
        raise ValueError(
            "Length of mock_catalog must be the same as magnitude catalog."
        )

    if not np.array_equal(ids_mock_catalalog, ids_magnitude_catalog):
        raise ValueError(
            "ID mismatch between the mock galaxies and the magnitude catalog."
        )

    gal_df = pd.read_csv(mock_galaxies_catalog, sep='\s+')
    mag_df = pd.read_csv(magnitude_catalog, sep='\s+')
    combined = pd.concat([gal_df, mag_df.drop(columns="ID")], axis=1)
    combined['id_galaxy_sky'] = combined['id_galaxy_sky'].astype(int)
    combined.to_csv(outfile, sep=" ", index=False)


if __name__ == "__main__":
    # SED_FILE = 'SED_sample_files/VST_filters.dat'
    SED_FILE = "SED_sample_files/sdss_filters.dat"
    MAG_LIM = 19.8
    galaxy_sky_ids = ids_less_than_mag(SED_FILE, "z_SDSS_ap", MAG_LIM)

    mock_files = np.sort(glob.glob("mock_data_hdf5/mock_??.hdf5"))
    gal_properties = ["id_galaxy_sky", "ra", "dec", "zobs", "zcos", "zcmb"]
    grp_properties = ["id_group_sky", "ra", "dec", "zobs", "zcos", "zcmb", "mvir"]

    make_mock_catalog(
        mock_files, gal_properties, grp_properties, galaxy_ids=galaxy_sky_ids
    )
    select_magnitudes_with_ids(SED_FILE, galaxy_sky_ids, "magnitudes.dat")
    combine_mag_gal_cats("mock_galaxies.dat", "magnitudes.dat", "test_mock_catalog.dat")
