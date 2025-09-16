import tkinter as tk
import pygame
from PIL import Image, ImageTk
from tkinter import filedialog
from scipy.io.wavfile import write
import numpy as np
from IPython.display import Audio
from pydub import AudioSegment
from pydub.playback import play
import time
import mutagen
from mutagen.wave import WAVE

global PAUSED
PAUSED = False
global SONG_LIST
SONG_LIST = []
global F
F = None

def song_time():
    current_time = pygame.mixer.music.get_pos() / 1000
    converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))
    time_bar.config(text=converted_current_time)
    time_bar.after(1000, song_time)
    cal_length_file = WAVE(F)
    file_info = cal_length_file.info
    song_length = int(file_info.length)

def add_songs():
    global SONG_LIST
    mp3_files_list = filedialog.askopenfilenames(initialdir='./', title="Choose a Song", filetypes=(('mp3 Files', '*.mp3'), ))
    for mp3_file in mp3_files_list:
        window.insert('end', mp3_file)
        SONG_LIST.append(mp3_file)
    print(SONG_LIST)

def play_song():
    """
    mp3_file = window.get('active')
    mp3_file = mp3_file
    pygame.mixer.music.load(mp3_file)
    """
    global F
    if F == None:
        F = "./week4 - e-karma/test songs/Cartoon - On & On (feat. Daniel Levi) [NCS Release].mp3"
    pygame.mixer.music.load(F)
    pygame.mixer.music.play(loops=0)
    song_time()
    
def stop_song():
    PAUSED = False
    pygame.mixer.music.stop()
    
def pause_song(paused):
    global PAUSED
    PAUSED = paused
    if not PAUSED:
        pygame.mixer.music.pause()
        PAUSED = True
    else:
        pygame.mixer.music.unpause()
        PAUSED = False
    

root = tk.Tk()
root.title("AI Music Mixer")
root.geometry("500x300")

pygame.mixer.init()
window = tk.Listbox(root, bg="purple", fg="white", width=60, selectbackground="grey", selectforeground="black")
window.pack(pady=20)

# create buttons
back_btn_img = Image.open('./week4 - e-karma/gui_pictures/previous_song_button_2.png')
back_btn_img = back_btn_img.resize((50, 50))
back_btn_img = ImageTk.PhotoImage(back_btn_img)

forward_btn_img = Image.open('./week4 - e-karma/gui_pictures/next_song_button_2.png')
forward_btn_img = forward_btn_img.resize((70, 70))
forward_btn_img = ImageTk.PhotoImage(forward_btn_img)

play_btn_img = Image.open('./week4 - e-karma/gui_pictures/play_button_2.png')
play_btn_img = play_btn_img.resize((50, 50))
play_btn_img = ImageTk.PhotoImage(play_btn_img)

pause_btn_img = Image.open('./week4 - e-karma/gui_pictures/pause_button.png')
pause_btn_img = pause_btn_img.resize((50, 50))
pause_btn_img = ImageTk.PhotoImage(pause_btn_img)

stop_btn_img = Image.open('./week4 - e-karma/gui_pictures/stop_button.png')
stop_btn_img = stop_btn_img.resize((50, 50))
stop_btn_img = ImageTk.PhotoImage(stop_btn_img)

# create button functionality
frame = tk.Frame(root)
frame.pack()


back_btn = tk.Button(frame, image=back_btn_img, borderwidth=0)
forward_btn = tk.Button(frame, image=forward_btn_img, borderwidth=0)
play_btn = tk.Button(frame, image=play_btn_img, borderwidth=0, command=play_song)
pause_btn = tk.Button(frame, image=pause_btn_img, borderwidth=0, command=lambda: pause_song(PAUSED))
stop_btn = tk.Button(frame, image=stop_btn_img, borderwidth=0, command=stop_song)

back_btn.grid(row=0, column=0, padx=10)
forward_btn.grid(row=0, column=4, padx=0)
play_btn.grid(row=0, column=2, padx=10)
pause_btn.grid(row=0, column=1, padx=10)
stop_btn.grid(row=0, column=3, padx=10)


# create the box for inputting songs
song_menu = tk.Menu(root)
root.config(menu=song_menu)
added_menu = tk.Menu(song_menu)
song_menu.add_cascade(label="Add Songs", menu=added_menu)
added_menu.add_command(label="Choose songs to add to the playlist", command=add_songs)

# create time status bar
time_bar = tk.Label(root, text='', bd=1, relief='groove', anchor='e')
time_bar.pack(fill='x', side='bottom', ipady=2)

root.mainloop()