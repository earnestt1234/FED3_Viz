# -*- coding: utf-8 -*-
"""
FED3 Viz: A tkinter program for visualizing FED3 Data

@author: https://github.com/earnestt1234
"""
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
        
        self.fed_text.grid(row=1,column=0,sticky='w',padx=(10,0))
        self.fed_buttons.grid(row=2,column=0, sticky='ews') 
        self.home_sheets.grid(row=3,column=0,sticky='nsew',columnspan=2)
        self.home_sheets.rowconfigure(0,weight=1)
        self.home_sheets.columnconfigure(0,weight=1)
        self.plot_buttons.grid(row=4,column=0,sticky='ew',columnspan=2)
        
        #labels
        self.home_buttons_help = tk.Label(self.fed_text, text='Welcome to FED3 Viz!',
                                          anchor='w')
        self.file_view_label    = tk.Label(self.home_sheets, text='File View',
                                          font='Segoe 10 italic')
        self.group_view_label    = tk.Label(self.home_sheets, text='Group View',
                                          font='Segoe 10 italic')
        
        #spreadsheets
        treeview_columns = ['Name','# events','start time',
                            'end time','duration','groups']
        self.files_spreadsheet = ttk.Treeview(self.home_sheets, 
                                              columns=treeview_columns)
        self.files_spreadsheet.column('Name', width=200)
        self.files_spreadsheet.column('# events', width=100)
        self.files_spreadsheet.column('start time', width=125)
        self.files_spreadsheet.column('end time', width=125)
        self.files_spreadsheet.column('duration', width=100)
        self.files_spreadsheet.column('groups', width=100)
        self.group_view = tk.Listbox(self.home_sheets,selectmode=tk.EXTENDED,
                               activestyle=tk.NONE)
        self.group_view.bind('<ButtonRelease-1>', self.select_group)
        for i,val in enumerate(treeview_columns):
            self.files_spreadsheet.heading(i, text=val)
        self.files_spreadsheet['show'] = 'headings'
        self.files_spreadsheet.bind('<Button-1>', lambda event, reverse=False: 
                                    self.sort_FEDs(event,reverse))
        self.files_spreadsheet.bind('<ButtonRelease-1>', self.update_buttons_home)
        self.files_spreadsheet.bind('<Double-Button-1>', lambda event, reverse=True: 
                                    self.sort_FEDs(event,reverse))

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
        self.button_single_pellet_plot = tk.Button(self.plot_buttons, 
                                                   text='Single Pellet Plot',
                                                   command=self.pellet_plot_single_TK,
                                                   state=tk.DISABLED)
        self.button_group_pellet_plot  = tk.Button(self.plot_buttons, 
                                                   text='Multi Pellet Plot',
                                                   command=self.pellet_plot_multi_TK,
                                                   state=tk.DISABLED)
        self.button_avg_pellet_plot    = tk.Button(self.plot_buttons,
                                                   text='Average Pellet Plot',
                                                   command=self.pellet_plot_avg_TK,
                                                   state=tk.DISABLED)
        self.button_interpellet_plot   = tk.Button(self.plot_buttons,
                                                   text='Interpellet Interval Plot',
                                                   command=self.interpellet_plot_TK,
                                                   state=tk.DISABLED)
        self.button_diagnostic_plot    = tk.Button(self.plot_buttons,
                                                   text='Diagnostic Plot',
                                                   command=self.diagnostic_plot_TK,
                                                   state=tk.DISABLED)
        self.button_daynight_plot      = tk.Button(self.plot_buttons,
                                                   text='Day/Night Plot',
                                                   command=self.daynight_plot_TK,
                                                   state=tk.DISABLED)
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
        

    #---HOVER TEXT DICTIONARY          
        #dictionary mapping widgets to hover text
        self.hover_text_one_dict = {self.button_load : 'Load FED3 files',
                                    self.button_delete: 'Unload highlighted FED3 files',
                                    self.button_single_pellet_plot:
                                        'Plot pellets received for one device',
                                    self.button_group_pellet_plot:
                                        'Plot pellets received for multiple devices (no averaging)',
                                    self.button_avg_pellet_plot:
                                        'Plot average pellets received for grouped devices (groups make individual curves)',
                                    self.button_create_group:
                                        'Add selected devices to a group',
                                    self.button_delete_group:
                                        'Delete selected group',
                                    self.button_save_groups:
                                        'Save the current group labels for the loaded devices',
                                    self.button_load_groups:
                                        'Load group labels from a saved groups file',
                                    self.button_diagnostic_plot:
                                        'Plot battery life and motor turns',
                                    self.button_interpellet_plot:
                                        'Plot histogram of intervals between pellet retrievals',
                                    self.button_daynight_plot:
                                        'Plot group averages for day/night on a bar chart'}
        for button in self.hover_text_one_dict.keys():
            button.bind('<Enter>', self.hover_text_one)
            button.bind('<Leave>', self.clear_hover_text_one)
     
    #---PLACE WIDGETS FOR HOME TAB     
        #fed_buttons/group buttons
        self.button_load.grid(row=0,column=0,sticky='sew')
        self.button_delete.grid(row=0,column=1,sticky='nsew')
        self.button_create_group.grid(row=0,column=2,sticky='sew')
        self.button_delete_group.grid(row=0,column=3,sticky='sew')
        self.button_save_groups.grid(row=0,column=4,sticky='sew')
        self.button_load_groups.grid(row=0,column=5,sticky='sew')
        
        #labels
        self.home_buttons_help.grid(row=0,column=0,sticky='w',padx=(0,20),
                                    pady=(10,10))
        
        #spreadsheets
        self.files_spreadsheet.grid(row=0,column=0,sticky='nsew')
        self.group_view.grid(row=0,column=1,sticky='nse')
        self.file_view_label.grid(row=1,column=0,sticky='w')
        self.group_view_label.grid(row=1,column=1,sticky='w')
        
        #plot_buttons
        self.button_single_pellet_plot.grid(row = 0, column = 0,sticky='ew')
        self.button_group_pellet_plot.grid(row=0, column = 1,sticky='ew')
        self.button_avg_pellet_plot.grid(row=0,column=2,sticky='ew')
        self.button_interpellet_plot.grid(row=0,column=3,sticky='ew')
        self.button_diagnostic_plot.grid(row=0,column=4,sticky='ew')
        self.button_daynight_plot.grid(row=0,column=5,sticky='ew')

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
        self.settings_col1.grid(row=0,column=0, sticky='nw')
        self.settings_col2.grid(row=0,column=1, sticky='nw')
        
        self.general_settings_frame = tk.Frame(self.settings_col1)
        self.general_settings_frame.grid(row=0,column=0, sticky='nsew')
        
        self.pellet_settings_frame = tk.Frame(self.settings_col1)
        self.pellet_settings_frame.grid(row=1,column=0, sticky='nsew')
        
        self.average_settings_frame = tk.Frame(self.settings_col1)
        self.average_settings_frame.grid(row=2,column=0,sticky='nsew',
                                         pady=(0,50))
        
        self.daynight_settings_frame = tk.Frame(self.settings_col2)
        self.daynight_settings_frame.grid(row=0,column=0,sticky='nsew',
                                          padx=(20,20))
        
        self.ipi_settings_frame = tk.Frame(self.settings_col2)
        self.ipi_settings_frame.grid(row=1,column=0, sticky='nsew',
                                     padx=20, pady=(20,0))
        
        self.load_settings_frame = tk.Frame(self.settings_col2)
        self.load_settings_frame.grid(row=2,column=0,sticky='nsew', 
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
                                                text='Average Pellet Plots',
                                                font=self.section_font)
        self.average_error_label     = tk.Label(self.average_settings_frame,
                                                text='Error value for average plots')
        self.average_bin_label       = tk.Label(self.average_settings_frame,
                                                text='Bin size for averaging (hours)')
        self.daynight_settings_label = tk.Label(self.daynight_settings_frame,
                                                text='Day/Night Plots',
                                                font=self.section_font)
        self.daynight_values_label = tk.Label(self.daynight_settings_frame,
                                              text='Values to plot')
        self.daynight_error_label  = tk.Label(self.daynight_settings_frame,
                                              text='Error bar value')
        self.ipi_settings_label = tk.Label(self.ipi_settings_frame,
                                           text='Interpellet Interval Plots',
                                           font=self.section_font)
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
                                                  var=self.nightshade_checkbox_val,
                                                  command=self.check_nightshade)
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
        #   average
        self.average_error_menu = ttk.Combobox(self.average_settings_frame,
                                               values=['SEM','STD','raw data','None'],
                                               width=10)
        self.average_error_menu.set('SEM')
        
        self.average_bin_menu = ttk.Combobox(self.average_settings_frame,
                                             values=list(range(1,25)),
                                             width=10)
        self.average_bin_menu.set(1)
        
        self.average_align_checkbox_val = tk.BooleanVar()
        self.average_align_checkbox_val.set(True)
        self.average_align_checkbox = ttk.Checkbutton(self.average_settings_frame,
                                                     text='Align average plots to the same start time (start time/no. days)',
                                                     command=self.check_average_align,
                                                     variable=self.average_align_checkbox_val)
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
        
        self.pellet_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))       
        self.pelletplottype_label.grid(row=1,column=0,padx=(20,100),sticky='w')
        self.pelletplottype_menu.grid(row=1,column=1,sticky='nw')
        self.pelletplotcumu_label.grid(row=2,column=0,padx=(20,100),sticky='w')
        self.pelletplotcumu_menu.grid(row=2,column=1,sticky='w')
        self.pelletplotcolor_label.grid(row=3,column=0,padx=(20,100),sticky='w')
        self.pelletplotcolor_menu.grid(row=3,column=1,sticky='nw')
        self.pelletplotalign_checkbox.grid(row=4,column=0,padx=(20,100),
                                           sticky='nw')
        
        self.average_settings_label.grid(row=0,column=0,sticky='w',pady=(20,0))
        self.average_error_label.grid(row=1,column=0,padx=(20,215),sticky='w')
        self.average_error_menu.grid(row=1,column=1,sticky='nw')
        self.average_bin_label.grid(row=2,column=0,sticky='w', padx=(20,0))
        self.average_bin_menu.grid(row=2,column=1,sticky='w')
        self.average_align_checkbox.grid(row=4,column=0,padx=(20,0),
                                         sticky='nw')
        self.average_alignstart_menu.grid(row=4,column=1,sticky='w')
        self.average_aligndays_menu.grid(row=4,column=2,sticky='w')
        
        self.daynight_settings_label.grid(row=0,column=0,sticky='w')
        self.daynight_values_label.grid(row=1,column=0,sticky='w',padx=(20,175))
        self.daynight_values.grid(row=1,column=1,sticky='w')
        self.daynight_error_label.grid(row=2,column=0,sticky='w',padx=(20,175))
        self.daynight_error_menu.grid(row=2,column=1,sticky='w')
        self.daynight_show_indvl.grid(row=3,column=0,sticky='w',padx=(20,0))
        
        self.ipi_settings_label.grid(row=0,column=0,sticky='w')
        self.ipi_kde_checkbox.grid(row=1,column=0,sticky='w',padx=(20,0))
        
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
        self.version1.grid(row=0,column=0,sticky='w')
        self.version2.grid(row=0,column=1,sticky='w')
        self.vdate1.grid(row=1,column=0,sticky='w')
        self.vdate2.grid(row=1,column=1,sticky='w')
        self.kravitzlab1.grid(row=2,column=0,sticky='w')
        self.kravitzlab2.grid(row=2,column=1,sticky='w')
        self.fedhack1.grid(row=3,column=0,sticky='w')
        self.fedhack2.grid(row=3,column=1,sticky='w')
        self.github1.grid(row=4,column=0,sticky='w')
        self.github2.grid(row=4,column=1,sticky='w')
        self.googlegr1.grid(row=5,column=0,sticky='w')
        self.googlegr2.grid(row=5,column=1,sticky='w')
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
            if overwrite:
                self.LOADED_FEDS = []
            for file in files:
                if skip_duplicates:
                    file_name = os.path.splitext(os.path.basename(file))
                    if file_name[0] not in loaded_filenames:
                        try:
                            pass_FEDs.append(FED3_File(file))
                        except:
                            failed_FEDs.append(file_name[0]+file_name[1])                     
                else:
                    try:
                        pass_FEDs.append(FED3_File(file))
                    except:
                        failed_FEDs.append(file_name[0]+file_name[1])
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
           
    def pellet_plot_avg_TK(self):
        args_dict = self.get_current_settings_as_args()
        args_dict['FEDs'] = self.LOADED_FEDS
        if self.allgroups_val.get():
            groups = self.GROUPS
        else:
            ints = [int(i) for i in self.group_view.curselection()]
            groups = [self.GROUPS[i] for i in ints]
        args_dict['groups'] = groups
        if self.average_align_checkbox_val.get():
            plotfunc=plots.pellet_plot_aligned_average
            plotdata=getdata.pellet_plot_aligned_average(**args_dict)
        else:
            plotfunc=plots.pellet_plot_average
            plotdata=getdata.pellet_plot_average(**args_dict)
        fig = plotfunc(**args_dict)
        if fig == 'NO_OVERLAP ERROR':
            self.raise_average_warning()
            return
        fig_name = self.create_plot_name('Average Pellet Plot')
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
        value = args_dict['dn_value'].capitalize()
        fig_name = self.create_plot_name(value + ' Day Night Plot')
        new_plot_frame = ttk.Frame(self.plot_container)
        new_plot = FED_Plot(figure=fig, frame=new_plot_frame,
                            figname=fig_name, plotfunc=plots.daynight_plot,
                            arguments=args_dict, plotdata=plotdata,)
        self.PLOTS[fig_name] = new_plot
        self.draw_figure(new_plot)
        self.raise_figure(fig_name)
        
    #---HOME HELPER FUNCTIONS
    def update_file_view(self):
        self.files_spreadsheet.delete(*self.files_spreadsheet.get_children())
        for i,fed in enumerate(self.LOADED_FEDS):
            values = (fed.basename, fed.events, fed.start_time.strftime('%b %d %Y, %H:%M'),
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
        self.home_buttons_help.configure(text='')
    
    def sort_FEDs(self, event, reverse):
        where_clicked = self.files_spreadsheet.identify_region(event.x,event.y)
        if where_clicked == 'heading':
            column = self.files_spreadsheet.identify_column(event.x)
            column_name = self.files_spreadsheet.column(column)['id']
            if column_name == "Name":
                self.LOADED_FEDS.sort(key=lambda x:x.basename, reverse=reverse)
            if column_name == "start time":
                self.LOADED_FEDS.sort(key=lambda x:x.start_time, reverse=reverse)
            if column_name == "end time":
                self.LOADED_FEDS.sort(key=lambda x:x.end_time, reverse=reverse)
            if column_name == "# events":
                self.LOADED_FEDS.sort(key=lambda x:x.events, reverse=reverse)
            if column_name == "duration":
                self.LOADED_FEDS.sort(key=lambda x:x.duration, reverse=reverse)
            if column_name == "groups":
                self.LOADED_FEDS.sort(key=lambda x:len(x.group), reverse=reverse)
            self.update_file_view()
            
    def update_buttons_home(self,*event):
        #if there are feds selected
        if self.files_spreadsheet.selection():
            self.button_delete.configure(state=tk.NORMAL)
            self.button_single_pellet_plot.configure(state=tk.NORMAL)
            self.button_group_pellet_plot.configure(state=tk.NORMAL)
            self.button_diagnostic_plot.configure(state=tk.NORMAL)
            self.button_create_group.configure(state=tk.NORMAL)
            self.button_interpellet_plot.configure(state=tk.NORMAL)
        else:
            self.button_delete.configure(state=tk.DISABLED)
            self.button_single_pellet_plot.configure(state=tk.DISABLED)
            self.button_group_pellet_plot.configure(state=tk.DISABLED)
            self.button_avg_pellet_plot.configure(state=tk.DISABLED)
            self.button_diagnostic_plot.configure(state=tk.DISABLED)
            self.button_create_group.configure(state=tk.DISABLED)
            self.button_interpellet_plot.configure(state=tk.DISABLED)
        #if the use all groups box is checked
        if self.allgroups_val.get():
            if self.GROUPS:
                self.button_avg_pellet_plot.configure(state=tk.NORMAL)
                self.button_daynight_plot.configure(state=tk.NORMAL)
            else:
                self.button_avg_pellet_plot.configure(state=tk.DISABLED)
                self.button_daynight_plot.configure(state=tk.DISABLED)
        else:
            if self.group_view.curselection():
                self.button_avg_pellet_plot.configure(state=tk.NORMAL)
                self.button_daynight_plot.configure(state=tk.NORMAL)
            else:
                self.button_avg_pellet_plot.configure(state=tk.DISABLED)
                self.button_daynight_plot.configure(state=tk.DISABLED)
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
                    if plot.plotfunc == plots.interpellet_interval_plot:
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
    def check_nightshade(self):
        if self.nightshade_checkbox_val.get():
            self.nightshade_lightson.configure(state=tk.NORMAL)
            self.nightshade_lightsoff.configure(state=tk.NORMAL)
        else:
            self.nightshade_lightson.configure(state=tk.DISABLED)
            self.nightshade_lightsoff.configure(state=tk.DISABLED)
            
    def check_pellet_type(self, *event):
        if self.pelletplottype_menu.get() == 'Frequency':
            self.pelletplotcumu_label.configure(fg='black')
            self.pelletplotcumu_menu.configure(state=tk.NORMAL)
        else:
            self.pelletplotcumu_label.configure(fg='gray')
            self.pelletplotcumu_menu.configure(state=tk.DISABLED)
            
    def check_average_align(self):
        if self.average_align_checkbox_val.get():
            self.average_alignstart_menu.configure(state=tk.NORMAL)
            self.average_aligndays_menu.configure(state=tk.NORMAL)
        else:
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
            self.average_align_checkbox_val.set(settings_df.loc['average_align','Values'])
            self.average_alignstart_menu.set(settings_df.loc['average_align_start','Values'])
            self.average_aligndays_menu.set(settings_df.loc['average_align_days','Values'])
            self.daynight_values.set(settings_df.loc['dn_value','Values'])
            self.daynight_error_menu.set(settings_df.loc['dn_error','Values'])
            self.daynight_show_indvl_val.set(settings_df.loc['dn_show_indvl','Values'])
            self.settings_lastused_val.set(settings_df.loc['load_last_used','Values'])
            self.ipi_kde_val.set(settings_df.loc['kde','Values'])
            self.check_average_align()
            self.check_nightshade()
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
                             average_align      =self.average_align_checkbox_val.get(),
                             average_align_start=self.average_alignstart_menu.get(),
                             average_align_days =self.average_aligndays_menu.get(),
                             dn_value           =self.daynight_values.get(),
                             dn_error           =self.daynight_error_menu.get(),
                             dn_show_indvl      =self.daynight_show_indvl_val.get(),
                             kde                =self.ipi_kde_val.get())
        return settings_dict
    
    def get_current_settings_as_args(self):
        settings_dict = self.get_current_settings()
        for time_setting in ['lights_on','lights_off','average_align_start']:
            settings_dict[time_setting] = self.times_to_int[settings_dict[time_setting]]
        for bin_setting in ['pellet_bins','average_bins']:
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
                '\n\nYou can still make an average pellet plot by checking' +  
                '\n"Align average plots to the same start time" in the settings tab.')
                
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
# def print_focus(*args):
#     print(root.focus_get())
root.protocol("WM_DELETE_WINDOW", root.save_last_used)
root.bind('<Escape>', root.update_all_buttons)
# root.bind('<ButtonRelease-1>', print_focus)
root.maxsize(1500,1000)
root.minsize(1050,20)
if __name__=="__main__":
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    root.mainloop()