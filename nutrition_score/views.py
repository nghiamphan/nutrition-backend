from rest_framework.response import Response
from rest_framework.decorators import api_view

from .utils import helpers


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

    profiles = request.data

    food_object = helpers.fetch_and_calculate(barcode, profiles)

    if not food_object:
        return Response({"error": "Product not found"}, status=404)

    return Response(food_object, status=200)
