import numpy as np
import pandas as pd
import librosa
import tempfile
import yt_dlp
import argparse
import os
import blosc
import pickle

def video_ids_spectrograms(video_ids, quiet: bool = True):
    with tempfile.TemporaryDirectory() as tempdir:
        ydl_opts = {
            'quiet': quiet,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav'
            }],
            'outtmpl': f'{tempdir}/%(id)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'http://www.youtube.com/watch?v={videoId}' for videoId in video_ids])

        SONG_LEN = 240
        SR = 48000
        SAMPLE_CNT = int(SR * SONG_LEN)
        VID_LEN = len(video_ids)
        N_FFT = 4096
        HOP_LEN = 4096
        HOP_CNT = SAMPLE_CNT // HOP_LEN + 1
        N_MELS = 256
        full_samples = np.empty((SAMPLE_CNT))
        all_ps_dbs = np.empty((VID_LEN, N_MELS, HOP_CNT))

        for i, video_id in enumerate(video_ids):
            print(i, video_id, sep='\t')
            samples, _ = librosa.load(f'{tempdir}/{video_id}.wav', sr=SR)
            os.remove(f'{tempdir}/{video_id}.wav')

            if samples.shape[0] > SAMPLE_CNT:
                full_samples[:] = samples[:SAMPLE_CNT]
            else:
                full_samples[:samples.shape[0]] = samples
                full_samples[samples.shape[0]:] = 0

            all_ps_dbs[i] = librosa.feature.melspectrogram(y=full_samples, sr=SR, hop_length=HOP_LEN, n_mels=N_MELS, n_fft=N_FFT)
            all_ps_dbs[i] = librosa.power_to_db(all_ps_dbs[i], ref=np.max)

            all_ps_dbs[i] = (all_ps_dbs[i] - all_ps_dbs[i].min()) / (all_ps_dbs[i].max() - all_ps_dbs[i].min())

        return all_ps_dbs

def csv_to_spectrogram_npy(path, start_idx, end_idx):
    song_data = pd.read_csv(path, sep=';')
    all_ps_dbs = video_ids_spectrograms(song_data['video_id'][start_idx:end_idx])

    pickled_data = pickle.dumps(all_ps_dbs)
    compressed_pickle = blosc.compress(pickled_data)

    with open(f'all_ps_dbs/all_ps_dbs_{start_idx}_to_{end_idx}.npy', 'wb') as f:
        f.write(compressed_pickle)

parser = argparse.ArgumentParser()

parser.add_argument('--csv-file', type=str)
parser.add_argument('--start-idx', type=int)
parser.add_argument('--end-idx', type=int)

args = parser.parse_args()

csv_to_spectrogram_npy(args.csv_file, args.start_idx, args.end_idx)
