# -*- coding: utf-8 -*-
"""
Generates the text used when the "Plot Code" button is pressed
in FED3 Viz.  Creates a runnable python script for recreating graphs.

@author: https://github.com/earnestt1234
"""
import inspect
from importlib import import_module
import importlib.util
import os

mymod1 = import_module('load.load') #my load module
homedir = os.path.dirname(os.path.dirname(__file__))
plotsloc = os.path.join(homedir, 'plots/plots.py')
spec = importlib.util.spec_from_file_location("plots.plots", plotsloc)
mymod2 = importlib.util.module_from_spec(spec) #my plots module
spec.loader.exec_module(mymod2)

plotfuncs = {name:func for name, func in inspect.getmembers(mymod2)}

string_arguments = ['pellet_color', 'pellet_bins', 'average_bins',
                    'average_error', 'circ_value', 'circ_error','bias_style',
                    'poke_bins','dependent','poke_style','break_style',
                    'break_error']
shade_dark_funcs = ['pellet_plot_single', 'pellet_freq_single',
                    'pellet_plot_multi_unaligned',
                    'pellet_freq_multi_unaligned',
                    'average_plot_ontime','average_plot_ondatetime',
                    'average_plot_onstart',
                    'diagnostic_plot','poke_plot','poke_bias',
                    'retrieval_time_single', 'battery_plot','motor_plot',
                    'day_night_ipi_plot']
avg_funcs = ['average_plot_ontime','average_plot_ondatetime',
             'average_plot_onstart',]
circ_funcs = ['daynight_plot', 'line_chronogram', 'heatmap_chronogram']
date_format_funcs = ['pellet_plot_single','pellet_freq_single',
                     'average_plot_ondatetime','poke_plot','poke_bias',
                     'diagnostic plot','pellet_plot_multi_unaligned',
                     'pellet_freq_multi_unaligned','retrieval_time_single',
                     'battery_plot','motor_plot']
pr_funcs = ['pr_plot','group_pr_plot']
meal_funcs = ['meal_size_histogram']

def add_quotes(string):
    output = '"' + string + '"'
    return output

def generate_code(PLOTOBJ):
    used_args = PLOTOBJ.arguments
    plotfunc    = plotfuncs[PLOTOBJ.plotfunc.__name__]
    args_ordered = inspect.getfullargspec(plotfunc).args
    if PLOTOBJ.plotfunc.__name__ in avg_funcs:
        if used_args['dependent'] == 'retrieval time':
            args_ordered.append('retrieval_threshold')
    elif PLOTOBJ.plotfunc.__name__ in circ_funcs:
        if used_args['circ_value'] == 'retrieval time':
            args_ordered.append('retrieval_threshold')

    output = ""
    imports = """#IMPORTING LIBRARIES:
#these are libraries used for ALL plotting functions in FED3 Viz,
#so some may be redundant!

import datetime as dt
import os

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from difflib import SequenceMatcher
from matplotlib.ticker import AutoMinorLocator
from pandas.plotting import register_matplotlib_converters
from scipy import stats

register_matplotlib_converters()
"""
    load_code = '\n#CODE TO LOAD FED DATA FROM A DIRECTORY\n\n'
    load_code += inspect.getsource(mymod1.FED3_File)
    
    shade_helpers = '\n#HELPER FUNCTIONS (SHADING DARK)\n\n'
    shade_helpers += inspect.getsource(mymod2.convert_dt64_to_dt) + '\n'
    shade_helpers += inspect.getsource(mymod2.hours_between) + '\n'
    shade_helpers += inspect.getsource(mymod2.night_intervals) + '\n'
    shade_helpers += inspect.getsource(mymod2.shade_darkness)
    
    dn_helpers = '\n#HELPER FUNCTIONS (DAY/NIGHT PLOTS)\n\n'
    dn_helpers += inspect.getsource(mymod2.night_intervals) + '\n'
    dn_helpers += inspect.getsource(mymod2.raw_data_scatter)
    
    circ_helpers = '\n#HELPER FUNCTIONS (CIRCADIAN PLOTS)\n\n'
    circ_helpers += inspect.getsource(mymod2.resample_get_yvals) + '\n'
    
    poke_helpers = '\n#HELPER FUNCTIONS (POKE PLOTS)\n\n'
    poke_helpers += inspect.getsource(mymod2.left_right_noncumulative)
    
    bias_helpers = '\n#HELPER FUNCTIONS (BIAS PLOTS)\n\n'
    bias_helpers += inspect.getsource(mymod2.resample_get_yvals)
    bias_helpers += inspect.getsource(mymod2.left_right_bias)
    
    avg_helpers = '\n#HELPER FUNCTIONS (AVERAGE PLOTS)\n\n'
    avg_helpers += inspect.getsource(mymod2.resample_get_yvals)
    avg_helpers += inspect.getsource(mymod2.left_right_noncumulative)
    avg_helpers += inspect.getsource(mymod2.left_right_bias)
    
    date_helpers = '\n#HELPER FUNCTIONS (DATE FORMATTING)\n\n'
    date_helpers += inspect.getsource(mymod2.date_format_x)
    
    pr_helpers = '\n#HELPER FUNCTIONS (BREAKPOINT PLOTS)\n\n'
    pr_helpers += inspect.getsource(mymod2.raw_data_scatter)
    
    meal_helpers = '\n#HELPER FUNCTIONS (MEAL SIZE)\n\n'
    meal_helpers += inspect.getsource(mymod2.label_meals)
    
    function_code ='\n#PLOTTING FUNCTION:\n\n'
    inspected = inspect.getsource(plotfunc).replace('plt.close()','')
    function_code += inspected
    
    arguments = '\n#ARGUMENT VALUES:\n\n'
    for arg in args_ordered:
        if arg == 'FEDs' and len(used_args['FEDs']) > 1:
            feds_text = ''
            fed_list = []
            fed_varname_dict = {}
            for i, fedfile in enumerate(used_args[arg],start=1):
                var_name = 'fed' + str(i)
                feds_text += var_name + ' = ' + str(fedfile) + '\n'
                fed_list.append(var_name)
                fed_varname_dict[fedfile] = var_name
            feds_text += '\nFEDs = ' + '[%s]' % ', '.join(map(str, fed_list)) + '\n'
            arguments += feds_text
        elif arg == 'groups':
            arguments += ('\ngroups = ' + str(used_args['groups']) + '\n\n')
            for fedfile in used_args['FEDs']:
                for group in used_args['groups']:
                    if group in fedfile.group:
                        arguments += (fed_varname_dict[fedfile] + '.group.append(' 
                                      + add_quotes(group) +')\n')
            arguments += '\n'           
        else:
            if arg in string_arguments:
                formatted = add_quotes(str(used_args[arg]))
            else:
                formatted = str(used_args[arg])
            text = arg + ' = ' + formatted +'\n'
            arguments += text
        
    call = '\n#CALLING THE FUNCTION\n\n'
    call += 'plot = '
    call += plotfunc.__name__ + '('
    for i, arg in enumerate(args_ordered, start=1):
        if arg == 'retrieval_threshold' and (plotfunc.__name__ in avg_funcs):
            call += (arg + '=retrieval_threshold')
        else:
            call+=arg
        if i != len(args_ordered):
            call += ', '
        else:
            call += ')'
    
    output += imports
    output += load_code
    if plotfunc.__name__ in shade_dark_funcs:
        output += shade_helpers
    if plotfunc.__name__ == 'daynight_plot':
        output += dn_helpers
    if plotfunc.__name__ in circ_funcs:
        output += circ_helpers
    if plotfunc.__name__ == 'poke_plot':
        output += poke_helpers
    if plotfunc.__name__ == 'poke_bias':
        output += bias_helpers
    if plotfunc.__name__ in avg_funcs:
        output += avg_helpers
    if plotfunc.__name__ in date_format_funcs:
        output += date_helpers
    if plotfunc.__name__ in pr_funcs:
        output += pr_helpers
    if plotfunc.__name__ in meal_funcs:
        output += meal_helpers
    output += function_code
    output += arguments
    output += call
    return output

def get_arguments(PLOTOBJ):
    func_name = PLOTOBJ.plotfunc.__name__
    plotfunc = plotfuncs[func_name]
    arguments = inspect.getfullargspec(plotfunc).args
    if func_name in ['pellet_plot_single', 'pellet_freq_single']:
        arguments.append('pellet_values')
    if func_name in ['pellet_plot_multi_aligned', 'pellet_plot_multi_unaligned',
                    'pellet_freq_multi_aligned','pellet_freq_multi_unaligned']:
        arguments.append('pellet_values')
        arguments.append('pellet_align')
    if func_name in ['average_plot_ontime','average_plot_ondatetime',
                    'average_plot_onstart',]:
        arguments.append('average_method')
    return arguments