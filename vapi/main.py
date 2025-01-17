# TODO: Conditional API responses
# TODO: Find better way to batch process and refactor

from fastapi import FastAPI, status, Body
from .models import (
    UpdatePageModel,
    PageCollectionModel,
    QueueCollectionModel,
)
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017/viginition")
db = client.viginition
page_collection = db.get_collection("pages")
queue_collection = db.get_collection("queue")
index_collection = db.get_collection("index")
incoming_collection = db.get_collection("incoming")


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
                    "outgoing": page.outgoing,
                    "last_crawled": page.last_crawled,
                }
            },
        )
        print("FOUND EXISTING PAGE")
    else:
        await page_collection.insert_one(page.model_dump(by_alias=True, exclude=["id"]))
        print("CREATED NEW PAGE")

    return "Done"


@app.get(
    "/pages/",
    response_description="List all pages",
    response_model=PageCollectionModel,
    response_model_by_alias=False,
)
async def list_pages():
    """
    List all of the student data in the database.
    The response is unpaginated and limited to 1000 results.
    """
    return PageCollectionModel(pages=await page_collection.find().to_list(1000))


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
    queueList = list(queue)[0][1]
    if len(queueList) > 0:
        for url in queueList:
            if url.respects_robots:
                await queue_collection.insert_one(
                    url.model_dump(
                        by_alias=True, exclude=["id", "anchor_text", "respects_robots"]
                    )
                )
            if not len(await page_collection.find({"url": url.url}).to_list()) > 0:
                await page_collection.insert_one(
                    url.model_dump(by_alias=True, exclude=["id", "respects_robots"])
                )
    return "Done"


@app.delete(
    "/dequeue",
    response_description="Dequeue URL from queue",
    response_model=str,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def dequeue():
    """
    Remove an unvisited URL from the queue.
    """
    found = False
    url_string = None
    while not found:
        url = await queue_collection.find_one()
        url_string = url["url"]
        await queue_collection.delete_one({"_id": url["_id"]})
        lst = await page_collection.find(
            {"url": url_string, "last_crawled": {"$exists": True}}
        ).to_list()
        if not len(lst) > 0:
            found = True
    return url_string
