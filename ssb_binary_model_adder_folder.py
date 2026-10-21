# Adds binary data to a ssb model file from a folder while adding offset to all pointers affected.
# Especially useful for models converted for RAM use by Model2F3DEX-SSB.

# Copyright (C) 2025 Thomas Rader


import shutil
import os
import subprocess
from inspect import currentframe, getframeinfo
from ssb_binary_model_adder_arguments import args
from ssb_binary_model_functions import read_hex_from_offset

def error_message(e,cf=currentframe()):
    print(f'File "{os.path.basename(getframeinfo(cf).filename)}", line {cf.f_lineno}, An error occurred: \n{e}\n')

# Finds first E7 command offset
def find_op_index(file_path):
    # Setting variables
    reading_loc = "0x00"
    file_size = int(os.path.getsize(file_path))
    reading_loc_hex = hex(int(reading_loc, 16))
    data = read_hex_from_offset(file_path, reading_loc_hex, 8)

    while 1:
        # Setting decimal value for location
        reading_loc_dec = int(reading_loc_hex,16)

        # Finding E7 command
        if str(data[:8]).upper() == "E7000000":
            return reading_loc_hex

        # No more to read, exiting
        if reading_loc_dec >= file_size:
            print("Couldn't find indexes, exiting.")
            break

        # Reading next 8 bytes
        reading_loc = hex(int(reading_loc, 16) + 8)
        reading_loc_hex = hex(int(reading_loc,16))
        data = read_hex_from_offset(file_path, reading_loc_hex, 8)
    return "0x00"

def add_files():
    """
    Adds multiple files within given directory to a binary F3DEX2 file.

    Args:
        None

    Returns:
        None

    TODO: Add arguments instead of using args
    """
    try:
        # Get the current working directory
        current_directory = os.getcwd()

        # Copy the file
        source_path = os.path.join(current_directory,args.file)
        destination_path = os.path.join(current_directory,args.o)

        # Setting temp output if we're overwriting
        if args.file == args.o and args.overwrite == True:
            output_path = args.o+"temp"
            destination_path = os.path.join(current_directory, output_path)

        if args.file == args.o:
            error_message(f"The file '{args.file}' is the same as the output '{args.o}'.")
            exit(1)

        # Deleting output file 
        if os.path.exists(destination_path):
            os.remove(destination_path)
            
        # Copy the file
        shutil.copy(source_path, destination_path)
        if args.debug:
            print(f"File '{os.path.basename(args.file)}' copied and renamed to '{os.path.basename(args.o)}' successfully.")

        # Construct full paths for source and destination
        folder_to_add_path = os.path.join(current_directory, args.folder_to_add)
        folder_directory = os.fsencode(folder_to_add_path)
        last_file_sizes = 0

        # Debug printing
        print(f"~Adding to {args.o}~")

        # Going through folder
        if os.path.isdir(folder_to_add_path):
            for file in os.listdir(folder_directory):
                # Setting file location
                filename = os.fsdecode(file)
                file_to_add_path = os.path.join(folder_to_add_path,filename)
                file_path = os.path.join(current_directory,args.o)

                # Checking offset
                if args.offset == "-1":
                    file_size = int(os.path.getsize(file_path))
                    hex_location = hex(file_size)
                else:
                    hex_location = hex(int(args.offset,16) + last_file_sizes)
                    file_size = int(os.path.getsize(file_to_add_path))
                    last_file_sizes = last_file_sizes + file_size

                # Getting first op command for printing help
                op_index = find_op_index(file_to_add_path) 
                op_index = hex(int(op_index,16)+int(hex_location,16))
                op_index_segmented = hex(int(int(op_index,16) / 4))

                # Debug printing
                if args.debug:
                    print(f"{hex_location}: Adding {filename} to {args.o}; E7 at {op_index} ({op_index_segmented})")
                else:
                    print(f"--{hex_location}: Adding {filename}; E7 at {op_index} ({op_index_segmented})")

                # Adding file here
                current_python_file_directory = os.path.dirname(os.path.realpath(__file__))
                python_file_path = os.path.join(current_python_file_directory, "ssb_binary_model_adder.py")
                arguments = ["-file", args.o, "-file_to_add", file_to_add_path, "-add", args.add, "-subtract", args.subtract, "-offset", hex_location, "-first_pointer", args.first_pointer, "-first_pointer_file_to_add", args.first_pointer_file_to_add, "-palette_costume", args.palette_costume, "-original_character_offset", args.original_character_offset, "-original_character_file_size", args.original_character_file_size, "-main_file", args.main_file, "-req_file", args.req_file, "-python", args.python, "-output", args.o]
                if args.debug:
                    arguments.append("-debug")
                if args.no_convert:
                    arguments.append("-no_convert")
                if args.no_main:
                    arguments.append("-no_main")
                if not args.overwrite:
                    arguments.append("-keep_main")
                # Forcing overwrite
                arguments.append("-overwrite")

                command = [args.python, python_file_path] + arguments
                # # Converting file_to_add
                # result = subprocess.run(command, capture_output=True, text=True)

                # # Printing output
                # if args.debug:
                #     print(f"~Output from {args.o}:~\n\n{result.stdout}")
                #     if (result.stderr):
                #         print(f"~Errors from {args.o}:~\n\n{result.stderr}")

                # Converting file_to_add
                process = subprocess.Popen(command,stdout=subprocess.PIPE,text=True)
                
                # Printing output
                if args.debug:
                    print(f"~Output from {args.o}:~\n\n")
                    for line in process.stdout:
                        print(line, end="")

                else:
                    for line in process.stdout:
                        # Printing input lines
                        if "Enter " in line:
                            print(line)
                        continue

                process.wait()
                    
            # Deleting temporary file we used to modify pointers with
            if os.path.exists(args.o+"temp"):
                os.remove(args.o+"temp")
                if args.debug:
                    print(f"Removing {args.o}temp")
        else:
            error_message(f"The destination given '{folder_to_add_path}' is not a folder, exiting.")
            exit(1)
    except FileNotFoundError as e:
        error_message(f"File not found: {e}")
        exit(1)
    except Exception as e:
        error_message(f"{e}")
        exit(1)

        
    # Overwriting base file
    if args.overwrite:
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

if __name__ == "__main__":
    add_files()