from ..main import proc_page_collection, incoming_collection
import sys
import asyncio
import time

async def build_inverted_link_index():
    last_id = None
    while True:
        # Fetch pages in batches using _id pagination to avoid cursor timeout
        query = {"_id": {"$gt": last_id}} if last_id else {}
        cursor = proc_page_collection.find(query).sort("_id").limit(1000)
        pages = await cursor.to_list(length=1000)
        
        if not pages:
            break

        # Process each page in the current batch
        for page in pages:
            print(f'Finding incoming links to {page["url"]}')
            
            # Get all incoming URLs in a SINGLE QUERY using distinct()
            incoming_urls = await proc_page_collection.distinct(
                "url", 
                {"outgoing": page["url"]}
            )
            incoming_set = set(incoming_urls)

            # Insert result into incoming collection
            await incoming_collection.insert_one({
                "incoming": list(incoming_set),
                "url": page["url"]
            })

        # Update pagination marker
        last_id = pages[-1]["_id"]

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(build_inverted_link_index())
    end_time = time.time()
    print(f"Inverted link index built in {(end_time - start_time) / 60:.2f} minutes")