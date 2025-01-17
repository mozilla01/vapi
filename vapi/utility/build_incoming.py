from ..main import page_collection, incoming_collection, queue_collection
import sys
import asyncio
import time


async def build_inverted_link_index():
    async for page in page_collection.find():
        print(f'Finding incoming links to {page["url"]}')
        incoming_set = set()
        async for incoming in page_collection.find({"outgoing": page["url"]}):
            print(f'{incoming["url"]} --> {page["url"]}')
            incoming_set.add(incoming["url"])

        await incoming_collection.insert_one(
            {"incoming": list(incoming_set), "url": page["url"]}
        )


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(build_inverted_link_index())
    end_time = time.time()
    print(f"Inverted link index built in {end_time - start_time} seconds")
