import os
import re
import yt_dlp
from threading import Thread, Lock, Semaphore

def is_youtube_video_available(link):
    ydl_opts = {
        'extract_flat': True,
        'simulate': True,
        'cachedir': False,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(link, download=False)
        return True
    except Exception as e:
        print(f"Check failed for {link}: {e}")
        return False

def run_checker(FOLDER_PATH, number_of_threads=25):
    missing = []
    lock = Lock()
    threads = []
    semaphore = Semaphore(int(number_of_threads))

    def thread_target(FOLDER_PATH, filename, missing, lock):
        with semaphore:
            get_artist_from_file(FOLDER_PATH, filename, missing, lock)

    for filename in os.listdir(FOLDER_PATH):
        # Only check .txt files, don't check subdirectories like NoYoutubeLink
        if filename.endswith('.txt'):
            thread = Thread(target=thread_target, args=(FOLDER_PATH, filename, missing, lock))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    move_files(missing, FOLDER_PATH)


def get_artist_from_file(FOLDER_PATH, filename, missing, lock):
    link_picture = 1
    found_youtube = False
    if filename.endswith('.txt'):
        file_path = os.path.join(FOLDER_PATH, filename)

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()

        for line in lines:
            if line.startswith("#VIDEO") and not line.startswith("#VIDEOGAP:"):
                content = line[len("#VIDEO:"):].strip()
                co_index = content.find("co=")
                if (co_index != -1):
                    video_part = content[:co_index].strip()
                    co_part = content[co_index + 3:].strip()
                    comma_index = co_part.find(',')
                    if comma_index != -1:
                        link_picture = co_part[:comma_index].strip()
                    else:
                        link_picture = co_part

                    if not link_picture.startswith("https://"):
                        link_picture = "https://" + link_picture
                else:
                    video_part = content
                    link_picture = 1

                match_v = re.search(r'v=([^,\s\n]+)', content)
                match_a = re.search(r'a=([^,\s\n]+)', content)
                if match_v or match_a:
                    if match_v:
                        video_id = match_v.group(1).strip()
                    else:
                        video_id = match_a.group(1).strip()
                        
                    link = "https://www.youtube.com/watch?v=" + video_id
                    found_youtube = True
                    if is_youtube_video_available(link):
                        print(filename + ": found YouTube link: " + link)
                    else:
                        print("ERROR: " + filename + ": YouTube video no longer exists or is unavailable!")
                        with lock:
                            if filename not in missing:
                                missing.append(filename)
                else:
                    print("ERROR: " + filename + ": has no YouTube link!")
                    with lock:
                        if filename not in missing:
                            missing.append(filename)

                if link_picture == 1:
                    print("WARNING: " + filename + ": has no link to a picture!")
                else:
                    print(filename + ": found link to picture: " + link_picture)

        if not found_youtube:
            print("ERROR: " + filename + ": no YouTube link found in file!")
            with lock:
                if filename not in missing:
                    missing.append(filename)

    print(missing)
    return missing


def move_files(missing, FOLDER_PATH):
    file_path = os.path.join(FOLDER_PATH, "NoYoutubeLink")
    isExist = os.path.exists(file_path)
    if not isExist:
        os.makedirs(file_path)
        print("Created directory: " + file_path)
    
    for entry in missing:
        os.replace(os.path.join(FOLDER_PATH, entry), os.path.join(FOLDER_PATH, "NoYoutubeLink", entry))