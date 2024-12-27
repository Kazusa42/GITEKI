# -*- coding:utf-8 -*-
# !/usr/bin/env python
#---------------------------------------------------------------------------------
# Author: Zhang
#
# Create Date: 2024/11/14
# Last Update on: 2024/11/15
#
# FILE: component.py
# Description: Basic components are defined here
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# IMPORT REQUIRED PACKAGES HERE

import os
import re
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# END OF PACKAGE IMPORT
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# DEFINE CLASS HERE

class TraceDataCalculator:
    """
    A class to calculate OBW, SBW and average power
    """
    def __init__(self) -> None:
        self.data = pd.DataFrame()

    def read_trace_data(self, file_path: str):
        # load raw data from csv file
        self.df = pd.read_csv(file_path, header=None)
        self.df = self.df.apply(pd.to_numeric, errors='coerce')

        # extract valid data
        data_header_index = self.df[0].apply(pd.to_numeric, errors='coerce').first_valid_index()
        self.data = self.df.iloc[data_header_index:, :2]
        self.data.columns = ['freq', 'pow_dBm']
        self.data['pow_mW'] = 10 ** (self.data['pow_dBm'] / 10.0)  # Convert dBm to mW
    
    def calculate_obw(self, obw_power_percent=0.99) -> dict:
        # Compute cumulative power percentage
        cumulative_percent = self.data['pow_mW'].cumsum() / self.data['pow_mW'].sum()
        thre = (1 - float(obw_power_percent)) / 2.0

        # Determine OBW freq bounds based on cumulative power percentage
        lower_freq = self.data.loc[cumulative_percent <= thre, 'freq'].iloc[-1] / 1e9       # GHz
        upper_freq = self.data.loc[cumulative_percent >= (1 - thre), 'freq'].iloc[0] / 1e9  # GHz
        obw = round((upper_freq - lower_freq) * 1e3, 2)  # MHz
        return obw, lower_freq, upper_freq

    def calculate_sbw(self, sbw_power_thre=0.1) -> dict:
        max_power = self.data['pow_mW'].max()
        power_limit = max_power * float(sbw_power_thre)
        
        # Find indices for SBW boundaries
        lower_index = self.data.index[self.data['pow_mW'] > power_limit][0] - 1
        upper_index = self.data.index[self.data['pow_mW'] > power_limit][-1] + 1
        
        lower_sbw = self.data.at[lower_index, 'freq']
        upper_sbw = self.data.at[upper_index, 'freq']
        sbw = round((upper_sbw - lower_sbw) / 1e6, 2)  # MHz
        return sbw
    
    def calculate_ave_power(self, window_size=100) -> float:
        moving_ave = self.data['pow_mW'].rolling(window_size).mean()
        return 10 * math.log10(moving_ave.max())
    
    def calculate_ave_spurious(self, threshold=0.5) -> float:
        mW_power = self.data['pow_mW']
        filtered_power = mW_power[mW_power >= (mW_power.max() * threshold)]
        return 10 * math.log10(filtered_power.mean())


class TracePlot:
    def __init__(self, working_dir: str, trace_data_dir='trace_data') -> None:
        self._trace_data_absdir = os.path.join(working_dir, trace_data_dir)
        self._trace_files = self._sort_trace_data(self._trace_data_absdir)
        self._verify_trace_data_integrity(self._trace_files)
        self._trace_data, self._data_density = self._load_trace_data()
        self.sampled_trace_data = self._sampling()
        self.sampled_trace_data.columns = ['freq', 'pow_dBm']

    @staticmethod
    def _sort_trace_data(trace_data_absdir: str, freq_pattern=r'\((.*?)\)'):
        """Gather all trace data files and ensure data integrity."""
        all_trace_files = sorted([f for f in os.listdir(trace_data_absdir) if f.startswith('trace_data')])
        sorted_trace_files = all_trace_files[1:]
        freqs = re.findall(freq_pattern, ' '.join(sorted_trace_files))

        for i in range(len(freqs) - 1):
            if freqs[i].split('~')[1] != freqs[i + 1].split('~')[0]:
                sorted_trace_files.insert(i + 1, all_trace_files[0])
                break
        return sorted_trace_files
    
    @staticmethod
    def _verify_trace_data_integrity(trace_data_list, freq_pattern=r'\((.*?)\)'):
        freqs = re.findall(freq_pattern, ' '.join(trace_data_list))
        for i in range(len(freqs) - 1):
            curr_stop_freq, next_start_freq = freqs[i].split('~')[1], freqs[i + 1].split('~')[0]
            if curr_stop_freq != next_start_freq:
                missing_freq_range = f"{curr_stop_freq}~{next_start_freq}"
                raise FileNotFoundError(f"Missing trace data for freq range: {missing_freq_range}")

    @staticmethod
    def _convert_freq_to_ghz(freq_str: str) -> float:
        """Convert freq from string to GHz."""
        freq_value, unit = float(freq_str[:-1]), freq_str[-1]
        return freq_value if unit == 'G' else freq_value / 1e3

    def _load_trace_data(self) -> tuple:
        """Load all trace data and calculate the lowest data density."""
        data_density = float('inf')
        trace_data = []
        for trace_file in self._trace_files:
            try:
                df = pd.read_csv(os.path.join(self._trace_data_absdir, trace_file), header=None)
                df = df.apply(pd.to_numeric, errors='coerce')
                data_header_index = df[0].apply(pd.to_numeric, errors='coerce').first_valid_index()
                data = df.iloc[data_header_index:, :2]
                data.iloc[:, 0] /= 1e9  # Convert freq to GHz
                trace_data.append(data)

                # Calculate current data density
                start_freq, end_freq = data.iloc[0, 0], data.iloc[-1, 0]
                curr_density = (len(data) * 1e6) / (end_freq - start_freq)
                data_density = min(data_density, curr_density)
            except Exception as e:
                print(f"Error loading {trace_file}: {e}")
        return trace_data, data_density

    def _sampling(self) -> pd.DataFrame:
        """Sample trace data based on calculated data density."""
        sampled_traces = []
        for trace in self._trace_data:
            start_freq, end_freq = trace.iloc[0, 0], trace.iloc[-1, 0]
            interval = max(1, int((len(trace) * 1e6) / ((end_freq - start_freq) * self._data_density)))
            sampled_traces.append(trace.iloc[np.arange(0, len(trace), interval)])
        return pd.concat(sampled_traces, axis=0)

    def plot(self, mask: dict = None, figsize=(18, 6)) -> None:
        """Plot the trace data with optional mask."""
        plt.figure(figsize=figsize)
        plt.plot(self.sampled_trace_data['freq'], self.sampled_trace_data['pow_dBm'], label='Trace Data')

        if mask:
            new_mask = self._build_mask(mask)
            plt.step(new_mask['freq'], new_mask['ave_limit'], color='red', label='Ave. Mask')
            plt.step(new_mask['freq'], new_mask['peak_limit'], color='green', label='Peak Mask')

        plt.xlabel('Freq. [GHz]')
        plt.ylabel('Power [dBm]')
        plt.grid(True)
        plt.legend()
        plt.show()

    def _build_mask(self, mask: dict) -> dict:
        """Build the freq mask for plotting."""
        new_mask = {'freq': [], 'ave_limit': [], 'peak_limit': []}
        for freq_range, limit in mask.items():
            for idx in [0, 1]:
                freq = self._convert_freq_to_ghz(freq_range.split('~')[idx].split('Hz')[0])
                if freq not in new_mask['freq']:
                    new_mask['freq'].append(freq) 
                    new_mask['ave_limit'].append(float(limit['average'].split('dBm')[0]))
                    new_mask['peak_limit'].append(float(limit['peak'].split('dBm')[0]))
        return new_mask


class Const:
    """
    Const is a class designed to simulate constant values in Python.

    This class allows for the definition of constants that cannot be modified
    once they are set. It also enforces that constant names must be in uppercase.
    Attempting to change the value of an existing constant or using a lowercase
    name will raise an exception.

    Attributes:
        None

    Methods:
        __setattr__(name, value): Assigns a value to a constant and raises an error 
                                  if the constant already exists or if the name is 
                                  not in uppercase.
    """
    class ConstError(TypeError):
        """Exception raised when attempting to modify a constant."""
        pass

    class ConstCaseError(ConstError):
        """Exception raised when a constant name is not all uppercase."""
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            # Raise an error if trying to change an existing constant
            raise self.ConstError(f"Cannot change constant '{name}'")
        if not name.isupper():
            # Raise an error if the constant name is not in uppercase
            raise self.ConstCaseError(f"Constant name '{name}' must be uppercase")

        # Set the constant
        self.__dict__[name] = value
    
# END OF FILE
#---------------------------------------------------------------------------------