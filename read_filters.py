"""
Collect all the filters of all the SED hdf5 files.
"""

from dataclasses import dataclass
import glob
import h5py
import numpy as np

from mock_file_types import SED


def _select_appropriate_sed_files(directory: str) -> list[str]:
    """
    Searches for the 00 representative sample of files that can be searched for filters as well
    as used to make the glob cmd.
    """
    files = np.sort(glob.glob(directory + "*SED*00.hdf5"))[::-1]
    return files


def scrape_available_filters(directory: str) -> list[str]:
    """
    Goes through the given directory and scrapes all SED files for filter types then returns a list
    of the unique filters.
    """
    files = _select_appropriate_sed_files(directory)
    raw_filters = []
    for file in files:
        with h5py.File(file, "r") as f:
            raw_filters.append(f["filters"][:])

    all_filters = np.concatenate(raw_filters)
    unique_filters, indicies = np.unique(all_filters, return_index=True)
    unique_in_order = unique_filters[np.argsort(indicies)]
    return unique_in_order


def print_available_filters(directory: str, pretty: bool = False) -> None:
    """
    Scrapes all SEDs in the given directory and prints the available filters.
    """
    filters = scrape_available_filters(directory)
    if pretty:
        for _filter in filters:
            print(_filter.decode("utf-8"))
    else:
        print(filters)


def find_sed_files_with_filter(sed_files: list[str], filter_name: str) -> str:
    """
    Finds a SED file with that filter in the list of sed files.
    """
    for sed_file in sed_files:
        with h5py.File(sed_file, "r") as file:
            if filter_name in file["filters"][:]:
                correct_file = sed_file
                break
    return correct_file.split(".hdf5")[0][:-2] + "??.hdf5"


def get_mag_data(
    sed_ls_command: str, filter_names: list[str]
) -> tuple[np.ndarray, np.ndarray]:
    """
    Searches all the files with the given sed_ls_command and then downloads the ap_dust_total and
    ab_dust total values for the given filter. The filter needs to be present.
    """
    files = np.sort(glob.glob(sed_ls_command))

    galaxy_sky_ids = []
    ap_mags = []
    ab_mags = []
    for file in files:
        with SED(file) as sed:
            print("opening: ", file)
            galaxy_sky_ids.append(sed.galaxy_sky_ids)
            ap_mags.append(sed.get_filters_data(filter_names, "Apparent"))
            ab_mags.append(sed.get_filters_data(filter_names, "Absolute"))
    return np.concatenate(galaxy_sky_ids), np.hstack(ap_mags), np.hstack(ab_mags)


@dataclass
class Magnitudes:
    """Magnitude clas with methods for appending and writing."""

    name: str
    apparent_magnitudes: np.ndarray
    absolute_magnitudes: np.ndarray


class FilterData:
    """
    Representation of the filter data.
    """

    def __init__(self, directory: str, filter_names: list[str]) -> None:
        """
        Determine filters are available and get them.
        """

        self.searchable_hdf5_file = _select_appropriate_sed_files(directory)
        self.filter_names = filter_names
        cmds = [
            find_sed_files_with_filter(self.searchable_hdf5_file, filter_name)
            for filter_name in filter_names
        ]
        unique_cmds, idx, counts = np.unique(
            cmds, return_index=True, return_counts=True
        )
        filter_groups = [
            filter_names[_id : _id + count] for _id, count in zip(idx, counts)
        ]
        self.cmds = unique_cmds
        self.filter_groups = filter_groups
        self.magnitudes = {}
        self.get_mag_data()

    def get_mag_data(self) -> None:
        """
        Gathers the filter information from the correct files.
        """
        for filter_group, cmd in zip(self.filter_groups, self.cmds):
            ids, ap_mags, ab_mags = get_mag_data(cmd, filter_group)
            self.magnitudes["galaxy_ids"] = ids
            for filter_name, ap_mag, ab_mag in zip(filter_group, ap_mags, ab_mags):
                self.magnitudes[filter_name] = Magnitudes(filter_name, ap_mag, ab_mag)

    def write_to_ascii(self, outfile: str) -> None:
        """
        Writes filter data to a ascii file that can be downloaded.
        """
        print("Writing to File")
        with open(outfile, "w", encoding="utf-8") as file:
            file.write("ID ")
            for filter_name in self.filter_names:
                string_name = filter_name.decode("utf-8")
                file.write(f"{string_name}_ap {string_name}_ab ")
            file.write("\n")
            mags = []
            for filter_name in self.filter_names:
                mags.append(self.magnitudes[filter_name].apparent_magnitudes)
                mags.append(self.magnitudes[filter_name].absolute_magnitudes)
            mags = np.array(mags).T
            for _id, row in zip(self.magnitudes["galaxy_ids"].astype(int), mags):
                if _id != 0: # nans get turned into 0s with .astype(int). Removing nans in this step
                    file.write(f"{_id} ")
                    for column in row:
                        file.write(f"{column} ")
                    file.write(" \n")
                else:
                    print('SKIPPED_ROW')


if __name__ == "__main__":
    #TEST_DIRECTORY = 'SED_sample_files/'
    #test_filts = scrape_available_filters(TEST_DIRECTORY)
    #chosen_filts = test_filts[10:13]
    #test = FilterData(TEST_DIRECTORY, chosen_filts)
    #test.write_to_ascii('is_this_right.dat')

    # For Pawsey
    DIRECTORY = "/scratch/pawsey0119/clagos/Stingray/output/medi-SURFS/\
        Shark-TreeFixed-ReincPSO-kappa0p002/deep-optical-final/split/"
    available_filters = scrape_available_filters(DIRECTORY)
    VST_filters = available_filters[40:44]
    VISTA_filters = available_filters[44:49]
    sdss_filters = available_filters[4:7]
    print("Getting These Filters: ", sdss_filters)
    data = FilterData(DIRECTORY, sdss_filters)
    data.write_to_ascii("sdss_filters.dat")
