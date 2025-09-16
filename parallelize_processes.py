import subprocess
import math
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--start-idx', type=int)
parser.add_argument('--end-idx', type=int)

args = parser.parse_args()

global_start = args.start_idx
global_end = args.end_idx
global_interval = 500

run_cnt = math.ceil((global_end - global_start) / global_interval)

for run in range(run_cnt):
    start = run * global_interval + global_start
    end = min((run + 1) * global_interval + global_start, global_end)

    print('Processing:', start, 'to', end)

    processes = []
    interval = 25
    command_len = math.ceil((end - start) / interval)

    command_template = 'python3 spectrogram_production.py --csv-file outgood.csv --start-idx %d --end-idx %d'

    for i in range(command_len):
        start_idx = i * interval + start
        end_idx = min((i + 1) * interval + start, end)
        processes.append(subprocess.Popen(command_template % (start_idx, end_idx), shell=True))

    for process in processes:
        process.wait()
