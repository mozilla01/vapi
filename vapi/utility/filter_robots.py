import asyncio
from ..main import queue_collection
import requests
import re


def get_root_url(url):
    """
    Get the root URL of a given URL
    """
    return url.split("/")[2]


def compile_rule(rule):
    # Escape special characters in the rule and prepend a domain matcher
    escaped_rule = re.escape(rule)
    return re.compile(r"https?://[^/]+" + escaped_rule)


async def filter_robots():

    while (
        await queue_collection.count_documents({"respects_robots": {"$exists": False}})
        > 0
    ):
        some_url = await queue_collection.find_one(
            {"respects_robots": {"$exists": False}}
        )
        print(f'Found URL: {some_url["url"]}')
        root_url = get_root_url(some_url["url"])
        print(f"Root URL: {root_url}")
        robots = requests.get(f"https://{root_url}/robots.txt").text.split("\n")
        line_number = 0
        for i, line in enumerate(robots):
            if line.startswith("User-agent: *"):
                line_number = i
                break
        print(f"User-agent block starts at line {line_number}")

        for line in robots[line_number + 1 :]:
            line = line.strip()
            print(f"Processing line: {line}")
            if line.startswith("User-agent:") or line.startswith("Sitemap:"):
                break
            if line == "" or line.startswith("#") or line == " ":
                continue

            rule = line.split(":")
            async for url in queue_collection.find(
                {"url": {"$regex": f"^{root_url}.*"}}
            ):
                print(f"Processing URL: {url['url']}")
                delete = False
                if rule[0].startswith("Disallow"):
                    disallowed = compile_rule(rule[1].strip())
                    match = re.match(disallowed, url["url"])
                    print(f"Found disallowed rule: {disallowed}")
                    if rule[1].strip() == "/" or match:
                        print(f"Matched {disallowed} with {url['url']}")
                        delete = True
                if rule[0].startswith("Allow"):
                    allowed = compile_rule(rule[1].strip())
                    match = re.match(allowed, url["url"])
                    print(f"Found allowed rule: {allowed}")
                    if match:
                        print(f"Matched {allowed} with {url['url']}")
                        delete = False

                if delete:
                    await queue_collection.update_many(
                        {"url": url["url"]}, {"$set": {"respects_robots": False}}
                    )
                else:
                    await queue_collection.update_many(
                        {"url": url["url"]}, {"$set": {"respects_robots": True}}
                    )

        await queue_collection.delete_many({"respects_robots": False})


if __name__ == "__main__":
    asyncio.run(filter_robots())
