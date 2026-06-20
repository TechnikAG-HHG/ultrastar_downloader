import customtkinter as ctk
from ultrastar_downloader import run_ultrastar_downloader
from ultrastar_checker import run_checker
from ultrastar_add_YouTube_links import add_youtube_links
import tkinter as tk
from tkinter import filedialog as fd
import os
from threading import Thread, active_count as threading_active_count
from time import sleep
import sys
import queue
import re

# Initialize thread-safe queue for UI console log redirection
log_queue = queue.Queue()

class QueueRedirector:
    def __init__(self, q, prefix=""):
        self.q = q
        self.prefix = prefix
        self.original_stdout = sys.stdout

    def write(self, string):
        self.q.put(self.prefix + string)
        if self.original_stdout:
            self.original_stdout.write(string)

    def flush(self):
        if self.original_stdout:
            self.original_stdout.flush()

# Redirect stdout and stderr
sys.stdout = QueueRedirector(log_queue)
sys.stderr = QueueRedirector(log_queue, prefix="[ERROR] ")

# Helper functions for robust config management
def load_config():
    config = {
        "DEBUG": "False",
        "DEFAULT_THREADS": "10",
        "DEFAULT_DIRECTORY": ""
    }
    if os.path.exists("config.txt"):
        try:
            with open("config.txt", "r", encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "=" in line:
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2:
                            config[parts[0].strip()] = parts[1].strip()
        except Exception as e:
            print("Error reading config.txt:", e)
    else:
        save_config(config)
    return config

def save_config(config):
    try:
        with open("config.txt", "w", encoding='utf-8') as f:
            for key, val in config.items():
                f.write(f"{key}={val}\n")
    except Exception as e:
        print("Error writing config.txt:", e)

# Initialize variables from config
config = load_config()
FOLDER_PATH = config.get("DEFAULT_DIRECTORY", "")
if not FOLDER_PATH:
    FOLDER_PATH = "C:/Texte"

FOLDER_PATH2 = f"{FOLDER_PATH}/NoYoutubeLink"
name = config.get("DEFAULT_DIRECTORY", "")
start = 0
execute = 0

try:
    number_of_threads = int(config.get("DEFAULT_THREADS", "10"))
except ValueError:
    number_of_threads = 10

progress = 0
debug = 1 if config.get("DEBUG", "False") == "True" else 0

prefix_list1 = ['#VIDEO:', '#MP3:', "#COVER:"]
prefix_list2 = ['#VIDEO:']

# Functions

def busy(madeprogress):
    global progress
    if madeprogress is not None and progress < madeprogress:
        progress = madeprogress
    file_open_button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    for button in buttons:
        button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    root.update_idletasks()
    global start
    start = 1

def unbusy():
    file_open_button.configure(state="normal", fg_color="#89B4FA", text_color="#11111B")
    
    # Re-enable specific buttons based on debug status
    if debug:
        start_button_label.configure(state="normal", fg_color="#F9E2AF", text_color="#11111B")
        start_button_label2.configure(state="normal", fg_color="#A6E3A1", text_color="#11111B")
        start_button_label3.configure(state="normal", fg_color="#F38BA8", text_color="#11111B")
    start_button_label_all.configure(state="normal", fg_color="#FAB387", text_color="#11111B")
    
    root.update_idletasks()
    global start
    start = 0

def eisbxrerror(e):
    print("An error occurred:", e)
    title_label.configure(text="ERROR OCCURRED", text_color="#F38BA8")
    path_label.configure(text="Blame Eisbxr", text_color="#F38BA8")
    root.update_idletasks()

def refresh_search_results():
    count = 0
    search_results.configure(state="normal")
    search_results.delete('1.0', tk.END)  # Use '1.0' to indicate the start of the text
    if not FOLDER_PATH or not os.path.exists(FOLDER_PATH):
        search_results.insert(tk.END, "Folder does not exist or is not set.")
        search_results.configure(state="disabled")
        return
    try:
        for file_name in os.listdir(FOLDER_PATH):
            if file_name.endswith(".txt"):
                search_results.insert(tk.END, f"{count + 1}# {file_name}\n")
                count += 1
        if count == 0:
            search_results.insert(tk.END, "No UltraStar .txt files found in this folder.")
    except Exception as e:
        print("Error refreshing search results:", e)
    search_results.configure(state="disabled")

def changethreads():
    global number_of_threads
    val = thread_entry.get()
    if val.isdigit():
        number_of_threads = int(val)
        thread_entry_label2.configure(text="")
        if number_of_threads > 30:
            number_of_threads = 30
        elif number_of_threads < 2:
            number_of_threads = 2
        thread_entry.delete(0, tk.END)
        thread_entry.insert(tk.END, number_of_threads)
        
        # Save updated thread count to config
        cfg = load_config()
        cfg["DEFAULT_THREADS"] = str(number_of_threads)
        save_config(cfg)
        
        thread_entry_label2.configure(text=f"Updated: {number_of_threads}", fg_color="#F38BA8")
        root.update_idletasks()
        sleep(1.5)
        thread_entry_label2.configure(text="Change", fg_color="#45475A")

def callback():
    global FOLDER_PATH, FOLDER_PATH2, start, name, progress
    if start == 0:
        newname = fd.askdirectory()
        if newname:
            name = newname
            progress = 0
            busy(None)
            unbusy()
            path_label.configure(text=name)
            FOLDER_PATH = name
            FOLDER_PATH2 = f"{name}/NoYoutubeLink"
            
            # Save updated directory to config
            cfg = load_config()
            cfg["DEFAULT_DIRECTORY"] = name
            save_config(cfg)
            
            refresh_search_results()

def programm():
    refresh_search_results()
    global start, name, progress
    if start == 0 and name:
        busy(1)
        run_checker(FOLDER_PATH, number_of_threads)
        unbusy()
        start_button_label.configure(fg_color="#A6E3A1", text="FINISHED")
        root.update_idletasks()
        sleep(1.5)
        start_button_label.configure(fg_color="#F9E2AF", text="Run Checker")
        root.update_idletasks()
        start = 0

def programm1():
    refresh_search_results()
    global start, name, progress
    if start == 0 and name and progress >= 1:
        busy(2)
        try:
            add_youtube_links(FOLDER_PATH2, prefix_list2)
        except Exception as e:
            eisbxrerror(e)
            return
        unbusy()
        start_button_label2.configure(fg_color="#A6E3A1", text="FINISHED")
        root.update_idletasks()
        sleep(1.5)
        start_button_label2.configure(fg_color="#A6E3A1", text="Add Youtube Links")
        root.update_idletasks()
        start = 0

def programm2():
    refresh_search_results()
    global start, name, progress
    if start == 0 and name and progress >= 2:
        busy(3)
        try:
            run_ultrastar_downloader(FOLDER_PATH, prefix_list1, number_of_threads)
        except Exception as e:
            eisbxrerror(e)
            return
        while threading_active_count() > 1:
            sleep(0.5)
        unbusy()
        start_button_label3.configure(fg_color="#A6E3A1", text="FINISHED")
        root.update_idletasks()
        sleep(1.5)
        start_button_label3.configure(fg_color="#F38BA8", text="Download Videos and Images")
        root.update_idletasks()
        start = 0

def programmall():
    refresh_search_results()
    global start, name, progress
    if start == 0 and name:
        busy(3)
        start_button_label_all.configure(text="Running Checker")
        root.update_idletasks()
        run_checker(FOLDER_PATH, number_of_threads)
        
        start_button_label_all.configure(text="Adding Youtube Links")
        root.update_idletasks()
        try:
            add_youtube_links(FOLDER_PATH2, prefix_list2)
        except Exception as e:
            eisbxrerror(e)
            return
            
        start_button_label_all.configure(text="Downloading Videos")
        root.update_idletasks()
        try:
            run_ultrastar_downloader(FOLDER_PATH, prefix_list1, number_of_threads)
        except Exception as e:
            eisbxrerror(e)
            return
            
        while threading_active_count() > 2:
            sleep(0.5)
            
        start_button_label_all.configure(text="Finished", fg_color="#A6E3A1")
        root.update_idletasks()
        sleep(3)
        start_button_label_all.configure(text="Execute All Processes", fg_color="#FAB387")
        root.update_idletasks()
        unbusy()

# UI log polling function
def update_logs():
    try:
        while True:
            msg = log_queue.get_nowait()
            if not msg:
                continue
            
            # Remove ANSI colors/escapes for cleaner UI terminal logs
            clean_msg = re.sub(r'\x1b\[[0-9;]*[mK]', '', msg)
            
            console_textbox.configure(state="normal")
            
            # Check if this is an update-in-place (carriage return)
            if '\r' in clean_msg:
                # Splitting on carriage return to handle multiple updates
                parts = clean_msg.split('\r')
                for idx, part in enumerate(parts):
                    if idx > 0:
                        # Delete the last line of the textbox to update in-place
                        console_textbox.delete("end-2l", "end-1c")
                        console_textbox.insert("end", "\n")
                    console_textbox.insert("end", part)
            else:
                # Direct message insertion with color-coded tags
                if clean_msg.startswith("[ERROR] "):
                    err_content = clean_msg[len("[ERROR] "):]
                    console_textbox.insert("end", err_content, "error")
                elif clean_msg.startswith("WARNING:"):
                    console_textbox.insert("end", clean_msg, "warning")
                elif "ERROR:" in clean_msg:
                    console_textbox.insert("end", clean_msg, "error")
                else:
                    console_textbox.insert("end", clean_msg)
            
            console_textbox.see("end")
            console_textbox.configure(state="disabled")
    except queue.Empty:
        pass
    root.after(50, update_logs)

# Create tkinter window
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("Ultrastar Deluxe Song Downloader")

# Setup modern window frame (maximizing instead of borderless full-screen)
root.geometry("1300x850")
root.minsize(1024, 700)
root.after(0, lambda: root.state('zoomed') if os.name == 'nt' else root.attributes('-zoomed', True))

# Set columns and rows configuration for clean grid layout
root.columnconfigure(0, weight=0, minsize=350)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# --- LEFT SIDEBAR PANEL ---
sidebar_frame = ctk.CTkFrame(root, width=350, corner_radius=0, fg_color="#1E1E2E")
sidebar_frame.grid(row=0, column=0, sticky="nsew")
sidebar_frame.columnconfigure(0, weight=1)

# Row 0: App Title
title_label = ctk.CTkLabel(
    sidebar_frame, 
    text="UltraStar Deluxe\nSong Downloader", 
    font=ctk.CTkFont(family="Inter", size=26, weight="bold"), 
    text_color="#F5E0DC", 
    anchor="w", 
    justify="left"
)
title_label.grid(row=0, column=0, padx=25, pady=(35, 10), sticky="ew")

# Row 1: Subtitle
desc_label = ctk.CTkLabel(
    sidebar_frame, 
    text="Download video, audio, and cover art to your UltraStar TXT files automatically.", 
    font=ctk.CTkFont(family="Inter", size=13), 
    text_color="#A6ADC8", 
    wraplength=300, 
    anchor="w", 
    justify="left"
)
desc_label.grid(row=1, column=0, padx=25, pady=(0, 25), sticky="ew")

# Row 2: Directory Selection Frame
dir_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
dir_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
dir_frame.columnconfigure(0, weight=1)

file_open_button = ctk.CTkButton(
    dir_frame, 
    text="Select Songs Folder", 
    command=callback, 
    font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
    fg_color="#89B4FA",
    text_color="#11111B",
    hover_color="#B4BEFE",
    height=40
)
file_open_button.grid(row=0, column=0, sticky="ew", pady=(0, 8))

path_label = ctk.CTkLabel(
    dir_frame, 
    text=name if name else "No folder selected", 
    font=ctk.CTkFont(family="Inter", size=12), 
    text_color="#CDD6F4", 
    wraplength=300, 
    anchor="w"
)
path_label.grid(row=1, column=0, sticky="ew", padx=5)

# Row 3: Thread Controller Frame
thread_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
thread_frame.grid(row=3, column=0, padx=20, pady=15, sticky="ew")
thread_frame.columnconfigure(0, weight=1)
thread_frame.columnconfigure(1, weight=0)

thread_entry_label = ctk.CTkLabel(
    thread_frame, 
    text="Max Concurrent Threads", 
    font=ctk.CTkFont(family="Inter", size=13, weight="bold"), 
    text_color="#BAC2DE"
)
thread_entry_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

thread_entry = ctk.CTkEntry(
    thread_frame, 
    font=ctk.CTkFont(family="Inter", size=14), 
    fg_color="#313244", 
    text_color="#CDD6F4", 
    border_color="#45475A",
    width=180,
    height=35
)
thread_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
thread_entry.insert(tk.END, str(number_of_threads))

thread_entry_label2 = ctk.CTkButton(
    thread_frame, 
    text="Change", 
    command=changethreads, 
    font=ctk.CTkFont(family="Inter", size=13, weight="bold"), 
    fg_color="#45475A", 
    text_color="#CDD6F4", 
    hover_color="#585B70",
    width=80,
    height=35
)
thread_entry_label2.grid(row=1, column=1, sticky="e")

# Row 4: Spacer to push action buttons down
sidebar_frame.rowconfigure(4, weight=1)

# Row 5: Action Buttons Frame
actions_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
actions_frame.grid(row=5, column=0, padx=20, pady=(20, 30), sticky="ew")
actions_frame.columnconfigure(0, weight=1)

# Setup action buttons
start_button_label = ctk.CTkButton(
    actions_frame, 
    text="Run Checker", 
    command=lambda: Thread(target=programm).start(), 
    font=ctk.CTkFont(family="Inter", size=14, weight="bold"), 
    fg_color="#F9E2AF", 
    text_color="#11111B",
    hover_color="#FAE3B0",
    height=38
)

start_button_label2 = ctk.CTkButton(
    actions_frame, 
    text="Add Youtube Links", 
    command=lambda: Thread(target=programm1).start(), 
    font=ctk.CTkFont(family="Inter", size=14, weight="bold"), 
    fg_color="#A6E3A1", 
    text_color="#11111B",
    hover_color="#B5E8B0",
    height=38
)

start_button_label3 = ctk.CTkButton(
    actions_frame, 
    text="Download Videos & Images", 
    command=lambda: Thread(target=programm2).start(), 
    font=ctk.CTkFont(family="Inter", size=14, weight="bold"), 
    fg_color="#F38BA8", 
    text_color="#11111B",
    hover_color="#F5A3B8",
    height=38
)

start_button_label_all = ctk.CTkButton(
    actions_frame, 
    text="Execute All Processes", 
    command=lambda: Thread(target=programmall).start(), 
    font=ctk.CTkFont(family="Inter", size=15, weight="bold"), 
    fg_color="#FAB387", 
    text_color="#11111B",
    hover_color="#FBC29E",
    height=45
)

# Render buttons depending on debug state
if debug:
    start_button_label.grid(row=0, column=0, sticky="ew", pady=5)
    start_button_label2.grid(row=1, column=0, sticky="ew", pady=5)
    start_button_label3.grid(row=2, column=0, sticky="ew", pady=5)
    start_button_label_all.grid(row=3, column=0, sticky="ew", pady=(15, 5))
else:
    start_button_label_all.grid(row=0, column=0, sticky="ew", pady=5)

buttons = [start_button_label, start_button_label2, start_button_label3, start_button_label_all]

# --- RIGHT MAIN DASHBOARD PANEL ---
main_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="#11111B")
main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(0, weight=3)  # Files list gets 3/7 of space
main_frame.rowconfigure(1, weight=4)  # Logs list gets 4/7 of space

# Row 0: Files Panel
files_panel = ctk.CTkFrame(main_frame, fg_color="#1E1E2E", border_width=1, border_color="#313244")
files_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
files_panel.columnconfigure(0, weight=1)
files_panel.rowconfigure(1, weight=1)

files_header = ctk.CTkLabel(
    files_panel, 
    text="Found Song Text Files", 
    font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
    text_color="#CDD6F4",
    anchor="w"
)
files_header.grid(row=0, column=0, padx=15, pady=10, sticky="ew")

search_results = ctk.CTkTextbox(
    files_panel, 
    font=ctk.CTkFont(family="monospace", size=12), 
    fg_color="#11111B", 
    text_color="#A6E3A1",
    border_color="#313244",
    border_width=1
)
search_results.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

# Row 1: Live Logs Panel
logs_panel = ctk.CTkFrame(main_frame, fg_color="#1E1E2E", border_width=1, border_color="#313244")
logs_panel.grid(row=1, column=0, sticky="nsew")
logs_panel.columnconfigure(0, weight=1)
logs_panel.rowconfigure(1, weight=1)

logs_header = ctk.CTkLabel(
    logs_panel, 
    text="Live Terminal Output", 
    font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
    text_color="#CDD6F4",
    anchor="w"
)
logs_header.grid(row=0, column=0, padx=15, pady=10, sticky="ew")

console_textbox = ctk.CTkTextbox(
    logs_panel, 
    font=ctk.CTkFont(family="monospace", size=11), 
    fg_color="#11111B", 
    text_color="#CDD6F4",
    border_color="#313244",
    border_width=1
)
console_textbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
console_textbox.tag_config("error", foreground="#F38BA8")
console_textbox.tag_config("warning", foreground="#F9E2AF")

# Initialize and update display if default folder exists
if name and os.path.exists(name):
    refresh_search_results()

# Start log update poller
root.after(50, update_logs)

# Run the tkinter main loop
root.mainloop()
