from ..main import page_collection
import asyncio
import html


async def replace_html_characters():
    """
    Replace HTML characters in all pages.
    """
    async for page in page_collection.find():
        print(f'Updating page "{page["url"]}"')
        if "text" in page:
            await page_collection.find_one_and_update(
                {"_id": page["_id"]},
                {
                    "$set": {
                        "text": [html.unescape(text) for text in page["text"]],
                    },
                },
            )
        if "title" in page:
            await page_collection.find_one_and_update(
                {"_id": page["_id"]},
                {
                    "$set": {
                        "title": html.unescape(page["title"]),
                    },
                },
            )
        if "anchor_text" in page and page["anchor_text"]:
            await page_collection.find_one_and_update(
                {"_id": page["_id"]},
                {
                    "$set": {
                        "anchor_text": html.unescape(page["anchor_text"]),
                    },
                },
            )


if __name__ == "__main__":
    asyncio.run(replace_html_characters(), debug=True)
