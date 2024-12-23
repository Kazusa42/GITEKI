import os
import json

import utils.functions as funcs
import utils.components as comps

"""comps.Const.WORKING_DIR = os.path.dirname(__file__)

import json

with open('config\GITEKI.json', 'r') as f:
    giteki_dict = json.load(f)['measurements']

rule = '49_27_3'
tmp = comps.TracePlot(comps.Const.WORKING_DIR)
tmp.plot(giteki_dict['mask'][rule])"""

funcs.menu()

rule = funcs.choose_condition("rule")
print(f"#--------------------------------------------------------------#")
print(f"#  All measurements will be conducted to align rule: {rule}.  #")
print(f"#--------------------------------------------------------------#\n")

while True:
    user_input = input('- Waiting for command: ').lower()
    if user_input == 'set rule':
        rule = funcs.choose_condition("rule")
        print(f"#--------------------------------------------------------------#")
        print(f"#  All measurements will be conducted to align rule: {rule}.  #")
        print(f"#--------------------------------------------------------------#\n")

import math

def measure_peak_power(sa: instru.SpectrumAnalyzer, giteki_dict: dict, rule, method):
    # search step
    # construct spectrum analyzer config
    sa_config = giteki_dict['search']['common']
    sa_config.update(giteki_dict['mask'][rule]['occ_freqband']['freq'])
    sa_config.update(giteki_dict['search']['diff']['peak']['general'])

    search_freq, search_peak = unit_measurement(sa, sa_config)  # perform measurement
    # save screen shot
    sa.save_screenshot('search.png')

    # update spectrum analyzer config to perform measure(zoom in) step
    del sa_config["start_freq"]
    del sa_config["stop_freq"]
    sa_config.update({'span': '100MHz', 'center_freq': search_freq})
    sa_config.update(giteki_dict['search']['diff']['peak'][method])

    measure_freq, measure_peak = unit_measurement(sa, sa_config)
    # save screen shot
    sa.save_screenshot('measure.png')

    # pass / fail determination
    rbw = giteki_dict['search']['diff']['peak'][method]['RBW']
    correction_factor = 20 * math.log10(float(50.0) / rbw)
    peak = measure_peak + correction_factor

    # load limit
    limit = float(giteki_dict['mask'][rule]['occ_freqband']['limit']['peak'].split('dBm')[0])
    allowable_dev = float(giteki_dict['mask'][rule]['occ_freqband']['limit']['allowable_dev'].split('%')[0]) / 100
    limit = 10 * math.log10((10 ** (limit / 10)) * (1 + allowable_dev))
    
    status = f"Passed" if peak <= limit else f"Failed"

    return {
        "peak@search (reading)": f"{round(search_peak, 2)}dBm",
        "freq@search": f"{round(search_freq / 1e9, 5)}GHz",
        "peak@measure (reading)": f"{round(measure_peak, 2)}dBm",
        "freq@measure": f"{round(measure_freq / 1e9, 5) }GHz",
        "correction factor": f"{round(correction_factor, 2)}",
        "peak (reading + correction factor)": [f"{round(peak, 2)}dBm", status],
    }