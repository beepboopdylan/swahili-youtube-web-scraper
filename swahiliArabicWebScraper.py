"""
Workflow:

1. take query and open the chrome driver
2. scroll down all the way
3. get all videos on page
4. one by one, execute script to get all those metadata of the video, as well as get the transcript.
5. attach to csv file (should open outside of the loop)
6. repeat 4 until there are no more videos.
7. repeat for second query (might make a class out of this)

"""
import csv
import subprocess
import json
import time
from selenium import webdriver
from xml.etree.ElementTree import ParseError
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import urllib.parse


def get_video_metadata(url):
    command = ["yt-dlp", "--dump-json", url]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    metadata = json.loads(result.stdout)
    return metadata


def scroll_down(driver):
    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    scroll_pause_time = 2

    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.documentElement.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def video_id(value):
    #from https://stackoverflow.com/a/7936523
    query = urllib.parse.urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = urllib.parse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    return None


def get_youtube_links(soup):
    links = soup.findAll('a',id='video-title')
    return links


class YoutubeScrape:
    def __init__(self, search_query, output_file, max_minutes, processed_video_ids):
        self.search_query = search_query
        self.output_file = output_file
        self.max_minutes = max_minutes
        self.processed_video_ids = processed_video_ids

    def process(self):
        #query of the
        driver = webdriver.Chrome()
        url = "https://www.youtube.com/results?search_query=" + self.search_query + "&sp=EgIoAQ%253D%253D"
        driver.get(url)
        scroll_down(driver)
        content = driver.page_source
        driver.quit()

        soup = BeautifulSoup(content, 'lxml')
        links = get_youtube_links(soup) #every link in the video

        #for each link, we get metadata, but we need to get the script first

        with open(self.output_file, 'a', encoding='UTF8', newline='') as f:
            minutes = 0
            i = 0
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            while minutes < self.max_minutes and i < len(links):
                video_url = "https://www.youtube.com" + links[i]['href']
                theid = video_id(video_url)

                if not isinstance(theid, str) or not theid.strip():
                    i += 1
                    continue  # Skip if `theid` is not a valid string

                if not theid or theid in self.processed_video_ids:
                    i += 1
                    continue

                self.processed_video_ids.add(theid)

                try:
                    transcript = YouTubeTranscriptApi.get_transcript(theid, languages=['sw','ar'])
                except (NoTranscriptFound, ParseError, TranscriptsDisabled, Exception):
                    i += 1
                    continue

                transcript_str = json.dumps(transcript, ensure_ascii=False)

                metadata = get_video_metadata(video_url)

                append_data = [metadata.get("title"),
                               metadata.get("description"),
                               metadata.get("view_count"),
                               metadata.get("like_count"),
                               metadata.get("location"),
                               metadata.get("language"),
                               metadata.get("duration"),
                               metadata.get("format"),
                               metadata.get("categories"),
                               metadata.get("tags"),
                               metadata.get("timestamp"),
                               metadata.get("upload_date"),
                               metadata.get("playlist_id"),
                               metadata.get("channel"),
                               metadata.get("channel_id"),
                               transcript_str,
                               video_url,
                               self.search_query
                               ]
                writer.writerow(append_data)
                minutes += float(append_data[6]) / 60
                i += 1

        return minutes