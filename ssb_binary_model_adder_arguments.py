# Arguments for ssb_binary_model_adder.py

# Copyright (C) 2025 Thomas Rader

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-file","--file",required=True,type=str,help="File we're expanding (pointers here need to be connected).")
parser.add_argument("-file_to_add","--file_to_add",default="",type=str,help="File to add.")
parser.add_argument("-folder_to_add","--folder_to_add",default="",type=str,help="Folder to add.")
parser.add_argument("-offset","--offset","-location","--location",default="-1",type=str,help="Hexadecimal location of where we're adding the file in the binary (as a string, ex: '0xA4').")
parser.add_argument("-add","--add",default="",type=str,help="Adds certain amount from pointers that point past given offset. (as a string, ex: '0x8A')")
parser.add_argument("-subtract","--subtract",default="",type=str,help="Subtracts certain amount from pointers that point past given offset. (as a string, ex: '0x8A')")
parser.add_argument("-first_pointer","--first_pointer","-internal_file_table_offset","--internal_file_table_offset",default="-1",type=str,help="First pointer to start checking (usually following the first FD command) (as a string, ex: '0xA4').")
parser.add_argument("-first_pointer_file_to_add","--first_pointer_file_to_add","-internal_file_table_offset_fta","--internal_file_table_offset_fta",default="-1",type=str,help="First pointer in the file we're adding, if -2 then we don't change any pointers (usually following the first FD command) (as a string, ex: '0xA4').")
parser.add_argument("-no_convert","--no_convert",action="store_true",help="Prevents converting the binary file_to_add from a single pointer to a 2 pointer command.")
parser.add_argument("-palette_costume","--palette_costume","-costume","--costume",default="",help="Changes FD1 (palette) command with DE000000 0EXXXXXX to make palette based on costume palette. Enter entire DE command, ex DE0000000E000000.")
parser.add_argument("-debug","--debug",action="store_true",help="Prints debugging messages to output.")
parser.add_argument("-python","--python","-python_version","--python_version",default="python3",type=str,help="Python version or location to run python commands with.")
parser.add_argument("-overwrite","--overwrite","-force","--force",action="store_true",help="Forces overwrite, making output go to -file.")
parser.add_argument("-o","--o","-output","--output",default="output.bin",type=str,help="Output file.")

args = parser.parse_args()