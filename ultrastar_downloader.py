import threading
import os
import shutil
import time
import requests
import re
import unicodedata
import yt_dlp
import imageio_ffmpeg
from threading import Thread, active_count
from time import sleep
from PIL import Image
from io import BytesIO

def safe_move(src, dst, max_retries=10, delay=5):
    for attempt in range(max_retries):
        try:
            if os.path.exists(src):
                shutil.move(src, dst)
                print(f"Moved file from {src} to {dst} on attempt {attempt+1}")
                return True
            else:
                print(f"Source file not found: {src}")
                return False
        except PermissionError as e:
            print(f"PermissionError on attempt {attempt+1}: {e}")
            time.sleep(delay)
    print(f"Failed to move file from {src} to {dst} after {max_retries} attempts")
    return False

def download_youtube_video(link, FOLDER_PATH, file_path, link_picture, video_id, audio_link):
    print("Downloading video!")
    print(link)
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        # Step 1: Extract video info without downloading
        with yt_dlp.YoutubeDL({'cachedir': False}) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            
            # Use the TXT file's base name as the safe_title to prevent naming collisions
            txt_filename = os.path.basename(file_path)
            txt_base = os.path.splitext(txt_filename)[0]
            safe_title = replace_non_ascii(txt_base)
            
            extension = 'mp4'
            desired_filename = f"{safe_title}.{extension}"
            desired_file_path = os.path.join(FOLDER_PATH, desired_filename)

        # Step 4: Set ydl_opts with desired outtmpl
        ydl_opts = {
            'outtmpl': desired_file_path,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
            'merge_output_format': 'mp4',
            'cachedir': False,
            'ffmpeg_location': ffmpeg_path,
        }

        # Download the video with the desired filename
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
        print(f"Video downloaded and saved as: {desired_filename}")
    except Exception as e:
        print(f"Error downloading video: {e}")
        with lock:
            processed_videos.discard(video_id)
        return

    if not os.path.exists(desired_file_path):
        print(f"Downloaded file not found: {desired_file_path}")
        return

    if link_picture != 1:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(link_picture, headers=headers)
            if response.status_code == 200:
                image_filename = f"{safe_title}.jpg"
                with open(os.path.join(FOLDER_PATH, image_filename), 'wb') as file:
                    file.write(response.content)
                print("Image downloaded successfully as", image_filename)
            else:
                get_youtube_thumbnail(safe_title, info_dict, FOLDER_PATH)
        except Exception as e:
            get_youtube_thumbnail(safe_title, info_dict, FOLDER_PATH)
    else:
        get_youtube_thumbnail(safe_title, info_dict, FOLDER_PATH)
            
    if audio_link != 1:
        try:
            extension_audio = 'mp3'
            desired_filename = f"{safe_title}.{extension_audio}"
            desired_file_path = os.path.join(FOLDER_PATH, desired_filename)

            # Set ydl_opts to download best audio and convert to mp3 using FFmpeg
            ydl_opts = {
                'outtmpl': os.path.join(FOLDER_PATH, f"{safe_title}.%(ext)s"),
                'format': 'bestaudio/best',
                'cachedir': False,
                'ffmpeg_location': ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            # Download and extract the audio with the desired filename
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([audio_link])
            print(f"Audio downloaded and saved as: {desired_filename}")
        except Exception as e:
            print(f"Error downloading audio: {e}")
            with lock:
                processed_videos.discard(video_id)
            return
    else:
        extension_audio = extension

    rename_file_and_add_line(safe_title, file_path, FOLDER_PATH, extension, extension_audio)
    with lock:
        processed_videos.discard(video_id)
        print(f"Removed video {video_id} from processed_videos set")

def delete_lines_with_prefix(file_path, prefix_list):
    with open(file_path, 'r+', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()
        for line in lines:
            if not any(line.startswith(prefix) for prefix in prefix_list):
                file.write(line)

processed_videos = set()
lock = threading.Lock()

def get_title_artist_from_file(FOLDER_PATH, prefix_list):
    for filename in os.listdir(FOLDER_PATH):
        if filename.endswith('.txt'):
            file_path = os.path.join(FOLDER_PATH, filename)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            for line in lines:
                if line.startswith("#VIDEO") and not line.startswith("#VIDEOGAP:"):
                    print(f"Processing line: {line}")
                    x1 = line.find("co=")
                    if x1 != -1:
                        co_part = line[x1 + 3:].strip()
                        comma_index = co_part.find(',')
                        if comma_index != -1:
                            link_picture = co_part[:comma_index].strip()
                        else:
                            link_picture = co_part

                        if not link_picture.startswith("https://"):
                            link_picture = "https://" + link_picture
                    else:
                        link_picture = 1

                    # Extract video_id using regex to capture the text after "v=" until a comma, space or line end.
                    match_v = re.search(r'v=([^,\s\n]+)', line)
                    match_a = re.search(r'a=([^,\s\n]+)', line)
                    
                    if match_v:
                        video_id = match_v.group(1).strip()
                        link = "https://www.youtube.com/watch?v=" + video_id
                    elif match_a:
                        video_id = match_a.group(1).strip()
                        link = "https://www.youtube.com/watch?v=" + video_id
                    else:
                        print(f"No valid video ID found in line: {line}")
                        continue
                    
                    # if there is an "a=" part in the line, extract the audio_id
                    if match_a:
                        audio_id = match_a.group(1).strip()
                        audio_link = "https://www.youtube.com/watch?v=" + audio_id
                    else:
                        audio_link = 1

                    # Check if the video has already been processed
                    with lock:
                        if video_id in processed_videos:
                            print(f"Video {video_id} is already being processed.")
                            continue
                        else:
                            processed_videos.add(video_id)

                    delete_lines_with_prefix(file_path, prefix_list)

                    while active_count() > int(number_of_threads):
                        sleep(0.01)
                    x = Thread(target=download_youtube_video, args=(link, FOLDER_PATH, file_path, link_picture, video_id, audio_link), daemon=True)
                    print(f"Link Picture: {link_picture}")
                    x.start()

def rename_file_and_add_line(title, file_path, FOLDER_PATH, extension, extension_audio):
    print("Changing file")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as old_file:
        old_content = old_file.read()
    with open(file_path, 'w', encoding='utf-8') as new_file:
        new_file.write(
            "#VIDEO:" + title + f".{extension}" + '\n' +
            "#MP3:" + title + f".{extension_audio}" + '\n' +
            "#COVER:" + title + ".jpg" + '\n' +
            old_content
        )

def replace_non_ascii(text):
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-zA-Z0-9_\s]', '', text)
    text = text.replace(' ', '_')
    return text

def run_ultrastar_downloader(FOLDER_PATH, prefix_list, number_of_threads2):
    global number_of_threads
    number_of_threads = number_of_threads2
    get_title_artist_from_file(FOLDER_PATH, prefix_list)
    
def get_youtube_thumbnail(safe_title, info_dict, FOLDER_PATH):
    # Use yt thumbnail if no custom image is provided
    image_filename = f"{safe_title}.jpg"
    thumbnail_url = info_dict.get('thumbnail', '')
    if thumbnail_url:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(thumbnail_url, headers=headers)
            if response.status_code == 200:
                # Crop the thumbnail to a square
                image = Image.open(BytesIO(response.content))
                width, height = image.size
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                right = (width + size) // 2
                bottom = (height + size) // 2
                cropped_image = image.crop((left, top, right, bottom))
                cropped_image.save(os.path.join(FOLDER_PATH, image_filename))
                print("Thumbnail downloaded and cropped successfully as", image_filename)
            else:
                print("Failed to download the thumbnail")
        except Exception as e:
            print(f"Website not reachable: {e}")
    else:
        print("No thumbnail found")