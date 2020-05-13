# -*- coding: utf-8 -*-
"""
FED3 Viz: A tkinter program for visualizing FED3 Data

@author: https://github.com/earnestt1234
"""
import emoji
import matplotlib.pyplot as plt
import os
import pandas as pd
import platform
import tkinter as tk
import tkinter.filedialog
import webbrowser

from collections import OrderedDict
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from tkinter import ttk

from _version import __version__, __date__
from fed_inspect import fed_inspect
from getdata import getdata
from load.load import FED3_File
from plots import plots

class FED_Plot():
    def __init__(self, figure, frame, figname,
                 plotfunc, arguments, plotdata=None,):       
        self.figure = figure
        self.frame  = frame
        self.figname = figname
        self.arguments = arguments
        self.plotfunc = plotfunc
        self.plotdata = plotdata
        self.fednames = []
        self.width  = int(self.figure.get_size_inches()[0] *self.figure.dpi)
        self.height = int(self.figure.get_size_inches()[1] *self.figure.dpi)

class FED3_Viz(tk.Tk):
    def __init__(self):
        super(FED3_Viz, self).__init__()
        self.title('FED3 Viz')
        if not platform.system() == 'Darwin': 
            self.iconbitmap('img/fedviz_logo.ico')
        self.LOADED_FEDS = []
        self.PLOTS = OrderedDict()
        self.GROUPS = []
        self.mac_color = '#E2E2E2'
        self.colors =  ['blue','red','green','yellow','purple','orange',
                        'black',]
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
        
    #---SETUP TABS
        self.tabcontrol = ttk.Notebook(self)
        self.home_tab   = tk.Frame(self.tabcontrol)
        self.plot_tab   = tk.Frame(self.tabcontrol)
        self.settings_tab = tk.Frame(self.tabcontrol)
        self.about_tab = tk.Frame(self.tabcontrol)
        self.tabcontrol.add(self.home_tab, text='Home')
        self.tabcontrol.add(self.plot_tab, text='Plots')
        self.tabcontrol.add(self.settings_tab, text='Settings')
        self.tabcontrol.add(self.about_tab, text='About')
        self.tabcontrol.pack(expan = 1, fill='both')
        self.home_tab.rowconfigure(3,weight=1)
        self.home_tab.columnconfigure(0,weight=1)

    #---INIT WIDGETS FOR HOME TAB
        #organization frames
        self.fed_text     = tk.Frame(self.home_tab, width=400, height=30)
        self.fed_buttons  = tk.Frame(self.home_tab)
        self.home_sheets = tk.Frame(self.home_tab)
        self.plot_buttons = tk.Frame(self.home_tab)
        self.plot_selector = tk.Frame(self.home_tab)
        
        self.fed_text.grid(row=1,column=0,sticky='w',padx=(10,0))
        self.fed_buttons.grid(row=2,column=0, sticky='ews') 
        self.home_sheets.grid(row=3,column=0,sticky='nsew',columnspan=2)
        self.home_sheets.rowconfigure(0,weight=1)
        self.home_sheets.columnconfigure(0,weight=1)
        self.plot_selector.grid(row=3, column=3, sticky='nsew', padx=(20,0),
                                columnspan=2)
        self.plot_selector.rowconfigure(0,weight=1)
        
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
        self.files_spreadsheet.bind('<Control-a>',self.select_all_FEDs)
        self.files_spreadsheet.bind('<Control-A>',self.select_all_FEDs)
        self.files_scrollbar = ttk.Scrollbar(self.home_sheets, command=self.files_spreadsheet.yview,)
        self.files_spreadsheet.configure(yscrollcommand=self.files_scrollbar.set)
        self.group_view = tk.Listbox(self.home_sheets,selectmode=tk.EXTENDED,
                                     activestyle=tk.NONE, height=5)
        self.group_view.bind('<ButtonRelease-1>', self.select_group)
        self.group_scrollbar = ttk.Scrollbar(self.home_sheets, command=self.group_view.yview)
        self.group_view.configure(yscrollcommand=self.group_scrollbar.set)
        
        #plot selector:
        self.plot_treeview = ttk.Treeview(self.plot_selector, selectmode = 'browse',)
        self.plot_treeview.heading('#0', text='Plots')
        self.ps_pellet = self.plot_treeview.insert("", 1, text='Pellets')
        self.plot_treeview.insert(self.ps_pellet, 1, text='Single Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 2, text='Multi Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 3, text='Average Pellet Plot')
        self.plot_treeview.insert(self.ps_pellet, 4, text='Interpellet Interval')
        self.plot_treeview.insert(self.ps_pellet, 5, text='Group Interpellet Interval')
        self.ps_poke = self.plot_treeview.insert("", 2, text='Pokes')
        self.plot_treeview.insert(self.ps_poke, 1, text='Single Poke Plot')
        self.plot_treeview.insert(self.ps_poke, 2, text='Average Poke Plot (Correct)')
        self.plot_treeview.insert(self.ps_poke, 3, text='Average Poke Plot (Error)')
        self.plot_treeview.insert(self.ps_poke, 4, text='Poke Bias Plot')
        self.plot_treeview.insert(self.ps_poke, 5, text='Average Poke Bias Plot')
        self.ps_circadian = self.plot_treeview.insert("", 3, text='Circadian')
        self.plot_treeview.insert(self.ps_circadian, 1, text='Day/Night Plot')
        self.plot_treeview.insert(self.ps_circadian, 2, text='Chronogram (Line)')
        self.plot_treeview.insert(self.ps_circadian, 3, text='Chronogram (Heatmap)')
        self.ps_other = self.plot_treeview.insert("", 4, text='Other')
        self.plot_treeview.insert(self.ps_other, 1, text='Diagnostic Plot')
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
        self.button_load   = tk.Button(self.fed_buttons, text='Load',
                                       command=lambda: 
                                       self.load_FEDs(overwrite=False,
                                                      skip_duplicates=self.loadduplicates_checkbox_val.get()),
                                       width=8)
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
        self.button_save_groups        = tk.Button(self.fed_buttons, text='Save Groups',
                                                   command=lambda: self.save_groups(),
                                                   state=tk.DISABLED)
        self.button_load_groups        = tk.Button(self.fed_buttons, text='Load Groups',
                                                   command=lambda: self.load_groups(),
                                                   state=tk.DISABLED)
        self.button_create_plot        = tk.Button(self.plot_selector, text='Create Plot',
                                                   command=self.init_plot,
                                                   state=tk.DISABLED, height=2,
                                                   font='Segoe 10 bold')
        

    #---HOVER TEXT DICTIONARY          
        #dictionary mapping widgets to hover text
        self.hover_text_one_dict = {self.button_load : 'Load FED3 files',
                                    self.button_delete: 'Unload highlighted FED3 files',
                                    self.button_create_group:
                                        'Add selected devices to a group',
                                    self.button_delete_group:
                                        'Delete selected group',
                                    self.button_save_groups:
                                        'Save the current group labels for the loaded devices',
                                    self.button_load_groups:
                                        'Load group labels from a saved groups file',}
        for button in self.hover_text_one_dict.keys():
            button.bind('<Enter>', self.hover_text_one)
            button.bind('<Leave>', self.clear_hover_text_one)
     
    #---PLOT TREEVIEW > HELP TEXT
        #associate each plot_treeview entry with helptext
        self.plot_nodes_help = {'Single Pellet Plot':'Plot pellets received for one device',
                                'Multi Pellet Plot':'Plot pellets received for multiple devices (no averaging)',
                                'Average Pellet Plot':'Plot average pellets received for grouped devices (groups make individual curves)',
                                'Interpellet Interval':'Plot histogram of intervals between pellet retrievals',
                                'Group Interpellet Interval':'Plot histogram of intervals between pellet retrievals for groups',
                                'Single Poke Plot':'Plot the amount of correct or incorrect pokes',
                                'Average Poke Plot (Correct)':'Plot average correct pokes for grouped devices (groups make individual curves)',
                                'Average Poke Plot (Error)':'Plot average error pokes for grouped devices (groups make individual curves)',
                                'Poke Bias Plot':'Plot the tendency to pick one poke over another',
                                'Average Poke Bias Plot':'Plot the average group tendency to pick one poke over another (groups make individual curves)',
                                'Day/Night Plot':'Plot group averages for day/night on a bar chart',
                                'Diagnostic Plot':'Plot battery life and motor turns',
                                'Chronogram (Line)':'Plot average 24-hour curves for groups',
                                'Chronogram (Heatmap)':'Make a 24-hour heatmap with individual devices as rows'}
            
    #---PLOT TREEVIEW > PLOT FUNCTION
        #associate each plot_treeview entry with a plotting function
        self.plot_nodes_func = {'Single Pellet Plot':self.pellet_plot_single_TK,
                                'Multi Pellet Plot':self.pellet_plot_multi_TK,
                                'Average Pellet Plot':self.avg_plot_TK,
                                'Interpellet Interval':self.interpellet_plot_TK,
                                'Group Interpellet Interval':self.group_ipi_TK,
                                'Day/Night Plot':self.daynight_plot_TK,
                                'Diagnostic Plot':self.diagnostic_plot_TK,
                                'Single Poke Plot':self.poke_plot_single_TK,
                                'Average Poke Plot (Correct)':self.avg_plot_TK,
                                'Average Poke Plot (Error)':self.avg_plot_TK,
                                'Poke Bias Plot':self.poke_bias_single_TK,
                                'Average Poke Bias Plot':self.avg_plot_TK,
                                'Chronogram (Line)':self.chronogram_line_TK,
                                'Chronogram (Heatmap)':self.chronogram_heatmap_TK}   
               
    #---PLACE WIDGETS FOR HOME TAB     
        #fed_buttons/group buttons
        self.button_load.grid(row=0,column=0,sticky='sew')
        self.button_delete.grid(row=0,column=1,sticky='nsew')
        self.button_create_group.grid(row=0,column=2,sticky='sew')
        self.button_delete_group.grid(row=0,column=3,sticky='sew')
        self.button_save_groups.grid(row=0,column=4,sticky='sew')
        self.button_load_groups.grid(row=0,column=5,sticky='sew')
        
        #labels
        self.home_buttons_help.grid(row=0,column=0,sticky='nsw',padx=(0,20),
                                    pady=(20))  
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
        self.settings_col1 = tk.Frame(self.settings_tab)
        self.settings_col2 = tk.Frame(self.settings_tab)
        self.settings_col1.grid(row=0,column=0, sticky='nw', padx=(5,0))
        self.settings_col2.grid(row=0,column=1, sticky='nw')
        
        self.general_settings_frame = tk.Frame(self.settings_col1)
        self.general_settings_frame.grid(row=0,column=0, sticky='nsew')
        
        self.pellet_settings_frame = tk.Frame(self.settings_col1)
        self.pellet_settings_frame.grid(row=2,column=0, sticky='nsew')
        
        self.average_settings_frame = tk.Frame(self.settings_col1)
        self.average_settings_frame.grid(row=1,column=0,sticky='nsew',)
        
        self.ipi_settings_frame = tk.Frame(self.settings_col2)
        self.ipi_settings_frame.grid(row=0,column=0, sticky='nsew',
                                     padx=20, pady=(0,20))
        
        self.poke_settings_frame = tk.Frame(self.settings_col2)
        self.poke_settings_frame.grid(row=1,column=0,sticky='nsew',padx=(20))
        
        self.daynight_settings_frame = tk.Frame(self.settings_col2)
        self.daynight_settings_frame.grid(row=2,column=0,sticky='nsew',
                                          padx=(20,20), pady=(20,0))
        
        self.load_settings_frame = tk.Frame(self.settings_col2)
        self.load_settings_frame.grid(row=3,column=0,sticky='nsew', 
                                      padx=(20,20))
        
        #labels
        self.section_font = 'Segoe 10 bold'
        if platform.system() == 'Darwin':
            self.section_font = 'Segoe 14 bold'
        self.general_settings_label = tk.Label(self.general_settings_frame,
                                               text='General',
                                               font=self.section_font)        
        self.pellet_settings_label   = tk.Label(self.pellet_settings_frame,
                                                text='Individual Pellet Plots',
                                                font=self.section_font)
        self.pelletplottype_label    = tk.Label(self.pellet_settings_frame,
                                                text='Values to plot')
        self.pelletplotcumu_label    = tk.Label(self.pellet_settings_frame,
                                                text='Bin size of pellet frequency (hours)',
                                                fg='gray')
        self.pelletplotcolor_label   = tk.Label(self.pellet_settings_frame,
                                                text='Default color (single pellet plots)')
        
        self.average_settings_label  = tk.Label(self.average_settings_frame,
                                                text='Averaging (Pellet & Poke Plots)',
                                                font=self.section_font)
        self.average_error_label     = tk.Label(self.average_settings_frame,
                                                text='Error value for average plots')
        self.average_bin_label       = tk.Label(self.average_settings_frame,
                                                text='Bin size for averaging (hours)')
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
        self.poke_settings_label = tk.Label(self.poke_settings_frame,
                                            text='Individual Poke Plots',
                                            font=self.section_font)
        self.poke_style_label = tk.Label(self.poke_settings_frame,
                                         text='Values to plot')
        self.poke_binsize_label  = tk.Label(self.poke_settings_frame,
                                            text='Bin size for poke plots (hours)')
        self.poke_biasstyle_label = tk.Label(self.poke_settings_frame,
                                             text='Comparison for poke bias plots')
        self.load_settings_label = tk.Label(self.load_settings_frame,
                                              text='Save/Load Settings',
                                              font=self.section_font)
        lse_text = 'Save the current settings for future use.'
        self.load_settings_explan = tk.Label(self.load_settings_frame,
                                             text=lse_text)
                                              
        #dropdowns/checkboxes
        #   general
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
        self.loadduplicates_checkbox_val = tk.BooleanVar()
        self.loadduplicates_checkbox_val.set(True)
        self.loadduplicates_checkbox = ttk.Checkbutton(self.general_settings_frame,
                                                      text='Don\'t load a FED if its filename is already loaded',
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
        #   average
        self.average_error_menu = ttk.Combobox(self.average_settings_frame,
                                               values=['SEM','STD','raw data','None'],
                                               width=10)
        self.average_error_menu.set('SEM')
        
        self.average_bin_menu = ttk.Combobox(self.average_settings_frame,
                                             values=list(range(1,25)),
                                             width=10)
        self.average_bin_menu.set(1)
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
                                                values=list(range(1,49)),
                                                state=tk.DISABLED)
        self.pelletplotcumu_menu.set(1)
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
        self.daynight_show_indvl_val.set(True)
        self.daynight_show_indvl = ttk.Checkbutton(self.daynight_settings_frame,
                                                  text='Show individual FED data points',
                                                  var=self.daynight_show_indvl_val)
        #   ipi
        self.ipi_kde_val = tk.BooleanVar()
        self.ipi_kde_val.set(True)
        self.ipi_kde_checkbox = ttk.Checkbutton(self.ipi_settings_frame,
                                                text='Use kernel density estimation',
                                                var=self.ipi_kde_val)
        #   poke
        self.poke_style_menu = ttk.Combobox(self.poke_settings_frame,
                                            values=['Cumulative','Frequency','Percentage'])
        self.poke_style_menu.set('Cumulative')
        self.poke_bins_menu = ttk.Combobox(self.poke_settings_frame,
                                           values=list(range(1,25)),
                                           width=10)
        self.poke_bins_menu.set(1)     
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
        self.poke_dynamiccolor_val = tk.BooleanVar()
        self.poke_dynamiccolor_val.set(True)
        self.poke_dynamiccolor_box = ttk.Checkbutton(self.poke_settings_frame,
                                                     text='Use dynamic color for bias plots',
                                                     var=self.poke_dynamiccolor_val)
        self.poke_biasstyle_menu = ttk.Combobox(self.poke_settings_frame,
                                                values=['correct - error','left - right'],)
        self.poke_biasstyle_menu.set('correct - error')
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
        self.nightshade_checkbox.grid(row=1,column=0,padx=(20,160),sticky='w')
        self.nightshade_lightson.grid(row=1,column=1,sticky='w')
        self.nightshade_lightsoff.grid(row=1,column=2,sticky='w')
        self.allgroups.grid(row=2,column=0,padx=(20,0),sticky='w')
        self.loadduplicates_checkbox.grid(row=3,column=0,padx=(20,0),sticky='w')
        self.overwrite_checkbox.grid(row=4,column=0,padx=(20,0),sticky='w')
        self.weirdfed_warning.grid(row=5,column=0,padx=(20,0),sticky='w')
        
        self.average_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))
        self.average_error_label.grid(row=1,column=0,padx=(20,215),sticky='w')
        self.average_error_menu.grid(row=1,column=1,sticky='nw')
        self.average_bin_label.grid(row=2,column=0,sticky='w', padx=(20,0))
        self.average_bin_menu.grid(row=2,column=1,sticky='w')
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
        
        self.poke_settings_label.grid(row=0,column=0,sticky='w')
        self.poke_style_label.grid(row=1,column=0,sticky='w',padx=(20,0))
        self.poke_style_menu.grid(row=1,column=1,sticky='ew',)
        self.poke_binsize_label.grid(row=2,column=0,sticky='w', padx=(20,95))
        self.poke_bins_menu.grid(row=2,column=1,sticky='w')
        self.poke_correct_box.grid(row=3,column=0,sticky='w',padx=(20))
        self.poke_error_box.grid(row=4,column=0,sticky='w',padx=20)
        self.poke_biasstyle_label.grid(row=5,column=0,sticky='w',padx=20,pady=(10,0))
        self.poke_biasstyle_menu.grid(row=5,column=1,sticky='w', pady=(10,0))
        self.poke_dynamiccolor_box.grid(row=6,column=0,sticky='w',padx=20)
        
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
        self.caveat.grid(row=1, column=0, pady=40, columnspan=2)
        
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
            self.plot_listbox.config(width=20)
            self.w_offset = 350
            self.h_offset = 100
            for widget in [self.home_tab, self.plot_tab,
                            self.settings_tab, self.about_tab]:
                config_color_mac(widget)
    #---HOME TAB BUTTON FUNCTIONS
    def load_FEDs(self, overwrite=True, skip_duplicates=True):
        file_types = [('All', '*.*'),
                      ('Comma-Separated Values', '*.csv'),
                      ('Excel', '*.xls, *.xslx'),]
        files = tk.filedialog.askopenfilenames(title='Select FED3 Data',
                                               filetypes=file_types)
        loaded_filenames = [fed.basename for fed in self.LOADED_FEDS]
        pass_FEDs = []
        failed_FEDs = []
        weird_FEDs = []
        if files:
            self.home_buttons_help.configure(text='')
            self.progressbar.grid(row=0,column=0,sticky='ew',padx=(0,20),pady=(12))
            self.progressbar.lift()
            self.progresstext.grid(row=0,column=1,sticky='nsw')
            if overwrite:
                self.LOADED_FEDS = []
            for file in files:
                if skip_duplicates:
                    file_name = os.path.basename(file)
                    if file_name not in loaded_filenames:
                        try:
                            pass_FEDs.append(FED3_File(file))
                        except:
                            failed_FEDs.append(file_name[0]+file_name[1])                     
                else:
                    try:
                        pass_FEDs.append(FED3_File(file))
                    except:
                        failed_FEDs.append(file_name[0]+file_name[1])
                self.progresstextvar.set(os.path.basename(file) + '...')
                self.progressbar.step(1/len(files)*100)
                self.update()
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
        
    def save_groups(self):
        group_dict = {fed.basename : fed.group for fed in self.LOADED_FEDS
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
                filename = fed.basename
                if filename in df.columns:
                    fed.group = []
                    for grp in df[filename]:
                        if not pd.isna(grp):
                            fed.group.append(str(grp))
        self.update_file_view()
        self.update_group_view()
    
    def init_plot(self):
        selection = self.plot_treeview.selection()
        text = self.plot_treeview.item(selection,'text')
        if text in self.plot_nodes_func:
            self.plot_nodes_func[text]()
    
    def pellet_plot_single_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            arg_dict = self.get_current_settings_as_args()
            arg_dict['FED'] = obj
            new_plot_frame = ttk.Frame(self.plot_container)
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
            fig = plotfunc(**arg_dict)
            new_plot = FED_Plot(frame=new_plot_frame,figure=fig,
                                figname=fig_name, plotfunc=plotfunc,
                                plotdata=plotdata, arguments=arg_dict,)
            self.PLOTS[fig_name] = new_plot
            self.draw_figure(new_plot)
            self.raise_figure(fig_name)
            self.update()
            
    def pellet_plot_multi_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        fig_name = self.create_plot_name('Multi-FED Pellet Plot')
        new_plot_frame = ttk.Frame(self.plot_container)
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
        figure = plotfunc(**arg_dict)
        new_plot = FED_Plot(frame=new_plot_frame, figure=figure,
                            figname=fig_name, plotfunc=plotfunc, 
                            arguments=arg_dict, plotdata=plotdata)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
           
    def avg_plot_TK(self):
        args_dict = self.get_current_settings_as_args()
        args_dict['FEDs'] = self.LOADED_FEDS
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        selection = self.plot_treeview.selection()
        text = self.plot_treeview.item(selection,'text')
        choices = {'Average Pellet Plot':'pellets',
                   'Average Poke Plot (Correct)':'correct pokes',
                   'Average Poke Plot (Error)':'errors',
                   'Average Poke Bias Plot':'poke bias (correct - error)'}
        args_dict['dependent'] = choices[text]
        method = self.average_method_menu.get()
        if method == 'shared time':
            plotfunc=plots.average_plot_ontime
            plotdata=getdata.average_plot_ontime(**args_dict)
        elif method == 'shared date & time':
            plotfunc=plots.average_plot_ondatetime
            plotdata=getdata.average_plot_ondatetime(**args_dict)
        elif method == 'elapsed time':
            plotfunc=plots.average_plot_onstart
            plotdata=getdata.average_plot_onstart
        fig = plotfunc(**args_dict)
        if fig == 'NO_OVERLAP ERROR':
            self.raise_average_warning()
            return
        fig_name = self.create_plot_name('Average Plot of ' + args_dict['dependent'].capitalize())
        new_plot_frame = ttk.Frame(self.plot_container)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,
                            figname=fig_name, plotfunc=plotfunc,
                            plotdata=plotdata,arguments=args_dict)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
       
    def interpellet_plot_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        basename = 'Inter-pellet Interval Plot'
        fig_name = self.create_plot_name(basename)
        new_plot_frame = ttk.Frame(self.plot_container)
        fig = plots.interpellet_interval_plot(**arg_dict)
        plotdata = getdata.interpellet_interval_plot(**arg_dict)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,figname=fig_name,
                            plotfunc=plots.interpellet_interval_plot,
                            plotdata=plotdata,arguments=arg_dict,)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)

    def group_ipi_TK(self):
        args_dict = self.get_current_settings_as_args()
        args_dict['FEDs'] = self.LOADED_FEDS
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        fig = plots.group_interpellet_interval_plot(**args_dict)
        plotdata = getdata.group_interpellet_interval_plot(**args_dict)
        fig_name = self.create_plot_name('Group Interpellet Interval Plot')
        new_plot_frame = ttk.Frame(self.plot_container)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,
                            figname=fig_name, plotfunc=plots.group_interpellet_interval_plot,
                            arguments=args_dict, plotdata=plotdata,)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)

    def diagnostic_plot_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for FED in FEDs_to_plot:
            arg_dict = self.get_current_settings_as_args()
            arg_dict['FED'] = FED
            basename = 'Diagnostic Plot for ' + FED.filename
            fig_name = self.create_plot_name(basename)
            new_plot_frame = ttk.Frame(self.plot_container)
            fig = plots.diagnostic_plot(**arg_dict)
            plotdata = getdata.diagnostic_plot(**arg_dict)
            new_plot = FED_Plot(figure=fig, frame=new_plot_frame,figname=fig_name,
                                plotfunc=plots.diagnostic_plot,
                                plotdata=plotdata, arguments=arg_dict,)
            self.PLOTS[fig_name] = new_plot
            self.draw_figure(new_plot)
            self.raise_figure(fig_name)
            self.update()
        
    def daynight_plot_TK(self):
        args_dict = self.get_current_settings_as_args()
        args_dict['FEDs'] = self.LOADED_FEDS
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        fig = plots.daynight_plot(**args_dict)
        plotdata = getdata.daynight_plot(**args_dict)
        value = args_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Day Night Plot')
        new_plot_frame = ttk.Frame(self.plot_container)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,
                            figname=fig_name, plotfunc=plots.daynight_plot,
                            arguments=args_dict, plotdata=plotdata,)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
    
    def chronogram_line_TK(self):
        args_dict = self.get_current_settings_as_args()
        args_dict['FEDs'] = self.LOADED_FEDS
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        fig = plots.line_chronogram(**args_dict)
        plotdata = getdata.line_chronogram(**args_dict)
        value = args_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Chronogram (Line)')
        new_plot_frame = ttk.Frame(self.plot_container)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,
                            figname=fig_name, plotfunc=plots.line_chronogram,
                            arguments=args_dict, plotdata=plotdata,)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
    
    def chronogram_heatmap_TK(self):
        arg_dict = self.get_current_settings_as_args()
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        arg_dict['FEDs'] = FEDs_to_plot
        value = arg_dict['circ_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Chronogram (Heatmap)')
        new_plot_frame = ttk.Frame(self.plot_container)
        figure = plots.heatmap_chronogram(**arg_dict)
        plotdata = getdata.heatmap_chronogram(**arg_dict)
        new_plot = FED_Plot(frame=new_plot_frame, figure=figure,
                            figname=fig_name, plotfunc=plots.heatmap_chronogram, 
                            arguments=arg_dict, plotdata=plotdata)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
    
    def poke_plot_single_TK(self):
        to_plot = [int(i) for i in self.files_spreadsheet.selection()]
        FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
        for obj in FEDs_to_plot:
            arg_dict = self.get_current_settings_as_args()
            arg_dict['FED'] = obj
            new_plot_frame = ttk.Frame(self.plot_container)
            fig_name = self.create_plot_name('Poke plot for ' + obj.filename)
            fig = plots.poke_plot(**arg_dict)
            new_plot = FED_Plot(frame=new_plot_frame,figure=fig,
                                figname=fig_name, plotfunc=plots.poke_plot,
                                plotdata=getdata.poke_plot(**arg_dict), arguments=arg_dict,)
            self.PLOTS[fig_name] = new_plot
            self.draw_figure(new_plot)
            self.raise_figure(fig_name)
            self.update()
    
    def poke_bias_single_TK(self):
            to_plot = [int(i) for i in self.files_spreadsheet.selection()]
            FEDs_to_plot = [self.LOADED_FEDS[i] for i in to_plot]
            for obj in FEDs_to_plot:
                arg_dict = self.get_current_settings_as_args()
                arg_dict['FED'] = obj
                new_plot_frame = ttk.Frame(self.plot_container)
                fig_name = self.create_plot_name('Poke bias plot for ' + obj.filename)
                fig = plots.poke_bias(**arg_dict)
                new_plot = FED_Plot(frame=new_plot_frame,figure=fig,
                                    figname=fig_name, plotfunc=plots.poke_bias,
                                    plotdata=getdata.poke_bias(**arg_dict), 
                                    arguments=arg_dict,)
                self.PLOTS[fig_name] = new_plot
                self.draw_figure(new_plot)
                self.raise_figure(fig_name)
                self.update()
        
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
  
    def hover_text_one(self, event):
        widget = event.widget
        self.home_buttons_help.configure(text=self.hover_text_one_dict[widget])
        
    def clear_hover_text_one(self, event):
        self.show_plot_help()
    
    def show_plot_help(self, *event):
        selection = self.plot_treeview.selection()
        text = self.plot_treeview.item(selection,'text')
        if text in self.plot_nodes_help:
            self.home_buttons_help.configure(text=self.plot_nodes_help[text])
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
            
    def update_buttons_home(self,*event):
        #start with the create plot button
        selection = self.plot_treeview.selection()
        text = self.plot_treeview.item(selection,'text')
        if text in ['Single Pellet Plot', 'Multi Pellet Plot', 'Diagnostic Plot',
                    'Interpellet Interval', 'Poke Bias Plot',
                    'Chronogram (Heatmap)']:
            #if there are feds selected
            if self.files_spreadsheet.selection():
                self.button_create_plot.configure(state=tk.NORMAL)
            else:
                self.button_create_plot.configure(state=tk.DISABLED)
        elif text == 'Single Poke Plot':
            if self.files_spreadsheet.selection():
                if self.poke_correct_val.get() or self.poke_error_val.get():
                    self.button_create_plot.configure(state=tk.NORMAL)
            else:
                self.button_create_plot.configure(state=tk.DISABLED)
        elif text in ['Average Pellet Plot', 'Day/Night Plot', 'Chronogram (Line)',
                      'Average Poke Plot (Correct)','Average Poke Plot (Error)',
                      'Average Poke Bias Plot', 'Group Interpellet Interval']:
            #if the all groups box is checked
            if self.allgroups_val.get():
                #if there are any groups
                if self.GROUPS:
                    self.button_create_plot.configure(state=tk.NORMAL)
                else:
                    self.button_create_plot.configure(state=tk.DISABLED)
            else:
                #if there are groups selected
                if self.group_view.curselection():
                    self.button_create_plot.configure(state=tk.NORMAL)
                else:
                    self.button_create_plot.configure(state=tk.DISABLED)
        else:
            self.button_create_plot.configure(state=tk.DISABLED)
        #if there are feds selected
        if self.files_spreadsheet.selection():
            self.button_delete.configure(state=tk.NORMAL)
            self.button_create_group.configure(state=tk.NORMAL)
        else:
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
        
    #---PLOT TAB BUTTON FUNCTIONS
    def rename_plot(self):
        clicked = self.plot_listbox.curselection()[0]
        self.old_name = self.plot_listbox.get(clicked)
        self.rename_window = tk.Toplevel(self)
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
         
    def delete_plot(self):
        clicked=sorted(list(self.plot_listbox.curselection()), reverse=True)
        for i in clicked:
            selection=self.plot_listbox.get(i)
            self.plot_listbox.delete(i)
            self.PLOTS[selection].frame.destroy()
            del(self.PLOTS[selection])
            new_plot_index=self.plot_listbox.size()-1
            if new_plot_index>=0:
                new_plot=self.plot_listbox.get(new_plot_index)
                self.raise_figure(new_plot)
        self.update_buttons_plot(None)
                
    def new_window_plot(self):
        clicked=self.plot_listbox.curselection()
        for i in clicked:
            graph_name=self.plot_listbox.get(i)
            self.draw_figure(self.PLOTS[graph_name], pop_window=True)
            
    def save_plots(self):
        clicked=self.plot_listbox.curselection()
        if clicked:
            savepath = tk.filedialog.askdirectory(title='Select where to save highlighted plots')
            if savepath:
                for i in clicked:
                    graph_name=self.plot_listbox.get(i)
                    fig = self.PLOTS[graph_name].figure
                    save_name = graph_name+'.png'
                    full_save = os.path.join(savepath,save_name)
                    if not self.overwrite_checkbox_val.get():
                        c=1
                        while os.path.exists(full_save):
                            save_name = graph_name +  ' (' + str(c) + ').png'
                            full_save = os.path.join(savepath,save_name)
                            c+=1
                    fig.savefig(full_save, dpi=300)
                    
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
                                    command=lambda: self.save_code(plotname, code))
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
                                         plots.group_interpellet_interval_plot]:
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
    def draw_figure(self, plot_obj, pop_window=False):
        frame = plot_obj.frame
        if pop_window:
            frame = tk.Toplevel(self)
            frame.title(plot_obj.figname)
            if not platform.system() == 'Darwin': 
                frame.iconbitmap('img/graph_icon.ico')        
        canvas = FigureCanvasTkAgg(plot_obj.figure, master=frame)
        canvas.draw_idle()
        canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
        if not pop_window:
            self.plot_listbox.insert(tk.END,plot_obj.figname)
                
    def raise_figure(self, fig_name):
        frame = self.PLOTS[fig_name].frame
        for graph in self.PLOTS:
            if graph != fig_name:
                self.PLOTS[graph].frame.grid_remove()
        self.tabcontrol.select(self.plot_tab)
        width = str(self.PLOTS[fig_name].width + self.w_offset)
        height = str(self.PLOTS[fig_name].height + self.h_offset)
        self.geometry(width+'x'+height)
        frame.grid()
        frame.tkraise()
        fig_index = list(self.PLOTS).index(fig_name)
        self.plot_listbox.selection_clear(0,self.plot_listbox.size())
        self.plot_listbox.selection_set(fig_index)
        self.update_all_buttons()
        
    def raise_figure_from_listbox(self, event):
        clicked=self.plot_listbox.curselection()
        if len(clicked) == 1:
            selection=self.plot_listbox.get(clicked[0])
            self.raise_figure(selection)

    def create_plot_name(self, basename):
        fig_name = basename
        c=1
        while fig_name in self.PLOTS.keys():
            fig_name = basename + ' ' + str(c)
            c+=1
        return fig_name
    
    def create_file_name(self, savepath, savename, ext, overwrite=False):
        file_name = savename + ext
        full_save = os.path.join(savepath, file_name)
        if not overwrite:
            c=1
            while os.path.exists(full_save):
                file_name = savename + ' (' + str(c) + ')' + ext
                full_save = os.path.join(savepath,file_name)
        return full_save
             
    def update_buttons_plot(self,*event):
        if self.plot_listbox.curselection():
            self.plot_delete.configure(state=tk.NORMAL)
            self.plot_popout.configure(state=tk.NORMAL)
            self.plot_save.configure(state=tk.NORMAL)
            self.plot_data.configure(state=tk.NORMAL)
            self.plot_inspect.configure(state=tk.NORMAL)
            if len(self.plot_listbox.curselection()) == 1:
                self.plot_rename.configure(state=tk.NORMAL)              
            else:
                self.plot_rename.configure(state=tk.DISABLED)                
        else:
            self.plot_rename.configure(state=tk.DISABLED)
            self.plot_delete.configure(state=tk.DISABLED)
            self.plot_popout.configure(state=tk.DISABLED)
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
            
    def load_settings(self, dialog=True, settings_file=['']):
        if dialog:
            settings_file = tk.filedialog.askopenfilenames(title='Select FED3 Data',
                                                           defaultextension='.csv',
                                                           filetypes=[('Comma-Separated Values', '*.csv')],
                                                           initialdir='settings')
        if settings_file:
            settings_df = pd.read_csv(settings_file[0],index_col=0)
            self.nightshade_checkbox_val.set(settings_df.loc['shade_dark','Values'])
            self.nightshade_lightson.set(settings_df.loc['lights_on','Values'])
            self.nightshade_lightsoff.set(settings_df.loc['lights_off','Values'])
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
            self.settings_lastused_val.set(settings_df.loc['load_last_used','Values'])
            self.ipi_kde_val.set(settings_df.loc['kde','Values'])
            self.poke_style_menu.set(settings_df.loc['poke_style','Values'])
            self.poke_bins_menu.set(settings_df.loc['poke_bins','Values'])
            self.poke_correct_val.set(settings_df.loc['poke_show_correct','Values'])
            self.poke_error_val.set(settings_df.loc['poke_show_error','Values'])
            self.poke_biasstyle_menu.set(settings_df.loc['bias_style','Values'])
            self.poke_dynamiccolor_val.set(settings_df.loc['dynamic_color','Values'])
            self.check_average_align()
            self.check_pellet_type()
                
    def save_last_used(self):
        settingsdir = 'settings'
        last_used = 'settings/LAST_USED.csv'
        if os.path.isdir(settingsdir):
            self.save_settings(dialog=False,savepath=last_used)
        self.destroy()
 
    #---SETTINGS HELPER FUNCTIONS
    def get_current_settings(self):
        settings_dict = dict(shade_dark         =self.nightshade_checkbox_val.get(),
                             lights_on          =self.nightshade_lightson.get(),
                             lights_off         =self.nightshade_lightsoff.get(),
                             allgroups          =self.allgroups_val.get(),
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
                             poke_style         =self.poke_style_menu.get(),
                             poke_bins          =self.poke_bins_menu.get(),
                             poke_show_correct  =self.poke_correct_val.get(),
                             poke_show_error    =self.poke_error_val.get(),
                             bias_style         =self.poke_biasstyle_menu.get(),
                             dynamic_color      =self.poke_dynamiccolor_val.get())
        return settings_dict
    
    def get_current_settings_as_args(self):
        settings_dict = self.get_current_settings()
        for time_setting in ['lights_on','lights_off','average_align_start']:
            settings_dict[time_setting] = self.times_to_int[settings_dict[time_setting]]
        for bin_setting in ['pellet_bins','average_bins', 'poke_bins']:
            settings_dict[bin_setting] += 'H' 
        for int_setting in ['average_align_days']:
            settings_dict[int_setting] = int(settings_dict[int_setting])
        return settings_dict
    
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
        warn_window = tk.Toplevel(self)
        warn_window.grab_set()
        warn_window.title('Load Error')
        if not platform.system() == 'Darwin':
            warn_window.iconbitmap('img/exclam.ico')
        intro1 = ("The following files were not recognized as FED3 data, " +
                 "and weren't loaded:\n")
        body1 = ''
        for name in failed_names:
            body1 += ('\n - ' + name)
        # outro1 = """\n\nPlease see the documentation to resolve this issue"""
        all_text1 = intro1+body1
        warning1 = tk.Label(warn_window, text=all_text1,
                           justify=tk.LEFT, wraplength=500)
        intro2 = ("The following files do not contain all the expected " +
                  "FED3 column names; some plots may not work or produce " +
                  "unexpected results (this warning can be toggled from " + 
                  "the settings menu):\n")
        body2 = ''
        for name in weird_names:
            body2 += ('\n - ' + name)
        all_text2 = intro2+body2
        warning2 = tk.Label(warn_window, text=all_text2,
                           justify=tk.LEFT, wraplength=500)
        if failed_names:
            warning1.grid(row=0,column=0,padx=(20,20),pady=(20,20),sticky='nsew')
        if weird_names:
            warning2.grid(row=1,column=0,padx=(20,20),pady=(20,20),sticky='nsew')
            
root = FED3_Viz()
root.protocol("WM_DELETE_WINDOW", root.save_last_used)
root.bind('<Escape>', root.update_all_buttons)
root.minsize(1050,20)
if __name__=="__main__":
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.mainloop()
plt.close('all')