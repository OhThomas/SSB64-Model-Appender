# Checks main file of a character and updates pointers.

# Copyright (C) 2026 Thomas Rader

import shutil
import os
import re
from inspect import currentframe, getframeinfo
from ssb_binary_model_adder_arguments import args
from ssb_binary_model_functions import find_first_pointer_original_character, read_hex_from_offset, write_hex_from_offset, append_hex_from_offset

def error_message(e,cf=currentframe()):
    print(f'File "{os.path.basename(getframeinfo(cf).filename)}", line {cf.f_lineno}, An error occurred: \n{e}\n')

def find_first_character_main(file_path):
    """
    Finds first line in main txt file that has "Character" in it to use if req_file isn't set.
    
        Args:
            file_path (str): Character main txt file for req files.
    
        Returns:
            str: First "Character" string found in main txt file.
    """
    char_reg = re.compile(r'.*Character.*')
    with open(file_path, "r") as txt_file:
        for line in txt_file:
            if char_reg.match(line.replace('\n','')):
                return line.replace('\n','')
        return ""

# Updating pointer data for main character file
def update_main_pointer_data(file_path,destination_path,hex_content,current_location,hex_location_section,offset_to_add,req_file="",num_bytes=4,pointers_overwritten=0,force_offset=0):
    """
    Updates pointers in a file for ROM usage based on offset and amount given. (Finds pointers based on previous pointer location) 

    Args:
        file_path (str): Source file.
        destination_path (str): Output that the changes go to.
        hex_content (str): Current hexadecimal value we're at (pointer).
        current_location (str): Where we are in file_path, aka where hex_content is.
        hex_location_section (str): current_location / 4: if a pointer is more than this then we update it.
        offset_to_add (int): Decimal value that will be added to pointers.
        req_file (str): File name used in main req txt list to update pointers with, ex: '1552 Dedede Cowboy Character'.
        num_bytes (int): How many bytes we read when reading binary data.
        pointers_overwritten (int): Keeps track of how many pointers we've overwritten.
        force_offset(int): Used mainly for the file we're adding to the base file; overrules hex_location_section and always adds whatever value in offset_to_add to every pointer encountered. (also used for adding pointer difference)

    Returns:
        None
    """
    # Checking arguments
    if not os.path.exists(file_path):
        error_message(f"Main file not found {file_path}.")
        exit(1)

    # Setting variables
    txt_file_path = os.path.splitext(file_path)[0] + ".txt"
    if not os.path.isfile(txt_file_path):
        error_message(f"Text file not found {txt_file_path}.")
        exit(1)
    with open(txt_file_path, "r") as txt_file:
        txt_lines = txt_file.readlines()
    if not txt_lines:
        error_message(f"No data found in text file {txt_file_path}: {txt_lines}.")
        exit(1)
    current_line = 0

    # Checking if destination path exists
    destination_path = create_output_file(destination_path)

    # Checking if destination txt file exists, copy source txt if not
    txt_file_destination = os.path.splitext(destination_path)[0] + ".txt"
    if not os.path.isfile(txt_file_destination):
        shutil.copy(txt_file_path, txt_file_destination)

    # Checking if req file is set and setting if not (so we update the pointers related to the Character file).
    if req_file == "":
        req_file = find_first_character_main(txt_file_path)
        if req_file == "":
            error_message(f"Req file not set and couldn't be found in character main txt file {txt_file_path}")
            exit(1)
        print(f"Using req_file {req_file} to update main character file with. -req_file wasn't set.")

    # Debug printing
    print(f"Updating pointers in {os.path.basename(file_path)} into output {os.path.basename(destination_path)}:")
    
    hex_content = read_hex_from_offset(file_path, current_location, num_bytes)
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
        # if hex_content_upper_offset >= hex_location_section:
        #     # print(f"Upper hexadecimal content is bigger")
        #     new_upper_offset = hex_content_upper_offset + offset_to_add
        #     new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset)) # 0000 byte format
        if hex_content_lower_offset >= hex_location_section:
            # print(f"Lower hexadecimal content is bigger")
            new_lower_offset = hex_content_lower_offset + offset_to_add
            new_lower_offset_padded = '{:04x}'.format(int(new_lower_offset)) # 0000 byte format

        # Force offset change when using file_to_add (if we're looking at that and not the base file)
        if force_offset != 0:
            # new_upper_offset = hex_content_upper_offset + offset_to_add
            # new_upper_offset_padded = '{:04x}'.format(int(new_upper_offset)) # 0000 byte format
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
            # print(f"here,  req file at {current_line}. Line = {txt_lines[current_line]} Reg file = {req_file}.")
            # Setting new byte
            new_byte_to_write = new_upper_offset_padded + new_lower_offset_padded

            # Making sure this is the pointer used in the character file as opposed to a diff req file
            if current_line > len(txt_lines):
                error_message(f"Past req lines available in text file {txt_file_path} while still trying to update pointers. Something is wrong in either the main binary ({args.main_file}) or main text file ({txt_file_path}). Exiting...")
                exit(1)
            else:
                txt_lines[current_line] = txt_lines[current_line].replace('\n','')
                if txt_lines[current_line] == req_file:
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
                else:
                    if args.debug:
                        print(f"Non matching req file at {current_line}. Line = {txt_lines[current_line]} Reg file = {req_file}.")

        # End of file (0xFFFF)
        if hex_content_upper_offset == 65535:
            print(f"Done writing to {os.path.basename(destination_path)}, total pointers overwritten = {pointers_overwritten}\n")
            # return None
            break

        # Update our next pointer location if it was changed (only do this if the content is already added)
        #if hex_content_upper_offset >= hex_location_section:
            # hex_content_upper_offset = new_upper_offset

        # Going to next pointer location
        current_location = hex((int(hex_content_upper_offset) * 4) + force_offset)
        hex_content = read_hex_from_offset(file_path, current_location, num_bytes)
        current_line = current_line + 1
    else:
        error_message("Error, couldn't find pointer.")
        exit(1)

    # Overwriting base file
    if args.overwrite and not args.keep_main and destination_path != args.main_file:
        # Deleting base file
        if os.path.exists(args.main_file):
            os.remove(args.main_file)

        # Copying temp to base
        shutil.copy(destination_path, args.main_file)

        # Deleting temp file
        if os.path.exists(destination_path):
            os.remove(destination_path)
        print(f"Finished modifying {os.path.basename(args.main_file)}.")
    else:
        print(f"Finished modifying {os.path.basename(destination_path)}.")
    return None

def create_output_file(destination_path):
    """
    Creates main character output file. 
    Will create a duplicate if overwriting that will replace the main file later in the program.
    
    Args:
        destination_path (str): Main character file.

    Returns:
        None
    """
    if destination_path == args.main_file:
        return destination_path

    # Setting temp output if we're overwriting
    if args.main_file == args.o and args.overwrite == True:
        destination_path = args.o+"temp"#os.path.join(current_directory, output_path)

    # Checking if our output is proper (we overwrite later so source and output need to be diff here)
    if args.main_file == destination_path and not args.overwrite and args.keep_main:
        error_message(f"Error: The file '{args.main_file}' is the same as the output '{destination_path}'; current argument output = '{args.o}'.")
        exit(1)

    # Deleting output file 
    if os.path.exists(destination_path):
        os.remove(destination_path)

    # Copy the file
    shutil.copy(args.main_file, destination_path)
    if args.debug:
        print(f"File '{os.path.basename(args.main_file)}' copied and renamed to '{os.path.basename(args.o)}' successfully.")
    return destination_path

if __name__ == "__main__":
    args.main_file = args.file
    if args.main_file == "":
        error_message(f"No main file set, {args.main_file}.")
        exit(1)

    try:
        # Setting variables
        offset_to_add = 0
        if args.add == "":
            offset_to_add = (int(args.subtract, 16) * -1)
        else:
            offset_to_add = int(args.add, 16)
        if offset_to_add < 4 and offset_to_add > -4:
            error_message(f"Add size '{args.add}' or subtract size '{args.subtract}' not adequate, has to at least be 4.")
            exit(1)
        else:
            offset_to_add = int(offset_to_add / 4)
        
        first_pointer = find_first_pointer_original_character(args.main_file)

        if args.offset == "-1" or args.offset == "0x0":
            error_message(f"Offset not set, {args.offset}.")
            exit(1)
        
        destination_path = create_output_file(args.o)

        # Getting 4 bytes from first pointer
        hex_content = read_hex_from_offset(args.main_file, first_pointer, 4)
        current_location = first_pointer
        hex_location_section = int(args.offset, 16) / 4

        update_main_pointer_data(args.main_file,destination_path,hex_content,current_location,hex_location_section,offset_to_add,args.req_file)

        # Overwriting base file
        if args.overwrite:
            # Deleting base file
            if os.path.exists(args.main_file):
                os.remove(args.main_file)

            # Copying temp to base
            shutil.copy(destination_path, args.main_file)

            # Deleting temp file
            if os.path.exists(destination_path):
                os.remove(destination_path)
            print(f"Finished modifying {os.path.basename(args.main_file)}.")
        else:
            print(f"Finished modifying {os.path.basename(destination_path)}.")

    except FileNotFoundError as e:
        error_message(f"{e}")
        exit(1)
    except Exception as e:
        error_message(e)
        exit(1)