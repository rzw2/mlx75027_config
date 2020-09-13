#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 09:17:30 2018

@author: refael
"""

import os
import sys
from EPC660_PLLConfig import EPC660PLLViewer
from EPC660_ROIConfig import EPC660ROIViewer

#import configuration.ChronoOPT8241Registers as opt8241_reg
from ToFSensorConfiguration import RegisterViewer
from ToFSensorConfiguration import get_entry, update_entry

import copy

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import mlx75027_config as mlx


class EPC660_reg_viewer(RegisterViewer):
    def __init__(self, master, reg_dict, mclk=96.0, demod_clk=0.0):
        RegisterViewer.__init__(self, master, reg_dict, "epc660")

        self.buts = []
        self.buts.append(["Export CSV", self.export_csv])
        self.buts.append(["Export Registers", self.export_registers])
        self.buts.append(["Import CSV", self.import_csv])
        self.buts.append(["ROI", self.roi_gui])
        self.buts.append(["Time", self.pll_gui])
        self.buts.append(["Quit", self.gui_exit])

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        row_ind = 0
        for bu in self.buts:
            curr_but = tk.Button(self.master, text=bu[0], command=bu[1])
            curr_but.grid(row=row_ind, column=6, sticky=tk.W+tk.E+tk.N+tk.S)
            tk.Grid.rowconfigure(self.master, row_ind, weight=1)
            row_ind += 1

        self.mclk = mclk
        self.demod_clk = demod_clk

    def pll_gui(self):
        val = self.parse_reg()
        if val < 0:
            return

        top = tk.Toplevel(self.master)
        plls = EPC660PLLViewer(
            top, self._reg_dict, self.mclk, self.demod_clk)
        self.master.wait_window(plls.master)

        # Now copy over the new reg_dict, mclk and demod_clk
        self._reg_dict = copy.copy(plls.reg_dict)
        self.mclk = plls.mclk
        self.demod_clk = plls.demod_clk
        self.update_values()

        return

    def roi_gui(self):
        val = self.parse_reg()
        if val < 0:
            return

        # Create the ROI gui here
        top = tk.Toplevel(self.master)
        rois = EPC660ROIViewer(top, self._reg_dict)
        self.master.wait_window(rois.master)
        self._reg_dict = copy.copy(rois.reg_dict)
        self.update_values()
        return


if __name__ == "__main__":
    print("EPC660 Register Map Viewer")
    infile = os.path.join("..", "epc660.csv")

    root = tk.Tk()
    if not os.path.isfile(infile):
        infile = filedialog.askopenfilename(title="Select Registers", filetypes=(
            ('CSV Files', '*.csv'), ('all files', '*.*')))
        if not infile:
            raise RuntimeError("ERROR: Can not find register map file:")

    reg_dict = mlx.csv_import(infile)
    app = EPC660_reg_viewer(root, reg_dict)
    root.mainloop()
