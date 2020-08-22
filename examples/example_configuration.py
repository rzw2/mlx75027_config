
import os

import numpy as np
import mlx75027_config as mlx

# Camera configuration

# 35MHz modulation frequency
mod_freq = 35.0
# Two readout lanes
nlanes = 2
# Reading out at 800 Mbps
speed = 800
# Phase steps of 0, 90, 180, 270 degrees
phase_steps = np.array([0.0, 0.25, 0.5, 0.75])
# Integration time of 250us per raw frame
int_times = np.array([250, 250, 250, 250])
# Four raw frames being used
nphases = 4
# duty cycle of 50%
duty_cycle = 0.5
# Full VGA output
row_start = 1
row_end = 480
col_start = 1
col_end = 640
# Binning of 0 (full VGA)
binning = 0
# Output mode of A-B
output_mode = 0

csvFile = os.path.join("..", "mlx75027.csv")

# The update order is important!!
reg_dict = mlx.csv_import(csvFile)
mlx.set_nlanes(reg_dict, nlanes)
mlx.set_output_mode(reg_dict, output_mode)
hmax = mlx.calc_hmax(reg_dict, speed=speed)
mlx.set_hmax(reg_dict, hmax)
mlx.set_roi(reg_dict, col_start, col_end, row_start, row_end)
mlx.set_mod_freq(reg_dict, mod_freq)
mlx.set_nraw(reg_dict, nphases)
mlx.set_int_times(reg_dict, int_times)
mlx.set_binning(reg_dict, binning)
mlx.set_duty_cycle(reg_dict, duty_cycle)
mlx.set_phase_shift(reg_dict, phase_steps)

# Export CSV file of registers
mlx.csv_export_registers("config_registers.csv", reg_dict)
