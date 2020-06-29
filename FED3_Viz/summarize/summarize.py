# -*- coding: utf-8 -*-
"""
Module for creating summary statistics for FED3 Files.

@author: https://github.com/earnestt1234
"""
import pandas as pd

def label_meals(ipi, pellet_minimum, meal_delay):
    output = []
    meal_no = 1
    c = 0
    while c < len(ipi):
        following_pellets = ipi[c+1:c+pellet_minimum]
        if len(following_pellets) == 0 and c == len(ipi) - 1:
            last = meal_no if pellet_minimum == 1 else None
            output.append(last)
            break
        if all(p < meal_delay for p in following_pellets):
            output.append(meal_no)
            while c < len(ipi):
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

def fed_summary(FED, ipi_pellet_minimum=2, ipi_meal_delay=1):
    df = FED.data
    v = 'Value'
    output = pd.DataFrame(columns=[v])
    output.index.name = 'Variable'
    
    #vars
    starttime = df.index[0]
    endtime = df.index[-1]
    duration = endtime-starttime
    hours = duration/pd.Timedelta(hours=1)
    
    #pellets
    output.loc['Pellets Taken', v] = df['Pellet_Count'].max()
    output.loc['Pellets per Hour', v] = df['Pellet_Count'].max()/hours
    
    #ipi
    if 'Interpellet_Intervals' in df.columns:
        meals = label_meals(df['Interpellet_Intervals'].dropna(),
                            pellet_minimum=ipi_pellet_minimum,
                            meal_delay=ipi_meal_delay)
        output.loc['Number of Meals',v] =  meals.max()
        output.loc['Avg Pellets per Meal',v] =  meals.value_counts().mean()
        output.loc['% Pellets within Meals',v] =  (len(meals.dropna())/
                                                   len(meals) * 100)
            
        
    
    return output.astype(float)