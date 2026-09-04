# ultrastar_downloader
A tool to download the song and image data to an UltraStar Deluxe text file.


# How to use
1. Download UltraStar Deluxe text files from: https://usdb.animux.de/ or https://usdb.eu/ .

2. Move them all into one folder.

3. Run ultrastar_main.py, select your songs folder, and click **Refresh Songs** to verify detected .txt files.

4. For text files without a youtube link it searches for the right video. If the video is too long because it is a music video it uses the second result. Check these files because it can be that in the text files you have to set #GAP: to 0 or the video is just not right.

5. Copy everything into your UltraStar Deluxe song folder.

# How it works:
1. The programm extracts the link and downloads the video from Youtube. This can be through the supplied link or through a YouTube search.

2. It tries to download a picture to the video as a Cover.
  
3. It renames the downloaded files and it adds the names of them in the text file.


Important: You can use the Downloader only once on the same txt file because we need to delete the line with the YT Link for UltraStar when we paste in the name of the mp4 file
