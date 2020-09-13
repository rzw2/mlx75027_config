"""
Refael Whyte, r.whyte@chronoptics.com 

Copyright 2020 Refael Whyte - Chronoptics

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import platform
import copy

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import mlx75027_config as mlx


def update_entry(entry, value, disable=False):
    entry.config(state='normal')
    entry.delete(0, tk.END)
    entry.insert(0, str(value))
    if disable:
        entry.config(state='disabled')
    return


def get_entry(entry, min_val, max_val):
    try:
        value = float(entry.get())
    except ValueError as er:
        entry.configure(background="red")
        raise er

    if value < min_val:
        entry.configure(background="red")
        raise ValueError("Value out of range")
    elif value > max_val:
        entry.configure(background="red")
        raise ValueError("Value out of range")

    entry.configure(background="white")
    return value


class ResizingCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        # determine the ratio of old width/height to new width/height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        # resize the canvas
        self.config(width=self.width, height=self.height)
        # rescale all the objects tagged with the "all" tag
        self.scale("all", 0, 0, wscale, hscale)


class RegisterViewer(tk.Toplevel):
    def __init__(self, master, reg_dict, camera_type):
        self.master = master
        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap("@Chronoptics.xbm")

        self.master.wm_title("Chronoptics - Register Viewer")

        self._reg_dict = reg_dict
        # We need to generate a blank default configuration
        mclk = 4.0

        self._cam_config = {"version": 1,
                            "type": camera_type,
                            "mclk": mclk,
                            "registers": mlx.dict_to_registers(self._reg_dict),
                            "checksum": 0}
        self.can = tk.Canvas(self.master)
        self.can.grid(row=0, column=0, rowspan=12, sticky=tk.W+tk.E+tk.N+tk.S)

        self.scrollbar = tk.Scrollbar(self.master, command=self.can.yview)
        self.scrollbar.grid(row=0, column=1, rowspan=11,
                            sticky=tk.E+tk.N+tk.S+tk.W)
#        self.can.configure(yscrollcommand=self.scrollbar.set)
        self.can.configure(
            yscrollcommand=self.scrollbar.set, yscrollincrement=1)
        self.can.bind("<Configure>", self.on_configure)

        #self.can.bind_all("<MouseWheel>", self.on_mousewheel)

        # These are the functions that work on linux, need to update so can also work on windows.
        if platform.system() == 'Windows' or platform.system() == 'Darwin':
            self.can.bind_all("<MouseWheel>", self.on_mousewheel)
        else:
            self.can.bind_all("<Button-4>", self.on_mousewheel_up)
            self.can.bind_all("<Button-5>", self.on_mousewheel_down)

        self.frame = tk.Frame(self.can)
        self.can.create_window((0, 0), window=self.frame, anchor='nw')
        self.reg_text = tk.Label(
            self.frame, text="Register", font='Helvetica 12 bold')
        self.bits_text = tk.Label(
            self.frame, text="Bits", font='Helvetica 12 bold')
        #self.prop_text = tk.Label(self.frame,text="Property", font='Helvetica 12 bold')
        self.desc_text = tk.Label(
            self.frame, text="Description", font='Helvetica 12 bold')
        self.val_text = tk.Label(
            self.frame, text="Value", font='Helvetica 12 bold')

        self.reg_text.grid(row=0, column=0)
        self.bits_text.grid(row=0, column=1)
        # self.prop_text.grid(row=0,column=2)
        self.desc_text.grid(row=0, column=3)
        self.val_text.grid(row=0, column=4)
        # How to setup buttons
        # Is there a way to make this more generic ??

        self.val_entry = []
        row_ind = 1
        #reg_cnt = 0

        # This is really fucking slow for large register maps, or some versions of python ...
        # I think we will have to replace this with a table to increase the speed.
        for k in reg_dict:
            reg_txt = tk.Label(self.frame, text=str(k))
            reg_txt.grid(row=row_ind, column=0)

            bit_str = mlx.calc_bits(reg_dict[k][0], reg_dict[k][1])
            bit_txt = tk.Label(self.frame, text=bit_str)
            bit_txt.grid(row=row_ind, column=1, sticky=tk.E)

            desc_txt = tk.Text(self.frame)
            desc_txt.configure(height=2, wrap=tk.WORD)
            desc_txt.insert(tk.INSERT, reg_dict[k][3]+reg_dict[k][5])
            desc_txt.configure(state="disabled")
            desc_txt.grid(row=row_ind, column=3, sticky=tk.E+tk.W)

            val_txt = tk.Entry(self.frame, bd=3)
            val_txt.insert(0, str(reg_dict[k][2]))
            val_txt.grid(row=row_ind, column=4, sticky=tk.E+tk.W)
            self.val_entry.append(val_txt)

            row_ind += 1

    def gui_exit(self):
        self.master.destroy()
        return

    def update_values(self):
        ind = 0
        for k in self._reg_dict:
            self.val_entry[ind].delete(0, tk.END)
            self.val_entry[ind].insert(0, str(int(self._reg_dict[k][2])))
            ind += 1

        return

    def import_csv(self, import_file=""):
        if import_file == "":
            import_file = filedialog.askopenfilename(title="Select Registers", filetypes=(
                ('CSV Files', '*.csv'), ('all files', '*.*')))
            if not import_file:
                return

        self._reg_dict = mlx.csv_import(import_file)
        self.update_values()

        return

    def parse_reg(self):
        ind = 0
        for k in self._reg_dict:
            try:
                new_val = int(float(self.val_entry[ind].get()))
                if(new_val >= (2**self._reg_dict[k][1])):
                    raise ValueError("Size")
                if new_val < 0:
                    raise ValueError("Negative register value")
                self._reg_dict[k][2] = new_val
            except ValueError:
                self.val_entry[ind].configure(background="red")
                messagebox.showwarning(
                    k, k + ": Invalid Value of " + self.val_entry[ind].get())
                return -1
            self.val_entry[ind].configure(background="white")
            ind += 1
        return 0

    def export_csv(self):
        val = self.parse_reg()
        if val < 0:
            return
        out_file = filedialog.asksaveasfilename(title="Output Registers", filetypes=(
            ('CSV files', '*.csv'), ('all files', '*.*')))
        if not out_file:
            return

        mlx.csv_export(out_file, self._reg_dict)
        return

    def export_registers(self):
        """
        """
        val = self.parse_reg()
        if val < 0:
            return
        out_file = filedialog.asksaveasfilename(title="Output Registers", filetypes=(
            ('CSV files', '*.csv'), ('all files', '*.*')))
        if not out_file:
            return

        mlx.csv_export_registers(out_file, self._reg_dict)
        return

    def on_mousewheel_down(self, event):
        self.can.yview_scroll(1, tk.UNITS)
        return

    def on_mousewheel_up(self, event):
        self.can.yview_scroll(-1, tk.UNITS)
        return

    def on_mousewheel(self, event):
        # XXX : On some versions of python event.delta might need to be divided by 120
        self.can.yview_scroll(int(-1*(event.delta)), "units")
        return

    def on_configure(self, event):
        self.can.configure(scrollregion=self.can.bbox('all'))
        return


class BaseROIViewer(tk.Toplevel):
    def __init__(self, master, reg_dict):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.gui_exit)
        os_name = platform.system()
        if os_name == "Windows":
            self.master.iconbitmap('Chronoptics.ico')
        else:
            self.master.iconbitmap('@Chronoptics.xbm')

        tk.Grid.columnconfigure(self.master, 0, weight=1)
        tk.Grid.columnconfigure(self.master, 1, weight=1)
        tk.Grid.columnconfigure(self.master, 2, weight=1)
        tk.Grid.columnconfigure(self.master, 3, weight=1)
        tk.Grid.columnconfigure(self.master, 4, weight=1)

        tk.Grid.rowconfigure(self.master, 0, weight=1)

        self.reg_dict = copy.copy(reg_dict)

        self.roi_can = ResizingCanvas(
            self.master, width=700, height=300, bg="lightgrey", highlightthickness=0)

        self.roi_can.grid(row=0, column=0, columnspan=7,
                          sticky=tk.N+tk.S+tk.W+tk.E)
        # We want to setup start and finish rows and columns
        row_ind = 1
        self.row_start_text = tk.Label(self.master, text="Start Row")
        self.row_start_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.row_start_entry = tk.Entry(self.master, bd=3)
        self.row_start_entry.grid(row=row_ind, column=1, sticky=tk.W+tk.E)

        self.row_end_text = tk.Label(self.master, text="End Row")
        self.row_end_text.grid(row=row_ind, column=2, sticky=tk.E)
        self.row_end_entry = tk.Entry(self.master, bd=3)
        self.row_end_entry.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        # Enable binning and skipping of readouts
        row_ind += 1
        self.col_start_text = tk.Label(self.master, text="Start Col")
        self.col_start_text.grid(row=row_ind, column=0, sticky=tk.E)
        self.col_start_entry = tk.Entry(self.master, bd=3)
        self.col_start_entry.grid(row=row_ind, column=1, sticky=tk.W+tk.E)
        self.col_end_text = tk.Label(self.master, text="End Col")
        self.col_end_text.grid(row=row_ind, column=2, sticky=tk.E)
        self.col_end_entry = tk.Entry(self.master, bd=3)
        self.col_end_entry.grid(row=row_ind, column=3, sticky=tk.W+tk.E)
        row_ind += 1
        self.set_roi()
        return row_ind

    def set_roi(self):
        col_start, col_end, row_start, row_end = self.reg_to_roi()

        update_entry(self.row_start_entry, row_start)
        update_entry(self.row_end_entry, row_end)
        update_entry(self.col_start_entry, col_start)
        update_entry(self.col_end_entry, col_end)
        return

    def update_can(self):
        self.get_roi()
        self.set_roi()
        self.get_mode()
        self.set_mode()
        self.set_nxy()
        self.draw_roi()
        return

    def draw_active(self):
        return

    def draw_roi(self):
        return

    def gui_exit(self):
        self.master.destroy()
        return
