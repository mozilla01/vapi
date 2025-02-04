from ..main import queue_collection, page_collection
from ..models import QueueModel
import asyncio


async def add_starting_point():
    urls = [
        "https://www.merriam-webster.com/word-of-the-day",
        "https://www.dictionary.com/",
        "https://www.bbc.com/news",
        "https://www.hindustantimes.com/",
        "https://www.wikipedia.org/",
        "https://www.youtube.com/@kurzgesagt",
        "https://www.reddit.com/",
        "https://stackoverflow.com/",
        "https://news.ycombinator.com/",
        "https://www.github.com/",
        "https://www.twitter.com/",
        "https://developer.mozilla.org/",
    ]
    await queue_collection.delete_many({})
    await queue_collection.insert_many(
        [
            QueueModel(url=url, respects_robots=True).model_dump(
                exclude=["respects_robots", "anchor_text"]
            )
            for url in urls
        ]
    )
    await page_collection.delete_many({})


if __name__ == "__main__":
    asyncio.run(add_starting_point(), debug=True)
