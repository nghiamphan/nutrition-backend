import json
import os
import tempfile

from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.files.uploadedfile import InMemoryUploadedFile

from .utils import helpers
from .utils import nutri_score as ns


@api_view(["POST"])
def calculate_nutrition_score(request, barcode=None) -> Response:
    """
    Given a product barcode, calculate the nutrition score of the product.

    Parameters
    ----------
    request : Request
        The request object containing the nutrition profile.

        For example:
        request.data = {
            "energy_profile_factor": 1,
            "saturation_profile_factor": 1,
            "sugars_profile_factor": 1,
            "sodium_profile_factor": 1,
            "max_additives_penalty": 50,
            "non_organic_penalty": 10,
        }
    barcode : str
        The barcode string (UPC, EAN) of the product.

    Returns
    -------
    Response
        The response object containing the nutrition score and various information of the product.

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
    if not barcode:
        return Response({"error": "Barcode is required"}, status=400)

    profile = request.data

    food_object = helpers.fetch_and_calculate(barcode, profile)

    if not food_object:
        return Response({"error": "Nutritional values not found"}, status=404)

    return Response(food_object, status=200)


@api_view(["POST"])
def calculate_nutrition_score_from_image(request) -> Response:
    """
    Given images of a nutrition label and ingredients, calculate the nutrition score of the product.

    Parameters
    ----------
    request : Request
        The request object containing the image file and the nutrition profile.

        For example:
        request.data = {
            "food_type": "general_food",
            "profiles": {
                "energy_profile_factor": 1,
                "saturation_profile_factor": 1,
                "sugars_profile_factor": 1,
                "sodium_profile_factor": 1,
                "max_additives_penalty": 50,
                "non_organic_penalty": 10,
            }
            "images": ["Image file 1", "Image file 2"],
        }

    Returns
    -------
    Response
        The response object containing the nutrition score and various information of the product.
    """
    # Check if image files are included in the request
    if "images" not in request.FILES or not (1 <= len(request.FILES.getlist("images")) <= 2):
        return Response({"error": "One or two image files are required in the request"}, status=400)

    images = request.FILES.getlist("images")
    temp_file_paths = []

    try:
        # Save the images to temporary files
        for image in images:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in image.chunks():
                    temp_file.write(chunk)
                temp_file_paths.append(temp_file.name)

        food_type = request.data.get("food_type", ns.GENERAL_FOOD)
        profile = json.loads(request.data.get("nutritionProfile", {}))

        food_object = helpers.process_image_and_calculate(temp_file_paths, food_type, profile)

    finally:
        # Clean up the temporary files
        for temp_file_path in temp_file_paths:
            os.remove(temp_file_path)

    return Response(food_object, status=200)
