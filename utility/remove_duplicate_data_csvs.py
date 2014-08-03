# -------------------------------------------------------------
# Name:       remove_duplicate_data_csvs
# Purpose:    Removes duplicate data files if they're in the pokemon data folder
# Author:     Duke
# Created:    8/2/2014
#-------------------------------------------------------------

from os import listdir, getcwd, remove
from os.path import isfile, join


def retrieve_files_in_folder(folder):
    pokemon_folder = getcwd().replace('\utility', '')
    return [f for f in listdir(join(pokemon_folder, folder))
            if isfile(join(pokemon_folder, folder, f))]


def main():
    folder_1_files = retrieve_files_in_folder('pokemon data')
    folder_2_files = retrieve_files_in_folder('unused data')

    for f in folder_2_files:
        if f in folder_1_files:
            remove(join(getcwd(), 'unused data', f))

if __name__ == '__main__':
    main()