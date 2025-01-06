import os
import re
import math
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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
        obw = mask['obw']
    
        tmp_mask = mask.copy()
        del tmp_mask['obw']
        for freq_range, limit in tmp_mask.items():
            if freq_range != obw:
                for idx in [0, 1]:
                    freq = float(freq_range.split('~')[idx])
                    if freq not in new_mask['freq']:
                        new_mask['freq'].append(freq)
                        new_mask['ave_limit'].append(float(limit['ave']))
                        new_mask['peak_limit'].append(float(limit['peak']))
            else:
                d_freq = float(limit['dividing_freq'])
                new_mask['freq'].append(d_freq)
                new_mask['ave_limit'].append(float(limit['ave1']))
                new_mask['peak_limit'].append(float(limit['peak']))

                freq = float(freq_range.split('~')[1])
                if freq not in new_mask['freq']:
                    new_mask['freq'].append(freq)
                    new_mask['ave_limit'].append(float(limit['ave2']))
                    new_mask['peak_limit'].append(float(limit['peak']))
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


with open(r'C:\Users\a5149517\Desktop\GITEKI\config\GITEKI.json', 'r') as f:
    giteki_dict = json.load(f)

tmp = TracePlot(r'C:\Users\a5149517\Desktop\GITEKI\trace_data')
tmp.plot(giteki_dict['masks']['49_27_4'])
