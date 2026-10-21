# Functions for ssb_binary_model files.

# Copyright (C) 2026 Thomas Rader

import os
import binascii
from inspect import currentframe, getframeinfo
from ssb_binary_model_adder_arguments import args

def error_message(e,cf=currentframe()):
    print(f'File "{os.path.basename(getframeinfo(cf).filename)}", line {cf.f_lineno}, An error occurred: \n{e}\n')
    
# Reads hexadecimal data from a file with hex offset given
def read_hex_from_offset(file_path, offset, num_bytes):
    """
    Reads data from binary file.

    Args:
        file_path (string): Source file.
        offset (string): Where in the file to read the data from.
        num_bytes (int): How many bytes to read.

    Returns:
        string: Hexadecimal data read from binary file.
    """
    try:
        with open(file_path, "rb") as f:
            offset_decimal = int(offset, 16)
            f.seek(offset_decimal)
            data = f.read(num_bytes)
            #print(f"Data read at {offset}: {data.hex()}")
            return data.hex()
    except FileNotFoundError:
        error_message(f"Error: File not found at {file_path}")
    except ValueError:
        error_message(f"Error: Invalid hex location '{offset}'")
    return None

# Writes hexadecimal data to a file with hex offset given
def write_hex_from_offset(new_file_path, offset, hex_string):
    """
    Writes over data in binary file.

    Args:
        new_file_path (string): File to write to.
        offset (string): Where to write the data to.
        hex_string (string): Hexadecimal data we are writing.

    Returns:
        None
    """
    try:
        with open(new_file_path, "rb+") as f:
            offset_decimal = int(offset, 16)
            f.seek(offset_decimal)
            binary_data = binascii.unhexlify(hex_string)
            f.write(binary_data)
            #print(f"Data written at {offset}: {hex_string} as {binary_data}")
    except FileNotFoundError:
        error_message(f"Error: File not found at {new_file_path}")
    except ValueError:
        error_message(f"Error: Invalid hex location '{offset}'")
    except binascii.Error as e:
        error_message(f"Error converting hex string: {e}. Ensure the hex string has an even number of characters and contains only valid hex digits (0-9, A-F).")

# Appends hexadecimal data to a file with hex offset given
def append_hex_from_offset(new_file_path, offset, hex_string):
    """
    Appends data to binary file.

    Args:
        new_file_path (string): File to write to.
        offset (string): Where to append the data to.
        hex_string (string): Hexadecimal data we are appending.

    Returns:
        None
    """
    try:
        with open(new_file_path, "r+b") as f:
            offset_decimal = int(offset, 16)
            f.seek(offset_decimal)
            remaining_data = f.read()
            f.seek(offset_decimal)
            binary_data = hex_string#binascii.unhexlify(hex_string)
            f.write(binary_data)
            f.write(remaining_data)
            #print(f"Data written at {offset}: {hex_string} as {binary_data}")
    except FileNotFoundError:
        error_message(f"Error: File not found at {new_file_path}")
    except ValueError as e:
        error_message(f"Error: Invalid hex location '{offset}' '{e}'")
    except binascii.Error as e:
        error_message(f"Error converting hex string: {e}. Ensure the hex string has an even number of characters and contains only valid hex digits (0-9, A-F).")

# Finds first pointer based on first non zero data in file (used for full pointer conversion on original character file)
def find_first_pointer_original_character(file_path):
    """
    Finds first pointer location in f3dex model file by looking for first non zero data.

    Args:
        file_path (string): Source file.

    Returns:
        int: Location of first pointer; returns -1 if nothing found.
    """
    # Setting variables
    reading_loc = "0x00"
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 2)
    # Determining index values
    while 1:
        # Setting decimal value to make sure we don't read over file size
        reading_loc_dec = int(reading_loc_hex,16)
        
        # Checking for first pointer command
        if (str(data).upper() != "0000"):
            return hex(int(reading_loc_hex, 16))
        
        # If at the end of the file, exit.
        if reading_loc_dec >= file_size:
            error_message("Couldn't find first pointer in original character file, exiting.")
            return -1
        
        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) + 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)
    return -1
