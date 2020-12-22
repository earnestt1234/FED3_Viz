# -*- coding: utf-8 -*-
"""
FED3 Viz: A tkinter program for visualizing FED3 Data

@author: https://github.com/earnestt1234
"""
#try to disable warning
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

import datetime as dt
import emoji
import matplotlib.pyplot as plt
import os
import pandas as pd
import pickle
import platform
import subprocess
import sys
import tkinter as tk
import tkinter.filedialog
import webbrowser

from collections import OrderedDict
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import ttk
from tkcalendar import DateEntry

from _version import __version__, __date__
from fed_inspect import fed_inspect
from getdata import getdata
from load.load import FED3_File, fed_concat, FedCannotConcat
from plots import plots

class FED_Plot():
    def __init__(self, figname, plotfunc, arguments, plotdata=None,
                 x=7, y=3.5, dpi=150):
        self.figname = figname
        self.arguments = arguments
        self.plotfunc = plotfunc
        self.plotdata = plotdata
        self.x = x
        self.y = y
        self.dpi = dpi
        self.x_pix = int(self.x * self.dpi) + 300
        self.y_pix = int(self.y * self.dpi) + 100

class New_Window_Figure():
    def __init__(self, toplevel, fig, ax, frame, canvas, toolbar, in_use,):
        self.toplevel = toplevel
        self.fig = fig
        self.ax = ax
        self.frame = frame
        self.canvas = canvas
        self.toolbar = toolbar
        self.in_use = in_use

class FED3_Viz(tk.Tk):
    def __init__(self):
        super(FED3_Viz, self).__init__()
        self.title('FED3 Viz')
        if not platform.system() == 'Darwin':
            self.iconbitmap('img/fedviz_logo.ico')
        self.r_click = '<Button-3>'
        self.LOADED_FEDS = []
        self.PLOTS = OrderedDict()
        self.GROUPS = []
        self.failed_date_feds = []
        self.on_display_func = None
        self.loading = False
        self.plotting = False
        self.mac_color = '#E2E2E2'
        self.colors =  ['blue','red','green','yellow','purple','orange',
                        'black',]
        self.NEW_WINDOW_FIGS = [] #created before the main figure/ax to new window resizing bug!
        for i in range(5):
            fig, ax = plt.subplots(dpi=150)
            self.NEW_WINDOW_FIGS.append(New_Window_Figure(toplevel=None,fig=fig,ax=ax,
                                                         frame=None,canvas=None,
                                                         toolbar=None,in_use=False))
        self.FIGURE, self.AX = plt.subplots(figsize=(5,3.5), dpi=150) #fig/axes used in plot tab
        self.CB = None
        self.POLAR = False
        times = []
        for xm in [' am', ' pm']:
            for num in range(0,12):
                time = str(num) + xm
                if time == '0 am':
                    time = 'midnight'
                if time == '0 pm':
                    time = 'noon'
                times.append(time)

        self.times_to_int = {time : num for num,time in enumerate(times)}
        self.freq_bins = ['5 minutes', '10 minutes', '15 minutes', '30 minutes', '1 hour']
        self.freq_bins += [str(i) + ' hours' for i in range(2,25)]
        self.freq_bins_to_args = {}
        for val in self.freq_bins:
            out =''
            for char in val:
                if char.isdigit():
                    out += char
            if 'minutes' in val:
                out += 'T'
            elif 'hour' in val:
                out += 'H'
            self.freq_bins_to_args[val] = out

    #---SETUP TABS
        self.tabcontrol = ttk.Notebook(self)
        self.home_tab   = tk.Frame(self.tabcontrol)
        self.plot_tab   = tk.Frame(self.tabcontrol)
        self.plot_tab.rowconfigure(0,weight=1)
        self.plot_tab.columnconfigure(2,weight=1)
        self.settings_tab = tk.Frame(self.tabcontrol)
        self.about_tab = tk.Frame(self.tabcontrol)
        self.tabcontrol.add(self.home_tab, text='Home')
        self.tabcontrol.add(self.plot_tab, text='Plots')
        self.tabcontrol.add(self.settings_tab, text='Settings')
        self.tabcontrol.add(self.about_tab, text='About')
        self.tabcontrol.pack(expan = 1, fill='both')
        self.home_tab.rowconfigure(2,weight=1)
        self.home_tab.columnconfigure(2,weight=1)

    #---INIT WIDGETS FOR HOME TAB
        #organization frames
        self.fed_text     = tk.Frame(self.home_tab, width=400, height=30)
        self.fed_buttons  = tk.Frame(self.home_tab)
        self.home_sheets = tk.Frame(self.home_tab)
        self.plot_buttons = tk.Frame(self.home_tab)
        self.plot_selector = tk.Frame(self.home_tab)

        self.fed_text.grid(row=1,column=0,sticky='w',padx=(10,0),
                            columnspan=2)
        self.fed_buttons.grid(row=2,column=0, sticky='nsew', padx=5)
        self.home_sheets.grid(row=2,column=1,sticky='nsew',columnspan=2)
        self.home_sheets.rowconfigure(0,weight=1)
        self.home_sheets.columnconfigure(0,weight=1)
        self.plot_selector.grid(row=2, column=3, sticky='nsew', padx=(20,0),
                                columnspan=2)
        self.plot_selector.rowconfigure(0,weight=1)
        self.plot_selector.columnconfigure(0,weight=1)


        #labels
        italic = 'Segoe 10 italic'
        self.home_buttons_help = tk.Label(self.fed_text, text='Welcome to FED3 Viz!',
                                          anchor='w')
        self.file_view_label    = tk.Label(self.home_sheets, text='File View',
                                          font=italic)
        self.group_view_label    = tk.Label(self.home_sheets, text='Group View',
                                          font=italic)
        #spreadsheets
        treeview_columns = ['','Name','Mode','# Events','Start Time',
                            'End Time','Duration','Groups']
        self.files_spreadsheet = ttk.Treeview(self.home_sheets,
                                              columns=treeview_columns)
        self.files_spreadsheet.column('', width=25, stretch=False)
        self.files_spreadsheet.column('Name', width=200)
        self.files_spreadsheet.column('Mode', width=125)
        self.files_spreadsheet.column('# Events', width=75)
        self.files_spreadsheet.column('Start Time', width=125)
        self.files_spreadsheet.column('End Time', width=125)
        self.files_spreadsheet.column('Duration', width=100)
        self.files_spreadsheet.column('Groups', width=150)
        for i,val in enumerate(treeview_columns):
            self.files_spreadsheet.heading(i, text=val)
        self.files_spreadsheet['show'] = 'headings'
        self.files_spreadsheet.bind('<Button-1>', lambda event, reverse=False:
                                    self.sort_FEDs(event,reverse))
        self.files_spreadsheet.bind('<ButtonRelease-1>', self.update_buttons_home)
        self.files_spreadsheet.bind('<Double-Button-1>', lambda event, reverse=True:
                                    self.sort_FEDs(event,reverse))
        ctrla1 = '<Control-a>'
        ctrla2 = '<Control-A>'
        if platform.system() == 'Darwin':
            ctrla1 = '<Mod1-a>'
            ctrla2 = '<Mod1-A>'
        self.files_spreadsheet.bind(ctrla1,self.select_all_FEDs)
        self.files_spreadsheet.bind(ctrla2,self.select_all_FEDs)
        self.files_scrollbar = ttk.Scrollbar(self.home_sheets, command=self.files_spreadsheet.yview,)
        self.files_spreadsheet.configure(yscrollcommand=self.files_scrollbar.set)
        self.group_view = tk.Listbox(self.home_sheets,selectmode=tk.EXTENDED,
                                     activestyle=tk.NONE, height=5,
                                     exportselection=False)
        self.group_view.bind('<ButtonRelease-1>', self.select_group)
        self.group_scrollbar = ttk.Scrollbar(self.home_sheets, command=self.group_view.yview)
        self.group_view.configure(yscrollcommand=self.group_scrollbar.set)

        #plot selector:
        self.plot_treeview = ttk.Treeview(self.plot_selector,)
        self.plot_treeview.heading('#0', text='Plots',)
        self.plot_treeview.column('#0', width=230)
        self.ps_pellet = self.plot_treeview.insert("", 1, text='Pellets')
        self.plot_treeview.insert(self.ps_pellet, 1, text='Single Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 2, text='Multi Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 3, text='Average Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 4, text='Interpellet Interval')
        self.plot_treeview.insert(self.ps_pellet, 5, text='Group Interpellet Interval')
        self.plot_treeview.insert(self.ps_pellet, 6, text='Meal Size Histogram')
        self.plot_treeview.insert(self.ps_pellet, 7, text='Group Meal Size Histogram')
        self.plot_treeview.insert(self.ps_pellet, 8, text='Retrieval Time Plot')
        self.plot_treeview.insert(self.ps_pellet, 9, text='Multi Retrieval Time Plot')
        self.plot_treeview.insert(self.ps_pellet, 10, text='Average Retrieval Time Plot')
        self.ps_poke = self.plot_treeview.insert("", 2, text='Pokes')
        self.plot_treeview.insert(self.ps_poke, 1, text='Single Poke Plot')
        self.plot_treeview.insert(self.ps_poke, 2, text='Average Poke Plot (Correct)')
        self.plot_treeview.insert(self.ps_poke, 3, text='Average Poke Plot (Error)')
        self.plot_treeview.insert(self.ps_poke, 4, text='Average Poke Plot (Left)')
        self.plot_treeview.insert(self.ps_poke, 5, text='Average Poke Plot (Right)')
        self.plot_treeview.insert(self.ps_poke, 6, text='Poke Bias Plot')
        self.plot_treeview.insert(self.ps_poke, 7, text='Average Poke Bias Plot (Correct %)')
        self.plot_treeview.insert(self.ps_poke, 8, text='Average Poke Bias Plot (Left %)')
        self.plot_treeview.insert(self.ps_poke, 9, text='Poke Time Plot')
        self.ps_pr = self.plot_treeview.insert('', 3, text='Progressive Ratio')
        self.plot_treeview.insert(self.ps_pr, 1, text = 'Breakpoint Plot')
        self.plot_treeview.insert(self.ps_pr, 2, text = 'Group Breakpoint Plot')
        self.ps_circadian = self.plot_treeview.insert("", 4, text='Circadian')
        self.plot_treeview.insert(self.ps_circadian, 1, text='Day/Night Plot')
        self.plot_treeview.insert(self.ps_circadian, 2, text='Day/Night Interpellet Interval Plot')
        self.plot_treeview.insert(self.ps_circadian, 3, text='Chronogram (Line)')
        self.plot_treeview.insert(self.ps_circadian, 4, text='Chronogram (Circle)')
        self.plot_treeview.insert(self.ps_circadian, 5, text='Chronogram (Heatmap)')
        self.ps_other = self.plot_treeview.insert("", 5, text='Diagnostic')
        self.plot_treeview.insert(self.ps_other, 1, text='Battery Life')
        self.plot_treeview.insert(self.ps_other, 2, text='Motor Turns')
        self.plot_treeview.bind('<<TreeviewSelect>>', self.handle_plot_selelection)

        self.plot_tree_scroll = ttk.Scrollbar(self.plot_selector, command=self.plot_treeview.yview)
        self.plot_treeview.configure(yscrollcommand=self.plot_tree_scroll.set)

        #progessbar
        self.progressbar = ttk.Progressbar(self.fed_text, orient='horizontal',
                                           mode='determinate', length=500)
        self.progresstextvar = tk.StringVar()
        self.progresstextvar.set('')
        self.progresstext = tk.Label(self.fed_text, textvariable=self.progresstextvar)

        #buttons
        self.button_load   = tk.Button(self.fed_buttons, text='Load Files',
                                       command=lambda:
                                       self.load_FEDs(overwrite=False,
                                                      skip_duplicates=self.loadduplicates_checkbox_val.get()),
                                       width=8)
        self.button_load_folder = tk.Button(self.fed_buttons, text='Load Folder',
                                       command=lambda:
                                       self.load_FEDs(overwrite=False,
                                                      skip_duplicates=self.loadduplicates_checkbox_val.get(),
                                                      from_folder=True),
                                       width=10)
        self.button_abort_load = tk.Button(self.fed_buttons, text='Abort Load',
                                    command = self.escape,
                                    state=tk.DISABLED)
        self.button_concat = tk.Button(self.fed_buttons, text='Concatenate',
                                       command=self.concat_feds,
                                       state=tk.DISABLED)
        self.button_delete = tk.Button(self.fed_buttons, text='Delete',
                                       command=self.delete_FEDs,
                                       state=tk.DISABLED,
                                       width=8)
        self.button_create_group       = tk.Button(self.fed_buttons, text='Create Group',
                                                   command=self.create_group,
                                                   state=tk.DISABLED,
                                                   width=10)
        self.button_delete_group       = tk.Button(self.fed_buttons, text='Delete Group',
                                                   command=self.delete_group,
                                                   state=tk.DISABLED,
                                                   width=10)
        self.button_edit_group         = tk.Button(self.fed_buttons, text='Edit Group',
                                                   command=self.edit_group,
                                                   state=tk.DISABLED,
                                                   width=10)
        self.button_save_groups        = tk.Button(self.fed_buttons, text='Save Groups',
                                                   command=lambda: self.save_groups(),
                                                   state=tk.DISABLED)
        self.button_load_groups        = tk.Button(self.fed_buttons, text='Load Groups',
                                                   command=lambda: self.load_groups(),
                                                   state=tk.DISABLED)
        self.button_save_session       = tk.Button(self.fed_buttons, text='Save Session',
                                                   command = self.save_session,
                                                   state=tk.NORMAL)
        self.button_load_session       = tk.Button(self.fed_buttons, text='Load Session',
                                                   command=self.load_session,
                                                   state=tk.NORMAL)
        self.button_descriptives       = tk.Button(self.fed_buttons, text='Summary Stats',
                                                   command=self.descriptives_window,
                                                   state=tk.DISABLED)
        self.button_create_plot        = tk.Button(self.plot_selector, text='Create Plot',
                                                   command=self.init_plot,
                                                   state=tk.DISABLED, height=2,
                                                   font='Segoe 10 bold')

    #---HOVER TEXT DICTIONARY
        #dictionary mapping widgets to hover text
        self.hover_text_one_dict = {self.button_load : 'Load FED3 files',
                                    self.button_load_folder: 'Load all FED3 files in a folder (and subfolders)',
                                    self.button_abort_load: 'Cancel loading (or press Esc)',
                                    self.button_delete: 'Delete highlighted FED3 files',
                                    self.button_create_group:
                                        'Add selected devices to a Group',
                                    self.button_delete_group:
                                        'Delete selected Group',
                                    self.button_edit_group:
                                        'Add/Remove FEDs from Groups',
                                    self.button_save_groups:
                                        'Save the current Group labels for the loaded devices',
                                    self.button_load_groups:
                                        'Load Group labels from a saved groups file',
                                    self.button_save_session:
                                        'Save the entire application state (files, groups, plots)',
                                    self.button_load_session:
                                        'Load a session file',
                                    self.button_concat:
                                        'Combine files with non-overlapping dates into a single file',
                                    self.button_descriptives:
                                        'Create a table of descriptive statistics for FED3 files'}
        for button in self.hover_text_one_dict.keys():
            button.bind('<Enter>', self.hover_text_one)
            button.bind('<Leave>', self.clear_hover_text_one)

    #---PLOT TREEVIEW > HELP TEXT
        #associate each plot_treeview entry with helptext
        self.plot_nodes_help = {'Single Pellet Plot':'Plot pellets received for one device',
                                'Multi Pellet Plot':'Plot pellets received for multiple devices (no averaging)',
                                'Average Pellet Plot':'Plot average pellets received for Grouped devices (groups make individual curves)',
                                'Interpellet Interval':'Plot a histogram of intervals between pellet retrievals',
                                'Group Interpellet Interval':'Plot a histogram of intervals between pellet retrievals for Grouped files',
                                'Meal Size Histogram':'Plot histogram of number of pellets in a meal',
                                'Group Meal Size Histogram':'Plot a histogram of the number of pellets in a meal for Grouped files',
                                'Single Poke Plot':'Plot the amount of pokes for one device',
                                'Average Poke Plot (Correct)':'Plot average correct pokes for Grouped devices (Groups make individual curves)',
                                'Average Poke Plot (Error)':'Plot average error pokes for Grouped devices (Groups make individual curves)',
                                'Average Poke Plot (Left)':'Plot average left pokes for Grouped devices (Groups make individual curves)',
                                'Average Poke Plot (Right)':'Plot average right pokes for Grouped devices (Groups make individual curves)',
                                'Poke Bias Plot':'Plot the tendency to pick one poke over another',
                                'Average Poke Bias Plot (Correct %)':'Plot the average Group tendency to poke the active poke (Groups make individual curves)',
                                'Average Poke Bias Plot (Left %)':'Plot the average Group tendency to poke the left poke (Groups make individual curves)',
                                'Poke Time Plot':'Plot the time the nose poke beam was broken for each poke',
                                'Day/Night Plot':'Plot Group averages for day/night on a bar chart',
                                'Day/Night Interpellet Interval Plot':'Plot intervals between pellet retrieval for Grouped animals, grouping by day and night',
                                'Chronogram (Line)':'Plot average 24-hour behavior for groups',
                                'Chronogram (Circle)':'Plot average 24-hour behavior for groups in a circular plot',
                                'Chronogram (Heatmap)':'Make a 24-hour heatmap with individual devices as rows',
                                'Breakpoint Plot':'Plot the breakpoint for individual files (maximum pellets or pokes reached before a period of inactivity)',
                                'Group Breakpoint Plot':'Plot the average breakpoint for Groups (maximum pellets or pokes reached before a period of inactivity)',
                                'Retrieval Time Plot':'Plot the retrieval time for each pellet (along with pellets retrieved) for a single device',
                                'Multi Retrieval Time Plot':'Plot pellet retrieval times for multiple devices (aligned to the same start point)',
                                'Average Retrieval Time Plot':'Plot mean pellet retrieval time for Groups (Groups make individual curves)',
                                'Battery Life':'Plot the battery voltage for a device over time.',
                                'Motor Turns':'Plot the amount of motor turns for each pellet dispensed.'}

    #---PLOT TREEVIEW > PLOT FUNCTION
        #associate each plot_treeview entry with a plotting function
        self.plot_nodes_func = {'Single Pellet Plot':self.pellet_plot_single_TK,
                                'Multi Pellet Plot':self.pellet_plot_multi_TK,
                                'Average Pellet Plot':self.avg_plot_TK,
                                'Interpellet Interval':self.interpellet_plot_TK,
                                'Group Interpellet Interval':self.group_ipi_TK,
                                'Meal Size Histogram':self.meal_histo_TK,
                                'Group Meal Size Histogram':self.group_meal_histo_TK,
                                'Day/Night Plot':self.daynight_plot_TK,
                                'Single Poke Plot':self.poke_plot_single_TK,
                                'Average Poke Plot (Correct)':self.avg_plot_TK,
                                'Average Poke Plot (Error)':self.avg_plot_TK,
                                'Average Poke Plot (Left)':self.avg_plot_TK,
                                'Average Poke Plot (Right)':self.avg_plot_TK,
                                'Poke Bias Plot':self.poke_bias_single_TK,
                                'Poke Time Plot':self.poketime_plot_TK,
                                'Average Poke Bias Plot (Correct %)':self.avg_plot_TK,
                                'Average Poke Bias Plot (Left %)':self.avg_plot_TK,
                                'Chronogram (Line)':self.chronogram_line_TK,
                                'Chronogram (Circle)':self.chronogram_circle_TK,
                                'Chronogram (Heatmap)':self.chronogram_heatmap_TK,
                                'Breakpoint Plot':self.breakpoint_plot,
                                'Group Breakpoint Plot':self.group_breakpoint_plot,
                                'Retrieval Time Plot':self.retrieval_plot_TK,
                                'Multi Retrieval Time Plot':self.retrieval_plot_multi_TK,
                                'Average Retrieval Time Plot':self.avg_plot_TK,
                                'Battery Life': self.battery_life_TK,
                                'Motor Turns': self.motor_turns_TK,
                                'Day/Night Interpellet Interval Plot': self.dn_ipi_TK}

    #---PLACE WIDGETS FOR HOME TAB
        #fed_buttons/group buttons
        self.button_load.grid(row=0,column=0,sticky='sew')
        self.button_load_folder.grid(row=1,column=0,sticky='sew')
        self.button_abort_load.grid(row=2,column=0,sticky='sew')
        self.button_concat.grid(row=3,column=0,sticky='sew')
        self.button_delete.grid(row=4,column=0,sticky='nsew',pady=20)
        self.button_create_group.grid(row=5,column=0,sticky='sew')
        self.button_delete_group.grid(row=6,column=0,sticky='sew')
        self.button_edit_group.grid(row=7,column=0,sticky='sew')
        self.button_save_groups.grid(row=8,column=0,sticky='sew')
        self.button_load_groups.grid(row=9,column=0,sticky='sew')
        self.button_save_session.grid(row=10,column=0,sticky='sew',pady=(20,0))
        self.button_load_session.grid(row=11,column=0,sticky='sew')
        self.button_descriptives.grid(row=12,column=0,sticky='sew',pady=(20,0))

        #labels
        self.home_buttons_help.grid(row=0,column=0,sticky='nsw',
                                    pady=(20),)
        #spreadsheets
        self.files_spreadsheet.grid(row=0,column=0,sticky='nsew')
        self.files_scrollbar.grid(row=0,column=1,sticky='nsew')
        self.file_view_label.grid(row=1,column=0,sticky='w')
        self.group_view.grid(row=2,column=0,sticky='nsew')
        self.group_scrollbar.grid(row=2,column=1,sticky='nsew')
        self.group_view_label.grid(row=3,column=0,sticky='w')
        self.progresstext.grid(row=0,column=1,sticky='w')
        self.home_buttons_help.lift()

        #plot selector
        self.plot_treeview.grid(row=0,column=0,sticky='nsew')
        self.plot_tree_scroll.grid(row=0,column=1,sticky='nsew')
        self.button_create_plot.grid(row=1,column=0,sticky='nsew')

    #---INIT WIDGETS FOR PLOTS TAB
        self.plot_container = tk.Frame(self.plot_tab)
        self.plot_container.grid_columnconfigure(0,weight=1)
        self.plot_container.grid_rowconfigure(0,weight=1)
        self.plot_frame = ttk.Frame(self.plot_container)
        self.plot_frame.grid(row=0,column=0, sticky='nsew')
        self.plot_cover = tk.Frame(self.plot_container, bg='white')
        self.plot_cover.grid(row=0,column=0, sticky='nsew')
        self.plot_cover.grid_remove()
        self.canvas = FigureCanvasTkAgg(self.FIGURE, master=self.plot_frame)
        self.canvas.draw_idle()
        self.canvas.get_tk_widget().pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=1)
        self.nav_toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.nav_toolbar.update()
        self.canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        self.plot_listbox = tk.Listbox(self.plot_tab, selectmode=tk.EXTENDED,
                                       activestyle=tk.NONE,)
        self.plot_listbox.config(width=40)
        self.plot_listbox.bind('<ButtonRelease-1>', self.plot_listbox_event)
        self.plot_listbox.bind('<KeyRelease-Down>', self.plot_listbox_event)
        self.plot_listbox.bind('<KeyRelease-Up>', self.plot_listbox_event)
        self.plot_buttons = tk.Frame(self.plot_tab)
        self.plot_rename = tk.Button(self.plot_buttons,text='Rename',
                                     command=self.rename_plot,
                                     state=tk.DISABLED)
        self.plot_delete = tk.Button(self.plot_buttons,text='Delete',
                                     command=self.delete_plot,
                                     state=tk.DISABLED)
        self.plot_popout = tk.Button(self.plot_buttons,text='New Window',
                                     command=self.new_window_plot,
                                     state=tk.DISABLED)
        self.plot_save   = tk.Button(self.plot_buttons,text='Save Plots',
                                     command=self.save_plots,
                                     state=tk.DISABLED)
        self.plot_inspect = tk.Button(self.plot_buttons, text='Plot Code',
                                      command=self.show_plot_code,
                                      state=tk.DISABLED)
        self.plot_data = tk.Button(self.plot_buttons, text='Save Plot Data',
                                   command=self.save_plot_data,
                                   state=tk.DISABLED)
    #---PLACE WIDGETS FOR PLOTS TAB
        self.plot_buttons.grid(row=0,column=0,sticky='nsew')
        self.plot_listbox.grid(row=0,column=1,sticky='nsew')
        self.plot_container.grid(row=0,column=2,sticky='nsew')
        self.plot_tab.grid_rowconfigure(0,weight=1)
        self.plot_rename.grid(row=0,column=0,sticky='ew')
        self.plot_popout.grid(row=1,column=0,sticky='ew')
        self.plot_save.grid(row=2,column=0,sticky='ew')
        self.plot_inspect.grid(row=3,column=0,sticky='ew')
        self.plot_data.grid(row=4, column=0,sticky='ew')
        self.plot_delete.grid(row=5,column=0,sticky='ew', pady=(20,0))

    #---INIT WIDGETS FOR SETTINGS TAB
        #organization frames
        self.settings_tab.grid_rowconfigure(0,weight=1)
        self.settings_tab.grid_columnconfigure(0,weight=1)
        self.settings_canvas = tk.Canvas(self.settings_tab, highlightthickness=0)
        self.settings_scroll = ttk.Scrollbar(self.settings_tab, orient='horizontal',
                                             command=self.settings_canvas.xview)
        self.settings_scroll2 = ttk.Scrollbar(self.settings_tab, orient='vertical',
                                              command=self.settings_canvas.yview)
        self.all_settings_frame = tk.Frame(self.settings_canvas)
        self.all_settings_frame.bind('<Configure>',self.settings_canvas_config)
        self.settings_canvas.configure(xscrollcommand=self.settings_scroll.set)
        self.settings_canvas.configure(yscrollcommand=self.settings_scroll2.set)
        self.settings_canvas.create_window((0,0),window=self.all_settings_frame,
                                            anchor='nw')
        self.settings_canvas.grid(row=0,column=0,sticky='nsew')
        self.settings_scroll.grid(row=1,column=0,sticky='sew', columnspan=2)
        self.settings_scroll2.grid(row=0,column=1,sticky='nse', rowspan=2)
        self.settings_col1 = tk.Frame(self.all_settings_frame)
        self.settings_col2 = tk.Frame(self.all_settings_frame)
        self.settings_col1.grid(row=0,column=0, sticky='nw', padx=(5,0))
        self.settings_col2.grid(row=0,column=1, sticky='nw')

        self.general_settings_frame = tk.Frame(self.settings_col1)
        self.general_settings_frame.grid(row=0,column=0, sticky='nsew')

        self.pellet_settings_frame = tk.Frame(self.settings_col1)
        self.pellet_settings_frame.grid(row=2,column=0, sticky='nsew')

        self.average_settings_frame = tk.Frame(self.settings_col1)
        self.average_settings_frame.grid(row=1,column=0,sticky='nsew',)

        self.ipi_settings_frame = tk.Frame(self.settings_col1)
        self.ipi_settings_frame.grid(row=3,column=0, sticky='nsew',
                                     pady=(20,0))

        self.meal_settings_frame = tk.Frame(self.settings_col1)
        self.meal_settings_frame.grid(row=4,column=0,sticky='nsew',
                                      pady=(20,40))

        self.retrieval_settings_frame = tk.Frame(self.settings_col2)
        self.retrieval_settings_frame.grid(row=0,column=0,sticky='nsew',
                                           pady=(0,20),padx=(20))

        self.poketime_settings_frame = tk.Frame(self.settings_col2)
        self.poketime_settings_frame.grid(row=1,column=0,sticky='nsew',
                                          padx=(20), pady=(0,20))

        self.pr_settings_frame = tk.Frame(self.settings_col2)
        self.pr_settings_frame.grid(row=2,column=0,sticky='nsew',padx=(20))

        self.poke_settings_frame = tk.Frame(self.settings_col2)
        self.poke_settings_frame.grid(row=3,column=0,sticky='nsew',padx=(20))

        self.daynight_settings_frame = tk.Frame(self.settings_col2)
        self.daynight_settings_frame.grid(row=4,column=0,sticky='nsew',
                                          padx=(20,20), pady=(20,0))

        self.load_settings_frame = tk.Frame(self.settings_col2)
        self.load_settings_frame.grid(row=5,column=0,sticky='nsew',
                                      padx=(20,20), pady=(0,40))

        #labels
        self.section_font = 'Segoe 10 bold'
        if platform.system() == 'Darwin':
            self.section_font = 'Segoe 14 bold'
        self.general_settings_label = tk.Label(self.general_settings_frame,
                                               text='General',
                                               font=self.section_font)
        self.date_filter_days_label  = tk.Label(self.general_settings_frame,
                                                text='Date', fg='gray')
        self.date_filter_hours_label = tk.Label(self.general_settings_frame,
                                                text='Hour', fg='gray')
        self.img_format_label = tk.Label(self.general_settings_frame,
                                         text='Image saving format')
        self.pellet_settings_label   = tk.Label(self.pellet_settings_frame,
                                                text='Individual Pellet Plots',
                                                font=self.section_font)
        self.pelletplottype_label    = tk.Label(self.pellet_settings_frame,
                                                text='Values to plot')
        self.pelletplotcumu_label    = tk.Label(self.pellet_settings_frame,
                                                text='Bin size of pellet frequency',
                                                fg='gray')
        self.pelletplotcolor_label   = tk.Label(self.pellet_settings_frame,
                                                text='Default color (single pellet plots)')

        self.average_settings_label  = tk.Label(self.average_settings_frame,
                                                text='Averaging (Pellet & Poke Plots)',
                                                font=self.section_font)
        self.average_error_label     = tk.Label(self.average_settings_frame,
                                                text='Error value for average plots')
        self.average_bin_label       = tk.Label(self.average_settings_frame,
                                                text='Bin size for averaging')
        self.average_method_label    = tk.Label(self.average_settings_frame,
                                                text='Alignment method for averaging')
        self.average_align_ontime_label = tk.Label(self.average_settings_frame,
                                                   text='Start time & length of average (time/days)')
        self.daynight_settings_label = tk.Label(self.daynight_settings_frame,
                                                text='Circadian Plots',
                                                font=self.section_font)
        self.daynight_values_label = tk.Label(self.daynight_settings_frame,
                                              text='Values to plot')
        self.daynight_error_label  = tk.Label(self.daynight_settings_frame,
                                              text='Error value')
        self.ipi_settings_label = tk.Label(self.ipi_settings_frame,
                                           text='Interpellet Interval Plots',
                                           font=self.section_font)
        self.meal_settings_label = tk.Label(self.meal_settings_frame,
                                            text='Meal Analyses',
                                            font=self.section_font)
        self.mealdelay_label = tk.Label(self.meal_settings_frame,
                                        text='Maximum interpellet interval within meals (minutes)')
        self.meal_pelletmin_label = tk.Label(self.meal_settings_frame,
                                             text='Minimum pellets in a meal')
        self.retrieval_label = tk.Label(self.retrieval_settings_frame,
                                        text='Retrieval Time',
                                        font=self.section_font)
        self.retrieval_threshold_label = tk.Label(self.retrieval_settings_frame,
                                                  text='Cutoff for excluding retrieval times (seconds)')
        self.poketime_label = tk.Label(self.poketime_settings_frame,
                                       text='Poke Time',
                                       font=self.section_font)
        self.poketime_cutoff_label = tk.Label(self.poketime_settings_frame,
                                              text='Cutoff for excluding poke times (seconds)')
        self.pr_settings_label = tk.Label(self.pr_settings_frame,
                                          text='Progressive Ratio',
                                          font=self.section_font)
        self.pr_style_label = tk.Label(self.pr_settings_frame,
                                       text='Value to plot')
        self.pr_length_label = tk.Label(self.pr_settings_frame,
                                        text='Break length (hours/minutes)')
        self.pr_error_label = tk.Label(self.pr_settings_frame,
                                       text='Error value for group breakpoint plots')
        self.poke_settings_label = tk.Label(self.poke_settings_frame,
                                            text='Individual Poke Plots',
                                            font=self.section_font)
        self.poke_style_label = tk.Label(self.poke_settings_frame,
                                         text='Values to plot')
        self.poke_binsize_label  = tk.Label(self.poke_settings_frame,
                                            text='Bin size for poke plots')
        self.poke_biasstyle_label = tk.Label(self.poke_settings_frame,
                                             text='Comparison for single poke bias plots')
        self.load_settings_label = tk.Label(self.load_settings_frame,
                                              text='Save/Load Settings',
                                              font=self.section_font)
        lse_text = 'Save the current settings for future use.'
        self.load_settings_explan = tk.Label(self.load_settings_frame,
                                             text=lse_text)

        #dropdowns/checkboxes
        #   general
        self.date_filter_val = tk.BooleanVar()
        self.date_filter_val.set(False)
        self.date_filter_box = ttk.Checkbutton(self.general_settings_frame,
                                               text='Globally filter dates',
                                               var=self.date_filter_val,
                                               command=self.check_date_filter)
        self.date_filter_s_days = DateEntry(self.general_settings_frame,
                                            width=10)
        self.date_filter_e_days = DateEntry(self.general_settings_frame,
                                            width=10)
        self.date_filter_s_days.configure(state=tk.DISABLED)
        self.date_filter_e_days.configure(state=tk.DISABLED)
        self.date_filter_s_hour = ttk.Combobox(self.general_settings_frame,
                                               values=times, width=10,
                                               state=tk.DISABLED)
        self.date_filter_e_hour = ttk.Combobox(self.general_settings_frame,
                                               values=times, width=10,
                                               state=tk.DISABLED)
        self.date_filter_s_hour.set('noon')
        self.date_filter_e_hour.set('noon')
        self.nightshade_checkbox_val= tk.BooleanVar()
        self.nightshade_checkbox_val.set(True)
        self.nightshade_checkbox = ttk.Checkbutton(self.general_settings_frame,
                                                  text='Shade dark periods (lights on/off)',
                                                  var=self.nightshade_checkbox_val,)
        self.nightshade_lightson = ttk.Combobox(self.general_settings_frame,
                                                values=times, width=10)
        self.nightshade_lightsoff = ttk.Combobox(self.general_settings_frame,
                                                 values=times, width=10)
        self.nightshade_lightson.set('7 am')
        self.nightshade_lightsoff.set('7 pm')
        self.allgroups_val = tk.BooleanVar()
        self.allgroups_val.set(True)
        self.allgroups = ttk.Checkbutton(self.general_settings_frame,
                                        text='For plots using groups, include all loaded groups\nrather than those selected',
                                        var=self.allgroups_val,
                                        command=self.update_buttons_home)
        self.abs_groups_val = tk.BooleanVar()
        self.abs_groups_val.set(True)
        self.abs_groups_box = ttk.Checkbutton(self.general_settings_frame,
                                              text='When loading groups, check for the absolute path (rather than file name)',
                                              var=self.abs_groups_val)
        self.loadduplicates_checkbox_val = tk.BooleanVar()
        self.loadduplicates_checkbox_val.set(True)
        self.loadduplicates_checkbox = ttk.Checkbutton(self.general_settings_frame,
                                                      text='Don\'t load a file if a matching filename is already loaded',
                                                      var=self.loadduplicates_checkbox_val)
        self.overwrite_checkbox_val = tk.BooleanVar()
        self.overwrite_checkbox_val.set(False)
        self.overwrite_checkbox = ttk.Checkbutton(self.general_settings_frame,
                                                 text='Overwrite plots & plot data with same name when saving',
                                                 var=self.overwrite_checkbox_val)
        self.weirdfed_warning_val = tk.BooleanVar()
        self.weirdfed_warning_val.set(True)
        self.weirdfed_warning = ttk.Checkbutton(self.general_settings_frame,
                                               text='Show missing column warning when loading',
                                               var=self.weirdfed_warning_val)
        self.img_format_menu = ttk.Combobox(self.general_settings_frame,
                                            values=['.png', '.jpg', '.svg', '.pdf', '.tif'])
        self.img_format_menu.set('.png')

        #   average
        self.average_error_menu = ttk.Combobox(self.average_settings_frame,
                                               values=['SEM','STD','raw data','None'],
                                               width=10)
        self.average_error_menu.set('SEM')

        self.average_bin_menu = ttk.Combobox(self.average_settings_frame,
                                             values=self.freq_bins,
                                             width=10)
        self.average_bin_menu.set('1 hour')
        self.average_method_menu = ttk.Combobox(self.average_settings_frame,
                                                values=['shared date & time','shared time', 'elapsed time'],)
        self.average_method_menu.set('shared date & time')
        self.average_method_menu.bind('<<ComboboxSelected>>', self.check_average_align)
        self.average_alignstart_menu = ttk.Combobox(self.average_settings_frame,
                                                    values=times,
                                                    width=10,
                                                    state=tk.DISABLED)
        self.average_alignstart_menu.set('7 am')
        self.average_aligndays_menu = ttk.Combobox(self.average_settings_frame,
                                                  values=list(range(1,8)),
                                                  width=10,
                                                  state=tk.DISABLED)
        self.average_aligndays_menu.set(3)
        #   pellet plot
        self.pelletplottype_menu = ttk.Combobox(self.pellet_settings_frame,
                                                values=['Cumulative',
                                                        'Frequency'])
        self.pelletplottype_menu.set('Cumulative')
        self.pelletplottype_menu.bind('<<ComboboxSelected>>',self.check_pellet_type)
        self.pelletplotcumu_menu = ttk.Combobox(self.pellet_settings_frame,
                                                values=self.freq_bins,
                                                state=tk.DISABLED)
        self.pelletplotcumu_menu.set('1 hour')
        self.pelletplotcolor_menu = ttk.Combobox(self.pellet_settings_frame,
                                                 values=self.colors)
        self.pelletplotcolor_menu.set('blue')
        self.pelletplotalign_checkbox_val = tk.BooleanVar()
        self.pelletplotalign_checkbox_val.set(False)
        self.pelletplotalign_checkbox = ttk.Checkbutton(self.pellet_settings_frame,
                                                       text='Align multi pellet plots to the same start time',
                                                       var=self.pelletplotalign_checkbox_val)

        #   day/night
        dn_options = ['pellets','retrieval time','interpellet intervals',
                      'correct pokes','errors','correct pokes (%)','errors (%)']
        self.daynight_values = ttk.Combobox(self.daynight_settings_frame,
                                            values=dn_options)
        self.daynight_values.set('pellets')
        self.daynight_error_menu = ttk.Combobox(self.daynight_settings_frame,
                                                values=['SEM','STD','None'])
        self.daynight_error_menu.set('SEM')
        self.daynight_show_indvl_val = tk.BooleanVar()
        self.daynight_show_indvl_val.set(False)
        self.daynight_show_indvl = ttk.Checkbutton(self.daynight_settings_frame,
                                                  text='Show individual FED data points',
                                                  var=self.daynight_show_indvl_val)
        #   ipi
        self.ipi_kde_val = tk.BooleanVar()
        self.ipi_kde_val.set(True)
        self.ipi_kde_checkbox = ttk.Checkbutton(self.ipi_settings_frame,
                                                text='Use kernel density estimation',
                                                var=self.ipi_kde_val)
        self.ipi_log_val = tk.BooleanVar()
        self.ipi_log_val.set(True)
        self.ipi_log_checkbox = ttk.Checkbutton(self.ipi_settings_frame,
                                                text='Plot on a logarithmic axis',
                                                var=self.ipi_log_val)
        #   meals
        self.norm_meal_val = tk.BooleanVar()
        self.norm_meal_val.set(True)
        self.norm_meal_box = ttk.Checkbutton(self.meal_settings_frame,
                                             var=self.norm_meal_val,
                                             text='Normalize meal histogram counts')
        self.mealdelay_box = ttk.Combobox(self.meal_settings_frame,
                                          values=[1,2,3,4,5,10,15,30,60],
                                          width=10)
        self.mealdelay_box.set(1)
        self.meal_pelletmin_box = ttk.Combobox(self.meal_settings_frame,
                                        values=list(range(1,11)),
                                        width=10)
        self.meal_pelletmin_box.set(1)

        #   retrieval
        self.retrieval_threshold_menu = ttk.Combobox(self.retrieval_settings_frame,
                                                     values=['None',5,10,15,30,
                                                             60,120,300,600],
                                                     width=10)
        self.retrieval_threshold_menu.set('None')

        #   poke time
        self.poketime_cutoff_menu = ttk.Combobox(self.poketime_settings_frame,
                                                 values=['None',1,2,3,4,5,10,20,30],
                                                 width=10)
        self.poketime_cutoff_menu.set('None')

        #   progressive ratio
        self.pr_style_menu = ttk.Combobox(self.pr_settings_frame,
                                          values=['pellets','pokes'],
                                          width=10)
        self.pr_style_menu.set('pellets')
        self.pr_hours_menu = ttk.Combobox(self.pr_settings_frame,
                                          values=list(range(4)),
                                          width=5)
        self.pr_hours_menu.set(1)
        self.pr_mins_menu = ttk.Combobox(self.pr_settings_frame,
                                         values=[0,15,30,45],
                                         width=5)
        self.pr_mins_menu.set(0)
        self.pr_error_menu = ttk.Combobox(self.pr_settings_frame,
                                          values=['SEM','STD','None'],
                                          width=10)
        self.pr_error_menu.set('SEM')

        self.pr_show_indvl_val = tk.BooleanVar()
        self.pr_show_indvl_val.set(False)
        self.pr_show_indvl_box = ttk.Checkbutton(self.pr_settings_frame,
                                                 text='Show individual values',
                                                 var=self.pr_show_indvl_val)

        #   poke
        self.poke_style_menu = ttk.Combobox(self.poke_settings_frame,
                                            values=['Cumulative','Frequency',])
        self.poke_style_menu.set('Cumulative')
        self.poke_bins_menu = ttk.Combobox(self.poke_settings_frame,
                                           values=self.freq_bins,
                                           width=10)
        self.poke_bins_menu.set('1 hour')
        self.poke_correct_val = tk.BooleanVar()
        self.poke_correct_val.set(True)
        self.poke_correct_box = ttk.Checkbutton(self.poke_settings_frame,
                                                text='Show correct pokes',
                                                var=self.poke_correct_val,
                                                command=self.update_buttons_home)
        self.poke_error_val = tk.BooleanVar()
        self.poke_error_val.set(True)
        self.poke_error_box = ttk.Checkbutton(self.poke_settings_frame,
                                              text='Show incorrect pokes',
                                              var=self.poke_error_val,
                                              command=self.update_buttons_home)
        self.poke_left_val = tk.BooleanVar()
        self.poke_left_val.set(False)
        self.poke_left_box = ttk.Checkbutton(self.poke_settings_frame,
                                             text='Show left pokes',
                                             var=self.poke_left_val,
                                             command=self.update_buttons_home)
        self.poke_right_val = tk.BooleanVar()
        self.poke_right_val.set(False)
        self.poke_right_box = ttk.Checkbutton(self.poke_settings_frame,
                                             text='Show right pokes',
                                             var=self.poke_right_val,
                                             command=self.update_buttons_home)
        self.poke_dynamiccolor_val = tk.BooleanVar()
        self.poke_dynamiccolor_val.set(True)
        self.poke_dynamiccolor_box = ttk.Checkbutton(self.poke_settings_frame,
                                                     text='Use dynamic color for single bias plots',
                                                     var=self.poke_dynamiccolor_val)
        self.poke_biasstyle_menu = ttk.Combobox(self.poke_settings_frame,
                                                values=['correct (%)','left (%)'],)
        self.poke_biasstyle_menu.set('correct (%)')
        #   load/save
        self.settings_lastused_val = tk.BooleanVar()
        self.settings_lastused_val.set(False)
        self.settings_lastused = ttk.Checkbutton(self.load_settings_frame,
                                                text='Load last used settings when opening',
                                                var=self.settings_lastused_val)

        #buttons
        self.settings_load_button = tk.Button(self.load_settings_frame,
                                              text='Load',
                                              command=self.load_settings)
        self.settings_save_button = tk.Button(self.load_settings_frame,
                                              text='Save',
                                              command=self.save_settings)

    #---PLACE WIDGETS FOR SETTINGS TAB
        self.general_settings_label.grid(row=0,column=0,sticky='w')
        self.date_filter_box.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.date_filter_days_label.grid(row=2,column=0,sticky='w',padx=(40,0))
        self.date_filter_s_days.grid(row=2,column=1,sticky='ew')
        self.date_filter_e_days.grid(row=2,column=2,sticky='ew')
        self.date_filter_hours_label.grid(row=3,column=0,sticky='w',padx=(40,0))
        self.date_filter_s_hour.grid(row=3,column=1,sticky='ew',)
        self.date_filter_e_hour.grid(row=3,column=2,sticky='ew',)
        self.nightshade_checkbox.grid(row=4,column=0,padx=(20,160),sticky='w')
        self.nightshade_lightson.grid(row=4,column=1,sticky='w')
        self.nightshade_lightsoff.grid(row=4,column=2,sticky='w')
        self.allgroups.grid(row=5,column=0,padx=(20,0),sticky='w')
        self.abs_groups_box.grid(row=6,column=0,padx=(20,0),sticky='w')
        self.loadduplicates_checkbox.grid(row=7,column=0,padx=(20,0),sticky='w')
        self.overwrite_checkbox.grid(row=8,column=0,padx=(20,0),sticky='w')
        self.weirdfed_warning.grid(row=9,column=0,padx=(20,0),sticky='w')
        self.img_format_label.grid(row=10,column=0,padx=(20,0),sticky='w')
        self.img_format_menu.grid(row=10,column=1,sticky='ew',columnspan=2)

        self.average_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))
        self.average_error_label.grid(row=1,column=0,padx=(20,215),sticky='w')
        self.average_error_menu.grid(row=1,column=1,sticky='nw')
        self.average_bin_label.grid(row=2,column=0,sticky='w', padx=(20,0))
        self.average_bin_menu.grid(row=2,column=1,sticky='ew', columnspan=2)
        self.average_method_label.grid(row=3, column=0, sticky='w', padx=(20,0))
        self.average_method_menu.grid(row=3,column=1,sticky='ew', columnspan=2)
        self.average_align_ontime_label.grid(row=4,column=0,sticky='w',padx=(30,0))
        self.average_alignstart_menu.grid(row=4,column=1,sticky='w')
        self.average_aligndays_menu.grid(row=4,column=2,sticky='w')

        self.pellet_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))
        self.pelletplottype_label.grid(row=1,column=0,padx=(20,100),sticky='w')
        self.pelletplottype_menu.grid(row=1,column=1,sticky='nw')
        self.pelletplotcumu_label.grid(row=2,column=0,padx=(20,100),sticky='w')
        self.pelletplotcumu_menu.grid(row=2,column=1,sticky='w')
        self.pelletplotcolor_label.grid(row=3,column=0,padx=(20,100),sticky='w')
        self.pelletplotcolor_menu.grid(row=3,column=1,sticky='nw')
        self.pelletplotalign_checkbox.grid(row=4,column=0,padx=(20,100),
                                           sticky='nw')

        self.daynight_settings_label.grid(row=0,column=0,sticky='w')
        self.daynight_values_label.grid(row=1,column=0,sticky='w',padx=(20,175))
        self.daynight_values.grid(row=1,column=1,sticky='w')
        self.daynight_error_label.grid(row=2,column=0,sticky='w',padx=(20,175))
        self.daynight_error_menu.grid(row=2,column=1,sticky='w')
        self.daynight_show_indvl.grid(row=3,column=0,sticky='w',padx=(20,0))

        self.ipi_settings_label.grid(row=0,column=0,sticky='w')
        self.ipi_kde_checkbox.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.ipi_log_checkbox.grid(row=2,column=0,sticky='w',padx=(20,0))

        self.meal_settings_label.grid(row=0,column=0,sticky='w')
        self.norm_meal_box.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.mealdelay_label.grid(row=2,column=0,padx=(20,175),sticky='w')
        self.mealdelay_box.grid(row=2,column=1,sticky='ew')
        self.meal_pelletmin_label.grid(row=3,column=0,sticky='w',padx=(20,0))
        self.meal_pelletmin_box.grid(row=3,column=1,sticky='ew')

        self.retrieval_label.grid(row=0,column=0,sticky='w')
        self.retrieval_threshold_label.grid(row=1,column=0,sticky='w',padx=(20,100))
        self.retrieval_threshold_menu.grid(row=1,column=1,sticky='w',)

        self.poketime_label.grid(row=0,column=0,sticky='w')
        self.poketime_cutoff_label.grid(row=1,column=0,sticky='w',padx=(20,100))
        self.poketime_cutoff_menu.grid(row=1,column=1,sticky='w',)

        self.pr_settings_label.grid(row=0,column=0,sticky='w')
        self.pr_style_label.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.pr_style_menu.grid(row=1,column=1,sticky='ew',columnspan=2)
        self.pr_length_label.grid(row=2,column=0,sticky='w',padx=(20,0))
        self.pr_hours_menu.grid(row=2,column=1,sticky='ew')
        self.pr_mins_menu.grid(row=2,column=2,sticky='ew')
        self.pr_error_label.grid(row=3,column=0,sticky='w',padx=(20,55))
        self.pr_error_menu.grid(row=3,column=1,sticky='ew',columnspan=2)
        self.pr_show_indvl_box.grid(row=4,column=0,sticky='w',padx=(20,0), pady=(0,20))

        self.poke_settings_label.grid(row=0,column=0,sticky='w')
        self.poke_style_label.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.poke_style_menu.grid(row=1,column=1,sticky='ew',)
        self.poke_binsize_label.grid(row=2,column=0,sticky='w', padx=(20,95))
        self.poke_bins_menu.grid(row=2,column=1,sticky='ew')
        self.poke_correct_box.grid(row=3,column=0,sticky='w',padx=(20))
        self.poke_error_box.grid(row=4,column=0,sticky='w',padx=20)
        self.poke_left_box.grid(row=5,column=0,sticky='w',padx=20)
        self.poke_right_box.grid(row=6,column=0,sticky='w',padx=20)
        self.poke_biasstyle_label.grid(row=7,column=0,sticky='w',padx=20,pady=(10,0))
        self.poke_biasstyle_menu.grid(row=7,column=1,sticky='w', pady=(10,0))
        self.poke_dynamiccolor_box.grid(row=8,column=0,sticky='w',padx=20)

        self.load_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))
        self.load_settings_explan.grid(row=1,column=0,padx=(20,30),sticky='w')
        self.settings_load_button.grid(row=1,column=2,sticky='w',ipadx=20,padx=(0,10))
        self.settings_save_button.grid(row=1,column=3,sticky='nw',ipadx=20)
        self.settings_lastused.grid(row=2,column=0,sticky='w',padx=(20,0))

    #---INIT WIDGETS FOR ABOUT TAB
        self.graphic_frame = tk.Frame(self.about_tab)
        self.information_frame = tk.Frame(self.about_tab)
        title_text = 'FED3 Viz'
        title_font = ('Fixedsys', '48','bold')
        subtitle_text = 'a GUI for plotting FED3 data'
        subtitle_font = ('Times','14','normal')
        self.fed_title = tk.Label(self.graphic_frame, text=title_text,
                                  font=title_font)
        self.fed_subtitle = tk.Label(self.graphic_frame,text=subtitle_text,
                                     font=subtitle_font)
        self.sep1 = ttk.Separator(self.graphic_frame, orient='horizontal')
        #information
        bold = ('Segoe 9 bold')
        if platform.system() == 'Darwin':
            bold=None
        self.precolon_text = tk.Frame(self.information_frame)
        self.postcolon_text = tk.Frame(self.information_frame)
        self.version1 = tk.Label(self.precolon_text, text='Version:', font=bold)
        self.version2 = tk.Label(self.postcolon_text, text=__version__)
        self.vdate1 = tk.Label(self.precolon_text,text='Version Date:', font=bold)
        self.vdate2 = tk.Label(self.postcolon_text,text=__date__,)
        self.kravitzlab1 = tk.Label(self.precolon_text, text='Kravitz Lab:',
                                    font=bold)
        kravitz_url='https://kravitzlab.com/'
        self.kravitzlab2 = tk.Label(self.postcolon_text,
                                    text=kravitz_url, fg='blue',
                                    cursor='hand2')
        self.kravitzlab2.bind('<ButtonRelease-1>',
                              lambda event: self.open_url(kravitz_url))
        self.fedhack1 = tk.Label(self.precolon_text,text='FED3 Hackaday:',
                                 font=bold)
        hackurl = 'https://hackaday.io/project/106885-feeding-experimentation-device-3-fed3'
        self.fedhack2 = tk.Label(self.postcolon_text,text=hackurl,
                                 fg='blue',cursor='hand2',)
        self.fedhack2.bind('<ButtonRelease-1>',
                            lambda event: self.open_url(hackurl))
        self.github1 = tk.Label(self.precolon_text,text='GitHub:',
                                font=bold)
        giturl = 'https://github.com/earnestt1234/'
        self.github2 = tk.Label(self.postcolon_text,text=giturl,fg='blue',
                                cursor='hand2')
        self.github2.bind('<ButtonRelease-1>',
                          lambda event: self.open_url(giturl))
        self.googlegr1 = tk.Label(self.precolon_text, text='Google Group:',
                                  font=bold)
        googlegr_url = 'https://groups.google.com/forum/#!forum/fedforum'
        self.googlegr2 = tk.Label(self.postcolon_text,text=googlegr_url,
                                  fg='blue',cursor='hand2')
        self.googlegr2.bind('<ButtonRelease-1>',
                            lambda event: self.open_url(googlegr_url))
        self.help_link1 = tk.Label(self.precolon_text,text='HELP (MANUAL): ',
                                   font=bold)
        manual_url='https://github.com/earnestt1234/FED3_Viz/blob/master/Manual.md'
        self.help_link2 = tk.Label(self.postcolon_text,text=manual_url,
                                   fg='blue',cursor='hand2')
        self.help_link2.bind('<ButtonRelease-1>',
                             lambda event: self.open_url(manual_url))
        spaces = 100
        if platform.system() == 'Darwin':
            spaces = 60
        caveat_text = ('FED3 Viz is still being developed and has not ' +
                      'been thoroughly tested.  Please help improve the ' +
                      'program by sharing compliments, criticisms, bugs, ' +
                      'and other requests on the FED Google Group.\n' +
                      ' '*spaces + '-Tom & Lex')
        self.caveat = tk.Label(self.information_frame,text=caveat_text,
                               wraplength=400, justify=tk.LEFT)

    #---PLACE WIDGETS FOR ABOUT TAB
        #title_frame
        self.about_tab.grid_columnconfigure(0,weight=1)
        self.graphic_frame.grid(row=0,column=0, sticky='ew')
        self.information_frame.grid(row=1,column=0,)
        self.precolon_text.grid(row=0,column=0)
        self.postcolon_text.grid(row=0,column=1, padx=(20))
        self.fed_title.grid(row=0,column=0,sticky='nsew')
        self.fed_subtitle.grid(row=1,column=0,sticky='nsew')
        self.sep1.grid(row=2,column=0,sticky='ew', padx=20, pady=20)
        self.graphic_frame.grid_columnconfigure(0,weight=1)
        self.help_link1.grid(row=0,column=0,sticky='w',pady=(0,30))
        self.help_link2.grid(row=0,column=1,sticky='w',pady=(0,30))
        self.version1.grid(row=1,column=0,sticky='w')
        self.version2.grid(row=1,column=1,sticky='w')
        self.vdate1.grid(row=2,column=0,sticky='w')
        self.vdate2.grid(row=2,column=1,sticky='w')
        self.kravitzlab1.grid(row=3,column=0,sticky='w')
        self.kravitzlab2.grid(row=3,column=1,sticky='w')
        self.fedhack1.grid(row=4,column=0,sticky='w')
        self.fedhack2.grid(row=4,column=1,sticky='w')
        self.github1.grid(row=5,column=0,sticky='w')
        self.github2.grid(row=5,column=1,sticky='w')
        self.googlegr1.grid(row=6,column=0,sticky='w')
        self.googlegr2.grid(row=6,column=1,sticky='w')
        # self.caveat.grid(row=1, column=0, pady=40, columnspan=2)

    #---LOAD SETTINGS ON START
    #try to load default settings when the application starts:
        default=True
        last_used = 'settings/LAST_USED.csv'
        if os.path.isfile(last_used):
            try:
                settings_df = pd.read_csv(last_used,index_col=0)
                if settings_df.loc['load_last_used','Values'] == 'True':
                    del settings_df
                    self.load_settings(dialog=False,settings_file=[last_used])
                    default=False
            except:
                print("Found 'LAST_USED.CSV' settings file, but couldn't load!")

        if default:
            default_file = 'settings/DEFAULT.csv'
            if os.path.isfile(default_file):
                try:
                    self.load_settings(dialog=False,settings_file=[default_file])
                    now = dt.datetime.today().date()
                    if str(self.date_filter_s_days.cget('state')) == 'disabled':
                        self.date_filter_s_days.configure(state=tk.NORMAL)
                        self.date_filter_s_days.set_date(now)
                        self.date_filter_s_days.configure(state=tk.DISABLED)
                    else:
                        self.date_filter_s_days.set_date(now)
                    if str(self.date_filter_e_days.cget('state')) == 'disabled':
                        self.date_filter_e_days.configure(state=tk.NORMAL)
                        self.date_filter_e_days.set_date(now)
                        self.date_filter_e_days.configure(state=tk.DISABLED)
                    else:
                        self.date_filter_e_days.set_date(now)
                except:
                    print("Found 'DEFAULT.CSV' settings file, but couldn't load!")

    #---OS CONFIG
        self.w_offset = 400
        self.h_offset = 60
        def config_color_mac(widget):
            if type(widget) in [tk.Button, tk.Frame, tk.Label,]:
                widget.configure(bg=self.mac_color)
            if type(widget) == tk.Button:
                widget.configure(highlightbackground=self.mac_color)
            if widget.grid_slaves():
                for i in widget.grid_slaves():
                    config_color_mac(i)

        if platform.system() == 'Darwin':
            self.plot_treeview.column('#0', width=250)
            self.plot_listbox.config(width=30)
            self.w_offset = 350
            self.h_offset = 100
            self.r_click = '<Button-2>'
            for widget in [self.home_tab, self.plot_tab,
                            self.settings_tab, self.about_tab]:
                config_color_mac(widget)

    #---RIGHT CLICK MENUS
        #file_view_single
        self.files_spreadsheet.bind(self.r_click, self.r_raise_menu)
        self.r_menu_file_empty = tkinter.Menu(self, tearoff=0,)
        self.r_menu_file_empty.add_command(label='Load files',
                                            command=lambda:self.load_FEDs(skip_duplicates=self.loadduplicates_checkbox_val.get()))
        self.r_menu_file_empty.add_command(label='Load folder',
                                            command=lambda:self.load_FEDs(skip_duplicates=self.loadduplicates_checkbox_val.get(),
                                                                          from_folder=True))

        self.r_menu_file_single = tkinter.Menu(self, tearoff=0,)
        self.r_menu_file_single.add_command(label='Open file location',command= self.r_open_location,)
        self.r_menu_file_single.add_command(label='Open file externally', command=self.r_open_externally)
        self.r_menu_file_single.add_separator()
        self.r_menu_file_single.add_command(label='Create Group', command=self.create_group)
        self.r_menu_file_single.add_command(label='Edit Group', command=self.edit_group)
        self.r_menu_file_single.add_separator()
        self.r_menu_file_single.add_command(label='Delete', command=self.delete_FEDs)

        self.r_menu_file_multi = tkinter.Menu(self, tearoff=0,)
        self.r_menu_file_multi.add_command(label='Create Group', command=self.create_group)
        self.r_menu_file_multi.add_command(label='Edit Group', command=self.edit_group)
        self.r_menu_file_multi.add_separator()
        self.r_menu_file_multi.add_command(label='Concatenate', command=self.concat_feds)
        self.r_menu_file_multi.add_separator()
        self.r_menu_file_multi.add_command(label='Delete', command=self.delete_FEDs)

        self.plot_listbox.bind(self.r_click, self.r_raise_menu)
        self.r_menu_plot_single = tkinter.Menu(self, tearoff=0,)
        self.r_menu_plot_single.add_command(label='Load settings used in this graph',command= self.r_load_plot_settings,)
        self.r_menu_plot_single.add_command(label='Select files used in this graph',command= self.r_select_from_plot,)
        self.r_menu_plot_single.add_separator()
        self.r_menu_plot_single.add_command(label='Rename',command= self.rename_plot,)
        self.r_menu_plot_single.add_command(label='New window',command= self.new_window_plot,)
        self.r_menu_plot_single.add_command(label='Plot code',command= self.show_plot_code,)
        self.r_menu_plot_single.add_command(label='Save figure',command= self.save_plots,)
        self.r_menu_plot_single.add_command(label='Save data',command= self.save_plot_data,)
        self.r_menu_plot_single.add_separator()
        self.r_menu_plot_single.add_command(label='Delete',command= self.delete_plot,)

        self.r_menu_plot_multi = tkinter.Menu(self, tearoff=0,)
        self.r_menu_plot_multi.add_command(label='Plot Code',command= self.show_plot_code,)
        self.r_menu_plot_multi.add_command(label='Save Figure',command= self.save_plots,)
        self.r_menu_plot_multi.add_command(label='Save Data',command= self.save_plot_data,)
        self.r_menu_plot_multi.add_separator()
        self.r_menu_plot_multi.add_command(label='Delete',command= self.delete_plot,)

    #---HOME TAB BUTTON FUNCTIONS
    def load_FEDs(self, overwrite=True, skip_duplicates=True, from_folder=False, file_paths=None):
        if file_paths:
            files = file_paths
        else:
            if from_folder:
                folder = tk.filedialog.askdirectory(title='Select folder to search for FEDs')
                files = self.walk_filenames(folder)
            else:
                file_types = [('All', '*.*'),
                              ('Comma-Separated Values', '*.csv'),
                              ('Excel', '*.xls, *.xslx'),]
                files = tk.filedialog.askopenfilenames(title='Select FED3 Data',
                                                       filetypes=file_types)
        loaded_filenames = [fed.basename for fed in self.LOADED_FEDS]
        pass_FEDs = []
        failed_FEDs = []
        weird_FEDs = []
        self.loading = True
        self.button_abort_load.configure(state=tk.NORMAL)
        if files:
            self.home_buttons_help.configure(text='')
            self.progressbar.grid(row=0,column=0,sticky='ew',padx=(0,20),pady=(12))
            self.progressbar.lift()
            self.progresstext.grid(row=0,column=1,sticky='nsw')
            if overwrite:
                self.LOADED_FEDS = []
            for i,file in enumerate(files):
                file_name = os.path.basename(file)
                if self.loading:
                    if skip_duplicates:
                        if file_name not in loaded_filenames:
                            try:
                                pass_FEDs.append(FED3_File(file))
                            except:
                                failed_FEDs.append(file_name)
                    else:
                        try:
                            pass_FEDs.append(FED3_File(file))
                        except:
                            failed_FEDs.append(file_name)
                    self.progresstextvar.set(os.path.basename(file)[:50] + '...')
                    self.progressbar.step(1/len(files)*100)
                    self.update()
        self.button_abort_load.configure(state=tk.DISABLED)
        self.progressbar.grid_remove()
        self.progresstext.grid_remove()
        for file in pass_FEDs:
            if file.missing_columns:
                weird_FEDs.append(os.path.basename(file.directory))
        if not self.weirdfed_warning_val.get():
            weird_FEDs=None
        if failed_FEDs or weird_FEDs:
            self.raise_load_errors(failed_FEDs, weird_FEDs,)
        self.LOADED_FEDS += pass_FEDs
        self.update_file_view()
        self.update_group_view()
        self.update_buttons_home()
        self.loading=False

    def concat_feds(self):
        selected = self.files_spreadsheet.selection()
        to_concat = [self.LOADED_FEDS[int(i)] for i in selected]
        if to_concat:
            try:
                new = fed_concat(to_concat)
                savepath = tk.filedialog.asksaveasfilename(title='Select where to save new file',
                                                           defaultextension='.csv',
                                                           filetypes = [('Comma-Separated Values', '*.csv')])
                if savepath:
                    new.to_csv(savepath)
                    new_FED = FED3_File(savepath)
                    self.LOADED_FEDS.append(new_FED)
                    for fed in to_concat:
                        self.LOADED_FEDS.remove(fed)
                    self.update_file_view()
                    self.update_group_view()
                    self.update_buttons_home()
            except FedCannotConcat:
                self.raise_fed_concat_error()
                return

    def delete_FEDs(self):
        to_delete = [int(i) for i in self.files_spreadsheet.selection()]
        for index in sorted(to_delete, reverse=True):
            del(self.LOADED_FEDS[index])
        self.update_file_view()
        self.update_group_view()
        self.update_buttons_home(None)

    def create_group(self):
        self.create_window = tk.Toplevel(self)
        self.create_window.title('Enter a group name')
        self.create_name = tk.StringVar()
        self.create_name.set('')
        self.create_name.trace_add('write',self.create_check)
        self.warning_var = tk.StringVar()
        self.warning_var.set('')
        warning_label = tk.Label(self.create_window,
                                      textvariable=self.warning_var)
        entry = tk.Entry(self.create_window,
                         textvariable=self.create_name,
                         width=50)
        self.ok_button_create = tk.Button(self.create_window,text='OK',
                              command=lambda: self.create_okay(),
                              state=tk.DISABLED)
        cancel_button = tk.Button(self.create_window,
                                       text='Cancel',
                                       command=self.create_window.destroy)
        warning_label.grid(row=0,column=0, sticky='w',
                                columnspan=2,padx=(20,0),pady=(20,0))
        entry.grid(row=1,column=0,sticky='ew',padx=(20,20),pady=(20,0),
                   columnspan=2)
        self.ok_button_create.grid(row=2,column=0,sticky='ew',padx=(20,20),pady=(20,20))
        cancel_button.grid(row=2,column=1,sticky='ew',padx=(20,20),pady=(20,20))
        self.update_buttons_home()

    def delete_group(self):
        clicked = self.group_view.curselection()
        if clicked:
            for i in clicked:
                group = self.GROUPS[int(i)]
                for fed in self.LOADED_FEDS:
                    if group in fed.group:
                        fed.group.remove(group)
            self.update_file_view()
            self.update_group_view()
            self.update_buttons_home()

    def edit_group(self):
        selected = [int(i) for i in self.files_spreadsheet.selection()]
        self.edit_window = tk.Toplevel(self)
        self.edit_window.grab_set()
        if not platform.system() == 'Darwin':
            self.edit_window.iconbitmap('img/edit.ico')
        self.edit_window.title('Edit Groups')
        introtext = 'For ' + str(len(selected)) + ' selected file(s), add to / remove from these groups:'
        edit_intro = tk.Label(self.edit_window, text=introtext)
        self.edit_listbox = tk.Listbox(self.edit_window, width=50,selectmode=tk.EXTENDED,
                                     activestyle=tk.NONE)
        for group in self.GROUPS:
            self.edit_listbox.insert(tk.END, group)
        self.button_edit_add = tk.Button(self.edit_window, text='Add',
                                         state=tk.DISABLED, width=6,
                                         command=lambda: self.handle_edit('add'))
        self.button_edit_remove = tk.Button(self.edit_window, text='Remove',
                                            state=tk.DISABLED, width=6,
                                            command=lambda: self.handle_edit('remove'))
        edit_intro.grid(row=0,column=0,sticky='nsew', padx=(30), pady=30,
                        columnspan=2)
        self.edit_listbox.grid(row=1,column=0,sticky='nsew',padx=(30), pady=(0,30),
                               columnspan=2)
        self.button_edit_add.grid(row=2, column=0, sticky='nsew', padx=30, pady=(0,30))
        self.button_edit_remove.grid(row=2,column=1,sticky='nsew', padx=30, pady=(0,30))
        self.edit_listbox.bind('<<ListboxSelect>>', self.check_addremove)

    def save_groups(self):
        group_dict = {fed.directory : fed.group for fed in self.LOADED_FEDS
                      if fed.group}
        savepath = tk.filedialog.asksaveasfilename(title='Select where to save group labels',
                                                       defaultextension='.csv',
                                                       filetypes = [('Comma-Separated Values', '*.csv')],
                                                       initialdir='groups')
        if savepath:
            df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in group_dict.items()]))
            df.to_csv(savepath)
            del df

    def load_groups(self):
        settings_file = tk.filedialog.askopenfilenames(title='Select group labels to load',
                                                        defaultextension='.csv',
                                                        filetypes=[('Comma-Separated Values', '*.csv')],
                                                        initialdir='groups')
        if settings_file:
            df = pd.read_csv(settings_file[0],index_col=0,dtype=str)
            for fed in self.LOADED_FEDS:
                if self.abs_groups_val.get():
                    lookfor = fed.directory
                else:
                    lookfor = fed.basename
                    df.columns = [os.path.basename(col) for col in df.columns]
                if lookfor in df.columns:
                    fed.group = []
                    for grp in df[lookfor]:
                        if not pd.isna(grp):
                            fed.group.append(str(grp))
        self.update_file_view()
        self.update_group_view()

    def save_session(self, dialog=True):
        if dialog:
            savepath = tk.filedialog.asksaveasfilename(title='Select where to save session file',
                                                       defaultextension='.fed',
                                                       filetypes = [('FED Session (pickled file)', '*.FED')],
                                                       initialdir='sessions')
        else:
            savepath = 'sessions/LAST_USED.fed'
        if savepath:
            jarred = {}
            jarred['feds'] = self.LOADED_FEDS
            jarred_plots = OrderedDict()
            for name, obj in self.PLOTS.items():
                saved_args = {key:val for key, val in obj.arguments.items() if key != 'ax'}
                jarred_plots[name] = FED_Plot(figname=obj.figname,
                                              plotfunc=obj.plotfunc,
                                              arguments=saved_args,
                                              plotdata=obj.plotdata,
                                              x=obj.x,y=obj.y,
                                              dpi=obj.dpi)
            jarred['plots'] = jarred_plots
            jarred['settings'] = self.save_settings(return_df = True)
            pickle.dump(jarred, open(savepath, 'wb'))

    def load_session(self):
        session_file = tk.filedialog.askopenfilenames(title='Select a session file to load',
                                                      initialdir='sessions',
                                                      multiple=False)
        if session_file:
            unjarred = pickle.load(open(session_file[0],'rb'))
            self.LOADED_FEDS = unjarred['feds']
            self.update_file_view()
            self.update_group_view()
            self.update_all_buttons()
            self.delete_plot(all=True, raise_plots=False)
            self.PLOTS = unjarred['plots']
            for plot in self.PLOTS:
                self.PLOTS[plot].arguments['ax'] = self.AX
                self.raise_figure(plot)
            self.load_settings(dialog=False, from_df=unjarred['settings'])

    def descriptives_window(self):
        self.stat_window = tk.Toplevel(self)
        self.stat_window.resizable(False, False)
        self.stat_window.grab_set()
        if not platform.system() == 'Darwin':
            self.stat_window.iconbitmap('img/mu.ico')
        self.stat_window.title('Summary Stats')
        self.stats_radio_var = tk.StringVar()
        self.stats_radio_var.set('None')
        self.stats_from_feds = ttk.Radiobutton(self.stat_window,
                                               text='Use selected FEDs',
                                               var=self.stats_radio_var,
                                               value='from_feds',
                                               command=self.handle_stats_check)
        self.stats_from_groups = ttk.Radiobutton(self.stat_window,
                                                 text='Use selected Groups',
                                                 var=self.stats_radio_var,
                                                 value='from_groups',
                                                 command=self.handle_stats_check)
        self.stats_all_groups = ttk.Radiobutton(self.stat_window,
                                                text='Use all Groups',
                                                var=self.stats_radio_var,
                                                value='all_groups',
                                                command=self.handle_stats_check)
        self.stats_okay_button = tk.Button(self.stat_window,
                                           text='Okay',
                                           command=self.stats_proceed,
                                           state=tk.DISABLED)
        self.stats_stop_button = tk.Button(self.stat_window,
                                           text='Cancel',
                                           command=self.stat_window.destroy,)
        self.stats_from_feds.grid(row=0,column=0,sticky='nsew',padx=100,pady=(20,5),
                                  columnspan=2)
        self.stats_from_groups.grid(row=1,column=0,sticky='nsew',padx=100,pady=5,
                                    columnspan=2)
        self.stats_all_groups.grid(row=2,column=0,sticky='nsew',padx=100,pady=5,
                                   columnspan=2)
        self.stats_okay_button.grid(row=3, column=0, sticky='nsew', padx=(40,5), pady=(20,5))
        self.stats_stop_button.grid(row=3, column=1, sticky='nsew', padx=(5,40), pady=(20,5))
        if not self.files_spreadsheet.selection():
            self.stats_from_feds.configure(state=tk.DISABLED)
        if not self.group_view.curselection():
            self.stats_from_groups.configure(state=tk.DISABLED)
        if not self.GROUPS:
            self.stats_all_groups.configure(state=tk.DISABLED)

    def init_plot(self):
        self.failed_date_feds = []
        selection = self.plot_treeview.selection()
        self.plotting = True
        for i in selection:
            text = self.plot_treeview.item(i,'text')
            if self.is_plottable(text):
                if self.plotting:
                    if text in self.plot_nodes_func:
                        self.clear_axes()
                        plotting_function = self.plot_nodes_func[text]
                        self.format_polar_axes(text)
                        if plotting_function == self.avg_plot_TK:
                            plotting_function(text)
                        else:
                            plotting_function()
            self.update()
        if self.failed_date_feds:
            self.raise_date_filter_error()

    def pellet_plot_single_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                arg_dict['ax'] = self.AX
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                func_choices = {'Cumulative': plots.pellet_plot_single,
                                'Frequency' : plots.pellet_freq_single}
                name_choices = {'Cumulative': 'Cumulative pellet plot for ' + obj.filename,
                                'Frequency' : 'Frequency pellet plot for ' + obj.filename}
                plotdata_choices = {'Cumulative': getdata.pellet_plot_single,
                                    'Frequency' : getdata.pellet_freq_single}
                plotfunc = func_choices[self.pelletplottype_menu.get()]
                basename = name_choices[self.pelletplottype_menu.get()]
                plotdata = plotdata_choices[self.pelletplottype_menu.get()](**arg_dict)
                fig_name = self.create_plot_name(basename)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                                    plotdata=plotdata, arguments=arg_dict,
                                    x=7,y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plotfunc(**arg_dict)
                self.display_plot(new_plot)

    def pellet_plot_multi_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        arg_dict['FEDs'] = FEDs_to_plot
        arg_dict['ax'] = self.AX
        fig_name = self.create_plot_name('Multi-FED Pellet Plot')
        multi_plot_choices = {('Cumulative',True) :plots.pellet_plot_multi_aligned,
                              ('Cumulative',False):plots.pellet_plot_multi_unaligned,
                               ('Frequency',True)  :plots.pellet_freq_multi_aligned,
                               ('Frequency',False) :plots.pellet_freq_multi_unaligned}
        plotdata_choices = {('Cumulative',True) :getdata.pellet_plot_multi_aligned,
                              ('Cumulative',False):getdata.pellet_plot_multi_unaligned,
                               ('Frequency',True)  :getdata.pellet_freq_multi_aligned,
                               ('Frequency',False) :getdata.pellet_freq_multi_unaligned}
        choice = (self.pelletplottype_menu.get(),self.pelletplotalign_checkbox_val.get())
        plotfunc = multi_plot_choices[choice]
        plotdata = plotdata_choices[choice](**arg_dict)
        new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                            arguments=arg_dict, plotdata=plotdata,
                            x=7,y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plotfunc(**arg_dict)
        self.display_plot(new_plot)

    def avg_plot_TK(self, plot_name):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        args_dict['FEDs'] = feds
        args_dict['ax'] = self.AX
        choices = {'Average Pellet Plot':'pellets',
                   'Average Poke Plot (Correct)':'correct pokes',
                   'Average Poke Plot (Error)':'errors',
                   'Average Poke Plot (Left)':'left pokes',
                   'Average Poke Plot (Right)':'right pokes',
                   'Average Poke Bias Plot (Correct %)':'poke bias (correct %)',
                   'Average Poke Bias Plot (Left %)':'poke bias (left %)',
                   'Average Retrieval Time Plot':'retrieval time'}
        args_dict['dependent'] = choices[plot_name]
        method = self.average_method_menu.get()
        if method == 'shared time':
            plotfunc=plots.average_plot_ontime
            plotdata=getdata.average_plot_ontime(**args_dict)
        elif method == 'shared date & time':
            plotfunc=plots.average_plot_ondatetime
            plotdata=getdata.average_plot_ondatetime(**args_dict)
        elif method == 'elapsed time':
            plotfunc=plots.average_plot_onstart
            plotdata=getdata.average_plot_onstart(**args_dict)
        fig = plotfunc(**args_dict)
        if fig == 'NO_OVERLAP ERROR':
            self.raise_average_warning()
            return
        fig_name = self.create_plot_name('Average Plot of ' + args_dict['dependent'].capitalize())
        new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                            plotdata=plotdata,arguments=args_dict,
                            x=7,y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plotfunc(**args_dict)
        self.display_plot(new_plot)

    def interpellet_plot_TK(self):
        arg_dict = self.get_current_settings_as_args()
        arg_dict['ax'] = self.AX
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        basename = 'Inter-pellet Interval Plot'
        fig_name = self.create_plot_name(basename)
        plotdata = getdata.interpellet_interval_plot(**arg_dict)
        new_plot = FED_Plot(figname=fig_name,plotfunc=plots.interpellet_interval_plot,
                            plotdata=plotdata,arguments=arg_dict,
                            x=4, y=5,)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.interpellet_interval_plot(**arg_dict)
        self.display_plot(new_plot)

    def group_ipi_TK(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.group_interpellet_interval_plot(**args_dict)
        fig_name = self.create_plot_name('Group Interpellet Interval Plot')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.group_interpellet_interval_plot,
                            arguments=args_dict, plotdata=plotdata,
                            x=4, y=5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.group_interpellet_interval_plot(**args_dict)
        self.display_plot(new_plot)

    def meal_histo_TK(self):
        arg_dict = self.get_current_settings_as_args()
        arg_dict['ax'] = self.AX
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        arg_dict['FEDs'] = FEDs_to_plot
        basename = 'Meal Size Histogram'
        fig_name = self.create_plot_name(basename)
        plotdata = getdata.meal_size_histogram(**arg_dict)
        new_plot = FED_Plot(figname=fig_name,plotfunc=plots.meal_size_histogram,
                            plotdata=plotdata,arguments=arg_dict,
                            x=7, y=3.5,)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.meal_size_histogram(**arg_dict)
        self.display_plot(new_plot)

    def group_meal_histo_TK(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.grouped_meal_size_histogram(**args_dict)
        fig_name = self.create_plot_name('Group Meal Histogram Plot')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.grouped_meal_size_histogram,
                            arguments=args_dict, plotdata=plotdata,
                            x=7, y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.grouped_meal_size_histogram(**args_dict)
        self.display_plot(new_plot)

    def daynight_plot_TK(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.daynight_plot(**args_dict)
        value = args_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Day Night Plot')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.daynight_plot,
                            arguments=args_dict, plotdata=plotdata,
                            x=5,y=5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.daynight_plot(**args_dict)
        self.display_plot(new_plot)

    def chronogram_line_TK(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.line_chronogram(**args_dict)
        value = args_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Chronogram (Line)')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.line_chronogram,
                            arguments=args_dict, plotdata=plotdata,
                            x=7, y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.line_chronogram(**args_dict)
        self.display_plot(new_plot)

    def chronogram_circle_TK(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.circle_chronogram(**args_dict)
        value = args_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Chronogram (Circle)')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.circle_chronogram,
                            arguments=args_dict, plotdata=plotdata,
                            x=7, y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.circle_chronogram(**args_dict)
        self.display_plot(new_plot)

    def chronogram_heatmap_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        arg_dict['ax'] = self.AX
        arg_dict['return_cb'] = True
        value = arg_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Chronogram (Heatmap)')
        plotdata = getdata.heatmap_chronogram(**arg_dict)
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.heatmap_chronogram,
                            arguments=arg_dict, plotdata=plotdata,
                            x=7, y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        self.CB = plots.heatmap_chronogram(**arg_dict)
        self.display_plot(new_plot)

    def dn_ipi_TK(self):
        arg_dict = self.get_current_settings_as_args()
        arg_dict['ax'] = self.AX
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        basename = 'Day Night Interpellet Interval Plot'
        fig_name = self.create_plot_name(basename)
        plotdata = getdata.day_night_ipi_plot(**arg_dict)
        new_plot = FED_Plot(figname=fig_name,plotfunc=plots.day_night_ipi_plot,
                            plotdata=plotdata,arguments=arg_dict,
                            x=4, y=5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.day_night_ipi_plot(**arg_dict)
        self.display_plot(new_plot)

    def poke_plot_single_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                arg_dict['ax'] = self.AX
                fig_name = self.create_plot_name('Poke plot for ' + obj.filename)
                plotdata=getdata.poke_plot(**arg_dict)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plots.poke_plot,
                                    plotdata=plotdata, arguments=arg_dict,
                                    x=7,y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plots.poke_plot(**arg_dict)
                self.display_plot(new_plot)

    def poke_bias_single_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                arg_dict['ax'] = self.AX
                fig_name = self.create_plot_name('Poke bias plot for ' + obj.filename)
                plotdata=getdata.poke_bias(**arg_dict)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plots.poke_bias,
                                    plotdata=plotdata,
                                    arguments=arg_dict,
                                    x=7,y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plots.poke_bias(**arg_dict)
                self.display_plot(new_plot)

    def poketime_plot_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                arg_dict['ax'] = self.AX
                fig_name = self.create_plot_name('Poke time plot for ' + obj.filename)
                plotdata=getdata.poketime_plot(**arg_dict)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plots.poketime_plot,
                                    plotdata=plotdata,
                                    arguments=arg_dict,
                                    x=7,y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plots.poketime_plot(**arg_dict)
                self.display_plot(new_plot)

    def breakpoint_plot(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        arg_dict['ax'] = self.AX
        fig_name = self.create_plot_name('Breakpoint Plot')
        plotdata = getdata.pr_plot(**arg_dict)
        fig_len = min([max([len(FEDs_to_plot), 4]), 8])
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.pr_plot,
                            arguments=arg_dict, plotdata=plotdata,
                            x=fig_len, y=5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.pr_plot(**arg_dict)
        self.display_plot(new_plot)

    def group_breakpoint_plot(self):
        args_dict = self.get_current_settings_as_args()
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        feds = []
        for fed in self.LOADED_FEDS:
            for group in fed.group:
                if group in groups:
                    feds.append(fed)
                    break
        args_dict['FEDs'] = feds
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            args_dict['date_filter'] = (s,e)
            for fed in feds:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        args_dict['ax'] = self.AX
        plotdata = getdata.group_pr_plot(**args_dict)
        fig_name = self.create_plot_name('Group Breakpoint Plot')
        new_plot = FED_Plot(figname=fig_name, plotfunc=plots.group_pr_plot,
                            arguments=args_dict, plotdata=plotdata,
                            x=3.5,y=5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plots.group_pr_plot(**args_dict)
        self.display_plot(new_plot)

    def retrieval_plot_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                arg_dict['ax'] = self.AX
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                plotdata = getdata.retrieval_time_single(**arg_dict)
                fig_name = self.create_plot_name('Retrieval Time Plot for ' + obj.filename)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plots.retrieval_time_single,
                                    plotdata=plotdata, arguments=arg_dict,
                                    x=7,y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plots.retrieval_time_single(**arg_dict)
                self.display_plot(new_plot)

    def retrieval_plot_multi_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        if self.date_filter_val.get():
            s,e = self.get_date_filter_dates()
            arg_dict['date_filter'] = (s,e)
            for fed in FEDs_to_plot:
                if not plots.date_filter_okay(fed.data, s, e):
                    self.failed_date_feds.append(fed)
                    continue
        if self.failed_date_feds:
            return
        arg_dict['FEDs'] = FEDs_to_plot
        arg_dict['ax'] = self.AX
        fig_name = self.create_plot_name('Multi Retrieval Time Plot')
        plotfunc = plots.retrieval_time_multi
        plotdata = getdata.retrieval_time_multi(**arg_dict)
        new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                            arguments=arg_dict, plotdata=plotdata,
                            x=7, y=3.5)
        self.PLOTS[fig_name] = new_plot
        self.resize_plot(new_plot)
        plotfunc(**arg_dict)
        self.display_plot(new_plot)

    def battery_life_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                arg_dict['ax'] = self.AX
                plotfunc = plots.battery_plot
                fig_name = self.create_plot_name('Battery Life for ' + obj.filename)
                plotdata = getdata.battery_plot(**arg_dict)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                                    plotdata=plotdata, arguments=arg_dict,
                                    x=7, y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plotfunc(**arg_dict)
                self.display_plot(new_plot)

    def motor_turns_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            if self.plotting == True:
                self.clear_axes()
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                if self.date_filter_val.get():
                    s,e = self.get_date_filter_dates()
                    if not plots.date_filter_okay(obj.data, s, e):
                        self.failed_date_feds.append(obj)
                        continue
                    else:
                        arg_dict['date_filter'] = (s,e)
                arg_dict['ax'] = self.AX
                plotfunc = plots.motor_plot
                fig_name = self.create_plot_name('Motor Turns for ' + obj.filename)
                plotdata = getdata.motor_plot(**arg_dict)
                new_plot = FED_Plot(figname=fig_name, plotfunc=plotfunc,
                                    plotdata=plotdata, arguments=arg_dict,
                                    x=7, y=3.5)
                self.PLOTS[fig_name] = new_plot
                self.resize_plot(new_plot)
                plotfunc(**arg_dict)
                self.display_plot(new_plot)

    #---HOME HELPER FUNCTIONS
    def update_file_view(self):
        self.files_spreadsheet.delete(*self.files_spreadsheet.get_children())
        for i,fed in enumerate(self.LOADED_FEDS):
            if fed.missing_columns:
                tag = emoji.emojize(':warning:')
            else:
                tag = ''
            values = (tag, fed.basename, fed.mode, fed.events,
                      fed.start_time.strftime('%b %d %Y, %H:%M'),
                      fed.end_time.strftime('%b %d %Y, %H:%M'),
                      str(fed.duration), ', '.join(fed.group))
            self.files_spreadsheet.insert('', i, str(i), values=values)

    def update_group_view(self):
        self.GROUPS = list(set([name for fed in self.LOADED_FEDS for name in fed.group]))
        self.GROUPS.sort()
        self.group_view.delete(0,tk.END)
        for group in self.GROUPS:
            self.group_view.insert(tk.END,group)

    def walk_filenames(self, folder):
        output = []
        dirs = os.walk(folder)
        for directory in dirs:
            dirname = directory[0]
            filelist = directory[-1]
            if filelist:
                for file in filelist:
                    path_to_file = os.path.join(dirname, file)
                    output.append(path_to_file)
        return output

    def hover_text_one(self, event):
        widget = event.widget
        self.home_buttons_help.configure(text=self.hover_text_one_dict[widget])

    def clear_hover_text_one(self, event):
        self.show_plot_help()

    def show_plot_help(self, *event):
        selection = self.plot_treeview.selection()
        if selection:
            text = self.plot_treeview.item(selection[-1],'text')
            if text in self.plot_nodes_help:
                self.home_buttons_help.configure(text=self.plot_nodes_help[text])
            else:
                self.home_buttons_help.configure(text='')
        else:
                self.home_buttons_help.configure(text='')

    def sort_FEDs(self, event, reverse):
        where_clicked = self.files_spreadsheet.identify_region(event.x,event.y)
        if where_clicked == 'heading':
            column = self.files_spreadsheet.identify_column(event.x)
            column_name = self.files_spreadsheet.column(column)['id']
            if column_name == "Name":
                self.LOADED_FEDS.sort(key=lambda x:x.basename, reverse=reverse)
            if column_name == "Mode":
                self.LOADED_FEDS.sort(key=lambda x:x.mode, reverse=reverse)
            if column_name == "Start Time":
                self.LOADED_FEDS.sort(key=lambda x:x.start_time, reverse=reverse)
            if column_name == "End Time":
                self.LOADED_FEDS.sort(key=lambda x:x.end_time, reverse=reverse)
            if column_name == "# Events":
                self.LOADED_FEDS.sort(key=lambda x:x.events, reverse=reverse)
            if column_name == "Duration":
                self.LOADED_FEDS.sort(key=lambda x:x.duration, reverse=reverse)
            if column_name == "Groups":
                self.LOADED_FEDS.sort(key=lambda x:len(x.group), reverse=reverse)
            if column_name == '':
                self.LOADED_FEDS.sort(key=lambda x:len(x.missing_columns), reverse=reverse)
            self.update_file_view()

    def is_plottable(self, plot_name):
        plottable = False
        if plot_name in ['Single Pellet Plot', 'Multi Pellet Plot',
                         'Interpellet Interval', 'Poke Bias Plot',
                         'Chronogram (Heatmap)', 'Breakpoint Plot', 'Retrieval Time Plot',
                         'Multi Retrieval Time Plot', 'Battery Life', 'Motor Turns',
                         'Day/Night Interpellet Interval Plot', 'Meal Size Histogram']:
            if self.files_spreadsheet.selection():
                plottable = True
                if plot_name == 'Breakpoint Plot':
                    selected = [self.LOADED_FEDS[int(i)]
                                for i in self.files_spreadsheet.selection()]
                    if not all(f.mode == 'PR' for f in selected):
                        plottable = False
            else:
                plottable = False
        elif plot_name in ['Single Poke Plot', 'Poke Time Plot']:
            if self.files_spreadsheet.selection():
                if (self.poke_correct_val.get() or self.poke_error_val.get() or
                    self.poke_left_val.get() or self.poke_right_val.get()):
                    plottable = True
            else:
                plottable = False
        elif plot_name in ['Average Pellet Plot', 'Day/Night Plot', 'Chronogram (Line)',
                          'Average Poke Plot (Correct)','Average Poke Plot (Error)',
                          'Average Poke Plot (Left)','Average Poke Plot (Right)',
                          'Average Poke Bias Plot (Correct %)','Average Poke Bias Plot (Left %)',
                          'Group Interpellet Interval','Group Breakpoint Plot',
                          'Average Retrieval Time Plot', 'Group Meal Size Histogram',
                          'Chronogram (Circle)']:
            #if the all groups box is checked
            if self.allgroups_val.get():
                #if there are any groups
                if self.GROUPS:
                    plottable = True
                else:
                    plottable = False
                if plot_name == 'Group Breakpoint Plot':
                    to_plot = []
                    for fed in self.LOADED_FEDS:
                        for group in self.GROUPS:
                            if group in fed.group:
                                to_plot.append(fed)
                                break
                    if not all(f.mode == 'PR' for f in to_plot):
                        plottable = False
            else:
                #if there are groups selected
                if self.group_view.curselection():
                    plottable = True
                else:
                    plottable = False
                if plot_name == 'Group Breakpoint Plot':
                    to_plot = []
                    for fed in self.LOADED_FEDS:
                        for i in self.group_view.curselection():
                            group = self.GROUPS[int(i)]
                            if group in fed.group:
                                to_plot.append(fed)
                                break
                    if not all(f.mode == 'PR' for f in to_plot):
                        plottable = False
        else:
            plottable = False
        return plottable

    def update_create_plot_button(self):
        plottables = []
        selected = self.plot_treeview.selection()
        for i in selected:
            plot_name = self.plot_treeview.item(i,'text')
            plottables.append(self.is_plottable(plot_name))
        if any(plottables):
            self.button_create_plot.configure(state=tk.NORMAL)
        else:
            self.button_create_plot.configure(state=tk.DISABLED)

    def update_buttons_home(self,*event):
        self.update_create_plot_button()
        #if there are feds selected
        if self.files_spreadsheet.selection():
            self.button_concat.configure(state=tk.NORMAL)
            self.button_delete.configure(state=tk.NORMAL)
            self.button_create_group.configure(state=tk.NORMAL)
        else:
            self.button_concat.configure(state=tk.DISABLED)
            self.button_delete.configure(state=tk.DISABLED)
            self.button_create_group.configure(state=tk.DISABLED)
        #if groups are selected
        if self.group_view.curselection():
            self.button_delete_group.configure(state=tk.NORMAL)
        else:
            self.button_delete_group.configure(state=tk.DISABLED)
        #if there are feds loaded
        if self.LOADED_FEDS:
            self.button_load_groups.configure(state=tk.NORMAL)
        else:
            self.button_load_groups.configure(state=tk.DISABLED)
        #if there are groups loaded
        if self.GROUPS:
            self.button_save_groups.configure(state=tk.NORMAL)
        else:
            self.button_save_groups.configure(state=tk.DISABLED)
        #if there are feds selected and groups loaded
        if self.files_spreadsheet.selection() and self.GROUPS:
            self.button_edit_group.configure(state=tk.NORMAL)
        else:
            self.button_edit_group.configure(state=tk.DISABLED)
        #if there are feds selected OR groups loaded
        if self.files_spreadsheet.selection() or self.GROUPS:
             self.button_descriptives.configure(state=tk.NORMAL)
        else:
            self.button_descriptives.configure(state=tk.DISABLED)

    def update_all_buttons(self,*event):
        self.update_buttons_home()
        self.update_buttons_plot()

    def create_okay(self):
        group_name = self.create_name.get()
        selected = self.files_spreadsheet.selection()
        FEDs_to_add = [self.LOADED_FEDS[int(i)] for i in selected]
        for fed in FEDs_to_add:
            fed.group.append(group_name)
        self.update_file_view()
        self.update_group_view()
        self.update_buttons_home()
        self.create_window.destroy()

    def create_check(self, *args):
        new_name = self.create_name.get()
        if new_name == '':
            self.ok_button_create.configure(state=tk.DISABLED)
        else:
            if new_name in self.GROUPS:
                self.warning_var.set('Group already in use!')
                self.ok_button_create.configure(state=tk.DISABLED)
            else:
                self.warning_var.set('')
                self.ok_button_create.configure(state=tk.NORMAL)

    def select_group(self, event):
        clicked = self.group_view.curselection()
        if clicked:
            to_raise = []
            for ind in clicked:
                group = self.GROUPS[ind]
                for i,fed in enumerate(self.LOADED_FEDS):
                    if group in fed.group:
                        to_raise.append(i)
            to_raise = list(set(to_raise))
            self.files_spreadsheet.selection_set(to_raise)
        self.update_buttons_home(None)

    def open_url(self, url, *args):
        webbrowser.open_new(url)

    def expand_plot_selector(self):
        self.plot_treeview.item(self.ps_pellet, open=True)
        self.plot_treeview.item(self.ps_poke, open=True)
        self.plot_treeview.item(self.ps_circadian, open=True)
        self.plot_treeview.item(self.ps_other, open=True)

    def handle_plot_selelection(self, event):
        self.show_plot_help()
        self.update_buttons_home()

    def select_all_FEDs(self, *event):
        items = len(self.LOADED_FEDS)
        self.files_spreadsheet.selection_set(list(range(items)))
        self.update_all_buttons()

    def escape(self, *event):
        if self.focus_get() == self.files_spreadsheet:
            self.files_spreadsheet.selection_remove(self.files_spreadsheet.selection())
        if self.focus_get() == self.plot_treeview:
            self.plot_treeview.selection_remove(self.plot_treeview.selection())
        if self.loading:
            self.loading = False
        if self.plotting:
            self.plotting = False
        self.update_all_buttons()

    def check_addremove(self, *event):
        if self.edit_listbox.curselection():
            self.button_edit_add.configure(state=tk.NORMAL)
            self.button_edit_remove.configure(state=tk.NORMAL)
        else:
            self.button_edit_add.configure(state=tk.DISABLED)
            self.button_edit_remove.configure(state=tk.DISABLED)

    def handle_edit(self, todo):
        selected_groups = self.edit_listbox.curselection()
        selected_feds = [int(i) for i in self.files_spreadsheet.selection()]
        groups = []
        for i in selected_groups:
            groups.append(self.edit_listbox.get(i))
        for group in groups:
            for i in selected_feds:
                fed = self.LOADED_FEDS[i]
                if todo == 'add':
                    if group not in fed.group:
                        fed.group.append(group)
                elif todo == 'remove':
                    if group in fed.group:
                        fed.group.remove(group)
        self.update_all_buttons()
        self.update_group_view()
        self.update_file_view()
        self.edit_window.destroy()

    def handle_stats_check(self):
        if self.stats_radio_var.get() != 'None':
            self.stats_okay_button.configure(state=tk.NORMAL)

    def stats_proceed(self):
        time = dt.datetime.now().strftime('%m%d%y_%H%M%S')
        mini = int(self.meal_pelletmin_box.get())
        delay = int(self.mealdelay_box.get())
        if self.stats_radio_var.get() == 'from_feds':
            feds = [self.LOADED_FEDS[int(i)] for i in self.files_spreadsheet.selection()]
            results = plots.fed_summary(feds, meal_pellet_minimum=mini,
                                        meal_duration=delay)
            savepath = tk.filedialog.askdirectory(title='Select where to save stats')
            if savepath:
                name = 'FED Stats ' + time
                savename = self.create_file_name(savepath, name, ext='.csv')
                results.to_csv(savename)
        else:
            if self.stats_radio_var.get() == 'from_groups':
                groups = [self.GROUPS[int(i)] for i in self.group_view.curselection()]
            elif self.stats_radio_var.get() == 'all_groups':
                groups = self.GROUPS
            results = OrderedDict()
            for group in groups:
                feds = [fed for fed in self.LOADED_FEDS if group in fed.group]
                results[group] = plots.fed_summary(feds, meal_pellet_minimum=mini,
                                                   meal_duration=delay)
            savepath = tk.filedialog.askdirectory(title='Select where to save stats')
            if savepath:
                name = 'FED Stats ' + time
                dirname = self.create_file_name(savepath, name)
                os.makedirs(dirname)
                for group, result in results.items():
                    result.to_csv(os.path.join(dirname, group) + '.csv')
        self.stat_window.destroy()

    #---PLOT TAB BUTTON FUNCTIONS
    def rename_plot(self):
        clicked = self.plot_listbox.curselection()[0]
        self.old_name = self.plot_listbox.get(clicked)
        self.rename_window = tk.Toplevel(self)
        self.rename_window.grab_set()
        self.rename_window.title('Rename plot: ' + self.old_name)
        self.rename_var = tk.StringVar()
        self.rename_var.set(self.old_name)
        self.rename_var.trace_add('write',self.rename_check)
        self.warning_var = tk.StringVar()
        self.warning_var.set('')
        self.warning_label = tk.Label(self.rename_window,
                                      textvariable=self.warning_var)
        self.entry = tk.Entry(self.rename_window,
                         textvariable=self.rename_var,
                         width=50)
        self.ok_button = tk.Button(self.rename_window,text='OK',
                              command=lambda: self.rename_okay())
        self.cancel_button = tk.Button(self.rename_window,
                                       text='Cancel',
                                       command=self.rename_window.destroy)
        self.warning_label.grid(row=0,column=0, sticky='w',
                                columnspan=2,padx=(20,0),pady=(20,0))
        self.entry.grid(row=1,column=0,sticky='ew',padx=(20,20),pady=(20,0),
                   columnspan=2)
        self.ok_button.grid(row=2,column=0,sticky='ew',padx=(20,20),pady=(20,20))
        self.cancel_button.grid(row=2,column=1,sticky='ew',padx=(20,20),pady=(20,20))

    def delete_plot(self, **kwargs):
        raise_plots = True
        clicked=sorted(list(self.plot_listbox.curselection()), reverse=True)
        if 'all' in kwargs:
            if kwargs.get('all'):
                clicked = sorted(list(range(len(self.PLOTS))), reverse=True)
        if 'raise_plots' in kwargs:
            if not kwargs.get('raise_plots'):
                raise_plots = False
        new_plot_index = 0
        for i in clicked:
            selection=self.plot_listbox.get(i)
            self.plot_listbox.delete(i)
            del(self.PLOTS[selection])
            new_plot_index=self.plot_listbox.size()-1
        if new_plot_index>=0 and raise_plots:
            new_plot=self.plot_listbox.get(new_plot_index)
            self.raise_figure(new_plot, new=False)
        else:
            self.clear_axes()
            self.canvas.draw_idle()
            self.nav_toolbar.update()
        self.update_buttons_plot(None)

    def new_window_plot(self):
        in_use = [obj.in_use for obj in self.NEW_WINDOW_FIGS]
        if sum(in_use) == 5:
            self.raise_new_window_warning()
            return
        clicked=self.plot_listbox.curselection()
        graph_name=self.plot_listbox.get(clicked)
        plot_obj = self.PLOTS[graph_name]
        self.reuse_new_window_figure(plot_obj)

    def reuse_new_window_figure(self, plot_obj):
        obj_to_reuse = next(x for x in self.NEW_WINDOW_FIGS if x.in_use == False)
        if obj_to_reuse.canvas == None:
            self.create_new_window_canvas(obj_to_reuse, plot_obj)
        obj_to_reuse.in_use = True
        new_arguments = {key:val for key,val in plot_obj.arguments.items() if key != 'ax'}
        obj_to_reuse.ax.clear()
        new_arguments['ax'] = obj_to_reuse.ax
        for ax in obj_to_reuse.fig.axes:
            ax.clear()
            if ax != obj_to_reuse.ax:
                ax.remove()
        plot_obj.plotfunc(**new_arguments)
        obj_to_reuse.toplevel.deiconify()
        obj_to_reuse.toplevel.geometry('{0}x{1}'.format(int(plot_obj.x*plot_obj.dpi),
                                             int(plot_obj.y*plot_obj.dpi)))
        obj_to_reuse.canvas.draw_idle()
        obj_to_reuse.toolbar.update()

    def create_new_window_canvas(self, new_window_fig, plot_obj):
        obj_to_reuse = new_window_fig
        new_window = tk.Toplevel()
        new_window.title(plot_obj.figname)
        if not platform.system() == 'Darwin':
            new_window.iconbitmap('img/graph_icon.ico')
        new_window.protocol("WM_DELETE_WINDOW", lambda: self.close_new_window(new_window))
        new_frame = ttk.Frame(new_window)
        new_frame.pack(fill=tk.BOTH, expand=1)
        new_fig, new_ax = obj_to_reuse.fig, obj_to_reuse.ax
        for ax in new_fig.axes:
            ax.clear()
            if ax != new_ax:
                ax.remove()
        canvas = FigureCanvasTkAgg(new_fig, master=new_frame)
        canvas.draw_idle()
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        nav_toolbar = NavigationToolbar2Tk(canvas, new_frame)
        nav_toolbar.update()
        canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        obj_to_reuse.toplevel = new_window
        obj_to_reuse.frame = new_frame
        obj_to_reuse.canvas = canvas
        obj_to_reuse.toolbar = nav_toolbar

    def close_new_window(self, toplevel):
        #set in_use of New_Window_Figure
        for obj in self.NEW_WINDOW_FIGS:
            if obj.toplevel == toplevel:
                obj.in_use = False
        #close, but use withdraw
        toplevel.withdraw()

    def save_plots(self):
        clicked=self.plot_listbox.curselection()
        ext = self.img_format_menu.get()
        if clicked:
            savepath = tk.filedialog.askdirectory(title='Select where to save highlighted plots')
            if savepath:
                for i in clicked:
                    graph_name=self.plot_listbox.get(i)
                    if len(clicked) > 1:
                        self.raise_figure(graph_name, new=False)
                    save_name = graph_name+ext
                    full_save = os.path.join(savepath,save_name)
                    if not self.overwrite_checkbox_val.get():
                        c=1
                        while os.path.exists(full_save):
                            save_name = graph_name +  ' (' + str(c) + ')' + ext
                            full_save = os.path.join(savepath,save_name)
                            c+=1
                    self.FIGURE.savefig(full_save,dpi=300)
                    self.FIGURE.set_dpi(150)
                    self.canvas.draw_idle()
                    self.nav_toolbar.update()
                    self.update()

    def show_plot_code(self):
        clicked = self.plot_listbox.curselection()
        for i in clicked:
            plotname = self.plot_listbox.get(i)
            plotobj  = self.PLOTS[plotname]
            new_window = tk.Toplevel(self)
            new_window.title('Code for "' + plotname +'"')
            if not platform.system() == 'Darwin':
                new_window.iconbitmap('img/python.ico')
            textview = tk.Text(new_window, width=150)
            code = fed_inspect.generate_code(plotobj)
            textview.insert(tk.END, code)
            textview.configure(state=tk.DISABLED)
            scrollbar = tk.Scrollbar(new_window, command=textview.yview)
            textview['yscrollcommand'] = scrollbar.set
            save_button = tk.Button(new_window, text='Save as...',
                                    command=lambda plotname=plotname, code=code:
                                        self.save_code(plotname, code))
            textview.grid(row=0,column=0,sticky='nsew')
            scrollbar.grid(row=0,column=1,sticky='nsew')
            save_button.grid(row=1,column=0,sticky='w')
            new_window.grid_rowconfigure(0,weight=1)
            new_window.grid_columnconfigure(0,weight=1)

    def save_plot_data(self):
        clicked=self.plot_listbox.curselection()
        if clicked:
            savepath = tk.filedialog.askdirectory(title='Select where to save data for the highlighted plots')
            if savepath:
                for i in clicked:
                    graph_name=self.plot_listbox.get(i)
                    plot = self.PLOTS[graph_name]
                    df = plot.plotdata
                    overwrite = self.overwrite_checkbox_val.get()
                    if plot.plotfunc in [plots.interpellet_interval_plot,
                                         plots.group_interpellet_interval_plot,
                                         plots.day_night_ipi_plot]:
                        if not df[0].empty:
                            kde_name = graph_name + ' KDE'
                            kde_save = self.create_file_name(savepath, kde_name,
                                                             ext = '.csv',
                                                             overwrite=overwrite)
                            df[0].to_csv(kde_save)
                        bar_name = graph_name + ' bars'
                        bar_save = self.create_file_name(savepath, bar_name,
                                                         ext = '.csv',
                                                         overwrite=overwrite)
                        df[1].to_csv(bar_save)
                    else:
                        save_name = graph_name
                        full_save = self.create_file_name(savepath, save_name,
                                                          ext = '.csv',
                                                          overwrite=overwrite)
                        df.to_csv(full_save)

    #---PLOT HELPER FUNCTIONS
    def display_plot(self, plot_obj, new=True):
        self.update()
        self.canvas.draw_idle()
        self.nav_toolbar.update()
        if new:
            if self.on_display_func == 'heatmap_chronogram':
                self.clear_axes()
                self.format_polar_axes(plot_obj.plotfunc)
                plot_obj.plotfunc(**plot_obj.arguments)
            self.plot_listbox.insert(tk.END,plot_obj.figname)
            self.plot_listbox.selection_clear(0,self.plot_listbox.size())
            self.plot_listbox.selection_set(self.plot_listbox.size()-1)
        self.update_buttons_plot()
        self.update()
        self.tabcontrol.select(self.plot_tab)
        self.on_display_func = plot_obj.plotfunc.__name__

    def raise_figure(self, fig_name, new=True):
        plot_obj = self.PLOTS[fig_name]
        if platform.system() == 'Windows':
            self.plot_cover.grid()
        self.resize_plot(plot_obj)
        print(type(self.AX))
        if plot_obj.plotfunc.__name__ == 'heatmap_chronogram':
            self.CB = plot_obj.plotfunc(**plot_obj.arguments)
        else:
            plot_obj.plotfunc(**plot_obj.arguments)
            if self.on_display_func == 'heatmap_chronogram':
                #annoying bug
                self.clear_axes()
                self.format_polar_axes(plot_obj.plotfunc)
                plot_obj.plotfunc(**plot_obj.arguments)
        self.display_plot(plot_obj, new)
        if platform.system() == 'Windows':
            self.plot_cover.grid_remove()
        plot_index = list(self.PLOTS).index(fig_name)
        self.plot_listbox.selection_clear(0,self.plot_listbox.size())
        self.plot_listbox.selection_set(plot_index)
        self.update_all_buttons()

    def raise_figure_from_listbox(self, event):
        clicked=self.plot_listbox.curselection()
        if len(clicked) == 1:
            selection=self.plot_listbox.get(clicked[0])
            self.raise_figure(selection, new=False)

    def create_plot_name(self, basename):
        fig_name = basename
        c=1
        while fig_name in self.PLOTS.keys():
            fig_name = basename + ' ' + str(c)
            c+=1
        return fig_name

    def create_file_name(self, savepath, savename, ext='', overwrite=False):
        file_name = savename + ext
        full_save = os.path.join(savepath, file_name)
        if not overwrite:
            c=1
            while os.path.exists(full_save):
                file_name = savename + ' (' + str(c) + ')' + ext
                full_save = os.path.join(savepath,file_name)
                c += 1
        return full_save

    def update_buttons_plot(self,*event):
        if self.plot_listbox.curselection():
            self.plot_delete.configure(state=tk.NORMAL)
            self.plot_save.configure(state=tk.NORMAL)
            self.plot_data.configure(state=tk.NORMAL)
            self.plot_inspect.configure(state=tk.NORMAL)
            if len(self.plot_listbox.curselection()) == 1:
                self.plot_rename.configure(state=tk.NORMAL)
                self.plot_popout.configure(state=tk.NORMAL)
            else:
                self.plot_rename.configure(state=tk.DISABLED)
                self.plot_popout.configure(state=tk.DISABLED)
        else:
            self.plot_rename.configure(state=tk.DISABLED)
            self.plot_delete.configure(state=tk.DISABLED)
            self.plot_save.configure(state=tk.DISABLED)
            self.plot_inspect.configure(state=tk.DISABLED)
            self.plot_data.configure(state=tk.DISABLED)
            self.plot_inspect.configure(state=tk.DISABLED)

    def plot_listbox_event(self,event):
        self.raise_figure_from_listbox(event)
        self.update_buttons_plot(event)

    def rename_okay(self):
        new_name = self.rename_var.get()
        self.PLOTS = OrderedDict([(new_name,v) if k == self.old_name
                                 else (k,v) for k,v in
                                 self.PLOTS.items()])
        self.PLOTS[new_name].figname = new_name
        new_position = list(self.PLOTS.keys()).index(new_name)
        self.plot_listbox.delete(new_position)
        self.plot_listbox.insert(new_position,new_name)
        self.rename_window.destroy()
        self.update_buttons_plot()

    def rename_check(self,*args):
        new_name = self.rename_var.get()
        if new_name in list(self.PLOTS.keys()):
            self.warning_var.set('Name already in use!')
            self.ok_button.configure(state=tk.DISABLED)
        else:
            self.warning_var.set('')
            self.ok_button.configure(state=tk.NORMAL)

    def save_code(self, plotname, text):
        savepath = tk.filedialog.asksaveasfilename(title='Select where to save code',
                                                   defaultextension='.py',
                                                   initialfile=plotname,
                                                   filetypes = [('Python', '*.py'),
                                                                ('Text', '*.txt')])
        if savepath:
            with open(savepath, 'w') as file:
                file.write(text)
                file.close()

    def clear_axes(self):
        if self.CB:
            self.CB.remove()
            self.CB = None
        for ax in self.FIGURE.axes:
            ax.clear()
            if ax != self.AX:
                ax.remove()

    def format_polar_axes(self, plotfunc):
        if callable(plotfunc):
            circle_funcs = [plots.circle_chronogram]
        else:
            circle_funcs = ['Chronogram (Circle)']
        if plotfunc in circle_funcs and not self.POLAR:
            print('turning on polar...')
            self.AX.remove()
            self.AX = self.FIGURE.add_subplot(polar=True)
            self.POLAR = True
        elif plotfunc not in circle_funcs and self.POLAR:
            print('turning off polar...')
            self.AX.remove()
            self.AX = self.FIGURE.add_subplot()
            self.POLAR = False
        print(type(self.AX))

    def resize_plot(self, plot_obj):
        self.tabcontrol.select(self.plot_tab)
        self.clear_axes()
        self.format_polar_axes(plot_obj.plotfunc)
        self.geometry('{0}x{1}'.format(plot_obj.x_pix, plot_obj.y_pix))
        self.update()

    #---SETTINGS TAB FUNCTIONS
    def check_pellet_type(self, *event):
        if self.pelletplottype_menu.get() == 'Frequency':
            self.pelletplotcumu_label.configure(fg='black')
            self.pelletplotcumu_menu.configure(state=tk.NORMAL)
        else:
            self.pelletplotcumu_label.configure(fg='gray')
            self.pelletplotcumu_menu.configure(state=tk.DISABLED)

    def check_average_align(self, *event):
        if self.average_method_menu.get() == 'shared time':
            self.average_align_ontime_label.configure(fg='black')
            self.average_alignstart_menu.configure(state=tk.NORMAL)
            self.average_aligndays_menu.configure(state=tk.NORMAL)
        else:
            self.average_align_ontime_label.configure(fg='gray')
            self.average_alignstart_menu.configure(state=tk.DISABLED)
            self.average_aligndays_menu.configure(state=tk.DISABLED)

    def check_date_filter(self, *event):
        if self.date_filter_val.get():
            self.date_filter_days_label.configure(fg='black')
            self.date_filter_hours_label.configure(fg='black')
            self.date_filter_s_days.configure(state=tk.NORMAL)
            self.date_filter_e_days.configure(state=tk.NORMAL)
            self.date_filter_s_hour.configure(state=tk.NORMAL)
            self.date_filter_e_hour.configure(state=tk.NORMAL)
        else:
            self.date_filter_days_label.configure(fg='gray')
            self.date_filter_hours_label.configure(fg='gray')
            self.date_filter_s_days.configure(state=tk.DISABLED)
            self.date_filter_e_days.configure(state=tk.DISABLED)
            self.date_filter_s_hour.configure(state=tk.DISABLED)
            self.date_filter_e_hour.configure(state=tk.DISABLED)

    def save_settings(self, dialog=True, savepath='', return_df=False):
        settings_dict = self.get_current_settings()
        df = pd.DataFrame.from_dict(settings_dict, orient='index',columns=['Values'])
        if return_df:
            return df
        else:
            if dialog:
                savepath = tk.filedialog.asksaveasfilename(title='Select where to save settings',
                                                           defaultextension='.csv',
                                                           filetypes = [('Comma-Separated Values', '*.csv')],
                                                           initialdir='settings')
            if savepath:
                df.to_csv(savepath)

    def load_settings(self, dialog=True, settings_file=[''], from_df=None):
        settings_df = pd.DataFrame()
        now = None
        if dialog:
            settings_file = tk.filedialog.askopenfilenames(title='Select FED3 Data',
                                                           defaultextension='.csv',
                                                           filetypes=[('Comma-Separated Values', '*.csv')],
                                                           initialdir='settings')

        if isinstance(from_df, pd.DataFrame):
            settings_df = from_df
        else:
            if settings_file:
                settings_df = pd.read_csv(settings_file[0],index_col=0)
                if os.path.basename(settings_file[0]).lower() == 'default.csv':
                    now = dt.datetime.now().date()
        if not settings_df.empty:
            self.date_filter_val.set(settings_df.loc['date_filter_val','Values'])
            s = pd.to_datetime(settings_df.loc['date_filter_s_days','Values'])
            e = pd.to_datetime(settings_df.loc['date_filter_e_days','Values'])
            if now is not None:
                s = now
                e = now
            if str(self.date_filter_s_days.cget('state')) == 'disabled':
                self.date_filter_s_days.configure(state=tk.NORMAL)
                self.date_filter_s_days.set_date(s)
                self.date_filter_s_days.configure(state=tk.DISABLED)
            else:
                self.date_filter_s_days.set_date(s)
            if str(self.date_filter_e_days.cget('state')) == 'disabled':
                self.date_filter_e_days.configure(state=tk.NORMAL)
                self.date_filter_e_days.set_date(e)
                self.date_filter_e_days.configure(state=tk.DISABLED)
            else:
                self.date_filter_e_days.set_date(e)
            self.date_filter_s_hour.set(settings_df.loc['date_filter_s_hour','Values'])
            self.date_filter_e_hour.set(settings_df.loc['date_filter_e_hour','Values'])
            self.img_format_menu.set(settings_df.loc['img_format','Values'])
            self.nightshade_checkbox_val.set(settings_df.loc['shade_dark','Values'])
            self.nightshade_lightson.set(settings_df.loc['lights_on','Values'])
            self.nightshade_lightsoff.set(settings_df.loc['lights_off','Values'])
            self.abs_groups_val.set(settings_df.loc['abs_group','Values'])
            self.allgroups_val.set(settings_df.loc['allgroups','Values'])
            self.loadduplicates_checkbox_val.set(settings_df.loc['skip_duplicates','Values'])
            self.overwrite_checkbox_val.set(settings_df.loc['overwrite','Values'])
            self.weirdfed_warning_val.set(settings_df.loc['weirdwarn','Values'])
            self.pelletplottype_menu.set(settings_df.loc['pellet_values','Values'])
            self.pelletplotcumu_menu.set(settings_df.loc['pellet_bins','Values'])
            self.pelletplotcolor_menu.set(settings_df.loc['pellet_color','Values']),
            self.pelletplotalign_checkbox_val.set(settings_df.loc['pellet_align','Values'])
            self.average_error_menu.set(settings_df.loc['average_error','Values'])
            self.average_bin_menu.set(settings_df.loc['average_bins','Values'])
            self.average_method_menu.set(settings_df.loc['average_method','Values'])
            self.average_alignstart_menu.set(settings_df.loc['average_align_start','Values'])
            self.average_aligndays_menu.set(settings_df.loc['average_align_days','Values'])
            self.daynight_values.set(settings_df.loc['circ_value','Values'])
            self.daynight_error_menu.set(settings_df.loc['circ_error','Values'])
            self.daynight_show_indvl_val.set(settings_df.loc['circ_show_indvl','Values'])
            self.ipi_kde_val.set(settings_df.loc['kde','Values'])
            self.ipi_log_val.set(settings_df.loc['logx','Values'])
            self.norm_meal_val.set(settings_df.loc['norm_meals','Values'])
            self.meal_pelletmin_box.set(settings_df.loc['meal_pellet_minimum','Values'])
            self.mealdelay_box.set(settings_df.loc['meal_duration','Values'])
            self.retrieval_threshold_menu.set(settings_df.loc['retrieval_threshold','Values'])
            self.poketime_cutoff_menu.set(settings_df.loc['poketime_cutoff','Values'])
            self.pr_style_menu.set(settings_df.loc['break_style','Values'])
            self.pr_hours_menu.set(settings_df.loc['break_hours','Values'])
            self.pr_mins_menu.set(settings_df.loc['break_mins','Values'])
            self.pr_error_menu.set(settings_df.loc['break_error','Values'])
            self.pr_show_indvl_val.set(settings_df.loc['break_show_indvl','Values'])
            self.poke_style_menu.set(settings_df.loc['poke_style','Values'])
            self.poke_bins_menu.set(settings_df.loc['poke_bins','Values'])
            self.poke_correct_val.set(settings_df.loc['poke_show_correct','Values'])
            self.poke_error_val.set(settings_df.loc['poke_show_error','Values'])
            self.poke_left_val.set(settings_df.loc['poke_show_left','Values'])
            self.poke_right_val.set(settings_df.loc['poke_show_right','Values'])
            self.poke_biasstyle_menu.set(settings_df.loc['bias_style','Values'])
            self.poke_dynamiccolor_val.set(settings_df.loc['dynamic_color','Values'])
            self.settings_lastused_val.set(settings_df.loc['load_last_used','Values'])
            self.check_average_align()
            self.check_pellet_type()
            self.check_date_filter()

    #---SETTINGS HELPER FUNCTIONS
    def get_current_settings(self):
        settings_dict = dict(date_filter_val    =self.date_filter_val.get(),
                             date_filter_s_days =self.date_filter_s_days.get_date(),
                             date_filter_e_days =self.date_filter_e_days.get_date(),
                             date_filter_s_hour =self.date_filter_s_hour.get(),
                             date_filter_e_hour =self.date_filter_e_hour.get(),
                             img_format         =self.img_format_menu.get(),
                             shade_dark         =self.nightshade_checkbox_val.get(),
                             lights_on          =self.nightshade_lightson.get(),
                             lights_off         =self.nightshade_lightsoff.get(),
                             allgroups          =self.allgroups_val.get(),
                             abs_group          =self.abs_groups_val.get(),
                             skip_duplicates    =self.loadduplicates_checkbox_val.get(),
                             overwrite          =self.overwrite_checkbox_val.get(),
                             weirdwarn          =self.weirdfed_warning_val.get(),
                             pellet_values      =self.pelletplottype_menu.get(),
                             pellet_bins        =self.pelletplotcumu_menu.get(),
                             pellet_color       =self.pelletplotcolor_menu.get(),
                             pellet_align       =self.pelletplotalign_checkbox_val.get(),
                             average_error      =self.average_error_menu.get(),
                             average_bins       =self.average_bin_menu.get(),
                             load_last_used     =self.settings_lastused_val.get(),
                             average_method     =self.average_method_menu.get(),
                             average_align_start=self.average_alignstart_menu.get(),
                             average_align_days =self.average_aligndays_menu.get(),
                             circ_value         =self.daynight_values.get(),
                             circ_error         =self.daynight_error_menu.get(),
                             circ_show_indvl    =self.daynight_show_indvl_val.get(),
                             kde                =self.ipi_kde_val.get(),
                             logx               =self.ipi_log_val.get(),
                             norm_meals         =self.norm_meal_val.get(),
                             meal_pellet_minimum=self.meal_pelletmin_box.get(),
                             meal_duration      =self.mealdelay_box.get(),
                             retrieval_threshold=self.retrieval_threshold_menu.get(),
                             poketime_cutoff    =self.poketime_cutoff_menu.get(),
                             poke_style         =self.poke_style_menu.get(),
                             poke_bins          =self.poke_bins_menu.get(),
                             poke_show_correct  =self.poke_correct_val.get(),
                             poke_show_error    =self.poke_error_val.get(),
                             poke_show_left     =self.poke_left_val.get(),
                             poke_show_right    =self.poke_right_val.get(),
                             bias_style         =self.poke_biasstyle_menu.get(),
                             dynamic_color      =self.poke_dynamiccolor_val.get(),
                             break_style        =self.pr_style_menu.get(),
                             break_hours        =self.pr_hours_menu.get(),
                             break_mins         =self.pr_mins_menu.get(),
                             break_error        =self.pr_error_menu.get(),
                             break_show_indvl   =self.pr_show_indvl_val.get())
        return settings_dict

    def get_current_settings_as_args(self):
        settings_dict = self.get_current_settings()
        for time_setting in ['lights_on','lights_off','average_align_start']:
            settings_dict[time_setting] = self.times_to_int[settings_dict[time_setting]]
        for bin_setting in ['pellet_bins','average_bins', 'poke_bins']:
            settings_dict[bin_setting] = self.freq_bins_to_args[settings_dict[bin_setting]]
        for int_setting in ['average_align_days','break_hours','break_mins',
                            'meal_pellet_minimum','meal_duration']:
            settings_dict[int_setting] = int(settings_dict[int_setting])
        if settings_dict['retrieval_threshold'] == 'None':
            settings_dict['retrieval_threshold'] = None
        else:
            settings_dict['retrieval_threshold'] = int(settings_dict['retrieval_threshold'])
        if settings_dict['poketime_cutoff'] == 'None':
            settings_dict['poketime_cutoff'] = None
        else:
            settings_dict['poketime_cutoff'] = int(settings_dict['poketime_cutoff'])
        return settings_dict

    def convert_settingsdict_to_df(self, settings_dict):
        def get_key(value, dictionary):
            items = dictionary.items()
            for key, val in items:
                if value==val:
                    return key
        for time_setting in ['lights_on','lights_off','average_align_start']:
            settings_dict[time_setting] = get_key(settings_dict[time_setting], self.times_to_int)
        for bin_setting in ['pellet_bins','average_bins', 'poke_bins']:
            settings_dict[bin_setting] = get_key(settings_dict[bin_setting], self.freq_bins_to_args)
        if settings_dict['retrieval_threshold'] == None:
            settings_dict['retrieval_threshold'] = 'None'
        if settings_dict['poketime_cutoff'] == None:
            settings_dict['poketime_cutoff'] = 'None'
        settingsdf = pd.DataFrame.from_dict(settings_dict, orient='index',columns=['Values'])
        return settingsdf

    def settings_canvas_config(self, event):
        self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all"),)

    def get_date_filter_dates(self):
        start_date = self.date_filter_s_days.get_date()
        start_hour = self.date_filter_s_hour.get()
        start_hour = self.times_to_int[start_hour]
        start_stamp = dt.datetime.combine(start_date, dt.time(hour=start_hour))
        end_date = self.date_filter_e_days.get_date()
        end_hour = self.date_filter_e_hour.get()
        end_hour = self.times_to_int[end_hour]
        end_stamp = dt.datetime.combine(end_date, dt.time(hour=end_hour))
        return start_stamp, end_stamp

    def on_close(self):
        #save last used settings
        settingsdir = 'settings'
        last_used = 'settings/LAST_USED.csv'
        if os.path.isdir(settingsdir):
            self.save_settings(dialog=False,savepath=last_used)
        #save current session
        if os.path.isdir('sessions'):
            self.save_session(dialog=False)
        self.destroy()
        self.quit()

    #---ERROR MESSAGES
    def raise_average_warning(self):
        warn_window = tk.Toplevel(self)
        warn_window.grab_set()
        warn_window.title('Average Plot Error')
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        text = ("There are no intervals where the selected FEDs all overlap." +
                '\n\nYou can still make an average pellet plot by changing the' +
                '\nalignment method for averaging from the settings tab.')

        warning = tk.Label(warn_window, text=text, justify=tk.LEFT)
        warning.pack(padx=(20,20),pady=(20,20))

    def raise_load_errors(self,failed_names, weird_names=None):
        warn_window = tk.Toplevel(self,)
        warn_window.geometry('{}x{}'.format(600, 300))
        warn_window.grab_set()
        warn_window.title('Load Error')
        warn_window.grid_columnconfigure(0,weight=1)
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        self.warn_canvas = tk.Canvas(warn_window)
        scrollbar = ttk.Scrollbar(warn_window, orient="vertical",
                                  command=self.warn_canvas.yview)
        warn_frame = tk.Frame(self.warn_canvas)
        self.warn_canvas.configure(yscrollcommand=scrollbar.set)
        self.warn_canvas.create_window((0,0),window=warn_frame,anchor='nw')
        intro1 = ("The following files were not recognized as FED3 data, " +
                 "and weren't loaded:\n")
        body1 = ''
        for name in failed_names:
            body1 += ('\n - ' + name)
        all_text1 = intro1+body1
        warning1 = tk.Label(warn_frame, text=all_text1,
                           justify=tk.LEFT, wraplength=500)
        intro2 = ("The following files do not contain all the expected " +
                  "FED3 column names; some plots may not work or produce " +
                  "unexpected results (this warning can be toggled from " +
                  "the settings menu):\n")
        body2 = ''
        for name in weird_names:
            body2 += ('\n - ' + name)
        all_text2 = intro2+body2
        warning2 = tk.Label(warn_frame, text=all_text2,
                           justify=tk.LEFT, wraplength=500)
        if failed_names:
            warning1.grid(row=0,column=0,padx=(20,20),pady=(20,20),sticky='nsew')
        if weird_names:
            warning2.grid(row=1,column=0,padx=(20,20),pady=(20,20),sticky='nsew')
        self.warn_canvas.grid(row=0,column=0,sticky='nsew')
        scrollbar.grid(row=0,column=1,sticky='nse')
        warn_frame.bind('<Configure>', self.canvas_config)

    def canvas_config(self, event):
        self.warn_canvas.configure(scrollregion=self.warn_canvas.bbox("all"),)

    def raise_new_window_warning(self,):
        warn_window = tk.Toplevel(self)
        warn_window.grab_set()
        warn_window.title('Error: maximum new window limit reached')
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        text = ("Only 5 New Windows can be opened at one time, in order to" +
                '\nprevent memory leak.  Please close one of the open windows.')

        warning = tk.Label(warn_window, text=text, justify=tk.LEFT)
        warning.pack(padx=(20,20),pady=(20,20))

    def raise_date_filter_error(self):
        warn_window = tk.Toplevel(self)
        warn_window.grab_set()
        warn_window.title('Error: Date filter')
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        text = ("The following files did not have any data within the date filter" +
                '\nPlease edit or remove the global date filter to plot them:\n')
        for fed in self.failed_date_feds:
            text += '\n  - ' + fed.basename
        warning = tk.Label(warn_window, text=text, justify=tk.LEFT)
        warning.pack(padx=(20,20),pady=(20,20))

    def raise_fed_concat_error(self):
        warn_window = tk.Toplevel(self)
        warn_window.grab_set()
        warn_window.title('Error: cannot concatenate')
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        text = ("The selected FEDs have overlapping dates and could not be concatenated")
        warning = tk.Label(warn_window, text=text, justify=tk.LEFT)
        warning.pack(padx=(20,20),pady=(20,20))

    #---RIGHT CLICK FUNCS
    def r_raise_menu(self, event):
        widget = event.widget
        menu = None
        if widget == self.files_spreadsheet:
            if len(self.files_spreadsheet.selection()) == 1:
                menu = self.r_menu_file_single
            elif len(self.files_spreadsheet.selection()) > 1:
                menu = self.r_menu_file_multi
            else:
                menu = self.r_menu_file_empty
        elif widget == self.plot_listbox:
            if len(self.plot_listbox.curselection()) == 1:
                menu = self.r_menu_plot_single
            elif len(self.plot_listbox.curselection()) > 1:
                menu = self.r_menu_plot_multi
        if menu:
            menu.tk_popup(event.x_root, event.y_root,)
            menu.grab_release()

    def r_open_location(self,):
        selected = self.files_spreadsheet.selection()
        fed = self.LOADED_FEDS[int(selected[0])]
        dirname = os.path.dirname(fed.directory)
        try:
            os.startfile(dirname)
        except:
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener,dirname])

    def r_open_externally(self):
        selected = self.files_spreadsheet.selection()
        fed = self.LOADED_FEDS[int(selected[0])]
        try:
            os.startfile(fed.directory)
        except:
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener,fed.directory])

    def r_load_plot_settings(self):
        current_settings_dict = self.get_current_settings_as_args()
        current_settings_df = self.convert_settingsdict_to_df(current_settings_dict)
        clicked=self.plot_listbox.curselection()
        graph_name=self.plot_listbox.get(clicked)
        plot_obj = self.PLOTS[graph_name]
        plot_settings_dict = {key:val for key,val in plot_obj.arguments.items()
                              if key != 'ax'}
        plot_settings_df = self.convert_settingsdict_to_df(plot_settings_dict)
        plot_arguments = fed_inspect.get_arguments_affecting_settings(plot_obj)
        output_df = current_settings_df
        for arg in plot_arguments:
            if arg in output_df.index:
                output_df.loc[arg,'Values'] = plot_settings_df.loc[arg, 'Values']
        self.load_settings(dialog=False,from_df=output_df)

    def r_select_from_plot(self):
        clicked=self.plot_listbox.curselection()
        graph_name=self.plot_listbox.get(clicked)
        plot_obj = self.PLOTS[graph_name]
        feds_to_select = []
        if 'FED' in plot_obj.arguments:
            feds_to_select.append(plot_obj.arguments['FED'])
        elif 'FEDs' in plot_obj.arguments:
            feds_to_select += plot_obj.arguments['FEDs']
        self.files_spreadsheet.selection_remove(self.files_spreadsheet.selection())
        to_select = []
        for plot_fed in feds_to_select:
            for i,loaded_fed in enumerate(self.LOADED_FEDS):
                if plot_fed == loaded_fed:
                    to_select.append(i)
        self.files_spreadsheet.selection_set(to_select)
        self.update_buttons_home(None)
        self.tabcontrol.select(self.home_tab)

root = FED3_Viz()
root.protocol("WM_DELETE_WINDOW", root.on_close)
root.bind('<Escape>', root.escape)
root.geometry("1400x700")
if __name__=="__main__":
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.focus_force()
    root.mainloop()
plt.close('all')