# -*- coding: utf-8 -*-
"""
Module for returning the data associated with each plot in FED3 Viz.
Has one "getdata" function for each "plots" function

@author: https://github.com/earnestt1234
"""
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from scipy import stats

from plots.plots import dn_get_yvals, night_intervals, poke_resample_func

def pellet_plot_single(FED,*args, **kwargs):
    df = FED.data
    x = df.index.values
    y = df['Pellet_Count']
    output = pd.DataFrame(y, index=x)
    return output

def pellet_freq_single(FED, pellet_bins,*args, **kwargs):
    df = FED.data.resample(pellet_bins).sum()
    x = df.index.values
    y = df['Binary_Pellets']
    output=pd.DataFrame(y,index=x)
    output.index.name = 'Time'
    return output

def pellet_plot_multi_aligned(FEDs,*args,**kwargs):
    df_list = []
    for file in FEDs:
        df = file.data
        x = [(time.total_seconds()/3600) for time in df['Elapsed_Time']]
        y = list(df['Pellet_Count'])
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Elapsed Hours'
    return output

def pellet_plot_multi_unaligned(FEDs,*args,**kwargs):
    df_list = []
    for file in FEDs:
        df = file.data
        x = df.index.values
        y = list(df['Pellet_Count'])
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Time'
    return output        

def pellet_freq_multi_aligned(FEDs, pellet_bins, *args,**kwargs):
    df_list = []
    for file in FEDs:
        df = file.data.resample(pellet_bins,base=0).sum()
        x = []
        for i, date in enumerate(df.index.values):
            x.append(date - df.index.values[0])
        x = [(time/np.timedelta64(1,'h')) for time in x]
        y = list(df['Binary_Pellets'])
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Elapsed Hours'
    return output    

def pellet_freq_multi_unaligned(FEDs, pellet_bins, *args,**kwargs):
    df_list = []
    for file in FEDs:
        df = file.data.resample(pellet_bins,base=0).sum()
        x = df.index.values
        y = list(df['Binary_Pellets'])
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Time'
    return output

def pellet_plot_average(FEDs, groups, average_bins, 
                        average_error, *args, **kwargs):
    output = pd.DataFrame()
    group_avg_df = pd.DataFrame()
    earliest_end = dt.datetime(2999,1,1,0,0,0)
    latest_start = dt.datetime(1970,1,1,0,0,0)
    for file in FEDs:
        df = file.data
        if min(df.index) > latest_start:
            latest_start = min(df.index)
        if max(df.index) < earliest_end:
            earliest_end = max(df.index)
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data.resample(average_bins,base=0).sum()
                df = df[(df.index > latest_start) &
                        (df.index < earliest_end)].copy()
                avg.append(df['Binary_Pellets'])
                if file.basename not in output.columns:
                    indvl_line = pd.DataFrame({file.basename:df['Binary_Pellets']},
                                              index=df.index)
                    output = output.join(indvl_line, how='outer')                     
        group_avg = np.mean(avg, axis=0)
        group_to_add = pd.DataFrame({group:group_avg}, index=df.index)
        if average_error == 'SEM':
            group_to_add[group + ' SEM'] = stats.sem(avg, axis=0)
        if average_error == 'STD':
            group_to_add[group + ' STD'] = np.std(avg, axis=0)
        group_avg_df = group_avg_df.join(group_to_add, how='outer')
    output = output.join(group_avg_df)
    output.index.name = 'Time'
    return output

def pellet_plot_aligned_average(FEDs, groups, average_bins, average_align_start,
                                average_align_days, average_error, *args, 
                                **kwargs):
    output = pd.DataFrame()
    group_avg_df = pd.DataFrame()
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
                if file.basename not in output.columns:
                    indvl_line = pd.DataFrame({file.basename:df['Binary_Pellets']},
                                              index=df.index)
                    output = output.join(indvl_line, how='outer')
                    
        group_avg = np.mean(avg, axis=0)
        group_to_add = pd.DataFrame({group:group_avg}, index=df.index)
        if average_error == 'SEM':
            group_to_add[group + ' SEM'] = stats.sem(avg, axis=0)
        if average_error == 'STD':
            group_to_add[group + ' STD'] = np.std(avg, axis=0)
        group_avg_df = group_avg_df.join(group_to_add, how='outer')
    output = output.join(group_avg_df)
    hours_since_start = [(i - output.index[0]).total_seconds()/3600
                         for i in output.index]
    output.index = hours_since_start
    output.index.name = 'Elapsed Hours'
    return output

def diagnostic_plot(FED, *args, **kwargs):
    df = FED.data
    dic = {'Pellets':df['Pellet_Count'],
           'Motor Turns':df['Motor_Turns'],
           'Battery (V)':df['Battery_Voltage']}
    output = pd.DataFrame(dic, index=df.index)
    output.index.name = 'Time'
    return output

def interpellet_interval_plot(FEDs, kde, *args, **kwargs):
    kde_output = pd.DataFrame()
    bar_output = pd.DataFrame()
    lowest = -2
    highest = 5
    c=0
    bins = []
    while c <= highest:
        bins.append(lowest+c)
        c+=0.1
    for FED in FEDs:
        fig = plt.figure() #made to not disrupt fig in app
        plt.clf()
        df = FED.data
        y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
        y = [np.log10(val) for val in y if not pd.isna(val)]
        plot = sns.distplot(y,bins=bins,label=FED.basename,kde=kde,
                            norm_hist=False)
        if kde:
            kde = plot.get_lines()[0].get_data()
            kde_dic = {FED.basename:kde[1]}
            kde_df = pd.DataFrame(kde_dic, index=kde[0])  
            kde_output = kde_output.join(kde_df, how='outer')
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {FED.basename:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        bar_output = bar_output.join(bar_df, how='outer')
        plt.close()      
    kde_output.index.name = 'log10(minutes)'
    bar_output.index.name = 'log10(minutes)'
    return kde_output, bar_output       

def daynight_plot(FEDs, groups, dn_value, lights_on, lights_off, dn_error,
                  *args, **kwargs):
    output = pd.DataFrame()
    group_avg_df = pd.DataFrame()
    used = []
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
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
                if fed.basename not in used:
                    f = fed.basename
                    output.loc[dn_value,f+' day'] = np.mean(day_vals)
                    output.loc[dn_value,f+' night'] = np.mean(night_vals)  
                    used.append(fed.basename)
        group_day_mean = np.nanmean(group_day_values)
        group_night_mean = np.nanmean(group_night_values)
        group_avg_df.loc[dn_value,group+' day'] = group_day_mean
        group_avg_df.loc[dn_value,group+' night'] = group_night_mean
        if dn_error == 'SEM':
            group_avg_df.loc[dn_value,group+' day SEM'] = stats.sem(group_day_values)
            group_avg_df.loc[dn_value,group+' night SEM']= stats.sem(group_night_values)
        if dn_error == 'STD':
            group_avg_df.loc[dn_value,group+' day STD'] = np.std(group_day_values)
            group_avg_df.loc[dn_value,group+' night STD'] = np.std(group_night_values)       
    output = output.merge(group_avg_df, left_index=True, right_index=True)
    return output

def poke_plot(FED, poke_bins, poke_show_correct, poke_show_error, poke_percent,
              *args, **kwargs):
    output=pd.DataFrame()
    resampled = FED.data['Correct_Poke'].dropna().resample(poke_bins)
    if poke_show_correct:
        y = resampled.apply(poke_resample_func, val=True, as_percent=poke_percent)
        y = y.rename('Correct Pokes')
        x = y.index
        temp = pd.DataFrame(y, index=x,)
        output = output.join(temp, how='outer')
    if poke_show_error:
        y = resampled.apply(poke_resample_func, val=False, as_percent=poke_percent)
        y = y.rename('Incorrect Pokes')
        x = y.index
        temp = pd.DataFrame(y, index=x,)
        output = output.join(temp, how='outer')
    return output

def poke_bias(FED, poke_bins, bias_style, *args, **kwargs):
    if bias_style == 'correct - error':
        resampled = FED.data['Correct_Poke'].dropna().resample(poke_bins)
        y = resampled.apply(lambda b: (b==True).sum() - (b==False).sum())
    elif bias_style == 'left - right':
        resampled = FED.data[['Binary_Left_Pokes',
                              'Binary_Right_Pokes']].resample(poke_bins).sum()
        y = resampled['Binary_Left_Pokes'] - resampled['Binary_Right_Pokes']
    y = y.rename('Poke Bias (' + bias_style + ')')
    x = y.index
    output = pd.DataFrame(y, index=x)
    return output