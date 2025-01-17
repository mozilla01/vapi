from ..main import page_collection, incoming_collection
from multiprocessing import Pool
import asyncio
import sys
from colorama import Fore, init
import time

init(autoreset=True)


def continue_run(page_ranks, duplicate_page_ranks):

    for url, rank in page_ranks.items():
        difference = abs(rank - duplicate_page_ranks[url])
        if difference > 0.000001:
            return True

    return False


async def rank_pages():
    """
    Rank pages using the PageRank algorithm
    """
    count = int(sys.argv[1])
    page_ranks = {}
    d = 0.85
    print(Fore.GREEN + f"Setting initial ranks as {1 / count}")
    print("-" * 50)
    duplicate_page_ranks = {}
    async for page in page_collection.find():
        print(f'Setting initial rank for page {page["_id"]}')
        page_ranks[page["url"]] = -1
        duplicate_page_ranks[page["url"]] = 1 / count

    iteration = 1
    print(Fore.GREEN + "Starting PageRank algorithm")
    while continue_run(page_ranks, duplicate_page_ranks):
        print(Fore.CYAN + f"Starting iteration {iteration}")
        page_ranks = duplicate_page_ranks.copy()
        cumulative_sink_rank = 0
        async for page in page_collection.find():
            if "outgoing" not in page or len(page["outgoing"]) == 0:
                cumulative_sink_rank += page_ranks[page["url"]] / (count - 1)

        async for page in incoming_collection.find():
            print("-" * 50)
            print(Fore.BLUE + f'Ranking page {page["_id"]}: {page["url"]}')
            rank = 0
            for incoming in page["incoming"]:
                print(f"Incoming link: {incoming}")
                if incoming != page["url"]:
                    outgoing_list = (await page_collection.find_one({"url": incoming}))[
                        "outgoing"
                    ]
                    rank += (
                        d
                        * page_ranks[incoming]
                        / (len(outgoing_list) - (1 if incoming in outgoing_list else 0))
                    )

            duplicate_page_ranks[page["url"]] = (
                (1 - d) / count + d * cumulative_sink_rank + rank
            )

        sum_ranks = sum(duplicate_page_ranks.values())
        print(Fore.GREEN + f"Sum of all ranks: {sum_ranks}")

        print(Fore.GREEN + "Normalizing ranks")
        for url, rank in duplicate_page_ranks.items():
            duplicate_page_ranks[url] = rank / sum_ranks

        iteration += 1
        print(f"Pausing for 5 seconds before starting iteration {iteration}")
        time.sleep(5)

    print("-" * 50)
    print(Fore.GREEN + f"Ranks have converged at iteration {iteration}")
    print("Writing ranks to the database")
    for url, rank in duplicate_page_ranks.items():
        print(f"Updating rank for page {url}")
        await page_collection.update_one({"url": url}, {"$set": {"rank": rank}})


if __name__ == "__main__":
    asyncio.run(rank_pages())
