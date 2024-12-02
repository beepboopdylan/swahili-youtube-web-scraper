import csv
from swahiliArabicWebScraper import YoutubeScrape

def main():
    search_queries = input("Enter search queries (separate by commas): ")
    search_queries_list = [query.strip().replace(" ", "+").lower() for query in search_queries.split(",")]

    output_file = 'output.csv'

    max_minutes = int(input("Enter maximum number of minutes to scrape: "))
    header = ['title', 'description', 'views', 'likes', 'location', 'language', 'duration', 'format', 'categories', 'tags', 'timestamp', 'upload date', 'playlist id', 'channel', 'channel id', 'transcript', 'url', 'keywords']

    with open(output_file, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        minutes = 0

        #handle duplicates
        processed_video_ids = set()
        for i in search_queries_list:
            if minutes > max_minutes:
                break
            scraper = YoutubeScrape(i, output_file, max_minutes, processed_video_ids)
            minutes += scraper.process()

main()