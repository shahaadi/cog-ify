import subprocess
import math
import os

start = 0
end = 4283
interval = 20
file_cnt = math.ceil((end - start) / interval)

path_template = 'all_ps_dbs/all_ps_dbs_%d_to_%d.dat'

for i in tqdm(range(file_cnt)):
    start_idx = i * interval + start
    end_idx = min((i + 1) * interval + start, end)
    if not os.path.isfile(path_template % (start_idx, end_idx)):
        print('Processing:', start_idx, 'to', end_idx)

        command_template = 'python3 spectrogram_production.py --csv-file outgood.csv --start-idx %d --end-idx %d'

        process = subprocess.Popen(command_template % (start_idx, end_idx), shell=True)
        process.wait()
