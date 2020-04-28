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
    for i, interval in enumerate(nights):
        start = interval[0]
        end = interval[1]
        ax.axvspan(start,
                   end,
                   color='gray',
                   alpha=.2,
                   label='_'*i + 'lights off')

def dn_get_yvals(value, df):
    possible = ['pellets','retrieval time','interpellet intervals',
                'correct pokes','errors','correct pokes (%)','errors (%)']
    assert value in possible, 'Value not understood by daynight plot: ' + value
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
            output = (list(df['Correct_Poke']).count(True) / len(df.index)) * 100
        except ZeroDivisionError:
            output = np.nan
    elif value == 'errors (%)':
        try:
            output = (list(df['Correct_Poke']).count(False) / len(df.index)) * 100
        except ZeroDivisionError:
            output = np.nan
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

#---PLOT FUNCTIONS

def pellet_plot_single(FED, shade_dark, lights_on, lights_off, pellet_color,
                       *args, **kwargs):
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_plot_single()'   
    fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    df = FED.data
    x = df.index.values
    y = df['Pellet_Count']
    ax.plot(x, y,color=pellet_color)
    days = mdates.DayLocator()
    hours = mdates.HourLocator(byhour=[0,6,12,18])
    xfmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.set_minor_locator(hours)
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
    x = df.index.values
    y = df['Binary_Pellets']    
    ax.bar(x, y,width=(x[1]-x[0]),
           align='edge', alpha=.8, color=pellet_color)
    ax.set_xlabel('Time')
    days = mdates.DayLocator()
    hours = mdates.HourLocator(byhour=[0,6,12,18])
    xfmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.set_minor_locator(hours)
    ax.set_ylabel('Pellets') 
    title = ('Pellets Retrieved for FED ' + FED.filename)
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax, min(x), max(x),
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
    days_in_hours = [24*day for day in range(number_of_days+1)]
    ax.set_xticks(days_in_hours)
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
        x = df.index.values
        y = df['Pellet_Count']
        ax.plot(x, y, label=file.filename)
        if max(x) > max_date:
            max_date = max(x)
        if min(x) < min_date:
            min_date = min(x)
    ax.set_xlabel('Time (h)')
    xfmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(xfmt)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    fontsize = 20/len(ax.xaxis.get_majorticklabels())
    if fontsize < 6:
        fontsize=6
    plt.setp(ax.xaxis.get_majorticklabels(), 
             fontsize=fontsize)
    plt.setp(ax.xaxis.get_majorticklabels(), ha='right')
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
        for i, date in enumerate(df.index.values):
            times.append(date - df.index.values[0])
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
        x = df.index.values
        y = df['Binary_Pellets']
        ax.bar(x, y, label=file.filename,
               alpha=.8,align='edge',width=(x[1]-x[0]))           
        if max(x) > max_date:
            max_date = max(x)
        if min(x) < min_date:
            min_date = min(x)      
    ax.set_xlabel('Time')
    xfmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(xfmt)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    fontsize = 20/len(ax.xaxis.get_majorticklabels())
    if fontsize < 6:
        fontsize=6
    plt.setp(ax.xaxis.get_majorticklabels(), 
             fontsize=fontsize)
    plt.setp(ax.xaxis.get_majorticklabels(), ha='right')
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

def pellet_plot_average(FEDs, groups, average_bins, average_error, shade_dark,
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
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data.resample(average_bins,base=0).sum()
                df = df[(df.index > latest_start) &
                        (df.index < earliest_end)].copy()
                avg.append(df['Binary_Pellets'])
                if show_indvl:
                    x = df.index
                    y = df['Binary_Pellets']
                    ax.plot(x, y, color=colors[i], alpha=.3, linewidth=.8)
                    
        group_avg = np.mean(avg, axis=0)        
        if average_error == 'None':
            label = group
        else:
            label = group + ' (±' + average_error + ')'
        x = df.index
        y = group_avg
        ax.plot(x, y, label=label, color=colors[i])
        if average_error != 'None':
            if average_error == 'STD':
                error_shade = np.std(avg, axis=0)
            elif average_error == 'SEM':
                error_shade = stats.sem(avg, axis=0)         
            ax.fill_between(df.index,
                            group_avg+error_shade,
                            group_avg-error_shade,
                            alpha = .3,
                            color=colors[i]) 
    ax.set_xlabel('Time')
    days = mdates.DayLocator()
    xfmt = mdates.DateFormatter('%b %d')
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(xfmt)
    ax.set_ylabel('Pellets')
    ax.set_title('Average Pellet Plot')
    if shade_dark:
        shade_darkness(ax, latest_start, earliest_end,
                       lights_on=lights_on,
                       lights_off=lights_off)       
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')    
    plt.tight_layout() 
    
    return fig

def pellet_plot_aligned_average(FEDs, groups, average_bins, average_align_start,
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
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data.resample(average_bins,base=average_align_start).sum()
                first_entry = df.index[0]
                aligned_first_entry = dt.datetime(year=1970,month=1,day=1,
                                                  hour=first_entry.hour)
                alignment_shift = first_entry - aligned_first_entry
                df.index = [i-alignment_shift for i in df.index]
                df = df.reindex(date_range)
                avg.append(df['Binary_Pellets'])
                if show_indvl:
                    x = df.index
                    y = df['Binary_Pellets']
                    ax.plot(x, y, color=colors[i], alpha=.3, linewidth=.8)
                    
        group_avg = np.mean(avg, axis=0)
        if average_error == 'None':
            label = group
        else:
            label = group + ' (±' + average_error + ')'
        x = df.index
        y = group_avg
        ax.plot(x, y, label=label, color=colors[i])
        if average_error != 'None':
            if average_error == 'STD':
                error_shade = np.std(avg, axis=0)
            elif average_error == 'SEM':
                error_shade = stats.sem(avg, axis=0)         
            ax.fill_between(df.index,
                            group_avg+error_shade,
                            group_avg-error_shade,
                            alpha = .3,
                            color=colors[i])
    if shade_dark:
        shade_darkness(ax, start_datetime, end_datetime,
                       lights_on=lights_on,
                       lights_off=lights_off,
                       convert=False)
    hours_start = start_datetime.strftime('%I%p').replace('0','')
    ax.set_xlabel('Hours since ' + hours_start + ' on first day')
    ticks = pd.date_range(start_datetime,end_datetime,freq='12H')
    tick_labels = [i*12 for i in range(len(ticks))]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels)
    ax.set_xlim(start_datetime,end_datetime + dt.timedelta(hours=5))
    ax.set_ylabel('Pellets')   
    ax.set_title('Average Pellet Plot')
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout() 
    
    return fig

def diagnostic_plot(FED, shade_dark, lights_on, lights_off, *args, **kwargs):
    assert isinstance(FED, FED3_File),'Non FED3_File passed to diagnostic_plot()'
    df = FED.data
    hours = mdates.HourLocator(byhour=[0,6,12,18])
    days  = mdates.DayLocator()
    xfmt = mdates.DateFormatter('%b %d')
    
    fig, (ax1,ax2,ax3) = plt.subplots(3,1,figsize=(7,5),sharex=True, dpi=125)
    plt.subplots_adjust(hspace=.1)
    x = df.index.values
    y = df['Pellet_Count']
    ax1.scatter(x,y,s=1,c='green')
    ax1.set_ylabel('Cumulative Pellets')
    
    x = df.index.values
    y = df['Motor_Turns']
    ax2.scatter(x,y,s=3,c=y,cmap='cool',vmax=100)
    ax2.set_ylabel('Motor Turns')
    if max(y) < 100:
        ax2.set_ylim(0,100)
    
    x = df.index.values
    y = df['Battery_Voltage']
    ax3.plot(x,y,c='orange')
    ax3.set_ylabel('Battery (V)')  
    ax3.set_ylim(0,4.5)
    ax3.set_xlim(min(x),max(x))
    ax3.xaxis.set_major_locator(days)
    ax3.xaxis.set_major_formatter(xfmt)
    ax3.xaxis.set_minor_locator(hours)
    ax3.set_xlabel('Date')
    plt.suptitle('Pellets Received, Motor Turns, and Battery Life\n' +
                 'for ' + FED.filename, y=.96)
    if shade_dark:
        for i,ax in enumerate((ax1,ax2,ax3)):
            shade_darkness(ax, FED.start_time, FED.end_time,
                       lights_on=lights_on,
                       lights_off=lights_off)
    
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
    
def daynight_plot(FEDs, groups, dn_value, lights_on, lights_off, dn_error,
                  dn_show_indvl, *args, **kwargs):
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
                    day_vals.append(dn_get_yvals(dn_value,day_slice))
                for start, end in nights:
                    night_slice = df[(df.index>start) & (df.index<end)].copy()
                    night_vals.append(dn_get_yvals(dn_value,night_slice))
                group_day_values.append(np.mean(day_vals))
                group_night_values.append(np.mean(night_vals))
        group_day_mean = np.nanmean(group_day_values)
        group_night_mean = np.nanmean(group_night_values)
        if dn_error == 'None':
            dn_error = None
            error_bar_day = None
            error_bar_night = None
        elif dn_error == 'SEM':
            error_bar_day = stats.sem(group_day_values)
            error_bar_night = stats.sem(group_night_values)
        elif dn_error == 'STD':
            error_bar_day = np.std(group_day_values)
            error_bar_night = np.std(group_night_values)       
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
            ax.plot([],[],'',color='gray',label=i*'_' + dn_error)
        if dn_show_indvl:
            spread = .2 * bar_width
            dayx, dayy = raw_data_scatter(group_day_values,
                                          xcenter=x1+bar_offsets[i],
                                          spread=spread)
            nightx, nighty = raw_data_scatter(group_night_values,
                                              xcenter=x2+bar_offsets[i],
                                              spread=spread)
            ax.scatter(dayx,dayy,s=10,color=colors[i],zorder=5)
            ax.scatter(nightx,nighty,s=10,color=colors[i],zorder=5)
    ax.set_xticks([np.mean(bar_offsets + x1),(np.mean(bar_offsets + x2))])
    ax.set_xticklabels(['Day', 'Night'])
    ax.set_ylabel(dn_value.capitalize())
    ax.set_title(dn_value.capitalize() + ' by Time of Day')
    handles, labels = ax.get_legend_handles_labels()
    if dn_error in labels:
        handles.append(handles.pop(labels.index(dn_error)))
        labels.append(labels.pop(labels.index(dn_error)))        
    ax.legend(handles, labels, bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()
    
    return fig