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
    
    comps.Const.WORKING_DIR = os.path.dirname(__file__)  # working dir

    # dir where all json file is saved
    comps.Const.CFG_DIR = os.path.join(comps.Const.WORKING_DIR, r'config')

    # ensure exists of screenshots folder
    comps.Const.SSHOT_DIR = os.path.join(comps.Const.WORKING_DIR, r'screenshots')
    os.makedirs(comps.Const.SSHOT_DIR, exist_ok=True)

    # ensure exists of trace data folder
    comps.Const.TRACE_DIR = os.path.join(comps.Const.WORKING_DIR, r'trace_data')
    os.makedirs(comps.Const.TRACE_DIR, exist_ok=True)

    # ensure exists of report file folder
    comps.Const.REPORT_DIR = os.path.join(comps.Const.WORKING_DIR, r'report')
    os.makedirs(comps.Const.REPORT_DIR, exist_ok=True)

    # load standard
    # TODO: support radio low in other region
    comps.Const.STANDARD = os.path.join(comps.Const.CFG_DIR, r'GITEKI.json')
    with open(comps.Const.STANDARD, 'r') as f:
        standard_dict = json.load(f)
    print("- [INIT] Standard loaded successfully.")

    # load SCPI commands
    comps.Const.SCPI_COMMANDS = os.path.join(comps.Const.CFG_DIR, r'scpi_commands.json')
    with open(comps.Const.SCPI_COMMANDS, 'r') as f:
        scpi_cmds = json.load(f)['scpi_cmds']
    print("- [INIT] SCPI commands loaded successfully.")

    # init a excel file as report
    start_time = time.strftime(r'%Y_%m_%d_%H_%M', time.localtime())
    report_file = os.path.join(comps.Const.REPORT_DIR, f"{start_time}_report.xlsx")
    print("- [INIT] Report file created successfully.")

    # instance a spectrum analyzer
    ip_addr = input("- Plaese input the ip address of instrument: ")
    sa = instr.SpectrumAnalyzer(scpi_cmds, ip_addr)

    funcs.menu()  # show a welcome menu and command list

    # choose a rule from '49_27_3' and '49_27_4'
    rule = funcs.choose_condition("rule")

    while True:
        user_input = input('- Waiting for command: ').lower()
        if user_input == 'obw' or user_input == 'sbw':
            # perform measurement
            result = funcs.measure_obw_and_sbw(sa, standard_dict, rule)
            print("The measurement result for OBW and SBW is:")
            funcs.show_measurement_result(result)  # display results

            # write report
            test_condition = {"rule": rule, "method": "general"}
            funcs.write_report(report_file, 'Measure condition', test_condition)
            funcs.write_report(report_file, 'obw and sbw', result)

        elif user_input == 'peak power':
            # let user choose a method from 'general' and 'exception'
            method = funcs.choose_condition(
                "method", 'Set RBW to 50MHz at measure step. Easier to pass the test.'
            )

            result = funcs.measure_peak_power(sa, standard_dict, rule, method)
            print("The measurement result for peak power is:")
            funcs.show_measurement_result(result)  # display results

            # write report
            test_condition = {"rule": rule, "method": method}
            funcs.write_report(report_file, 'Measure condition', test_condition)
            funcs.write_report(report_file, 'peak power', result)

        elif user_input == 'ave power':
            # let user choose a method from 'general' and 'exception'
            method = funcs.choose_condition("method", 'Use RMS detector at measure step.')

            result = funcs.measure_ave_power(sa, standard_dict, rule, method)
            print("The measurement result for average power is:")
            funcs.show_measurement_result(result)   # display results

            # write report
            test_condition = {"rule": rule, "method": method}
            funcs.write_report(report_file, 'Measure condition', test_condition)
            funcs.write_report(report_file, 'average power', result)

        elif user_input == 'spurious':
            result = funcs.measure_spurious(sa, standard_dict, rule)

            # write test condition to report
            test_condition = {"rule": rule, "method": "general"}
            funcs.write_report(report_file, 'Measure condition', test_condition)

            # display results on screen and write results to report
            print("The measurement result for average power is:")
            for freq_range, res in result.items():
                print(f"Spurious measurement result @ {freq_range} is:")
                funcs.show_measurement_result(res)
                print()
                funcs.write_report(report_file, f'spurious @ {freq_range}', res)

        elif user_input == 'plot':
            ploter = comps.TracePlot(comps.Const.TRACE_DIR)
            ploter.plot(mask=standard_dict['masks'][rule])

        elif user_input == 'set rule':
            rule = funcs.choose_condition("rule")

        elif user_input == 'exit':
            sa.close()
            sys.exit("Exiting by user input...")
            
        else:
            print(f"Unsupported command: {user_input}.")


if __name__ == "__main__":
    main()


# END OF FILE
#---------------------------------------------------------------------------------