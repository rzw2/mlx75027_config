"""
Refael Whyte, r.whyte@chronoptics.com 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import platform

import numpy as np
from ToFSensorConfiguration import BaseROIViewer
from ToFSensorConfiguration import get_entry, update_entry

from mlx75027_config import epc_calc_binning
from mlx75027_config import epc_calc_roi
from mlx75027_config import epc_set_roi
from mlx75027_config import epc_calc_binning
from mlx75027_config import epc_calc_bin_mode
from mlx75027_config import epc_set_binning
from mlx75027_config import epc_set_bin_mode
from mlx75027_config import epc_calc_img_size
from mlx75027_config import epc_calc_roi_coordinates

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


class EPC660ROIViewer(BaseROIViewer, tk.Toplevel):
    def __init__(self, master, reg_dict):
        # We will probably need a canvas here.
        row_ind = BaseROIViewer.__init__(self, master, reg_dict)

        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap('@Chronoptics.xbm')

        self.master.wm_title("Chronoptics - EPC660 ROI Configure")

        # This is just for visualization purposes
        self.max_rows = 251.0
        self.max_cols = 327.0

        # Now setup the binning and reduced readout modes
        self.bin_rows = tk.IntVar()
        self.bin_rows_check = tk.Checkbutton(self.master,
                                             text="Bin Rows",
                                             variable=self.bin_rows,
                                             command=self.update_can)
        self.bin_rows_check.grid(row=row_ind, column=1, sticky=tk.W+tk.E)

        self.bin_cols = tk.IntVar()
        self.bin_cols_check = tk.Checkbutton(self.master,
                                             text="Bin Cols",
                                             variable=self.bin_cols,
                                             command=self.update_can)
        self.bin_cols_check.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        row_ind += row_ind

        row_rud_opts = [0, 1, 2, 3]
        col_rud_opts = [0, 1]
        self.row_rud_text = tk.Label(self.master, text="Row Reduction:")
        self.col_rud_text = tk.Label(self.master, text="Col Reduction")
        self.row_rud_var = tk.StringVar(self.master)
        self.row_rud_option = tk.OptionMenu(
            self.master, self.row_rud_var, *row_rud_opts)
        self.col_rud_var = tk.StringVar(self.master)
        self.col_rud_option = tk.OptionMenu(
            self.master, self.col_rud_var, *col_rud_opts)

        self.row_rud_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.row_rud_option.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.col_rud_text.grid(row=row_ind, column=2, sticky=tk.E)
        self.col_rud_option.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
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
        return epc_calc_roi(self.reg_dict)

    def get_roi(self):
        col_start = get_entry(self.col_start_entry, 0, 328)
        col_end = get_entry(self.col_end_entry, 0, 328)
        row_start = get_entry(self.row_start_entry, 0, 252)
        row_end = get_entry(self.row_end_entry, 0, 252)
        epc_set_roi(self.reg_dict, col_start, col_end, row_start, row_end)
        return

    def get_mode(self):
        epc_set_bin_mode(self.reg_dict, self.bin_rows.get(),
                         self.bin_cols.get())
        col_rud = int(float(self.col_rud_var.get()))
        row_rud = int(float(self.row_rud_var.get()))
        epc_set_binning(self.reg_dict, row_rud, col_rud)
        return

    def set_mode(self):
        # Row and column binning
        row_bin, col_bin = epc_calc_bin_mode(self.reg_dict)
        self.bin_cols.set(col_bin)
        self.bin_rows.set(row_bin)

        row_rud, col_rud = epc_calc_binning(self.reg_dict)
        self.col_rud_var.set(col_rud)
        self.row_rud_var.set(row_rud)
        return

    def set_nxy(self):
        # We update the nrows ncols etc
        col_start, col_end, row_start, row_end = epc_calc_roi(self.reg_dict)
        nrows, ncols = epc_calc_img_size(self.reg_dict)

        update_entry(self.nrows_entry, nrows, disable=True)
        update_entry(self.ncols_entry, ncols, disable=True)
        return

    def draw_roi(self):
        # Draw the two ROI's on this image sensor.
        top_left, bottom_right, top_left_dash, bottom_right_dash = epc_calc_roi_coordinates(
            self.reg_dict)

        # We want to draw the ROI on the canvas
        wid = self.roi_can.width
        hei = self.roi_can.height

        # The offsets to the image areas
        wo = 5.0
        ho = 5.0
        # The maximum valid pixels

        # The maximum image sensor including dummy
        max_hei = self.max_rows + 2*ho
        max_wid = self.max_cols + 2*wo

        tag1 = "roi1"
        self.roi_can.delete(tag1)
        self.roi_can.create_rectangle(((top_left[1]+wo)/max_wid)*wid,
                                      ((top_left[0]+ho)/max_hei)*hei,
                                      ((bottom_right[1]+wo)/max_wid)*wid,
                                      ((bottom_right[0]+ho)/max_hei)*hei,
                                      width=2,
                                      tag=tag1,
                                      outline='red')

        tag2 = "roi2"
        self.roi_can.delete(tag2)
        self.roi_can.create_rectangle(((top_left_dash[1]+wo)/max_wid)*wid,
                                      ((top_left_dash[0]+ho)/max_hei)*hei,
                                      ((bottom_right_dash[1]+wo)/max_wid)*wid,
                                      ((bottom_right_dash[0]+ho)/max_hei)*hei,
                                      width=2,
                                      tag=tag1,
                                      outline='red')

        tag = "all_pixels"
        self.roi_can.delete(tag)
        self.roi_can.create_rectangle((wo/max_wid)*wid,
                                      (ho/max_hei)*hei,
                                      (self.max_cols + wo)/max_wid * wid,
                                      (self.max_rows + ho)/max_hei * hei,
                                      width=1,
                                      tag=tag)

        self.draw_active()
        return

    def draw_active(self):
        # We want to draw the ROI on the canvas
        wid = self.roi_can.width
        hei = self.roi_can.height

        # The offsets to the image areas
        wo = 5.0
        ho = 5.0
        # The maximum valid pixels
        # The maximum image sensor including dummy
        max_hei = 251.0 + 2*ho
        max_wid = 327.0 + 2*wo

        tag = "active_area"
        self.roi_can.delete(tag)
        self.roi_can.create_rectangle(((4.0+wo)/max_wid)*wid,
                                      ((6.0+ho)/max_hei)*hei,
                                      ((323.0+wo)/max_wid)*wid,
                                      ((245.0+ho)/max_hei)*hei,
                                      width=2,
                                      tag=tag)

        return
