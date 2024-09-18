"""
Collect all the filters of all the SED hdf5 files.
"""

import glob
import h5py
import numpy as np

def _select_appropriate_sed_files(directory: str) -> list[str]:
    """
    Searches for the 00 representative sample of files that can be searched for filters as well 
    as used to make the glob cmd.
    """
    files = np.sort(glob.glob(directory + '*SED*00.hdf5'))
    return files

def scrape_available_filters(directory: str) -> list[str]:
    """
    Goes through the given directory and scrapes all SED files for filter types then returns a list
    of the unique filters.
    """
    files = _select_appropriate_sed_files(directory)
    raw_filters = []
    for file in files:
        with h5py.File(file, 'r') as f:
            raw_filters.append(f['filters'][:])

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
            print(_filter.decode('utf-8'))
    else:
        print(filters)

def find_sed_files_with_filter(sed_files: list[str], filter_name: str) -> str:
    """
    Finds a SED file with that filter in the list of sed files.
    """
    for sed_file in sed_files:
        with h5py.File(sed_file, 'r') as file:
            if filter_name in file['filters'][:]:
                correct_file = sed_file
                break
    return correct_file.split('.hdf5')[0][:-2] + '*.hdf5'

def get_mag_data(sed_ls_command: str, filter_name: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Searches all the files with the given sed_ls_command and then downloads the ap_dust_total and
    ab_dust total values for the given filter. The filter needs to be present.
    """
    files = np.sort(glob.glob(sed_ls_command))

    galaxy_sky_ids = []
    ap_mags = []
    ab_mags = []
    for file in files:
        with h5py.File(file, 'r') as sed_file:
            filter_position = np.where(sed_file['filters'][:] == filter_name)[0]
            galaxy_sky_ids.append(sed_file['id_galaxy_sky'][:])
            ap_mags.append(sed_file['SED']['ap_dust']['total'][:][filter_position][0])
            ab_mags.append(sed_file['SED']['ab_dust']['total'][:][filter_position][0])
    return np.concatenate(galaxy_sky_ids), np.concatenate(ap_mags), np.concatenate(ab_mags)

def find_mag_data(directory: str, filter_names: list[str], outfile: str) -> None:
    """
    Builds a csv file with the magnitudes for all the given filters.
    """
    rough_search_sed_files = _select_appropriate_sed_files(directory)
    ap_mags_filters = []
    ab_mags_filters = []
    for filter_name in filter_names:
        cmd = find_sed_files_with_filter(rough_search_sed_files, filter_name)
        ids, ap_mags, ab_mags = get_mag_data(cmd, filter_name)
        ap_mags_filters.append(ap_mags)
        ab_mags_filters.append(ab_mags)
    ap_mags_filters = np.array(ap_mags_filters).T
    ab_mags_filters = np.array(ab_mags_filters).T

    #Write to file
    with open(outfile, 'w', encoding='utf-8') as file:
        file.write('ID ')
        for filter_name in filter_names:
            string_name = filter_name.decode('utf-8')
            file.write(f'{string_name}_ap {string_name}_ab ')
        file.write('\n')
        ids = ids.astype(int)
        for i, _id in enumerate(ids):
            file.write(f'{_id} ')
            for ap_mag, ab_mag in zip(ap_mags_filters[i], ab_mags_filters[i]):
                file.write(f'{ap_mag} {ab_mag} ')
            file.write('\n')


if __name__ == '__main__':
    TEST_DIRECTORY = 'SED_sample_files/'
    test_filts = scrape_available_filters(TEST_DIRECTORY)
    chosen_filts = test_filts[10:13]

    find_mag_data(TEST_DIRECTORY, chosen_filts, 'is_this_right.dat')
