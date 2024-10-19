# TODO: Conditional API responses
# TODO: Find better way to batch process and refactor

from fastapi import FastAPI, status, Body
from .models import PageModel, UpdatePageModel, PageCollectionModel, QueueCollectionModel
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://127.0.0.1:27017/viginition")
db = client.viginition
page_collection = db.get_collection("pages")
queue_collection = db.get_collection("queue")

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
    try:
        await page_collection.find_one_and_update(filter={'url': page.url}, update={'text': page.text, 'outgoing': page.outgoing, 'last_crawled': page.last_crawled})
    except:
        await page_collection.insert_one(
        page.model_dump(by_alias=True, exclude=["id"])
    )

    return 'Done'

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
    if len(list(queue)[0][1]) > 0:
        await queue_collection.insert_many(
            [url.model_dump(by_alias=True, exclude=["id"]) for url in list(queue)[0][1]]
        )
    return 'Done'

@app.delete(
    "/dequeue",
    response_description="Dequeue URL from queue",
    response_model=str,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def dequeue():
    """
    Add crawlable URLs into queue.
    A unique `id` will be created and provided in the response.
    """
    found = False
    url_string = None
    while not found:
        url = await queue_collection.find_one()
        url_string = url['url']
        await queue_collection.delete_one({'_id': url['_id']})
        if page_collection.find_one({'url':url_string}):
            found = True
    return url_string
