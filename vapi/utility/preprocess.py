from ..main import proc_page_collection
import asyncio
import html


async def replace_html_characters():
    """
    Replace HTML characters in all pages.
    """
    async for page in proc_page_collection.find(
        {
            "$or": [
                {"text": {"$exists": True}},
                {"title": {"$exists": True}},
                {"anchor_text": {"$exists": True}},
                {"description": {"$exists": True}},
                {"keywords": {"$exists": True}},
            ]
        }
    ):
        print(f'Updating page "{page["url"]}"')
        try:
            if "text" in page:
                await proc_page_collection.find_one_and_update(
                    {"_id": page["_id"]},
                    {
                        "$set": {
                            "text": [html.unescape(text) for text in page["text"]],
                        },
                    },
                )
            if "title" in page:
                await proc_page_collection.find_one_and_update(
                    {"_id": page["_id"]},
                    {
                        "$set": {
                            "title": html.unescape(page["title"]),
                        },
                    },
                )
            if "anchor_text" in page and page["anchor_text"]:
                await proc_page_collection.find_one_and_update(
                    {"_id": page["_id"]},
                    {
                        "$set": {
                            "anchor_text": html.unescape(page["anchor_text"]),
                        },
                    },
                )
            if "description" in page and page["description"]:
                await proc_page_collection.find_one_and_update(
                    {"_id": page["_id"]},
                    {
                        "$set": {
                            "description": html.unescape(page["description"]),
                        },
                    },
                )
            if "keywords" in page and page["keywords"]:
                await proc_page_collection.find_one_and_update(
                    {"_id": page["_id"]},
                    {
                        "$set": {
                            "keywords": html.unescape(page["keywords"]),
                        },
                    },
                )
        except Exception as e:
            print(f"Error updating page {page['url']}: {e}")


if __name__ == "__main__":
    asyncio.run(replace_html_characters(), debug=True)
