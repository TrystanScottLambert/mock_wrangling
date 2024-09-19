"""
Selection package to cut hdf5 files by a magnitdue criteria.
"""

import numpy as np


def read_header(file_name: str, delimiter: str = " ") -> np.ndarray[str]:
    """
    Reads the first line of the given text file.
    """
    with open(file_name, encoding="utf-8") as file:
        header = file.readline().split(" \n")[0]
    column_list = header.split(delimiter)

    if column_list[0] != "ID":
        raise ValueError("File does not seem to have an ID column. Please check.")
    return np.array(column_list)


def ids_less_than_mag(sed_file_name: str, filter_name: str, mag_limit: float) -> np.ndarray[int]:
    """
    Loads in the SED file and returns the galaxy ids that are less than the mag_limit.
    """
    # make sure that the columns exist before running.
    header = read_header(sed_file_name)
    if filter_name not in header:
        raise ValueError("File does not have that filter in the header. Please check.")

    mag_column = np.where(header == filter_name)[0][0]
    ids, mags = np.loadtxt(
        sed_file_name, usecols=(0, mag_column), unpack=True, skiprows=1
    )
    cut = np.where(mags < mag_limit)
    return ids[cut].astype(int)


if __name__ == "__main__":
    INFILE = "SED_sample_files/VST_filters.dat"
    chosen_ids = ids_less_than_mag(INFILE, "r_VST_ap", 19)
