
import numpy as np


def reg16_to_value(reg_dict, reg0, reg1):
    """
    Convert the input two 8 bit registers to a single 16bit value 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    reg0 : str, the name of the register in the dictionary of the low value 
    reg1 : str, the name of the register in the dictionary of the high value 

    Returns 
    ----------
    value : int, the combined 16bit value 
    """
    value = np.left_shift(reg_dict[reg1][2], 8) | reg_dict[reg0][2]
    return value


def reg_to_value(reg_dict, reg0, reg1, reg2, reg3):
    """
    Convert the input four 8 bit registers into a single 32it value 

    Parameters
    ----------
    reg_dict : dict 
        the dictionary that contains all the register information 
    reg0 : str 
        the name of the register in the dictionary of the low [7:0] bits
    reg1 : str 
        the name of the register in the dictionary of the [15:8] bits
    reg2 : str 
        the name of the register in the dictionary of the [23:16] bits
    reg3 : str 
        the name of the register in the dictionary of the high [31:24] btis

    Returns 
    ----------
    value : int 
        the combined 32bit value 
    """
    value = np.left_shift(reg_dict[reg3][2], 24) | np.left_shift(
        reg_dict[reg2][2], 16) | np.left_shift(reg_dict[reg1][2], 8) | reg_dict[reg0][2]
    return value


def value16_to_reg(reg_dict, value, hi_reg, low_reg):
    val16 = np.uint16(value)
    hi_val = np.right_shift(val16, 8)
    low_val = val16 & 0x00FF
    reg_dict[hi_reg][2] = hi_val
    reg_dict[low_reg][2] = low_val
    return


def value32_to_reg(reg_dict, value, reg0, reg1, reg2, reg3):
    # Write a value into difference registers
    val32 = np.uint32(value)
    val3 = np.right_shift(val32, 24) & 0xFF
    val2 = np.right_shift(val32, 16) & 0xFF
    val1 = np.right_shift(val32, 8) & 0xFF
    val0 = val32 & 0xFF
    #
    reg_dict[reg0][2] = val0
    reg_dict[reg1][2] = val1
    reg_dict[reg2][2] = val2
    reg_dict[reg3][2] = val3
    return


def reg24_to_value(reg_dict, reg0, reg1, reg2):
    value = np.left_shift(reg_dict[reg2][2], 16) | np.left_shift(
        reg_dict[reg1][2], 8) | reg_dict[reg0][2]
    return value


def value24_to_reg(reg_dict, value, reg0, reg1, reg2):
    val32 = np.uint32(value)
    val2 = np.right_shift(val32, 16) & 0xFF
    val1 = np.right_shift(val32, 8) & 0xFF
    val0 = val32 & 0xFF

    reg_dict[reg0][2] = val0
    reg_dict[reg1][2] = val1
    reg_dict[reg2][2] = val2
    return
