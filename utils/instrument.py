# -*- coding:utf-8 -*-
# !/usr/bin/env python
#---------------------------------------------------------------------------------
# Author: Zhang
#
# Create Date: 2024/11/15
# Last Update on: 2025/01/06
#
# FILE: instrument.py
# Description: Classe SpectrumAnalyzer is defined here
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# IMPORT REQUIRED PACKAGES HERE

import pyvisa
import time

# END OF PACKAGE IMPORT
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# DEFINE CLASS HERE

class SpectrumAnalyzer(object):
    def __init__(self, scpi_cmds: dict, ip_addr: str) -> None:
        self._scpi_cmds = scpi_cmds
        self._wait_sec = 0.5  # retry after 0.5 sec

        self._connect_to_instr(ip_addr)

    def _connect_to_instr(self, ip_addr: str):
        self._rm = pyvisa.ResourceManager()
        try:
            self._instr = self._rm.open_resource(f"TCPIP::{ip_addr}::INSTR")
        except Exception as e:
            raise ConnectionError(f'Connection failed: {e}.')
        
        instr_info = self._instr.query('*IDN?')
        print(f"Connected to: {instr_info.strip()} successfully.")

    def _set_parameter(self, param, value, delimiter=' '):
        if param == 'sweep_time' and value == 'AUTO ON':
            delimiter = ':'
        try:
            cfg_cmd = f"{self._scpi_cmds[param]}{delimiter}{value}"
            self._instr.write(cfg_cmd)
        except KeyError:
            print(f"Parameter '{param}' not found in SCPI commands dict.")

    def config(self, param=None, value=None, delimiter=' '):
        if isinstance(param, dict):
            for key, val in param.items():
                self._set_parameter(key, val, delimiter)

        if isinstance(param, str) and value is not None:
            self._set_parameter(param, value, delimiter)

    def _wait(self):  # prevent overlapping execution of commands
        while True:
            if self._instr.query("*OPC?").strip() == '1':
                break
            time.sleep(self._wait_sec)

    def save_screenshot(self, img_path):
        try:
            self._instr.write("HCOP:DEST 'MMEM'")
            self._instr.write("HCOP:ITEM:ALL")
            self._instr.write("MMEM:NAME 'test.bmp'")
            self._instr.write("HCOP:IMM")

            self._wait()  # prevent overlapping execution of commands
            image_data = self._instr.query_binary_values(
                "MMEM:DATA? 'test.bmp'", datatype='B' ,container=bytearray
            )
            with open(img_path, 'wb') as f:
                f.write(image_data)
            print(f"Screenshot saved.")
        except Exception as e:
            print(f"Failed to save screenshot: {e}")

    def save_trace(self, csv_path):
        def remove_first_line(byte_data: bytearray):
            newline_index = byte_data.find(b'\n')
            if newline_index != -1:
                return byte_data[newline_index + 1:]
            else:
                return bytearray()
             
        try:
            self._instr.write("FORM ASC")
            self._instr.write("MMEM:STOR:TRAC 1,'test.DAT'")

            self._wait()  # prevent overlapping execution of commands
            trace_data = self._instr.query_binary_values(
                "MMEM:DATA? 'test.DAT'", datatype='B', container=bytearray
            )
            trace_data = trace_data.replace(b';', b',')
            trace_data = remove_first_line(trace_data)

            with open(csv_path, 'wb') as f:
                f.write(trace_data)
            print(f"Trace data saved.")
        except Exception as e:
            print(f"Failed to save trace data: {e}")

    def aquire_peak_point(self):
        self._instr.write("CALC:MARK1:MAX")
        x = float(self._instr.query(f"CALC:MARK1:X?"))  # freq. value
        y = float(self._instr.query(f"CALC:MARK1:Y?"))  # power value
        return x, y

# END OF CLASS DEFINITION
#---------------------------------------------------------------------------------

# END OF FILE
#---------------------------------------------------------------------------------