# -*- coding: utf-8 -*-
"""
Module for creating summary statistics for FED3 Files.

@author: https://github.com/earnestt1234
"""
import pandas as pd
import numpy as np

from plots import plots

def label_meals(ipi, pellet_minimum=1, meal_delay=1): 
    output = []
    meal_no = 1
    c = 0
    while c < len(ipi):
        following_pellets = ipi[c+1:c+pellet_minimum]
        if len(following_pellets) == 0 and c == len(ipi) - 1:
            if ipi[c] >= meal_delay:
                output.append(meal_no if pellet_minimum == 1 else None)
            break
        if all(p < meal_delay for p in following_pellets):
            output.append(meal_no)
            while c < len(ipi) - 1:
                if ipi[c+1] < meal_delay:
                    output.append(meal_no)
                    c+=1
                else:
                    c+=1
                    break
            meal_no += 1
        else:
            output.append(None)
            c+=1
    return pd.Series(output)

def fed_summary(FEDs, ipi_pellet_minimum=1, ipi_meal_delay=1,
                motor_turns_thresh=10, lights_on=7, lights_off=19):
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    output_list = []
    for fed in FEDs:
        df = fed.data
        v = fed.basename
        results = pd.DataFrame(columns=[v])
        results.index.name = 'Variable'
        nights = plots.night_intervals(df.index, lights_on, lights_off)
        days = plots.night_intervals(df.index, lights_on, lights_off,
                                              instead_days=True)  
        
        #vars
        starttime = df.index[0]
        endtime = df.index[-1]
        duration = endtime-starttime
        hours = duration/pd.Timedelta(hours=1)
        
        #pellets
        results.loc['Pellets Taken', v] = df['Pellet_Count'].max()
        results.loc['Pellets per Hour', v] = df['Pellet_Count'].max()/hours
        
        #ipi
        if 'Interpellet_Intervals' in df.columns:
            meals = label_meals(df['Interpellet_Intervals'].dropna(),
                                pellet_minimum=ipi_pellet_minimum,
                                meal_delay=ipi_meal_delay)
            results.loc['Number of Meals',v] =  meals.max()
            results.loc['Average Pellets per Meal',v] =  meals.value_counts().mean()
            results.loc['% Pellets within Meals',v] =  (len(meals.dropna())/
                                                       len(meals) * 100)
            
        #pokes
        total_pokes = df['Left_Poke_Count'].max()+df['Right_Poke_Count'].max()
        results.loc['Total Pokes',v] = total_pokes
        results.loc['Left Pokes (%)',v] = df['Left_Poke_Count'].max()/total_pokes*100
        
        #other
        results.loc['Recording Duration (Hours)', v] = hours
        battery_use = (df['Battery_Voltage'][-1] - df['Battery_Voltage'][0])
        results.loc['Battery Change (V)', v] = battery_use
        results.loc['Battery Rate (V/hour)', v] = battery_use / hours
        motor_turns = df['Motor_Turns'][df['Motor_Turns'] > 0]
        results.loc['Motor Turns (Mean)', v] = motor_turns.mean()
        results.loc['Motor Turns (Median)', v] = motor_turns.median()
        motor_col = 'Motor Turns Above ' + str(motor_turns_thresh)
        results.loc[motor_col, v] = motor_turns[motor_turns >= motor_turns_thresh].sum()
        
        #circadian
        night_slices = []
        day_slices = []
        night_hours = []
        day_hours = []
        
        for start, end in nights:
            portion = df[(df.index>=start) & (df.index<=end)].copy()
            night_slices.append(portion)
            night_hours.append((portion.index[-1] - portion.index[0])/pd.Timedelta(hours=1))
        
        for start, end in days:
            portion = df[(df.index>=start) & (df.index<=end)].copy()
            day_slices.append(portion)
            day_hours.append((portion.index[-1] - portion.index[0])/pd.Timedelta(hours=1))
        
        night_hours = np.sum(night_hours)
        day_hours = np.sum(day_hours)
        
        for name, portions, hourz in zip([' (Night)', ' (Day)'], [night_slices, day_slices],
                                         [night_hours, day_hours]):
            results.loc['Pellets Taken' + name, v] = np.sum([d['Pellet_Count'].max()-d['Pellet_Count'].min()
                                                             for d in portions])
            results.loc['Pellets per Hour' + name, v] = np.sum([d['Pellet_Count'].max()-d['Pellet_Count'].min()
                                                             for d in portions])/hourz
            concat_meals = pd.concat([d['Interpellet_Intervals'] for d in portions])
            concat_meals = label_meals(concat_meals.dropna(),
                                       pellet_minimum=ipi_pellet_minimum,
                                       meal_delay=ipi_meal_delay)
            results.loc['Number of Meals' + name, v] = concat_meals.max()
            results.loc['Average Pellets per Meal' + name, v] = concat_meals.value_counts().mean()
            results.loc['% Pellets within Meals' + name, v] = (len(concat_meals.dropna())/
                                                               len(concat_meals))*100
            left_pokes = np.sum([d['Left_Poke_Count'].max() - d['Left_Poke_Count'].min()
                                 for d in portions])
            right_pokes = np.sum([d['Right_Poke_Count'].max() - d['Right_Poke_Count'].min()
                                 for d in portions])
            total_pokes = left_pokes + right_pokes
            results.loc['Total Pokes' + name,v] = total_pokes
            results.loc['Left Pokes (%)'+name,v] = left_pokes / total_pokes *100   
        output_list.append(results.astype(float))        
    output = pd.concat(output_list, axis=1)     
    avg = output.mean(axis=1)
    std = output.std(axis=1)
    order = []
    names = list(output.index)
    output['Average'] = avg
    output['STD'] = std
    for name in names:
        order.append(name)
        night_version = name + " (Night)"
        day_version = name + ' (Day)'
        if night_version in names:
            order.append(night_version)
            names.remove(night_version)
        if day_version in names:
            order.append(day_version)
            names.remove(day_version)
    output = output.reindex(order)
    return output