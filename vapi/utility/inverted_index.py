from ..models import IndexPageEntryModel
from ..main import proc_page_collection, index_collection
from nltk.corpus import stopwords
import string
import spacy
import asyncio


async def build_inverted_text_index():
    """
    Build an inverted text index from the MongoDB collection of pages
    """
    nlp = spacy.load("en_core_web_sm")
    stop_words = set(stopwords.words("english"))

    async for page in proc_page_collection.find(filter={"text": {"$exists": True}}):
        print("-" * 50)
        print(f'Indexing page {page["_id"]}: {page["url"]}')
        word_count = {}
        for i, text in enumerate(page["text"]):
            for j, token in enumerate(nlp(text)):
                word = token.lemma_.lower().strip()
                if word in stop_words or word in string.punctuation or not word:
                    continue
                if word in word_count:
                    word_count[word]["count"] += 1
                    word_count[word]["positions"].append((i, j))
                else:
                    word_count[word] = {}
                    word_count[word]["positions"] = [(i, j)]
                    word_count[word]["count"] = 1

        word_set = set()
        for text in page["text"]:
            for token in nlp(text):
                word = token.lemma_.lower().strip()
                if word in word_set:
                    continue
                else:
                    word_set.add(word)
                print(f'Indexing word "{word}"')
                if word in stop_words or word in string.punctuation or not word:
                    continue
                page_entry = IndexPageEntryModel(
                    page_id=page["_id"],
                    frequency=(
                        word_count[word]["count"]
                        + (
                            page["anchor_text"].count(word)
                            if page["anchor_text"]
                            else 0
                        )
                        + (page["title"].count(word) if "title" in page else 0)
                    ),
                    positions=word_count[word]["positions"],
                    anchor=(
                        word in page["anchor_text"].lower()
                        if page["anchor_text"]
                        else False
                    ),
                    title=word in page["title"].lower(),
                    description=(
                        word in page["description"].lower()
                        if "description" in page
                        else False
                    ),
                    keywords=(
                        word in page["keywords"].lower()
                        if "keywords" in page
                        else False
                    ),
                )
                await index_collection.find_one_and_update(
                    {"word": word},
                    {
                        "$push": {
                            "pages": page_entry.model_dump(
                                by_alias=True, exclude=["id"]
                            )
                        }
                    },
                    upsert=True,
                )
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(build_inverted_text_index())
