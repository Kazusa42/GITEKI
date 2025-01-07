# -*- coding:utf-8 -*-
# !/usr/bin/env python
#---------------------------------------------------------------------------------
# Author: Zhang
#
# Create Date: 2024/11/14
# Last Update on: 2024/11/26
#
# FILE: component.py
# Description: Basic components are defined here
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# IMPORT REQUIRED PACKAGES HERE

import os
import sys
import time
import platform
import openpyxl

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.components as comps
import utils.instrument as instr

# END OF PACKAGE IMPORT
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# DEFINE FUNCTIONS HERE


def measure_obw_and_sbw(spectrun_analyzer: instr.SpectrumAnalyzer, standard: dict,
                        working_dir: str, rule=r'49_27_3', method=r'general') -> dict:
    """
    Measure the OBW and SBW of a device

    Params:
        spectrum_analyzer: an instance of class SpectrumAnalyzer
        standard: GITEKI standard about OBW and SBW
        working_dir: where the main script is executed, bt used to store data
        rule: 49_27_3 or 49_27_4
    
    Return: 
        measurement result in a dict
    """

    # stop sweep
    spectrun_analyzer.config(param='continues_sweep', value='OFF')

    # wait for board launch up
    # TODO: use script to launch up board
    user_input = input('Waiting for board launch up. Enter anything to start measurement.')

    # config sepctrum analyzer and start continuous sweep
    print(f"Starting the OBW and SBW measurement.")
    spectrun_analyzer.config(standard[rule]['measure'][method]['configure'])

    # set power threshold of OBW to 99%
    spectrun_analyzer.config(param='obw_percent', value='99PCT')
    # measure OBW use the build-in function
    spectrun_analyzer.config(param='obw_measure', value='SEL OBW', delimiter=':')
    # show marker for lower and upper freq. bound
    spectrun_analyzer.config(param='obw_measure', value='RES? OBW', delimiter=':')

    # wait for the trace becomes stable
    # TODO: find a way to automatically determin if the trace becomes stable
    user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')

    # stop sweep in order to take screenshot and record trace data
    spectrun_analyzer.config(param='continues_sweep', value='OFF')

    # save screenshot
    screenshots_save_dir = os.path.join(working_dir, r'screenshots')
    screenshot = os.path.join(screenshots_save_dir, f'obw_and_sbw_{rule}.png')
    spectrun_analyzer.save_screenshot(screenshot)

    # save trace data
    trace_data_save_dir = os.path.join(working_dir, r'trace_data')
    trace_data_file = os.path.join(trace_data_save_dir, f'obw_and_sbw_{rule}.csv')
    spectrun_analyzer.save_trace(trace_data_file)

    # close temporary markers for obw measurement
    spectrun_analyzer.config(param='obw_measure', value='OFF')

    # calculate SBW and OBW and print result on terminal
    calculator = comps.TraceDataCalculator(trace_data_file, standard[rule]['standard'])
    obw_and_sbw_result = calculator.calculate_obw() | calculator.calculate_sbw()
    
    return obw_and_sbw_result


def measure_peak_power(spectrun_analyzer: instr.SpectrumAnalyzer, standard: dict,
                       working_dir: str, rule=r'49_27_3', method=r'general'):
    """
    Measure the peak power of a device

    Params:
        spectrum_analyzer: an instance of class SpectrumAnalyzer
        standard: GITEKI standard about peak power
        rule: 49-27-3 or 49-27-4
        method: test method. peak has 2 test methods.
                1. general test methods (general); 2. widen RBW to 50MHz (exception)
    """

    # stop sweep
    spectrun_analyzer.config(param='continues_sweep', value='OFF')

    # wait for board launch up
    # TODO: use script to launch up board
    user_input = input('Waiting for board launch up. Enter anything to start measurement.')

    # search step
    # config sepctrum analyzer for search step and start continuous sweep
    print("Starting the search step of peak powre measurement.")
    spectrun_analyzer.config(standard[rule]['search']['configure'])

    # wait for the trace becomes stable
    # TODO: find a way to automatically determin if the trace becomes stable
    user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')

    # stop sweep in order to take screenshot and record trace data
    spectrun_analyzer.config(param='continues_sweep', value='OFF')

    # place a marker to peak
    spectrun_analyzer.place_marker_at_peak()

    # read peak power and freq @ peak power
    peak_search = float(spectrun_analyzer.read_marker_value(axis='Y'))
    freq_at_search = spectrun_analyzer.read_marker_value(axis='X')

    # save screenshot when results get stable
    print("Starting to save screenshot for search step.")
    screenshots_save_dir = os.path.join(working_dir, r'screenshots')
    screenshot = os.path.join(screenshots_save_dir, f'peak_power_search_{rule}_{method}.png')
    spectrun_analyzer.save_screenshot(screenshot)

    # measure step

    # TODO: use script to launch up board
    user_input = input('Waiting for board launch up. Enter anything to start measurement.')

    # config sepctrum analyzer for measure step and start measure
    print("Starting the measure step of peak powre measurement.")
    spectrun_analyzer.config(param='center_freq', value=freq_at_search)
    spectrun_analyzer.config(standard[rule]['measure'][method]['configure'])

    # stop sweep in order to take screenshot and record trace data
    user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')
    spectrun_analyzer.config(param='continues_sweep', value='OFF')

    # record measurement results
    spectrun_analyzer.place_marker_at_peak()
    peak_measure = float(spectrun_analyzer.read_marker_value(axis='Y'))
    freq_at_measure = spectrun_analyzer.read_marker_value(axis='X')

    # save screenshot
    print("Starting to save screenshot for measure step.")
    screenshot = os.path.join(screenshots_save_dir, f'peak_power_measure_{rule}_{method}.png')
    spectrun_analyzer.save_screenshot(screenshot)

    # TODO: read cable loss and antenna gain to calculate EIRP

    return {
        "peak@search": f"{round(peak_search, 2)}dBm",
        "freq@search": f"{float(freq_at_search) / 1e9}GHz",
        "peak@measure": f"{round(peak_measure, 2)}dBm",
        "freq@measure": f"{float(freq_at_measure) / 1e9}GHz",
    }


def measure_ave_power(spectrum_analyzer: instr.SpectrumAnalyzer, standard: dict,
                      working_dir: str, rule=r'49_27_3', method=r'general'):
    """
    Measure the average power of a device

    Params:
        spectrum_analyzer: an instance of class SpectrumAnalyzer
        standard: GITEKI standard about average power
        rule: 49-27-3 or 49-27-4
        method: test method. average has 2 test methods.
                1. general test methods (general); 2. use RMS detector (exception)
    """

    # stop sweep
    spectrum_analyzer.config(param='continues_sweep', value='OFF')

    # wait for board launch up
    # TODO: use script to launch up board
    user_input = input('Waiting for board launch up. Enter anything to start measurement.')

    # search step
    # config sepctrum analyzer for search step
    print("Starting the search step for average power measurement.")
    spectrum_analyzer.config(standard[rule]['search']['configure'])

    # wait for the trace becomes stable
    # TODO: find a way to automatically determin if the trace becomes stable
    user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')

    # stop sweep in order to take screenshot and record trace data
    spectrum_analyzer.config(param='continues_sweep', value='OFF')

    # place a marker to peak
    spectrum_analyzer.place_marker_at_peak()

    # read freq @ peak power
    freq_at_search = spectrum_analyzer.read_marker_value(axis='X')

    # save screenshot when results get stable
    print("Starting to save screenshot for search step.")
    screenshots_save_dir = os.path.join(working_dir, r'screenshots')
    screenshot = os.path.join(screenshots_save_dir, f'ave_power_search_{rule}_{method}.png')
    spectrum_analyzer.save_screenshot(screenshot)

    # zoom_in step
    span_list = ['100MHz', '10MHz']
    for span in span_list:
        print(f"Starting to zoom in to get accurate search result with span {span}.")
        # set center freq
        spectrum_analyzer.config(param='center_freq', value=freq_at_search)
        # set span
        spectrum_analyzer.config(param='span', value=span)
        # set others and start continues sweep
        spectrum_analyzer.config(standard[rule]['zoom_in']['configure'])
        
        # wait and stop sweep in order to take screenshot and record trace data
        user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')
        spectrum_analyzer.config(param='continues_sweep', value='OFF')

        spectrum_analyzer.place_marker_at_peak()

        # read measurement results and update freq @ peak power
        freq_at_search = spectrum_analyzer.read_marker_value(axis='X')
        peak_search = float(spectrum_analyzer.read_marker_value(axis='Y'))

        # save screenshot
        print(f"Starting to save screenshot for zoom in step with span: {span}.")
        screenshot_name = f'ave_power_zoom_in_span={span}_{rule}_{method}.png'
        screenshot = os.path.join(screenshots_save_dir, screenshot_name)
        spectrum_analyzer.save_screenshot(screenshot)
        
    # measure step
    # config sepctrum analyzer for measure step
    print("Staring the measure step for average power measurement.")
    spectrum_analyzer.config(param='center_freq', value=freq_at_search)
    spectrum_analyzer.config(standard[rule]['measure'][method]['configure'])

    user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')
    # stop sweep in order to take screenshot and record trace data
    spectrum_analyzer.config(param='continues_sweep', value='OFF')

    if method == 'general':
        # save trace data to csv file
        trace_data_save_dir = os.path.join(working_dir, r'trace_data')
        trace_data_file = os.path.join(trace_data_save_dir, f'ave_power_measure_{rule}_{method}.csv')
        spectrum_analyzer.save_trace(trace_data_file)

        # calculate average power from trace data
        calculater = comps.TraceDataCalculator(trace_data_file, {})
        peak_measure = calculater.calculate_ave_power()
        freq_at_measure = freq_at_search

    elif method == 'exception':
        spectrum_analyzer.place_marker_at_peak()
        peak_measure = float(spectrum_analyzer.read_marker_value(axis='Y'))
        freq_at_measure = spectrum_analyzer.read_marker_value(axis='X')

    # save screenshot when results get stable
    print(f"Staring to save screenshot for measure step with method: {method}.")
    screenshot = os.path.join(screenshots_save_dir, f'ave_power_measure_{rule}_{method}.png')
    spectrum_analyzer.save_screenshot(screenshot)

    return {
        "peak@search": f"{round(peak_search, 2)}dBm",
        "freq@search": f"{float(freq_at_search) / 1e9}GHz",
        "peak@measure": f"{round(peak_measure, 2)}dBm",
        "freq@measure": f"{float(freq_at_measure) / 1e9}GHz",
    }


def measure_spurious(spectrun_analyzer: instr.SpectrumAnalyzer, standard: dict, rule=r'49_27_3'):
    """
    Measure the peak and average power of spurious (unwanted) emission

    Params:
        spectrum_analyzer: an instance of class SpectrumAnalyzer
        standard: GITEKI standard about average power of spurious emission
        rule: 49-27-3 or 49-27-4
    """

    spurious_results = {}
    
    # stop sweep
    spectrun_analyzer.config(param='continues_sweep', value='OFF')
    user_input = input('Waiting for board launch up. Enter anything to start measurement.')

    standard_limitation = standard[rule]['standard']

    # spurious emission is measured in several intervals
    freq_intervals = standard[rule]['intervals']
    for freq_range, interval_val in freq_intervals.items():
        flag_peak, flag_ave = 0, 0  # a flag use to see if peak / average spurious is already be assigned
        print(f"Starting to measure spurious @ frequency range: {freq_range}")
        spectrun_analyzer.config(interval_val)  # set start and stop freq

        # search step
        print('Starting the search step.')

        # config spectrum for search step and start measure
        spectrun_analyzer.config(standard[rule]['search']['configure'])
        # wait for the trace becomes stable
        user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')
        spectrun_analyzer.config(param='continues_sweep', value='OFF')

        # read searched data
        spectrun_analyzer.place_marker_at_peak()
        freq_at_search = spectrun_analyzer.read_marker_value(axis='X')
        peak_search = float(spectrun_analyzer.read_marker_value(axis='Y'))

        # save screenshot when results get stable
        screenshot_name = f'spurious_search_{freq_range}.png'
        spectrun_analyzer.save_screenshot(screenshot_name)

        # read limitation
        peak_limitation = float(standard_limitation[freq_range]['peak'].split('dBm')[0])
        ave_limitation = float(standard_limitation[freq_range]['average'].split('dBm')[0])
        print(f"peak@search: {peak_search}; peak limitation: {peak_limitation}; average limitation: {ave_limitation}")

        if ave_limitation >= peak_search:
            spurious_ave = peak_search
            spurious_ave_freq = freq_at_search
            flag_ave = 1
        
        if peak_limitation - peak_search > 3:
            spurious_peak = peak_search
            spurious_peak_freq = freq_at_search
            flag_peak = 1

        if (ave_limitation < peak_search) or (peak_limitation - peak_search < 3):
            # zoom_in step
            span_list = ['100MHz', '10MHz']
            for span in span_list:
                print(f"Start zoom in step with span {span}.")
                # set center freq
                spectrun_analyzer.config(param='center_freq', value=freq_at_search)
                # set span
                spectrun_analyzer.config(param='span', value=span)
                # set the rest and start sweep
                spectrun_analyzer.config(standard[rule]['zoom_in']['configure'])

                # stop sweep in order to take screenshot and record trace data
                user_input = input('Waiting trace becomes stable. Enter anything to stop sweep.')
                spectrun_analyzer.config(param='continues_sweep', value='OFF')

                # read measurement results and update freq_at_peak, peak_search
                spectrun_analyzer.place_marker_at_peak()
                freq_at_search = spectrun_analyzer.read_marker_value(axis='X')
                peak_search = float(spectrun_analyzer.read_marker_value(axis='Y'))

                # save screenshot when results get stable
                screenshot_name = f'spurious_ave_zoom_in_span={span}.png'
                spectrun_analyzer.save_screenshot(screenshot_name)
            
            # after zoom in try to find if peak is already assigned
            if not flag_peak:
                spurious_peak = peak_search
                spurious_peak_freq = freq_at_search

            if not flag_ave:
                # measure step using 0 span
                spectrun_analyzer.config(standard[rule]['measure']["general"]['configure'])
        
                spectrun_analyzer.place_marker_at_peak()
                freq_at_search = spectrun_analyzer.read_marker_value(axis='X')
                peak_search = float(spectrun_analyzer.read_marker_value(axis='Y'))

                spurious_ave = peak_search
                spurious_ave_freq = freq_at_search

                # add the code to calculate the average spurious

        # add results to result dict
        spurious_results[freq_range] = {
            "spurious peak": f"{round(spurious_peak, 2)}dBm",
            "freq@peak": f"{round(float(spurious_peak_freq) / 1e9, 5)}GHz",
            "spurious average (reading)": f"{round(spurious_ave, 2)}dBm",
            "spurious average (calculate)": f"{round(spurious_ave, 2)}dBm",
            "freq@average": f"{round(float(spurious_ave_freq) / 1e9, 5)}GHz",
        }