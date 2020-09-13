"""
Refael Whyte, r.whyte@chronoptics.com

Calculating the EPC660 settings from the register values.

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import numpy as np
import warnings

from mlx75027_config import value16_to_reg


def epc_set_external_mod(reg_dict, external):
    """
    Set the external modulation of the EPC660 image sensor. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    external : bool
        0, Use internal modulation. 1, use external modulation 
    """
    if external:
        reg_dict["mod_clk_src"][2] = 1
    else:
        reg_dict["mod_clk_src"][2] = 0
    return


def epc_calc_external_mod(reg_dict):
    """
    Returns the current setting of external modulation. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    bool 
        The external modulation settings. 0 use internal modulation, 1 use external. 
    """
    return bool(reg_dict["mod_clk_src"][2])


def epc_calc_mod_freq(reg_dict, mclk, demod_clk):
    """
    Calculates the modulation frequency of the EPC660 sensor

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mclk : float
        The mclk in MHz
    demod_clk : float
        The demod clock in MHz, this is required if using the external clock input

    Returns
    ----------
    float
        The modulation frequency in MHz
    """
    external_mod = epc_calc_external_mod(reg_dict)
    if external_mod is False:
        f_mod_clk = (mclk) / (reg_dict["mod_clk_div"][2]+1)
        f_led = f_mod_clk / 4.0
    else:
        f_led = demod_clk / 4.0
    return f_led


def epc_calc_closest_mod_freq(mod_freq_mhz, mclk):
    """
    Calculate the closest possible modulation frequency from the desired. 
    This can only be used with internal modulation. 

    Parameters
    ----------
    mod_freq_mhz : float
        The desired modulation frequency in MHz 
    mclk : float
        The mclk frequency in MHz 

    Returns
    ----------
    int
        The divider settings to use. 
    float
        The actual modulation frequency
    """
    # We calculate the nearest modulation frequency
    fmod_clk = mod_freq_mhz * 4.0
    mod_clk_div_p1 = mclk / fmod_clk
    mod_clk_div = np.uint8(np.round(mod_clk_div_p1 - 1.0))

    # Now calculate the actual modulation frequency
    f_act = (mclk/(mod_clk_div+1)) / 4.0
    return mod_clk_div, f_act


def epc_set_mod_freq(reg_dict, fmod, mclk):
    """
    We set the mod_clk_div to set for the closest modulation frequency. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    fmod : float
        The desired modulation frequency in MHz
    mclk : float
        The mclk in MHz
    """

    external_mod = epc_calc_external_mod(reg_dict)
    if external_mod:
        # We are using external modulation, no registers to set,
        # as the modulation is demod_clk/4.0
        return

    mod_clk_div, f_act = epc_calc_closest_mod_freq(fmod, mclk)
    # Set the divider values.
    reg_dict["mod_clk_div"][2] = mod_clk_div
    return


def epc_calc_hdr(reg_dict):
    """
    Returns True if high dynamic range is enabled, False otherwise

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    bool
        True if HDR enabled, false otherwise
    """
    hdr_enabled = (reg_dict["pixel_mode"][2] == 1) and (
        reg_dict["dual_int_mode"][2] == 1)
    return hdr_enabled


def epc_calc_dual_phase(reg_dict):
    """
    Returns True if dual phase mode is enabled, False otherwise

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    bool
        True if dual phase enabled, false otherwise
    """
    dual_phase = (reg_dict["mod_sel"][2] == 0) and (
        reg_dict["num_dcs"][2] == 1) and (reg_dict["pixel_mode"][2] == 1) and (reg_dict["dual_int_mode"][2] == 1)
    return dual_phase


def epc_calc_common_mode(reg_dict):
    """
    Returns True if common mode is enabled, False otherwise

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    bool
        True if common mode enabled, false otherwise
    """
    cm_enabled = reg_dict["num_dcs"][2] == 0 and reg_dict["mod_sel"][2] == 3
    return cm_enabled


def epc_set_mode(reg_dict, dual_phase, common_mode, hdr):
    """
    Set the operating mode of the EPC660 sensor.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    dual_phase : bool
        The dual phase mode
    common_mode : bool
        Common Mode
    hdr : bool
        High Dynamic Range mode.
    """
    if dual_phase:
        reg_dict["mod_sel"][2] = 0
        reg_dict["num_dcs"][2] = 1
        reg_dict["pixel_mode"][2] = 1
        reg_dict["dual_int_mode"][2] = 1
    else:
        reg_dict["dual_int_mode"][2] = 0
        reg_dict["dual_int_mode"][2] = 0

        if common_mode:
            reg_dict["num_dcs"][2] = 0
            reg_dict["mod_sel"][2] = 3
        else:
            reg_dict["num_dcs"][2] = 3
            reg_dict["mod_sel"][2] = 0

        if hdr:
            reg_dict["pixel_mode"][2] = 1
            reg_dict["dual_int_mode"][2] = 1
        else:
            reg_dict["pixel_mode"][2] = 0
    return


def epc_set_phase_steps(reg_dict, seq):
    """
    Set the sequence of the phase steps to capture
    """

    if np.size(seq) != 4:
        raise RuntimeError("Require input sequence of size 4!")

    for s in seq:
        if s < 0 or s > 3:
            raise RuntimeError(
                "Each sequence must be between 0 and 3! Only 4 possible phase steps!")

    dual_phase = epc_calc_dual_phase(reg_dict)
    if dual_phase:
        for n in range(0, 4):
            reg_dict["dcs_mgx1_{:d}".format(n)][2] = np.uint8(seq[n])
    else:
        for n in range(0, 4):
            reg_dict["dcs_mgx0_{:d}".format(n)][2] = np.uint8(seq[n])
    return


def epc_calc_phase_steps(reg_dict):
    """
    Returns the order of the phase steps being captured. 
    """

    dual_phase = epc_calc_dual_phase(reg_dict)

    if dual_phase:
        # Dual Phase DCS
        seq = np.array([reg_dict["dcs_mgx1_0"][2], reg_dict["dcs_mgx1_1"]
                        [2], reg_dict["dcs_mgx1_2"][2], reg_dict["dcs_mgx1_3"][2]])
    else:
        # 4 DCS - normal ToF
        seq = np.array([reg_dict["dcs_mgx0_0"][2],
                        reg_dict["dcs_mgx0_1"][2],
                        reg_dict["dcs_mgx0_2"][2],
                        reg_dict["dcs_mgx0_3"][2]])
    return seq


def epc_calc_int_times(reg_dict, mclk, demod_clk):
    """
    Calculate the integration time of each raw frame. In high dynamic range
    mode returns both integration times.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mclk : float
        The mclk in MHz
    demod_clk : float
        The external demod clock in MHz

    Returns
    ----------
    int_times : list[float]
        The integration times, the length of the list is the number of integration times
    """

    int_times = []

    int_len = reg_dict["int_len_hi"][2]*256 + reg_dict["int_len_low"][2]
    int_mult = reg_dict["int_mult_hi"][2]*256 + reg_dict["int_mult_low"][2]

    if reg_dict["mod_clk_src"][2] == 0:
        int_time = float(reg_dict["mod_clk_div"][2] + 1) / \
            (mclk*1e3) * (int_len+1)*int_mult
    else:
        int_time = (1.0 / (demod_clk*1e3)) * (int_len+1)*int_mult

    int_times.append(int_time)

    # If we are using HDR mode.
    hdr_mode = epc_calc_hdr(reg_dict)
    if hdr_mode:
        int_len2 = reg_dict["int_len2_hi"][2]*256 + reg_dict["int_len2_low"][2]

        if reg_dict["mod_clk_src"][2] == 0:
            int_time2 = float(reg_dict["mod_clk_div"][2] + 1) / \
                (mclk*1e3) * (int_len2+1)*int_mult
        else:
            int_time2 = (1.0 / (demod_clk*1e3)) * (int_len2+1)*int_mult
        int_times.append(int_time2)

    return int_times


def epc_set_int_times(reg_dict, int_time_ms, mclk, demod_clk):
    """
    Set the integration time of each frame.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    int_times_ms : np.array
        The integration times in milliseconds.
    mclk : float
        The mclk in MHz
    demod_clk : float
        The external clock frequency in MHz
    """

    if np.ndim(int_time_ms) == 0:
        int_time_ms = np.array([int_time_ms])
    if type(int_time_ms) == list:
        int_time_ms = np.array(int_time_ms)

    if np.size(int_time_ms) > 2:
        raise RuntimeError("Can only do 1 or 2 integration times")

    # Check if using demod clk or mclk
    if reg_dict["mod_clk_src"][2] == 0:
        int_total = np.int32((int_time_ms*mclk*1e3) /
                             (reg_dict["mod_clk_div"][2]+1))
    else:
        int_total = np.uint32((int_time_ms*demod_clk*1e3))

    # The multiplier is constant between the two values, if hdr is enabled
    # If HDR is not enabled then find the biggest and best multipler
    if np.size(int_time_ms) == 1:
        pos_mult = np.arange(1, 1023)
        mult_work = np.nonzero(np.mod(int_total[0], pos_mult) == 0)
        int_mult = mult_work[0][-1] + 1

    elif np.size(int_time_ms) == 2:
        if (int_time_ms[0] == int_time_ms[1]):
            pos_mult = np.arange(1, 1023)
            mult_work = np.nonzero(np.mod(int_total[0], pos_mult) == 0)
            int_mult = mult_work[0][-1] + 1
        else:
            # We now need to do this but as a vector
            pos_mult = np.tile(np.reshape(np.arange(1, 1023), (-1, 1)), (1, 2))
            com_mult = (np.mod(int_total, pos_mult) == 0)
            # Now find the highest pair [True,True] in com_mult
            use_ind = 0
            for n in range(0, 1022):
                if (com_mult[n, 0] == True and com_mult[n, 1] == True):
                    use_ind = n
            int_mult = use_ind + 1

            # int_mult = np.floor( np.max(int_total) / np.min(int_total) )

    if int_mult == 0:
        int_mult = 1.0
    elif int_mult > 0x03FF:
        int_mult = 0x03FF

    int_len = (int_total / int_mult) - 1.0
    if np.any(int_len > (2**16 - 1)):
        warnings.warn("Integration time too long! Saturating")
        int_len[int_len > (2**16 - 1)] = (2**16 - 1)

    # Set the registers
    value16_to_reg(reg_dict, np.uint16(
        int_len[0]), "int_len_hi", "int_len_low")
    if np.size(int_len) == 2:
        value16_to_reg(reg_dict, np.uint16(
            int_len[1]), "int_len2_hi", "int_len2_low")
    value16_to_reg(reg_dict, np.uint16(int_mult),
                   "int_mult_hi", "int_mult_low")
    return


def epc_set_binning(reg_dict, row_binning, col_binning):
    """
    Set the EPC660 binning. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    row_binning : int 
        The row binning setting. 
    col_binning : int 
        The column binning setting
    """
    if row_binning < 0 or row_binning > 3:
        raise RuntimeError("Invalid row binning mode!")
    if col_binning < 0 or col_binning > 1:
        raise RuntimeError("Invalid column binning mode!")

    reg_dict["row_rudy"][2] = row_binning
    reg_dict["col_rudx"][2] = col_binning
    return


def epc_calc_binning(reg_dict):
    """
    Calculates the row and column binning values 
    nrows = (rows) /(1 << binning)
    ncols = (cols) /(1 << binning) 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns 
    ----------
    int
        The row binning settings
    int 
        The column binning settings 
    """
    return reg_dict["row_rudy"][2], reg_dict["col_rudx"][2]


def epc_set_bin_mode(reg_dict, row_bin, col_bin):
    """
    Set the binning mode to enable/disable binning in the rows and columns. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    row_bin : bool 
        0, no row binning. 1, enables row binning 
    col_bin : bool 
        0, no column binning. 1, enables column binning 
    """
    bin_mode = np.uint8(0)
    if col_bin:
        bin_mode = bin_mode | 0x01
    if row_bin:
        bin_mode = bin_mode | 0x02

    reg_dict["bin_mode"][2] = bin_mode
    return


def epc_calc_bin_mode(reg_dict):
    """
    Get the current binning modes 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    bool 
        Row binning mode
    bool
        Column binning mode 
    """
    bin_mode = reg_dict["bin_mode"][2]
    col_bin = bool(bin_mode & 0x01)
    row_bin = bool(bin_mode & 0x02)
    return row_bin, col_bin


def epc_calc_roi(reg_dict):
    """
    Get the current region on interest (ROI) of the image sensor 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    col_start : int 
        The column start of readout 
    col_end : int 
        The column end
    row_start : int 
        The row start 
    row_end : int 
        The row end 
    """
    col_start = reg_dict["roi_top_leftx_hi"][2] * \
        256 + reg_dict["roi_top_leftx_low"][2]
    col_end = reg_dict["roi_bot_rightx_hi"][2] * \
        256 + reg_dict["roi_bot_rightx_low"][2]
    row_start = reg_dict["roi_top_lefty"][2]
    row_end = reg_dict["roi_bot_righty"][2]
    return col_start, col_end, row_start, row_end


def epc_set_roi(reg_dict, col_start, col_end, row_start, row_end):
    """
    Set the region on interest (ROI) for the image sensor 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    col_start : int 
        The column start of readout 
    col_end : int 
        The column end
    row_start : int 
        The row start 
    row_end : int 
        The row end. Which is 125 as the readout is mirrored around this row.  
    """
    if col_start < 0 or col_start > 327:
        raise RuntimeError("Column start must be between 0 and 328")
    if col_end < 0 or col_end > 327:
        raise RuntimeError("Column end must be between 0 and 328")
    if row_start < 0 or row_start > 125:
        raise RuntimeError("Row start must be between 0 and 125")
    if row_end < 0 or row_end > 125:
        raise RuntimeError("Row end must be between 0 and 125")

    if row_start > row_end:
        raise ValueError("Row readout must start before end")
    if col_start > col_end:
        raise ValueError("Col readout must start before end")

    value16_to_reg(reg_dict, np.uint16(col_start),
                   "roi_top_leftx_hi", "roi_top_leftx_low")
    value16_to_reg(reg_dict, np.uint16(col_end),
                   "roi_bot_rightx_hi", "roi_bot_rightx_low")
    reg_dict["roi_top_lefty"][2] = np.uint8(row_start)
    reg_dict["roi_bot_righty"][2] = np.uint8(row_end)
    return


def epc_calc_light_phase(reg_dict, mclk, demod_clk, radians=False):
    """
    Calculate the phase offset of the DLL of the light source. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mclk : float
        The mclk frequency in MHz 
    demod_clk : float
        The external clock frequency in MHz 
    radians : bool, optional 
        Defaults to False, to return phase in degrees, set to True to return in radians
    """
    if radians:
        fc = 2*np.pi
    else:
        fc = 360.0

    f_led = epc_calc_mod_freq(reg_dict, mclk, demod_clk)
    if reg_dict["dll_crt"][2] == 1:
        light_phase = 0
        fine_phase = 0
    elif reg_dict["dll_crt"][2] == 4:
        light_phase = reg_dict["coarse_dll"][2]
        fine_phase = reg_dict["fine_dll_hi"][2] * \
            256 + reg_dict["fine_dll_low"][2]
    # Show mode of camera.
    # print("Light Phase: " + str(light_phase))
    light_phase_ns = light_phase * 2.0 + fine_phase * 10e-3
    p_led = (1.0 / f_led) * 1e3  # Is the modulation period in ns
    phase_offset = (light_phase_ns / p_led) * fc
    return phase_offset


def epc_setup_light_phase(reg_dict, phase_desired, mclk, demod_clk, radians=False):
    """
    Set the DLL on the EPC660 to set the desired phase. 

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mclk : float 
        The internal clock frequency in MHz 
    demod_clk : float
        The external input clock frequency in MHz 
    phase_desired : float
        The desired phase of the output of the DLL 
    radians : bool, optional 
        Defaults to False, set to True to set the desired phase in radians. 
    """
    if radians:
        fc = 2*np.pi
    else:
        fc = 360.0

    if phase_desired == 0:
        reg_dict["dll_crt"][2] = 1
        return

    f_led = epc_calc_mod_freq(reg_dict, mclk, demod_clk)
    # For a given modulation frequency calculate the registers for the light phase
    p_led = (1.0 / f_led) * 1e3
    # The period in ns
    ph_time = (phase_desired/fc) * p_led
    coarse = np.floor(ph_time / 2.0)
    if coarse > 49:
        coarse = 49

    fine_time = ph_time - (2.0 * coarse)
    fine = np.round(fine_time / (10.0*1e-3))
    if fine > 799:
        fine = 799

    # Now check are possible in register settings
    reg_dict["dll_crt"][2] = 4  # Enable DLL
    reg_dict["coarse_dll"][2] = np.uint8(coarse)
    value16_to_reg(reg_dict, fine, "fine_dll_hi", "fine_dll_low")
    return


def epc_calc_roi_coordinates(reg_dict):
    """
    Calculates the coordinates of the two ROI in the EPC660 readout. 
    """
    col_start, col_end, row_start, row_end = epc_calc_roi(reg_dict)
    top_left = [row_start, col_start]
    bottom_right = [row_end, col_end]

    row_width = (row_end-row_start)
    x1_dash = 251-row_start
    x2_dash = x1_dash - row_width

    top_left_dash = [x2_dash, col_start]
    bottom_right_dash = [x1_dash, col_end]

    return top_left, bottom_right, top_left_dash, bottom_right_dash


def epc_calc_img_size(reg_dict):
    """
    Calcalute the output image size from the EPC660 sensor

    Parameters
    ----------
    reg_dict : dict

    Returns 
    ----------
    int 
        The number of rows 
    int
        The number of columns in the image 
    """
    col_start, col_end, row_start, row_end = epc_calc_roi(reg_dict)
    row_bin, col_bin = epc_calc_bin_mode(reg_dict)
    row_binning, col_binning = epc_calc_binning(reg_dict)

    row_div = 1
    col_div = 1
    if row_bin:
        row_div = (1 << row_binning)

    if col_bin:
        col_div = (1 << col_binning)

    nrows = (2*(row_end-row_start+1))/row_div
    ncols = (col_end-col_start+1)/col_div
    return nrows, ncols
