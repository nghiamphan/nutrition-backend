from django.urls import path
from . import views

urlpatterns = [
    path("barcode/", views.calculate_nutrition_score),
    path("barcode/<str:barcode>/", views.calculate_nutrition_score),
    path("image/", views.calculate_nutrition_score_from_image),
]
