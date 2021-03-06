"""
mlx75027_config is the configuration library for the Melexis MLX75027 time of flight (tof) image sensor provided by Chronoptics

The library contains the following functions 

    * csv_export_registers - 
    * csv_export - 

"""

from mlx75027_config.CSVConfigIO import csv_export_registers, csv_export, csv_import, dict_to_registers, calc_bits, check_reg_dict
from mlx75027_config.SensorConfig import value16_to_reg, value24_to_reg, value32_to_reg, reg24_to_value, reg16_to_value, reg_to_value

from mlx75027_config.MLX75027Config import calc_startup_time, set_startup_time, set_deadtime, calc_deadtime, calc_int_times, set_int_times
from mlx75027_config.MLX75027Config import calc_all_pretimes, calc_pretime, set_pretime, set_mod_freq, calc_mod_freq, calc_frame_time
from mlx75027_config.MLX75027Config import calc_fps, calc_idle_time, calc_duty_cycle, set_duty_cycle, calc_roi, set_roi, calc_speed
from mlx75027_config.MLX75027Config import calc_hmax, calc_pll_setup, calc_randnm7, calc_randnm0
from mlx75027_config.MLX75027Config import calc_nraw, set_nraw, calc_phase_shifts, calc_binning, set_binning
from mlx75027_config.MLX75027Config import calc_leden, set_leden, set_frame_time
from mlx75027_config.MLX75027Config import calc_preheat, set_preheat, calc_premix, set_premix, set_phase_shift
from mlx75027_config.MLX75027Config import calc_nlanes, set_nlanes, set_hmax, calc_output_mode, set_output_mode
from mlx75027_config.MLX75027Config import calc_analog_delay, set_analog_delay

# The EPC660 functions
from mlx75027_config.EPC660Config import epc_calc_mod_freq, epc_calc_phase_steps, epc_calc_int_times, epc_set_int_times, epc_calc_roi_coordinates
from mlx75027_config.EPC660Config import epc_calc_roi, epc_calc_light_phase, epc_setup_light_phase, epc_calc_hdr, epc_calc_dual_phase, epc_set_mode
from mlx75027_config.EPC660Config import epc_set_roi, epc_calc_bin_mode, epc_set_bin_mode, epc_calc_binning, epc_set_binning, epc_set_mod_freq, epc_calc_img_size
from mlx75027_config.EPC660Config import epc_set_phase_steps, epc_calc_phase_steps, epc_calc_external_mod, epc_set_external_mod
