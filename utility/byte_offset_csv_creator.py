# -------------------------------------------------------------
# Name:       byte_offset_csv_creator
# Purpose:    Create a byte offset CSV sheet of all pokemon ids to be used in main
# Author:     Duke
# Created:    8/2/2014
#-------------------------------------------------------------
# I'm not sure why newline characters are suddenly worth only one byte when compressed ...

import os


def retrieve_byte_offsets(path):
    with open(path, 'r') as file_object:
        iterator = 0
        tracking_letters = False

        string = ''
        byte_offset = {}

        for character in file_object.read():
            if tracking_letters:
                if character == ',':
                    tracking_letters = False
                    if not byte_offset.get(string, None):
                        byte_number = iterator - len(string)
                        byte_offset[string] = byte_number
                    string = ''
                string += character

            if character == '\n':
                # iterator += 1
                tracking_letters = True
                string = ''

            iterator += 1

    return byte_offset


def create_csv(dictionary):
    path = os.path.join(os.getcwd().replace('\utility', ''), 'pokemon data', 'pokemon_moves_bytes.csv')

    if os.path.exists(path):
        os.remove(path)

    with open(path, 'w+') as f:
        f.write('pokemon_id,byte_location')

        for pokemon_id, byte_location in sorted(dictionary.iteritems(), key=lambda x: int(x[0])):
            f.write('\n{},{}'.format(pokemon_id, byte_location))


def main():
    path = os.path.join(os.getcwd().replace('\utility', ''), 'pokemon data', 'pokemon_moves.csv')
    dictionary = retrieve_byte_offsets(path)
    create_csv(dictionary)


if __name__ == '__main__':
    main()