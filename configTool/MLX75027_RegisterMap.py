"""
Refael Whyte, r.whyte@chronoptics.com 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import copy
import platform

import numpy as np
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from ToFSensorConfiguration import RegisterViewer
from ToFSensorConfiguration import BaseROIViewer
import mlx75027_config as mlx


def cal_scale(canvas_size, img_size):
    # Now figure out how much to resize my
    row_scale = float(canvas_size[0]) / float(img_size[0])
    col_scale = float(canvas_size[1]) / float(img_size[1])
    # We take the smallest scale factor as it is the one that can fit
    scale = np.min(np.array([row_scale, col_scale]))
    return scale


class MLX75027TimeViewer(tk.Toplevel):
    def __init__(self, master, reg_dict):
        # We want to do the timing stuff here
        self.master = master
        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap('@Chronoptics.xbm')
        self.master.wm_title("Chronoptics - MLX75027 Time Configure")
        self.master.protocol("WM_DELETE_WINDOW", self.gui_exit)

        # Do the resize
        tk.Grid.rowconfigure(self.master, 0, weight=1)
        tk.Grid.rowconfigure(self.master, 1, weight=1)
        tk.Grid.rowconfigure(self.master, 2, weight=1)
        tk.Grid.rowconfigure(self.master, 3, weight=1)
        tk.Grid.rowconfigure(self.master, 4, weight=1)
        tk.Grid.rowconfigure(self.master, 5, weight=1)
        tk.Grid.rowconfigure(self.master, 6, weight=1)
        tk.Grid.rowconfigure(self.master, 7, weight=1)
        tk.Grid.rowconfigure(self.master, 8, weight=1)
        tk.Grid.rowconfigure(self.master, 9, weight=1)
        tk.Grid.rowconfigure(self.master, 10, weight=1)
        tk.Grid.rowconfigure(self.master, 11, weight=1)
        tk.Grid.rowconfigure(self.master, 12, weight=1)
        tk.Grid.rowconfigure(self.master, 13, weight=1)
        tk.Grid.rowconfigure(self.master, 14, weight=1)
        tk.Grid.rowconfigure(self.master, 15, weight=1)

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        tk.Grid.columnconfigure(self.master, 1, weight=1)
        tk.Grid.columnconfigure(self.master, 2, weight=1)
        tk.Grid.columnconfigure(self.master, 3, weight=1)
        tk.Grid.columnconfigure(self.master, 4, weight=1)
        tk.Grid.columnconfigure(self.master, 5, weight=1)
        tk.Grid.columnconfigure(self.master, 6, weight=1)
        tk.Grid.columnconfigure(self.master, 7, weight=1)
        tk.Grid.columnconfigure(self.master, 8, weight=1)
        tk.Grid.columnconfigure(self.master, 9, weight=1)
        tk.Grid.columnconfigure(self.master, 10, weight=1)
        tk.Grid.columnconfigure(self.master, 11, weight=1)

        self.reg_dict = copy.deepcopy(reg_dict)
        row_ind = 1

        self.raw_text = tk.Label(self.master, text="N RAW:")
        self.raw_text.grid(row=row_ind, column=1, sticky=tk.E)

        raw_opts = [1, 2, 3, 4, 5, 6, 7, 8]
        self.nraw_var = tk.StringVar(self.master)
        self.nraw_option = tk.OptionMenu(self.master, self.nraw_var, *raw_opts)
        self.nraw_option.grid(row=row_ind, column=2, sticky=tk.W+tk.E)

        self.fmod_text = tk.Label(self.master, text="Modulation Frequency:")
        self.fmod_text.grid(row=row_ind, column=3, sticky=tk.E)

        self.fmod_entry = tk.Entry(self.master, bd=3)
        self.fmod_entry.grid(row=row_ind, column=4, sticky=tk.W+tk.E)

        self.duty_cycle_text = tk.Label(self.master, text="Duty Cycle:")
        self.duty_cycle_text.grid(row=row_ind, column=5, sticky=tk.E)

        self.duty_cycle_entry = tk.Entry(self.master, bd=3)
        self.duty_cycle_entry.grid(row=row_ind, column=6, sticky=tk.W+tk.E)

        self.set_nraw()
        row_ind += 1

        # We want the MIPI speed, MIPI number of lanes and output Data type
        self.speed_list = [300, 600, 704, 800, 960]
        self.mipi_lanes = [2, 4]
        self.data_modes = ["a-b", "a+b", "a", "b", "a&b"]

        self.speed_text = tk.Label(self.master, text="MIPI Speed:")
        self.speed_text.grid(row=row_ind, column=1, sticky=tk.E)

        self.speed_var = tk.StringVar(self.master)
        self.speed_opt = tk.OptionMenu(
            self.master, self.speed_var, *self.speed_list)
        self.speed_opt.grid(row=row_ind, column=2, sticky=tk.W+tk.E)

        self.lane_text = tk.Label(self.master, text="MIPI Lanes:")
        self.lane_text.grid(row=row_ind, column=3, sticky=tk.E)

        self.lane_var = tk.StringVar(self.master)
        self.lane_opt = tk.OptionMenu(
            self.master, self.lane_var, *self.mipi_lanes)
        self.lane_opt.grid(row=row_ind, column=4, sticky=tk.W+tk.E)

        self.mode_text = tk.Label(self.master, text="Data Mode:")
        self.mode_text.grid(row=row_ind, column=5, sticky=tk.E)

        self.mode_var = tk.StringVar(self.master)
        self.mode_opt = tk.OptionMenu(
            self.master, self.mode_var, *self.data_modes)
        self.mode_opt.grid(row=row_ind, column=6, sticky=tk.W+tk.E)

        self.set_mipi()

        # Canvas for Chronoptics Logo
        self.resize_ratio = 0.2
        self.ruru_size = [1909, 575]

        self.canvas = tk.Canvas(self.master, width=int(
            self.ruru_size[0]*self.resize_ratio), height=int(self.ruru_size[1]*self.resize_ratio))
        self.canvas.grid(row=(row_ind-1), column=7, rowspan=2,
                         columnspan=5, sticky=tk.W+tk.E+tk.N+tk.S)
        self.ruruImg = Image.open("Chronoptics_blue_landscape.png")
        self.ruruTk = ImageTk.PhotoImage(self.ruruImg.resize(
            (int(self.ruru_size[0]*self.resize_ratio*0.95), int(self.ruru_size[1]*self.resize_ratio*0.95)), Image.ANTIALIAS))
        yOffset = (int(self.ruru_size[0]*self.resize_ratio) -
                   int(self.ruru_size[0]*self.resize_ratio*0.95)) / 2
        #xOffset = (self.canvas.width - int(self.ruru_size[1]*self.resize_ratio*0.95) ) / 2
        xOffset = 120
        self.image_on_canvas = self.canvas.create_image(
            int(xOffset), int(yOffset), image=self.ruruTk, anchor=tk.NW)
        self.canvas.bind("<Configure>", self.on_resize)

        row_ind += 1

        self.time_label = tk.Label(self.master, text="Time [us]")
        self.time_label.grid(row=row_ind, column=1, sticky=tk.W+tk.E)

        self.preheat_label = tk.Label(self.master, text="PreHeat Enable")
        self.preheat_label.grid(row=row_ind, column=2, sticky=tk.W+tk.E)

        self.premix_label = tk.Label(self.master, text="PreMix Enable")
        self.premix_label.grid(row=row_ind, column=3, sticky=tk.W+tk.E)

        self.pretime_time_label = tk.Label(
            self.master, text="Total PreTime [us]")
        self.pretime_time_label.grid(row=row_ind, column=4, sticky=tk.W+tk.E)

        self.integration_time_label = tk.Label(
            self.master, text="Integration Time [us]")
        self.integration_time_label.grid(
            row=row_ind, column=5, sticky=tk.W+tk.E)

        self.ideal_time_label = tk.Label(self.master, text="Idle Time [us]")
        self.ideal_time_label.grid(row=row_ind, column=6, sticky=tk.W+tk.E)

        self.led_en_label = tk.Label(self.master, text="Illum Pulse")
        self.led_en_label.grid(row=row_ind, column=7, sticky=tk.W+tk.E)

        self.dmix0_label = tk.Label(self.master, text="DMIX0")
        self.dmix0_label.grid(row=row_ind, column=8, sticky=tk.W+tk.E)

        self.dmix1_label = tk.Label(self.master, text="DMIX1")
        self.dmix1_label.grid(row=row_ind, column=9, sticky=tk.W+tk.E)

        self.illum_label = tk.Label(self.master, text="Illum")
        self.illum_label.grid(row=row_ind, column=10, sticky=tk.W+tk.E)

        self.phase_label = tk.Label(self.master, text="Phase Shift")
        self.phase_label.grid(row=row_ind, column=11, sticky=tk.W+tk.E)

        row_ind += 1

        # Now setup the frames
        self.frame_startup_text = tk.Label(
            self.master, text="Startup Time [us]")
        self.frame_startup_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.frame_startup_entry = tk.Entry(self.master, bd=3)
        self.frame_startup_entry.grid(row=row_ind, column=1, sticky=tk.E+tk.W)

        row_ind += 1

        self.pretime_text = tk.Label(self.master, text="Pretime [us]")
        self.pretime_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.pretime_entry = tk.Entry(self.master, bd=3)
        self.pretime_entry.grid(row=row_ind, column=1, sticky=tk.E+tk.W)

        row_ind += 1

        self.raw_texts = []
        self.preheat_checks = []
        self.preheat_vars = []
        self.premix_checks = []
        self.premix_vars = []
        self.pretime_entrys = []
        self.inttime_entrys = []
        self.idle_entrys = []
        self.illum_checks = []
        self.illum_vars = []

        self.mod_modes = ["Modulation", "Undefined", "Static Low", "Static Hi"]
        mod_modes = ["Modulation", "Static Low", "Static Hi"]

        phi_shifts = [0, 45, 90, 135, 180, 225, 270, 315]
        self.phi_shifts = phi_shifts

        self.dmix0_vars = []
        self.dmix0_opts = []
        self.dmix1_vars = []
        self.dmix1_opts = []
        self.led_vars = []
        self.led_opts = []

        self.phi_vars = []
        self.phi_opts = []

        for n in range(0, 8):
            raw_text = tk.Label(self.master, text="Phase " + str(n+1))
            raw_text.grid(row=row_ind, column=0, sticky=tk.E)
            self.raw_texts.append(raw_text)

            preheat_var = tk.IntVar()
            preheat_check = tk.Checkbutton(self.master,
                                           text="enable",
                                           variable=preheat_var,
                                           command=self.update_can)
            preheat_check.grid(row=row_ind, column=2, sticky=tk.E+tk.W)
            self.preheat_checks.append(preheat_check)
            self.preheat_vars.append(preheat_var)

            premix_var = tk.IntVar()
            premix_check = tk.Checkbutton(self.master,
                                          text="enable",
                                          variable=premix_var,
                                          command=self.update_can)
            premix_check.grid(row=row_ind, column=3, sticky=tk.E+tk.W)
            self.premix_checks.append(premix_check)
            self.premix_vars.append(premix_var)

            pretime_entry = tk.Entry(self.master, bd=3)
            pretime_entry.grid(row=row_ind, column=4, sticky=tk.W+tk.E)
            self.pretime_entrys.append(pretime_entry)

            inttime_entry = tk.Entry(self.master, bd=3)
            inttime_entry.grid(row=row_ind, column=5, sticky=tk.W+tk.E)
            self.inttime_entrys.append(inttime_entry)

            idle_entry = tk.Entry(self.master, bd=3)
            idle_entry.grid(row=row_ind, column=6, sticky=tk.W+tk.E)
            self.idle_entrys.append(idle_entry)

            illum_var = tk.IntVar()
            illum_check = tk.Checkbutton(self.master,
                                         text="LED Pulse",
                                         variable=illum_var,
                                         command=self.update_can)
            illum_check.grid(row=row_ind, column=7, sticky=tk.W+tk.E)

            self.illum_checks.append(illum_check)
            self.illum_vars.append(illum_var)

            dmix0_var = tk.StringVar(self.master)
            dmix0_opt = tk.OptionMenu(self.master, dmix0_var, *mod_modes)
            dmix0_opt.grid(row=row_ind, column=8, sticky=tk.W+tk.E)
            self.dmix0_vars.append(dmix0_var)
            self.dmix0_opts.append(dmix0_opt)

            dmix1_var = tk.StringVar(self.master)
            dmix1_opt = tk.OptionMenu(self.master, dmix1_var, *mod_modes)
            dmix1_opt.grid(row=row_ind, column=9, sticky=tk.W+tk.E)
            self.dmix1_vars.append(dmix1_var)
            self.dmix1_opts.append(dmix1_opt)

            led_var = tk.StringVar(self.master)
            led_opt = tk.OptionMenu(self.master, led_var, *mod_modes)
            led_opt.grid(row=row_ind, column=10, sticky=tk.W+tk.E)
            self.led_vars.append(led_var)
            self.led_opts.append(led_opt)

            phi_var = tk.StringVar(self.master)
            phi_opt = tk.OptionMenu(self.master, phi_var, *phi_shifts)
            phi_opt.grid(row=row_ind, column=11, sticky=tk.W+tk.E)
            self.phi_vars.append(phi_var)
            self.phi_opts.append(phi_opt)

            row_ind += 1

        self.frame_dead_text = tk.Label(self.master, text="Dead Time [us]")
        self.frame_dead_text.grid(row=row_ind, column=0, sticky=tk.E)

        self.frame_dead_entry = tk.Entry(self.master, bd=3)
        self.frame_dead_entry.grid(row=row_ind, column=1, sticky=tk.E+tk.W)

        row_ind += 1

        self.frame_time_text = tk.Label(self.master, text="Depth Time [us]")
        self.frame_time_text.grid(row=row_ind, column=0, sticky=tk.E)

        self.frame_time_entry = tk.Entry(self.master, bd=3)
        self.frame_time_entry.grid(row=row_ind, column=1, sticky=tk.E+tk.W)

        self.frame_fps_text = tk.Label(self.master, text="Depth fps")
        self.frame_fps_text.grid(row=row_ind, column=2, sticky=tk.E)

        self.frame_fps_entry = tk.Entry(self.master, bd=3)
        self.frame_fps_entry.grid(row=row_ind, column=3, sticky=tk.W+tk.E)

        self.set_frame()

        self.update_can()

        row_ind += 1

        self.but_update = tk.Button(
            self.master, text="Update", command=self.update_can)
        self.but_update.grid(row=row_ind, column=1, sticky=tk.W+tk.E)

        self.but_exit = tk.Button(
            self.master, text="Exit", command=self.gui_exit)
        self.but_exit.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        return

    def on_resize(self, event):

        canvas_size = [event.width, event.height]
        self.resize_ratio = cal_scale(canvas_size, self.ruru_size)

        self.ruruTk = ImageTk.PhotoImage(self.ruruImg.resize(
            (int(self.ruru_size[0]*self.resize_ratio*0.95), int(self.ruru_size[1]*self.resize_ratio*0.95)), Image.ANTIALIAS))
        # The new x,y posistion ...
        yOffset = (int(self.ruru_size[1]*self.resize_ratio) -
                   int(self.ruru_size[1]*self.resize_ratio*0.95)) / 2
        xOffset = (event.width -
                   int(self.ruru_size[0]*self.resize_ratio*0.95)) / 2
        # The current x,y posistion
        cords = self.canvas.coords(self.image_on_canvas)

        self.canvas.itemconfig(self.image_on_canvas, image=self.ruruTk)
        self.canvas.move(self.image_on_canvas, int(
            xOffset-cords[0]), int(yOffset-cords[1]))
        return

    def get_nraw(self):
        nraw = int(float(self.nraw_var.get()))
        mlx.set_nraw(self.reg_dict, nraw)
        fmod = self.get_entry(self.fmod_entry, 4.0, 100.0)
        mlx.set_mod_freq(self.reg_dict, fmod)
        mlx.set_duty_cycle(self.reg_dict, self.get_entry(
            self.duty_cycle_entry, 0.0, 1.0))
        return

    def set_nraw(self):
        nraw = mlx.calc_nraw(self.reg_dict)
        self.nraw_var.set(nraw)
        fmod = mlx.calc_mod_freq(self.reg_dict)
        self.update_entry(self.fmod_entry, fmod)
        self.update_entry(self.duty_cycle_entry,
                          mlx.calc_duty_cycle(self.reg_dict))
        return

    def set_frame(self):
        self.update_entry(self.frame_startup_entry,
                          mlx.calc_startup_time(self.reg_dict))
        self.update_entry(self.frame_dead_entry,
                          mlx.calc_deadtime(self.reg_dict))
        self.update_entry(self.pretime_entry, mlx.calc_pretime(self.reg_dict))

        int_times = mlx.calc_int_times(self.reg_dict)
        pretimes = mlx.calc_all_pretimes(self.reg_dict)
        idle_times = mlx.calc_idle_time(self.reg_dict)
        for n in range(0, 8):
            if (n+1) > mlx.calc_nraw(self.reg_dict):
                disable = True
            else:
                disable = False

            self.update_entry(
                self.inttime_entrys[n], int_times[n], disable=disable)
            self.update_entry(
                self.pretime_entrys[n], pretimes[n], disable=True)

            heat = self.reg_dict["Px_PREHEAT"][2] & (1 << n)
            if heat:
                self.preheat_vars[n].set(1)
            else:
                self.preheat_vars[n].set(0)

            mix = self.reg_dict["Px_PREMIX"][2] & (1 << n)
            if mix:
                self.premix_vars[n].set(1)
            else:
                self.premix_vars[n].set(0)

            led = self.reg_dict["Px_LEDEN"][2] & (1 << n)
            if led:
                self.illum_vars[n].set(1)
            else:
                self.illum_vars[n].set(0)

            dmix0 = self.reg_dict["P"+str(n+1)+"_DMIX0"][2]
            self.dmix0_vars[n].set(self.mod_modes[dmix0])

            dmix1 = self.reg_dict["P"+str(n+1)+"_DMIX1"][2]
            self.dmix1_vars[n].set(self.mod_modes[dmix1])

            ledmod = self.reg_dict["P"+str(n+1)+"_STATIC_LED"][2]
            self.led_vars[n].set(self.mod_modes[ledmod])

            self.phi_vars[n].set(
                self.phi_shifts[self.reg_dict["P"+str(n)+"_PHASE_SHIFT"][2]])

            self.update_entry(self.idle_entrys[n], idle_times[n])

        frame_time = mlx.calc_frame_time(self.reg_dict)
        depth_fps, raw_fps = mlx.calc_fps(self.reg_dict)

        self.update_entry(self.frame_fps_entry, depth_fps, disable=True)
        self.update_entry(self.frame_time_entry, frame_time, disable=True)

        return

    def get_frame(self):
        startup_time = self.get_entry(self.frame_startup_entry, 0, 2**32)
        mlx.set_startup_time(self.reg_dict, startup_time)

        dead_time = self.get_entry(self.frame_dead_entry, 0, 2**32)
        mlx.set_deadtime(self.reg_dict, dead_time)

        pre_time = self.get_entry(self.pretime_entry, 0, 2**32)
        mlx.set_pretime(self.reg_dict, pre_time)

        heat_all = np.uint8(0)
        mix_all = np.uint8(0)
        leden_all = np.uint8(0)

        int_times = np.zeros(8)
        for n in range(0, 8):
            int_times[n] = self.get_entry(self.inttime_entrys[n], 0, 2**32)

            heat = int(self.preheat_vars[n].get()) << n
            heat_all = heat_all | np.uint8(heat)

            mix = int(self.premix_vars[n].get()) << n
            mix_all = mix_all | np.uint8(mix)

            led = int(self.illum_vars[n].get()) << n
            leden_all = leden_all | led

            if self.dmix0_vars[n].get() == "Modulation":
                self.reg_dict["P"+str(n+1)+"_DMIX0"][2] = 0
            elif self.dmix0_vars[n].get() == "Static Hi":
                self.reg_dict["P"+str(n+1)+"_DMIX0"][2] = 3
            elif self.dmix0_vars[n].get() == "Static Low":
                self.reg_dict["P"+str(n+1)+"_DMIX0"][2] = 2

            if self.dmix1_vars[n].get() == "Modulation":
                self.reg_dict["P"+str(n+1)+"_DMIX1"][2] = 0
            elif self.dmix1_vars[n].get() == "Static Hi":
                self.reg_dict["P"+str(n+1)+"_DMIX1"][2] = 3
            elif self.dmix1_vars[n].get() == "Static Low":
                self.reg_dict["P"+str(n+1)+"_DMIX1"][2] = 2

            if self.led_vars[n].get() == "Modulation":
                self.reg_dict["P"+str(n+1)+"_STATIC_LED"][2] = 0
            elif self.led_vars[n].get() == "Static Hi":
                self.reg_dict["P"+str(n+1)+"_STATIC_LED"][2] = 3
            elif self.led_vars[n].get() == "Static Low":
                self.reg_dict["P"+str(n+1)+"_STATIC_LED"][2] = 2

            px = int(float(self.phi_vars[n].get()))

            self.reg_dict["P" +
                          str(n)+"_PHASE_SHIFT"][2] = self.phi_shifts.index(px)

        self.reg_dict["Px_PREHEAT"][2] = heat_all
        self.reg_dict["Px_PREMIX"][2] = mix_all
        self.reg_dict["Px_LEDEN"][2] = leden_all

        mlx.set_int_times(self.reg_dict, int_times)

        return

    def set_mipi(self):
        # Update the MIPI display
        speed = mlx.calc_speed(self.reg_dict)
        lane_ind = self.reg_dict["DATA_LANE_CONFIG"][2]
        mode_ind = self.reg_dict["OUTPUT_MODE"][2]

        self.lane_var.set(self.mipi_lanes[lane_ind])
        self.speed_var.set(speed)
        self.mode_var.set(self.data_modes[mode_ind])
        return

    def get_mipi(self):
        lane = int(self.lane_var.get())
        speed = int(self.speed_var.get())
        mode = self.mode_var.get()

        self.reg_dict["DATA_LANE_CONFIG"][2] = self.mipi_lanes.index(lane)
        self.reg_dict["OUTPUT_MODE"][2] = self.data_modes.index(mode)
        # Now update HMAX for the request speed.
        hmax = mlx.calc_hmax(self.reg_dict, speed=speed)
        #print("get_mipi() hmax: " + str(hmax) + " speed: " + str(speed))
        mlx.set_hmax(self.reg_dict, hmax)

        return

    def get_updates(self):
        pll_setup = mlx.calc_pll_setup(self.reg_dict)
        pix_rst = mlx.calc_pretime(self.reg_dict)
        randnm7 = mlx.calc_randnm7(self.reg_dict)
        randnm0 = mlx.calc_randnm0(self.reg_dict)
        # Update these values from the hmax selected.
        self.reg_dict["PLLSSETUP"][2] = np.uint8(pll_setup)
        mlx.value16_to_reg(self.reg_dict, pix_rst,
                           "Px_PRETIME_HI", "Px_PRETIME_LOW")
        mlx.value24_to_reg(self.reg_dict, randnm0, "RANDNM0_0",
                           "RANDNM0_1", "RANDNM0_2")
        mlx.value24_to_reg(self.reg_dict, randnm7, "RANDNM7_0",
                           "RANDNM7_1", "RANDNM7_2")
        return

    def update_entry(self, entry, value, disable=False):
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, str(value))
        if disable:
            entry.config(state='disabled')
        return

    def get_entry(self, entry, min_val, max_val):
        value = float(entry.get())
        if value < min_val:
            entry.configure(background="red")
            raise ValueError("Value out of range")
        elif value > max_val:
            entry.configure(background="red")
            raise ValueError("Value out of range")

        return value

    def update_can(self):
        self.get_mipi()
        self.get_nraw()
        self.get_frame()
        self.get_updates()

        #
        self.set_mipi()
        self.set_nraw()
        self.set_frame()

    def gui_exit(self):
        self.master.destroy()
        return


class MLX75027ROIViewer(BaseROIViewer, tk.Toplevel):
    def __init__(self, master, reg_dict):
        row_ind = BaseROIViewer.__init__(self, master, reg_dict)
        self.master.wm_title("Chronoptics - MLX27025 ROI Configure")

        self.max_rows = 480.0
        self.max_cols = 640.0

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        tk.Grid.columnconfigure(self.master, 1, weight=1)
        tk.Grid.columnconfigure(self.master, 2, weight=1)
        tk.Grid.columnconfigure(self.master, 3, weight=1)
        tk.Grid.columnconfigure(self.master, 4, weight=1)

        tk.Grid.rowconfigure(self.master, 0, weight=1)

        # Now setup the binning mode
        bin_opts = ["VGA", "QVGA", "QQVGA", "QQQVGA"]
        self.bin_text = tk.Label(self.master, text="Bin")
        self.bin_var = tk.StringVar(self.master)
        self.bin_option = tk.OptionMenu(self.master, self.bin_var, *bin_opts)
        self.bin_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.bin_option.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        row_ind += 1

        self.set_mode()

        ###
        self.nrows_text = tk.Label(self.master, text="N Rows")
        self.ncols_text = tk.Label(self.master, text="N Cols")
        self.nrows_entry = tk.Entry(self.master, bd=3)
        self.ncols_entry = tk.Entry(self.master, bd=3)
        self.nrows_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.nrows_entry.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.ncols_text.grid(row=row_ind, column=2, sticky=tk.E)
        self.ncols_entry.grid(row=row_ind, column=3, sticky=tk.W+tk.E)

        row_ind += 1
        self.set_nxy()

        ###
        self.but_update = tk.Button(
            self.master, text="Update", command=self.update_can)
        self.but_update.grid(row=row_ind, column=1, sticky=tk.N+tk.S+tk.W+tk.E)

        self.but_exit = tk.Button(
            self.master, text="Exit", command=self.gui_exit)
        self.but_exit.grid(row=row_ind, column=3, sticky=tk.W+tk.E)

        self.draw_roi()

        return

    def reg_to_roi(self):
        return mlx.calc_roi(self.reg_dict)

    def get_roi(self):
        col_start = self.get_entry(self.col_start_entry, 0, 640)
        col_end = self.get_entry(self.col_end_entry, 0, 640)
        row_start = self.get_entry(self.row_start_entry, 0, 482)
        row_end = self.get_entry(self.row_end_entry, 0, 482)

        if row_start > row_end:
            raise ValueError("Row readout must start before end")
        if col_start > col_end:
            raise ValueError("Col readout must start before end")

        # Now have to convert the output values into registers
        mlx.set_roi(self.reg_dict, col_start, col_end, row_start, row_end)
        return

    def get_mode(self):
        bin_mode = self.bin_var.get()
        if bin_mode == "VGA":
            self.reg_dict["BINNING_MODE"][2] = 0
        elif bin_mode == "QVGA":
            self.reg_dict["BINNING_MODE"][2] = 1
        elif bin_mode == "QQVGA":
            self.reg_dict["BINNING_MODE"][2] = 2
        elif bin_mode == "QQQVGA":
            self.reg_dict["BINNING_MODE"][2] = 3
        return

    def set_mode(self):
        bin_mode = self.reg_dict["BINNING_MODE"][2]
        if bin_mode == 0:
            self.bin_var.set("VGA")
        elif bin_mode == 1:
            self.bin_var.set("QVGA")
        elif bin_mode == 2:
            self.bin_var.set("QQVGA")
        elif bin_mode == 3:
            self.bin_var.set("QQQVGA")
        return

    def set_nxy(self):
        # We update the number of rows and columns
        col_start, col_end, row_start, row_end = self.reg_to_roi()
        #print("col_start: " + str(col_start) + " col_end: " + str(col_end))
        #print("row_start: " + str(row_start) + " row_end: " + str(row_end))
        bin_mode = self.reg_dict["BINNING_MODE"][2]
        nrows = (row_end - row_start) + 1
        ncols = (col_end - col_start) + 1

        # XXX : Clean up this fuck up.
        if bin_mode == 0:
            if (ncols < 8):
                # We want to force the minimum ROI
                col_end = col_start + 7
                ncols = 8
            if (nrows < 2):
                # Force the minimum ROI
                row_end = row_start + 1
                nrows = 2
            # x4 in cols
            col_inc = ncols % 4
            col_end -= col_inc
            # x2 in rows
            row_inc = nrows % 2
            row_end -= row_inc
        elif bin_mode == 1:
            if (ncols < 16):
                col_end = col_start + 15
                ncols = 16
            if nrows < 2:
                row_end = row_start + 1
                nrows = 2
            col_inc = ncols % 8
            col_end -= col_inc
            ncols -= col_inc
            row_inc = nrows % 2
            row_end -= row_inc
            nrows -= row_inc
            nrows = int(nrows/2)
            ncols = int(ncols/2)
        elif bin_mode == 2:
            if ncols < 32:
                col_end = col_start + 31
                ncols = 32
            if nrows < 4:
                row_end = row_start + 3
                nrows = 4
            col_inc = ncols % 16
            col_end -= col_inc
            ncols -= col_inc
            row_inc = nrows % 4
            row_end -= row_inc
            nrows -= row_inc
            nrows = int(nrows/4)
            ncols = int(ncols/4)
        elif bin_mode == 3:
            if ncols < 64:
                col_end = col_start + 63
                ncols = 64
            if nrows < 8:
                row_end = row_start + 7
                nrows = 8
            col_inc = ncols % 32
            col_end -= col_inc
            ncols -= col_inc
            row_inc = nrows % 8
            row_end -= row_inc
            nrows -= row_inc
            nrows = int(nrows/8)
            ncols = int(ncols/8)

        # Update the start and end values based on our new values
        mlx.set_roi(self.reg_dict, col_start, col_end, row_start, row_end)
        self.update_entry(self.col_start_entry, col_start)
        self.update_entry(self.col_end_entry, col_end)
        self.update_entry(self.row_start_entry, row_start)
        self.update_entry(self.row_end_entry, row_end)

        self.update_entry(self.nrows_entry, nrows, disable=True)
        self.update_entry(self.ncols_entry, ncols, disable=True)
        return


class MLX75027PLLViewer(tk.Toplevel):
    def __init__(self, master, reg_dict):
        self.master = master
        self.master.wm_title("Chronoptics - MLX75027 PLL Configure")
        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap('@Chronoptics.xbm')
        self.master.protocol("WM_DELETE_WINDOW", self.gui_exit)

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        tk.Grid.columnconfigure(self.master, 1, weight=1)
        tk.Grid.columnconfigure(self.master, 2, weight=1)
        tk.Grid.columnconfigure(self.master, 3, weight=1)
        tk.Grid.columnconfigure(self.master, 4, weight=1)

        tk.Grid.rowconfigure(self.master, 0, weight=1)

        self.reg_dict = copy.deepcopy(reg_dict)

        return


class MLX75027_reg_viewer(RegisterViewer):
    def __init__(self, master, reg_dict):
        RegisterViewer.__init__(self, master, reg_dict, "mlx75027")

        self.buts = []
        self.buts.append(["Export CSV", self.export_csv])
        self.buts.append(["Export Registers", self.export_registers])
        self.buts.append(["Import CSV", self.import_csv])
        self.buts.append(["ROI", self.roi_gui])
        self.buts.append(["Time", self.time_gui])
        self.buts.append(["Quit", self.gui_exit])

        tk.Grid.columnconfigure(self.master, 0, weight=1)

        row_ind = 0

        for bu in self.buts:
            curr_but = tk.Button(self.master, text=bu[0], command=bu[1])
            curr_but.grid(row=row_ind, column=6, sticky=tk.W+tk.E+tk.N+tk.S)
            tk.Grid.rowconfigure(self.master, row_ind, weight=1)
            row_ind += 1

        return

    def roi_gui(self):
        val = self.parse_reg()
        if val < 0:
            return

        top = tk.Toplevel(self.master)
        rois = MLX75027ROIViewer(top, self._reg_dict)
        self.master.wait_window(rois.master)
        self._reg_dict = copy.copy(rois.reg_dict)
        self.update_values()
        return

    def time_gui(self):
        val = self.parse_reg()
        if val < 0:
            return

        top = tk.Toplevel(self.master)
        times = MLX75027TimeViewer(top, self._reg_dict)
        self.master.wait_window(times.master)
        self._reg_dict = copy.copy(times.reg_dict)
        self.update_values()
        return


if __name__ == "__main__":
    print("MLX75027 Register Map Viewer")
    infile = os.path.join("..", "mlx75027.csv")

    root = tk.Tk()
    if not os.path.isfile(infile):
        infile = filedialog.askopenfilename(title="Select Registers", filetypes=(
            ('Binary Files', '*.csv'), ('all files', '*.*')))
        if not infile:
            raise RuntimeError("ERROR: Can not find register map file:")

    reg_dict = mlx.csv_import(infile)
    app = MLX75027_reg_viewer(root, reg_dict)
    root.mainloop()
