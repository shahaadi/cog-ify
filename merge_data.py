import numpy as np
import math
from tqdm import tqdm
import blosc
import pickle

start = 0
end = 4283
interval = 25
file_cnt = math.ceil((end - start) / interval)

path_template = 'all_ps_dbs/all_ps_dbs_%d_to_%d.dat'

all_ps_dbs = [None for _ in range(file_cnt)]

for i in tqdm(range(file_cnt)):
    start_idx = i * interval + start
    end_idx = min((i + 1) * interval + start, end)
    with open(path_template % (start_idx, end_idx), 'rb') as f:
        all_ps_dbs[i] = pickle.loads(blosc.decompress(f.read()))

all_ps_dbs = np.concatenate(all_ps_dbs, axis=0)
print(all_ps_dbs.shape)

interval = 370
file_cnt = math.ceil((end - start) / interval)

path_template = 'all_ps_dbs/all_ps_dbs_%d_to_%d.dat'

for i in tqdm(range(file_cnt)):
    start_idx = i * interval + start
    end_idx = min((i + 1) * interval + start, end)
    with open(path_template % (start_idx, end_idx), 'wb') as f:
        f.write(blosc.compress(pickle.dumps(all_ps_dbs[start_idx:end_idx])))
