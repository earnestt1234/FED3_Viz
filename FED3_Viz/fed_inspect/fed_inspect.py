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
                    'average_error', 'dn_value', 'dn_error']
shade_dark_funcs = ['pellet_plot_single', 'pellet_freq_single',
                    'pellet_plot_multi_unaligned',
                    'pellet_freq_multi_unaligned',
                    'pellet_plot_average','pellet_plot_aligned_average',
                    'diagnostic_plot',]
    
def add_quotes(string):
    output = '"' + string + '"'
    return output

def generate_code(PLOTOBJ):
    used_args = PLOTOBJ.arguments
    plotfunc    = plotfuncs[PLOTOBJ.plotfunc.__name__]
    args_ordered = inspect.getfullargspec(plotfunc).args

    output = ""
    imports = """
#IMPORTING LIBRARIES:
#these are libraries used for ALL plotting functions in FED3 Viz,
#so some may be redundant!

import datetime as dt
import os

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
    load_code = '\n\n#CODE TO LOAD FED DATA FROM A DIRECTORY\n\n'
    load_code += inspect.getsource(mymod1.FED3_File)
    
    shade_functions = '\n#HELPER FUNCTIONS (SHADING DARK)\n\n'
    shade_functions += inspect.getsource(mymod2.convert_dt64_to_dt) + '\n'
    shade_functions += inspect.getsource(mymod2.hours_between) + '\n'
    shade_functions += inspect.getsource(mymod2.night_intervals) + '\n'
    shade_functions += inspect.getsource(mymod2.shade_darkness)
    
    bar_functions = '\n#HELPER FUNCTIONS (DAY/NIGHT PLOTS)\n\n'
    bar_functions += inspect.getsource(mymod2.night_intervals) + '\n'
    bar_functions += inspect.getsource(mymod2.dn_get_yvals) + '\n'
    bar_functions += inspect.getsource(mymod2.raw_data_scatter)
        
    function_code ='\n#PLOTTING FUNCTION:\n\n'
    inspected = inspect.getsource(plotfunc).replace('plt.close()','')
    function_code += inspected
    
    arguments = '\n#ARGUMENT VALUES:\n\n'
    for arg in args_ordered:
        if arg == 'FEDs':
            if len(used_args[arg]) > 1:
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
                for group in fedfile.group:
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
        call += arg
        if i != len(args_ordered):
            call += ', '
        else:
            call += ')'
    
    output += imports
    output += load_code
    if plotfunc.__name__ in shade_dark_funcs:
        if used_args['shade_dark'] == True:
            output += shade_functions
    elif plotfunc.__name__ == 'daynight_plot':
        output += bar_functions
    output += function_code
    output += arguments
    output += call
    return output
        