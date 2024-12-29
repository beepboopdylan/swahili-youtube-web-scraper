from swahiliArabicWebScraperJSON import YoutubeScrape
import time

def main():
    search_queries = "queries.txt"
    with open(search_queries, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        search_queries_list = [query.strip().replace(" ", "+").lower() for query in content.split(",")]

    mongodb_uri = "mongodb+srv://dylantran:imJ4aiNAoTdZzwsO@transcripts.td8yz.mongodb.net/youtube_data?retryWrites=true&w=majority&appName=Transcripts"
    db_name = "youtube_data"
    metadata_database = "metadata"

    max_minutes = int(input("Enter maximum number of minutes to scrape: "))
    #header = ['title', 'description', 'views', 'likes', 'location', 'language', 'duration', 'format', 'categories', 'tags', 'timestamp', 'upload date', 'playlist id', 'channel', 'channel id', 'url', 'keywords']

       # writer = csv.writer(f)
       # writer.writerow(header)
    minutes = 0
    #handle duplicates
    processed_video_ids = set()
    queries = 0
    for i in search_queries_list:
        if minutes > max_minutes:
            break
        scraper = YoutubeScrape(i, mongodb_uri, db_name, metadata_database, max_minutes, processed_video_ids)
        minutes += scraper.process()
        print("Total minutes so far: ", minutes)
        queries += 1

    print("Number of queries processed: ", queries)
    print("Total minutes processed: ", minutes)

if __name__ == "__main__":
    start_time = time.time()

    main()

    end_time = time.time()

    elapsed_time = end_time - start_time

    # Display runtime in seconds
    print(f"\nProgram completed in {elapsed_time:.2f} seconds.")