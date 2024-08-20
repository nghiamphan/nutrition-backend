import json
import requests
import os
import sys

# Add the parent directory to the path to import the utils module so that we can run this script from the command line (https://stackoverflow.com/questions/16981921/relative-imports-in-python-3)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils import constants as c
from utils import nutri_score as ns
from utils import process_image


def fetch_and_calculate(barcode: str, profiles: dict) -> dict:
    """
    Fetch a product using the Open Food Facts API and calculate its nutrition score.

    Parameters
    ----------
    barcode : str
        The barcode string (UPC, EAN) of the product.
    profiles : dict
        The profile factors to calculate the nutri-score.
        For example:
        {
            "energy_profile_factor": 1,
            "saturation_profile_factor": 1,
            "sugars_profile_factor": 1,
            "sodium_profile_factor": 1,
            "max_additives_penalty": 50,
            "non_organic_penalty": 10
        }

    Returns
    -------
    product information : dict
        The information of the product including its name, image, ingredients, nutri-score, additives, additives risk, organic, and final score, food type, and nutritional values.
        For example:
        {
            "name": "Product Name",
            "image": "Image URL",
            "ingredients": "Ingredients",
            "nutriscore_scaled_100": 50,
            "additives": ["E100", "E200"],
            "additives_risk": 10,
            "organic": False,
            "final_score": 30,
            "food_type": "General food",
            "energy": 100,
            "energy_from_saturates": 0,
            "saturated_fat": 20,
            "saturates_over_total_fat": 0,
            "sugars": 10,
            "sodium": 10,
            "nn_sweeteners": 0,
            "protein": 10,
            "fiber": 10,
            "fruit_percentage": 0
        }
    """
    URL = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    response = requests.get(URL)
    if response.status_code == 200:
        product = response.json().get("product", {})
        if not product:
            print(f"Product not found: {barcode}")
            return None

        product_name = product.get("product_name", "")
        brand = product.get("brands", "")
        image = product.get("image_url", "")
        ingredients = product.get("ingredients_text", "")

        # Get the nutritional values of the product to calculate nutri-score
        nutriscore_2023_data = product.get("nutriscore", {}).get("2023", {}).get("data", {})

        # Get the negative components of the product
        energy = 0
        energy_from_saturated_fat = 0
        saturated_fat = 0
        saturated_over_total_fat = 0
        sugars = 0
        sodium = 0
        nn_sweeteners = 0

        if nutriscore_2023_data.get("components", {}).get("negative", {}):
            negative = nutriscore_2023_data.get("components", {}).get("negative", {})
            for item in negative:
                if item.get("id") == "energy":
                    energy = item.get("value") or 0  # If the value is None, set it to 0
                elif item.get("id") == "energy_from_saturated_fat":
                    energy_from_saturated_fat = item.get("value") or 0
                elif item.get("id") == "saturated_fat":
                    saturated_fat = item.get("value") or 0
                elif item.get("id") == "saturated_fat_ratio":
                    saturated_over_total_fat = item.get("value") or 0
                elif item.get("id") == "sugars":
                    sugars = item.get("value") or 0
                elif item.get("id") == "non_nutritive_sweeteners":
                    nn_sweeteners = 4
                elif item.get("id") == "salt":
                    sodium = item.get("value") or 0
        else:
            if nutriscore_2023_data.get("energy"):
                energy = nutriscore_2023_data.get("energy") or 0
            if nutriscore_2023_data.get("energy_from_saturated_fat"):
                energy_from_saturated_fat = nutriscore_2023_data.get("energy_from_saturated_fat") or 0
            if nutriscore_2023_data.get("saturated_fat"):
                saturated_fat = nutriscore_2023_data.get("saturated_fat") or 0
            if nutriscore_2023_data.get("saturated_fat_ratio"):
                saturated_over_total_fat = nutriscore_2023_data.get("saturated_fat_ratio") or 0
            if nutriscore_2023_data.get("sugars"):
                sugars = nutriscore_2023_data.get("sugars") or 0
            if nutriscore_2023_data.get("non_nutritive_sweeteners"):
                nn_sweeteners = 4
            if nutriscore_2023_data.get("salt"):
                sodium = nutriscore_2023_data.get("salt") or 0

        # Get the positive components of the product
        protein = 0
        fiber = 0
        fruit_percentage = 0

        if nutriscore_2023_data.get("components", {}).get("positive", {}):
            positive = nutriscore_2023_data.get("components", {}).get("positive", {})
            for item in positive:
                if item.get("id") == "proteins":
                    protein = item.get("value") or 0
                elif item.get("id") == "fiber":
                    fiber = item.get("value") or 0
                elif item.get("id") == "fruits_vegetables_legumes":
                    fruit_percentage = item.get("value") or 0
        else:
            if nutriscore_2023_data.get("proteins"):
                protein = nutriscore_2023_data.get("proteins") or 0
            if nutriscore_2023_data.get("fiber"):
                fiber = nutriscore_2023_data.get("fiber") or 0
            if nutriscore_2023_data.get("fruits_vegetables_legumes"):
                fruit_percentage = nutriscore_2023_data.get("fruits_vegetables_legumes") or 0

        # Put all the nutritional values in a dictionary
        nutritions = {
            ns.ENERGY: energy,
            ns.ENERGY_FROM_SATURATES: energy_from_saturated_fat,
            ns.SATURATED_FAT: saturated_fat,
            ns.SATURATES_OVER_TOTAL_FAT: saturated_over_total_fat,
            ns.SUGARS: sugars,
            ns.NN_SWEETENERS: nn_sweeteners,
            ns.SODIUM: sodium,
            ns.PROTEIN: protein,
            ns.FIBER: fiber,
            ns.FRUIT_PERCENTAGE: fruit_percentage,
        }

        # Determine the type of food
        if nutriscore_2023_data.get("is_red_meat_product"):
            food_type = ns.RED_MEAT
        elif nutriscore_2023_data.get("is_cheese"):
            food_type = ns.CHEESE
        elif nutriscore_2023_data.get("is_fat_oil_nuts_seeds"):
            food_type = ns.FATS_NUTS_SEEDS
        elif nutriscore_2023_data.get("is_beverage"):
            food_type = ns.BEVERAGES
        elif nutriscore_2023_data.get("is_water"):
            food_type = ns.WATER
        else:
            food_type = ns.GENERAL_FODD

        nutriscore_scaled_100 = calculate_nutriscore_scale_100(nutritions, food_type, profiles)

        # Get the additives and calculate the risk
        additives = product.get("additives_tags", [])
        additives = [additive.replace("en:", "") for additive in additives]

        max_additive_penalty = profiles.get(c.MAX_ADDITIVES_PENALTY) or c.MAX_ADDITIVES_PENALTY_DEFAULT_VALUE

        additives_risk, additives_list = calculate_additive_risk(additives)

        additives_risk = min(additives_risk, max_additive_penalty)

        # Check if the product is organic
        labels = product.get("labels_tags", [])
        organic = "en:organic" in labels

        if not organic:
            non_organic_penalty = profiles.get(c.NON_ORGANIC_PENALTY, c.NON_ORGANIC_PENALTY_DEFAULT_VALUE)
        else:
            non_organic_penalty = 0

        final_score = max(nutriscore_scaled_100 - additives_risk - non_organic_penalty, 0)

        return {
            "name": product_name,
            "brand": brand,
            "image": image,
            "ingredients": ingredients,
            "nutriscore_scaled_100": nutriscore_scaled_100,
            "additives": additives_list,
            "additives_risk": additives_risk,
            "organic": organic,
            "final_score": final_score,
            "food_type": food_type,
            **nutritions,
        }
    else:
        print(f"Error fetching product: {response.status}")
        return None


def process_image_and_calculate(image_path: str, food_type: str, profiles: dict) -> dict:
    """
    Calculate the nutrition score of a product from an image of a nutrition label.

    Parameters
    ----------
    image_path : str
        The path to the image file.
    food_type : str
        The type of food product.
    profiles : dict
        The profile factors to calculate the nutri-score.

    Returns
    -------
    product information : dict
        The product information including its name, image, ingredients, nutri-score, additives, additives risk, organic, and final score, food type, and nutritional values.
    """
    text = process_image.extract_text_from_image(image_path)
    nutritions = process_image.extract_all_nutrient_info(text)

    nutriscore_scaled_100 = calculate_nutriscore_scale_100(nutritions, food_type, profiles)

    food_object = {
        "name": "",
        "brand": "",
        "image": "",
        "ingredients": "",
        "nutriscore_scaled_100": nutriscore_scaled_100,
        "additives": [],
        "additives_risk": 0,
        "organic": False,
        "final_score": nutriscore_scaled_100,
        "food_type": food_type,
        **nutritions,
    }

    return food_object


def calculate_nutriscore_scale_100(nutritional_values: dict, food_type: str, profiles: dict) -> int:
    """
    Calculate the nutri-score of a product on a scale of 0-100.

    Parameters
    ----------
    nutritional_values : dict
        The nutritional values of the product including energy, saturated fat, sugars, sodium, protein, fiber, and fruit percentage.
    food_type : str
        The type of food product.
    profiles : dict
        The profile factors to calculate the nutri-score.

    Returns
    -------
    int
        The nutri-score value (-15 to 40).
    """
    calculator = ns.NutriScoreCalculator()

    # Setup the profile factors to calculate the nutri-score
    calculator.setup_profiles(
        {
            ns.ENERGY: profiles.get(c.ENERGY_PROFILE_FACTOR, c.ENERGY_PROFILE_FACTOR_DEFAULT_VALUE),
            ns.SATURATED_FAT: profiles.get(c.SATURATION_PROFILE_FACTOR, c.SATURATION_PROFILE_FACTOR_DEFAULT_VALUE),
            ns.SUGARS: profiles.get(c.SUGARS_PROFILE_FACTOR, c.SUGARS_PROFILE_FACTOR_DEFAULT_VALUE),
            ns.SODIUM: profiles.get(c.SODIUM_PROFILE_FACTOR, c.SODIUM_PROFILE_FACTOR_DEFAULT_VALUE),
        }
    )

    score = calculator.calculate(nutritional_values, food_type)

    # Convert the nutri-score to a score on a scale of 0-100
    nutriscore_scaled_100 = convert_nutri_score(score, food_type != ns.BEVERAGES)

    return nutriscore_scaled_100


def convert_nutri_score(nutri_score: int, solid: bool) -> int:
    """
    Convert the nutri-score to a score on a scale of 0-100 usinng [Yuka conversion table](https://help.yuka.io/l/en/article/owuc9rbhqs).

    Parameters
    ----------
    nutri_score : int
        The nutri-score value (-15 to 40).
    solid : bool
        True if the product is solid, False if the product is liquid.

    Returns
    -------
    int
        The nutrition score value on a scale of 0-100.
    """
    # Get the current file's directory
    current_dir = os.path.dirname(__file__)

    # Construct the path to the parent directory
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

    # Construct the path to the nutri_score_conversion.json file in the data subfolder
    file_path = os.path.join(parent_dir, "data", "nutri_score_conversion.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if solid:
        if nutri_score < -3:
            return 100
        elif nutri_score >= 19:
            return 0
        else:
            return data[str(nutri_score)]["solid"]
    else:
        if nutri_score < -3:
            return 80
        elif nutri_score >= 10:
            return 0
        else:
            return data[str(nutri_score)]["liquid"]


def calculate_additive_risk(additives: list[str]) -> tuple[int, list[dict]]:
    """
    Search for an additive by name and return its risk level

    Parameters
    ----------
    additives : list[str]
        A list of additives.

    Returns
    -------
    total_risk: int
        The total risk of the additives.
    additives_dict: list[dict]
        A list of dictionaries containing the additive name, e-number, type, and risk level.
    """
    # Get the current file's directory
    current_dir = os.path.dirname(__file__)

    # Construct the path to the parent directory
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

    # Construct the path to the additives.json file in the data subfolder
    file_path = os.path.join(parent_dir, "data", "additives.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    risk_level_present = [False, False, False, False]
    total_risk = 0

    additives_list = []

    for item in data:
        for additive in additives:
            if additive in item.get("e-number"):
                # Get the risk level of the additive: 0: no risk, 1: low risk, 2: moderate risk, 3: high risk
                if item.get("efsa_risk") != -1:
                    risk_level = item.get("efsa_risk")
                else:
                    risk_level = item.get("risk")

                risk_level_present[risk_level] = True
                total_risk += c.RISK_PER_ADDITIVE_PENALTY[risk_level]
                additives_list.append(
                    {"e-number": additive, "name": item.get("name"), "type": item.get("type"), "risk": risk_level}
                )

    # Add the additive presence penalty for the additive in the highest risk level
    for i in range(len(risk_level_present) - 1, -1, -1):
        if risk_level_present[i]:
            total_risk += c.RISK_ADDITIVE_PRESENCE_PENALTY[i]
            break

    return total_risk, additives_list


if __name__ == "__main__":
    print(fetch_and_calculate("00628915231984", {}))
    print(
        fetch_and_calculate(
            "00605388872074",
            {
                c.ENERGY_PROFILE_FACTOR: 0.25,
                c.SATURATION_PROFILE_FACTOR: 0.25,
                c.SUGARS_PROFILE_FACTOR: 0.25,
                c.SODIUM_PROFILE_FACTOR: 0.25,
                c.MAX_ADDITIVES_PENALTY: 50,
                c.NON_ORGANIC_PENALTY: 10,
            },
        )
    )
