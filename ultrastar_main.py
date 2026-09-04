import customtkinter as ctk
from ultrastar_downloader import run_ultrastar_downloader
from ultrastar_checker import run_checker
from ultrastar_add_YouTube_links import add_youtube_links
import tkinter as tk
from tkinter import filedialog as fd, messagebox
import os
from threading import Thread, active_count as threading_active_count
from time import sleep
import sys
import queue
import re

APPLICATION_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APPLICATION_DIRECTORY, "config.txt")

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
        "DEFAULT_DIRECTORY": "",
        "INPUT_DIRECTORY": "",
        "READY_OUTPUT_DIRECTORY": "",
        "CLEAN_TXT_OUTPUT_DIRECTORY": "",
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding='utf-8', errors='ignore') as f:
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
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            for key, val in config.items():
                f.write(f"{key}={val}\n")
    except Exception as e:
        print("Error writing config.txt:", e)

# Initialize variables from config
config = load_config()
INPUT_FOLDER = config.get("INPUT_DIRECTORY", "") or config.get("DEFAULT_DIRECTORY", "")
if not INPUT_FOLDER:
    INPUT_FOLDER = os.path.expanduser("~/Texte")

def default_output_paths(input_folder):
    parent_folder = os.path.dirname(os.path.normpath(input_folder))
    return (
        os.path.join(parent_folder, "Ultrastar Songs Output"),
        os.path.join(parent_folder, "Clean TXT Output"),
    )

def folder_summary(input_folder, ready_output_folder, clean_txt_output_folder):
    return (
        f"Input: {input_folder}\n"
        f"Ready: {ready_output_folder}\n"
        f"Clean TXT: {clean_txt_output_folder}"
    )

DEFAULT_READY_OUTPUT, DEFAULT_CLEAN_TXT_OUTPUT = default_output_paths(INPUT_FOLDER)
READY_OUTPUT_FOLDER = config.get("READY_OUTPUT_DIRECTORY", "") or DEFAULT_READY_OUTPUT
CLEAN_TXT_OUTPUT_FOLDER = config.get("CLEAN_TXT_OUTPUT_DIRECTORY", "") or DEFAULT_CLEAN_TXT_OUTPUT
FOLDER_PATH = INPUT_FOLDER
FOLDER_PATH2 = os.path.join(INPUT_FOLDER, "NoYoutubeLink")
name = INPUT_FOLDER
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
    ready_output_button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    clean_txt_output_button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    refresh_folder_button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    thread_entry_label2.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    for button in buttons:
        button.configure(state="disabled", fg_color="#313244", text_color="#7F849C")
    root.update_idletasks()
    global start
    start = 1

def unbusy():
    file_open_button.configure(state="normal", fg_color="#89B4FA", text_color="#11111B")
    ready_output_button.configure(state="normal", fg_color="#89B4FA", text_color="#11111B")
    clean_txt_output_button.configure(state="normal", fg_color="#89B4FA", text_color="#11111B")
    refresh_folder_button.configure(state="normal", fg_color="#74C7EC", text_color="#11111B")
    thread_entry_label2.configure(state="normal", fg_color="#45475A", text_color="#CDD6F4")
    
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
        song_files = sorted(
            [file_name for file_name in os.listdir(FOLDER_PATH) if file_name.lower().endswith(".txt")],
            key=str.casefold
        )
        count = len(song_files)
        if count > 0:
            search_results.insert(tk.END, f"Found {count} song text file(s):\n\n")
            for idx, file_name in enumerate(song_files, start=1):
                search_results.insert(tk.END, f"{idx}# {file_name}\n")
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

def folders_are_valid(input_folder, ready_output_folder, clean_txt_output_folder):
    paths = [input_folder, ready_output_folder, clean_txt_output_folder]
    normalized_paths = [os.path.realpath(os.path.abspath(path)) for path in paths if path]
    return len(normalized_paths) == 3 and len(set(normalized_paths)) == 3

def save_folder_config():
    cfg = load_config()
    cfg["DEFAULT_DIRECTORY"] = FOLDER_PATH
    cfg["INPUT_DIRECTORY"] = FOLDER_PATH
    cfg["READY_OUTPUT_DIRECTORY"] = READY_OUTPUT_FOLDER
    cfg["CLEAN_TXT_OUTPUT_DIRECTORY"] = CLEAN_TXT_OUTPUT_FOLDER
    save_config(cfg)

def update_folder_display():
    path_label.configure(
        text=folder_summary(
            FOLDER_PATH,
            READY_OUTPUT_FOLDER,
            CLEAN_TXT_OUTPUT_FOLDER,
        )
    )

def select_folder(folder_type):
    global FOLDER_PATH, FOLDER_PATH2, READY_OUTPUT_FOLDER, CLEAN_TXT_OUTPUT_FOLDER, name, progress
    selected_folder = fd.askdirectory()
    if not selected_folder:
        return

    new_input_folder = selected_folder if folder_type == "input" else FOLDER_PATH
    new_ready_output_folder = selected_folder if folder_type == "ready" else READY_OUTPUT_FOLDER
    new_clean_txt_output_folder = selected_folder if folder_type == "clean" else CLEAN_TXT_OUTPUT_FOLDER

    if not folders_are_valid(
        new_input_folder,
        new_ready_output_folder,
        new_clean_txt_output_folder,
    ):
        messagebox.showerror(
            "Invalid folder selection",
            "Input, ready-output, and clean-TXT folders must be different.",
        )
        return

    FOLDER_PATH = new_input_folder
    FOLDER_PATH2 = os.path.join(FOLDER_PATH, "NoYoutubeLink")
    READY_OUTPUT_FOLDER = new_ready_output_folder
    CLEAN_TXT_OUTPUT_FOLDER = new_clean_txt_output_folder
    name = FOLDER_PATH
    progress = 0
    save_folder_config()
    update_folder_display()
    refresh_search_results()

def callback():
    global FOLDER_PATH, FOLDER_PATH2, READY_OUTPUT_FOLDER, CLEAN_TXT_OUTPUT_FOLDER, start, name, progress
    if start == 0:
        select_folder("input")

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
        refresh_search_results()

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
        refresh_search_results()

def programm2():
    refresh_search_results()
    global start, name, progress
    if start == 0 and name and progress >= 2:
        busy(3)
        try:
            run_ultrastar_downloader(
                FOLDER_PATH,
                READY_OUTPUT_FOLDER,
                CLEAN_TXT_OUTPUT_FOLDER,
                prefix_list1,
                number_of_threads,
            )
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
        refresh_search_results()

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
            run_ultrastar_downloader(
                FOLDER_PATH,
                READY_OUTPUT_FOLDER,
                CLEAN_TXT_OUTPUT_FOLDER,
                prefix_list1,
                number_of_threads,
            )
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
        refresh_search_results()

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
def maximize_window():
    try:
        if sys.platform.startswith("win"):
            root.state("zoomed")
        elif sys.platform == "darwin":
            root.attributes("-fullscreen", True)
            root.after(100, lambda: root.attributes("-fullscreen", False))
        else:
            root.attributes("-zoomed", True)
    except Exception:
        pass

root.after(0, maximize_window)

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
    text="Select Input Folder",
    command=callback, 
    font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
    fg_color="#89B4FA",
    text_color="#11111B",
    hover_color="#B4BEFE",
    height=40
)
file_open_button.grid(row=0, column=0, sticky="ew", pady=(0, 8))

ready_output_button = ctk.CTkButton(
    dir_frame,
    text="Select Ready Output Folder",
    command=lambda: select_folder("ready"),
    font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
    fg_color="#89B4FA",
    text_color="#11111B",
    hover_color="#B4BEFE",
    height=34
)
ready_output_button.grid(row=1, column=0, sticky="ew", pady=(0, 6))

clean_txt_output_button = ctk.CTkButton(
    dir_frame,
    text="Select Clean TXT Output Folder",
    command=lambda: select_folder("clean"),
    font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
    fg_color="#89B4FA",
    text_color="#11111B",
    hover_color="#B4BEFE",
    height=34
)
clean_txt_output_button.grid(row=2, column=0, sticky="ew", pady=(0, 6))

refresh_folder_button = ctk.CTkButton(
    dir_frame,
    text="Refresh Songs",
    command=refresh_search_results,
    font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
    fg_color="#74C7EC",
    text_color="#11111B",
    hover_color="#89DCEB",
    height=34
)
refresh_folder_button.grid(row=3, column=0, sticky="ew", pady=(0, 8))

path_label = ctk.CTkLabel(
    dir_frame, 
    text=folder_summary(FOLDER_PATH, READY_OUTPUT_FOLDER, CLEAN_TXT_OUTPUT_FOLDER)
    if name else "No folder selected",
    font=ctk.CTkFont(family="Inter", size=12), 
    text_color="#CDD6F4", 
    wraplength=300, 
    anchor="w"
)
path_label.grid(row=4, column=0, sticky="ew", padx=5)

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
