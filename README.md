<div align="center">
    
# SSB64 Model Appender
Converts binary model pointers from RAM usage to ROM usage, and/or can append it to another file while updating pointers. <br>

(Especially great if you use [Model2F3DEX-SSB](http://n64vault.com/ssb-tools:model2f3dex-ssb))

This was used to help create [San Antonio Remix v2.0.0](https://github.com/OhThomas/smashremix/releases/tag/Latest)

<a href="https://github.com/OhThomas/smashremix/releases/tag/Latest">
    <img src="dddcowboy.png" alt="Cowboy DDD" style="width:150px; height:auto;">
</a>

## Usage
| Case | Example |
| :------- | :------- |
| Append a RAM model: | `python ssb_binary_model_adder.py -file peppy_cowboy.bin -file_to_add peppy_cowboy_cig.bin`|
| Append a ROM model: | `python ssb_binary_model_adder.py -file peppy_cowboy.bin -file_to_add peppy_cowboy_cig_ROM.bin -no_convert`|
| Edit pointer data in a model file without appending anything (adding 0x8 to every pointer): | `python ssb_binary_model_adder.py -file jigglypuff_microphone.bin -add 0x08 -offset 0x0`|
| Subtract (subtracting 0x8 from every pointer that points past 0x8380): | `python ssb_binary_model_adder.py -file jigglypuff_microphone.bin -subtract 0x08 -offset 0x8380`|
|Convert a model file with RAM addresses (changes pointers based on new offset 0x7370): | `python ssb_binary_model_converter.py -file peppy_cowboy_hat.bin -offset 0x7370`|
| Append a model to a specific location (0x8380) within a file: | `python ssb_binary_model_adder.py -file peppy_cowboy.bin -file_to_add peppy_cowboy_cig.bin -offset 0x8380`|

## Arguments
| Argument | Description |
| :------- | :------- |
| -file | File we're appending to (pointers here need to be connected).|
| -file_to_add | File we're adding.|
| -offset | Hexadecimal location of where we're adding the file in the binary; every pointer pointing past this location will be changed (as a string, ex: '0xA4').|
| -add | Adds certain amount from pointers that point past given offset. (as a string, ex: '0x8A')|
| -subtract | Subtracts certain amount from pointers that point past given offset. (as a string, ex: '0x8A')|
| -first_pointer | First pointer to start checking (usually following the first FD command) (as a string, ex: '0xA4').|
| -first_pointer_file_to_add | First pointer in the file we're adding, if -2 then we don't change any pointers (usually following the first FD command) (as a string, ex: '0xA4').|
| -no_convert | Prevents converting the binary file_to_add from a single pointer to a 2 pointer command.|
| -debug | Prints debugging messages to output.|
| -python | Python version or location to run python commands with.|
| -overwrite | Forces overwrite, making output go to -file.|
| -output | Output file.|

## License
Copyright (C) 2025 Thomas Rader
</div>
