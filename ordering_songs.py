import librosa
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
from pydub import AudioSegment
from pydub.playback import play
from IPython.display import Audio
from os import path
import random
from maad import util

# produce a spectrogram from digital samples (NumPy-array) of a song/recording
def spectrogram(sample, sampling_rate):
    fig, ax = plt.subplots()
    S, freqs, times, im = ax.specgram(sample, NFFT=4096, Fs=sampling_rate, window=mlab.window_hanning, noverlap=4096 // 2, mode='magnitude', scale='dB')
    
    log_S = S.ravel()  # ravel flattens 2D spectrogram into a 1D array
    spectrogram_logs = np.log(np.clip(log_S, np.exp(0-20), None))
    
    return spectrogram_logs


# calculate the cosine similarity between 2 spectrograms
def cos_dist(spec1, spec2):
    print(spec1.shape)
    print(spec2.shape)
    dist = 1 - (spec1 @ spec2) / (np.linalg.norm(spec1) * np.linalg.norm(spec2))
    return dist


"""
# testing multiple audio samples
audio = ["Cartoon - On & On (feat. Daniel Levi) [NCS Release].mp3",
         "DEAF KEV - Invincible [NCS Release].mp3",
         "Different Heaven & EH!DE - My Heart [NCS Release].mp3",
         "Janji - Heroes Tonight (feat. Johnning) [NCS Release].mp3",
         "Warriyo - Mortals (feat. Laura Brehm) [NCS Release].mp3",
         ] # PUT FILEPATHS HERE (FILES MUST BE IN MP3 FORMAT)
audio_paths = []
for a in range(len(audio)):
    src = audio[a]
    dst = "song" + str(a) + ".wav"                                                         
    sound = AudioSegment.from_mp3(src)
    sound.export(dst, format="wav")
    audio_paths.append(dst)
"""

def create_mix(audio):
    audio_list = audio
    # list of 1D spectrograms for each song
    spec_list = []
    #start_time = [43, 6, 17, 88, 128]
    #end_time = [64,16, 42, 100, 155]
    #audio_list = []
    #for i in range(len(audio_paths))):
    for sample in audio_list:
        #recorded_audio, sampling_rate = librosa.load(audio_paths[i], sr=48000, mono=True)
        #recorded_audio = recorded_audio[start_time[i]*sampling_rate:end_time[i]*sampling_rate]

        #spec_list.append(spectrogram(recorded_audio, sampling_rate))
        spec_list.append(spectrogram(sample, 48000))
        #audio_list.append(recorded_audio)


    # dictionary containing cosine similarity for each pair of songs
    # key: song_id (index of song in audio_paths)
    # value: [(cosine_similarity, second_song_id), (cosine_similarity, second_song_id)]
    #distances = {i:[] for i in range(len(audio_paths))}
    distances = {i:[] for i in range(len(audio_list))}
    num = 48000
    for i in range(len(distances)):
        for j in range(i + 1, len(distances)):
            dist = cos_dist(spec_list[i][-num:], spec_list[j][:num])
            distances[i].append((dist, j))
            dist = cos_dist(spec_list[j][-num:], spec_list[i][:num])
            distances[j].append((dist, i))


    # create the order in which the songs should be played
    for x in distances:
        distances[x].sort(key=lambda y:y[0])
    index = random.randint(0, len(distances) - 1)
    order = [index] # list of numbers that represent the song index in audio_paths
    for _ in range(0, len(audio_list) - 1):
        i = 0
        while distances[index][i][1] in order:
            i += 1
        order.append(distances[index][i][1])
        index = order[-1]
    print(order)


    # fade in the first song and fade out the last song
    def fade_in(audio, sampling_rate=48000, duration=2.0):
        length = int(duration*sampling_rate)
        start = 0
        end = start + length

        fade_curve = np.linspace(0.0, 1.0, length)
        audio[start:end] = audio[start:end] * fade_curve

    def fade_out(audio, sampling_rate=48000, duration=2.0):
        length = int(duration*sampling_rate)
        end = audio.shape[0]
        start = end - length

        fade_curve = np.linspace(1.0, 0.0, length)
        audio[start:end] = audio[start:end] * fade_curve

    fade_out(audio_list[order[-1]])
    fade_in(audio_list[order[0]])
    
    
    # create the mix and play it
    mix = []
    for ind in order:
        mix.append(audio_list[ind])
    crossfaded_mix = util.crossfade_list(mix, 48000, fade_len=2)
    return (crossfaded_mix, order)
    #Audio(crossfaded_mix, rate=48000)
