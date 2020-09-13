"""
Refael Whyte, r.whyte@chronoptics.com 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import copy
import platform

import numpy as np

from mlx75027_config import value16_to_reg, reg16_to_value

from mlx75027_config import epc_calc_mod_freq
from mlx75027_config import epc_calc_phase_steps
from mlx75027_config import epc_calc_int_times
from mlx75027_config import epc_set_int_times
from mlx75027_config import epc_calc_roi
from mlx75027_config import epc_calc_light_phase
from mlx75027_config import epc_setup_light_phase
from mlx75027_config import epc_calc_hdr
from mlx75027_config import epc_calc_dual_phase
from mlx75027_config import epc_set_mode

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from ToFSensorConfiguration import get_entry, update_entry


class EPC660PLLViewer(tk.Toplevel):
    def __init__(self, master, reg_dict, mclk, demod_clk):
        self.master = master
        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap('@Chronoptics.xbm')

        self.master.wm_title("Chronoptics - EPC660 PLL Configure")
        self.master.protocol("WM_DELETE_WINDOW", self.gui_exit)

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        tk.Grid.columnconfigure(self.master, 1, weight=1)
        tk.Grid.columnconfigure(self.master, 2, weight=1)
        tk.Grid.columnconfigure(self.master, 3, weight=1)
        tk.Grid.columnconfigure(self.master, 4, weight=1)

        tk.Grid.rowconfigure(self.master, 0, weight=1)

        self.mclk = mclk
        self.demod_clk = demod_clk
        self.reg_dict = copy.deepcopy(reg_dict)

        row_ind = 1

        # Modulation Frequency and clock source frequencies
        self.mclk_text = tk.Label(self.master, text="MCLK [MHz]:")
        self.mclk_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.mclk_entry = tk.Entry(self.master, bd=3)
        self.mclk_entry.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.demod_text = tk.Label(self.master, text="Demod CLK [MHz]:")
        self.demod_text.grid(row=row_ind, column=2, sticky=tk.E)
        self.demod_entry = tk.Entry(self.master, bd=3)
        self.demod_entry.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        self.demod_var = tk.IntVar()
        self.demod_check = tk.Checkbutton(self.master,
                                          text="Use DEMOD",
                                          variable=self.demod_var,
                                          command=self.update_can)
        self.demod_check.grid(row=row_ind, column=4, sticky=tk.W+tk.E)
        row_ind += 1
        self.mod_freq_act = tk.Label(self.master, text="Actual")
        self.mod_freq_act.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.mod_freq_clk_div = tk.Label(self.master, text="CLK_DIV")
        self.mod_freq_clk_div.grid(row=row_ind, column=2, sticky=tk.W+tk.E)

        row_ind += 1
        self.mod_freq_text = tk.Label(self.master, text="Mod Freq:")
        self.mod_freq_text.grid(row=row_ind, column=0, sticky=tk.E)
        clk_div_options = np.arange(1, 33)
        self.mod_freq_entry = tk.Entry(self.master, bd=3)
        self.mod_freq_entry.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.mod_freq_var = tk.StringVar(self.master)
        self.mod_freq_option = tk.OptionMenu(
            self.master, self.mod_freq_var, *clk_div_options)
        self.mod_freq_option.grid(row=row_ind, column=2, sticky=tk.W+tk.E)
        row_ind += 1
        self.set_clks()

        # Dual Phase
        self.dual_phase_text = tk.Label(self.master, text="Dual Phase:")
        self.dual_phase_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.dual_phase = tk.IntVar()
        self.dual_phase_check = tk.Checkbutton(self.master,
                                               text="Enable",
                                               variable=self.dual_phase,
                                               command=self.update_can)
        self.dual_phase_check.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        row_ind += 1
        self.set_dual_phase()

        # Sequence Configuration Tool
        dcs_step_text = tk.Label(self.master, text="PLL Step")
        dcs_step_text.grid(row=row_ind, column=1, sticky=tk.E+tk.W)
        abs_text = tk.Label(self.master, text="ABS")
        abs_text.grid(row=row_ind, column=2, sticky=tk.E+tk.W)
        led_mode_text = tk.Label(self.master, text="LED Mode")
        led_mode_text.grid(row=row_ind, column=3, sticky=tk.E+tk.W)
        dual_mode_text = tk.Label(self.master, text="Dual Step")
        dual_mode_text.grid(row=row_ind, column=4, sticky=tk.E+tk.W)
        row_ind += 1

        self.dcs_texts = []
        self.dcs_vars = []
        self.dcs_steps = []
        self.abs_checks = []
        self.abs_vars = []
        self.led_vars = []
        self.led_options = []
        self.dual_vars = []
        self.dual_steps = []
        dcs_options = [0, 1, 2, 3]
        led_modes = ["On", "Off", "Modulated"]
        for n in range(0, 4):
            # We start adding parse
            dcs_text = tk.Label(self.master, text="DCS"+str(n))
            dcs_text.grid(row=row_ind+n, column=0, sticky=tk.E)
            self.dcs_texts.append(dcs_text)

            dcs_var = tk.StringVar(self.master)
            dcs_option = tk.OptionMenu(self.master, dcs_var, *dcs_options)
            dcs_option.grid(row=row_ind+n, column=1, sticky=tk.E+tk.W)
            self.dcs_vars.append(dcs_var)
            self.dcs_steps.append(dcs_option)

            abs_var = tk.IntVar()
            abs_check = tk.Checkbutton(self.master,
                                       text="enable",
                                       variable=abs_var,
                                       command=self.update_can)
            abs_check.grid(row=row_ind+n, column=2, sticky=tk.E+tk.W)
            self.abs_vars.append(abs_var)
            self.abs_checks.append(abs_check)

            led_var = tk.StringVar(self.master)
            led_option = tk.OptionMenu(self.master, led_var, *led_modes)
            led_option.grid(row=row_ind+n, column=3, sticky=tk.E+tk.W)
            self.led_vars.append(led_var)
            self.led_options.append(led_option)

            dual_var = tk.StringVar(self.master)
            dual_option = tk.OptionMenu(self.master, dual_var, *dcs_options)
            dual_option.grid(row=row_ind+n, column=4, sticky=tk.W+tk.E)
            self.dual_vars.append(dual_var)
            self.dual_steps.append(dual_option)

        self.set_dcs()
        row_ind += 4

        # Integration time configuration
        self.int_mult_text = tk.Label(self.master, text="Multipler")
        self.int_mult_text.grid(row=row_ind, column=1, sticky=tk.E+tk.W)
        self.int_len_text = tk.Label(self.master, text="Int Len")
        self.int_len_text.grid(row=row_ind, column=2, sticky=tk.E+tk.W)
        self.int_time_text = tk.Label(self.master, text="Time [ms]")
        self.int_time_text.grid(row=row_ind, column=3, sticky=tk.E+tk.W)

        row_ind += 1

        self.int_time_text = tk.Label(self.master, text="Integration Time:")
        self.int_time_text.grid(row=row_ind, column=0, sticky=tk.E)

        self.int_time_mult = tk.Entry(self.master, bd=3)
        self.int_time_mult.grid(row=row_ind, column=1, sticky=tk.E+tk.W)

        self.int_len = tk.Entry(self.master, bd=3)
        self.int_len.grid(row=row_ind, column=2, sticky=tk.E+tk.W)

        self.int_time = tk.Entry(self.master, bd=3)
        self.int_time.grid(row=row_ind, column=3, sticky=tk.E+tk.W)

        row_ind += 1

        self.hdr_text = tk.Label(self.master, text="HDR:")
        self.hdr_text.grid(row=row_ind, column=0, sticky=tk.E)

        self.hdr_var = tk.IntVar()
        self.hdr_check = tk.Checkbutton(self.master,
                                        text="enable",
                                        variable=self.hdr_var,
                                        command=self.update_can)
        self.hdr_check.grid(row=row_ind, column=1, sticky=tk.E)
        self.int_len2 = tk.Entry(self.master, bd=3)

        self.int_len2.grid(row=row_ind, column=2, sticky=tk.E+tk.W)
        self.int_time2 = tk.Entry(self.master, bd=3)
        self.int_time2.grid(row=row_ind, column=3, sticky=tk.E+tk.W)

        row_ind += 1

        self.set_int_time()

        # Light Source Phase Configuration
        self.light_ph_act_text = tk.Label(self.master, text="Phase [deg]")
        self.light_ph_act_text.grid(row=row_ind, column=2, sticky=tk.E+tk.W)

        row_ind += 1

        self.light_ph_text = tk.Label(self.master, text="Light Phase:")
        self.light_ph_text.grid(row=row_ind, column=0, stick=tk.E)

        """
        self.light_ph_var = tk.IntVar()
        self.light_ph_check = tk.Checkbutton(self.master,
                                             text="enable",
                                             variable=self.light_ph_var)  # command=self.update_can)
        self.light_ph_check.grid(row=row_ind, column=1, sticky=tk.E)
        """
        self.light_ph = tk.Entry(self.master, bd=3)
        self.light_ph.grid(row=row_ind, column=2, sticky=tk.E+tk.W)
        row_ind += 1
        self.set_light_phase()

        # Gray Scale Configuration (Common Mode)
        self.cm_led_text = tk.Label(self.master, text="LED Mode")
        self.cm_led_text.grid(row=row_ind, column=2, sticky=tk.W+tk.E)
        row_ind += 1

        self.cm_text = tk.Label(self.master, text="Common Mode:")
        self.cm_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.cm_enable_var = tk.IntVar()
        self.cm_enable_check = tk.Checkbutton(self.master,
                                              text="enable",
                                              variable=self.cm_enable_var,
                                              command=self.update_can)
        self.cm_enable_check.grid(row=row_ind, column=1, sticky=tk.E)
        cm_led_options = ["Off", "On", "Modulated"]
        self.cm_led_var = tk.StringVar(self.master)
        self.cm_led_var.set(cm_led_options[0])
        self.cm_led_option = tk.OptionMenu(
            self.master, self.cm_led_var, *cm_led_options)
        self.cm_led_option.grid(row=row_ind, column=2, sticky=tk.E+tk.W)

        row_ind += 1
        self.set_common_mode()

        ###
        self.but_update = tk.Button(
            self.master, text="Update", command=self.update_can)
        self.but_update.grid(row=row_ind, column=0, sticky=tk.N+tk.S+tk.W+tk.E)

        self.but_exit = tk.Button(
            self.master, text="Exit", command=self.gui_exit)
        self.but_exit.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        return

    def set_dual_phase(self):
        self.dual_phase.set(epc_calc_dual_phase(self.reg_dict))
        return

    def get_dual_phase(self):
        dual_phase = self.dual_phase.get()
        hdr = self.hdr_var.get()
        common_mode = self.cm_enable_var.get()
        epc_set_mode(self.reg_dict, dual_phase, common_mode, hdr)
        return

    def set_clks(self):
        update_entry(self.mclk_entry, self.mclk, disable=False)
        update_entry(self.demod_entry, self.demod_clk, disable=False)
        self.demod_var.set(self.reg_dict["mod_clk_src"][2])
        self.mod_freq_var.set(self.reg_dict["mod_clk_div"][2] + 1)
        f_led = epc_calc_mod_freq(self.reg_dict, self.mclk, self.demod_clk)
        update_entry(self.mod_freq_entry, f_led, disable=True)
        return

    def get_clks(self):
        self.reg_dict["mod_clk_src"][2] = self.demod_var.get()
        self.mclk = float(self.mclk_entry.get())
        self.demod_clk = float(self.demod_entry.get())
        self.reg_dict["mod_clk_div"][2] = int(
            float(self.mod_freq_var.get())) - 1
        return

    def set_dcs(self):
        for n in range(0, 4):
            if self.reg_dict["led_on_int_"+str(n)][2] == 0 and self.reg_dict["led_off_int_"+str(n)][2] == 1:
                led_mode = "Off"
            elif self.reg_dict["led_on_int_"+str(n)][2] == 1 and self.reg_dict["led_off_int_"+str(n)][2] == 0:
                led_mode = "On"
            elif self.reg_dict["led_on_int_"+str(n)][2] == 0 and self.reg_dict["led_off_int_"+str(n)][2] == 0:
                led_mode = "Modulated"
            self.led_vars[n].set(led_mode)
            self.dcs_vars[n].set(self.reg_dict["dcs_mgx0_"+str(n)][2])
            self.abs_vars[n].set(self.reg_dict["abs_"+str(n)][2] == 3)
            self.dual_vars[n].set(self.reg_dict["dcs_mgx1_"+str(n)][2])

        return

    def get_dcs(self):
        for n in range(0, 4):
            led_mode = self.led_vars[n].get()
            if led_mode == "Off":
                self.reg_dict["led_on_int_"+str(n)][2] = 0
                self.reg_dict["led_off_int_"+str(n)][2] = 1
            elif led_mode == "On":
                self.reg_dict["led_on_int_"+str(n)][2] = 1
                self.reg_dict["led_off_int_"+str(n)][2] = 0
            elif led_mode == "Modulated":
                self.reg_dict["led_on_int_"+str(n)][2] = 0
                self.reg_dict["led_off_int_"+str(n)][2] = 0

            dcs_step = self.dcs_vars[n].get()
            self.reg_dict["dcs_mgx0_"+str(n)][2] = int(float(dcs_step))
            abs_enable = self.abs_vars[n].get()
            if abs_enable:
                self.reg_dict["abs_"+str(n)][2] = 3
            else:
                self.reg_dict["abs_"+str(n)][2] = 0

            dual_mode = self.dual_vars[n].get()
            self.reg_dict["dcs_mgx1_"+str(n)][2] = int(float(dual_mode))
        return

    def set_common_mode(self):
        # We
        cm_enable = self.reg_dict["num_dcs"][2] == 0 and self.reg_dict["mod_sel"][2] == 3
        self.cm_enable_var.set(cm_enable)

        if cm_enable:
            self.cm_led_option.config(state='normal')
            # We set the value
            # self.cm_led_option.set(led_mode)
        else:
            self.cm_led_option.config(state='disabled')

        if self.reg_dict["led_on_int_gray"][2] == 0 and self.reg_dict["led_off_int_gray"][2] == 0:
            led_mode = "Modulated"
        elif self.reg_dict["led_on_int_gray"][2] == 1 and self.reg_dict["led_off_int_gray"][2] == 0:
            led_mode = "On"
        elif self.reg_dict["led_on_int_gray"][2] == 0 and self.reg_dict["led_off_int_gray"][2] == 1:
            led_mode = "Off"
        self.cm_led_var.set(led_mode)
        #print("CM Led Mode: " + led_mode)
        return

    def get_common_mode(self):
        cm_enabled = self.cm_enable_var.get()
        if cm_enabled:
            # XXX : Will change if dual phase is enabled
            self.reg_dict["num_dcs"][2] = 0
            self.reg_dict["mod_sel"][2] = 3

            led_mode = self.cm_led_var.get()
            if led_mode == "Off":
                # We set some register values
                self.reg_dict["led_on_int_gray"][2] = 0
                self.reg_dict["led_off_int_gray"][2] = 1
            elif led_mode == "On":
                self.reg_dict["led_on_int_gray"][2] = 1
                self.reg_dict["led_off_int_gray"][2] = 0
            elif led_mode == "Modulated":
                self.reg_dict["led_on_int_gray"][2] = 0
                self.reg_dict["led_off_int_gray"][2] = 0
        else:
            dual_phase = self.dual_phase.get()
            if dual_phase:
                self.reg_dict["num_dcs"][2] = 1
            else:
                self.reg_dict["num_dcs"][2] = 3
            self.reg_dict["mod_sel"][2] = 0
        return

    def set_light_phase(self):
        light_phase = epc_calc_light_phase(
            self.reg_dict, self.mclk, self.demod_clk)
        update_entry(self.light_ph, np.round(
            light_phase, 1), False)
        return

    def get_light_phase(self):

        phase_desired = float(self.light_ph.get())
        epc_setup_light_phase(self.reg_dict,
                              phase_desired, self.mclk, self.demod_clk)
        return

    def set_int_time(self):
        # Used to update the information displayed from internal variables
        hdr_enabled = epc_calc_hdr(self.reg_dict)
        self.hdr_var.set(hdr_enabled)

        int_len2 = self.reg_dict["int_len2_hi"][2] * \
            256 + self.reg_dict["int_len2_low"][2]
        int_len = self.reg_dict["int_len_hi"][2] * \
            256 + self.reg_dict["int_len_low"][2]
        mult_val = self.reg_dict["int_mult_hi"][2] * \
            256 + self.reg_dict["int_mult_low"][2]
        int_times = epc_calc_int_times(
            self.reg_dict, self.mclk, self.demod_clk)

        update_entry(self.int_time_mult, mult_val, True)
        update_entry(self.int_len, int_len, True)
        update_entry(self.int_len2, int_len2, True)

        update_entry(self.int_time, np.round(int_times[0], 4), False)
        if hdr_enabled:
            update_entry(self.int_time2, np.round(
                int_times[1], 4), not hdr_enabled)
        else:
            update_entry(self.int_time2, 0, not hdr_enabled)

        return

    def get_int_time(self):
        # Get the integration time values from the gui and update internal values
        hdr_enabled = self.hdr_var.get()
        if hdr_enabled:
            self.reg_dict["pixel_mode"][2] = 1
            self.reg_dict["dual_int_mode"][2] = 1
        else:
            self.reg_dict["dual_int_mode"][2] = 0
            # It depends on dual phase, but currently not supported
            dual_phase = self.dual_phase.get()
            if dual_phase:
                self.reg_dict["pixel_mode"][2] = 1
            else:
                self.reg_dict["pixel_mode"][2] = 0

        int_time = float(self.int_time.get())
        if hdr_enabled:
            # print("hdr_enabled:")
            int_time2 = float(self.int_time2.get())
            int_times = np.array([int_time, int_time2])
        else:
            int_times = np.array([int_time])

        epc_set_int_times(self.reg_dict, int_times, self.mclk, self.demod_clk)
        return

    def update_can(self):
        # Get all the values and update everything
        self.get_clks()
        self.set_clks()
        self.get_dual_phase()
        self.set_dual_phase()
        self.get_dcs()
        self.set_dcs()
        self.get_int_time()
        self.set_int_time()
        self.get_light_phase()
        self.set_light_phase()
        self.get_common_mode()
        self.set_common_mode()
        return

    def gui_exit(self):
        self.master.destroy()
        return
