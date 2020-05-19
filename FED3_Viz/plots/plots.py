# -*- coding: utf-8 -*-
"""
Set of functions for plotting FED3 data.  These functions are called
by FED3 Viz to make plots, and the getdata module inspects the code and 
shows it to the user when prompted with the "Plot Code" button.

@author: https://github.com/earnestt1234
"""
import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from scipy import stats
import seaborn as sns

from load.load import FED3_File

register_matplotlib_converters()

#---HELPER FUNCTIONS

def convert_dt64_to_dt(dt64):
    new_date = (dt64 - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
    new_date = dt.datetime.utcfromtimestamp(new_date)
    return new_date

def hours_between(start, end, convert=True):
    if convert:
        start = convert_dt64_to_dt(start)
        end = convert_dt64_to_dt(end)
    rounded_start = dt.datetime(year=start.year,
                                month=start.month,
                                day=start.day,
                                hour=start.hour)
    rounded_end = dt.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=end.hour)
    return pd.date_range(rounded_start,rounded_end,freq='1H')

def night_intervals(array, lights_on, lights_off, instead_days=False):
    lights_on = dt.time(hour=lights_on)
    lights_off = dt.time(hour=lights_off)
    if lights_on == lights_off:
            night_intervals = []
            return night_intervals
    elif lights_off > lights_on:
        at_night = [((i.time() >= lights_off) or
                    (i.time() < lights_on)) for i in array]
    elif lights_off < lights_on:
        at_night = [((i.time() >= lights_off) and
                    (i.time() < lights_on)) for i in array]
    if instead_days:
        at_night = [not i for i in at_night]
    night_starts = []
    night_ends = []
    if at_night[0] == True:
        night_starts.append(array[0])
    for i, _ in enumerate(at_night[1:],start=1):
        if at_night[i] == True and at_night[i-1] == False:
            night_starts.append(array[i])
        elif at_night[i] == False and at_night[i-1] == True:
            night_ends.append(array[i])
    if at_night[-1] == True:
        night_ends.append(array[-1])
    night_intervals = list(zip(night_starts, night_ends))
    return night_intervals

def shade_darkness(ax, min_date,max_date,lights_on,lights_off,
                   convert=True):
    hours_list = hours_between(min_date, max_date,convert=convert)
    nights = night_intervals(hours_list, lights_on=lights_on,
                             lights_off=lights_off)
    if nights:
        for i, interval in enumerate(nights):
            start = interval[0]
            end = interval[1]
            if start != end:
                ax.axvspan(start,
                           end,
                           color='gray',
                           alpha=.2,
                           label='_'*i + 'lights off',
                           zorder=0)

def resample_get_yvals(df, value):
    possible = ['pellets','retrieval time','interpellet intervals',
                'correct pokes','errors','correct pokes (%)','errors (%)',
                'poke bias (correct - error)', 'poke bias (left - right)',
                'poke bias (correct %)',]
    assert value in possible, 'Value not understood by daynight plot: ' + value
    if value == 'poke bias (correct %)':
        value = 'correct pokes (%)'
    if value == 'pellets':
        output = df['Binary_Pellets'].sum()
    elif value == 'retrieval time':
        output = df['Retrieval_Time'].mean()
    elif value == 'interpellet intervals':
        output = df['Interpellet_Intervals'].mean()
    elif value == 'correct pokes':
        output = list(df['Correct_Poke']).count(True)
    elif value == 'errors':
        output = list(df['Correct_Poke']).count(False)
    elif value == 'correct pokes (%)':
        try:
            correct = (list(df['Correct_Poke']).count(True))
            incorrect = (list(df['Correct_Poke']).count(False))
            output = correct/(correct+incorrect) * 100
        except ZeroDivisionError:
            output = np.nan
    elif value == 'errors (%)':
        try:
            correct = (list(df['Correct_Poke']).count(True))
            incorrect = (list(df['Correct_Poke']).count(False))
            output = incorrect/(correct+incorrect)*100
        except ZeroDivisionError:
            output = np.nan
    elif value == 'poke bias (correct - error)':
        output = list(df['Correct_Poke']).count(True) - list(df['Correct_Poke']).count(False)
    elif value == 'poke bias (left - right)':
        output = df['Binary_Left_Pokes'].sum() - df['Binary_Right_Pokes'].sum()
    return output      

def raw_data_scatter(array, xcenter, spread):    
    y = array
    x = np.random.uniform(0,(spread/2), size=len(y))
    half = int(len(y)/2)
    for i in range(half):
        x[i] *= -1
    np.random.shuffle(x)
    x += xcenter
    return x,y

def poke_resample_func(bin_, val, style):
    if style == 'Percentage':
        output = (bin_==val).sum()/len(bin_)*100 if len(bin_) else np.nan
    elif style == 'Frequency':
        output = (bin_==val).sum()
    return output

def date_format_x(ax, start, end):
    quarter_hours = mdates.MinuteLocator(byminute=[0,15,30,45])
    all_hours = mdates.HourLocator()
    quarter_days = mdates.HourLocator(byhour=[0,6,12,18])
    days = mdates.DayLocator()
    two_days = mdates.DayLocator(interval=2)
    three_days = mdates.DayLocator(interval=3)
    months = mdates.MonthLocator()
    d8_span = end - start
    if d8_span < dt.timedelta(hours=12):
        xfmt = mdates.DateFormatter('%H:%M')
        major = all_hours
        minor = quarter_hours
    elif (d8_span >= dt.timedelta(hours=12)) and (d8_span < dt.timedelta(hours=24)):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = quarter_days
        minor = all_hours
    elif (d8_span >= dt.timedelta(hours=24)) and (d8_span < dt.timedelta(days=3)):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = days
        minor = quarter_days
    elif d8_span >= dt.timedelta(days=3) and (d8_span < dt.timedelta(days=6)):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = two_days
        minor = days
    elif (d8_span >= dt.timedelta(days=6)) and (d8_span < dt.timedelta(days=20)):
        xfmt = mdates.DateFormatter('%b %d')
        major = three_days
        minor = days
    elif d8_span >= dt.timedelta(days=20):
        xfmt = mdates.DateFormatter("%b '%y")
        major = months
        minor = three_days
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax.xaxis.set_major_locator(major)
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.set_minor_locator(minor)   
    

def left_right_bias(df, bin_size, version='ondatetime', starttime=None):
    if version == 'ondatetime':
        grouper = pd.Grouper(freq=bin_size,base=0)
    elif version == 'ontime':
        grouper = pd.Grouper(freq=bin_size,base=starttime)
    elif version == 'onstart':
        grouper = pd.Grouper(key='Elapsed_Time',freq=bin_size,base=0)
    resampled = df.groupby(grouper)
    left_resampled = resampled['Left_Poke_Count'].max().dropna()
    right_resampled = resampled['Right_Poke_Count'].max().dropna()
    left_diff = left_resampled.diff()
    left_diff[0] = left_resampled[0]
    left_diff = left_diff.reindex(resampled.sum().index)
    right_diff = right_resampled.diff()
    right_diff[0] = right_resampled[0]
    right_diff = right_diff.reindex(resampled.sum().index)
    out = left_diff/(left_diff+right_diff).replace([np.inf,-np.inf], np.nan)*100
    return out
    
#---Single Pellet Plots

def pellet_plot_single(FED, shade_dark, lights_on, lights_off, pellet_color,
                       *args, **kwargs):
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_plot_single()'   
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    df = FED.data
    x = df.index
    y = df['Pellet_Count']
    ax.plot(x, y,color=pellet_color)
    date_format_x(ax, x[0], x[-1])
    ax.set_xlabel('Time')
    ax.set_ylabel('Cumulative Pellets')    
    title = ('Pellets Retrieved for ' + FED.filename)
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax,min(x), max(x),
                       lights_on=lights_on,
                       lights_off=lights_off)
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()
    return fig

def pellet_freq_single(FED, pellet_bins, shade_dark, lights_on,
                       lights_off, pellet_color, *args, **kwargs):
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_freq_single()'
    df = FED.data.resample(pellet_bins).sum()
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    x = df.index
    y = df['Binary_Pellets']    
    ax.bar(x, y,width=(x[1]-x[0]),
           align='edge', alpha=.8, color=pellet_color)
    ax.set_xlabel('Time')
    date_format_x(ax, x[0], x[-1])
    ax.set_ylabel('Pellets') 
    title = ('Pellets Retrieved for FED ' + FED.filename)
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax, x[0], x[-1],
                       lights_on=lights_on,
                       lights_off=lights_off)
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')   
    plt.tight_layout()
    
    return fig

def pellet_plot_multi_aligned(FEDs, *args,**kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    xmax = 0
    ymax = 0          
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    for file in FEDs:
        df = file.data
        x = [(time.total_seconds()/3600) for time in df['Elapsed_Time']]   
        y = df['Pellet_Count']
        ax.plot(x, y, label=file.filename)            
        if max(x) > xmax:
            xmax = max(x)
        if max(y) > ymax:
            ymax = max(y)
    ax.set_xlabel('Time (h)')
    ax.set_xlim(0,xmax)
    number_of_days = int(xmax//24)
    if number_of_days > 2:
        days_in_hours = [24*day for day in range(number_of_days+1)]
        ax.set_xticks(days_in_hours)
    else:
        days_in_sixes = [6*quart for quart in range((number_of_days+1)*4)]
        ax.set_xticks(days_in_sixes)
    ax.xaxis.set_minor_locator(AutoMinorLocator()) 
    ax.set_ylabel('Cumulative Pellets')     
    ax.set_ylim(0,ymax*1.1)    
    title = ('Pellets Retrieved for Multiple FEDs')
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()     
    
    return fig

def pellet_plot_multi_unaligned(FEDs, shade_dark, lights_on,
                                lights_off,*args,**kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    days = mdates.DayLocator()
    min_date = np.datetime64('2100')
    max_date = np.datetime64('1970')    
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    for file in FEDs:
        df = file.data
        x = df.index
        y = df['Pellet_Count']
        ax.plot(x, y, label=file.filename)
        if max(x) > max_date:
            max_date = max(x)
        if min(x) < min_date:
            min_date = min(x)
    ax.set_xlabel('Time (h)')
    date_format_x(ax, min_date, max_date)
    ax.set_ylabel('Cumulative Pellets')  
    title = ('Pellets Retrieved for Multiple FEDs')
    ax.set_title(title)   
    if shade_dark:
        shade_darkness(ax, min_date, max_date,
                   lights_on=lights_on,
                   lights_off=lights_off)  
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()     
    
    return fig

def pellet_freq_multi_aligned(FEDs, pellet_bins, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    max_time = 0
    
    for file in FEDs:
        df = file.data.resample(pellet_bins,base=0).sum()         
        times = []
        for i, date in enumerate(df.index):
            times.append(date - df.index[0])
        times = [(time/np.timedelta64(1,'h')) for time in times]      
        x = times
        y = df['Binary_Pellets'] 
        ax.bar(x, y, width=(x[1]-x[0]),
               align='edge', alpha=.8, label=file.filename)
        if max(times) > max_time:
            max_time = max(times)
    ax.set_xlabel('Time (h)')
    ax.set_xlim(0,max_time)
    number_of_days = int(max_time//24)
    days_in_hours = [24*day for day in range(number_of_days+1)]
    ax.set_xticks(days_in_hours)
    ax.xaxis.set_minor_locator(AutoMinorLocator())      
    ax.set_ylabel('Pellets')    
    title = ('Pellets Retrieved for Multiple FEDs')
    ax.set_title(title)   
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()     
    
    return fig

def pellet_freq_multi_unaligned(FEDs, pellet_bins, pellet_align, shade_dark,
                                lights_on, lights_off, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    days = mdates.DayLocator()
    min_date = np.datetime64('2100')
    max_date = np.datetime64('1970')   
        
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    for file in FEDs:
        df = file.data.resample(pellet_bins,base=0).sum()
        x = df.index
        y = df['Binary_Pellets']
        ax.bar(x, y, label=file.filename,
               alpha=.8,align='edge',width=(x[1]-x[0]))           
        if max(x) > max_date:
            max_date = max(x)
        if min(x) < min_date:
            min_date = min(x)      
    ax.set_xlabel('Time')
    date_format_x(ax, min_date, max_date)
    ax.set_ylabel('Pellets')
    title = ('Pellets Retrieved for Multiple FEDs')
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax, min_date, max_date,
                   lights_on=lights_on,
                   lights_off=lights_off)        
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()     
    
    return fig

def interpellet_interval_plot(FEDs, kde, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to interpellet_interval_plot()'
        
    fig, ax = plt.subplots(figsize=(4,5), dpi=125)
    lowest = -2
    highest = 5
    ylabel = 'Density Estimation' if kde else 'Count'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('minutes between pellets')
    ax.set_xticks(range(lowest,highest))
    ax.set_xticklabels([10**num for num in range(-2,5)])
    ax.set_title('Interpellet Interval Plot')
    c=0
    bins = []
    while c <= highest:
        bins.append(lowest+c)
        c+=0.1
    for FED in FEDs:
        df = FED.data
        y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
        y = [np.log10(val) for val in y if not pd.isna(val)]
        sns.distplot(y,bins=bins,label=FED.filename,ax=ax,norm_hist=False,
                     kde=kde)
    ax.legend(fontsize=8)
    plt.tight_layout()
    
    return fig

def group_interpellet_interval_plot(FEDs, groups, kde, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to interpellet_interval_plot()'
        
    fig, ax = plt.subplots(figsize=(4,5), dpi=125)
    lowest = -2
    highest = 5
    ylabel = 'Density Estimation' if kde else 'Count'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('minutes between pellets')
    ax.set_xticks(range(lowest,highest))
    ax.set_xticklabels([10**num for num in range(-2,5)])
    ax.set_title('Interpellet Interval Plot')
    c=0
    bins = []
    while c <= highest:
        bins.append(lowest+c)
        c+=0.1
    for group in groups:
        all_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
                y = [np.log10(val) for val in y if not pd.isna(val)]
                all_vals += y
        sns.distplot(all_vals,bins=bins,label=group,ax=ax,norm_hist=False,
                     kde=kde)
        ax.legend(fontsize=8)
        plt.tight_layout()
    
    return fig

#---Average Pellet Plots

def average_plot_ondatetime(FEDs, groups, dependent, average_bins, average_error, shade_dark,
                            lights_on, lights_off,*args, **kwargs):
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    earliest_end = dt.datetime(2999,1,1,0,0,0)
    latest_start = dt.datetime(1970,1,1,0,0,0)
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_average_cumulative()'
        df = file.data
        if min(df.index) > latest_start:
            latest_start = min(df.index)
        if max(df.index) < earliest_end:
            earliest_end = max(df.index)
    if earliest_end < latest_start:
        return 'NO_OVERLAP ERROR'
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    maxy = 0
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data.groupby(pd.Grouper(freq=average_bins,base=0))
                y = df.apply(resample_get_yvals,dependent)
                y = y[(y.index > latest_start) &
                        (y.index < earliest_end)].copy()
                avg.append(y)
                if show_indvl:
                    x = y.index
                    y = y
                    ax.plot(x, y, color=colors[i], alpha=.3, linewidth=.8)                   
        group_avg = np.nanmean(avg, axis=0)    
        if average_error == 'None':
            label = group
        else:
            label = group + ' (±' + average_error + ')'
        x = y.index
        y = group_avg
        ax.plot(x, y, label=label, color=colors[i])
        if average_error != 'None':
            if average_error == 'STD':
                error_shade = np.nanstd(avg, axis=0)
            elif average_error == 'SEM':
                error_shade = stats.sem(avg, axis=0, nan_policy='omit')         
            ax.fill_between(x,
                            group_avg+error_shade,
                            group_avg-error_shade,
                            alpha = .3,
                            color=colors[i]) 
        if np.nanmax(np.abs(group_avg) + error_shade) > maxy:
            maxy = np.nanmax(np.abs(group_avg) + error_shade)
    ax.set_xlabel('Time')
    date_format_x(ax, latest_start, earliest_end)
    if "%" in dependent:
        ax.set_ylim(0,100)
    if 'bias' in dependent:
        ax.set_ylim(-abs(maxy)*1.1, abs(maxy)*1.1)
        ax.axhline(y=0, linestyle='--', color='gray', zorder=2)
    ax.set_title('Average Plot of ' + dependent.capitalize())
    if shade_dark:
        shade_darkness(ax, latest_start, earliest_end,
                       lights_on=lights_on,
                       lights_off=lights_off)       
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')    
    plt.tight_layout() 
    
    return fig


def average_plot_ontime(FEDs, groups, dependent, average_bins, average_align_start,
                        average_align_days, average_error,
                        shade_dark, lights_on, lights_off,
                        *args, **kwargs):
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_average_cumulative()'
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    start_datetime = dt.datetime(year=1970,
                                 month=1,
                                 day=1,
                                 hour=average_align_start)
    end_datetime = start_datetime + dt.timedelta(days=average_align_days)
    date_range = pd.date_range(start_datetime,end_datetime,freq=average_bins)    
    maxy=0
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data.groupby(pd.Grouper(freq=average_bins,base=average_align_start))
                y = df.apply(resample_get_yvals, dependent)
                first_entry = y.index[0]
                aligned_first_entry = dt.datetime(year=1970,month=1,day=1,
                                                  hour=first_entry.hour)
                alignment_shift = first_entry - aligned_first_entry
                y.index = [i-alignment_shift for i in y.index]
                y = y.reindex(date_range)
                avg.append(y)
                if show_indvl:
                    x = y.index
                    ax.plot(x, y, color=colors[i], alpha=.3, linewidth=.8)               
        group_avg = np.nanmean(avg, axis=0)
        if average_error == 'None':
            label = group
        else:
            label = group + ' (±' + average_error + ')'
        x = y.index
        y = group_avg
        ax.plot(x, y, label=label, color=colors[i])
        if average_error != 'None':
            if average_error == 'STD':
                error_shade = np.nanstd(avg, axis=0)
            elif average_error == 'SEM':
                error_shade = stats.sem(avg, axis=0, nan_policy='omit')         
            ax.fill_between(x,
                            group_avg+error_shade,
                            group_avg-error_shade,
                            alpha = .3,
                            color=colors[i])
            if np.nanmax(np.abs(group_avg) + error_shade) > maxy:
                maxy = np.nanmax(np.abs(group_avg) + error_shade)
    if shade_dark:
        shade_darkness(ax, start_datetime, end_datetime,
                       lights_on=lights_on,
                       lights_off=lights_off,
                       convert=False)
    hours_start = start_datetime.strftime('%I%p')
    if hours_start[0] == '0':
        hours_start = hours_start[1:]
    ax.set_xlabel('Hours since ' + hours_start + ' on first day')
    ticks = pd.date_range(start_datetime,end_datetime,freq='12H')
    tick_labels = [i*12 for i in range(len(ticks))]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(start_datetime,end_datetime + dt.timedelta(hours=5))
    ax.set_ylabel(dependent.capitalize())
    if "%" in dependent:
        ax.set_ylim(0,100)
    if 'bias' in dependent:
        ax.set_ylim(-abs(maxy)*1.1, abs(maxy)*1.1)
        ax.axhline(y=0, linestyle='--', color='gray', zorder=2)
    ax.set_title('Average Plot of ' + dependent.capitalize())
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig

def average_plot_onstart(FEDs, groups, dependent, average_bins, average_error,
                         *args, **kwargs):
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    longest_index = []
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_average_onstart()'
        df = file.data
        resampled = df.resample(average_bins, base=0, on='Elapsed_Time').sum()
        if len(longest_index) == 0:
            longest_index = resampled.index
        elif len(resampled.index) > len(longest_index):
            longest_index = resampled.index
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    maxy=0
    maxx=0
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:              
                if dependent == 'poke bias (left %)':
                    y = left_right_bias(file.data, average_bins, version='onstart')
                else:
                    df = file.data.groupby(pd.Grouper(key='Elapsed_Time',freq=average_bins,
                                                  base=0))
                    y = df.apply(resample_get_yvals, dependent)
                y = y.reindex(longest_index)          
                y.index = [time.total_seconds()/3600 for time in y.index]
                if np.nanmax(y.index) > maxx:
                    maxx=np.nanmax(y.index)
                avg.append(y)
                if show_indvl:
                    x = y.index
                    ax.plot(x, y, color=colors[i], alpha=.3, linewidth=.8)
        group_avg = np.nanmean(avg, axis=0)
        if average_error == 'None':
            label = group
        else:
            label = group + ' (±' + average_error + ')'
        x = y.index
        y = group_avg
        ax.plot(x, y, label=label, color=colors[i])
        if average_error != 'None':
            if average_error == 'STD':
                error_shade = np.nanstd(avg, axis=0)
            elif average_error == 'SEM':
                error_shade = stats.sem(avg, axis=0, nan_policy='omit')  
            ax.fill_between(x,
                            group_avg+error_shade,
                            group_avg-error_shade,
                            alpha = .3,
                            color=colors[i])
            if np.nanmax(np.abs(group_avg) + error_shade) > maxy:
                maxy = np.nanmax(np.abs(group_avg) + error_shade)
    ax.set_xlabel('Time (h since recording start)')
    number_of_days = int(maxx//24)
    if number_of_days > 2:
        days_in_hours = [24*day for day in range(number_of_days+1)]
        ax.set_xticks(days_in_hours)
    else:
        days_in_sixes = [6*quart for quart in range((number_of_days+1)*4)]
        ax.set_xticks(days_in_sixes)
    ax.xaxis.set_minor_locator(AutoMinorLocator()) 
    ax.set_ylabel(dependent.capitalize())  
    if "%" in dependent:
        ax.set_ylim(-5,105)
    if 'bias' in dependent:
        ax.axhline(y=50, linestyle='--', color='gray', zorder=2)     
    title = ('Average Plot of ' + dependent.capitalize())
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()     
    
    return fig

#---Single Poke Plots

def poke_plot(FED, poke_bins, poke_show_correct, poke_show_error, poke_style,
              shade_dark, lights_on, lights_off, *args, **kwargs):
    assert isinstance(FED, FED3_File), 'Non FED3_File passed to poke_plot()'
    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)
    if poke_style == 'Cumulative':
        pokes = FED.data['Correct_Poke']
        if poke_show_correct:
            y = pd.Series([1 if i==True else np.nan for i in pokes]).cumsum()
            y.index = FED.data.index
            y = y.dropna()
            x = y.index
            ax.plot(x, y, color='mediumseagreen', label = 'correct pokes')
        if poke_show_error:
            y = pd.Series([1 if i==False else np.nan for i in pokes]).cumsum()
            y.index = FED.data.index
            y = y.dropna()
            x = y.index
            ax.plot(x, y, color='indianred', label = 'error pokes')
    else:
        resampled = FED.data['Correct_Poke'].dropna().resample(poke_bins)
        if poke_show_correct:
            y = resampled.apply(poke_resample_func, val=True, style=poke_style)
            x = y.index
            ax.plot(x, y, color='mediumseagreen', label = 'correct pokes')
        if poke_show_error:
            y = resampled.apply(poke_resample_func, val=False, style=poke_style)
            x = y.index
            ax.plot(x, y, color='indianred', label = 'error pokes')
    date_format_x(ax, x[0], x[-1])
    ax.set_xlabel('Time')
    ylabel = 'Pokes'
    if poke_style == "Percentage":
        ylabel += ' (%)'
        ax.set_ylim(0,100)
    ax.set_ylabel(ylabel)
    title = ('Pokes for ' + FED.filename)
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax, min(FED.data.index), max(FED.data.index),
                       lights_on=lights_on,
                       lights_off=lights_off)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')   
    plt.tight_layout()
        
    return fig

def poke_bias(FED, poke_bins, bias_style, shade_dark, lights_on,
              lights_off, dynamic_color, *args, **kwargs):
    DENSITY = 10000
    assert isinstance(FED, FED3_File), 'Non FED3_File passed to poke_plot()'
    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)
    if bias_style == 'C/E':
        resampled = FED.data.resample(poke_bins)
        y = resampled.apply(resample_get_yvals, 'poke bias (correct %)')
    elif bias_style == 'L/R':
        y = left_right_bias(FED.data, poke_bins)
    x = y.index
    if not dynamic_color:
        ax.plot(x, y, color = 'magenta', zorder=3)
    else:
        xnew = pd.date_range(min(x),max(x),periods=DENSITY)
        ynew = np.interp(xnew, x, y)
        ax.scatter(xnew, ynew, s=1, c=ynew,
                   cmap='bwr', vmin=0, vmax=100, zorder=1)
    date_format_x(ax, x[0], x[-1])
    if bias_style == 'C/E':
        label = 'Correct Pokes (%)'
    elif bias_style == 'L/R':
        label = 'Left Pokes (%)'
    ax.set_ylabel(label)
    ax.set_ylim(-5,105)
    ax.set_title('Poke Bias for ' + FED.filename)
    ax.axhline(y=50, linestyle='--', color='gray', zorder=2)
    if shade_dark:
        shade_darkness(ax, min(x), max(x),
                       lights_on=lights_on,
                       lights_off=lights_off)
        ax.legend(bbox_to_anchor=(1,1), loc='upper left') 
    plt.tight_layout()
    
    return fig   

#---Progressive Ratio Plots
import matplotlib as mpl

def pr_plot(FEDs, break_hours, break_mins, break_style, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File), 'Non FED3_File passed to pr_plot()'
    delta = dt.timedelta(hours=break_hours, minutes=break_mins)
    ys = []
    color_gradient_divisions = [(1/len(FEDs))*i for i in range(len(FEDs))]
    cmap = mpl.cm.get_cmap('spring')
    color_gradients = cmap(color_gradient_divisions)
    for FED in FEDs:
        df = FED.data
        index = df.index
        nextaction = [index[j+1] - index[j] for j in range(len(index[:-1]))]
        try:
            break_index = next(i for i, val in enumerate(nextaction) if val > delta)
        except StopIteration:
            break_index = len(nextaction)
        if break_style == 'pellets':
            out = df.loc[df.index[break_index],'Pellet_Count']
        elif break_style == 'pokes':
            cum_correct = pd.Series([1 if i==True else np.nan for i in df['Correct_Poke']]).cumsum()
            cum_correct.index = df.index
            cum_correct = cum_correct[cum_correct.index <= df.index[break_index]].copy()
            out = np.nanmax(cum_correct)
        ys.append(out)
    fig_len = min([max([len(FEDs), 4]), 8])
    fig, ax = plt.subplots(figsize=(fig_len, 5), dpi=125)
    xs = range(len(FEDs))
    xticklabels = [x.filename for x in FEDs]
    ax.bar(xs, ys, color=color_gradients)
    ax.set_xlabel('File')
    ax.set_xticks(xs)
    ax.set_xticklabels(xticklabels, rotation=45, ha='right')
    labels = {'pellets':'Pellets', 'pokes':'Correct Pokes',}
    ax.set_ylabel(labels[break_style])
    ax.set_title("Breakpoint")
    plt.tight_layout()
    
    return fig
   
def group_pr_plot(FEDs, groups, break_hours, break_mins, break_style,
                  break_error, break_show_indvl, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File), 'Non FED3_File passed to group_pr_plot()'
    fig, ax = plt.subplots(figsize=(3.5,5), dpi=125)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color'] 
    xs = range(len(groups))
    delta = dt.timedelta(hours=break_hours, minutes=break_mins)
    title = 'Breakpoint'
    for i, group in enumerate(groups):
        group_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                index = df.index
                nextaction = [index[j+1] - index[j] for j in range(len(index[:-1]))]
                try:
                    break_index = next(i for i, val in enumerate(nextaction) if val > delta)
                except StopIteration:
                    break_index = len(nextaction)
                if break_style == 'pellets':
                    out = df.loc[df.index[break_index],'Pellet_Count']
                elif break_style == 'pokes':
                    cum_correct = pd.Series([1 if i==True else np.nan for i in df['Correct_Poke']]).cumsum()
                    cum_correct.index = df.index
                    cum_correct = cum_correct[cum_correct.index <= df.index[break_index]].copy()
                    out = np.nanmax(cum_correct)
                group_vals.append(out)
        y = np.nanmean(group_vals,)
        error_val = None
        if break_error == 'SEM':
            error_val = stats.sem(group_vals,nan_policy='omit')
            title = 'Breakpoint\n(error = SEM)'
        elif break_error == 'STD':
            error_val = np.nanstd(group_vals)
            title = 'Breakpoint\n(error = STD)'
        ax.bar(xs[i], y, color=colors[i], yerr=error_val,
               capsize=3,alpha=.5,ecolor='gray')
        if break_show_indvl:
            spread = .16
            x, y = raw_data_scatter(group_vals,
                                    xcenter=xs[i],
                                    spread=spread)
            ax.scatter(x,y,s=10,color=colors[i],zorder=5)            
    ax.set_xlabel('Group')
    ax.set_xticklabels(groups)
    ax.set_xticks(range(len(groups)))
    labels = {'pellets':'Pellets', 'pokes':'Correct Pokes',}
    ax.set_ylabel(labels[break_style]) 
    ax.set_title(title)
    plt.tight_layout()
    
    return fig

#---Circadian Plots
    
def daynight_plot(FEDs, groups, circ_value, lights_on, lights_off, circ_error,
                  circ_show_indvl, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    fig, ax = plt.subplots(figsize=(5,5), dpi=125)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    bar_width = (.7/len(groups))
    bar_offsets = np.array([bar_width*i for i in range(len(groups))])
    for i, group in enumerate(groups):
        group_day_values = []
        group_night_values = []
        for fed in FEDs:
            if group in fed.group:
                df = fed.data
                nights = night_intervals(df.index, lights_on, lights_off)
                days = night_intervals(df.index, lights_on, lights_off, 
                                       instead_days=True)
                day_vals = []
                night_vals = []
                for start, end in days:
                    day_slice = df[(df.index>start) & (df.index<end)].copy()
                    day_vals.append(resample_get_yvals(day_slice,circ_value))
                for start, end in nights:
                    night_slice = df[(df.index>start) & (df.index<end)].copy()
                    night_vals.append(resample_get_yvals(night_slice,circ_value))
                group_day_values.append(np.nanmean(day_vals))
                group_night_values.append(np.nanmean(night_vals))
        group_day_mean = np.nanmean(group_day_values)
        group_night_mean = np.nanmean(group_night_values)
        if circ_error == 'None':
            circ_error = None
            error_bar_day = None
            error_bar_night = None
        elif circ_error == 'SEM':
            error_bar_day = stats.sem(group_day_values,nan_policy='omit')
            error_bar_night = stats.sem(group_night_values,nan_policy='omit')
        elif circ_error == 'STD':
            error_bar_day = np.nanstd(group_day_values)
            error_bar_night = np.nanstd(group_night_values)       
        x1 = 1
        x2 = 2
        y1 = group_day_mean
        y2 = group_night_mean
        bar_width = (.7 / len(groups))
        ax.bar(x1+bar_offsets[i], y1, width=bar_width, color=colors[i],
                yerr=error_bar_day,label=group,capsize=3,alpha=.5,
                ecolor='gray')
        ax.bar(x2+bar_offsets[i], y2, width=bar_width, color=colors[i],
                yerr=error_bar_night, capsize=3, alpha=.5, ecolor='gray')
        ax.errorbar(x1+bar_offsets[i], y1, fmt='none', yerr=error_bar_day,
                    capsize=3,ecolor='gray', zorder=3)
        ax.errorbar(x2+bar_offsets[i], y2, fmt='none', yerr=error_bar_night,
                    capsize=3,ecolor='gray',zorder=3)
        if error_bar_day != None:
            ax.plot([],[],'',color='gray',label=i*'_' + circ_error)
        if circ_show_indvl:
            spread = .2 * bar_width
            dayx, dayy = raw_data_scatter(group_day_values,
                                          xcenter=x1+bar_offsets[i],
                                          spread=spread)
            nightx, nighty = raw_data_scatter(group_night_values,
                                              xcenter=x2+bar_offsets[i],
                                              spread=spread)
            ax.scatter(dayx,dayy,s=10,color=colors[i],zorder=5)
            ax.scatter(nightx,nighty,s=10,color=colors[i],zorder=5)
    ax.set_xticks([np.nanmean(bar_offsets + x1),(np.nanmean(bar_offsets + x2))])
    ax.set_xticklabels(['Day', 'Night'])
    ax.set_ylabel(circ_value.capitalize())
    ax.set_title(circ_value.capitalize() + ' by Time of Day')
    if "%" in circ_value:
            ax.set_ylim(0,100)
    handles, labels = ax.get_legend_handles_labels()
    if circ_error in labels:
        handles.append(handles.pop(labels.index(circ_error)))
        labels.append(labels.pop(labels.index(circ_error)))        
    ax.legend(handles, labels, bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()
    
    return fig

def line_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark,
                    lights_on, lights_off, *args, **kwargs):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if circ_show_indvl:
        circ_error = "None"
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, group in enumerate(groups):
        group_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                byhour = df.groupby([df.index.hour])
                byhour = byhour.apply(resample_get_yvals,value=circ_value)
                new_index = list(range(lights_on, 24)) + list(range(0,lights_on))
                reindexed = byhour.reindex(new_index)
                reindexed.index.name = 'hour'
                if circ_value in ['pellets', 'correct pokes','errors']:
                    reindexed = reindexed.fillna(0)
                y = reindexed
                x = range(0,24)
                if circ_show_indvl:
                    ax.plot(x,y,color=colors[i],alpha=.3,linewidth=.8)
                group_vals.append(y)
        group_mean = np.nanmean(group_vals, axis=0)    
        label = group       
        error_shade = np.nan
        if circ_error == "SEM":
            error_shade = stats.sem(group_vals, axis=0,nan_policy='omit')
            label += ' (±' + circ_error + ')'
        elif circ_error == 'STD':
            error_shade = np.nanstd(group_vals, axis=0)
            label += ' (±' + circ_error + ')'
        if circ_show_indvl:
            error_shade = np.nan
        if "%" in circ_value:
            ax.set_ylim(0,100)
        x = range(24)
        y = group_mean
        ax.plot(x,y,color=colors[i], label=label)
        ax.fill_between(x, y-error_shade, y+error_shade, color=colors[i],
                        alpha=.3)
    ax.set_xlabel('Hours (since start of light cycle)')
    ax.set_xticks([0,6,12,18,24])
    ax.set_ylabel(circ_value)
    ax.set_title('Chronogram')
    if shade_dark:
        off = new_index.index(lights_off)
        ax.axvspan(off,24,color='gray',alpha=.2,zorder=0,label='lights off')
    ax.legend(bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()
        
    return fig

def heatmap_chronogram(FEDs, circ_value, lights_on, *args, **kwargs):
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    matrix = []
    index = []
    for FED in FEDs:       
        df = FED.data
        byhour = df.groupby([df.index.hour])
        byhour = byhour.apply(resample_get_yvals,value=circ_value)
        new_index = list(range(lights_on, 24)) + list(range(0,lights_on))
        reindexed = byhour.reindex(new_index)
        if circ_value in ['pellets', 'correct pokes','errors']:
            reindexed = reindexed.fillna(0)
        matrix.append(reindexed)
        index.append(FED.filename)
    matrix = pd.DataFrame(matrix, index=index)
    avg = matrix.mean(axis=0)
    avg = avg.rename('Average')
    matrix = matrix.append(avg)
    if '%' in circ_value:
        vmin, vmax = 0, 100
    else:
        vmin, vmax = None, None
    im = ax.imshow(matrix, cmap='jet', aspect='auto', vmin=vmin, vmax=vmax)
    ax.set_title('Chronogram of ' + circ_value.capitalize())
    ax.set_ylabel('File')
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.get_yticklabels()[-1].set_weight('bold')
    ax.set_xlabel('Hours (since start of light cycle)')
    ax.set_xticks([0,6,12,18,])
    plt.colorbar(im)
    plt.tight_layout()
    
    return fig

#---Other Plots

def diagnostic_plot(FED, shade_dark, lights_on, lights_off, *args, **kwargs):
    assert isinstance(FED, FED3_File),'Non FED3_File passed to diagnostic_plot()'
    df = FED.data
    
    fig, (ax1,ax2,ax3) = plt.subplots(3,1,figsize=(7,5),sharex=True, dpi=125)
    plt.subplots_adjust(hspace=.1)
    x = df.index
    y = df['Pellet_Count']
    ax1.scatter(x,y,s=1,c='green')
    ax1.set_ylabel('Cumulative Pellets')
    
    x = df.index
    y = df['Motor_Turns']
    ax2.scatter(x,y,s=3,c=y,cmap='cool',vmax=100)
    ax2.set_ylabel('Motor Turns')
    if max(y) < 100:
        ax2.set_ylim(0,100)
    
    x = df.index
    y = df['Battery_Voltage']
    ax3.plot(x,y,c='orange')
    ax3.set_ylabel('Battery (V)')  
    ax3.set_ylim(0,4.5)
    date_format_x(ax3, x[0], x[-1])
    ax3.set_xlabel('Date')
    plt.suptitle('Pellets Received, Motor Turns, and Battery Life\n' +
                 'for ' + FED.filename, y=.96)
    if shade_dark:
        for i,ax in enumerate((ax1,ax2,ax3)):
            shade_darkness(ax, FED.start_time, FED.end_time,
                       lights_on=lights_on,
                       lights_off=lights_off)
    
    return fig