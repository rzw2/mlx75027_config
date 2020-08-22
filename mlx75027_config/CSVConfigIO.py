"""
Refael Whyte, r.whyte@chronoptics.com

This is the functions for parsing the csv files that contain the register configurations. 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import csv


def calc_bits(offset, size):
    """
    Generates the string of where the bits of that property in a register live 

    Parameters
    ----------
    offset : int,  
    size : int, 

    Returns 
    ----------
    ret_str : str, the string
    """

    # Generate the register bits
    if size == 1:
        ret_str = "[" + str(offset) + "]"
    else:
        top_bit = offset + size - 1
        ret_str = "[" + str(top_bit) + ":" + str(offset) + "]"

    return ret_str


def dict_to_registers(reg_dict):
    """
    Converts the input dictionary to a dictionary of registers 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the information from the CSV file

    Returns 
    ----------
    reg : dict, dictionary where the keys are the register and the values are the register value
    """
    # We convert a dictionary to the register values
    reg = {}
    for k in reg_dict:
        if not reg_dict[k][4] in reg:
            reg[reg_dict[k][4]] = 0
        # Now
        reg[reg_dict[k][4]] |= (int(reg_dict[k][2]) << int(reg_dict[k][0]))
    return reg


def registers_to_dict(reg_dict, reg):
    """
    Updates an existing dictionary with new register values 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the information from the CSV file
    reg : dict, the dictionary of registers and values 
    """

    # We convert a registers to and update an existing dictionary
    for k in reg_dict:
        mask = (2**(reg_dict[k][1]))-1
        try:
            reg_dict[k][2] = (reg[reg_dict[k][4]] >> reg_dict[k][0]) & mask
        except KeyError:
            pass
    return


def csv_export_registers(outFile, reg_dict):
    """
    Export the registers and their values to a csv file

    Parameters
    ----------
    outFile : str, the CSV file to write the register values to
    reg_dict : dict, the dictionary that contains all the information from the CSV file

    """
    registers = dict_to_registers(reg_dict)
    fieldnames = ["Register", "Value"]
    with open(outFile, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for reg in registers:
            row_dict = {"Register": "0x{:04X}".format(
                reg), "Value": "0x{:02X}".format(registers[reg])}
            writer.writerow(row_dict)
    return


def csv_export(outFile, reg_dict):
    """
    Export the csv file and configuration. 

    Parameters
    ----------
    outFile : str, the CSV file to write the data to
    reg_dict : dict, the dictionary that contains all the information from the CSV file

    """
    with open(outFile, 'w', newline='') as csvfile:
        # Write the headers.
        fieldnames = ["Section", "RegisterNumber", "Bits",
                      "Property", "Description", "ValueMeaning", "Value"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for reg in reg_dict.keys():

            bits = calc_bits(reg_dict[reg][0], reg_dict[reg][1])
            row_dict = {
                "Property": reg,
                "Value": reg_dict[reg][2],
                "RegisterNumber": "0x{:04X}".format((reg_dict[reg][4])),
                "Bits": bits,
                "ValueMeaning":  reg_dict[reg][5],
                "Description": reg_dict[reg][3],
                "Section": reg_dict[reg][6]}
            writer.writerow(row_dict)
    return


def csv_import(infile):
    """
    Export the csv file and configuration. 

    Parameters
    ----------
    infile : str, the CSV file to read from 

    Returns
    ----------
    reg_dict : dict, the dictionary of everything 
    """

    reg_dict = {}
    translation_table = dict.fromkeys(map(ord, '[]'), None)
    with open(infile) as csvfile:
        spamreader = csv.reader(csvfile)
        # Read the header
        for row in spamreader:
            # print(str(row))
            if row[1] != '' and spamreader.line_num > 1:
                reg_num = int((row[1]), 0)

            if row[3] != '' and row[3] != 'invalid' and row[3] != 'reserved' and spamreader.line_num > 1:

                bits = row[2]
                t0 = bits.split(':')
                if len(t0) == 1:
                    offset = int(float(bits[1:-1]))
                    size = 1
                else:
                    high_bit = int(
                        float(t0[0].translate(translation_table)))
                    low_bit = int(
                        float(t0[1].translate(translation_table)))

                    offset = low_bit
                    size = high_bit - low_bit + 1

                section = row[0]
                value = int(float(row[6]))
                desc = row[4]
                value_meaning = row[5]
                reg_dict[row[3]] = [offset, size, value,
                                    desc, reg_num, value_meaning, section]

    return reg_dict
