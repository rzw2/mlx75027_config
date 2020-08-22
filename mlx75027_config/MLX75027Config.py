"""
Refael Whyte, r.whyte@chronoptics.com

Calculating the MLX75027 settings from the register values. 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import numpy as np
import warnings


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


def calc_binning(reg_dict):
    """
    Calculates the binning value 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns 
    ----------
    binning : int, the binning value, 0: None (640x480), 1: QVGA (320x240), 2: QQVGA (160x120), 3: QQQVGA (80x60)
    """
    binning = reg_dict["BINNING_MODE"][2]
    return binning


def set_binning(reg_dict, binning):
    """
    Sets the binning mode of the image sensor 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    binning : int, the binning value, 0: None (640x480), 1: QVGA (320x240), 2: QQVGA (160x120), 3: QQQVGA (80x60)
    """
    if binning < 0 or binning > 3:
        raise RuntimeError("Invalid binning mode")

    reg_dict["BINNING_MODE"][2] = int(binning)
    return


def calc_phase_shifts(reg_dict):
    """
    Calculates the phase shifts of each raw frame. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns 
    ----------
    phase_shifts : np.array, the array of phase shift values from [0,1], with 1 being 2pi 

    """

    phase_shifts = np.zeros(8)
    for n in range(0, 8):
        phase_shifts[n] = reg_dict["P"+str(n)+"_PHASE_SHIFT"][2]/8.0

    return phase_shifts


def set_phase_shift(reg_dict, phase_shifts):
    """
    Set the phase shift of each raw frame. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    phase_shifts : np.array, an array of values of the desired phase shift in the range [0,1]

    """

    # We set the phase shifts of each of the 8 raw steps
    if len(phase_shifts) > 8:
        raise ValueError("Maximum length of phase_shifts is 8")

    pos_vals = np.arange(0, 1, 0.125)
    n = 0
    for shift in phase_shifts:
        if shift not in pos_vals:
            raise ValueError("Invalid phase shift value")

        ind = np.where(shift == pos_vals)[0][0]
        reg_dict["P"+str(n)+"_PHASE_SHIFT"][2] = int(ind)
        n += 1

    return


def calc_mod_freq(reg_dict):
    """
    Calculate the modulation frequency of a depth frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    mod_freq : float, the modulation frequency in MHz     
    """
    fmod = reg_dict["FMOD_HI"][2]*256 + reg_dict["FMOD_LOW"][2]
    mod_freq = fmod / \
        ((1 << (reg_dict["DIVSELPRE"][2]+3)) *
         (1 << reg_dict["DIVSEL"][2]) * (1.0/8.0))
    return mod_freq


def set_mod_freq(reg_dict, mod_freq):
    """
    Set the modulation frequency of the MLX75027 depth frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    mod_freq : float, the desired modulation frequency in MHz 

    Returns
    ----------
    fmod : float, the actual modulation frequency in MHz    
    divselpre : int
    divsel : int  
    """
    if mod_freq < 4.0 or mod_freq > 100.0:
        raise RuntimeError(
            "Modulation Frequency outside range of 4 to 100 MHz")

    divselpre = 0
    # Calculate the values of DIVSELPRE and DIVSEL
    if mod_freq < 100 and mod_freq >= 75:
        divselpre = 0
    elif mod_freq < 75 and mod_freq >= 51:
        divselpre = 1
    elif mod_freq < 51 and mod_freq >= 38:
        divselpre = 0
    elif mod_freq < 38 and mod_freq >= 21:
        divselpre = 1
    elif mod_freq < 21 and mod_freq >= 19:
        divselpre = 0
    elif mod_freq < 19 and mod_freq >= 10:
        divselpre = 1
    elif mod_freq < 10 and mod_freq >= 5:
        divselpre = 2
    else:
        divselpre = 3

    if mod_freq >= 51:
        divsel = 0
    elif mod_freq >= 21:
        divsel = 1
    else:
        divsel = 2

    fmod = int(((1 << (divselpre+3)) * (1 << divsel) * mod_freq) / 8)
    # Now actually set the values
    reg_dict["DIVSEL"][2] = divsel
    reg_dict["DIVSELPRE"][2] = divselpre
    value16_to_reg(reg_dict, fmod, "FMOD_HI", "FMOD_LOW")
    # Set the other register
    if((mod_freq*8 < 900) and (mod_freq*8 >= 500)):
        reg_dict["FVCO_FMOD"][2] = 2
    elif ((mod_freq*8 <= 1200) and (mod_freq*8 >= 900)):
        reg_dict["FVCO_FMOD"][2] = 0
    return int(fmod), divselpre, divsel


def set_nlanes(reg_dict, nlanes):
    """
    """
    if nlanes != 2 and nlanes != 4:
        raise RuntimeError("Invalid number of lanes! Must be 2 or 4")

    if nlanes == 2:
        reg_dict["DATA_LANE_CONFIG"][2] = 0
    elif nlanes == 4:
        reg_dict["DATA_LANE_CONFIG"][2] = 1
    return


def calc_nlanes(reg_dict):
    """
    """
    if reg_dict["DATA_LANE_CONFIG"][2] == 0:
        return 2
    elif reg_dict["DATA_LANE_CONFIG"][2] == 1:
        return 4
    else:
        raise RuntimeError("Invalid lane configuration!")
    return


def calc_speed(reg_dict):
    """
    For a given hmax return what the MIPI speed must be.

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    mipi_speed : int, the speed of the MIPI bus in megabits per second
    """
    hmax = reg16_to_value(reg_dict, "HMAX_LOW", "HMAX_HI")
    hmax300 = [0x0E60, 0x0860, 0x1CC0, 0x0E60]
    hmax600 = [0x0744, 0x0444, 0x0E88, 0x0744]
    hmax704 = [0x0636, 0x03A8, 0x0C6C, 0x0636]
    hmax800 = [0x057A, 0x0338, 0x0AF4, 0x057A]
    hmax960 = [0x0514, 0x02B6, 0x0A28, 0x0514]

    if hmax in hmax300:
        return 300
    elif hmax in hmax600:
        return 600
    elif hmax in hmax704:
        return 704
    elif hmax in hmax800:
        return 800
    elif hmax in hmax960:
        return 960
    else:
        if hmax == 824:
            return 800
        elif hmax == 826:
            return 800
        raise ValueError("Invalid hmax: " + str(hmax))
    return


def calc_output_mode(reg_dict):
    return reg_dict["OUTPUT_MODE"][2]


def set_output_mode(reg_dict, output_mode):
    if output_mode < 0 or output_mode > 4:
        raise RuntimeError("Invalid output mode! Must be between 0 and 4")
    reg_dict["OUTPUT_MODE"][2] = int(output_mode)
    return


def set_hmax(reg_dict, hmax):
    """
    """
    if hmax < 0 or hmax > 16383:
        raise RuntimeError("Invalid hmax value! Must be between 0 and 16383")

    value16_to_reg(reg_dict, hmax, "HMAX_HI", "HMAX_LOW")
    return


def calc_hmax(reg_dict, speed=800):
    """
    Calculate the HMAX value given the MIPI readout speed. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    speed : int, optional, the speed of the MIPI readout in Mbps 

    Returns
    ----------
    hmax : int, the value of the hmax registers, used a lot for the timing calculations

    """
    speed_list = [300, 600, 704, 800, 960]
    ind = speed_list.index(speed)

    if reg_dict["OUTPUT_MODE"][2] == 4:
        # We are outputting A & B
        if reg_dict["DATA_LANE_CONFIG"][2] == 1:
            # 4 Lane speed
            hmax_vec = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
            hmax = hmax_vec[ind]
        else:
            # 2 Lane speed
            hmax_vec = [0x1CC0, 0x0E88, 0x0C6C, 0x0AF4, 0x0A28]
            hmax = hmax_vec[ind]
    else:
        # We are in normal mode
        if reg_dict["DATA_LANE_CONFIG"][2] == 1:
            # 4 Lane speed
            hmax_vec = [0x0860, 0x0444, 0x03A8, 0x033A, 0x02B6]
            hmax = hmax_vec[ind]
        else:
            # 2 Lane speed
            hmax_vec = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
            hmax = hmax_vec[ind]
    return hmax


def calc_int_times(reg_dict):
    """
    Calculates the integration times of each raw frame in us

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    int_times : np.array, an array of the raw frame integration times in micro-seconds 
    """

    px_int = np.zeros(8, dtype=np.uint32)
    for n in range(0, 8):
        px_int[n] = reg_to_value(reg_dict, "P"+str(n)+"_INT0", "P" +
                                 str(n)+"_INT1", "P"+str(n)+"_INT2", "P"+str(n)+"_INT3")

    int_times = np.round((px_int) / 120)
    return int_times


def set_int_times(reg_dict, int_times):
    """
    Set the integration times of each raw frame in micro-seconds 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    int_times : np.array, the array of integration times in micro-seconds (us)
    """

    if np.size(int_times) > 8:
        raise RuntimeError("MLX75027 has maximum number of 8 raw frames!")

    for n in range(0, np.size(int_times)):
        reg_value = np.uint32(int_times[n]*120)
        value32_to_reg(reg_dict, reg_value, "P"+str(n)+"_INT0",
                       "P"+str(n)+"_INT1", "P"+str(n)+"_INT2", "P"+str(n)+"_INT3")
    return


def calc_startup_time(reg_dict):
    """
    Calculates the startup time in micro-seconds

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    startup_time : float, the startup time in micro-seconds (us)
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)
    value = reg_dict["FRAME_STARTUP_HI"][2] * \
        256 + reg_dict["FRAME_STARTUP_LOW"][2]

    startup_time = value*hmax / 120.0
    return startup_time


def set_startup_time(reg_dict, startup_time_us):
    """
    Set the startup time in micro-seconds 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    startup_time_us : float, the startup time in micro-seconds (us) 
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)
    frame_startup = int((startup_time_us*120) / hmax)
    reg_dict["FRAME_STARTUP_HI"][2] = frame_startup >> 8
    reg_dict["FRAME_STARTUP_LOW"][2] = frame_startup & 0xFF
    return


def calc_idle_time(reg_dict):
    """
    Calculates the idle time in micro-seconds of each raw frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    idle_time : np.array, the idle time of each raw frame in micro-seconds (us)

    """
    idle_time = np.zeros(8)
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    for n in range(0, 8):
        idle_time[n] = reg_dict["P"+str(n)+"_PHASE_IDLE"][2] * hmax / (120.0)

    return idle_time


def set_idle_time(reg_dict, idle_times):
    """
    Set the idle time in micro-seconds for each raw frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    idle_times : np.array, the idle time of each raw frame in micro-seconds 
    """
    if np.size(idle_times) > 8:
        raise RuntimeError("MLX75027 only 8 raw frame possible!")

    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    for n in range(0, np.size(idle_times)):
        reg_dict["P"+str(n) +
                 "_PHASE_IDLE"][2] = np.uint8(idle_times[n]*120 / hmax)
    return


def calc_pretime(reg_dict):
    """
    Returns the pretime in micro-seconds for each raw frame.  

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    pretime : float, the pretime in micro-seconds (us)

    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    # As noted in 7.12. both preheat and premix use the same register timing.
    # We are assuming that if either are enabled then.
    pretime_enabled = np.any(
        reg_dict["Px_PREHEAT"][2] | reg_dict["Px_PREMIX"][2])

    if pretime_enabled:
        Px_pretime = int(reg_dict["Px_PRETIME_HI"][2]) * \
            256 + int(reg_dict["Px_PRETIME_LOW"][2])

        if reg_dict["OUTPUT_MODE"][2] == 4:
            pre_heat_time = (Px_pretime - 5)*hmax/120.0
        else:
            pre_heat_time = (Px_pretime - 9)*hmax/120.0

        if pre_heat_time < 0:
            pre_heat_time = 0
    else:
        # This is the register value calculation
        # pre_heat_time = np.floor((50.0*120.0) / hmax)
        # This is the inverse of the register
        pre_heat_time = 50.0*hmax/120.0
    return pre_heat_time


def set_pretime(reg_dict, pretime):
    """
    Sets the pretime in micro-secnods. If preheat or premix is not enabled than uses section 7.4.2 of the MLX75027 datasheet

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    pretime : float, the pretime in micro-seconds
    """
    pretime_enabled = np.any(
        reg_dict["Px_PREHEAT"][2] | reg_dict["Px_PREMIX"][2])

    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    if pretime_enabled:
        # TODO: Add warning for this Note : (𝐹𝐿𝑂𝑂𝑅(Px_PRETIME(in µs)∗120 ) HMAX ) + Px_INTEGRATION should not exceed 1ms.
        if reg_dict["OUTPUT_MODE"][2] == 4:
            pretime_reg = int(np.floor((pretime*120.0)/hmax) + 5)
        else:
            pretime_reg = int(np.floor((pretime*120.0)/hmax) + 9)

        if pretime >= 11.13:
            randnm7 = (1070 + hmax) * np.floor(((pretime-11.13)/hmax) * 120.0)
        else:
            randnm7 = 1070

    else:
        # We use calculation in section 7.4.2
        pretime_reg = int(np.floor(50.0*120.0 / hmax))
        randnm7 = 1070

    randnm0 = hmax*pretime_reg - randnm7 - 2098

    value16_to_reg(reg_dict, pretime_reg,
                   "Px_PRETIME_HI", "Px_PRETIME_LOW")
    # Now set the other pretime registers
    value24_to_reg(reg_dict, randnm0, "RANDNM0_0",
                   "RANDNM0_1", "RANDNM0_2")
    value24_to_reg(reg_dict, randnm7, "RANDNM7_0",
                   "RANDNM7_1", "RANDNM7_2")
    return


def calc_preheat(reg_dict):
    """

    """
    heat = np.zeros(8, dtype=np.bool)
    for n in range(0, 8):
        heat[n] = bool(reg_dict["Px_PREHEAT"][2] & (1 << n))
    return heat


def set_preheat(reg_dict, heat):
    """
    """
    px_heat = int(0)
    for n in range(0, 8):
        px_heat |= (int(heat[n]) << n)
    reg_dict["Px_PREHEAT"][2] = px_heat
    return


def calc_premix(reg_dict):
    premix = np.zeros(8, dtype=np.bool)
    for n in range(0, 8):
        premix[n] = bool(reg_dict["Px_PREMIX"][2] & (1 << n))
    return premix


def set_premix(reg_dict, premix):
    """
    """
    px_premix = int(0)
    for n in range(0, 8):
        px_premix |= (int(premix[n]) << n)
    reg_dict["Px_PREMIX"][2] = px_premix
    return


def calc_leden(reg_dict):
    """
    """
    leden = np.zeros(8, dtype=np.bool)
    for n in range(0, 8):
        leden[n] = bool(reg_dict["Px_LEDEN"][2] & (1 << n))
    return leden


def set_leden(reg_dict, leden):
    """
    """
    px_leden = int(0)
    for n in range(0, 8):
        px_leden |= (int(leden[n]) << n)

    reg_dict["Px_LEDEN"][2] = px_leden
    return


def calc_all_pretimes(reg_dict):
    """
    Calculate the combination of all the preheat and premix times 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    pre_times : np.array, the pretime in micro-seconds (us) of each raw frame 

    """
    pretime = calc_pretime(reg_dict)

    pre_heat_time = np.zeros(8)
    pre_mix_time = np.zeros(8)

    for n in range(0, 8):
        heat = reg_dict["Px_PREHEAT"][2] & (1 << n)
        if heat:
            pre_heat_time[n] = pretime
        mix = reg_dict["Px_PREMIX"][2] & (1 << n)
        if mix:
            pre_mix_time[n] = pretime

    pre_times = pre_heat_time + pre_mix_time
    return pre_times


def calc_phase_time(reg_dict):
    """
    Calculates the total time of a raw frame, pretime, integration and idle times 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    phase_times : np.array, the time in micro-seconds (us) 
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    pre_time = calc_all_pretimes(reg_dict)
    int_times = calc_int_times(reg_dict)
    idle_times = calc_idle_time(reg_dict)

    phase_times = pre_time+int_times+idle_times + (266.0*hmax)/120.0

    return phase_times


def calc_deadtime(reg_dict):
    """
    Calculates the deadtime of a depth frame. Which is the time at the end of the depth acquisition the sensor waits. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    dead_time : float, the dead time in micro-seconds (us) 
    """

    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)
    frame_time_reg = reg_to_value(
        reg_dict, "FRAME_TIME0", "FRAME_TIME1", "FRAME_TIME2", "FRAME_TIME3")
    frame_time_us = (frame_time_reg*hmax) / 120.0

    phase_times = calc_phase_time(reg_dict)

    # XXX : The datasheet doesn't say about the sum of phase times
    min_frame_time = np.sum(phase_times[0:reg_dict["PHASE_COUNT"][2]])

    if min_frame_time > frame_time_us:
        dead_time = 0
    else:
        dead_time = frame_time_us - min_frame_time

    return dead_time


def set_deadtime(reg_dict, dead_time):
    """
    Set the deadtime in micro-seconds for a depth frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    dead_time : float, the desired dead time in micro-seconds (us)

    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)
    phase_times = calc_phase_time(reg_dict)

    min_frame_time = np.sum(phase_times[0:reg_dict["PHASE_COUNT"][2]])

    frame_time_us = min_frame_time + dead_time
    if dead_time > 0:
        frame_time_reg = np.uint32(120*frame_time_us / hmax)
    else:
        frame_time_reg = 0

    value32_to_reg(reg_dict, frame_time_reg, "FRAME_TIME0",
                   "FRAME_TIME1", "FRAME_TIME2", "FRAME_TIME3")

    return


def calc_frame_time(reg_dict):
    """
    Calculates the total depth frame time in micro-seconds 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns 
    frame_time : float, the total depth frame time in micro-seconds (us) 
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    frame_startup = reg_dict["FRAME_STARTUP_HI"][2] * \
        256 + reg_dict["FRAME_STARTUP_LOW"][2]
    frame_startup_us = (frame_startup*hmax)/120

    dead_time = calc_deadtime(reg_dict)
    phase_times = calc_phase_time(reg_dict)
    frame_setup = 500.0

    phase_time = np.sum(phase_times[0:reg_dict["PHASE_COUNT"][2]])

    frame_time = phase_time + frame_setup + dead_time + frame_startup_us
    return frame_time


def calc_nraw(reg_dict):
    """
    Return the number of raw frames used in a depth frame 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns 
    nraw : int, the number of raw frames in a depth sequence  
    """
    return reg_dict["PHASE_COUNT"][2]


def set_nraw(reg_dict, nraw):
    """
    Sets the number of raw frames in a depth sequence 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    nraw : int the number of raw frames in a depth sequence must be between 1 and 8. 
    """
    if nraw < 1 or nraw > 8:
        raise RuntimeError(
            "Invalid number of raw frames, must be between 1 and 8")
    reg_dict["PHASE_COUNT"][2] = int(nraw)


def calc_fps(reg_dict):
    """
    Calculates the frames per seconds, returns both the depth frame rate, and the raw frame rate. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    depth_fps : float, the number of depth frames per second 
    raw_fps : float, the number of raw frames per second 
    """
    frame_time_us = calc_frame_time(reg_dict)
    depth_fps = 1.0 / (frame_time_us*1e-6)
    raw_fps = depth_fps * reg_dict["PHASE_COUNT"][2]
    return depth_fps, raw_fps


def calc_roi(reg_dict):
    """
    Calculates the MLX75027 region of interest. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    col_start : int, 
    col_end : int, 
    row_start : int,  
    row_end : int, 
    """

    col_start = reg_dict["ROI_COL_START_HI"][2] * \
        256 + reg_dict["ROI_COL_START_LOW"][2]
    col_end = col_start + \
        reg_dict["ROI_COL_WIDTH_HI"][2]*256 + \
        reg_dict["ROI_COL_WIDTH_LOW"][2] - 1
    row_start = (reg_dict["ROI_ROW_START_HI"][2]*256 +
                 reg_dict["ROI_ROW_START_LOW"][2])*2 + 1
    row_end = ((reg_dict["ROI_ROW_END_HI"][2]*256 +
                reg_dict["ROI_ROW_END_LOW"][2]) - 1)*2
    return col_start, col_end, row_start, row_end


def set_roi(reg_dict, col_start, col_end, row_start, row_end):
    """
    Set the region of interest (ROI) of the MLX75027 image sensor 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    col_start : int, The column start between 0 and 640 
    col_end : int, the column end between 0 and 640 
    row_start : int, the row start between 0 and 480 
    row_end : int, the row end between 0 and 480 
    """

    # Check input data is correct
    if col_start < 1 or col_start > 640:
        raise RuntimeError("Column start must be between 0 and 640")
    if col_end < 0 or col_end > 640:
        raise RuntimeError("Column end must be between 0 and 640")
    if col_start >= col_end:
        raise RuntimeError("The column start must less than the column end")
    if row_start < 1 or row_start > 480:
        raise RuntimeError("The row start must be between 0 and 482")
    if row_end < 0 or row_end > 480:
        raise RuntimeError("The row end must be between 0 and 482")
    if row_start >= row_end:
        raise RuntimeError("The row start must be less than the row end")

    # As per section 7.19. Y1 should be uneven while Y2 is even, where y is the rows
    if not (row_start & 0x01):
        warnings.warn("Row start is even, it should be odd!", RuntimeWarning)
    if row_end & 0x01:
        warnings.warn("Row end is odd, it should be even!", RuntimeWarning)

    reg_dict["ROI_COL_START_HI"][2] = int(col_start) >> 8
    reg_dict["ROI_COL_START_LOW"][2] = int(col_start) & 0xFF

    reg_dict["ROI_COL_WIDTH_HI"][2] = int(col_end-col_start+1) >> 8
    reg_dict["ROI_COL_WIDTH_LOW"][2] = int(col_end-col_start+1) & 0xFF

    reg_dict["ROI_ROW_START_LOW"][2] = (int(row_start-1) >> 1) & 0xFF
    reg_dict["ROI_ROW_START_HI"][2] = (int(row_start-1) >> 1) >> 8

    reg_dict["ROI_ROW_END_LOW"][2] = ((int(row_end) >> 1)+1) & 0xFF
    reg_dict["ROI_ROW_END_HI"][2] = ((int(row_end) >> 1)+1) >> 8
    return


def calc_duty_cycle(reg_dict):
    """
    Calculate the duty cycle of the illumination. The duty cycle might want to be varied 
    because of the rise time of the VCSEL or laser. Changing the duty cycle also changes 
    the harmonic content of the illumination waveform which will change the wiggle/circular 
    error of the ToF camera. 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns 
    ----------
    duty_cycle : float, the duty cycle of the illumination output between 0.0 and 1.0  
    """
    if reg_dict["DUTY_CYCLE"][2] == 0:
        # Duty cycle is disabled
        return 0.5

    edge_change_ps = 0.5 * reg_dict["DUTY_CYCLE_VALUE"][2]
    if reg_dict["DUTY_CYCLE"][2] == 2:
        edge_change_ps = -1.0 * edge_change_ps

    fmod = calc_mod_freq(reg_dict)

    period = 1e3 / fmod

    duty_cycle = ((period/2.0) + edge_change_ps) / period

    return duty_cycle


def set_duty_cycle(reg_dict, duty_cycle):
    """
    Set the duty cycle of the illumination driver 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 
    duty_cycle : float, the desired duty cycle from 0.0 to 1.0, will select the closest value. 
    """
    if duty_cycle == 0.5:
        cycle = 0
        value = 0
        reg_dict["DUTY_CYCLE"][2] = cycle
        reg_dict["DUTY_CYCLE_VALUE"][2] = value
        return cycle, value

    if duty_cycle < 0.5:
        cycle = 2
    else:
        cycle = 1

    fmod = calc_mod_freq(reg_dict)
    period = 1e3 / fmod

    # This is the value in ns,
    # duty_cycle = ( (period/2.0) + edge_change_ps ) / period
    edge_change_ps = (duty_cycle * period) - (period/2.0)
    value_fl = np.round(np.abs(edge_change_ps) / 0.5)
    value_int = int(value_fl)
    #print("set_duty_cycle() - value_int: " + str(value_int))
    if value_int > 0xF:
        value_int = 0xF

    reg_dict["DUTY_CYCLE"][2] = cycle
    reg_dict["DUTY_CYCLE_VALUE"][2] = value_int
    return cycle, value_int


def calc_pll_setup(reg_dict):
    """
    Calculate the PLL setup time 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    pll_setup : int, the setup time. 
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    pll_setup = np.ceil((503.0*120.0)/hmax + 8)
    return int(pll_setup)


"""
# This is calculating using calc_pretime() use that function instead  
def calc_pix_rst(reg_dict):
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    pix_rst = np.ceil((50*120)/hmax)
    return int(pix_rst)
"""


def calc_randnm7(reg_dict):
    """
    Calculate the RANDMN7 register value 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    randnm7 : int, the randnm7 register value
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    pretime_enabled = np.any(
        reg_dict["Px_PREHEAT"][2] | reg_dict["Px_PREMIX"][2])

    if pretime_enabled:
        px_pretime = calc_pretime(reg_dict)
        # As noted in 7.12. can be calculated as: 1070 + HMAX * FLOOR( ((Px_PRETIME(in µs)−11.13) / HMAX )* 120),𝑤𝑖𝑡ℎ Px_PRETIME ≥ 11.13
        if px_pretime >= 11.13:
            randnm7 = 1070 + hmax * np.floor(((px_pretime-11.13)/hmax) * 120)
        else:
            randnm7 = 1070
    else:
        randnm7 = 1070
    return int(randnm7)


def calc_randnm0(reg_dict):
    """
    Calculate the RANDNM0 register value 

    Parameters
    ----------
    reg_dict : dict, the dictionary that contains all the register information 

    Returns
    ----------
    randnm0 : int, the randnm0 register value  
    """
    speed = calc_speed(reg_dict)
    hmax = calc_hmax(reg_dict, speed=speed)

    pixrst = calc_pretime(reg_dict)
    randnm7 = calc_randnm7(reg_dict)
    randnm0 = hmax*pixrst - randnm7 - 2098
    return int(randnm0)
