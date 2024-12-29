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
import subprocess
import json
import time
import certifi
import pymongo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
    def __init__(self, search_query, mongodb_uri, db_name, metadata_database, max_minutes, processed_video_ids):
        self.search_query = search_query
        self.mongodb_uri = mongodb_uri
        self.max_minutes = max_minutes
        self.db_name = db_name
        self.processed_video_ids = processed_video_ids
        self.data = []
        self.transcripts = []

        #mongodb
        self.client = pymongo.MongoClient(mongodb_uri, tlsCAFile=certifi.where())
        self.db = self.client[db_name]
        self.metadata_database = self.db[metadata_database]

    def process(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")  # Disable GPU for better performance
        chrome_options.add_argument("--no-sandbox")  # Required for some environments
        chrome_options.add_argument("--disable-dev-shm-usage")  # Avoid shared memory issues

        driver = webdriver.Chrome(options=chrome_options)
        url = "https://www.youtube.com/results?search_query=" + self.search_query + "&sp=EgIoAQ%253D%253D"
        driver.get(url)
        scroll_down(driver)
        content = driver.page_source
        driver.quit()

        soup = BeautifulSoup(content, 'lxml')
        links = get_youtube_links(soup) #every link in the video

        #for each link, we get metadata, but we need to get the script first
        minutes = 0
        i = 0
        print("Total number of videos in this search query: " + str(len(links)))

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
                #self.transcripts.append({
                #    "video_id": theid,
                #    "transcript": transcript
                #})
            except (NoTranscriptFound, ParseError, TranscriptsDisabled, Exception):
                i += 1
                continue

            metadata = get_video_metadata(video_url)

            self.data.append({
                "title": metadata.get("title"),
                "description": metadata.get("description"),
                "views": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "location": metadata.get("location"),
                "language": metadata.get("language"),
                "duration": metadata.get("duration"),
                "format": metadata.get("format"),
                "categories": metadata.get("categories"),
                "tags": metadata.get("tags"),
                "timestamp": metadata.get("timestamp"),
                "upload_date": metadata.get("upload_date"),
                "playlist_id": metadata.get("playlist_id"),
                "channel": metadata.get("channel"),
                "channel_id": metadata.get("channel_id"),
                "transcript": transcript,
                "url": video_url,
                "search_query": self.search_query
            })

            minutes += metadata.get("duration", 0) / 60
            i += 1

        self.save_metadata()
        #self.save_transcript()
        return minutes

    def save_metadata(self):
        if self.data:
            self.metadata_database.insert_many(self.data, ordered=False)

    #def save_transcript(self):
    #    if self.transcripts:
    #        self.transcript_database.insert_many(self.transcripts, ordered=False)
