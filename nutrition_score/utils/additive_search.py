import json
import os
import time
import warnings

from elasticsearch import Elasticsearch, helpers


warnings.filterwarnings("ignore")


def setup_elasticsearch():
    """
    Setup the Elasticsearch client and load the additives data into the Elasticsearch index.
    """
    URL = "https://localhost:9200/"
    USERNAME = "elastic"
    PASSWORD = "4tWSNtb2S*akIdToGENy"

    try:
        # Initialize Elasticsearch client
        es = Elasticsearch(
            [URL],
            basic_auth=(USERNAME, PASSWORD),
            verify_certs=False,
        )

        # Define index name
        index_name = "additives"

        # es.indices.delete(index=index_name, ignore=[400, 404])

        # Check if the index exists
        if not es.indices.exists(index=index_name):
            # If the index does not exist, create it
            es.indices.create(index=index_name)

            # Get the current file's directory
            current_dir = os.path.dirname(__file__)

            # Construct the path to the parent directory
            parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

            # Construct the path to the additives.json file in the data subfolder
            file_path = os.path.join(parent_dir, "data", "additives.json")

            # Load additives data from JSON file
            with open(file_path, "r", encoding="utf-8") as file:
                additives = json.load(file)

            # Prepare data for bulk indexing
            actions = [{"_index": "additives", "_source": additive} for additive in additives]

            # Bulk index data
            helpers.bulk(es, actions)

            time.sleep(1)

        return es

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def search_additive(es, name) -> dict:
    """
    Search for an additive by name in the Elasticsearch index.

    Parameters
    ----------
    es : Elasticsearch
        The Elasticsearch client instance.
    name : str
        The name of the additive to search for.

    Returns
    -------
    additive: dict
        The additive object found in the Elasticsearch index.
    """
    query = {"query": {"match": {"name": {"query": name, "fuzziness": 0}}}, "size": 1}
    response = es.search(index="additives", body=query)

    for hit in response["hits"]["hits"]:
        return hit["_source"]

    return None


def search_additives(names) -> list:
    """
    Search for additives by name in the Elasticsearch index.

    Parameters
    ----------
    names : list
        A list of additive names to search for.

    Returns
    -------
    additives: list
        A list of additive objects found in the Elasticsearch index.
    """
    es = setup_elasticsearch()
    additives = []

    for name in names:
        additive = search_additive(es, name)
        if additive:
            additives.append(additive)

    return additives


if __name__ == "__main__":
    es = setup_elasticsearch()
    ingredients = [
        "enriched wheat flour",
        "water",
        "whole grain rye flour",
        "sunflower seeds",
        "flaxseeds",
        "vegetable oil canola or soybean",
        "millet",
        "sugars sugar",
        "dextrose",
        "yeast",
        "sea salt",
        "pumpkin seeds",
        "sprouted malted wheat flakes",
        "vinegar",
        "wheat bran",
        "quinoa",
        "chia seeds",
        "calcium propionate",
        "cultured rye flour",
        "malt extract",
        "malted barley flour",
        "guar gum",
        "wheat gluten",
        "lactic acid",
        "ingredients may vary",
        "may contain treenuts",
    ]
    if es:
        for ingredient in ingredients:
            additive = search_additive(es, ingredient)
            if additive:
                print(f"Ingredient: '{ingredient}' - Additive Found: {additive['name']}")
            else:
                print(f"No additive found for ingredient: '{ingredient}'")

    print(search_additives(ingredients))
