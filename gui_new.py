import tkinter as tk
import pygame
from PIL import Image, ImageTk
from tkinter import filedialog
from scipy.io.wavfile import write
import numpy as np
from IPython.display import Audio
from pydub import AudioSegment
from pydub.playback import play
from urllib.parse import urlparse
import tkinter.ttk as ttk
import tensorflow as tf
import time
import mutagen
import tkinter.font
from mutagen.wave import WAVE

from ordering_songs import create_mix
from Spotify_Youtube_API import get_songs_artists, get_token, find_videoID
from spectrogram_download import video_ids_spectrograms

model = tf.keras.models.load_model('week4 - e-karma/models/test3.keras')

global PAUSED
PAUSED = False
global MIX
MIX = None
global F
F = None
global SPOTIFY
SPOTIFY = None
global song_length
global STOPPED
STOPPED = False

def prediction_to_index(pred, cutoff):
    good_dp_i = pred > cutoff
    peak_i = np.argmax(pred)

    prev_dp = ~good_dp_i[:peak_i][::-1]
    if prev_dp.any():
        start_idx = peak_i - np.argmax(prev_dp)
    else:
        start_idx = 0

    post_dp = ~good_dp_i[peak_i:]
    if post_dp.any():
        end_idx = peak_i + np.argmax(post_dp)
    else:
        end_idx = good_dp_i.shape[0]

    dif = end_idx - start_idx
    if dif < 9:
        if (start_idx + 9) > good_dp.shape[0]:
            start_idx = end_idx - 9
        else:
            end_idx = start_idx + 9

    return start_idx, end_idx

def song_time():
    global STOPPED
    if STOPPED:
        return
    global F
    global song_length
    global PAUSED
    current_time = pygame.mixer.music.get_pos() / 1000
    # slider_label.config(text=f'Slider: {int(slider.get())} and Song Pos: {int(current_time)}')
    converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))
    
    """
    with wave.open(F) as mywav:
        song_length = mywav.getnframes() / mywav.getframerate()
    """
    
    cal_length_file = WAVE(F)
    file_info = cal_length_file.info
    song_length = int(file_info.length)
    converted_song_length = time.strftime('%M:%S', time.gmtime(song_length))   
    
    current_time += 1
    if int(slider.get()) == int(song_length):
        time_bar.config(text=f'Time Elapsed: {converted_song_length} of {converted_song_length}')
    elif PAUSED:
        pass
    elif int(slider.get()) == int(current_time):
        slider_position = int(song_length)
        slider.config(to=slider_position, value=int(current_time))
    else:
        slider_position = int(song_length)
        slider.config(to=slider_position, value=int(slider.get()))
        converted_current_time = time.strftime('%M:%S', time.gmtime(slider.get()))
        time_bar.config(text=f'Time Elapsed: {converted_current_time} of {converted_song_length}')
        next_time = int(slider.get()) + 1
        slider.config(value=next_time)
    
    # time_bar.config(text=f'Time Elapsed: {converted_current_time} of {converted_song_length}')
    # slider.config(value=int(current_time))
    time_bar.after(1000, song_time)
    
    

def add_songs():
    spotify_playlist = text_box.get("1.0", "end-1c")
    # spotify_playlist = 'https://open.spotify.com/playlist/7IXaLrFAFxmUELfKUycf1H?si=5b9991759b0d479b'
    spotify_string = urlparse(spotify_playlist).path.split('/')[-1]
    print(spotify_string)
    l = get_songs_artists(get_token(), spotify_string)
    l = l[0:5]
    video_ids = find_videoID(l)
    audio, spectrograms = video_ids_spectrograms(video_ids)
    spectrograms = np.expand_dims(spectrograms, axis=-1)
    pred = model.predict(spectrograms)
    
    cutoff = 0.8
    
    audio_files = []
    for i in range(len(video_ids)):
        start_idx, end_idx = prediction_to_index(pred[i], cutoff)
        audio_files.append(audio[i, start_idx * 48000:end_idx * 48000])
    
    global MIX
    MIX = create_mix(audio_files) # pass in spotify playlist to code for determining artist and song names, then pass that to model, then pass to order, then get the mix

def add_songs_updated():
    global SPOTIFY
    spotify_playlist = text_box.get("1.0", "end-1c")
    # spotify_playlist = 'https://open.spotify.com/playlist/7IXaLrFAFxmUELfKUycf1H?si=5b9991759b0d479b'
    spotify_string = urlparse(spotify_playlist).path.split('/')[-1]
    l = get_songs_artists(get_token(), spotify_string)
    l = l[0:5]
    SPOTIFY = l
    print(l)
    display_songs_box.delete('1.0', 'end')
    for s in l:
        display = "Song: " + s[0] + ", Artist: " + s[1][0] 
        if len(s[1]) > 1:
            for x in range(1, len(s[1])):
                display += ", " + s[1][x]
        display += "\n"
        display_songs_box.insert('end', display)

def create_mashup():
    global SPOTIFY
    if SPOTIFY != None:
        video_ids = find_videoID(SPOTIFY)
        audio, spectrograms = video_ids_spectrograms(video_ids)
        spectrograms = np.expand_dims(spectrograms, axis=-1)
        pred = model.predict(spectrograms)
        
        cutoff = 0.5
        
        audio_files = []
        for i in range(len(video_ids)):
            start_idx, end_idx = prediction_to_index(pred[i], cutoff)
            audio_files.append(audio[i, start_idx * 48000:end_idx * 48000])
        
        global MIX
        MIX, order = create_mix(audio_files) # pass in spotify playlist to code for determining artist and song names, then pass that to model, then pass to order, then get the mix
        
        display_songs_box.delete('1.0', 'end')
        display_songs_box.insert('end', 'SONGS REMIXED:\n\n')
        for index in order:
            display = "Song: " + SPOTIFY[index][0] + ", Artist: " + SPOTIFY[index][1][0] 
            if len(SPOTIFY[index][1]) > 1:
                for x in range(1, len(SPOTIFY[index][1])):
                    display += ", " + SPOTIFY[index][1][x]
            display += "\n"
            display_songs_box.insert('end', display)
        

def play_song():
    # mp3_file = window.get('active')
    # mp3_file = mp3_file
    # pygame.mixer.music.load(mp3_file)
    global MIX
    global F
    global song_length
    global STOPPED
    STOPPED = False
    if F == None:
        write('playlist.wav', 48000, MIX)
        F = "playlist.wav"
    pygame.mixer.music.load(F)
    pygame.mixer.music.play(loops=0)
    
    song_time()
    # slider_position = int(song_length)
    # slider.config(to=slider_position, value=0)
    
def stop_song():
    time_bar.config(text='')
    slider.config(value=0)
    PAUSED = False
    pygame.mixer.music.stop()
    time_bar.config(text='')
    global STOPPED
    STOPPED = True
    
def pause_song(paused):
    global PAUSED
    PAUSED = paused
    if not PAUSED:
        pygame.mixer.music.pause()
        PAUSED = True
    else:
        pygame.mixer.music.unpause()
        PAUSED = False
        
def slide(x):
    # slider_label.config(text=f'{int(slider.get())} of {int(song_length)}')
    global F
    pygame.mixer.music.load(F)
    pygame.mixer.music.play(loops=0, start=int(slider.get()))
    

root = tk.Tk()
root.title("AI Music Mixer")
root.geometry("870x540")
bg = tk.PhotoImage(file='./week4 - e-karma/gui_pictures/bg_pic_2.png')
label1 = tk.Label(root, image=bg)
label1.place(x=0, y=0)

pygame.mixer.init()

font_tuple = tk.font.Font(family="Bungee", size=11, weight='bold')

text_box = tk.Text(root, height=2, width=100, font=font_tuple, bg='black', fg='white')
text_box.insert(tk.INSERT, "Paste Link Here: ")
text_box.pack(pady=(50, 0))
display_songs_box = tk.Text(root, height=10, width=100, font=font_tuple, bg='black', fg='white')
display_songs_box.pack(pady=10)
open_btn = tk.Button(root, text="QUERY SPOTIFY PLAYLIST", font=font_tuple, fg='white', command=add_songs_updated)
open_btn.config(bg='black')
open_btn.pack()
play_music_btn = tk.Button(root, text="CREATE THE MASHUP", font=font_tuple, fg='white', command=create_mashup)
play_music_btn.config(bg='black')
play_music_btn.pack(pady=(5, 30))

# create buttons
# back_btn_img = Image.open('./week4 - e-karma/gui_pictures/previous_song_button_2.png')
# back_btn_img = back_btn_img.resize((50, 50))
# back_btn_img = ImageTk.PhotoImage(back_btn_img)

# forward_btn_img = Image.open('./week4 - e-karma/gui_pictures/next_song_button_2.png')
# forward_btn_img = forward_btn_img.resize((70, 70))
# forward_btn_img = ImageTk.PhotoImage(forward_btn_img)

play_btn_img = Image.open('./week4 - e-karma/gui_pictures/play_play.png')
play_btn_img = play_btn_img.resize((50, 50))
play_btn_img = ImageTk.PhotoImage(play_btn_img)

pause_btn_img = Image.open('./week4 - e-karma/gui_pictures/pause_pause.png')
pause_btn_img = pause_btn_img.resize((50, 50))
pause_btn_img = ImageTk.PhotoImage(pause_btn_img)

stop_btn_img = Image.open('./week4 - e-karma/gui_pictures/restart_restart.png')
stop_btn_img = stop_btn_img.resize((50, 50))
stop_btn_img = ImageTk.PhotoImage(stop_btn_img)

# create button functionality
frame = tk.Frame(root)
frame.config(bg='black')
frame.pack()


# back_btn = tk.Button(frame, image=back_btn_img, borderwidth=0)
# forward_btn = tk.Button(frame, image=forward_btn_img, borderwidth=0)
play_btn = tk.Button(frame, image=play_btn_img, borderwidth=0, bg='black', command=play_song)
pause_btn = tk.Button(frame, image=pause_btn_img, borderwidth=0, bg='black', command=lambda: pause_song(PAUSED))
stop_btn = tk.Button(frame, image=stop_btn_img, borderwidth=0, bg='black', command=stop_song)

# back_btn.grid(row=0, column=0, padx=10, pady=20)
# forward_btn.grid(row=0, column=4, padx=0, pady=20)
play_btn.grid(row=0, column=1, padx=30)
pause_btn.grid(row=0, column=0, padx=30)
stop_btn.grid(row=0, column=2, padx=30)


# create time status bar
time_bar = tk.Label(root, text='', fg='white', font=font_tuple, bd=1, relief='groove', anchor='e')
time_bar.config(bg='black')
time_bar.pack(fill='x', side='bottom', ipady=2)

# create slider
slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', value=0, command=slide, length=650)
slider.pack(pady=(5, 0))

# slider_label = tk.Label(root, text="0")
# slider_label.pack(pady=10)


root.mainloop()