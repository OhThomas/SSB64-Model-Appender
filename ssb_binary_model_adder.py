# Adds binary data to a ssb model file while adding offset to all pointers affected.
# Especially useful for models converted for RAM use by Model2F3DEX-SSB.

# Copyright (C) 2025 Thomas Rader


import shutil
import os
import subprocess
import argparse
import binascii
import re
from inspect import currentframe, getframeinfo
from ssb_binary_model_adder_arguments import args

file_path = args.file
file_to_add_path = args.file_to_add
folder_to_add_path = args.folder_to_add
add = args.add
subtract = args.subtract
hex_location = args.offset
first_pointer = args.first_pointer
first_pointer_fta = args.first_pointer_file_to_add
convert = not args.no_convert
debug = args.debug
palette_costume = args.palette_costume
python_version = args.python
overwrite = args.overwrite
output_path = args.o
original_character_offset = args.original_character_offset
original_character_file_size = args.original_character_file_size
num_bytes = 4
offset_to_add = 0
pointers_overwritten = 0
current_python_file_directory = os.path.dirname(os.path.realpath(__file__))

# Regex expressions
texture_regex = re.compile(r'FD[2-9,A-F][0-8]0000')
palette_regex = re.compile(r'FD[1][0-8]0000')
primitive_regex = re.compile(r'FA000000')
primitive_sync_regex = re.compile(r'E8000000')
rdp_sync_regex = re.compile(r'E7000000')
costume_regex = re.compile(r'DE0000000E[0-9]{6}')

def error_message(e,cf=currentframe()):
    print(f'File "{os.path.basename(getframeinfo(cf).filename)}", line {cf.f_lineno}, An error occurred: \n{e}\n')

# Checking if original_character_file_size is set
if original_character_offset != "-1" and original_character_file_size == "-1":
    original_character_file_size = str(os.path.getsize(file_path))
    args.original_character_file_size = original_character_file_size

# Folder code redirection
if folder_to_add_path != "":
    # Get the current working directory
    current_directory = os.getcwd()

    # Define the arguments to pass to the script
    python_convert_path = os.path.join(current_python_file_directory, "ssb_binary_model_adder_folder.py")
    arguments = ["-file", file_path, "-file_to_add", file_to_add_path, "-folder_to_add", folder_to_add_path, "-add", add, "-subtract", subtract, "-offset", hex_location, "-first_pointer", first_pointer, "-first_pointer_file_to_add", first_pointer_fta, "-palette_costume", args.palette_costume, "-original_character_offset", args.original_character_offset, "-original_character_file_size", args.original_character_file_size, "-python", python_version, "-output", output_path]
    if debug:
        arguments.append("-debug")
    if not convert:
        arguments.append("-no_convert")
    if overwrite:
        arguments.append("-overwrite")
    # command = [python_version, python_convert_path]
    command = [python_version, python_convert_path] + arguments
    # Converting file_to_add
    result = subprocess.run(command, capture_output=True, text=True)
    
    if debug:
        print(f"command = {command}")

    # Printing output
    print(f"~Output {os.path.basename(file_to_add_path)}~\n")
    print(f"{result.stdout}")

    exit(0)

# Checking arguments
if file_to_add_path == "" and subtract == "" and add == "":
    error_message(f"Error file_to_add is '{file_to_add_path}' and there's nothing to subtract, subtract = '{subtract}', nothing to do, exiting.")
    exit(1)
if add != "" and subtract != "":
    error_message(f"Error, both subtract and add are set, subtract is '{subtract}' and add is '{add}'. You need to choose to either subtract or add, exiting.")
    exit(1)
if palette_costume != "" and not (costume_regex.match(str(palette_costume).upper())):
    error_message(f"Error, palette_costume doesn't match DE000000 0EXXXXXX, exiting.")
    exit(1)

# Duplicating file
try:
    # Get the current working directory
    current_directory = os.getcwd()

    # Construct full paths for source and destination
    source_path = os.path.join(current_directory, file_path)
    destination_path = os.path.join(current_directory, output_path)
    if file_to_add_path != "":
        file_to_add_path = os.path.join(current_directory, file_to_add_path)
        file_to_add_path_temp = os.path.join(current_directory, file_to_add_path+"_temp")

        # Getting size of file to add so we can add it to pointer offsets
        offset_to_add = os.path.getsize(file_to_add_path)
    else:
        if add == "":
            offset_to_add = (int(subtract, 16) * -1)
        else:
            offset_to_add = int(add, 16)

    # Setting temp output if we're overwriting
    if file_path == output_path and overwrite == True:
        output_path = output_path+"temp"
        destination_path = os.path.join(current_directory, output_path)

    if file_path == output_path:
        error_message(f"Error: The file '{file_path}' is the same as the output '{output_path}'.")
        exit(1)

    # Deleting output file 
    if os.path.exists(destination_path):
        os.remove(destination_path)

    # Copy the file
    shutil.copy(source_path, destination_path)
    if debug:
        print(f"File '{os.path.basename(file_path)}' copied and renamed to '{os.path.basename(output_path)}' successfully.")
except FileNotFoundError as e:
    error_message(f"{e}")
    exit(1)
except Exception as e:
    error_message(e)
    exit(1)

if offset_to_add < 4 and offset_to_add > -4:
    error_message(f"File size of '{file_to_add_path}' or add size '{add}' or subtract size '{subtract}' not adequate, has to at least be 4.")
    exit(1)
else:
    offset_to_add = int(offset_to_add / 4)

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

# Returns last pointer based on last DF command in file_path
def find_last_pointer(file_path=file_path):
    """
    Finds last pointer location in f3dex model file based on DF command. (Finds pointers based on op commands)

    Args:
        file_path (string): Source file.

    Returns:
        int: Location of last pointer; returns -1 if nothing found.
    """
    # Setting variables
    file_size = int(os.path.getsize(file_path))
    reading_loc = hex(file_size)
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 8)

    while 1:
        # Setting decimal value to make sure we don't read over file size
        reading_loc_dec = int(reading_loc_hex,16)

        # Determining if op commands coming
        if str(data).upper() == "DF00000000000000":
            while 1:
                # Setting decimal value to make sure we don't read over file size
                reading_loc_dec = int(reading_loc_hex,16)

                # Checking for 01 command
                if (str(data[:2]).upper() == "01"):
                    return hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the 01 command

                # No more to read, exiting
                if reading_loc_dec <= 0:
                    print("Couldn't find indexes, exiting.")
                    return -1

                # Reading next 8 bytes
                reading_loc = hex(int(reading_loc, 16) - 8)
                reading_loc_hex = hex(int(reading_loc,16))
                data = read_hex_from_offset(file_path, reading_loc_hex, 8)
        # No more to read, exiting
        if reading_loc_dec <= 0:
            print("Couldn't find indexes, exiting.")
            return -1

        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) - 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)


# Finds first pointer based on op commands in a f3dex model file
def find_first_pointer(file_path=file_path):
    """
    Finds first pointer location in f3dex model file by looking for op commands. (Finds pointers based on op commands)

    Args:
        file_path (string): Source file.

    Returns:
        int: Location of first pointer; returns -1 if nothing found.
    """
    # Setting variables
    reading_loc = "0x00"
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 8)
    commands_found = False    # used to look for 01 command

    # Determining index values
    while 1:
        # Setting decimal value to make sure we don't read over file size
        reading_loc_dec = int(reading_loc_hex,16)

        # Checking for 01 command when certain regex have been seen
        if commands_found:
            # Checking for 01 command
            if (str(data[:2]).upper() == "01"):
                return hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the 01 command
        # FD5 = texture
        if (texture_regex.match(str(data[:8]).upper())):
            return hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the FD command
        # FD1 = palette
        elif (palette_regex.match(str(data[:8]).upper())):
            return hex(int(reading_loc_hex, 16) + 4) # adding 4 because reading_loc_hex is at the FD1 command
        # Look for 01 commands if we see these regex; FA = primitive coloring; E8 = tile; E7 = RDP sync
        elif primitive_regex.match(str(data[:8]).upper()) or primitive_sync_regex.match(str(data[:8]).upper()) or rdp_sync_regex.match(str(data[:8]).upper()):
            commands_found = True
        
        # If everything else fails (no index found), then we go through and see if
        # there's an 01 command after an E7 command for our first pointer
        if reading_loc_dec >= file_size:
            error_message("Couldn't find first pointer, exiting.")
            return -1

        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) + 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)
    return -1

# Making sure first_pointer is set
if first_pointer == "-1":
    first_pointer = find_first_pointer(file_path)
    if debug:
        print(f"First pointer in {os.path.basename(file_path)} set to {first_pointer}")

# If first_pointer is still -1 then something went wrong
if first_pointer == "-1":
    error_message(f"Error finding first pointer in {file_path}, first_pointer = {first_pointer}")
    exit(1)

# Making sure offset is set
if hex_location == "-1":
    file_size = int(os.path.getsize(file_path))
    hex_location = hex(file_size)
    if debug:
        print(f"Offset set to end of file at {hex_location}")

# Setting section to see if we need to change other pointers based on where we're adding
hex_location_section = int(hex_location, 16) / 4

# Getting 4 bytes from first pointer
hex_content = read_hex_from_offset(file_path, first_pointer, num_bytes)
current_location = first_pointer

# Getting base offset
# TODO: Look for 01 command after appropriate commands seen
def get_base_offset_ROM(file_path=file_path):
    """
    Gets base offset pointers use in a ROM model file. (Finds pointers based on op commands) 

    Args:
        file_path (string): Source file.

    Returns:
        int: Base offset of pointers.
    """
    
    # Debug printing
    if debug:
        print(f"Getting base offset in {os.path.basename(file_path)}:")
    
    # Setting variables
    reading_loc = "0x00"
    base_offset = "0x00"
    base_offset_dec = 65535 # FFFF
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 8)

    # Looping through file
    while 1:
        # Setting decimal value for location
        reading_loc_dec = int(reading_loc_hex,16)
        
        # Determining indexes
        # FD5 = texture
        if (texture_regex.match(str(data[:8]).upper())):
            location_offset = int(data[12:16],16)
            # print(f"location offset is {location_offset} hex is {data[12:16]}")
            if location_offset < base_offset_dec:
                base_offset_dec = location_offset
                base_offset = data[12:16]
        # FD1 = palette
        elif (palette_regex.match(str(data[:8]).upper())):
            location_offset = int(data[12:16],16)
            if location_offset < base_offset_dec:
                base_offset_dec = location_offset
                base_offset = data[12:16]
        # FA = primitive coloring
        elif (primitive_regex.match(str(data[:8]).upper())):
            while 1:
                reading_loc_dec = int(reading_loc_hex,16)

                # Checking for 01 command
                if (str(data[:2]).upper() == "01"):
                    # No texture found, set base_offset to where next 01 command points to
                    location_offset = int(data[12:16],16)
                    if location_offset < base_offset_dec:
                        base_offset_dec = location_offset
                        base_offset = data[12:16]
                    break
                # DF = end; only going through first commands
                elif str(data[:8]).upper() == "DF000000":
                    if base_offset_dec != 65535:
                        return base_offset

                # No more to read, exiting
                if reading_loc_dec >= file_size:
                    return base_offset

                # Reading next 8 bytes
                reading_loc = hex(int(reading_loc, 16) + 8)
                reading_loc_hex = hex(int(reading_loc,16))
                data = read_hex_from_offset(file_path, reading_loc_hex, 8)
            # base_offset = data[4:]
        # DF = end; only going through first commands
        elif str(data[:8]).upper() == "DF000000":
            if base_offset_dec != 65535:
                return base_offset
        # No more to read, exiting
        if reading_loc_dec >= file_size:
            return base_offset

        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) + 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)
    return base_offset

# Updating pointer data
def update_pointer_data(file_path=file_path,destination_path=destination_path,hex_content=hex_content,current_location=current_location,hex_location_section=hex_location_section,offset_to_add=offset_to_add,num_bytes=num_bytes,pointers_overwritten=pointers_overwritten,force_offset=0):
    """
    Updates pointers in a file for ROM usage based on offset and amount given. (Finds pointers based on previous pointer location) 

    Args:
        file_path (string): Source file.
        destination_path (string): Output that the changes go to.
        hex_content (string): Current hexadecimal value we're at (pointer).
        current_location (string): Where we are in file_path, aka where hex_content is.
        hex_location_section (string): current_location / 4: if a pointer is more than this then we update it.
        offset_to_add (int): Decimal value that will be added to pointers.
        num_bytes (int): How many bytes we read when reading binary data.
        pointers_overwritten (int): Keeps track of how many pointers we've overwritten.
        force_offset(int): Used mainly for the file we're adding to the base file; overrules hex_location_section and always adds whatever value in offset_to_add to every pointer encountered. (also used for adding pointer difference)

    Returns:
        None
    """
    
    # Debug printing
    print(f"Updating pointers in {os.path.basename(file_path)} into output {os.path.basename(destination_path)}:")
    
    while hex_content:
        # Setting upper and lower bits
        hex_content_upper_offset = int(hex_content[:4], 16) # This is what points to the next pointer
        hex_content_lower_offset = int(hex_content[4:], 16) # This is what points to the data
        new_upper_offset = 0
        new_lower_offset = 0
        new_upper_offset_padded = '{:04x}'.format(int(hex_content[:4], 16))
        new_lower_offset_padded = '{:04x}'.format(int(hex_content[4:], 16))

        # Making sure there's another pointer
        if hex_content_upper_offset == 0:
            error_message(f"Error, pointer at {hex_content} not pointing to anything. First 4 bytes are {new_upper_offset_padded}")
            exit(1)

        # If the offset we're adding is before the pointer locations, then we need to change them and add the offset
        if hex_content_upper_offset >= hex_location_section:
            # print(f"Upper hexadecimal content is bigger")
            new_upper_offset = hex_content_upper_offset + offset_to_add
            new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset)) # 0000 byte format
        if hex_content_lower_offset >= hex_location_section:
            # print(f"Lower hexadecimal content is bigger")
            new_lower_offset = hex_content_lower_offset + offset_to_add
            new_lower_offset_padded = '{:04x}'.format(int(new_lower_offset)) # 0000 byte format

        # Force offset change when using file_to_add (if we're looking at that and not the base file)
        if force_offset != 0:
            new_upper_offset = hex_content_upper_offset + offset_to_add
            new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset)) # 0000 byte format
            new_lower_offset = hex_content_lower_offset + offset_to_add
            new_lower_offset_padded = '{:04x}'.format(int(new_lower_offset)) # 0000 byte format

        
        # If upper bytes are 0xFFFF that indicates end of file so don't add the offset
        if hex_content_upper_offset == 65535:
            new_upper_offset = 65535
            new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset))

        # Making sure new bytes aren't bigger than possible (0xFFFF)
        if new_upper_offset >= 65536 or new_lower_offset >= 65536:
            error_message(f"Error with lower_offset: {new_lower_offset} or upper_offset:{new_upper_offset} being greater than 0xFFFF.")
            exit(1)

        # One or both of the pointers was after our insertion, so we must add the offset and update
        if new_upper_offset != 0 or new_lower_offset != 0:
            # Setting new byte
            new_byte_to_write = new_upper_offset_padded + new_lower_offset_padded

            # Making sure the bytes are different
            if hex_content != new_byte_to_write:
                # Making sure new byte is 4 bytes (less than 0xFFFF FFFF), then writing it to the new file
                if int(new_byte_to_write,16) > 4294967295:
                    print(f"Error, {new_upper_offset_padded} {new_lower_offset_padded} > 0xFFFFFFFF")
                # Changing byte
                else:
                    print(f"{current_location}: changing {hex_content} to {new_byte_to_write}\n")
                    write_hex_from_offset(destination_path,current_location,new_byte_to_write)
                    pointers_overwritten = pointers_overwritten + 1

        # End of file (0xFFFF)
        if hex_content_upper_offset == 65535:
            print(f"Done writing to {os.path.basename(destination_path)}, total pointers overwritten = {pointers_overwritten}\n")
            return None

        # Update our next pointer location if it was changed
        if hex_content_upper_offset >= hex_location_section:
            hex_content_upper_offset = new_upper_offset

        # Going to next pointer location
        current_location = hex((int(hex_content_upper_offset) * 4) + force_offset)
        hex_content = read_hex_from_offset(file_path, current_location, num_bytes)
    else:
        error_message("Error, couldn't find pointer.")
        exit(1)

# Updating base file pointers
update_pointer_data(file_path,destination_path,hex_content,current_location,hex_location_section,offset_to_add,num_bytes,pointers_overwritten)

# If we're adding a file to the output
if file_to_add_path != "":
    # Auto setting first pointer in file_to_add
    if first_pointer_fta == "-1":
        first_pointer_fta = find_first_pointer(file_to_add_path)
        if debug:
            print(f"First pointer in {os.path.basename(file_to_add_path_temp)} set to {first_pointer_fta}")

    # If no pointer in file we're adding then we just append to the location
    # if int(first_pointer_fta, 16) == 0:
    if first_pointer_fta == "-1" or first_pointer_fta == "-2":
        try:
            with open(file_to_add_path, 'rb') as f:
                file_to_add_data = f.read()
                append_hex_from_offset(destination_path,hex_location,file_to_add_data)
        except FileNotFoundError:
            error_message(f"Error: The file {file_to_add_path} was not found.")
        except Exception as e:
            error_message(e)
        exit(0)

    # Determining last pointer based on DF command and what to update it to based on first pointer in file_to_add
    end_pointer_loc = find_last_pointer(file_path)
    end_pointer_loc_content = read_hex_from_offset(file_path, end_pointer_loc, num_bytes)
    first_pointer_fta_test = find_first_pointer(file_to_add_path)
    first_pointer_fta_test_offset = hex(int(first_pointer_fta_test,16)+int(hex_location,16))

    # Getting last pointer in file_to_add to make it point back to the end of the file
    end_pointer_loc_fta = find_last_pointer(file_to_add_path) # use this with end_pointer_loc_content
    pointer_connect = '{:04x}'.format(int(int(first_pointer_fta_test_offset,16) / 4))
    write_hex_from_offset(destination_path,end_pointer_loc,pointer_connect)
    if debug:
        print(f"{end_pointer_loc}: changing {end_pointer_loc_content} to {pointer_connect} in {os.path.basename(destination_path)}")

    try:
        # Converting file_to_add to a ROM model (from 1 to 2 pointers per pointer command)
        if convert:
            # Define the arguments to pass to the script
            python_convert_path = os.path.join(current_python_file_directory, "ssb_binary_model_converter.py")
            arguments = ["-file", file_to_add_path, "-output", file_to_add_path_temp, "-offset", hex_location, "-palette_costume", args.palette_costume, "-original_character_offset", args.original_character_offset, "-original_character_file_size", args.original_character_file_size]
            if debug:
                arguments.append("-debug")
            command = [python_version, python_convert_path] + arguments

            # Converting file_to_add
            result = subprocess.run(command, capture_output=True, text=True, check=True)

            # Printing output
            print(f"~Converting {os.path.basename(file_to_add_path)}~\n\n{result.stdout}")

            if debug and result.stderr:
                error_message(f"~Errors from {args.o}:~\n\n{result.stderr}")
        # Updating file_to_add pointers
        else:
            # Copying file_to_add
            shutil.copy(file_to_add_path, file_to_add_path_temp)

            # Setting up to update file_to_add pointers
            file_size = int(os.path.getsize(file_to_add_path))
            hex_content = read_hex_from_offset(file_to_add_path, first_pointer_fta, num_bytes)
            current_location = first_pointer_fta
            pointers_overwritten = 0

            # Getting file_to_add offsets from where we're adding to apply to the pointers
            fta_base_offset = get_base_offset_ROM(file_to_add_path)
            fta_base_offset_difference = int(abs(int(fta_base_offset,16) - hex_location_section))
            fta_pointer_difference = int(int(fta_base_offset,16)*4)

            # If our base offset in file_to_add is more than the offset of where we're putting it, then we need to subtract instead of add
            if int(fta_base_offset,16) > hex_location_section:
                fta_pointer_difference = fta_pointer_difference * -1
                fta_base_offset_difference = fta_base_offset_difference * -1

            # Debug printing
            if debug:
                print(f"Applying difference of {hex(fta_base_offset_difference)} to pointers in {os.path.basename(file_to_add_path_temp)}")
                print(f"file_to_add: first_pointer = {first_pointer_fta} which is \t\t{hex_content}")
                print(f"file_to_add: base_offset   = {fta_base_offset} pointer_difference = \t{fta_pointer_difference}")

            # Applying offset to pointers
            update_pointer_data(file_to_add_path,file_to_add_path_temp,hex_content,current_location,hex_location_section,fta_base_offset_difference,num_bytes,pointers_overwritten,force_offset=fta_pointer_difference)

        # Replacing last pointer in file we're adding to the last pointer from the base file
        end_pointer_loc_content = end_pointer_loc_content[:4]
        write_hex_from_offset(file_to_add_path_temp,end_pointer_loc_fta,end_pointer_loc_content)
        if debug:
            print(f"{end_pointer_loc_fta}: changing FFFF to {end_pointer_loc_content} in {os.path.basename(file_to_add_path_temp)}")

        # Opening temporary file to append with
        with open(file_to_add_path_temp, 'rb') as f:
            file_to_add_data = f.read()
            append_hex_from_offset(destination_path,hex_location,file_to_add_data)

        # Deleting temporary file we used to modify pointers with
        if os.path.exists(file_to_add_path_temp):
            os.remove(file_to_add_path_temp)
    except Exception as e:
        error_message(e)

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
    print(f"Finished modifying {os.path.basename(source_path)}.")
else:
    print(f"Finished modifying {os.path.basename(destination_path)}.")