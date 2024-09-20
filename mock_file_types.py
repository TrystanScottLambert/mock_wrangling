"""
HDF5 specific classes
"""

from typing import Union

import numpy as np
import h5py

StrOrByte = Union[str, bytes]


class SED(h5py.File):
    """
    SED Extension of the hdf5 File type in h5py.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def print_filters(self):
        """Nicely prints all available filters"""
        for _filter in self["filters"][:]:
            print(_filter.decode())

    def get_filter_data(self, filter_name: StrOrByte, mag_type: str) -> np.ndarray:
        """
        Dumps the filter value for the given filter and mag type. filter name can be in bytes or
        in string.
        """
        if mag_type not in ("Apparent", "Absolute"):
            raise ValueError('mag_type must either be "Apparent" or "Absolute"')

        if isinstance(filter_name, str):
            filter_name = filter_name.encode()

        if filter_name not in self.filter_names:
            raise ValueError(f"{self.filename} has no filter called {filter_name}.")

        pos = np.where(self["filters"][:] == filter_name)[0]
        mags = self["SED"][f"{mag_type[:2].lower()}_dust"]["total"][pos][0]
        return mags

    def get_filters_data(
        self, filter_names: list[StrOrByte], mag_type: str
    ) -> np.ndarray[np.ndarray]:
        """
        Dumps the magnitude data for the given filter and mag type.
        """
        mags = []
        for filter_name in filter_names:
            mags.append(self.get_filter_data(filter_name, mag_type))
        return np.array(mags)

    @property
    def filter_names(self) -> np.ndarray:
        """
        Dumps the filter names from the hdf5 file.
        """
        return self["filters"][:]

    @property
    def galaxy_sky_ids(self) -> np.ndarray:
        """
        Dumps the id_galaxy_sky value from the hdf5 file.
        """
        return self["id_galaxy_sky"][:]
