from .main import queue_collection, page_collection
from .models import QueueModel
import asyncio

async def add_starting_point():
    urls = [
        'https://www.merriam-webster.com/word-of-the-day',
        'https://www.bbc.com/news',
        'https://www.wikipedia.org/',
        'https://www.youtube.com/@kurzgesagt',
        'https://openai.com/',
        'https://www.reddit.com/',
    ]
    await queue_collection.delete_many({})
    await queue_collection.insert_many([QueueModel(url=url, respects_robots=True).model_dump(exclude=['respects_robots', 'anchor_text']) for url in urls])
    await page_collection.delete_many({})

if __name__ == '__main__':
    asyncio.run(add_starting_point(), debug=True)