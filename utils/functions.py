# -*- coding:utf-8 -*-
# !/usr/bin/env python
#---------------------------------------------------------------------------------
# Author: Zhang
#
# Create Date: 2024/11/14
# Last Update on: 2024/12/04
#
# FILE: component.py
# Description: Basic components are defined here
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# IMPORT REQUIRED PACKAGES HERE

import os
import sys
import time
import math
import platform
import openpyxl

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import utils.components as comps
import utils.instrument as instr

# END OF PACKAGE IMPORT
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# DEFINE FUNCTIONS HERE

def menu() -> None:
    print(f"Initialize successfully. Starting the program...")
    time.sleep(2)
    os.system('cls') if platform.system() == 'Windows' else os.system('clear')
    print(f'# ----------------------------------------------------------------------------- #')
    print(f'# GITEKI PRE-TEST AUTOMATION TOOL')
    print(f'# INTERNAL USE ONYL @ RENESAS/A&C/CONN/LIC/ACENG')
    print(f'# AUTHOR: ZHANG')
    print(f'# CREATED ON: 2024/11/14')
    print(f'# For now (2024/11/28), all output about power is reading value, not EIRP.')
    print(f'# ----------------------------- COMMAND LIST ---------------------------------- #')
    print(f'# \"obw\" or \"sbw\"  :     Start the measurement of OBW and SBW.')
    print(f'# \"peak power\"    :     Start the measurement of peak power.')
    print(f'# \"ave power\"     :     Start the measurement of average power.')
    print(f'# \"spurious\"      :     Start the measurement of peak and averagr spurious.')
    print(f'# \"plot\"          :     Plot trace data and mask. (Mannully save needed)')
    print(f'# \"set rule\"      :     Re-select the rule (49_27_3 or 49_27_4).')
    print(f'# \"exit\"          :     Exit the program.')
    print(f'# ----------------------------------------------------------------------------- #')
    print(f'')

def show_measurement_result(result_dict: dict, headers=None):
    def format_row(*args):
        return "| " + " | ".join(f"{str(arg):<{col_widths[i]}}" for i, arg in enumerate(args)) + " |"
    
    if headers is None:
        headers = ["Item", "Value", "Passed/Failed"]
    
    col_widths = [max(len(str(key)) for key in result_dict.keys())]
    for i in range(1, len(headers)):
        col_widths.append(
            max(
                len(str(value[i - 1])) if isinstance(value, list) else len(str(value))
                for value in result_dict.values()
            )
        )
    col_widths = [max(width, len(headers[i])) for i, width in enumerate(col_widths)]
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"

    print(separator)
    print(format_row(*headers))
    print(separator)
    for key, value in result_dict.items():
        row = [key] + (value if isinstance(value, list) else [value, "-----"])
        print(format_row(*row[:len(headers)]))
    print(separator)

def show_configure(config_dict: dict):
    keys = list(config_dict.keys())
    values = list(config_dict.values())

    col_widths = [max(len(str(key)), len(str(value))) for key, value in config_dict.items()]

    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"

    def format_row(items):
        return "| " + " | ".join(f"{str(item):<{col_widths[i]}}" for i, item in enumerate(items)) + " |"

    print(separator)
    print(format_row(keys))
    print(separator)
    print(format_row(values))
    print(separator)

def write_report(report_file, text, data_dict):
    try:
        workbook = openpyxl.load_workbook(report_file)
    except FileNotFoundError:
        workbook = openpyxl.Workbook()
    sheet = workbook.active

    row = 1
    while sheet.cell(row=row, column=1).value is not None:
        row += 1

    sheet.cell(row=row, column=1, value=text)
    row += 1

    for key, value in data_dict.items():
        sheet.cell(row=row, column=1, value=key)
        if isinstance(value, list) and len(value) == 2:
            sheet.cell(row=row, column=2, value=value[0])
            sheet.cell(row=row, column=3, value=value[1])
        else:
            sheet.cell(row=row, column=2, value=value)
        row += 1

    workbook.save(report_file)
    workbook.close()

def choose_condition(condition_type) -> str:
    if condition_type == 'rule':
        print("Please select a rule: 1) 49_27_3; 2) 49_27_4.")
        user_input = input("Waiting for index of rule: ")
        return "49_27_3" if user_input == '1' else "49_27_4"
    elif condition_type == 'method':
        print("Please select a method: 1) general; 2) exception.")
        print("  - General  : the basic method describled in rule book.")
        print("  - Exception: other methods, such as wide RBW to 50MHz;")
        print("               or use RMS detector to measure average power.")
        user_input = input("Waiting for index of method: ")
        return "general" if user_input == '1' else "exception"
    else:
        return None

def measure_obw_and_sbw(spectrum_analyzer: instr.SpectrumAnalyzer, standard: dict,
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

    # stop sweep, wait for board launch up
    spectrum_analyzer.config(param='continues_sweep', value='OFF')
    input('Waiting for board launch up. Press enter to start measurement.')

    # config sepctrum analyzer and start continuous sweep
    print(f"Starting the OBW and SBW measurement.")
    spectrum_analyzer.config(standard[rule]['measure'][method]['configure'])

    # set OBW measurement parameters
    spectrum_analyzer.config(param='obw_percent', value='99PCT')
    spectrum_analyzer.config(param='obw_measure', value='SEL OBW', delimiter=':')
    spectrum_analyzer.config(param='obw_measure', value='RES? OBW', delimiter=':')

    # wait for the trace becomes stable
    input('Waiting trace becomes stable. Press enter to stop sweep.')

    # stop sweeping to capture stable data
    spectrum_analyzer.config(param='continues_sweep', value='OFF')

    # save screenshot
    screenshots_save_dir = os.path.join(working_dir, r'screenshots')
    screenshot = os.path.join(screenshots_save_dir, f'obw_and_sbw_{rule}.png')
    spectrum_analyzer.save_screenshot(screenshot)

    # save trace data
    trace_data_save_dir = os.path.join(working_dir, r'trace_data')
    trace_data_file = os.path.join(trace_data_save_dir, f'obw_and_sbw_{rule}.csv')
    spectrum_analyzer.save_trace_to_csv(trace_data_file)

    # close temporary markers for obw measurement
    spectrum_analyzer.config(param='obw_measure', value='OFF')

    # calculate SBW and OBW and union them in one dict
    calculator = comps.TraceDataCalculator(trace_data_file)
    obw_result = calculator.calculate_obw(standard[rule]['standard'])
    sbw_result = calculator.calculate_sbw(standard[rule]['standard'])
    obw_and_sbw_result = obw_result | sbw_result
    
    return obw_and_sbw_result

def measure_peak_power(spectrum_analyzer: instr.SpectrumAnalyzer, standard: dict,
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

    # a unit measurement step, do some measure and capture the peak point value
    def capture_peak_data(step: str) -> tuple:
        print(f"Starting {step} step of peak power measurement.")

        # Configure spectrum analyzer
        if step == "search":
            spectrum_analyzer.config(standard[rule]['search']['configure'])
        elif step == "measure":
            spectrum_analyzer.config(param='center_freq', value=freq_at_search)
            spectrum_analyzer.config(standard[rule]['measure'][method]['configure'])
        # wait trace to stabilize and stop sweeping
        input(f"Waiting trace to stabilize for {step} step. Press Enter to stop sweep.")
        spectrum_analyzer.config(param='continues_sweep', value='OFF')

        # aquire peak point information
        peak_freq, peak_power = spectrum_analyzer.aquire_peak_point()

        # save screenshot for current step
        screenshot = os.path.join(screenshots_save_dir, f'peak_power_{step}_{rule}_{method}.png')
        spectrum_analyzer.save_screenshot(screenshot)

        return peak_power, peak_freq
    
    # init screenshot directory
    screenshots_save_dir = os.path.join(working_dir, 'screenshots')

    # stop sweep, wait for board launch up
    spectrum_analyzer.config(param='continues_sweep', value='OFF')
    spectrum_analyzer.config(param='yaxis_ref_level', value='0dBm')
    input('Waiting for board launch up. Press enter to start measurement.')

    # search step
    peak_search, freq_at_search = capture_peak_data(step='search')

    # measure step
    peak_measure, freq_at_measure = capture_peak_data(step='measure')

    # pass / fail determin

    # calculate correction factor and plus it to reading value
    rbw = 3 if method == 'general' else 50
    correction_factor = 20 * math.log10(float(50.0) / rbw)
    peak = correction_factor + peak_measure

    # load limitation
    limit = float(standard[rule]['standard']['limitation'].split('dBm')[0])
    allowable_dev = float(standard[rule]['standard']['allowable_dev'].split('%')[0]) / 100

    max_limit_mW = (10 ** (limit / 10)) * (1 + allowable_dev)
    max_limit_dBm = 10 * math.log10(max_limit_mW)

    peak_status = f"Passed" if peak <= max_limit_dBm else f"Failed"

    return {
        "peak@search (reading)": f"{round(peak_search, 2)}dBm",
        "freq@search": f"{round(freq_at_search / 1e9, 5)}GHz",
        "peak@measure (reading)": f"{round(peak_measure, 2)}dBm",
        "correction factor": f"{round(correction_factor, 2)}",
        "peak (reading + correction factor)": [f"{round(peak, 2)}dBm", peak_status],
        "freq@measure": f"{round(freq_at_measure / 1e9, 5) }GHz",
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

    # a unit measurement step, do some measure and capture the peak point value
    def capture_peak_data(step: str, span: str = None) -> tuple:
        print(f"Starting {step} step of average power measurement" + (f" with span {span}" if span else "") + ".")

        # Configure analyzer and place marker at peak
        spectrum_analyzer.config(standard[rule][step]['configure'])

        # wait trace to stabilize and stop sweeping
        input(f"Waiting trace to stabilize for {step} step. Press Enter to stop sweep.")
        spectrum_analyzer.config(param='continues_sweep', value='OFF')

        # aquire peak point information
        peak_freq, peak_power = spectrum_analyzer.aquire_peak_point()

        # save screenshot for current step
        screenshot_name = f"ave_power_{step}" + (f"_span={span}" if span else "") + f"_{rule}_{method}.png"
        spectrum_analyzer.save_screenshot(os.path.join(screenshots_save_dir, screenshot_name))

        return peak_power, peak_freq
    
    def get_occupied_freq_range(standard: dict, rule: str) -> str:
        try:
            center_freq_str = standard[rule]['search']['configure']['center_freq']
            center_freq = float(center_freq_str.rstrip('GHz'))

            span_str = standard[rule]['search']['configure']['span'].split('Hz')[0]
            span_value, span_unit = float(span_str[:-1]), span_str[-1]
            span_ghz = span_value if span_unit == 'G' else span_value / 1e3  # 转换为 GHz

            start_freq = center_freq - span_ghz / 2
            stop_freq = center_freq + span_ghz / 2

            return f"{start_freq}GHz~{stop_freq}GHz"

        except KeyError as e:
            return f"Missing key in configuration: {e}"
        except ValueError:
            return "Invalid frequency format in the standard."

    # some init
    screenshots_save_dir = os.path.join(working_dir, 'screenshots')
    trace_data_save_dir = os.path.join(working_dir, 'trace_data')

    # stop sweep and wait for board launch up
    spectrum_analyzer.config(param='continues_sweep', value='OFF')
    spectrum_analyzer.config(param='yaxis_ref_level', value='0dBm')
    input('Waiting for board launch up. Press enter to start measurement.')

    # search step
    peak_search, freq_at_search = capture_peak_data('search')

    # save trace data in order to draw all signal wave and mask
    print("Saving trace data in order to draw all signal wave and mask")
    occupied_freq_range = get_occupied_freq_range(standard, rule)
    trace_data_name = f'trace_data_interval00({occupied_freq_range}).csv'
    trace_data_file = os.path.join(trace_data_save_dir, trace_data_name)
    spectrum_analyzer.save_trace_to_csv(trace_data_file)

    # zoom in step with spans
    for span in ['100MHz', '10MHz']:
        # set span and center freq
        spectrum_analyzer.config({'center_freq': freq_at_search, 'span': span})
        # start zoom in measurement
        peak_search, freq_at_search = capture_peak_data("zoom_in", span)
        
    # measure step
    # config sepctrum analyzer for measure step
    spectrum_analyzer.config(param='center_freq', value=freq_at_search)
    spectrum_analyzer.config(standard[rule]['measure'][method]['configure'])

    # retrieve power for each method and save trace data if needed
    if method == 'general':
        # save trace data to csv file
        trace_data_file = os.path.join(trace_data_save_dir, f'ave_power_measure_{rule}.csv')
        spectrum_analyzer.save_trace_to_csv(trace_data_file)

        # calculate average power from trace data
        calculater = comps.TraceDataCalculator(trace_data_file)
        peak_measure = calculater.calculate_ave_power()
        freq_at_measure = freq_at_search

    elif method == 'exception':  # measure average power with RMS detector
        # wait trace to stabilize and stop sweeping
        input('Waiting trace becomes stable. Press enter to stop sweep.')
        spectrum_analyzer.config(param='continues_sweep', value='OFF')
        freq_at_measure, peak_measure = spectrum_analyzer.aquire_peak_point()

    # save screenshot for measure step
    screenshot_name = f"ave_power_measure_{rule}_{method}.png"
    screenshot = os.path.join(screenshots_save_dir, screenshot_name)
    spectrum_analyzer.save_screenshot(screenshot)

    # pass / fail determin
    if rule == '49_27_3':
        dividing_freq_hz = float(standard[rule]['standard']['dividing_freq'].split('GHz')[0]) * 1e9
        limit_key_suffix = '1' if freq_at_measure <= dividing_freq_hz else '2'
    else:  # rule is 49_27_4
        limit_key_suffix = ''

    limit_key = f"limitation{limit_key_suffix}"
    
    limit = float(standard[rule]['standard'][limit_key].split('dBm')[0])
    allowable_dev = float(standard[rule]['standard']['allowable_dev'].split('%')[0]) / 100

    max_limit_mW = (10 ** (limit / 10)) * (1 + allowable_dev)
    max_limit_dBm = 10 * math.log10(max_limit_mW)

    ave_status = f"Passed" if peak_measure <= max_limit_dBm else f"Failed"

    return {
        "average@search": f"{round(peak_search, 2)}dBm",
        "freq@search": f"{round(freq_at_search / 1e9, 5)}GHz",
        "average@measure": [f"{round(peak_measure, 2)}dBm", ave_status],
        "freq@measure": f"{round(freq_at_measure / 1e9, 5)}GHz",
    }

def measure_spurious(spectrum_analyzer: instr.SpectrumAnalyzer, standard: dict,
                     working_dir: str, rule='49_27_3') -> dict:
    """
    Measure the peak and average power of spurious (unwanted) emission

    Params:
        spectrum_analyzer: an instance of class SpectrumAnalyzer
        standard: GITEKI standard about average power of spurious emission
        rule: 49-27-3 or 49-27-4
    """
    # a unit measurement step, do some measure and capture the peak point value
    def capture_peak_data(freq_range: str, config: dict, step: str) -> tuple:
        
        spectrum_analyzer.config(config)
        input('Waiting trace becomes stable. Press enter to stop sweep.')
        spectrum_analyzer.config(param='continues_sweep', value='OFF')

        spectrum_analyzer.place_marker_at_peak()
        freq_at_search = float(spectrum_analyzer.read_marker_value(axis='X'))
        peak_search = float(spectrum_analyzer.read_marker_value(axis='Y'))

        screenshot_name = f"spurious_{step}_{freq_range}.png"
        screenshot = os.path.join(screenshots_save_dir, screenshot_name)
        spectrum_analyzer.save_screenshot(screenshot)
        return freq_at_search, peak_search
    
    spurious_results = {}

    # Stop sweep and prepare for measurement
    spectrum_analyzer.config(param='continues_sweep', value='OFF')
    input('Waiting for board launch up. Press enter to start measurement.')

    standard_limitation = standard[rule]['standard']
    freq_intervals = standard[rule]['intervals']

    screenshots_save_dir = os.path.join(working_dir, r'screenshots')
    trace_data_save_dir = os.path.join(working_dir, r'trace_data')

    # Measure across frequency intervals
    for index, (freq_range, interval_val) in enumerate(freq_intervals.items()):
        print(f"Measuring spurious @ frequency range: {freq_range}")
        spectrum_analyzer.config(interval_val)

        # search step
        freq_at_search, peak_search = capture_peak_data(
            freq_range, standard[rule]['search']['configure'], 'search'
        )

        # save trace data in order to draw all signal wave and mask
        print("Saving trace data in order to draw all signal wave and mask.")
        trace_data_name = f'trace_data_interval{(index + 1):02}({freq_range}).csv'
        trace_data_file = os.path.join(trace_data_save_dir, trace_data_name)
        spectrum_analyzer.save_trace_to_csv(trace_data_file)

        # Check peak and average limitations
        peak_limit = float(standard_limitation[freq_range]['peak'].split('dBm')[0])
        ave_limit = float(standard_limitation[freq_range]['average'].split('dBm')[0])
        print(f"peak@search: {round(peak_search, 2)}dBm;", end=' ')
        print(f"peak limit: {peak_limit}dBm; average limit: {ave_limit}dBm")

        # Initialize spurious result placeholders
        spurious_peak = spurious_ave = None
        spurious_peak_freq = spurious_ave_freq = None
        spurious_ave_cal = None

        if ave_limit >= peak_search:
            spurious_ave = peak_search
            spurious_ave_freq = freq_at_search

        if peak_limit - peak_search > 3:
            spurious_peak = peak_search
            spurious_peak_freq = freq_at_search

        # zoom-in if peak@search does not meet limitations
        if ave_limit < peak_search or peak_limit - peak_search < 3:
            for span in ['100MHz', '10MHz']:
                print(f"Starting zoom in step with span {span}.")
                spectrum_analyzer.config({'center_freq': freq_at_search, 'span': span})
                freq_at_search, peak_search = capture_peak_data(
                    freq_range, standard[rule]['zoom_in']['configure'], f'zoom_in_span={span}'
                )

            # Update peak if necessary
            spurious_peak = spurious_peak or peak_search
            spurious_peak_freq = spurious_peak_freq or freq_at_search
            spurious_ave_freq = spurious_ave_freq or freq_at_search

            # Zero span measurement for average if necessary
            if spurious_ave is None:
                spectrum_analyzer.config(standard[rule]['measure']['general']['configure'])
                spectrum_analyzer.place_marker_at_peak()
                spurious_ave = float(spectrum_analyzer.read_marker_value(axis='Y'))
                screenshot = os.path.join(screenshots_save_dir, f'spurious_measure_{rule}_{freq_range}_0span.png')
                spectrum_analyzer.save_screenshot(screenshot)

                # save trace data in order to calculate average spurious
                trace_data_name = f'ave_spurious_measure_{rule}_{freq_range}.csv'
                trace_data_file = os.path.join(trace_data_save_dir, trace_data_name)
                spectrum_analyzer.save_trace_to_csv(trace_data_file)

                calculator = comps.TraceDataCalculator(trace_data_file)
                spurious_ave_cal = calculator.calculate_ave_spurious()
        
        # pass / faile determin
        ave_limit = float(standard[rule]['standard'][freq_range]['average'].split('dBm')[0])
        peak_limit = float(standard[rule]['standard'][freq_range]['peak'].split('dBm')[0])

        peak_status = f"Passed" if spurious_peak <= peak_limit else f"Failed"
        reading_ave_status = f"Passed" if spurious_ave <= ave_limit else f"Failed"
        if spurious_ave_cal is not None:
            cal_ave_status = f"Passed" if spurious_ave_cal <= ave_limit else f"Failed"
            res_spurious_ave_cal = f"{round(spurious_ave_cal, 2)}dBm"
        else:
            cal_ave_status = f"Not calculated"
            res_spurious_ave_cal = f"None"

        # Store results in dictionary
        spurious_results[freq_range] = {
            "spurious peak": [f"{round(spurious_peak, 2)}dBm", peak_status],
            "freq@peak": f"{round(spurious_peak_freq / 1e9, 5)}GHz",
            "spurious average (reading)": [f"{round(spurious_ave, 2)}dBm", reading_ave_status],
            "spurious average (calculate)": [res_spurious_ave_cal, cal_ave_status],
            "freq@average": f"{round(spurious_ave_freq / 1e9, 5)}GHz",
        }
        
    return spurious_results