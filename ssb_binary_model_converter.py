# Converts a RAM model file to one suited for ROM usage.

# Copyright (C) 2025 Thomas Rader


import shutil
import os
import argparse
import binascii

parser = argparse.ArgumentParser()
parser.add_argument("-file", "--file",required=True,type=str,help="File we're converting.")
parser.add_argument("-offset","--offset","-location", "--location",required=True,type=str,help="Hexadecimal location of where we're adding the file in the binary (as a string, ex: '0x14').")
parser.add_argument("-first_pointer","--first_pointer","-internal_file_table_offset","--internal_file_table_offset",default="0x0",type=str,help="First pointer in the file we're expanding (usually following the first 01 command) (as a string, ex: '0x14').")
parser.add_argument("-pi","--pi","-palette_index", "--palette_index",default="0x0",type=str,help="Location where palette starts in file (as a string, ex: '0x14').")
parser.add_argument("-ti","--ti","-texture_index", "--texture_index",default="0x0",type=str,help="Location where textures start in file (as a string, ex: '0x14').")
parser.add_argument("-vi","--vi","-vertice_index", "--vertice_index",default="0x0",type=str,help="Location where vertices start in file (as a string, ex: '0x14').")
parser.add_argument("-oi","--oi","-opcode_index", "--opcode_index",default="0x0",type=str,help="Location where opcodes start in file (as a string, ex: '0x14').")
parser.add_argument("-debug","--debug",action="store_true",help="Prints debugging messages to output.")
parser.add_argument("-overwrite","--overwrite","-force","--force",action="store_true",help="Forces overwrite, making output go to -file.")
parser.add_argument("-o","--o","-output","--output",default="output.bin",type=str,help="Output file.")

args = parser.parse_args()

file_path = args.file
hex_location = args.offset
first_pointer = args.first_pointer
palette_index = args.pi
texture_index = args.ti
vertice_index = args.vi
opcode_index = args.oi
debug = args.debug
overwrite = args.overwrite
output_path = args.o
num_bytes = 4
pointers_overwritten = 0
hex_content = ""
current_location = "0x0"

# Duplicating file
try:
    # Get the current working directory
    current_directory = os.getcwd()

    # Construct full paths for source and destination
    source_path = os.path.join(current_directory, file_path)
    destination_path = os.path.join(current_directory, output_path)

    # Setting temp output if we're overwriting
    if file_path == output_path and overwrite == True:
        output_path = output_path+"temp"
        destination_path = os.path.join(current_directory, output_path)

    if file_path == output_path:
        print(f"Error: The file '{file_path}' is the same as the output '{output_path}'.")
        exit(1)

    # Deleting output file 
    if os.path.exists(destination_path):
        os.remove(destination_path)

    # Copy the file
    shutil.copy(source_path, destination_path)
    if debug:
        print(f"File '{os.path.basename(file_path)}' copied and renamed to '{os.path.basename(output_path)}' successfully.\n")
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
    exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)

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
        print(f"Error: File not found at {file_path}")
    except ValueError:
        print(f"Error: Invalid hex location '{offset}'")
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
        print(f"Error: File not found at {new_file_path}")
    except ValueError:
        print(f"Error: Invalid hex location '{offset}'")
    except binascii.Error as e:
        print(f"Error converting hex string: {e}. Ensure the hex string has an even number of characters and contains only valid hex digits (0-9, A-F).")

# Used to convert a file that was made with Model2F3DEX2SSB with single pointer addresses meant for RAM, into 2 pointers
def convert_single_pointer_file(file_path=file_path,destination_path=destination_path,hex_content_new_file=hex_content,current_location=current_location,num_bytes=num_bytes,pointers_overwritten=pointers_overwritten,end_pointer="FFFF"):
    """
    Converts pointers in a file for ROM usage by turning them into 2, based on offset and amount given.

    Args:
        file_path (string): Source file.
        destination_path (string): Output that the changes go to.
        hex_content_new_file (string): Current hexadecimal value we're at (pointer).
        current_location (string): Where we are in file_path, aka where hex_content is.
        hex_location_section (string): current_location / 4: if a pointer is more than this then we update it.
        num_bytes (int): How many bytes we read when reading binary data.
        pointers_overwritten (int): Keeps track of how many pointers we've overwritten.
        end_pointer(int): Determines what the last pointer is to stop converting.

    Returns:
        None
    """

    # Setting variables
    last_pointer = current_location
    file_size = int(os.path.getsize(file_path))
    opcode_pointer = hex(int(current_location, 16) - 4)
    opcode = read_hex_from_offset(file_path, opcode_pointer, num_bytes)
    op_command_seek = 1

    # Debug printing
    print(f"Updating pointers in {os.path.basename(file_path)} into output {os.path.basename(destination_path)}:")
    if debug:
        print(f"first opcode = {opcode} at {opcode_pointer}")

    # Determining op command and finding difference based on that
    # FD5 = texture
    if (str(opcode[:3]).upper() == "FD5") or (str(opcode[:3]).upper() == "FD9"):
        hex_location_padded = int(hex_location, 16) + int(texture_index, 16)
    # FD1 = palette
    elif str(opcode[:3]).upper() == "FD1":
        hex_location_padded = int(hex_location, 16) + int(palette_index, 16)
    # 01 = vertices
    elif str(opcode[:2]).upper() == "01":
        hex_location_padded = int(hex_location, 16) + int(vertice_index, 16)
    else:
        hex_location_padded = 0

    # Setting up to read through file
    force_difference = hex(int(hex_content_new_file,16)-hex_location_padded)
    next_pointer_location = 0
    looping = 1
    current_command = hex(int(current_location, 16) - 4)
    current_command = read_hex_from_offset(file_path,current_command,num_bytes)

    # Now use force difference to find data location throughout the rest of the file
    # and update the file pointers as you go
    while looping:
        data_location = '{:04x}'.format(int((int(hex_content_new_file,16) - int(force_difference,16))/4))
        # Looking for next op command with a pointer to update the last accordingly
        while op_command_seek:
            current_location = hex(int(current_location, 16) + 4)
            current_location_dec = int(current_location,16)
            op_command_seek = read_hex_from_offset(file_path, current_location, num_bytes)
            if str(op_command_seek[:3]).upper() == "FD5" or str(op_command_seek[:3]).upper() == "FD1" or str(op_command_seek[:2]).upper() == "01":
                next_pointer_location = hex(int(current_location, 16) + 4)
                new_location = '{:04x}'.format(int((int(hex_location,16) + int(next_pointer_location,16))/4))
                break
            if current_location_dec >= file_size:
                looping = 0
                new_location = end_pointer
                break

        # Overwriting last pointer
        new_byte_to_write = new_location+data_location
        old_byte = read_hex_from_offset(file_path,last_pointer,num_bytes)
        print(f"{last_pointer}: changing {old_byte} to {new_byte_to_write}\n")
        write_hex_from_offset(destination_path,last_pointer,new_byte_to_write)
        pointers_overwritten = pointers_overwritten + 1

        # Going to next pointer
        last_pointer = next_pointer_location
        hex_content_new_file = read_hex_from_offset(file_path,next_pointer_location,num_bytes)

        # Getting command from current location
        current_command = hex(int(current_location, 16))
        current_command = read_hex_from_offset(file_path,current_command,num_bytes)

    # Debug printing
    print(f"Done writing to {os.path.basename(destination_path)}, total pointers overwritten = {pointers_overwritten}")

# Making sure we have indexes for palette, vertices, textures, opcodes, etc
if opcode_index == "0x0":
    # Debug statement
    if debug:
        print(f"Attempting auto indexing for palette, vertice, texture, and opcodes...")

    # Setting variables
    reading_loc = "0x0"
    base_offset = "0x0"
    looping = 1
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 8)

    while 1:
        # Setting decimal value for location
        reading_loc_dec = int(reading_loc_hex,16)
        
        # Determining indexes
        # FD5 = texture
        if (str(data[:3]).upper() == "FD5") or (str(data[:3]).upper() == "FD9"):
            if first_pointer == "0x0":
                first_pointer = hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the FD command
            if texture_index == "0x0":
                texture_index = data[8:]
        # FD1 = palette
        elif str(data[:3]).upper() == "FD1":
            if first_pointer == "0x0":
                first_pointer = hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the FD1 command
            base_offset = data[8:]
        # FA = primitive coloring
        elif str(data[:8]).upper() == "FA000000":
            while 1:
                # Setting as decimal to make sure we don't read over file_size
                reading_loc_dec = int(reading_loc_hex,16)

                # Checking for 01 command
                if (str(data[:2]).upper() == "01"):
                    # No texture found, set base_offset to where next 01 command points to
                    if base_offset == "0x0":
                        base_offset = data[8:]
                        if first_pointer == "0x0":
                            first_pointer = hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the 01 command
                    if vertice_index == "0x0":
                        vertice_index = data[8:]
                    break

                # No more to read, exiting
                if reading_loc_dec >= file_size:
                    print("Couldn't find indexes, exiting.")
                    exit(1)

                # Reading next 8 bytes
                reading_loc = hex(int(reading_loc, 16) + 8)
                reading_loc_hex = hex(int(reading_loc,16))
                data = read_hex_from_offset(file_path, reading_loc_hex, 8)
            # base_offset = data[4:]
            break
        elif str(data[:8]).upper() == "E7000000":
            if opcode_index == "0x0":
                opcode_index = reading_loc_hex

        # No more to read, exiting
        if reading_loc_dec >= file_size:
            print("Couldn't find indexes, exiting.")
            exit(1)

        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) + 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)

    # Finished indexing, making sure we have a base_offset
    if base_offset == "0x0":
        print("Couldn't find a single pointer, exiting.")
        exit(1)
    
    # Set other indexes
    if texture_index != "0x0":
        texture_index = hex(int(texture_index, 16) - int(base_offset,16))
    if vertice_index != "0x0":
        vertice_index = hex(int(vertice_index, 16) - int(base_offset,16))

    # Debug statements
    if debug:
        print(f"Index of palette, texture, vertice, & opcodes: ")
        print(f"base_offset = {base_offset} first_pointer = {first_pointer}")
        print(f"palette_index = {palette_index} texture_index = {texture_index} vertice_index = {vertice_index} opcode_index = {opcode_index}\n")
    # exit(1)

# Getting first pointer data
hex_content = read_hex_from_offset(source_path, first_pointer, num_bytes)
current_location = first_pointer
pointers_overwritten = 0

# Converting
convert_single_pointer_file(source_path,destination_path,hex_content,current_location,num_bytes,pointers_overwritten)

# Overwriting base file
if overwrite:
    # Deleting base file
    if os.path.exists(source_path):
        os.remove(source_path)

    # Copying temp to base
    shutil.copy(destination_path, source_path)
    
    # Deleting temp file
    if os.path.exists(destination_path):
        os.remove(destination_path)