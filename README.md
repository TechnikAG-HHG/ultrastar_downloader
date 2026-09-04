# ultrastar_downloader

A tool to download the song and image data to an UltraStar Deluxe text file.

## Requirements

- Python 3.10 or newer with Tk support
- The packages listed in `requirements.txt`

Install the packages with:

```text
python -m pip install -r requirements.txt
```

The requirements include yt-dlp's JavaScript challenge solver and Deno runtime,
as well as a bundled FFmpeg executable. No separate FFmpeg or Deno installation
is required. On Linux, install the distribution's Tk package if it is not already
included (for example, `python3-tk`).

# How to use

1. Download UltraStar Deluxe text files from: https://usdb.animux.de/ or https://usdb.eu/ .

2. Select an input folder and place the UltraStar `.txt` files to process there. Select the ready-output and clean-TXT output folders separately in the application.

    The program creates two sibling folders automatically:
    - `Ultrastar Songs Output` contains the edited TXT files and downloaded video, audio, and cover files.
    - `Clean TXT Output` contains the original, unedited TXT files after successful processing.

3. Run `ultrastar_main.py`, select the input, ready-output, and clean-TXT output folders, and click **Refresh Songs** to verify detected `.txt` files.

4. For text files without a youtube link it searches for the right video. If the video is too long because it is a music video it uses the second result. Check these files because it can be that in the text files you have to set #GAP: to 0 or the video is just not right.

5. Copy everything into your UltraStar Deluxe song folder.

# How it works:

1. The programm extracts the link and downloads the video from Youtube. This can be through the supplied link or through a YouTube search.

2. It tries to download a picture to the video as a Cover.

3. It renames the downloaded files and it adds the names of them in the text file.

The input TXT is moved to `Clean TXT Output` only after the download and edited output TXT have completed successfully. Failed downloads remain in the input folder so they can be retried.
