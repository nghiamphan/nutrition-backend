import cv2
import pytesseract
import numpy as np
import re
import os
import sys

# Add the parent directory to the path to import the utils module so that we can run this script from the command line
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils import constants as c
from utils import nutri_score as ns


def preprocess_image(image_path) -> np.ndarray:
    """
    Preprocess the image by converting it to grayscale, thresholding, and morphological operations.

    Parameters
    ----------
    image_path : str
        The path to the image file.

    Returns
    -------
    processed_image: np.ndarray
        The processed image as a NumPy array.
    """
    # Read the image
    image = cv2.imread(image_path)

    # Resize the image to a fixed height while maintaining aspect ratio
    height = 800
    aspect_ratio = height / image.shape[0]
    new_dimensions = (int(image.shape[1] * aspect_ratio), height)
    image = cv2.resize(image, new_dimensions, interpolation=cv2.INTER_AREA)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Denoise the image
    gray = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)

    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Morphological operations to close gaps
    kernel = np.ones((2, 2), np.uint8)
    processed_image = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Edge detection
    edges = cv2.Canny(processed_image, 100, 200)

    # Combine edges with the processed image
    processed_image = cv2.bitwise_or(processed_image, edges)

    return processed_image


def extract_text_from_image(image_path) -> str:
    """
    Extract text from the image using Tesseract OCR.

    Parameters
    ----------
    image_path : str
        The path to the image file.

    Returns
    -------
    text: str
        The extracted text from the image.
    """
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image, config="--psm 6").lower()
    return text


def extract_serving_info(text) -> float:
    """
    Extract the serving size information from the text.

    Parameters
    ----------
    text : str
        The text extracted from the image.

    Returns
    -------
    value: float
        The serving size in grams or milliliters.
    """
    for line in text.splitlines():
        if "per" in line or "pour" in line:
            # Extract the number and unit inside the bracket
            match = re.search(r"\((\d*\.?\d+)\s*(mL|L|g|kg)\)", line)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()

                # Convert units to a standard unit (grams or milliliters)
                if unit == "l" or unit == "kg":
                    value *= 1000

                return value

    return 100


def extract_nutrient_info(text, possible_nutrient_names: list, scale: float = 1) -> float:
    """
    Extract the value of a nutrient from the text.

    Parameters
    ----------
    text : str
        The text extracted from the image.
    possible_nutrient_names : list
        A list of possible names of the nutrient.
    scale : float, optional
        The scale factor to apply to the nutrient value, by default 1. This is used to convert the nutrient value to a standard size of 100g or 100ml for nutriscore calculation.

    Returns
    -------
    value: float
        The value of the nutrient in grams or milligrams per 100g or 100mL.
    """
    for line in text.splitlines():
        for nutrient_name in possible_nutrient_names:
            pattern = f"{nutrient_name}.*?(\\d*\\.?\\d+)\\s*(mg|g)?"
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = match.group(2)

                if unit == "mg":
                    value /= 1000  # Convert mg to g

                return value * scale

    return 0


def extract_all_nutrient_info(text) -> dict:
    """
    Extract all nutrient information from the text.

    Parameters
    ----------
    text : str
        The text extracted from the image.

    Returns
    -------
    nutritions: dict
        A dictionary containing the nutrient information per 100g or 100mL.
    """
    serving_size = extract_serving_info(text)
    scale = 100 / serving_size

    nutrients = {
        ns.ENERGY: ["calories", "energy", "cal", "ca"],
        "fat": ["fat", "lipides"],
        ns.SATURATED_FAT: ["saturated", "saturated fat", "saturés"],
        ns.SUGARS: ["sugars", "sucres", "sug", "su"],
        ns.SODIUM: ["sodium"],
        ns.PROTEIN: ["protein", "proteins", "protéine", "protéines"],
        ns.FIBER: ["fiber", "fibre", "fibres"],
    }

    nutritions = {
        ns.ENERGY: 0,
        ns.ENERGY_FROM_SATURATES: 0,
        ns.SATURATED_FAT: 0,
        ns.SATURATES_OVER_TOTAL_FAT: 0,
        ns.SUGARS: 0,
        ns.NN_SWEETENERS: 0,
        ns.SODIUM: 0,
        ns.PROTEIN: 0,
        ns.FIBER: 0,
        ns.FRUIT_PERCENTAGE: 0,
        "fat": 0,
    }
    for nutrient, possible_nutrient_names in nutrients.items():
        value = extract_nutrient_info(text, possible_nutrient_names, scale)
        nutritions[nutrient] = value

    nutritions[ns.ENERGY_FROM_SATURATES] = nutritions[ns.SATURATED_FAT] * 9

    if nutritions["fat"]:
        nutritions[ns.SATURATES_OVER_TOTAL_FAT] = nutritions[ns.SATURATED_FAT] / nutritions["fat"]

    return nutritions


def extract_ingredients(text) -> list:
    """
    Extract the ingredients from the text.

    Parameters
    ----------
    text : str
        The text extracted from the image.

    Returns
    -------
    ingredients: list
        A list of ingredients.
    """
    ingredients = []
    capture = False
    ingredients_text = ""

    for line in text.splitlines():
        if capture:
            ingredients_text += " " + line.strip()
        elif re.search(r"\bingredients\b", line, re.IGNORECASE):
            capture = True
            # Extract the ingredients after the word "ingredients"
            match = re.search(r"\bingredients\b\s*:\s*(.*)", line, re.IGNORECASE)
            if match:
                ingredients_text += match.group(1)

    # Split by comma or period, strip whitespace, and remove non-numeric/alphabet characters
    ingredients = [
        re.sub(r"[^a-zA-Z0-9\s]", "", ingredient.strip())
        for ingredient in re.split(r"[,.]", ingredients_text)
        if ingredient.strip()
    ]

    return ingredients


if __name__ == "__main__":
    # image_name = "nutrition_label.jpg"
    image_name = "ingredients.jpg"

    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the nutrition_label.png file in the tests folder
    image_path = os.path.join(current_dir, "..", "tests", image_name)

    # Normalize the path
    image_path = os.path.normpath(image_path)

    text = extract_text_from_image(image_path)
    print(text)

    if image_name.startswith("nutrition"):
        serving_info = extract_serving_info(text)
        print("Serving info:", serving_info)

        nutritions = extract_all_nutrient_info(text)
        print("Nutrition data:", nutritions)
    else:
        ingredients = extract_ingredients(text)
        print("Ingredients:", ingredients)
