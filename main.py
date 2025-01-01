# -*- coding:utf-8 -*-
# !/usr/bin/env python
#---------------------------------------------------------------------------------
# Author: Zhang
#
# Create Date: 2024/11/15
# Last Update on: 2024/11/26
#
# FILE: main.py
# Description: main entry for GITEKI test automation
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# IMPORT REQUIRED PACKAGES HERE

import os
import sys
import json
import time

import utils.components as comps
import utils.functions as funcs
import utils.instrument as instr


# END OF PACKAGE IMPORT
#---------------------------------------------------------------------------------

def main():

    # working dir
    comps.Const.WORKING_DIR = os.path.dirname(__file__)

    # dir where all json file is saved
    comps.Const.CONFIG_DIR = os.path.join(comps.Const.WORKING_DIR, r'config')
    os.makedirs(comps.Const.CONFIG_DIR, exist_ok=True)

    # dir where all screenshots is saved
    comps.Const.SCREENSHOT_DIR = os.path.join(comps.Const.WORKING_DIR, r'screenshots')
    os.makedirs(comps.Const.SCREENSHOT_DIR, exist_ok=True)

    # dir where all trace data is saved
    comps.Const.TRACE_DATA_DIR = os.path.join(comps.Const.WORKING_DIR, r'trace_data')
    os.makedirs(comps.Const.TRACE_DATA_DIR, exist_ok=True)

    # dir to save report
    comps.Const.REPORT_DIR = os.path.join(comps.Const.WORKING_DIR, r'report')
    os.makedirs(comps.Const.REPORT_DIR, exist_ok=True)

    # load test standard
    comps.Const.GITEKI_STANDARD = os.path.join(comps.Const.CONFIG_DIR, r'GITEKI.json')
    with open(comps.Const.GITEKI_STANDARD, 'r') as f:
        giteki_dict = json.load(f)
    print(" [INIT] GITEKI standard loaded successfully.")

    # load SCPI commands
    comps.Const.SCPI_COMMANDS = os.path.join(comps.Const.CONFIG_DIR, r'scpi_commands.json')
    with open(comps.Const.SCPI_COMMANDS, 'r') as f:
        scpi_cmds = json.load(f)['scpi_cmds']
    print(" [INIT] SCPI commands loaded successfully.")

    # init a excel file as report
    """measurement_start_time = time.strftime(r'%Y_%m_%d_%H_%M', time.localtime())
    report_file = os.path.join(comps.Const.REPORT_DIR, f"{measurement_start_time}_report.xlsx")
    print(" [INIT] Report file created successfully.")"""

    # instance a spectrum analyzer
    ip_addr = input("- Plaese input the ip address of instrument: ")
    spectrum_analyzer = instr.SpectrumAnalyzer(scpi_cmds, ip_addr)

    # show a welcome menu and command list
    funcs.menu()

    # let user choose a rule from '49_27_3' and '49_27_4'
    rule = funcs.choose_condition("rule")
    print(f"#--------------------------------------------------------------#")
    print(f"#  All measurements will be conducted to align rule: {rule}.  #")
    print(f"#--------------------------------------------------------------#\n")

    while True:
        user_input = input('- Waiting for command: ').lower()
        if user_input == 'obw' or user_input == 'sbw':
            # perform measurement
            obw_and_sbw_result = funcs.measure_obw_and_sbw(
                spectrum_analyzer, giteki_dict['OBW_and_SBW'], rule
            )
            # display results on screen
            print("The measurement result for OBW and SBW is:")
            funcs.show_measurement_result(obw_and_sbw_result)

            # write test condition to report
            test_condition = {
                "rule": rule,
                "method": "general"
            }

        elif user_input == 'peak power':
            # let user choose a method from 'general' and 'exception'
            method = funcs.choose_condition("method")

            peak_power_result = funcs.measure_peak_power(
                spectrum_analyzer, giteki_dict['peak_power'], comps.Const.WORKING_DIR, rule, method
            )
            # display results on screen
            print("The measurement result for peak power is:")
            funcs.show_measurement_result(peak_power_result)

            # write test condition to report
            test_condition = {
                "rule": rule,
                "method": method
            }

        elif user_input == 'ave power':
            # let user choose a method from 'general' and 'exception'
            method = funcs.choose_condition("method")

            ave_power_result = funcs.measure_ave_power(
                spectrum_analyzer, giteki_dict['average_power'], comps.Const.WORKING_DIR, rule, method
            )

            # display results on screen
            print("The measurement result for average power is:")
            funcs.show_measurement_result(ave_power_result)

            # write test condition to report
            test_condition = {
                "rule": rule,
                "method": method
            }

        elif user_input == 'spurious':
            spurious_result = funcs.measure_spurious(
                spectrum_analyzer, giteki_dict['spurious'], comps.Const.WORKING_DIR, rule
            )

            # write test condition to report
            test_condition = {
                "rule": rule,
                "method": "general"
            }

            # display results on screen and write results to report
            print("The measurement result for average power is:")
            for freq_range, result in spurious_result.items():
                print(f"Spurious measurement result @ {freq_range} is:")
                funcs.show_measurement_result(result)

        elif user_input == 'plot':
            ploter = comps.TracePlot(comps.Const.WORKING_DIR)
            ploter.plot(mask=giteki_dict['mask'][rule])

        elif user_input == 'set rule':
            rule = funcs.choose_condition("rule")
            print(f"#--------------------------------------------------------------#")
            print(f"#  All measurements will be conducted to align rule: {rule}.  #")
            print(f"#--------------------------------------------------------------#\n")

        elif user_input == 'exit':
            spectrum_analyzer.close()
            sys.exit("Exiting by user input...")
            
        else:
            print(f"Unsupported command: {user_input}.")


if __name__ == "__main__":
    main()


# END OF FILE
#---------------------------------------------------------------------------------