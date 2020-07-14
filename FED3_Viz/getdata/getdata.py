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

from plots.plots import (resample_get_yvals, night_intervals, left_right_bias,
                         left_right_noncumulative, label_meals,
                         get_daynight_count)

def pellet_plot_single(FED,*args, **kwargs):
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    x = df.index.values
    y = df['Pellet_Count']
    y = y.rename('Pellets')
    output = pd.DataFrame(y, index=x)
    return output

def pellet_freq_single(FED, pellet_bins,*args, **kwargs):
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    df = df.resample(pellet_bins).sum()
    x = df.index.values
    y = df['Binary_Pellets']
    y = y.rename('Pellets')
    output=pd.DataFrame(y,index=x)
    output.index.name = 'Time'
    return output

def pellet_plot_multi_aligned(FEDs,*args,**kwargs):
    df_list = []
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
            df['Elapsed_Time'] -= df['Elapsed_Time'][0]
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
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
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
        df = file.data
        if 'date_filter' in kwargs:         
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        df = df.resample(pellet_bins,base=0).sum()
        x = []
        for i, date in enumerate(df.index.values):
            x.append(date - df.index[0])
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
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        df = df.resample(pellet_bins,base=0).sum()
        x = df.index.values
        y = list(df['Binary_Pellets'])
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Time'
    return output

def average_plot_ondatetime(FEDs, groups, dependent, average_bins, 
                            average_error, *args, **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    output = pd.DataFrame()
    group_avg_df = pd.DataFrame()
    earliest_end = dt.datetime(2999,1,1,0,0,0)
    latest_start = dt.datetime(1970,1,1,0,0,0)
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        if min(df.index) > latest_start:
            latest_start = min(df.index)
        if max(df.index) < earliest_end:
            earliest_end = max(df.index)
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                if dependent == 'poke bias (left %)':
                    y = left_right_bias(df, average_bins, version='ondatetime')
                elif dependent == 'left pokes':
                    y = left_right_noncumulative(df,average_bins,side='l',version='ondatetime')
                elif dependent == 'right pokes':
                    y = left_right_noncumulative(df,average_bins,side='r',version='ondatetime')
                else:
                    df = df.groupby(pd.Grouper(freq=average_bins,base=0))
                    y = df.apply(resample_get_yvals,dependent, retrieval_threshold)
                    y = y[(y.index > latest_start) &
                          (y.index < earliest_end)].copy()
                avg.append(y)
                if file.basename not in output.columns:
                    indvl_line = pd.DataFrame({file.basename:y},
                                              index=y.index)
                    output = output.join(indvl_line, how='outer')                     
        group_avg = np.nanmean(avg, axis=0)
        group_to_add = pd.DataFrame({group:group_avg}, index=y.index)
        if average_error == 'SEM':
            group_to_add[group + ' SEM'] = stats.sem(avg, axis=0,nan_policy='omit')
        if average_error == 'STD':
            group_to_add[group + ' STD'] = np.nanstd(avg, axis=0)
        group_avg_df = group_avg_df.join(group_to_add, how='outer')
    output = output.join(group_avg_df)
    output.index.name = 'Time'
    return output

def average_plot_ontime(FEDs, groups, dependent, average_bins, average_align_start,
                        average_align_days, average_error, *args, 
                        **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
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
                df = file.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                if dependent == 'poke bias (left %)':
                    y = left_right_bias(df, average_bins, version='ontime',
                                        starttime=average_align_start)
                elif dependent == 'left pokes':
                    y = left_right_noncumulative(df,average_bins,side='l',version='ontime', 
                                                 starttime=average_align_start)
                elif dependent == 'right pokes':
                    y = left_right_noncumulative(df,average_bins,side='r',version='ontime',
                                                 starttime=average_align_start)
                else:
                    df = df.groupby(pd.Grouper(freq=average_bins,base=average_align_start))
                    y = df.apply(resample_get_yvals, dependent, retrieval_threshold)
                first_entry = y.index[0]
                aligned_first_entry = dt.datetime(year=1970,month=1,day=1,
                                                  hour=first_entry.hour)
                alignment_shift = first_entry - aligned_first_entry
                y.index = [i-alignment_shift for i in y.index]
                y = y.reindex(date_range)
                avg.append(y)
                if file.basename not in output.columns:
                    indvl_line = pd.DataFrame({file.basename:y},
                                              index=y.index)
                    output = output.join(indvl_line, how='outer')
                    
        group_avg = np.nanmean(avg, axis=0)
        group_to_add = pd.DataFrame({group:group_avg}, index=y.index)
        if average_error == 'SEM':
            group_to_add[group + ' SEM'] = stats.sem(avg, axis=0,nan_policy='omit')
        if average_error == 'STD':
            group_to_add[group + ' STD'] = np.nanstd(avg, axis=0)
        group_avg_df = group_avg_df.join(group_to_add, how='outer')
    output = output.join(group_avg_df)
    hours_since_start = [(i - output.index[0]).total_seconds()/3600
                         for i in output.index]
    output.index = hours_since_start
    output.index.name = 'Elapsed Hours (since ' + str(average_align_start) + ':00)' 
    return output

def average_plot_onstart(FEDs, groups, dependent, average_bins, average_error,
                         *args, **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    output = pd.DataFrame()
    group_avgs = pd.DataFrame()
    longest_index = []
    for file in FEDs:
        df = file.data
        resampled = df.resample(average_bins, base=0, on='Elapsed_Time').sum()
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
            df['Elapsed_Time'] -= df['Elapsed_Time'][0]
            resampled = df.resample(average_bins, base=0, on='Elapsed_Time').sum()
        if len(longest_index) == 0:
            longest_index = resampled.index
        elif len(resampled.index) > len(longest_index):
            longest_index = resampled.index
    for i, group in enumerate(groups):
        avg = []
        for file in FEDs:
            if group in file.group:
                df = file.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                    df['Elapsed_Time'] -= df['Elapsed_Time'][0]
                if dependent == 'poke bias (left %)':
                    y = left_right_bias(df, average_bins, version='onstart')
                elif dependent == 'left pokes':
                    y = left_right_noncumulative(df,average_bins,side='l',version='onstart')
                elif dependent == 'right pokes':
                    y = left_right_noncumulative(df,average_bins,side='r',version='onstart')
                else:
                    df = df.groupby(pd.Grouper(key='Elapsed_Time',freq=average_bins,
                                                  base=0))
                    y = df.apply(resample_get_yvals, dependent, retrieval_threshold)
                y = y.reindex(longest_index)           
                y.index = [time.total_seconds()/3600 for time in y.index]
                avg.append(y)
                if file.basename not in output.columns:
                    indvl = pd.DataFrame({file.basename:y},
                                         index=y.index)
                    output = output.join(indvl, how='outer')
        group_avg = np.nanmean(avg, axis=0)
        group_to_add = pd.DataFrame({group:group_avg}, index=y.index)
        if average_error == 'SEM':
            group_to_add[group + ' SEM'] = stats.sem(avg, axis=0,nan_policy='omit')
        if average_error == 'STD':
            group_to_add[group + ' STD'] = np.nanstd(avg, axis=0)
        group_avgs = group_avgs.join(group_to_add, how='outer')
    output = output.join(group_avgs)
    output.index.name = 'Elapsed Hours'
    return output



def interpellet_interval_plot(FEDs, kde, logx, *args, **kwargs):
    kde_output = pd.DataFrame()
    bar_output = pd.DataFrame()
    bins = []
    if logx:
        lowest = -2
        highest = 5
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        div = 900/50
        bins = [i*div for i in range(50)]
    for FED in FEDs:
        fig = plt.figure() #made to not disrupt fig in app
        plt.clf()
        df = FED.data
        y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
        if logx:
            y = [np.log10(val) for val in y if not pd.isna(val)]
        plot = sns.distplot(y,bins=bins,label=FED.basename,kde=kde,
                            norm_hist=False)
        if kde:
            if plot.get_lines():
                kde = plot.get_lines()[0].get_data()
                kde_dic = {FED.basename:kde[1]}
                kde_df = pd.DataFrame(kde_dic, index=kde[0])
                kde_output = kde_output.join(kde_df, how='outer')
            else:
                kde_output[FED.basename] = np.nan                 
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {FED.basename:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        bar_output = bar_output.join(bar_df, how='outer')
        plt.close()      
    kde_output.index.name = 'log10(minutes)' if logx else 'minutes'
    bar_output.index.name = 'log10(minutes)' if logx else 'minutes'
    return kde_output, bar_output       

def group_interpellet_interval_plot(FEDs, groups, kde, logx, *args, **kwargs):
    kde_output = pd.DataFrame()
    bar_output = pd.DataFrame()
    bins = []
    if logx:
        lowest = -2
        highest = 5
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        div = 900/50
        bins = [i*div for i in range(50)]
    for group in groups:
        #made to not disrupt fig in app            
        fig = plt.figure()
        plt.clf()
        all_vals = []
        for FED in FEDs:
            if group in FED.group:             
                df = FED.data
                y = list(df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0])
                if logx:
                    y = [np.log10(val) for val in y if not pd.isna(val)]
                all_vals += y
        plot = sns.distplot(all_vals,bins=bins,label=group,kde=kde,
                            norm_hist=False)
        if kde:
            if plot.get_lines():
                kde = plot.get_lines()[0].get_data()
                kde_dic = {group:kde[1]}
                kde_df = pd.DataFrame(kde_dic, index=kde[0])
                kde_output = kde_output.join(kde_df, how='outer')
            else:
                kde_output[group] = np.nan
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {group:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        bar_output = bar_output.join(bar_df, how='outer')
        plt.close()
    kde_output.index.name = 'log10(minutes)' if logx else 'minutes'
    bar_output.index.name = 'log10(minutes)' if logx else 'minutes'
    return kde_output, bar_output

def meal_size_histogram(FEDs, meal_pellet_minimum, meal_duration,
                        norm_meals, **kwargs):
    output = pd.DataFrame()
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    sizes = []
    for fed in FEDs:
        df = fed.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        meals = label_meals(df['Interpellet_Intervals'].dropna(),
                            meal_pellet_minimum=meal_pellet_minimum,
                            meal_duration=meal_duration)
        sizes.append(meals.value_counts())
    meal_maxes = [s.max() for s in sizes]
    longest_meal = max(meal_maxes) if meal_maxes else 5
    if pd.isna(longest_meal):
        longest_meal = 5
    bins = range(1,longest_meal+2)
    for series, fed in zip(sizes,FEDs):
        #made to not disrupt fig in app            
        fig = plt.figure()
        plt.clf()
        plot = sns.distplot(series,bins=bins,kde=False,label=fed.basename,
                            norm_hist=norm_meals,)
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {fed.filename:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        output = output.join(bar_df, how='outer')
        plt.close()
    return output

def grouped_meal_size_histogram(FEDs, groups, meal_pellet_minimum, meal_duration,
                                norm_meals, **kwargs):
    output = pd.DataFrame()
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    sizes = []
    for group in groups:
        fed_vals = []
        for fed in FEDs:
            if group in fed.group:
                df = fed.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                meals = label_meals(df['Interpellet_Intervals'].dropna(),
                                    meal_pellet_minimum=meal_pellet_minimum,
                                    meal_duration=meal_duration)
                fed_vals += list(meals.value_counts())
        sizes.append(fed_vals)
    meal_maxes = [np.nanmax(s) for s in sizes]
    longest_meal = max(meal_maxes) if meal_maxes else 5
    if pd.isna(longest_meal):
        longest_meal = 5
    bins = range(1,longest_meal+2)
    for series, group in zip(sizes,groups):
        #made to not disrupt fig in app            
        fig = plt.figure()
        plt.clf()
        plot = sns.distplot(series,bins=bins,kde=False,label=group,
                            norm_hist=norm_meals,)
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {group:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        output = output.join(bar_df, how='outer')
        plt.close()
    return output

def retrieval_time_single(FED, retrieval_threshold, **kwargs):
    output=pd.DataFrame()
    df = FED.data
    y1 = df['Pellet_Count'].copy()
    y2 = df['Retrieval_Time'].copy()
    if retrieval_threshold:
        y2.loc[y2>=retrieval_threshold] = np.nan
    y1[y2.isnull()] = np.nan
    output['Pellets'] = y1
    output['Retrieval Time'] = y2
    output=output.dropna()
    return output

def retrieval_time_multi(FEDs, retrieval_threshold, **kwargs):
    df_list = []
    for file in FEDs:
        df = file.data
        y = df['Retrieval_Time'].copy()
        if retrieval_threshold:
            y.loc[y>=retrieval_threshold] = np.nan
        x = [t.total_seconds()/3600 for t in df['Elapsed_Time']]
        y = list(y)
        dic = {file.basename:y}
        df_list.append(pd.DataFrame(dic, index=x))
    output = pd.DataFrame()
    for df in df_list:
        output = output.join(df, how='outer')
    output.index.name = 'Elapsed Hours'
    output = output.dropna(axis=0, how='all')
    return output 

def daynight_plot(FEDs, groups, circ_value, lights_on, lights_off, circ_error,
                  *args, **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
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
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                nights = night_intervals(df.index, lights_on, lights_off)
                days = night_intervals(df.index, lights_on, lights_off, 
                                       instead_days=True)
                durs = get_daynight_count(df.index[0], df.index[-1],
                                                lights_on, lights_off)
                days_completed = durs['day']
                nights_completed = durs['night']          
                day_vals = []
                night_vals = []
                for start, end in days:
                    day_slice = df[(df.index>start) & (df.index<end)].copy()
                    day_vals.append(resample_get_yvals(day_slice, circ_value,
                                                       retrieval_threshold))
                for start, end in nights:
                    night_slice = df[(df.index>start) & (df.index<end)].copy()
                    night_vals.append(resample_get_yvals(night_slice, circ_value,
                                                         retrieval_threshold))
                group_day_values.append(np.nansum(day_vals)/days_completed)
                group_night_values.append(np.nansum(night_vals)/nights_completed)
                if fed.basename not in used:
                    f = fed.basename
                    output.loc[circ_value,f+' day'] = np.nanmean(day_vals)
                    output.loc[circ_value,f+' night'] = np.nanmean(night_vals)  
                    used.append(fed.basename)
        group_day_mean = np.nanmean(group_day_values)
        group_night_mean = np.nanmean(group_night_values)
        group_avg_df.loc[circ_value,group+' day'] = group_day_mean
        group_avg_df.loc[circ_value,group+' night'] = group_night_mean
        if circ_error == 'SEM':
            group_avg_df.loc[circ_value,group+' day SEM'] = stats.sem(group_day_values,nan_policy='omit')
            group_avg_df.loc[circ_value,group+' night SEM']= stats.sem(group_night_values,nan_policy='omit')
        if circ_error == 'STD':
            group_avg_df.loc[circ_value,group+' day STD'] = np.nanstd(group_day_values)
            group_avg_df.loc[circ_value,group+' night STD'] = np.nanstd(group_night_values)       
    output = output.merge(group_avg_df, left_index=True, right_index=True)
    return output

def poke_plot(FED, poke_bins, poke_show_correct, poke_show_error, poke_show_left,
              poke_show_right, poke_style,
              *args, **kwargs):
    output=pd.DataFrame()
    df = FED.data
    offset_correct = 0
    offset_wrong = 0
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        base_df = df[(df.index) <= s].copy()
        df = df[(df.index >= s) &
                (df.index <= e)].copy()   
        base_correct = pd.Series([1 if i==True else np.nan
                                  for i in base_df['Correct_Poke']]).cumsum()
        base_wrong = pd.Series([1 if i==False else np.nan
                                for i in base_df['Correct_Poke']]).cumsum()
        offset_correct = base_correct.max()
        offset_wrong = base_wrong.max()
    if poke_style == 'Cumulative':
        pokes = df['Correct_Poke']
        if poke_show_correct:
            y = pd.Series([1 if i==True else np.nan for i in pokes]).cumsum()
            y = y.rename('Correct Pokes')
            y.index = df.index
            y = y.dropna()
            if not pd.isna(offset_correct):
                y += offset_correct
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_error:
            y = pd.Series([1 if i==False else np.nan for i in pokes]).cumsum()
            y = y.rename('Incorrect Pokes')
            y.index = df.index
            y = y.dropna()
            if not pd.isna(offset_wrong):
                y += offset_wrong
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_left:
            try:
                y = df[df['Event'] == 'Poke']['Left_Poke_Count']
            except:
                y = df['Left_Poke_Count']
            y = y.rename('Left Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_right:
            try:
                y = df[df['Event'] == 'Poke']['Right_Poke_Count']
            except:
                y = df['Right_Poke_Count']
            y = y.rename('Right Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
    else:
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
            df['Left_Poke_Count'] -= df['Left_Poke_Count'][0]
            df['Right_Poke_Count'] -= df['Right_Poke_Count'][0]
        resampled_correct = df['Correct_Poke'].dropna().resample(poke_bins)
        if poke_show_correct:
            y = resampled_correct.apply(lambda binn: (binn==True).sum())
            y = y.rename('Correct Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_error:
            y = resampled_correct.apply(lambda binn: (binn==False).sum())
            y = y.rename('Incorrect Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_left:
            y = left_right_noncumulative(df, bin_size=poke_bins,side='l')
            y = y.rename('Left Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
        if poke_show_right:
            y = left_right_noncumulative(df, bin_size=poke_bins,side='r')
            y = y.rename('Right Pokes')
            x = y.index
            temp = pd.DataFrame(y, index=x,)
            output = output.join(temp, how='outer')
    return output

def poke_bias(FED, poke_bins, bias_style, *args, **kwargs):
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    if bias_style == 'correct (%)':
        resampled = df.groupby(pd.Grouper(freq=poke_bins))
        y = resampled.apply(resample_get_yvals, 'poke bias (correct %)')
    elif bias_style == 'left (%)':
        y = left_right_bias(df, poke_bins)
    y = y.rename('Poke Bias (' + bias_style + ')')
    x = y.index
    output = pd.DataFrame(y, index=x)
    return output

def heatmap_chronogram(FEDs, circ_value, lights_on, *args, **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    matrix = []
    index = []
    for FED in FEDs:       
        df = FED.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        byhour = df.groupby([df.index.hour])
        byhour = byhour.apply(resample_get_yvals,circ_value,retrieval_threshold)
        byhourday = df.groupby([df.index.hour,df.index.date])
        num_days_by_hour = byhourday.sum().index.get_level_values(0).value_counts()
        byhour = byhour.divide(num_days_by_hour, axis=0)
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
    
    return matrix

def line_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark,
                    lights_on, lights_off, *args, **kwargs):
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    output = pd.DataFrame()
    avgs = pd.DataFrame()
    for i, group in enumerate(groups):
        group_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                byhour = df.groupby([df.index.hour])
                byhour = byhour.apply(resample_get_yvals,circ_value,retrieval_threshold)
                byhourday = df.groupby([df.index.hour,df.index.date])
                num_days_by_hour = byhourday.sum().index.get_level_values(0).value_counts()
                byhour = byhour.divide(num_days_by_hour, axis=0)
                new_index = list(range(lights_on, 24)) + list(range(0,lights_on))
                reindexed = byhour.reindex(new_index)
                if circ_value in ['pellets', 'correct pokes','errors']:
                    reindexed = reindexed.fillna(0)
                y = reindexed                
                group_vals.append(y)
                if FED.basename not in output.columns:
                    temp = pd.DataFrame({FED.basename:reindexed}, index=new_index)
                    output = output.join(temp, how='outer',)
        x = list(range(0,24))
        output.index = x
        group_mean = np.nanmean(group_vals, axis=0)    
        to_add = pd.DataFrame({group:group_mean})
        if circ_error == "SEM":
            to_add[group + " SEM"] = stats.sem(group_vals, axis=0,nan_policy='omit')
        elif circ_error == 'STD':
            to_add[group + " STD"] = np.nanstd(group_vals, axis=0)
        avgs = avgs.join(to_add, how='outer')
    output = output.join(avgs, how='outer')
    output.index.name = "Hours"
        
    return output

def day_night_ipi_plot(FEDs, kde, logx, lights_on, lights_off, **kwargs):
    kde_output = pd.DataFrame()
    bar_output = pd.DataFrame()
    bins = []
    if logx:
        lowest = -2
        highest = 5
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        div = 900/50
        bins = [i*div for i in range(50)]
    for val in [False, True]:
        fig = plt.figure()
        plt.clf()
        all_vals = []
        for FED in FEDs:
            df = FED.data
            if 'date_filter' in kwargs:
                s, e = kwargs['date_filter']
                df = df[(df.index >= s) &
                        (df.index <= e)].copy()
            y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
            periods = night_intervals(df.index, lights_on, lights_off,
                                      instead_days=val)
            vals = []
            for start, end in periods:
                vals.append(y[(y.index >= start) & (y.index < end)].copy())
            if vals:
                all_vals.append(pd.concat(vals))
        if all_vals:
            all_vals = pd.concat(all_vals)
        if logx:
            all_vals = [np.log10(val) for val in all_vals if not pd.isna(val)]
        label = 'Day' if val else 'Night'
        plot = sns.distplot(all_vals,bins=bins,label=label,norm_hist=False,
                            kde=kde,)
        if kde:
            if plot.get_lines():
                kde = plot.get_lines()[0].get_data()
                kde_dic = {label:kde[1]}
                kde_df = pd.DataFrame(kde_dic, index=kde[0])
                kde_output = kde_output.join(kde_df, how='outer')
            else:
                kde_output[label] = np.nan            
        bar_x = [v.get_x() for v in plot.patches]
        bar_h = [v.get_height() for v in plot.patches]
        bar_dic = {label:bar_h}
        bar_df = pd.DataFrame(bar_dic, index=bar_x)
        bar_output = bar_output.join(bar_df, how='outer')
        plt.close()
    kde_output.index.name = 'log10(minutes)' if logx else 'minutes'
    bar_output.index.name = 'log10(minutes)' if logx else 'minutes'
    return kde_output, bar_output

def pr_plot(FEDs, break_hours, break_mins, break_style, *args, **kwargs):
    delta = dt.timedelta(hours=break_hours, minutes=break_mins)
    output=pd.DataFrame()
    for FED in FEDs:
        df = FED.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
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
            if df['Correct_Poke'].dropna().empty:
                try:
                    if len(set(df['Active_Poke'])) == 1:
                        active = df['Active_Poke'][0]
                        if active.lower() == "left":
                            col = 'Left_Poke_Count'
                        elif active.lower() == 'right':
                            col = 'Right_Poke_Count'
                        out = df.loc[df.index[break_index],col]
                except:
                    pass
        if isinstance(out, pd.Series):
            out = out[-1]
        output.loc[break_style,FED.basename] = out
    return output

def group_pr_plot(FEDs, groups, break_hours, break_mins, break_style,
                  break_error, *args, **kwargs):
    delta = dt.timedelta(hours=break_hours, minutes=break_mins)
    output = pd.DataFrame()
    group_output = pd.DataFrame()
    for i, group in enumerate(groups):
        group_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
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
                    if df['Correct_Poke'].dropna().empty:
                        try:
                            if len(set(df['Active_Poke'])) == 1:
                                active = df['Active_Poke'][0]
                                if active.lower() == "left":
                                    col = 'Left_Poke_Count'
                                elif active.lower() == 'right':
                                    col = 'Right_Poke_Count'
                                out = df.loc[df.index[break_index],col]
                        except:
                            pass
                if isinstance(out, pd.Series):
                    out = out[-1]
                group_vals.append(out)
                if FED.basename not in output.columns:
                    output.loc[break_style, FED.basename] = out
        y = np.nanmean(group_vals,)
        group_output.loc[break_style, group] = y
        if break_error == 'SEM':
            group_output.loc[break_style, group + " SEM"] = stats.sem(group_vals,nan_policy='omit')
        elif break_error == 'STD':
            group_output.loc[break_style, group + " STD"] = np.nanstd(group_vals)
    output = output.merge(group_output, left_index=True, right_index=True)
    return output

def battery_plot(FED,*args, **kwargs):
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    x = df.index.values
    y = df['Battery_Voltage']
    y = y.rename('Battery (V)')
    output = pd.DataFrame(y, index=x)
    return output

def motor_plot(FED,*args, **kwargs):
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    x = df.index.values
    y = df['Motor_Turns']
    y = y.rename('Motor Turns')
    output = pd.DataFrame(y, index=x)
    return output

#---Old functions

def diagnostic_plot(FED, *args, **kwargs):
    df = FED.data
    dic = {'Pellets':df['Pellet_Count'],
           'Motor Turns':df['Motor_Turns'],
           'Battery (V)':df['Battery_Voltage']}
    output = pd.DataFrame(dic, index=df.index)
    output.index.name = 'Time'
    return output