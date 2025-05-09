# TODO: Conditional API responses
# TODO: Find better way to batch process and refactor

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    UpdatePageModel,
    PageCollectionModel,
    QueueCollectionModel,
)
import motor.motor_asyncio
from nltk.corpus import stopwords
import spacy
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGODB_URL = os.getenv("MONGODB_URL")
print(MONGODB_URL)
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.viginition
page_collection = db.get_collection("pages")
proc_page_collection = db.get_collection("pages_processed")
queue_collection = db.get_collection("queue")
index_collection = db.get_collection("index")
incoming_collection = db.get_collection("incoming")

stopwords = set(stopwords.words("english"))
nlp = spacy.load("en_core_web_sm")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post(
    "/pages/create-page",
    response_description="Add a single new Page",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_page(page: UpdatePageModel):
    """
    Insert a new page record.
    A unique `id` will be created and provided in the response.
    """
    find_page = await page_collection.find_one({"url": page.url})
    if find_page:
        await page_collection.find_one_and_update(
            {"url": page.url},
            {
                "$set": {
                    "text": page.text,
                    "title": page.title,
                    "description": page.description,
                    "keywords": page.keywords,
                    "outgoing": page.outgoing,
                    "last_crawled": page.last_crawled,
                }
            },
        )
    else:
        await page_collection.insert_one(page.model_dump(by_alias=True, exclude=["id"]))

    return "Done"


@app.post(
    "/enqueue",
    response_description="Enqueue URLs into queue",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def enqueue(queue: QueueCollectionModel):
    """
    Add crawlable URLs into queue.
    A unique `id` will be created and provided in the response.
    """
    urls = queue.model_dump(by_alias=True)["urls"]

    try:
        await page_collection.insert_many(urls, ordered=False)
    except Exception as e:
        print("Duplicate URLs not inserted into pages")

    cleaned_urls = []
    for entry in urls:
        result = await page_collection.find_one(
            {"url": entry["url"], "text": {"$exists": True}}
        )
        if result is None:
            print(f"Adding URL to queue: {entry['url']}")
            cleaned_urls.append({"url": entry["url"]})
        else:
            print(f"Duplicate URL found in pages: {entry['url']}")

    try:
        await queue_collection.insert_many(cleaned_urls, ordered=False)
    except Exception as e:
        print("Duplicate URLs not inserted into queue")

    return "Done"


@app.delete(
    "/dequeue",
    response_description="Dequeue URL from queue",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def dequeue():
    """
    Remove unvisited URLs from the queue.
    """
    urls = []
    while len(urls) < 3:
        # lock helps send different urls to different threads
        # can probably use MongoDB transactions
        url = await queue_collection.find_one_and_delete({})
        if url is None:
            break
        urls.append(url["url"])
    return urls


@app.get("/search")
async def search(query: str, level: int = 1, limit: int = 10):
    """
    Receive and respond to a user query.
    """

    link_frequency = {}
    for word in nlp(query):
        token = word.lemma_.lower().strip()
        if token in stopwords:
            continue
        entry = await index_collection.find_one({"word": token})
        if entry:
            for page in entry["pages"]:
                link_frequency[page["page_id"]] = (
                    {"positions": [], "big_score": 0, "score": 0}
                    if page["page_id"] not in link_frequency
                    else link_frequency[page["page_id"]]
                )
                link_frequency[page["page_id"]]["score"] += 1
                link_frequency[page["page_id"]]["big_score"] += (
                    page["anchor"] + page["title"]
                )
                link_frequency[page["page_id"]]["positions"].extend(page["positions"])

    links = list(link_frequency.items())
    pages = []
    for link in links:
        page = await proc_page_collection.find_one(
            {"_id": ObjectId(link[0])}, {"_id": 0}
        )
        page["score"] = link[1]["score"]
        page["big_score"] = link[1]["big_score"]
        page["relevant_text"] = []
        for position in link[1]["positions"]:
            (
                page["relevant_text"].append(page["text"][position[0] - 1])
                if position[0] > 0
                else 0
            )
            page["relevant_text"].append(page["text"][position[0]])
            (
                page["relevant_text"].append(page["text"][position[0] + 1])
                if position[0] < len(page["text"]) - 1
                else 0
            )
        page.pop("text", None)
        page.pop("outgoing", None)
        page.pop("last_crawled", None)
        pages.append(page)

    pages = sorted(
        pages, key=lambda x: (x["big_score"], x["score"], x["rank"]), reverse=True
    )

    return pages[(level - 1) * limit : level * limit]


@app.get("/get-news")
async def get_news():
    """
    Get the latest news from the BBC News URLs collection.
    """
    # Return urls starting with https://www.bbc.com/news/articles/...
    return await page_collection.find(
        {"url": {"$regex": "^https://www.bbc.com/news/articles/"}}
    ).to_list(10)
