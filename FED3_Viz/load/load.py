# -*- coding: utf-8 -*-
"""
Class for loading FED3 data (either .csv or .xlsx), adding
extra columns.

@author: https://github.com/earnestt1234
"""

from difflib import SequenceMatcher
import os
import pandas as pd
import numbers
import numpy as np

class FED3_File():
    """Class used by FED3 Viz to .csv and .xlsx FED3 Files"""
    def __init__(self,directory):
        """
        Reads FED3 data, adds variables, and assigns attributes
        based on recording.

        Parameters
        ----------
        directory : str
            Path to the FED3 file (.csv or .xlsx)

        Raises
        ------
        Exception
            An Exception is raised when reading the file fails; generally
            occurs if the file is not tabular or if it is missing the
            FED3 "MM:DD:YYYY hh:mm:ss" column.
        """
        self.directory = os.path.abspath(directory).replace('\\','/')
        self.fixed_names = ['Device_Number',
                            'Battery_Voltage',
                            'Motor_Turns',
                            'Session_Type',
                            'Event',
                            'Active_Poke',
                            'Left_Poke_Count',
                            'Right_Poke_Count',
                            'Pellet_Count',
                            'Retrieval_Time',]
        
        self.basename = os.path.basename(directory)
        splitext = os.path.splitext(self.basename)
        self.filename = splitext[0]
        self.extension = splitext[1].lower()
        self.foreign_columns=[]
        try:
            read_opts = {'.csv':pd.read_csv, '.xlsx':pd.read_excel}
            func = read_opts[self.extension]
            self.data = func(directory,
                                parse_dates=True,
                                index_col='MM:DD:YYYY hh:mm:ss')          
            for column in self.data.columns:
                for name in self.fixed_names:
                    likeness = SequenceMatcher(a=column, b=name).ratio()
                    if likeness > 0.85:
                        self.data.rename(columns={column:name}, inplace=True)
                        break
                    self.foreign_columns.append(column)
        except Exception as e:
            raise e
        self.missing_columns = [name for name in self.fixed_names if
                                name not in self.data.columns]           
        self.events = len(self.data.index)
        self.end_time = pd.Timestamp(self.data.index.values[-1])
        self.start_time = pd.Timestamp(self.data.index.values[0])
        self.duration = self.end_time-self.start_time
        self.add_elapsed_time()
        self.add_binary_pellet_count()
        try:
            self.reassign_events()
        except:
            pass
        self.add_interpellet_intervals()
        self.add_correct_pokes()
        self.group = []
        self.mode = self.determine_mode()
        self.handle_retrieval_time()

    def __repr__(self):
        """Shows the directory used to make the file."""
        return 'FED3_File("' + self.directory + '")'
    
    def add_elapsed_time(self):
        """pandas Timedelta relative to starting point for each row.
        Stored in new Elapsed_Time column"""
        events = self.data.index
        elapsed_times = [event - self.start_time for event in events]
        self.data['Elapsed_Time'] = elapsed_times
        
    def add_binary_pellet_count(self):
        """Convert cumulative pellet count to binary value for each row.
        Stored in new Binary_Pellets column."""
        self.data['Binary_Pellets'] = self.data['Pellet_Count'].diff()
        pos = self.data.columns.get_loc('Binary_Pellets')
        self.data.iloc[0,pos] = 0
    
    def add_interpellet_intervals(self):
        """Compute time between each pellet retrieval.
        Stored in new Interpellet_Intervals column.  When loading
        concatenated files (from load.fed_concat()), first IPIs for
        the concatenated files are skipped."""
        inter_pellet = np.array(np.full(len(self.data.index),np.nan))
        c=0
        for i,val in enumerate(self.data['Binary_Pellets']):         
            if val == 1:
                if c == 0:
                    c = i
                else:
                    inter_pellet[i] = (self.data.index[i] - 
                                       self.data.index[c]).total_seconds()/60
                    c = i
        self.data['Interpellet_Intervals'] = inter_pellet
        if 'Concat_#' in self.data.columns:
            if not any(self.data.index.duplicated()): #this can't do duplicate indexes
                #thanks to this answer https://stackoverflow.com/a/47115490/13386979
                dropped = self.data.dropna(subset=['Interpellet_Intervals'])
                pos = dropped.index.to_series().groupby(self.data['Concat_#']).first()
                self.data.loc[pos[1:],'Interpellet_Intervals'] = np.nan
    
    def add_correct_pokes(self):
        """Compute whether each poke was correct or not.  This process returns
        numpy NaN if files are in the older format (only pellets logged).  Stored
        in a new Correct_Poke column, also creates Binary_Left_Pokes and
        Binary_Right_Pokes."""
        df = self.data
        df['Binary_Left_Pokes']  = df['Left_Poke_Count'].diff()
        df['Binary_Right_Pokes'] = df['Right_Poke_Count'].diff()
        df.iloc[0,df.columns.get_loc('Binary_Left_Pokes')] = df['Left_Poke_Count'][0]
        df.iloc[0,df.columns.get_loc('Binary_Right_Pokes')] = df['Right_Poke_Count'][0]
        df['Correct_Poke'] = df.apply(lambda row: self.is_correct_poke(row), axis=1)
        df['Correct_Poke'] = df['Correct_Poke'].astype(float)
        
    def is_correct_poke(self,row):
        """For each poke event against the active poke column to verify correctness."""
        try:
            if row['Event'] == 'Poke':
                return (row['Active_Poke'] == 'Left' and row['Binary_Left_Pokes'] == 1 or
                        row['Active_Poke'] == 'Right' and row['Binary_Right_Pokes'] )
            else:
                return np.nan
        except:
            return np.nan
    
    def determine_mode(self):
        """Find the recording mode of the file.  Returns the mode as a string."""
        mode = 'Unknown'
        column = pd.Series()
        for name in ['FR_Ratio',' FR_Ratio','Mode','Session_Type']:
            if name in self.data.columns:
                column = self.data[name]
        if not column.empty:
            if all(isinstance(i,int) for i in column):
                if len(set(column)) == 1:
                    mode = 'FR' + str(column[0])
                else:
                    mode = 'PR'
            elif 'PR' in column[0]:
                mode = 'PR'
            else:
                mode = str(column[0])
        return mode
    
    def handle_retrieval_time(self):
        """Convert the Retrieval_Time column to deal with non-numeric entries.
        Currently, all are converted to np.nan.  Also, sets NaN retrieval
        times to 0 when there is a pellet event.  Issue due to very short
        retrieval times (<1 second) being logged as 0.  Likely will be
        fixed in future FED code."""
        self.data['Retrieval_Time'] = pd.to_numeric(self.data['Retrieval_Time'],errors='coerce')
        self.data.loc[(self.data['Event'] == 'Pellet') &
                      pd.isnull(self.data['Retrieval_Time']), 'Retrieval_Time'] = 0
    
    def reassign_events(self):
        """Reassign the "Event" column based on changes in the pellet and poke
        counts.  Catches some errors with improper event logging."""
        events = ["Pellet" if v else 'Poke' for v in self.data['Binary_Pellets']]
        self.data['Event'] = events
     
class FedCannotConcat(Exception):
    """Error when FEDs can't be concatendated"""
    pass

def is_concatable(feds):
    """
    Determines whether or not FED3_Files can be concatenated, (based on whether
    their start and end times overlap).

    Parameters
    ----------
    feds : array
        an array of FED3_Files

    Returns
    -------
    bool

    """
    sorted_feds = sorted(feds, key=lambda x: x.start_time)
    for i, file in enumerate(sorted_feds[1:], start=1):
        if file.start_time <= sorted_feds[i-1].end_time:
            return False
    return True
        
def fed_concat(feds):
    """
    Concatenates the data of multiple FED3_Files into a single DataFrame.
    It will only contain the default FED3 columns, but loading it into
    FED3 Viz can generate additional columns and metrics.

    Parameters
    ----------
    feds : array
        an array of FED3_Files

    Returns
    -------
    pandas.DataFrame

    """
    if not is_concatable(feds):
        raise FedCannotConcat('FED file dates overlap, cannot concat')
    output=[]
    original_names = ['Device_Number',
                      'Battery_Voltage',
                      'Motor_Turns',
                      'Session_Type',
                      'Event',
                      'Active_Poke',
                      'Left_Poke_Count',
                      'Right_Poke_Count',
                      'Pellet_Count',
                      'Retrieval_Time',]
    for fed in feds:
        cols = fed.data.columns
        for name in original_names:
            if name not in cols:
                original_names.remove(name)
    offsets = {}
    sorted_feds = sorted(feds, key=lambda x: x.start_time)
    for i, fed in enumerate(sorted_feds):
        df = fed.data.copy().loc[:,original_names]
        if i==0:
            df['Concat_#'] = i
            output.append(df)
            for col in['Pellet_Count', 'Left_Poke_Count','Right_Poke_Count']:
                if col in df.columns:
                    offsets[col] = df[col].max()
        else:
            df['Concat_#'] = i
            for name, offset in offsets.items():
                df[name] += offset
                offsets[name] = df[name].max()
            output.append(df)
    output = pd.concat(output)
    if len(set([i.mode for i in feds])) == 1:
        output.loc[:,'Mode'] = feds[0].mode
    return output