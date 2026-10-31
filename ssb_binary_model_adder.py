# Adds binary data to a ssb model file while adding offset to all pointers affected.
# Especially useful for models converted for RAM use by Model2F3DEX-SSB.

# TODO: 
#   *   inject pointers properly with last pointer in new data pointing to next possible pointer (or FFFF)
#       right now adding data with offset doesn't work properly when done multiple times.
#   *   fix formatting of this file
#   *   repurpose find_last_pointer_original_character

# Copyright (C) 2025 Thomas Rader


import shutil
import os
import subprocess
import binascii
import re
from inspect import currentframe, getframeinfo
from ssb_binary_model_adder_arguments import args
from ssb_binary_model_main import update_main_pointer_data
from ssb_binary_model_adder_folder import add_files
from ssb_binary_model_functions import remove_hex_from_range, backup_main_file

file_path = args.file
file_to_add_path = args.file_to_add
folder_to_add_path = args.folder_to_add
add = args.add
subtract = args.subtract
hex_location = args.offset
first_pointer = args.first_pointer
first_pointer_fta = args.first_pointer_file_to_add
first_pointer_main = -1 # Create argument
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
hex_location_range = -1
hex_location_range_section = int("0xFFFF",16)
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

def search_for_main(file_path):
    """
    Finds possible main character files in the same directory of the file
    we're modifying to use if non given.

    Args:
        file_path (str): Source file.

    Returns:
        list of str: All possible main character file candidates found.
    """
    # Setting variables
    main_candidates = []
    dir_path = os.path.dirname(file_path) or os.getcwd()
    main_reg = re.compile(r'.*main.*')
    number_file_candidate = 0

    # Check if file we're modifying is just numbers to see if a number file candidate exists
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if base_name.isdigit():
        number_file_candidate = int(base_name) - 1

    for files in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, files)):
            if files.endswith(".txt"):
                continue
            # Checking any file that has main in the name
            if main_reg.match(files):
                main_candidates.append(os.path.join(dir_path, files))
            # If current file we're modifying has all digit name (1234.bin) then we check for file with 1 less (1233.bin)
            if number_file_candidate != 0:
                file_name_digits = os.path.splitext(os.path.basename(files))[0]
                if file_name_digits.isdigit():
                    if int(file_name_digits) == number_file_candidate:
                        main_candidates.append(os.path.join(dir_path, files))

    return main_candidates

# Reads hexadecimal data from a file with hex offset given
def read_hex_from_offset(file_path, offset, num_bytes):
    """
    Reads data from binary file.

    Args:
        file_path (str): Source file.
        offset (str): Where in the file to read the data from.
        num_bytes (int): How many bytes to read.

    Returns:
        str: Hexadecimal data read from binary file.
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
        new_file_path (str): File to write to.
        offset (str): Where to write the data to.
        hex_string (str): Hexadecimal data we are writing.

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
        new_file_path (str): File to write to.
        offset (str): Where to append the data to.
        hex_string (str): Hexadecimal data we are appending.

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

def overwrite_file(source_path,destination_path):
    """
    Overwrites destination_path file.

    Args:
        source_path (str): Source file.
        destination_path (str): Output file.

    Returns:
        None
    """
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

# Finds first pointer based on op commands in a f3dex model file
def find_first_pointer(file_path=file_path):
    """
    Finds first pointer location in f3dex model file by looking for op commands. (Finds pointers based on op commands)

    Args:
        file_path (str): Source file.

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

# Returns last pointer based on last DF command in file_path
def find_last_pointer(file_path=file_path):
    """
    Finds last pointer location in f3dex model file based on DF command. (Finds pointers based on op commands)

    Args:
        file_path (str): Source file.

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

# Finds first pointer based on first non zero data in file (used for full pointer conversion on original character file)
def find_first_pointer_original_character(file_path=file_path,reading_loc="0x00"):
    """
    Finds first pointer location in f3dex model file by looking for first non zero data.

    Args:
        file_path (str): Source file.
        reading_loc (str): Beginning location in hexadecimal, ex: '0x10'.

    Returns:
        int: Location of first pointer; returns -1 if nothing found.
    """
    # Setting variables
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 4)
    # Determining index values
    while 1:
        # Setting decimal value to make sure we don't read over file size
        reading_loc_dec = int(reading_loc_hex,16)
        
        # Checking for first pointer command
        if (str(data[:4]).upper() != "0000"):
            return hex(int(reading_loc_hex, 16))
        
        # If at the end of the file, exit.
        if reading_loc_dec >= file_size:
            error_message("Couldn't find first pointer in original character file, exiting.")
            return -1
        
        # Reading next 4 bytes
        reading_loc = hex(int(reading_loc, 16) + 4)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 4)
    return -1

# Returns last pointer by following first non zero byte which is presumed to be a pointer
def find_last_pointer_original_character(file_path=file_path,ending_loc="0xFFFFFFFF",beginning_loc="0xFFFFFFFF"):
    """
    Finds last pointer location in f3dex model file based on the furthest pointer in the file.
    Will also return first pointer after beginning_loc or last pointer before ending_loc if either set.

    Args:
        file_path (str): Source file.
        ending_loc (str): Returns last pointer before this location if wanted.
        beginning_loc (str): Returns first pointer past this location if wanted.

    Returns:
        int: Location of last pointer; returns -1 if nothing found.
    """
    # Setting variables
    pointer_found = find_first_pointer_original_character(file_path)

    if pointer_found == -1:
        error_message("Couldn't find first pointer in original character so last pointer can't be found either, exiting.")
        return -1

    ending_loc = int(ending_loc, 16)
    beginning_loc = int(beginning_loc, 16)
    file_size = int(os.path.getsize(file_path))
    next_location = hex(int(pointer_found, 16))
    data = read_hex_from_offset(file_path, next_location, 4)
    furthest_pointer = 0

    # Determining index values
    while 1:
        # Setting decimal value to make sure we don't read over file size
        reading_loc_dec = int(next_location,16)
        
        # If at the end of the file, exit.
        if reading_loc_dec >= file_size:
            error_message("Couldn't find last pointer in original character file, exiting.")
            return -1

        # If next pointer is past our end location, return this pointer
        if int(data[:4].upper(),16)*4 >= ending_loc:
            return hex(furthest_pointer * 4)
        
        # If current position is past our beginning_loc, return this pointer
        if reading_loc_dec >= beginning_loc:
            return hex(furthest_pointer * 4)
        
        # Seeing if this is the last pointer
        if str(data[:4]).upper() != "FFFF" and int(str(data[:4]).upper(),16) > furthest_pointer:
            furthest_pointer = int(str(data[:4]).upper(),16)

        # If the next pointer is FFFF, return the furthest pointer found
        # this is how we determine the end of pointers
        if str(data[:4]).upper() == "FFFF":
            return hex(furthest_pointer * 4)

        # Finding next pointer location
        next_location = hex(int(str(data[:4]).upper(),16) * 4)
        data = read_hex_from_offset(file_path, next_location, 4)
    return -1

# Checking if original_character_file_size is set
if original_character_offset != "-1" and original_character_file_size == "-1":
    original_character_file_size = str(os.path.getsize(file_path))
    args.original_character_file_size = original_character_file_size

# Checking arguments
if file_to_add_path == "" and folder_to_add_path == "" and subtract == "" and add == "" and args.delete == "":
    error_message(f"Error file_to_add is '{file_to_add_path}' and there's nothing to subtract/add, subtract = '{subtract}', nothing to delete, delete = '{args.delete}', nothing to do, exiting.")
    exit(1)
if add != "" and subtract != "":
    error_message(f"Error, both subtract and add are set, subtract is '{subtract}' and add is '{add}'. You need to choose to either subtract or add, exiting.")
    exit(1)
if palette_costume != "" and not (costume_regex.match(str(palette_costume).upper())):
    error_message(f"Error, palette_costume doesn't match DE000000 0EXXXXXX, exiting.")
    exit(1)
if not args.no_main and args.main_file == "":
    main_candidates = search_for_main(file_path)
    response = "N"
    print("-no_main isn't set and no -main_file given, if updating a character file it's important to update main pointers too.")
    if main_candidates:
        print("Here are some possible candidates to use for the main file:")
        main_num = 0
        for main_files in main_candidates:
            print(f"{main_num}: {main_files}")
            main_num = main_num + 1
        print("Enter the leftmost number to use the corresponding file or\nEnter Y to continue without main or\nEnter C to cancel.")
        response = input()
        if response.isdigit():
            if int(response) >= len(main_candidates) or int(response) < 0:
                error_message(f"Response ({response}) isn't valid, please try again.")
                exit(1)
            else:
                args.main_file = main_candidates[int(response)]
        elif response.upper() != "Y":
            exit(0)
    else:
        print("Would you like to continue without a main character file? Enter Y/N")
        response = input()
        if response.upper() != "Y":
            exit(0)
if args.main_file != "":
    if not os.path.exists(args.main_file):
        error_message(f"Main file not found {args.main_file}.")
        exit(1)
    # Setting first main pointer
    if first_pointer_main == -1:
        first_pointer_main = find_first_pointer_original_character(args.main_file)

# Folder code redirection
if folder_to_add_path != "":
    add_files()
    exit(0)

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
    elif args.delete != "":
        offset_to_add = 4 # setting later
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

    # Backing up main file
    backup_main_file(args.main_file,args.no_main_backup)
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

# Making sure first_pointer is set
if first_pointer == "-1":
    first_pointer = find_first_pointer_original_character(file_path)
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
else:
    # Parsing offset to make sure it's not ranged
    if "-" in hex_location:
        hex_location_range = hex_location.split("-")[1]
        hex_location = hex_location.split("-")[0]
        hex_location_range_section = int(hex_location_range, 16) / 4

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
        file_path (str): Source file.

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
def update_pointer_data(file_path=file_path,destination_path=destination_path,hex_content=hex_content,current_location=current_location,hex_location_section=hex_location_section,offset_to_add=offset_to_add,num_bytes=num_bytes,pointers_overwritten=pointers_overwritten,force_offset=0,hex_location_range_section=65535):
    """
    Updates pointers in a file for ROM usage based on offset and amount given. (Finds pointers based on previous pointer location) 

    Args:
        file_path (str): Source file.
        destination_path (str): Output that the changes go to.
        hex_content (str): Current hexadecimal value we're at (pointer).
        current_location (str): Where we are in file_path, aka where hex_content is.
        hex_location_section (int): current_location / 4: if a pointer is more than this then we update it.
        offset_to_add (int): Decimal value that will be added to pointers.
        num_bytes (int): How many bytes we read when reading binary data.
        pointers_overwritten (int): Keeps track of how many pointers we've overwritten.
        force_offset(int): Used mainly for the file we're adding to the base file; overrules hex_location_section and always adds whatever value in offset_to_add to every pointer encountered. (also used for adding pointer difference)
        hex_location_range_section (int): if a pointer is less than this then we update it.

    Returns:
        None
    """
    
    # Debug printing
    print(f"Updating pointers in {os.path.basename(file_path)} into output {os.path.basename(destination_path)}:")
    
    while hex_content:
        # Setting upper and lower bits
        hex_content_upper_offset = int(hex_content[:4], 16) # This is what points to the next pointer
        hex_content_lower_offset = int(hex_content[4:], 16) # This is what points to the data
        new_upper_offset = -1
        new_lower_offset = -1
        new_upper_offset_padded = '{:04x}'.format(int(hex_content[:4], 16))
        new_lower_offset_padded = '{:04x}'.format(int(hex_content[4:], 16))

        # Making sure there's another pointer
        if hex_content_upper_offset == 0:
            error_message(f"Error, pointer at {hex_content} not pointing to anything. First 4 bytes are {new_upper_offset_padded}")
            exit(1)

        # If the offset we're adding is before the pointer locations, then we need to change them and add the offset
        if hex_content_upper_offset >= hex_location_section and hex_content_upper_offset <= hex_location_range_section:
            # print(f"Upper hexadecimal content is bigger")
            new_upper_offset = hex_content_upper_offset + offset_to_add
            new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset)) # 0000 byte format
        if hex_content_lower_offset >= hex_location_section and hex_content_lower_offset <= hex_location_range_section:
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
        if new_upper_offset != -1 or new_lower_offset != -1:
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

        # Update our next pointer location if it was changed (only do this if the content is already added)
        #if hex_content_upper_offset >= hex_location_section:
            # hex_content_upper_offset = new_upper_offset

        # Going to next pointer location
        current_location = hex((int(hex_content_upper_offset) * 4) + force_offset)
        hex_content = read_hex_from_offset(file_path, current_location, num_bytes)
    else:
        error_message("Error, couldn't find pointer.")
        exit(1)

# Setting up if we're deleting data
if args.delete:
    try:
        # Seperating our delete range
        beginning_range = args.delete.split("-")[0]
        ending_range = args.delete.split("-")[1]

        # Subtracting difference from all pointers pointing past ending_range
        offset_to_add = ((int(ending_range,16) - int(beginning_range,16)) * -1) / 4
        hex_location_section = int(ending_range,16) / 4

        # Printing ranges debug
        if debug:
            print(f"beginning_range = {beginning_range} ending_range = {ending_range} offset_to_add = {offset_to_add} hex_location_section = {hex_location_section}")

        # Finding first pointer after ending_range to set our last pointer before beginning_range to
        hanging_pointers = find_last_pointer_original_character(destination_path,beginning_loc=ending_range)
        hanging_pointers_data = read_hex_from_offset(destination_path,hanging_pointers,4)

        # Finding last pointer before beginning_range to set to our hanging pointers
        hanging_pointer = find_last_pointer_original_character(destination_path,beginning_range)
        new_pointer_location = hex(int(hanging_pointers,16) - (int(ending_range,16) - int(beginning_range,16)))

        # Updating pointer data
        update_pointer_data(file_path,destination_path,hex_content,current_location,hex_location_section,offset_to_add,num_bytes,pointers_overwritten)
        
        # Updating main character file pointers
        if args.main_file != "":
            update_main_pointer_data(args.main_file,args.main_file,first_pointer_main,hex_location_section,offset_to_add,args.req_file,num_bytes,pointers_overwritten,overwrite=True)

        # Printing pointer debug data
        if debug:
            print(f"hanging_pointers = {hanging_pointers} hanging_pointers_data = {hanging_pointers_data}\nhanging_pointer = {hanging_pointer} new_pointer_location = {"0x"+'{:04x}'.format(int(new_pointer_location,16))}")

        # Redirecting hanging pointer
        write_hex_from_offset(destination_path,hanging_pointer,'{:04x}'.format(int(int(new_pointer_location,16) / 4)))

        # Removing hexadecimal data
        remove_hex_from_range(destination_path,args.delete)

        # Overwriting if set
        overwrite_file(source_path,destination_path)

        # Done deleting data
        exit(0)
    except Exception as e:
        error_message(e)
        exit(1)

# Updating base file pointers
update_pointer_data(file_path,destination_path,hex_content,current_location,hex_location_section,offset_to_add,num_bytes,pointers_overwritten,0,hex_location_range_section)

# Updating main character file pointers
if args.main_file != "":
    update_main_pointer_data(args.main_file,args.main_file,first_pointer_main,hex_location_section,offset_to_add,args.req_file,num_bytes,pointers_overwritten,0,hex_location_range_section,overwrite=True)

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

            # Updating main file if we're not appending to end of character file
            if args.main_file != "" and int(hex_location,16) < os.path.getsize(file_path):
                update_main_pointer_data(args.main_file,args.main_file,first_pointer_main,hex_location_section,os.path.getsize(file_to_add_path),args.req_file,num_bytes,pointers_overwritten,hex_location_range_section,overwrite=True)
        except FileNotFoundError:
            error_message(f"Error: The file {file_to_add_path} was not found.")
        except Exception as e:
            error_message(e)
        exit(0)

    # Determining last pointer based on DF command and what to update it to based on first pointer in file_to_add
    end_pointer_loc = find_last_pointer_original_character(file_path)
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
            update_pointer_data(file_to_add_path,file_to_add_path_temp,hex_content,current_location,hex_location_section,fta_base_offset_difference,num_bytes,pointers_overwritten,force_offset=fta_pointer_difference,hex_location_range_section=hex_location_range_section)
            
            # Updating main file pointers if we're not appending file to end of character file
            if args.main_file != "" and int(hex_location,16) < os.path.getsize(file_path):
                update_main_pointer_data(args.main_file,args.main_file,first_pointer_main,hex_location_section,os.path.getsize(file_to_add_path),args.req_file,num_bytes,pointers_overwritten,0,hex_location_range_section,overwrite=True)

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
    except subprocess.CalledProcessError as e:
        error_message(e.stderr)
    except Exception as e:
        error_message(e)

# Overwriting if set
overwrite_file(source_path,destination_path)