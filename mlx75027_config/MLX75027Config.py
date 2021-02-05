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

from mlx75027_config import value16_to_reg, value24_to_reg, value32_to_reg, reg24_to_value, reg16_to_value, reg_to_value


def calc_analog_delay(reg_dict):
    """
    Calculates the delay in micro-seconds (us) of the analog delay settings
    of the MLX75026 sensor.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    delay_us : float
        The delay in microseconds
    """
    fmod = calc_mod_freq(reg_dict)
    if fmod < 21:
        N = 32
    elif fmod < 51:
        N = 16
    elif fmod < 101:
        N = 8
    else:
        N = 8
        warnings.warn("calc_analog_delay() - Invalid modulation frequency!")

    coarse_delay_seconds = reg_dict["ADELAY_COARSE"][2]/(fmod*1e6*N)

    #
    fine_delay_seconds = reg_dict["ADELAY_FINE"][2] * 75e-12
    super_fine_seconds = reg_dict["ADELAY_SFINE"][2] * 20e-12

    delay_us = (coarse_delay_seconds + fine_delay_seconds +
                super_fine_seconds) * 1e6

    return delay_us


def set_analog_delay(reg_dict, delay_us):
    """
    Sets the delay of the analog delay line with the input delay in micro seconds
    of the MLX75026 sensor.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    delay_us : float
        The desired delay in microseconds
    """
    delay_seconds = delay_us * 1e-6
    fmod = calc_mod_freq(reg_dict)
    if fmod < 21:
        N = 32
    elif fmod < 51:
        N = 16
    elif fmod < 101:
        N = 8
    else:
        N = 8
        warnings.warn("calc_analog_delay() - Invalid modulation frequency!")

    coarse_delay = np.floor(delay_seconds/(1.0/(fmod*1e6*N)))
    if coarse_delay > (N-1):
        coarse_delay = N-1
        warnings.warn("set_analog_delay() - Saturated coarse delay value!")

    remaining_time = delay_seconds - coarse_delay/(fmod*1e6*N)

    fine_delay = np.floor(remaining_time/(75e-12))
    if fine_delay > 71:
        fine_delay = 71

    #
    fine_time = (fine_delay*75e-12)
    # Verify that fine_delay isn't greater than a coarse delay step size
    if fine_time > (1.0/(fmod*1e6*N)):
        warnings.warn("calc_analog_delay() - Invalid fine delay time")

    remaining = remaining_time - fine_time

    super_fine = np.floor(remaining/(20e-12))
    if super_fine > 3:
        super_fine = 3

    # Now set the values
    reg_dict["ADELAY_SFINE"][2] = int(super_fine)
    reg_dict["ADELAY_FINE"][2] = int(fine_delay)
    reg_dict["ADELAY_COARSE"][2] = int(coarse_delay)
    return


def calc_binning(reg_dict):
    """
    Calculates the binning value

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    binning : int
        The binning value, for the MLX75027 0: None (640x480), 1: QVGA (320x240), 2: QQVGA (160x120), 3: QQQVGA (80x60)
        for the MLX75026 0: None (320x240), 1 : QQVGA (160x120), 2 : QQQVGA (80x60), 3 : QQQQVGA (40x30)
    """
    binning = reg_dict["BINNING_MODE"][2]
    return binning


def set_binning(reg_dict, binning):
    """
    Sets the binning mode of the image sensor

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    binning : int
        The binning value, for the MLX75027 0: None (640x480), 1: QVGA (320x240), 2: QQVGA (160x120), 3: QQQVGA (80x60)
        for the MLX75026 0: None (320x240), 1 : QQVGA (160x120), 2 : QQQVGA (80x60), 3 : QQQQVGA (40x30)
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
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    phase_shifts : numpy.array
        The array of phase shift values from [0,1], with 1 being 2pi

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
    reg_dict : dict
        The dictionary that contains all the register information
    phase_shifts : numpy.array
        An array of values of the desired phase shift in the range [0,1]

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
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    mod_freq : float
        The modulation frequency in MHz
    """
    fmod = reg_dict["FMOD_HI"][2]*256 + reg_dict["FMOD_LOW"][2]
    mod_freq = fmod / \
        ((1 << (reg_dict["DIVSELPRE"][2]+3)) *
         (1 << reg_dict["DIVSEL"][2]) * (1.0/8.0))
    return mod_freq


def set_mod_freq(reg_dict, mod_freq):
    """
    Set the modulation frequency of the MLX75027 or MLX75026 depth frame  in MHz
    and return the register values.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mod_freq : float
        The desired modulation frequency in MHz

    Returns
    ----------
    fmod : float
        The actual modulation frequency in MHz
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
    Set the number of MIPI Lanes to use during readout.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    nlanes : int
        The number of lanes, must be 2 or 4.
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
    Return the number of MIPI Lanes used during readout

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    nlanes : int
        The number of lanes, 2 or 4
    """
    if reg_dict["DATA_LANE_CONFIG"][2] == 0:
        return 2
    elif reg_dict["DATA_LANE_CONFIG"][2] == 1:
        return 4
    else:
        raise RuntimeError("Invalid lane configuration!")
    return


def calc_speed(reg_dict, mlx75027):
    """
    For a given hmax return what the MIPI speed must be.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False
        if using the MLX75026 sensor.

    Returns
    ----------
    mipi_speed : int
        The speed of the MIPI bus in megabits per second
    """
    hmax = reg16_to_value(reg_dict, "HMAX_LOW", "HMAX_HI")
    # print("mlx75027: " + str(mlx75027))
    if mlx75027:
        hmax300 = [0x0E78, 0x0860, 0x1A80, 0x0E60]
        hmax600 = [0x0750, 0x0444, 0x0D54, 0x0744]
        hmax704 = [0x0640, 0x03A8, 0x0B60, 0x0636]
        hmax800 = [0x0584, 0x0338, 0x0A06, 0x057A]
        hmax960 = [0x049E, 0x02B6, 0x0860, 0x0514]
    else:
        hmax300 = [0x0878, 0x0560, 0x0E80, 0x0860]
        hmax600 = [0x0450, 0x02C4, 0x0754, 0x0444]
        hmax704 = [0x03B2, 0x02B6, 0x0644, 0x03A8]
        hmax800 = [0x0344, 0x02B6, 0x0586, 0x033A]
        hmax960 = [0x02BE, 0x02B6, 0x0514, 0x02B6]

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
    """ Return the data output mode being used """
    return reg_dict["OUTPUT_MODE"][2]


def set_output_mode(reg_dict, output_mode):
    """ Set the data output mode """
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


def calc_hmax(reg_dict, mlx75027, speed=800):
    """
    Calculate the HMAX value given the MIPI readout speed.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False if using the MLX75026 sensor.
    speed : int, optional
        The speed of the MIPI readout in Mbps

    Returns
    ----------
    hmax : int
        The value of the hmax registers, used a lot for the timing calculations

    """
    speed_list = [300, 600, 704, 800, 960]
    ind = speed_list.index(speed)

    if reg_dict["OUTPUT_MODE"][2] == 4:
        # We are outputting A & B
        if reg_dict["DATA_LANE_CONFIG"][2] == 1:
            # 4 Lane speed
            if mlx75027:
                hmax_vec = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
            else:
                hmax_vec = [0x0860, 0x0444, 0x03A8, 0x033A, 0x02B6]
            hmax = hmax_vec[ind]
        else:
            # 2 Lane speed
            if mlx75027:
                hmax_vec = [0x1CC0, 0x0E88, 0x0C6C, 0x0AF4, 0x0A28]
            else:
                hmax_vec = [0x0E80, 0x0754, 0x0644, 0x0586, 0x0514]
            hmax = hmax_vec[ind]
    else:
        # We are in normal mode
        if reg_dict["DATA_LANE_CONFIG"][2] == 1:
            # 4 Lane speed
            if mlx75027:
                hmax_vec = [0x0860, 0x0444, 0x03A8, 0x033A, 0x02B6]
            else:
                hmax_vec = [0x0560, 0x02C4, 0x02B6, 0x02B6, 0x02B6]
            hmax = hmax_vec[ind]
        else:
            # 2 Lane speed
            if mlx75027:
                hmax_vec = [0x0E60, 0x0744, 0x0636, 0x057A, 0x0514]
            else:
                hmax_vec = [0x0878, 0x0450, 0x03B2, 0x0344, 0x02BE]
            hmax = hmax_vec[ind]
    return hmax


def calc_int_times(reg_dict):
    """
    Calculates the integration times of each raw frame in us

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information

    Returns
    ----------
    int_times : numpy.array
        An array of the raw frame integration times in micro-seconds
    """

    px_int = np.zeros(8, dtype=np.uint32)
    for n in range(0, 8):
        px_int[n] = reg_to_value(reg_dict, "P"+str(n)+"_INT0", "P" +
                                 str(n)+"_INT1", "P"+str(n)+"_INT2", "P"+str(n)+"_INT3")

    int_times = ((px_int) / 120)
    return int_times


def set_int_times(reg_dict, int_times, mlx75027):
    """
    Set the integration times of each raw frame in micro-seconds

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    int_times : numpy.array
        The array of integration times in micro-seconds (us)
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """

    if np.size(int_times) > 8:
        raise RuntimeError("MLX75027 has maximum number of 8 raw frames!")

    # print("set_int_times")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    for n in range(0, np.size(int_times)):
        reg_value = np.uint32(np.ceil(int_times[n]*120.0/hmax) * hmax)
        value32_to_reg(reg_dict, reg_value, "P"+str(n)+"_INT0",
                       "P"+str(n)+"_INT1", "P"+str(n)+"_INT2", "P"+str(n)+"_INT3")
    return


def calc_startup_time(reg_dict, mlx75027):
    """
    Calculates the startup time in micro-seconds

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set True for MLX75027 sensor, False for MLX75026

    Returns
    ----------
    startup_time : float
        The startup time in micro-seconds (us)
    """

    # print("calc_startup_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)
    value = reg_dict["FRAME_STARTUP_HI"][2] * \
        256 + reg_dict["FRAME_STARTUP_LOW"][2]

    startup_time = value*hmax / 120.0
    return startup_time


def set_startup_time(reg_dict, startup_time_us, mlx75027):
    """
    Set the startup time in micro-seconds

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    startup_time_us : float
        The startup time in micro-seconds (us)
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """

    # print("set_startup_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)
    frame_startup = int((startup_time_us*120) / hmax)
    reg_dict["FRAME_STARTUP_HI"][2] = frame_startup >> 8
    reg_dict["FRAME_STARTUP_LOW"][2] = frame_startup & 0xFF
    return


def calc_idle_time(reg_dict, mlx75027):
    """
    Calculates the idle time in micro-seconds of each raw frame

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    Returns
    ----------
    idle_time : numpy.array
        The idle time of each raw frame in micro-seconds (us)

    """
    idle_time = np.zeros(8)
    # print("calc_idle_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    for n in range(0, 8):
        idle_time[n] = reg_dict["P"+str(n)+"_PHASE_IDLE"][2] * hmax / (120.0)

    return idle_time


def set_idle_time(reg_dict, idle_times, mlx75027):
    """
    Set the idle time in micro-seconds for each raw frame

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    idle_times : numpy.array
        The idle time of each raw frame in micro-seconds
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """
    if np.size(idle_times) > 8:
        raise RuntimeError("MLX75027 only 8 raw frame possible!")

    # print("set_idle_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    for n in range(0, np.size(idle_times)):
        reg_dict["P"+str(n) +
                 "_PHASE_IDLE"][2] = np.uint8(idle_times[n]*120 / hmax)
    return


def calc_pretime(reg_dict, mlx75027):
    """
    Returns the pretime in micro-seconds for each raw frame.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False
        if using the MLX75026 sensor.

    Returns
    ----------
    pretime : float
        The pretime in micro-seconds (us)

    """

    # print("calc_pretime")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

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


def set_pretime(reg_dict, pretime, mlx75027):
    """
    Sets the pretime in micro-secnods. If preheat or premix is not enabled than uses section 7.4.2 of the MLX75027 datasheet

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    pretime : float
        The pretime in micro-seconds
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """
    pretime_enabled = np.any(
        reg_dict["Px_PREHEAT"][2] | reg_dict["Px_PREMIX"][2])

    # print("set_pretime")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    if pretime_enabled:
        # TODO: Add warning for this Note : FLOOR(Px_PRETIME_us*120)/HMAX) + Px_Integration should not exceed 1000us
        if reg_dict["OUTPUT_MODE"][2] == 4:
            pretime_reg = int(np.ceil((pretime*120.0)/hmax) + 5)
        else:
            pretime_reg = int(np.ceil((pretime*120.0)/hmax) + 9)

        if pretime >= 11.13:
            randnm7 = 1070 + hmax * np.ceil(((pretime-11.13)/hmax) * 120.0)
        else:
            randnm7 = 1070

    else:
        # We use calculation in section 7.4.2
        pretime_reg = int(np.ceil(50.0*120.0 / hmax))
        randnm7 = 1070

    randnm0 = hmax*pretime_reg - randnm7 - 2098
    if randnm0 > (2**22)-1:
        raise RuntimeError("Invalid RANDNM0 Value!")
    if randnm0 < 0:
        print("hmax: " + str(hmax) + " pretime: " +
              str(pretime_reg) + " randnm7: " + str(randnm7))
        raise RuntimeError("Negative RANDNM0 Value!")

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
    Calculate the pre-heat time
    """
    heat = np.zeros(8, dtype=np.bool)
    for n in range(0, 8):
        heat[n] = bool(reg_dict["Px_PREHEAT"][2] & (1 << n))
    return heat


def set_preheat(reg_dict, heat):
    """
    Set the pre-heat time
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


def calc_all_pretimes(reg_dict, mlx75027):
    """
    Calculate the combination of all the preheat and premix times

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    Returns
    ----------
    pre_times : numpy.array
        The pretime in micro-seconds (us) of each raw frame

    """
    pretime = calc_pretime(reg_dict, mlx75027)

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


def calc_phase_time(reg_dict, mlx75027):
    """
    Calculates the total time of a raw frame, pretime, integration and idle times

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    Returns
    ----------
    phase_times : numpy.array
        The time in micro-seconds (us)
    """

    # print("calc_phase_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    pre_time = calc_all_pretimes(reg_dict, mlx75027)
    int_times = calc_int_times(reg_dict)
    idle_times = calc_idle_time(reg_dict, mlx75027)

    # Updated to v0.9 of the datasheet
    roi_row_start = reg_dict["ROI_ROW_START_HI"][2] * \
        256 + reg_dict["ROI_ROW_START_LOW"][2]
    roi_row_end = (reg_dict["ROI_ROW_END_HI"][2] *
                   256 + reg_dict["ROI_ROW_END_LOW"][2])

    # Phase length (in µs) =(PRETIME + Px_INTEGRATION/HMAX+ 7 + (ROI_ROW_END − ROI_ROW_START + 1) + Px_PHASE_IDLE ) ∗ HMAX/120

    phase_times = pre_time+int_times+idle_times + \
        (7.0+(roi_row_end-roi_row_start+1))*hmax/120.0

    return phase_times


def calc_deadtime(reg_dict, mlx75027):
    """
    Calculates the deadtime of a depth frame. Which is the time at the end of the depth acquisition the sensor waits.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    Returns
    ----------
    dead_time : float
        The dead time in micro-seconds (us)
    """

    # print("calc_deadtime")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)
    frame_time_reg = reg_to_value(
        reg_dict, "FRAME_TIME0", "FRAME_TIME1", "FRAME_TIME2", "FRAME_TIME3")
    frame_time_us = (frame_time_reg*hmax) / 120.0

    min_frame_time = calc_frame_time(reg_dict, mlx75027, False)

    if min_frame_time > frame_time_us:
        dead_time = 0
    else:
        dead_time = frame_time_us - min_frame_time

    return dead_time


def set_deadtime(reg_dict, dead_time, mlx75027):
    """
    The MLX75027 does not have a dead time value, but the FRAME_TIME value is set
    to allow for a dead time.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    dead_time : float
        The desired dead time in micro-seconds (us)
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    """

    # print("set_deadtime")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)
    min_frame_time = calc_frame_time(reg_dict, mlx75027, False)

    frame_time_us = min_frame_time + dead_time
    if dead_time > 0:
        frame_time_reg = np.uint32(120*frame_time_us / hmax)
    else:
        frame_time_reg = 0

    value32_to_reg(reg_dict, frame_time_reg, "FRAME_TIME0",
                   "FRAME_TIME1", "FRAME_TIME2", "FRAME_TIME3")

    return


def set_frame_time(reg_dict, frame_time_us, mlx75027):
    """
    Sets the FRAME_TIME register. If the input time is less than the minimum allowable
    the FRAME_TIME register is set to 0.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    frame_time_us : float
        The frame time in microsecond (us)
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """
    frame_time_min = calc_frame_time(reg_dict, mlx75027, use_frame_time=False)
    if frame_time_us <= frame_time_min:
        # Set the frame_time register to zero
        value32_to_reg(reg_dict, 0, "FRAME_TIME0", "FRAME_TIME1",
                       "FRAME_TIME2", "FRAME_TIME3")
        return

    # print("set_frame_time")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)
    frame_time_reg = int(np.floor(frame_time_us*120.0/hmax))
    value32_to_reg(reg_dict, frame_time_reg, "FRAME_TIME0", "FRAME_TIME1",
                   "FRAME_TIME2", "FRAME_TIME3")
    return


def calc_frame_time(reg_dict, mlx75027, use_frame_time=False):
    """
    Calculates the total depth frame time in micro-seconds.

    Parameters
    ----------
    reg_dict : dict
        The dictionary that contains all the register information
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    use_frame_time, bool, optional
        Use the FRAME_TIME register

    Returns
    ----------
    frame_time : float
        The total depth frame time in micro-seconds (us)
    """
    # print("calc_frame_time()")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    frame_startup = reg_dict["FRAME_STARTUP_HI"][2] * \
        256 + reg_dict["FRAME_STARTUP_LOW"][2]
    frame_startup_us = (frame_startup*hmax)/120

    phase_times = calc_phase_time(reg_dict, mlx75027)
    frame_setup = 500.0

    phase_time = np.sum(phase_times[0:reg_dict["PHASE_COUNT"][2]])

    frame_time = phase_time + frame_setup + frame_startup_us
    if use_frame_time:
        frame_time_reg = reg_to_value(
            reg_dict, "FRAME_TIME0", "FRAME_TIME1", "FRAME_TIME2", "FRAME_TIME3")
        ft_reg = frame_time_reg*hmax/120.0
        if ft_reg > frame_time:
            return ft_reg
    return frame_time


def calc_nraw(reg_dict):
    """
    Return the number of raw frames used in a depth frame 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 

    Returns 
    nraw : int 
        The number of raw frames in a depth sequence  
    """
    return reg_dict["PHASE_COUNT"][2]


def set_nraw(reg_dict, nraw):
    """
    Sets the number of raw frames in a depth sequence 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    nraw : int 
        The number of raw frames in a depth sequence must be between 1 and 8. 
    """
    if nraw < 1 or nraw > 8:
        raise RuntimeError(
            "Invalid number of raw frames, must be between 1 and 8")
    reg_dict["PHASE_COUNT"][2] = int(nraw)


def calc_fps(reg_dict, mlx75027):
    """
    Calculates the frames per seconds, returns both the depth frame rate, and the raw frame rate. 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026

    Returns
    ----------
    depth_fps : float 
        The number of depth frames per second 
    raw_fps : float 
        The number of raw frames per second 
    """
    frame_time_us = calc_frame_time(reg_dict, mlx75027, use_frame_time=True)
    depth_fps = 1.0 / (frame_time_us*1e-6)
    raw_fps = depth_fps * reg_dict["PHASE_COUNT"][2]
    return depth_fps, raw_fps


def calc_roi(reg_dict):
    """
    Calculates the MLX75027 or MLX75026 region of interest. 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 

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


def set_roi(reg_dict, col_start, col_end, row_start, row_end, mlx75027):
    """
    Set the region of interest (ROI) of the MLX75027 or MLX75026 image sensor 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    col_start : int 
        The column start between 0 and 640 (or 320) 
    col_end : int 
        The column end between 0 and 640 (or 320)
    row_start : int 
        The row start between 0 and 480 (or 240)
    row_end : int 
        The row end between 0 and 480 (or 240)
    mlx75027 : bool
        Set to True if MLX75027, False for MLX75026
    """

    if mlx75027:
        col_max = 640
        row_max = 480
    else:
        col_max = 320
        row_max = 240

    # Check input data is correct
    if col_start < 1 or col_start > col_max:
        raise RuntimeError("Column start must be between 0 and 640")
    if col_end < 0 or col_end > col_max:
        raise RuntimeError("Column end must be between 0 and 640")
    if col_start >= col_end:
        raise RuntimeError("The column start must less than the column end")
    if row_start < 1 or row_start > row_max:
        raise RuntimeError("The row start must be between 0 and 482")
    if row_end < 0 or row_end > row_max:
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
    reg_dict : dict 
        The dictionary that contains all the register information 

    Returns 
    ----------
    duty_cycle : float 
        The duty cycle of the illumination output between 0.0 and 1.0  
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
    reg_dict : dict 
        The dictionary that contains all the register information 
    duty_cycle : float 
        The desired duty cycle from 0.0 to 1.0, will select the closest value. 
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
    # print("set_duty_cycle() - value_int: " + str(value_int))
    if value_int > 0xF:
        value_int = 0xF

    reg_dict["DUTY_CYCLE"][2] = cycle
    reg_dict["DUTY_CYCLE_VALUE"][2] = value_int
    return cycle, value_int


def calc_pll_setup(reg_dict, mlx75027):
    """
    Calculate the PLL setup time 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False
        if using the MLX75026 sensor. 

    Returns
    ----------
    pll_setup : int 
        The setup time. 
    """

    # print("calc_pll_setup()")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    pll_setup = np.ceil((503.0*120.0)/hmax + 8)
    return int(pll_setup)


def calc_randnm7(reg_dict, mlx75027):
    """
    Calculate the RANDMN7 register value 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False
        if using the MLX75026 sensor. 

    Returns
    ----------
    randnm7 : int 
        The randnm7 register value
    """

    # print("calc_randnm7()")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    pretime_enabled = np.any(
        reg_dict["Px_PREHEAT"][2] | reg_dict["Px_PREMIX"][2])

    if pretime_enabled:
        px_pretime = calc_pretime(reg_dict, mlx75027)
        # As noted in 7.12. can be calculated as: 1070 + HMAX * FLOOR( ((Px_PRETIME(in us)−11.13) / HMAX )* 120), with Px_PRETIME >= 11.13
        if px_pretime >= 11.13:
            randnm7 = 1070 + hmax * np.floor(((px_pretime-11.13)/hmax) * 120)
        else:
            randnm7 = 1070
    else:
        randnm7 = 1070
    return int(randnm7)


def calc_randnm0(reg_dict, mlx75027):
    """
    Calculate the RANDNM0 register value 

    Parameters
    ----------
    reg_dict : dict 
        The dictionary that contains all the register information 
    mlx75027 : bool
        Set to True if using the MLX75027 sensor, False
        if using the MLX75026 sensor. 

    Returns
    ----------
    randnm0 : int 
        The randnm0 register value  
    """

    # print("calc_randnm0")
    speed = calc_speed(reg_dict, mlx75027)
    hmax = calc_hmax(reg_dict, mlx75027, speed=speed)

    pixrst = calc_pretime(reg_dict, mlx75027)
    randnm7 = calc_randnm7(reg_dict, mlx75027)
    randnm0 = hmax*pixrst - randnm7 - 2098
    return int(randnm0)
