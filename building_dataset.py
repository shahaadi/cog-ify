import numpy as np
import pandas as pd
import requests, json
from yt_dlp import YoutubeDL
from tqdm import tqdm
import subprocess
import math
import os

# pulls song ids and titles
def save_pre_data(channel_id, path):
    SEP = ';'
    if not os.path.exists(path):
        basecommand = f'python -m yt_dlp --flat-playlist -j --print-to-file "{channel_id};%(id)s;%(title)s;;" "{path}" "https://www.youtube.com/channel/{channel_id}"'
        os.system(basecommand)

        song_data = pd.read_csv(path, sep=SEP, header=None)
        columns = ['channel_id', 'video_id', 'title', 'duration', 'view_count']
        song_data.columns = columns

        song_data[['t_step'] + [f'datapoint_{i}' for i in range(100)]] = np.nan
        song_data.to_csv(path, sep=SEP, index=False)

# pull song data and save to path
def save_song_data(path):
    SEP = ';'
    song_data = pd.read_csv(path, sep=SEP)

    for index in tqdm(range(len(song_data['video_id']) - 1, -1, -1)):
        videoID = song_data.at[index, 'video_id']
        if song_data.loc[[index]].isna().sum().sum() != 0:
            # get video activity from video
            url = f'https://yt.lemnoslife.com/videos?part=mostReplayed&id={videoID}'
            content = requests.get(url).text
            data = json.loads(content)
            print(videoID)
            if data['items'][0]['mostReplayed'] is None:
                song_data.drop(index=index, inplace=True)
            else:
                # get song_duration
                url = f'https://yt.lemnoslife.com/videos?part=contentDetails&id={videoID}'
                content = requests.get(url).text
                time_data = json.loads(content)
                duration = time_data['items'][0]['contentDetails']['duration']
                if duration > 600 or duration <= 60:
                    song_data.drop(index=index, inplace=True)
                else:
                    song_data.at[index, 't_step'] = data['items'][0]['mostReplayed']['heatMarkers'][0]['heatMarkerRenderer']['markerDurationMillis']
                    for i, heatMarker in enumerate(data['items'][0]['mostReplayed']['heatMarkers']):
                        song_data.at[index, f'datapoint_{i}'] = heatMarker['heatMarkerRenderer']['heatMarkerIntensityScoreNormalized']
                    if song_data.at[index, f'datapoint_{99}'] == 1:
                        song_data.drop(index=index, inplace=True)
                    else:
                        song_data.at[index, 'duration'] = duration

                        # get view_count of video
                        url = f'https://yt.lemnoslife.com/noKey/videos?part=statistics&id={videoID}'
                        content = requests.get(url).text
                        data = json.loads(content)
                        song_data.at[index, 'view_count'] = data['items'][0]['statistics']['viewCount']
        song_data.to_csv(path, sep=SEP, index=False)

# cleans data by removing non songs
def remove_non_songs(channel_id, path):
    SEP = ';'
    song_data = pd.read_csv(path, sep=SEP)

    keyphrases = []
    # Vlog No Copyright Music
    if channel_id == 'UCEickjZj99-JJIU8_IJ7J-Q':
        keyphrases.append('(Vlog No Copyright Music)')
    # Royalty Free Music [No Copyright Music] - all music
    if channel_id == 'UC_aEa8K-EOJ3D6gOs7HcyNg':
        keyphrases.append('Release')
        keyphrases.append('Official')
    # Audio Library
    if channel_id == 'UCht8qITGkBvXKsR1Byln-wA':
        keyphrases.append('Copyright')

    if len(keyphrases) != 0:
        for index in range(len(song_data['video_id']) - 1, -1, -1):
            if not any(keyphrase.lower() in song_data.at[index, 'title'].lower() for keyphrase in keyphrases):
                song_data.drop(index=index, inplace=True)

    song_data.to_csv(path, sep=SEP, index=False)

# all in one function
def save_data(channel_id, path):
    save_pre_data(channel_id, path)
    save_song_data(path)
    remove_non_songs(channel_id, path)

# merge all channel csvs
def save_and_concat(channel_ids=['UC4wUSUO1aZ_NyibCqIjpt0g',
                                 'UCEickjZj99-JJIU8_IJ7J-Q',
                                 'UC_aEa8K-EOJ3D6gOs7HcyNg',
                                 'UCht8qITGkBvXKsR1Byln-wA']):
    SEP = ';'
    dfs = []

    save_processes = []
    for channel_id in channel_ids:
        save_command = ["python", "-c", f"import building_dataset; building_dataset.save_data('{channel_id}', 'data/{channel_id}_output.csv')"]
        save_process = subprocess.Popen(save_command)
        save_processes.append(save_process)

    for save_process in save_processes:
        save_process.wait()

    for channel_id in channel_ids:
        dfs.append(pd.read_csv(f'data/{channel_id}_output.csv', sep=SEP))

    df = pd.concat(dfs)
    df.to_csv('data/output.csv', sep=SEP, index=False)