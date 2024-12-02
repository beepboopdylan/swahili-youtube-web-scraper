import csv
from swahiliArabicWebScraper import YoutubeScrape
import time

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
        queries = 0
        for i in search_queries_list:
            queries += 1
            if minutes > max_minutes:
                break
            scraper = YoutubeScrape(i, output_file, max_minutes, processed_video_ids)
            minutes += scraper.process()

    print("Number of queries processed: ", queries)
    print("Total minutes processed: ", minutes)

if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()

    elapsed_time = end_time - start_time

    # Display runtime in seconds
    print(f"\nProgram completed in {elapsed_time:.2f} seconds.")