from .main import queue_collection
from .models import QueueModel, QueueCollectionModel

urls = [
    'https://www.merriam-webster.com/word-of-the-day',
    'https://www.bbc.com/news',
    'https://www.wikipedia.org/',
    'https://www.youtube.com/@kurzgesagt',
    'https://openai.com/',
    'https://www.reddit.com/',
]
urls = QueueCollectionModel({QueueModel(url=url) for url in urls}
)
queue_collection.delete_many()
queue_collection.insert_many(urls)