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
    def __init__(self, trace_dir='trace_data'):
        self.trace_files = [
            f for f in os.listdir(trace_dir) if f.startswith('trace')
        ]
        self._verify_data_integrity()
        self.data = self._load_data(trace_dir)

    def _verify_data_integrity(self, p_end=r'~([\d.]+)\.csv', p_start=r'_([\d.]+)~'):
        trace_files = sorted(self.trace_files,
                             key=lambda name: float(re.search(p_start, name).group(1)))
        for idx in range(len(trace_files) - 1):
            curr_end = re.search(p_end, trace_files[idx]).group(1)
            next_start = re.search(p_start, trace_files[idx + 1]).group(1)
            if curr_end != next_start:
                missing_freq = f"{curr_end}~{next_start}"
                raise FileNotFoundError(f"Missing trace for freq range: {missing_freq}")
        self.trace_files = trace_files
            
    def _load_data(self, trace_dir) -> pd.DataFrame:
        density, all_data = float('inf'), []
        for f in self.trace_files:
            df = pd.read_csv(os.path.join(trace_dir, f)).apply(pd.to_numeric, errors='coerce')
            h_idx = df.iloc[:, 0].apply(pd.to_numeric, errors='coerce').first_valid_index()
            data = df.iloc[h_idx:, :2]
            data.iloc[:, 0] /= 1e9  # Convert freq to GHz
            all_data.append(data)

            start_freq, end_freq = data.iloc[0, 0], data.iloc[-1, 0]
            t_density = (len(data) * 1e6) / (end_freq - start_freq)
            density = min(t_density, density)
        
        sampled_data = []
        for data in all_data:
            start_freq, end_freq = data.iloc[0, 0], data.iloc[-1, 0]
            interval = max(1, int((len(data) * 1e6) / ((end_freq - start_freq) * density)))
            sampled_data.append(data.iloc[np.arange(0, len(data), interval)])
        return pd.concat(sampled_data, axis=0)
    
    def _build_mask(self, mask: dict) -> dict:
        """
        mask: giteki_dict['masks'][rule]
        """
        new_mask = {'freq': [], 'ave_limit': [], 'peak_limit': []}
        def add(freq, peak, ave):
            new_mask['freq'].append(float(freq))
            new_mask['ave_limit'].append(float(ave))
            new_mask['peak_limit'].append(float(peak))

        obw, tmp_mask = mask['obw'], mask.copy()
        del tmp_mask['obw']
        for freq_range, limit in tmp_mask.items():
            if freq_range != obw:
                for idx in [0, 1]:
                    freq = float(freq_range.split('~')[idx])
                    if freq not in new_mask['freq']:
                        add(freq, limit['peak'], limit['ave'])
            else:
                freq = float(limit['dividing_freq'])
                add(freq, limit['peak'], limit['ave1'])
                freq = float(freq_range.split('~')[1])
                if freq not in new_mask['freq']:
                    add(freq, limit['peak'], limit['ave2'])
        return new_mask
    
    def plot(self, mask: dict = None, figsize=(18, 6)):
        plt.figure(figsize=figsize)
        plt.plot(self.data.iloc[:, 0], self.data.iloc[:, 1], label='Trace Data')
        if mask:
            new_mask = self._build_mask(mask)
            plt.step(new_mask['freq'], new_mask['ave_limit'], color='red', label='Ave. Mask')
            plt.step(new_mask['freq'], new_mask['peak_limit'], color='green', label='Peak Mask')
        plt.xlabel('Freq. [GHz]')
        plt.ylabel('Power [dBm]')
        plt.grid(True)
        plt.legend()
        plt.show()


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