# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 16:55:48 2020

@author: earne
"""

import os
os.chdir(os.path.abspath(os.path.dirname(__file__)))

import numpy as np
import pandas as pd

from getdata import getdata
from plots import plots
from load.load import FED3_File

fed06 = r"C:\Users\earne\Box\Kravitz Lab Box Drive\Tom\Tom Files\python\FED3_Viz\FED3_sampledata\FEDs\#6\FED004_030620_01.CSV"
fed10 = r"C:/Users/earne/Box/Kravitz Lab Box Drive/Tom/Tom Files/python/FED3_Viz/FED3_sampledata/FEDs/#10/FED000_030620_01.CSV"
fed13 = r"C:/Users/earne/Box/Kravitz Lab Box Drive/Tom/Tom Files/python/FED3_Viz/FED3_sampledata/FEDs/#13/FED002_030620_02.CSV"

feds = [fed06,fed10,fed13]
feds = [FED3_File(fed) for fed in feds]
for fed in feds:
    fed.group.append('test')
#%%   
feds[0].group.append('test2')
feds[1].group.append('test2')
feds[2].group.append('test3')


x = feds[0].data
y = feds[1].data
z = feds[2].data

test = getdata.daynight_plot(feds, groups=['test','test2'], dn_value='pellets', 
                            lights_on=7, lights_off=19, dn_error='SEM',
                            dn_show_indvl=True,)

test2 = plots.daynight_plot(feds, groups=['test','test2'], dn_value='pellets', 
                            lights_on=7, lights_off=19, dn_error='SEM',
                            dn_show_indvl=True,)

