# Food types
GENERAL_FOOD = "general_food"
RED_MEAT = "red_meat"
CHEESE = "cheese"
FATS_NUTS_SEEDS = "fats_oils_nuts_seeds"
BEVERAGES = "beverages"
WATER = "water"

# Component names
ENERGY = "energy"
ENERGY_FROM_SATURATES = "energy_from_saturates"
SATURATED_FAT = "saturated_fat"
SATURATES_OVER_TOTAL_FAT = "saturates_over_total_fat"
SUGARS = "sugars"
NN_SWEETENERS = "non_nutritive_sweeteners"
SODIUM = "sodium"
PROTEIN = "protein"
FIBER = "fiber"
FRUIT_PERCENTAGE = "fruit_vegetables_legumes_percentage"

# Negative component thresholds
ENERGY_THRESHOLD = [335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350]
SATURATED_FAT_THRESHOLD = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SUGARS_THRESHOLD = [3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51]
SODIUM_THRESHOLD = [0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4]

ENERGY_FROM_SATURATES_THRESHOLD = [120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200]
SATURATES_OVER_TOTAL_FAT_THRESHOLD = [10, 16, 22, 28, 34, 40, 46, 52, 58, 64]

ENERGY_BEVERAGES_THRESHOLD = [30, 90, 150, 210, 240, 270, 300, 330, 360, 390]
SUGARS_BEVERAGES_THRESHOLD = [0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11]

# Positive component thresholds
PROTEIN_THRESHOLD = [2.4, 4.8, 7.2, 9.6, 12, 14, 17]
FIBER_THRESHOLD = [3.0, 4.1, 5.2, 6.3, 7.4]
FRUIT_THRESHOLD = [40, 60, 80, 80, 80]

PROTEIN_BEVERAGES_THRESHOLD = [1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]
FRUIT_BEVERAGES_THRESHOLD = [40, 40, 60, 60, 80, 80]

# Category thresholds
GENERAL_FODD_CATEGORY_THRESHOLD = [(0, "A"), (2, "B"), (10, "C"), (18, "D")]
FATS_NUTS_SEEDS_CATEGORY_THRESHOLD = [(-6, "A"), (2, "B"), (10, "C"), (18, "D")]
BEVERAGES_CATEGORY_THRESHOLD = [(1, "B"), (6, "C"), (9, "D")]

# Error Messages
INVALID_FOOD_TYPE = f"Invalid food type: {{}}. Must be one of {GENERAL_FOOD}, {RED_MEAT}, {CHEESE}, {FATS_NUTS_SEEDS}, {BEVERAGES}, {WATER}."


class NutriScoreCalculator:
    def __init__(self):
        self.setup_profiles()

    def setup_profiles(self, profiles: dict = {}) -> None:
        """
        Parameters
        ----------
        profiles: a dictionary of nutrition profiles.

        Example:
        {
            "energy": 1,
            "saturated_fat": 1,
            "sugars": 1.5,
            "sodium": 0.5
        }

        By default, all profile factors are set to 1. If a profile factor is greater than 1, it means that the user wants to be more strict with that component. If the factor is smaller than 1, it means that the user wants to be more flexible with that component.

        For example, if sugars profile is set to 1.5, it means that consuming 10 grams of sugars will incur the same amount of negative points as consuming 15 grams of sugars under default setting.

        Note: Energy profile affects both energy and energy_from_saturates. Saturated fat profile affects both saturated fat and saturates_over_total_fat.
        """
        self.energy_profile = profiles.get(ENERGY, 1)
        self.saturated_fat_profile = profiles.get(SATURATED_FAT, 1)
        self.sugar_profile = profiles.get(SUGARS, 1)
        self.sodium_profile = profiles.get(SODIUM, 1)

    def get_input(self, nutritions: dict) -> None:
        self.energy = nutritions.get(ENERGY, 0) * self.energy_profile
        self.energy_from_saturates = nutritions.get(ENERGY_FROM_SATURATES, 0) * self.energy_profile

        self.saturated_fat = nutritions.get(SATURATED_FAT, 0) * self.saturated_fat_profile
        self.saturates_over_total_fat = nutritions.get(SATURATES_OVER_TOTAL_FAT, 0) * self.saturated_fat_profile

        self.sugars = nutritions.get(SUGARS, 0) * self.sugar_profile
        self.nn_sweeteners = nutritions.get(NN_SWEETENERS, False)

        self.sodium = nutritions.get(SODIUM, 0) * self.sodium_profile

        self.protein = nutritions.get(PROTEIN, 0)
        self.fiber = nutritions.get(FIBER, 0)
        self.fruit_percentage = nutritions.get(FRUIT_PERCENTAGE, 0)

    def points_by_threshold(self, value: float, threshold_list: list[float]) -> int:
        """
        Calculate the points of a specific component based on its threshold list.
        """
        for i in range(len(threshold_list)):
            if value <= threshold_list[i]:
                return i
        return len(threshold_list)

    def calculate_negative_points(self, food_type: str) -> int:
        if food_type in [GENERAL_FOOD, RED_MEAT, CHEESE]:
            energy_points = self.points_by_threshold(self.energy, ENERGY_THRESHOLD)
            saturated_fat_points = self.points_by_threshold(self.saturated_fat, SATURATED_FAT_THRESHOLD)
            sugars_points = self.points_by_threshold(self.sugars, SUGARS_THRESHOLD)
            sodium_points = self.points_by_threshold(self.sodium, SODIUM_THRESHOLD)

            return energy_points + saturated_fat_points + sugars_points + sodium_points

        elif food_type == FATS_NUTS_SEEDS:
            energy_from_saturates_points = self.points_by_threshold(
                self.energy_from_saturates, ENERGY_FROM_SATURATES_THRESHOLD
            )
            saturates_over_total_fat_points = self.points_by_threshold(
                self.saturates_over_total_fat, SATURATES_OVER_TOTAL_FAT_THRESHOLD
            )
            sugars_points = self.points_by_threshold(self.sugars, SUGARS_THRESHOLD)
            sodium_points = self.points_by_threshold(self.sodium, SODIUM_THRESHOLD)

            return energy_from_saturates_points + sugars_points + saturates_over_total_fat_points + sodium_points

        elif food_type == BEVERAGES:
            energy_points = self.points_by_threshold(self.energy, ENERGY_BEVERAGES_THRESHOLD)
            saturated_fat_points = self.points_by_threshold(self.saturated_fat, SATURATED_FAT_THRESHOLD)
            sugars_points = self.points_by_threshold(self.sugars, SUGARS_BEVERAGES_THRESHOLD)
            sodium_points = self.points_by_threshold(self.sodium, SODIUM_THRESHOLD)
            sweeteners_points = 4 if self.nn_sweeteners else 0

            return energy_points + saturated_fat_points + sugars_points + sodium_points + sweeteners_points

        return 0

    def calculate_positive_points(self, food_type: str, negative_points: int) -> int:
        fiber_points = self.points_by_threshold(self.fiber, FIBER_THRESHOLD)

        if food_type != BEVERAGES:
            protein_points = self.points_by_threshold(self.protein, PROTEIN_THRESHOLD)
            fruit_points = self.points_by_threshold(self.fruit_percentage, FRUIT_THRESHOLD)
        else:
            protein_points = self.points_by_threshold(self.protein, PROTEIN_BEVERAGES_THRESHOLD)
            fruit_points = self.points_by_threshold(self.fruit_percentage, FRUIT_BEVERAGES_THRESHOLD)

        if food_type in [GENERAL_FOOD, RED_MEAT, CHEESE]:
            # If food type is red meat, the number of points for protein is limited to 2
            if food_type == RED_MEAT:
                protein_points = min(protein_points, 2)
            # If negative points >= 11 and food type is not cheese, exclude protein points
            if negative_points >= 11 and food_type != CHEESE:
                protein_points = 0
        elif food_type == FATS_NUTS_SEEDS:
            # If negative points >= 7, exclude protein points
            if negative_points >= 7:
                protein_points = 0

        return protein_points + fiber_points + fruit_points

    def calculate(self, nutritions: dict, food_type: str) -> int:
        """
        Calculate the Nutri-Score based on the nutritions and food type.

        Parameters
        ----------
        nutritions: dict
            a dictionary of nutritions.

            Example:
            {
                "energy": 100,
                "saturated_fat": 5,
                "sugars": 10,
                "sodium": 0.5,
                "protein": 1.5,
                "fiber": 2,
                "fruit_vegetables_legumes_percentage": 40
            }
        food_type: str
            the type of food.

        Returns
        -------
        nutri-score: int
            the calculated Nutri-Score.
        """
        if food_type not in [GENERAL_FOOD, RED_MEAT, CHEESE, FATS_NUTS_SEEDS, BEVERAGES, WATER]:
            raise ValueError(INVALID_FOOD_TYPE.format(food_type))

        # By default, water has a Nutri-Score of 0
        if food_type == WATER:
            return 0

        self.get_input(nutritions)
        negative_points = self.calculate_negative_points(food_type)
        positive_points = self.calculate_positive_points(food_type, negative_points)
        return negative_points - positive_points

    def calculate_category(self, nutritions: dict, food_type: str) -> str:
        """
        Calculate the Nutri-Score category based on the nutritions and food type.

        Parameters
        ----------
        nutritions: dict
            a dictionary of nutritions.

            Example:
            {
                "energy": 100,
                "saturated_fat": 5,
                "sugars": 10,
                "sodium": 0.5,
                "protein": 1.5,
                "fiber": 2,
                "fruit_vegetables_legumes_percentage": 40
            }
        food_type: str
            the type of food.

        Returns
        -------
        category: str
            the Nutri-Score category, from "A" to "E".
        """
        score = self.calculate(nutritions, food_type)
        category = self.categorize(score, food_type)
        return category

    def categorize(self, score: int, food_type: str) -> str:
        """
        Categorize a score into a letter category based on the food type.

        Parameters
        ----------
        score: int
            the calculated Nutri-Score.
        food_type: str
            the type of food.

        Returns
        -------
        category: str
            the Nutri-Score category, from "A" to "E".
        """
        # By default, water has a Nutri-Score category of "A"
        if food_type == WATER:
            return "A"
        elif food_type in [GENERAL_FOOD, RED_MEAT, CHEESE]:
            category_threshold = GENERAL_FODD_CATEGORY_THRESHOLD
        elif food_type == FATS_NUTS_SEEDS:
            category_threshold = FATS_NUTS_SEEDS_CATEGORY_THRESHOLD
        elif food_type == BEVERAGES:
            category_threshold = BEVERAGES_CATEGORY_THRESHOLD
        else:
            raise ValueError(INVALID_FOOD_TYPE.format(food_type))

        for threshold, category in category_threshold:
            if score <= threshold:
                return category
        return "E"
