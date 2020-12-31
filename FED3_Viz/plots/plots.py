# -*- coding: utf-8 -*-
"""
Set of functions for plotting FED3 data.  These functions are called
by FED3 Viz to make plots, and the getdata module inspects the code and
shows it to the user when prompted with the "Plot Code" button.

@author: https://github.com/earnestt1234
"""
import datetime

import matplotlib as mpl
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

#---ERROR HANDLING

# class DateFilterError(Exception):
#     """Error when date filter causes empty df"""
#     pass

def date_filter_okay(df, start, end):
    """
    Verify that a DataFrame has data in between 2 dates

    Parameters
    ----------
    df : pandas.DataFrame
        data to check
    start : datetime
        start of the date filter
    end : datetime
        end of the date filter

    Returns
    -------
    Bool
    """
    check = df[(df.index >= start) &
            (df.index <= end)].copy()
    return not check.empty

#---HELPER FUNCTIONS

def convert_dt64_to_dt(dt64):
    """Converts numpy datetime to standard datetime (needed for shade_darkness
    function in most cases)."""
    new_date = (dt64 - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
    new_date = datetime.datetime.utcfromtimestamp(new_date)
    return new_date

def hours_between(start, end, convert=True):
    """
    Create a range of hours between two dates.

    Parameters
    ----------
    start, end : datetime-like object
        When to begin and end the data range
    convert : bool, optional
        Whether to convert the start/end arguments from numpy datetime to
        standard datetime. The default is True.

    Returns
    -------
    pandas DateTimeIndex
        Index array of all hours between start and end.
    """
    if convert:
        start = convert_dt64_to_dt(start)
        end = convert_dt64_to_dt(end)
    rounded_start = datetime.datetime(year=start.year,
                                month=start.month,
                                day=start.day,
                                hour=start.hour)
    rounded_end = datetime.datetime(year=end.year,
                                month=end.month,
                                day=end.day,
                                hour=end.hour)
    return pd.date_range(rounded_start,rounded_end,freq='1H')

def is_day_or_night(time, period, lights_on=7, lights_off=19):
    """
    Check if a datetime occured at day or night

    Parameters
    ----------
    time : datetime or pandas.Timestamp
        time to check
    period : str
        'day' or 'night', which period to check if the date is part of,
        based on the lights_on and lights_off arguments
    lights_on : int, optional
        Hour of the day (0-23) when lights turn on. The default is 7.
    lights_off : int, optional
         Hour of the day (0-23) when lights turn off. The default is 19.

    Returns
    -------
    Bool
    """
    lights_on = datetime.time(hour=lights_on)
    lights_off = datetime.time(hour=lights_off)
    val = False
    #defaults to checking if at night
    if lights_off > lights_on:
        val = time.time() >= lights_off or time.time() < lights_on
    elif lights_off < lights_on:
        val = time.time() >= lights_off and time.time() < lights_on
    #reverses if period='day'
    return val if period=='night' else not val

def get_daynight_count(start_time, end_time, lights_on=7, lights_off=9):
    """
    Compute the (fractional) number of completed light and dark periods between
    two dates.  Used for normalizing values grouped by day & nightime.

    Parameters
    ----------
    start_time : datetime
        starting time
    end_time : datetime
        ending time
    lights_on : int, optional
        Hour of the day (0-23) when lights turn on. The default is 7.
    lights_off : int, optional
        Hour of the day (0-23) when lights turn off. The default is 19.

    Returns
    -------
    dict
        dictionary with keys "day" and "night", values are the
        number of completed periods for each key.
    """
    cuts = []
    cuts.append(start_time)
    loop_time = start_time.replace(minute=0,second=0)
    while loop_time < end_time:
        loop_time += pd.Timedelta(hours=1)
        if loop_time.hour == lights_on:
            cuts.append(loop_time)
        elif loop_time.hour == lights_off:
            cuts.append(loop_time)
    cuts.append(end_time)
    days = []
    nights = []
    if lights_off > lights_on:
        day_hours = lights_off - lights_on
        night_hours = 24 - day_hours
    else:
        night_hours = lights_on - lights_off
        day_hours = 24 - night_hours
    day_hours = pd.Timedelta(hours = day_hours)
    night_hours = pd.Timedelta(hours = night_hours)
    for i, t in enumerate(cuts[:-1]):
        if is_day_or_night(t, 'day', lights_on, lights_off):
            days.append((cuts[i+1] - t)/day_hours)
        else:
            nights.append((cuts[i+1] - t)/night_hours)
    return {'day':sum(days),'night':sum(nights)}

def night_intervals(array, lights_on, lights_off, instead_days=False):
    """
    Find intervals of a date-array corresponding to night time.

    Parameters
    ----------
    array : array-like
        Array of datetimes (e.g. generated by hours_between).
    lights_on : int
        Integer between 0 and 23 representing when the light cycle begins.
    lights_off : int
        Integer between 0 and 23 representing when the light cycle ends.
    instead_days : bool, optional
        Return intervals during daytime instead of nighttime. The default is False.

    Returns
    -------
    night_intervals : list
        List of tuples with structure (start of nighttime, end of nighttime).
    """
    l_on = datetime.time(hour=lights_on)
    l_off = datetime.time(hour=lights_off)
    if l_on == l_off:
            night_intervals = []
            return night_intervals
    else:
        at_night = [is_day_or_night(i, 'night', lights_on=lights_on, lights_off=lights_off) for i in array]
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
    """
    Shade the night periods of a matplotlib Axes with a datetime x-axis.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Plot Axes.
    min_date : datetime
        Earliest date to shade.
    max_date : datetime
        Latest date to shade.
    lights_on : int
        Integer between 0 and 23 representing when the light cycle begins.
    lights_off : int
        Integer between 0 and 23 representing when the light cycle ends.
    convert : bool, optional
        Whether to convert the start/end arguments from numpy datetime to
        standard datetime. The default is True.

    Returns
    -------
    None.
    """
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

def resample_get_yvals(df, value, retrieval_threshold=None):
    """
    Function for passing to the apply() method of pandas Resampler or
    DataFrameGroupBy object.  Computes an output for each bin of binned
    FED3 data.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame of FED3 data (loaded by FED3_Viz.load.FED3_File)
    value : str
        String signalling what output to compute for each bin.  Options are:
        'pellets','retrieval time','interpellet intervals','correct pokes',
        'errors','correct pokes (%)','errors (%)','poke bias (correct - error)',
        'poke bias (left - right)', & 'poke bias (correct %)'

    Returns
    -------
    output : float or int
        Computed value (for each bin of df)
    """
    possible = ['pellets','retrieval time','interpellet intervals',
                'correct pokes','errors','correct pokes (%)','errors (%)',
                'poke bias (correct - error)', 'poke bias (left - right)',
                'poke bias (correct %)',]
    assert value in possible, 'Value not understood by daynight plot: ' + value
    #in use
    if value == 'poke bias (correct %)':
        value = 'correct pokes (%)'
    if value == 'pellets':
        output = df['Binary_Pellets'].sum()
    elif value == 'retrieval time':
        output = df['Retrieval_Time'].copy()
        if retrieval_threshold:
            output.loc[output>=retrieval_threshold] = np.nan
        output = output.mean()
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
    #outdated
    elif value == 'poke bias (correct - error)':
        output = list(df['Correct_Poke']).count(True) - list(df['Correct_Poke']).count(False)
    elif value == 'poke bias (left - right)':
        output = df['Binary_Left_Pokes'].sum() - df['Binary_Right_Pokes'].sum()
    return output

def raw_data_scatter(array, xcenter, spread):
    """
    Create points for graphing individual observations as points on a bar plot.
    Output can be passed to a scatter-plot function.

    Parameters
    ----------
    array : array-like of float, int
        y-values being plotted (what goes into making the bar)
    xcenter : float, int
        x-position to center y-values
    spread : float, int
        Distance in x to randomly spread x-positions.  A spread equal to
        the bar width will allow for x-positions across the entire bar.  Points
        will be distributed randomly around xcenter, with half being greater
        and half being lesser

    Returns
    -------
    x : numpy.ndarray
        array of x-positions
    y : array-like
        returns the array argument as is
    """
    y = array
    x = np.random.uniform(0,(spread/2), size=len(y))
    half = int(len(y)/2)
    for i in range(half):
        x[i] *= -1
    np.random.shuffle(x)
    x += xcenter
    return x,y

def date_format_x(ax, start, end):
    """
    Format the x-ticks of datetime plots created by FED3 Viz.  Handles various
    incoming dates by lowering the (time) frequency of ticks with longer
    date ranges.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Graph Axes
    start : datetime
        Earliest x-position of the graph
    end : datetime
        Latest x-position of the graph

    Returns
    -------
    None.
    """
    d8_span = end - start
    if d8_span < datetime.timedelta(hours=12):
        xfmt = mdates.DateFormatter('%H:%M')
        major = mdates.HourLocator()
        minor = mdates.MinuteLocator(byminute=[0,15,30,45])
    elif datetime.timedelta(hours=12) <= d8_span < datetime.timedelta(hours=24):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = mdates.HourLocator(byhour=[0,6,12,18])
        minor = mdates.HourLocator()
    elif datetime.timedelta(hours=24) <= d8_span < datetime.timedelta(days=3):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = mdates.DayLocator()
        minor = mdates.HourLocator(byhour=[0,6,12,18])
    elif datetime.timedelta(days=3) <= d8_span < datetime.timedelta(days=6):
        xfmt = mdates.DateFormatter('%b %d %H:%M')
        major = mdates.DayLocator(interval=2)
        minor = mdates.DayLocator()
    elif datetime.timedelta(days=6) <= d8_span < datetime.timedelta(days=20):
        xfmt = mdates.DateFormatter('%b %d')
        major = mdates.DayLocator(interval=3)
        minor = mdates.DayLocator()
    elif datetime.timedelta(days=20) <= d8_span < datetime.timedelta(days=32):
        xfmt = mdates.DateFormatter('%b %d')
        major = mdates.DayLocator(interval=5)
        minor = mdates.DayLocator()
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    elif datetime.timedelta(days=32) <= d8_span < datetime.timedelta(days=60):
        xfmt = mdates.DateFormatter('%b %d')
        major = mdates.DayLocator(interval=10)
        minor = mdates.DayLocator(interval=5)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    elif datetime.timedelta(days=62) <= d8_span < datetime.timedelta(days=120):
        xfmt = mdates.DateFormatter('%b %d')
        major = mdates.DayLocator(interval=15)
        minor = mdates.DayLocator(interval=5)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    elif d8_span >= datetime.timedelta(days=120):
        xfmt = mdates.DateFormatter("%b '%y")
        major = mdates.MonthLocator()
        minor = mdates.DayLocator(bymonthday=[7,15,23])
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax.xaxis.set_major_locator(major)
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.set_minor_locator(minor)

def left_right_bias(df, bin_size, version='ondatetime', starttime=None):
    """
    Compute the binned left-right bias (% left pokes) for FED3 data.

    Parameters
    ----------
    df : pandas.DataFrame
        FED3 data (loaded from load.FED3_File)
    bin_size : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.Grouper
    version : str, optional
        Method for resampling; relates to different averaging behaviors in
        FED3 Viz. The default is 'ondatetime'.
        -'ondatetime': resample based on the absolute date time of df;
        the first bin start on the hour of the first entry (used by
        average_plot_ondatetime)
        -'ontime': resample based on the time of day, uses the starttime
        argument to set base of resample bins (used by average_plot_ontime)
        -'onstart': resample on the Elapsed_Time column (used by
        average_plot_onstart)
    starttime : int, optional
        Integer between 0 and 23 indicating hour of day to start resampling.
        Only used when version='ontime'.  The default is None.

    Returns
    -------
    out : pandas.Series
        Left poke percentage in each bin.
    """
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

def left_right_noncumulative(df, bin_size, side, version='ondatetime', starttime=None):
    """
    Return the left or right pokes as binned non-cumulative counts for FED3
    data.

    Parameters
    ----------
    df : pandas.DataFrame
        FED3 data (loaded from load.FED3_File)
    bin_size : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.Grouper
    side : str
        whether to compute for the left {'l', 'left'} or right {'r','right'}
        poke
    version : str, optional
        Method for resampling; relates to different averaging behaviors in
        FED3 Viz. The default is 'ondatetime'.
        -'ondatetime': resample based on the absolute date time of df;
        the first bin start on the hour of the first entry (used by
        average_plot_ondatetime)
        -'ontime': resample based on the time of day, uses the starttime
        argument to set base of resample bins (used by average_plot_ontime)
        -'onstart': resample on the Elapsed_Time column (used by
        average_plot_onstart)
    starttime : int, optional
        Integer between 0 and 23 indicating hour of day to start resampling.
        Only used when version='ontime'.  The default is None.

    Returns
    -------
    diff : pandas.Series
        Non-cumulative count of pokes in each resampled bin.
    """
    if version == 'ondatetime':
        grouper = pd.Grouper(freq=bin_size,base=0)
    elif version == 'ontime':
        grouper = pd.Grouper(freq=bin_size,base=starttime)
    elif version == 'onstart':
        grouper = pd.Grouper(key='Elapsed_Time',freq=bin_size,base=0)
    if side.lower() in ['left', 'l']:
        on = 'Left_Poke_Count'
    elif side.lower() in ['right', 'r']:
        on = 'Right_Poke_Count'
    try:
        df = df[df['Event'] == 'Poke']
    except:
        pass
    resampled = df.groupby(grouper)
    side_resampled = resampled[on].max()
    side_resampled_nona = side_resampled.dropna()
    diff = side_resampled_nona.diff()
    diff[0] = side_resampled_nona[0]
    diff = diff.reindex(side_resampled.index)
    diff = diff.fillna(0)
    return diff

def label_meals(ipi, meal_pellet_minimum=1, meal_duration=1):
    """
    Assign numbers to pellets based on their interpellet intervals (time passsed
    since the previos pellet).

    Parameters
    ----------
    ipi : array
        An array of interpellet intervals (without missing values!)
    meal_pellet_minimum : int, optional
        The minimum pellets required (within the meal_duration) to constitute
        a meal. The default is 1 (with 1, all pellets are assigned a meal
        regardless of the elapsed time between them).
    meal_duration : int, optional
        The amount of time (in minutes) that can pass before a new meal is
        assigned. The default is 1.  Pellets with an IPI below the meal_duration
        will either be assigned to the meal of the previous pellet (if there are
        enough previous/following pellets to pass the meal_pellet_minimum), to a new meal
        (if there are enough following pellets to pass the meal_pellet_minimum), or
        to None (if there are not enough surrounding pellets to surpass the
        meal_pellet_minimum)/

    Returns
    -------
    pandas.Series
        Series of meals labeled by meal number
    """
    output = []
    meal_no = 1
    c = 0
    while c < len(ipi):
        following_pellets = ipi[c+1:c+meal_pellet_minimum]
        if len(following_pellets) == 0 and c == len(ipi) - 1:
            if ipi[c] >= meal_duration:
                output.append(meal_no if meal_pellet_minimum == 1 else None)
            break
        if all(p < meal_duration for p in following_pellets):
            output.append(meal_no)
            while c < len(ipi) - 1:
                if ipi[c+1] < meal_duration:
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

#---Pellet Plots

def pellet_plot_single(FED, shade_dark, lights_on, lights_off, pellet_color,
                       **kwargs):
    """
    FED3 Viz: Creates a line plot cumulative pellet retrieval over time.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    pellet_color : str
        matplotlib named color string to color line
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_plot_single()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
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

    return fig if 'ax' not in kwargs else None

def pellet_freq_single(FED, pellet_bins, shade_dark, lights_on,
                       lights_off, pellet_color, **kwargs):
    """
    FED3 Viz: Creates a bar plot of non-cumulative pellet retrieval over time.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    pellet_bins : pandas date offset string
        how frequently to bin, passed to rule argument of DataFrame.resample()
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    pellet_color : str
        matplotlib named color string to color bars
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_freq_single()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data.resample(pellet_bins).sum()
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
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

    return fig if 'ax' not in kwargs else None

def pellet_plot_multi_aligned(FEDs, **kwargs):
    """
    FED3 Viz: Create a line plot showing cumulative pellets retrieved for
    multiple FEDs in relative time (0 represents start of each file)

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    xmax = 0
    ymax = 0
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
            # following line toggles where 0 is with date filter
            df['Elapsed_Time'] -= df['Elapsed_Time'][0]
        x = [(time.total_seconds()/3600) for time in df['Elapsed_Time']]
        y = df['Pellet_Count']
        ax.plot(x, y, label=file.filename, alpha=.6, lw=1)
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
    x_offset = .05 * xmax
    ax.set_xlim(0-x_offset,xmax+x_offset)
    ax.set_ylabel('Cumulative Pellets')
    ax.set_ylim(0,ymax*1.1)
    title = ('Pellets Retrieved for Multiple FEDs')
    ax.set_title(title)
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def pellet_plot_multi_unaligned(FEDs, shade_dark, lights_on,
                                lights_off,**kwargs):
    """
    FED3 Viz: Plot cumulaive pellet retrieval for multiple FEDs, keeping the
    x-axis to show absolute time.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    min_date = np.datetime64('2100')
    max_date = np.datetime64('1970')
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        x = df.index
        y = df['Pellet_Count']
        ax.plot(x, y, label=file.filename, alpha=.6, lw=1)
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
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def pellet_freq_multi_aligned(FEDs, pellet_bins, **kwargs):
    """
    FED3 Viz: Plot the binned count of pellet retrieval for multiple FEDs
    as a bar plot, aligning such that x-axis shows time since the start of
    each recording.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    pellet_bins : pandas date offset string
        how frequently to bin, passed to rule argument of DataFrame.resample()
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    max_time = 0
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        df = df.resample(pellet_bins,base=0).sum()
        times = []
        for i, date in enumerate(df.index):
            times.append(date - df.index[0])
        times = [(time/np.timedelta64(1,'h')) for time in times]
        x = times
        y = df['Binary_Pellets']
        ax.plot(x, y, alpha=.6, label=file.filename, lw=1)
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
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def pellet_freq_multi_unaligned(FEDs, pellet_bins, shade_dark,
                                lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Plot the binned count of pellet retrieval for multiple FEDs
    as a bar plot, without aligning the files in time.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    pellet_bins : pandas date offset string
        how frequently to bin, passed to rule argument of DataFrame.resample()
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    min_date = np.datetime64('2100')
    max_date = np.datetime64('1970')
    for file in FEDs:
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        df = df.resample(pellet_bins,base=0).sum()
        x = df.index
        y = df['Binary_Pellets']
        ax.plot(x, y, label=file.filename,
               alpha=.6, lw=1)
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
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def interpellet_interval_plot(FEDs, kde, logx, **kwargs):
    """
    FED3 Viz: Plot a histogram of interpellet intervals for multiple devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    kde : bool
        Whether or not to include kernel density estimation, which plots
        probability density (rather than count) and includes a fit line (see
        seaborn.distplot)
    logx : bool
        When True, plots on a logarithmic x-axis
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to interpellet_interval_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(4,5), dpi=125)
    else:
        ax = kwargs['ax']
    bins = []
    if logx:
        lowest = -2
        highest = 5
        ax.set_xticks(range(lowest,highest))
        ax.set_xticklabels([10**num for num in range(-2,5)])
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        ax.set_xticks([0,300,600,900])
        div = 900/50
        bins = [i*div for i in range(50)]
        ax.set_xlim(-100,1000)
    for FED in FEDs:
        df = FED.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
        if logx:
            y = [np.log10(val) for val in y if not pd.isna(val)]
        sns.distplot(y,bins=bins,label=FED.filename,ax=ax,norm_hist=False,
                     kde=kde)
    ax.legend(fontsize=8)
    ylabel = 'Density Estimation' if kde else 'Count'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('minutes between pellets')
    ax.set_title('Interpellet Interval Plot')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def group_interpellet_interval_plot(FEDs, groups, kde, logx, **kwargs):
    """
    FED3 Viz: Plot the interpellet intervals as a histogram, first aggregating
    the values for devices in a Groups.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to plot (based on the group attribute of each FED3_File)
    kde : bool
        Whether or not to include kernel density estimation, which plots
        probability density (rather than count) and includes a fit line (see
        seaborn.distplot)
    logx : bool
        When True, plots on a logarithmic x-axis
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to interpellet_interval_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(4,5), dpi=125)
    else:
        ax = kwargs['ax']
    bins=[]
    if logx:
        lowest = -2
        highest = 5
        ax.set_xticks(range(lowest,highest))
        ax.set_xticklabels([10**num for num in range(-2,5)])
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        ax.set_xticks([0,300,600,900])
        div = 900/50
        bins = [i*div for i in range(50)]
        ax.set_xlim(-100,1000)
    for group in groups:
        all_vals = []
        for FED in FEDs:
            if group in FED.group:
                df = FED.data
                if 'date_filter' in kwargs:
                    s, e = kwargs['date_filter']
                    df = df[(df.index >= s) &
                            (df.index <= e)].copy()
                y = list(df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0])
                if logx:
                    y = [np.log10(val) for val in y if not pd.isna(val)]
                all_vals += y
        sns.distplot(all_vals,bins=bins,label=group,ax=ax,norm_hist=False,
                     kde=kde)
    ax.legend(fontsize=8)
    ylabel = 'Density Estimation' if kde else 'Count'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('minutes between pellets')
    ax.set_title('Interpellet Interval Plot')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def retrieval_time_single(FED, retrieval_threshold, shade_dark,
                          lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Create a scatter plot with a twin y-axis showing cumulative
    pellets receieved and retrieval time (seconds) for each pellet.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    retrieval_threshold : int or float
        maximum value of retrieval time to include (higher becomes np.nan)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    pellet_color : str
        matplotlib named color string to color line
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to pellet_plot_single()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    y1 = df['Pellet_Count'].drop_duplicates()
    x1 = y1.index
    y2 = df['Retrieval_Time'].copy()
    x2 = y2.index
    if retrieval_threshold:
        y2.loc[y2>=retrieval_threshold] = np.nan
    ax.scatter(x1, y1, s=5, color='coral', label='pellets')
    ax.set_ylabel('Cumulative Pellets',)
    ax2 = ax.twinx()
    ax2.scatter(x2, y2, s=5, color='darkviolet', marker='s',label ='retrieval time')
    ax2.set_ylabel('Retrieval Time (s)',)
    if retrieval_threshold:
        ax2.set_ylim(0,retrieval_threshold)
    ax.set_title('Pellets and Retrieval Times for ' + FED.filename)
    date_format_x(ax, df.index[0], df.index[-1])
    x_offset = (x1[-1] - x1[0])*.05
    ax.set_xlim(x1[0] - x_offset, x1[-1] + x_offset)
    ax.set_xlabel('Time')
    if shade_dark:
        shade_darkness(ax,min(df.index), max(df.index),
                       lights_on=lights_on,
                       lights_off=lights_off)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1+h2, l1+l2, bbox_to_anchor=(1.15,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def retrieval_time_multi(FEDs, retrieval_threshold, **kwargs):
    """
    FED3 Viz: Create a scatter plot showing pelle retrieval time for
    multiple devices, aligning them to the same start point.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    retrieval_threshold : int or float
        maximum value of retrieval time to include (higher becomes np.nan)
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to retrieval_time_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    color_gradient_divisions = [(1/len(FEDs))*i for i in range(len(FEDs))]
    cmap = mpl.cm.get_cmap('jet')
    color_gradients = cmap(color_gradient_divisions)
    xmax = 0
    for i, fed in enumerate(FEDs):
        df = fed.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
            df['Elapsed_Time'] -= df["Elapsed_Time"][0] #toggles where t=0 is
        y = df['Retrieval_Time'].copy()
        if retrieval_threshold:
            y.loc[y>=retrieval_threshold] = np.nan
        x = [t.total_seconds()/3600 for t in df['Elapsed_Time']]
        ax.scatter(x, y, s=5, color=color_gradients[i], marker='s',
                   alpha=.3, label=fed.filename)
        if max(x) > xmax:
            xmax = max(x)
    ax.set_xlabel('Time (h)')
    number_of_days = int(xmax//24)
    if number_of_days > 2:
        days_in_hours = [24*day for day in range(number_of_days+1)]
        ax.set_xticks(days_in_hours)
    else:
        days_in_sixes = [6*quart for quart in range((number_of_days+1)*4)]
        ax.set_xticks(days_in_sixes)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    x_offset = .05 * xmax
    ax.set_xlim(0-x_offset,xmax+x_offset)
    ax.set_ylabel('Retrieval Time (seconds)')
    ax.set_title('Pellet Retrieval Time')
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def meal_size_histogram(FEDs, meal_pellet_minimum, meal_duration,
                        norm_meals, **kwargs):
    """
    FED3 Viz: Create a histogram of meal sizes for multiple devices.
    Each file is shown as a separate curve.


    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    meal_pellet_minimum : int
        minimum pellets to constitute a meal
    meal_duration : int
        amount of time to allow before a new meal is assigned
    norm_meals : bool
        Whether or not to normalize the histogram
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to retrieval_time_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    ax.set_title('Meal Size Histogram')
    label = 'Probability' if norm_meals else 'Count'
    ax.set_ylabel(label)
    ax.set_xlabel('Meal Size (# of Pellets)')
    if norm_meals:
        ax.set_ylim(0,1)
        ax.set_yticks([0,.2,.4,.6,.8,1.0])
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
        sns.distplot(series,bins=bins,kde=False,ax=ax,label=fed.basename,
                     norm_hist=norm_meals,)
    ax.set_xticks(range(1,longest_meal+1))
    if len(FEDs) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()
    return fig if 'ax' not in kwargs else None

def grouped_meal_size_histogram(FEDs, groups, meal_pellet_minimum, meal_duration,
                                norm_meals, **kwargs):
    """
    FED3 Viz: Create a histogram of meal sizes for Grouped devices.
    Each Group is shown as a separate curve; meal sizes within each
    Group are concatenated.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    meal_pellet_minimum : int
        minimum pellets to constitute a meal
    meal_duration : int
        amount of time to allow before a new meal is assigned
    norm_meals : bool
        Whether or not to normalize the histogram
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to retrieval_time_multi()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    ax.set_title('Meal Size Histogram')
    label = 'Probability' if norm_meals else 'Count'
    ax.set_ylabel(label)
    ax.set_xlabel('Meal Size (# of Pellets)')
    if norm_meals:
        ax.set_ylim(0,1)
        ax.set_yticks([0,.2,.4,.6,.8,1.0])
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
        sns.distplot(series,bins=bins,kde=False,ax=ax,label=group,
                     norm_hist=norm_meals,)
    ax.set_xticks(range(1, longest_meal+1))
    if len(groups) < 10:
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()
    return fig if 'ax' not in kwargs else None

#---Average Pellet Plots

def average_plot_ondatetime(FEDs, groups, dependent, average_bins, average_error,
                            shade_dark, lights_on, lights_off,**kwargs):
    """
    FED3 Viz: Create an average line plot for Grouped FED3 Files; averaging
    is only done for periods where all devices were active.  If there is no such
    period, an error string is returned.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    dependent : str
        String denoting the output variable.  Acceptable values are ones
        which can be passed to resample_get_yvals(), as well as "poke bias
        (left %)", "left pokes", and "right pokes".
    average_bins : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.groupby()
    average_error : str
        How to represent the spread of data around the average.  Options are
        "SEM", "STD", "raw data", or "None".
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    earliest_end = datetime.datetime(2999,1,1,0,0,0)
    latest_start = datetime.datetime(1970,1,1,0,0,0)
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_average_cumulative()'
        df = file.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        if min(df.index) > latest_start:
            latest_start = min(df.index)
        if max(df.index) < earliest_end:
            earliest_end = max(df.index)
    if earliest_end < latest_start:
        return 'NO_OVERLAP ERROR'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    maxy = 0
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
                    y = df.apply(resample_get_yvals,dependent,retrieval_threshold)
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
        error_shade = np.nan
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
    ax.set_ylabel(dependent.capitalize())
    if "%" in dependent:
        ax.set_ylim(-5,105)
    if 'bias' in dependent:
        ax.axhline(y=50, linestyle='--', color='gray', zorder=2)
    ax.set_title('Average Plot of ' + dependent.capitalize())
    if shade_dark:
        shade_darkness(ax, latest_start, earliest_end,
                       lights_on=lights_on,
                       lights_off=lights_off)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None


def average_plot_ontime(FEDs, groups, dependent, average_bins, average_align_start,
                        average_align_days, average_error, shade_dark, lights_on,
                        lights_off, **kwargs):
    """
    FED3 Viz: Create an average line plot for Grouped FED3 Files.  Data are
    first aligned by the time of day, and then averaged.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    dependent : str
        String denoting the output variable.  Acceptable values are ones
        which can be passed to resample_get_yvals(), as well as "poke bias
        (left %)", "left pokes", and "right pokes".
    average_bins : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.groupby()
    average_align_start : int
        Integer between 0 and 23 denoting the hour of the day to set as zero.
    average_align_days : int
        How many days to try and create an average for.
    average_error : str
        How to represent the spread of data around the average.  Options are
        "SEM", "STD", "raw data", or "None".
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_plot_average_cumulative()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    start_datetime = datetime.datetime(year=1970,
                                 month=1,
                                 day=1,
                                 hour=average_align_start)
    end_datetime = start_datetime + datetime.timedelta(days=average_align_days)
    date_range = pd.date_range(start_datetime,end_datetime,freq=average_bins)
    maxy=0
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
                aligned_first_entry = datetime.datetime(year=1970,month=1,day=1,
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
        error_shade = np.nan
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
    ax.set_xlim(start_datetime,end_datetime + datetime.timedelta(hours=5))
    ax.set_ylabel(dependent.capitalize())
    if "%" in dependent:
        ax.set_ylim(-5,105)
    if 'bias' in dependent:
        ax.axhline(y=50, linestyle='--', color='gray', zorder=2)
    ax.set_title('Average Plot of ' + dependent.capitalize())
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def average_plot_onstart(FEDs, groups, dependent, average_bins, average_error, **kwargs):
    """
    FED3 Viz: Create an average line plot for Grouped FED3 Files.  Data are
    first aligned by elapsed time, and then averaged.


    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    dependent : str
        String denoting the output variable.  Acceptable values are ones
        which can be passed to resample_get_yvals(), as well as "poke bias
        (left %)", "left pokes", and "right pokes".
    average_bins : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.groupby()
    average_error : str
        How to represent the spread of data around the average.  Options are
        "SEM", "STD", "raw data", or "None".
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    show_indvl=False
    if average_error == 'raw data':
        average_error = 'None'
        show_indvl=True
    longest_index = []
    for file in FEDs:
        assert isinstance(file, FED3_File),'Non FED3_File passed to pellet_average_onstart()'
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
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    maxy=0
    maxx=0
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
        error_shade = np.nan
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
    xlabel = ('Time (h since recording start)' if not 'date_filter' in kwargs else
              'Time (h since ' + str(kwargs['date_filter'][0]) + ')')
    ax.set_xlabel(xlabel)
    number_of_days = int(maxx//24)
    if number_of_days > 2:
        days_in_hours = [24*day for day in range(number_of_days+1)]
        ax.set_xticks(days_in_hours)
    else:
        days_in_sixes = [6*quart for quart in range((number_of_days+1)*4)]
        ax.set_xticks(days_in_sixes)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    x_offset = .1 * maxx
    ax.set_xlim(0-x_offset,maxx+x_offset)
    ax.set_ylabel(dependent.capitalize())
    if "%" in dependent:
        ax.set_ylim(-5,105)
    if 'bias' in dependent:
        ax.axhline(y=50, linestyle='--', color='gray', zorder=2)
    title = ('Average Plot of ' + dependent.capitalize())
    ax.set_title(title)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

#---Single Poke Plots

def poke_plot(FED, poke_bins, poke_show_correct, poke_show_error, poke_show_left,
              poke_show_right, poke_style, shade_dark, lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Generate a line plot showing pokes over time for a single device.

    Parameters
    ----------
    FED : FED3_File object
        FED3 file (loaded by load.FED3_File)
    poke_bins : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.groupby()
        or rule argument of DataFrame.resample()
    poke_show_correct : bool
        Whether to plot correct pokes
    poke_show_error : bool
        Whether to plot incorrect pokes
    poke_show_left : bool
        Whether to plot left pokes
    poke_show_right : bool
        Whether to plot right pokes
    poke_style : str
        Either "cumulative" or "frequency" (non-cumulative)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File), 'Non FED3_File passed to poke_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data
    if poke_style == 'Cumulative':
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
        correct_pokes = df['Correct_Poke']
        if poke_show_correct:
            y = pd.Series([1 if i==True else np.nan for i in correct_pokes]).cumsum()
            y.index = df.index
            y = y.dropna()
            if not pd.isna(offset_correct):
                y += offset_correct
            x = y.index
            ax.plot(x, y, color='mediumseagreen', label = 'correct pokes')
        if poke_show_error:
            y = pd.Series([1 if i==False else np.nan for i in correct_pokes]).cumsum()
            y.index = df.index
            y = y.dropna()
            if not pd.isna(offset_wrong):
                y += offset_wrong
            x = y.index
            ax.plot(x, y, color='indianred', label = 'error pokes')
        if poke_show_left:
            try:
                y = df[df['Event'] == 'Poke']['Left_Poke_Count']
            except:
                y = df['Left_Poke_Count']
            x = y.index
            ax.plot(x, y, color='cornflowerblue', label = 'left pokes')
        if poke_show_right:
            try:
                y = df[df['Event'] == 'Poke']['Right_Poke_Count']
            except:
                y = df['Right_Poke_Count']
            x = y.index
            ax.plot(x, y, color='gold', label = 'right pokes')
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
            x = y.index
            ax.plot(x, y, color='mediumseagreen', label = 'correct pokes')
        if poke_show_error:
            y = resampled_correct.apply(lambda binn: (binn==False).sum())
            x = y.index
            ax.plot(x, y, color='indianred', label = 'error pokes')
        if poke_show_left:
            y = left_right_noncumulative(df, bin_size=poke_bins,side='l')
            x = y.index
            ax.plot(x, y, color='cornflowerblue', label = 'left pokes')
        if poke_show_right:
            y = left_right_noncumulative(df, bin_size=poke_bins,side='r')
            x = y.index
            ax.plot(x, y, color='gold', label = 'right pokes')
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
        shade_darkness(ax, min(df.index), max(df.index),
                       lights_on=lights_on,
                       lights_off=lights_off)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def poke_bias(FED, poke_bins, bias_style, shade_dark, lights_on,
              lights_off, dynamic_color, **kwargs):
    """
    FED3 Viz: Create a line plot showing the tendency of one poke to be picked
    over another.

    Parameters
    ----------
    FED : FED3_File object
        FED3 file (loaded by load.FED3_File)
    poke_bins : pandas date offset string
        how frequently to bin, passed to freq argument of pandas.groupby()
        or rule argument of DataFrame.resample()
    bias_style : str
        "left %" or "correct %"
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    dynamic_color : bool
        Whether or not to color the line based on the distance from 50%
        (shifts plotting from matplotlib.pyplot.plot() to
        matplotlib.pyplot.scatter())
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    DENSITY = 10000
    assert isinstance(FED, FED3_File), 'Non FED3_File passed to poke_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    if bias_style == 'correct (%)':
        resampled = df.groupby((pd.Grouper(freq=poke_bins)))
        y = resampled.apply(resample_get_yvals, 'poke bias (correct %)')
    elif bias_style == 'left (%)':
        y = left_right_bias(df, poke_bins)
    x = y.index
    if not dynamic_color:
        ax.plot(x, y, color = 'magenta', zorder=3)
    else:
        xnew = pd.date_range(min(x),max(x),periods=DENSITY)
        ynew = np.interp(xnew, x, y)
        ax.scatter(xnew, ynew, s=1, c=ynew,
                   cmap='bwr', vmin=0, vmax=100, zorder=1)
    date_format_x(ax, x[0], x[-1])
    if bias_style == 'correct (%)':
        label = 'Correct Pokes (%)'
    elif bias_style == 'left (%)':
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

    return fig if 'ax' not in kwargs else None

def poketime_plot(FED, poke_show_correct, poke_show_error, poke_show_left,
                  poke_show_right, poketime_cutoff,
                  shade_dark, lights_on, lights_off,
                  **kwargs):
    """
    FED3 Viz: Generate a scatter plot showing poke time for a device
    Must have the Poke_Time column added.

    Parameters
    ----------
    FED : FED3_File object
        FED3 file (loaded by load.FED3_File)
    poke_show_correct : bool
        Whether to plot correct pokes
    poke_show_error : bool
        Whether to plot incorrect pokes
    poke_show_left : bool
        Whether to plot left pokes
    poke_show_right : bool
        Whether to plot right pokes
    poketime_cutoff : int
        Time (in seconds) to limit poke times.
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File), 'Non FED3_File passed to poke_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    correct_pokes = df['Correct_Poke']
    if poke_show_correct:
        y = df['Poke_Time'][correct_pokes == 1]
        if poketime_cutoff is not None:
            y[y > poketime_cutoff] = np.nan
        x = y.index
        ax.scatter(x, y, color='mediumseagreen', label = 'correct pokes', s=5)
    if poke_show_error:
        y = df['Poke_Time'][correct_pokes == 0]
        if poketime_cutoff is not None:
            y[y > poketime_cutoff] = np.nan
        x = y.index
        ax.scatter(x, y, color='indianred', label = 'error pokes', s=5)
    if poke_show_left:
        try:
            where = df['Left_Poke_Count'].where(df['Event'] == 'Poke', np.nan).ffill()
            diff = where.diff()
        except:
            diff = df['Left_Poke_Count'].diff()
        y = df['Poke_Time'][diff > 0]
        if poketime_cutoff is not None:
            y[y > poketime_cutoff] = np.nan
        x = y.index
        ax.scatter(x, y, color='cornflowerblue', label = 'left pokes')
    if poke_show_right:
        try:
            where = df['Right_Poke_Count'].where(df['Event'] == 'Poke', np.nan).ffill()
            diff = where.diff()
        except:
            diff = df['Right_Poke_Count'].diff()
        y = df['Poke_Time'][diff > 0]
        if poketime_cutoff is not None:
            y[y > poketime_cutoff] = np.nan
        x = y.index
        ax.scatter(x, y, color='gold', label = 'right pokes')
    date_format_x(ax, x[0], x[-1])
    ax.set_xlabel('Time')
    ylabel = 'Poke Time (s)'
    ax.set_ylabel(ylabel)
    title = ('Poke Time for ' + FED.filename)
    ax.set_title(title)
    if shade_dark:
        shade_darkness(ax, min(df.index), max(df.index),
                       lights_on=lights_on,
                       lights_off=lights_off)
    ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

#---Progressive Ratio Plots
def pr_plot(FEDs, break_hours, break_mins, break_style, **kwargs):
    """
    FED3 Viz: Make a bar plot showing the breakpoint (max pellets or pokes
    reached before a period of inactivity) for multiple files.  Works best
    for progressive ratio data

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    break_hours : int
        Number of hours of inactivity to use for the breakpoint
    break_mins : TYPE
        Number of minutes of inactivity to use for the breakpoint (in addition
        to the break_hours)
    break_style : str
        "pellets" or "pokes"
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File), 'Non FED3_File passed to pr_plot()'
    delta = datetime.timedelta(hours=break_hours, minutes=break_mins)
    ys = []
    color_gradient_divisions = [(1/len(FEDs))*i for i in range(len(FEDs))]
    cmap = mpl.cm.get_cmap('spring')
    color_gradients = cmap(color_gradient_divisions)
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
        if isinstance(out, pd.Series): #issue with non-unique indexes
            out = out[-1]
        ys.append(out)
    fig_len = min([max([len(FEDs), 4]), 8])
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(fig_len, 5), dpi=125)
    else:
        ax = kwargs['ax']
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

    return fig if 'ax' not in kwargs else None

def group_pr_plot(FEDs, groups, break_hours, break_mins, break_style,
                  break_error, break_show_indvl, **kwargs):
    """
    FED3 Viz: Make a bar plot showing the average break point (max pellets or
    pokes reached before a period of inactivity) for Grouped devices.  Works best
    for progressive ratio data.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    break_hours : int
        Number of hours of inactivity to use for the breakpoint
    break_mins : TYPE
        Number of minutes of inactivity to use for the breakpoint (in addition
        to the break_hours)
    break_style : str
        "pellets" or "pokes"
    break_error : str
        What error bars to show ("SEM", "STD", or "None")
    break_show_indvl : bool
        Whether to show individual observations overlaid on bars.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File), 'Non FED3_File passed to group_pr_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(3.5,5), dpi=125)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    xs = range(len(groups))
    delta = datetime.timedelta(hours=break_hours, minutes=break_mins)
    title = 'Breakpoint'
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

    return fig if 'ax' not in kwargs else None

#---Circadian Plots

def daynight_plot(FEDs, groups, circ_value, lights_on, lights_off, circ_error,
                  circ_show_indvl, **kwargs):
    """
    FED3 Viz: Make a bar plot showing the average of specified values during
    both day and nighttime for Grouped devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    circ_error : str
        What error bars to show ("SEM", "STD", or "None")
    circ_show_indvl : bool
        Whether to show individual observations overlaid on bars.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(5,5), dpi=125)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    bar_width = (.7/len(groups))
    bar_offsets = np.array([bar_width*i for i in range(len(groups))])
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
                    day_slice = df[(df.index>=start) & (df.index<end)].copy()
                    day_vals.append(resample_get_yvals(day_slice,circ_value,
                                                       retrieval_threshold))
                for start, end in nights:
                    night_slice = df[(df.index>=start) & (df.index<end)].copy()
                    night_vals.append(resample_get_yvals(night_slice,circ_value,
                                                         retrieval_threshold))
                group_day_values.append(np.nansum(day_vals)/days_completed)
                group_night_values.append(np.nansum(night_vals)/nights_completed)
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

    return fig if 'ax' not in kwargs else None

def line_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark,
                    lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Make a line plot showing the average 24 hour cycle of a value
    for Grouped devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    circ_error : str
        What error bars to show ("SEM", "STD", or "None")
    circ_show_indvl : bool
        Whether to show individual files as their own lines; if True, error
        bars will not be shown.
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if circ_show_indvl:
        circ_error = "None"
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=150)
    else:
        ax = kwargs['ax']
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
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

    return fig if 'ax' not in kwargs else None

def heatmap_chronogram(FEDs, circ_value, lights_on, **kwargs):
    """
    FED3 Viz: Create a heatmap showing the average 24-hour cycle of a value
    for multiple devices; the average of these devices is also shown.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        return_cb : bool
            return the matplotlib colorbar; really only useful
            within the GUI
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=125)
    else:
        ax = kwargs['ax']
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
    cb = plt.colorbar(im, ax=ax)
    plt.tight_layout()
    if 'return_cb' in kwargs:
        if 'return_cb':
            return cb

    return fig if 'ax' not in kwargs else None

def circle_chronogram(FEDs, groups, circ_value, circ_error, circ_show_indvl, shade_dark,
                      lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Make a polar line plot showing the average 24 hour cycle of a
    value for Grouped devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    groups : list of strings
        Groups to average (based on the group attribute of each FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    circ_error : str
        What error bars to show ("SEM", "STD", or "None")
    circ_show_indvl : bool
        Whether to show individual files as their own lines; if True, error
        bars will not be shown.
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    retrieval_threshold=None
    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if circ_show_indvl:
        circ_error = "None"
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(5,5), dpi=150,
                               subplot_kw=dict(polar=True))
    else:
        ax = kwargs['ax'] # should be a polar axes
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
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
                reindexed.index.name = 'hour'
                if circ_value in ['pellets', 'correct pokes','errors']:
                    reindexed = reindexed.fillna(0)
                y = reindexed
                if circ_show_indvl:
                    x = np.linspace(0, 2*np.pi, 25)
                    wrapped = np.append(y, y[0])
                    ax.plot(x,wrapped,color=colors[i],alpha=.3,linewidth=.8)
                group_vals.append(y)
        group_mean = np.nanmean(group_vals, axis=0)
        label = group
        error_shade = np.nan
        if circ_error == "SEM":
            error_shade = stats.sem(group_vals, axis=0,nan_policy='omit')
            error_shade = np.append(error_shade, error_shade[0])
            label += ' (±' + circ_error + ')'
        elif circ_error == 'STD':
            error_shade = np.nanstd(group_vals, axis=0)
            error_shade = np.append(error_shade, error_shade[0])
            label += ' (±' + circ_error + ')'
        if circ_show_indvl:
            error_shade = np.nan
        if "%" in circ_value:
            ax.set_ylim(0,100)
        x = np.linspace(0, 2*np.pi, 25)
        y = np.append(group_mean, group_mean[0])
        ax.plot(x,y,color=colors[i], label=label)
        ax.fill_between(x, y-error_shade, y+error_shade, color=colors[i],
                        alpha=.3)
    ax.set_xlabel('Hours (since start of light cycle)')
    ax.set_xticks(np.linspace(0, 2*np.pi, 5))
    ax.set_xticklabels([0, 6, 12, 18, None])
    ax.set_title('Chronogram ({})'.format(circ_value), pad=10)
    if shade_dark:
        off = new_index.index(lights_off)
        theta = (off/24)*2*np.pi
        ax.fill_between(np.linspace(theta, 2*np.pi, 100), 0, ax.get_rmax(),
                        color='gray',alpha=.2,zorder=0,label='lights off')
    ax.legend(bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def spiny_chronogram(FEDs, circ_value, resolution, shade_dark, lights_on, lights_off,
                     **kwargs):
    """
    FED3 Viz: Make a spiny polar line plot showing the average 24 hour cycle
    of a value, averaged for several devices.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    circ_value : str
        String value pointing to a variable to plot; any string accepted
        by resample_get_yvals()
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        retrieval_threshold : int or float
            Sets the maximum value when dependent is 'retrieval time'
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """

    def meanbytime(g):
        mindate = g.index.date.min()
        maxdate = g.index.date.max()
        diff = maxdate-mindate
        days = diff.total_seconds()/86400
        days += 1
        return g.mean()/days

    s = "Resolution in minutes must evenly divide one hour."
    assert resolution in [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60], s
    resolution = str(resolution) + 'T'
    retrieval_threshold=None
    t_on = datetime.time(hour=lights_on)

    if 'retrieval_threshold' in kwargs:
        retrieval_threshold = kwargs['retrieval_threshold']
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to daynight_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(5,5), dpi=150,
                               subplot_kw=dict(polar=True))
    else:
        ax = kwargs['ax']
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    group_vals = []
    for FED in FEDs:
        df = FED.data.copy()
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        r = df.groupby([pd.Grouper(freq=resolution)]).apply(resample_get_yvals,
                                                            circ_value,
                                                            retrieval_threshold)
        r = r.groupby([r.index.time]).apply(meanbytime)
        all_stamps = pd.date_range('01-01-2020 00:00:00',
                                   '01-02-2020 00:00:00',
                                   freq=resolution, closed='left').time
        r = r.reindex(all_stamps)
        loci = r.index.get_loc(t_on)
        new_index = pd.Index(pd.concat([r.index[loci:].to_series(), r.index[:loci].to_series()]))
        r = r.reindex(new_index)
        hours = pd.Series([i.hour for i in r.index])
        minutes = pd.Series([i.minute/60 for i in r.index])
        float_index = hours + minutes
        r.index = float_index
        group_vals.append(r)
    group_mean = np.nanmean(group_vals, axis=0)
    if "%" in circ_value:
        ax.set_ylim(0,100)
    x = np.linspace(0, 2*np.pi, len(group_mean)+1)
    for n, val in enumerate(group_mean):
        ax.plot([0, x[n]], [0, val], color='crimson', lw=1)
    ax.set_xlabel('Hours (since start of light cycle)')
    ax.set_xticks(np.linspace(0, 2*np.pi, 5))
    ax.set_xticklabels([0, 6, 12, 18, None])
    ax.set_title('Chronogram ({})'.format(circ_value), pad=10)
    if shade_dark:
        off = r.index.get_loc(lights_off)
        theta = (off/len(group_mean))*2*np.pi
        ax.fill_between(np.linspace(theta, 2*np.pi, 100), 0, ax.get_rmax(),
                        color='gray',alpha=.2,zorder=0,label='lights off')
        ax.legend(bbox_to_anchor=(1,1),loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def day_night_ipi_plot(FEDs, kde, logx, lights_on, lights_off, **kwargs):
    '''
    FED3 Viz: Create a histogram of interpellet intervals aggregated for
    multiple FEDs and separated by day and night.

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    kde : bool
        Whether or not to include kernel density estimation, which plots
        probability density (rather than count) and includes a fit line (see
        seaborn.distplot)
    logx : bool
        When True, plots on a logarithmic x-axis
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    '''
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    for FED in FEDs:
        assert isinstance(FED, FED3_File),'Non FED3_File passed to interpellet_interval_plot()'
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(4,5), dpi=125)
    else:
        ax = kwargs['ax']
    bins = []
    if logx:
        lowest = -2
        highest = 5
        ax.set_xticks(range(lowest,highest))
        ax.set_xticklabels([10**num for num in range(-2,5)])
        c=0
        while c <= highest:
            bins.append(round(lowest+c,2))
            c+=0.1
    else:
        ax.set_xticks([0,300,600,900])
        div = 900/50
        bins = [i*div for i in range(50)]
        ax.set_xlim(-100,1000)
    all_day = []
    all_night = []
    for FED in FEDs:
        df = FED.data
        if 'date_filter' in kwargs:
            s, e = kwargs['date_filter']
            df = df[(df.index >= s) &
                    (df.index <= e)].copy()
        y = df['Interpellet_Intervals'][df['Interpellet_Intervals'] > 0]
        nights = night_intervals(df.index, lights_on, lights_off)
        days = night_intervals(df.index, lights_on, lights_off,
                               instead_days=True)
        day_vals = []
        night_vals = []
        for start, end in days:
            day_vals.append(y[(y.index >= start) & (y.index < end)].copy())
        for start, end in nights:
            night_vals.append(y[(y.index >= start) & (y.index < end)].copy())
        if day_vals:
            all_day.append(pd.concat(day_vals))
        if night_vals:
            all_night.append(pd.concat(night_vals))
    if all_day:
        all_day = pd.concat(all_day)
    if all_night:
        all_night = pd.concat(all_night)
    if logx:
        all_day = [np.log10(val) for val in all_day if not pd.isna(val)]
        all_night = [np.log10(val) for val in all_night if not pd.isna(val)]
    sns.distplot(all_day,bins=bins,label='Day',ax=ax,norm_hist=False,
                 kde=kde, color='gold')
    sns.distplot(all_night,bins=bins,label='Night',ax=ax,norm_hist=False,
                 kde=kde, color='indigo')
    ax.legend(fontsize=8)
    ylabel = 'Density Estimation' if kde else 'Count'
    ax.set_ylabel(ylabel)
    ax.set_xlabel('minutes between pellets')
    ax.set_title('Day Night Interpellet Interval Plot')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None
#---Diagnostic
def battery_plot(FED, shade_dark, lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Plot the battery life for a device.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to battery_plot()'
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=125)
    else:
        ax = kwargs['ax']
    x = df.index
    y = df['Battery_Voltage']
    ax.plot(x,y,c='orange')
    title = ('Battery Life for ' + FED.filename)
    ax.set_title(title)
    ax.set_ylabel('Battery (V)')
    ax.set_ylim(0,4.5)
    date_format_x(ax, x[0], x[-1])
    ax.set_xlabel('Date')
    if shade_dark:
        shade_darkness(ax, x[0], x[-1],
                   lights_on=lights_on,
                   lights_off=lights_off)
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

    return fig if 'ax' not in kwargs else None

def motor_plot(FED, shade_dark, lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Plot the motor turns for each pellet release.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
        date_filter : array
            A two-element array of datetimes (start, end) used to filter
            the data
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to battery_plot()'
    df = FED.data
    if 'date_filter' in kwargs:
        s, e = kwargs['date_filter']
        df = df[(df.index >= s) &
                (df.index <= e)].copy()
    if 'ax' not in kwargs:
        fig, ax = plt.subplots(figsize=(7,3.5), dpi=125)
    else:
        ax = kwargs['ax']
    x = df.index
    y = df['Motor_Turns']
    ax.scatter(x,y,s=3,c=y,cmap='cool',vmax=100)
    title = ('Motor Turns for ' + FED.filename)
    ax.set_title(title)
    ax.set_ylabel('Motor Turns')
    if max(y) < 100:
        ax.set_ylim(0,100)
    date_format_x(ax, x[0], x[-1])
    ax.set_xlabel('Date')
    if shade_dark:
        shade_darkness(ax, x[0], x[-1],
                   lights_on=lights_on,
                   lights_off=lights_off)
        ax.legend(bbox_to_anchor=(1,1), loc='upper left')
    plt.tight_layout()

#---Stats
def fed_summary(FEDs, meal_pellet_minimum=1, meal_duration=1,
                motor_turns_thresh=10, lights_on=7, lights_off=19):
    """
    FED3 Viz: generate a DataFrame of summary stats for multiple feds

    Parameters
    ----------
    FEDs : list of FED3_File objects
        FED3 files (loaded by load.FED3_File)
    meal_pellet_minimum : int
        minimum pellets to constitute a meal
    meal_duration : int
        amount of time to allow before a new meal is assigned
    motor_turns_thresh : int, optional
        Threshold of motor turns to count how many have surpassed. The default is 10.
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.

    Returns
    -------
    output : pandas.DataFrame
        table of summary statistics for each file, with average and
        standard deviation for all files
    """
    if not isinstance(FEDs, list):
        FEDs = [FEDs]
    output_list = []
    for fed in FEDs:
        df = fed.data
        v = fed.basename
        results = pd.DataFrame(columns=[v])
        results.index.name = 'Variable'
        nights = night_intervals(df.index, lights_on, lights_off)
        days = night_intervals(df.index, lights_on, lights_off,
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
                                meal_pellet_minimum=meal_pellet_minimum,
                                meal_duration=meal_duration)
            results.loc['Number of Meals',v] =  meals.max()
            results.loc['Average Pellets per Meal',v] =  meals.value_counts().mean()
            d = len(meals) * 100 if len(meals) > 0 else 1
            results.loc['% Pellets within Meals',v] =  (len(meals.dropna())/
                                                        d)

        #pokes
        total_pokes = df['Left_Poke_Count'].max()+df['Right_Poke_Count'].max()
        d = total_pokes * 100 if total_pokes else 1
        results.loc['Total Pokes',v] = total_pokes
        if all(pd.isna(df['Correct_Poke'])):
            results.loc['Left Pokes (%)',v] = df['Left_Poke_Count'].max()/d
        else:
            results.loc['Correct Pokes (%)',v] = df['Correct_Poke'].sum()/d


        #other
        results.loc['Recording Duration (Hours)', v] = hours
        battery_use = (df['Battery_Voltage'][-1] - df['Battery_Voltage'][0])
        results.loc['Battery Change (V)', v] = battery_use
        results.loc['Battery Rate (V/hour)', v] = battery_use / hours
        motor_turns = df['Motor_Turns'][df['Motor_Turns'] > 0]
        results.loc['Motor Turns (Mean)', v] = motor_turns.mean()
        results.loc['Motor Turns (Median)', v] = motor_turns.median()
        motor_col = 'Motor Turns Above ' + str(motor_turns_thresh)
        results.loc[motor_col, v] = (motor_turns[motor_turns >= motor_turns_thresh]).size

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
            if len(portions) == 0:
                continue
            results.loc['Pellets Taken' + name, v] = np.sum([d['Pellet_Count'].max()-d['Pellet_Count'].min()
                                                             for d in portions])
            results.loc['Pellets per Hour' + name, v] = np.sum([d['Pellet_Count'].max()-d['Pellet_Count'].min()
                                                             for d in portions])/hourz
            concat_meals = pd.concat([d['Interpellet_Intervals'] for d in portions])
            concat_meals = label_meals(concat_meals.dropna(),
                                       meal_pellet_minimum=meal_pellet_minimum,
                                       meal_duration=meal_duration)
            d = len(concat_meals) if len(concat_meals) > 0 else 1
            results.loc['Number of Meals' + name, v] = concat_meals.max()
            results.loc['Average Pellets per Meal' + name, v] = concat_meals.value_counts().mean()
            results.loc['% Pellets within Meals' + name, v] = (len(concat_meals.dropna())/
                                                               d)*100
            left_pokes = np.sum([d['Left_Poke_Count'].max() - d['Left_Poke_Count'].min()
                                 for d in portions])
            right_pokes = np.sum([d['Right_Poke_Count'].max() - d['Right_Poke_Count'].min()
                                 for d in portions])
            total_pokes = left_pokes + right_pokes
            results.loc['Total Pokes' + name,v] = total_pokes
            d = total_pokes if total_pokes > 0 else 1
            if all(pd.isna(df['Correct_Poke'])):
                results.loc['Left Pokes (%)'+name,v] = left_pokes / d *100
            else:
                correct_pokes = np.sum([d['Correct_Poke'].sum() for d in portions])
                results.loc['Correct Pokes (%)'+name,v] = correct_pokes / d * 100
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

#---Unused by FED3 Viz

def old_diagnostic_plot(FED, shade_dark, lights_on, lights_off, **kwargs):
    """
    FED3 Viz: Make a 3-panel plot showing the pellet retrieval, motor turns,
    and battery life over time.

    Parameters
    ----------
    FED : FED3_File object
        FED3 data (from load.FED3_File)
    shade_dark : bool
        Whether to shade lights-off periods
    lights_on : int
        Integer between 0 and 23 denoting the start of the light cycle.
    lights_off : int
        Integer between 0 and 23 denoting the end of the light cycle.
    **kwargs :
        ax : matplotlib.axes.Axes
            Axes to plot on, a new Figure and Axes are
            created if not passed
        **kwargs also allows FED3 Viz to pass all settings to all functions.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    assert isinstance(FED, FED3_File),'Non FED3_File passed to diagnostic_plot()'
    df = FED.data
    fig, (ax1,ax2,ax3) = plt.subplots(3,1,sharex=True, figsize=(7,5),dpi=125)
    ax1.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.subplots_adjust(hspace=.1)
    y = df['Pellet_Count'].drop_duplicates()
    x = y.index
    ax1.scatter(x,y,s=1,c='green')
    ax1.set_ylabel('Cumulative Pellets')

    ax2.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
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

    return fig if 'ax' not in kwargs else None