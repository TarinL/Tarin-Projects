from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recipe.domainmodel.recipe import Recipe


class Nutrition:
    def __init__(self, recipe_id: int, calories: float, fat_content: float, saturated_fat_content: float,
                 cholesterol_content: float, sodium_content: float,
                 carbohydrates_content: float, sugars_content: float, proteins_content: float, fiber_content: float):
        self.__recipe_id: int = recipe_id
        self.__calories: float = calories
        self.__fat_content: float = fat_content
        self.__sat_fat_content: float = saturated_fat_content
        self.__cholesterol_content: float = cholesterol_content
        self.__sodium_content: float = sodium_content
        self.__carbohydrates_content: float = carbohydrates_content
        self.__sugars_content: float = sugars_content
        self.__proteins_content: float = proteins_content
        self.__fiber_content: float = fiber_content
        self.__health_stars: float = self.calculate_health_stars()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Nutrition):
            return False
        return self.__recipe_id == other.recipe_id

    def __lt__(self, other) -> bool:
        if not isinstance(other, Nutrition):
            raise TypeError("Comparison must be between Nutrition instances")
        return self.__calories < other.__calories

    def __hash__(self) -> int:
        return hash(self.__recipe_id)

    def __repr__(self) -> str:
        return (f"<Nutrition Recipe={self.__recipe_id}, Calories={self.__calories}, "
                f"Fat={self.__fat_content}g, Protein={self.__proteins_content}g>")

    @property
    def recipe_id(self) -> int:
        return self.__recipe_id

    @property
    def calories(self) -> float:
        return self.__calories

    @calories.setter
    def calories(self, calories: float) -> None:
        self.__calories = calories

    @property
    def fat_content(self) -> float:
        return self.__fat_content

    @fat_content.setter
    def fat_content(self, fat_content: float):
        self.__fat_content = fat_content

    @property
    def saturated_fat_content(self) -> float:
        return self.__sat_fat_content

    @saturated_fat_content.setter
    def saturated_fat_content(self, sat_fat: float) -> None:
        self.__sat_fat_content = sat_fat

    @property
    def cholesterol_content(self) -> float:
        return self.__cholesterol_content

    @cholesterol_content.setter
    def cholesterol_content(self, cholesterol: float) -> None:
        self.__cholesterol_content = cholesterol

    @property
    def sodium_content(self) -> float:
        return self.__sodium_content

    @sodium_content.setter
    def sodium_content(self, sodium: float) -> None:
        self.__sodium_content = sodium

    @property
    def carbohydrates_content(self) -> float:
        return self.__carbohydrates_content

    @carbohydrates_content.setter
    def carbohydrates_content(self, carbohydrates: float) -> None:
        self.__carbohydrates_content = carbohydrates

    @property
    def sugars_content(self) -> float:
        return self.__sugars_content

    @sugars_content.setter
    def sugars_content(self, sugars: float) -> None:
        self.__sugars_content = sugars

    @property
    def proteins_content(self) -> float:
        return self.__proteins_content

    @proteins_content.setter
    def proteins_content(self, proteins: float) -> None:
        self.__proteins_content = proteins

    @property
    def fiber_content(self) -> float:
        return self.__fiber_content

    @fiber_content.setter
    def fiber_content(self, fiber: float) -> None:
        self.__fiber_content = fiber

    @property
    def health_star_rating(self) -> float:
        return self.__health_stars

    def calculate_health_stars(self) -> float:
        """
        Calculates an inaccurate health star rating based on NZ and AUS standards due to missing information (i.e what
        percentage of the food is fruit/nuts, and total weight to adjust values for per 100g for calculations).

        """
        # Calculate baseline points (negatively impact star rating)
        # Convert calories to kJ
        energy_points = (self.calories * 4.184) // 335
        sodium_points = self.sodium_content // 90
        sat_fat_points = math.floor(self.saturated_fat_content)
        sugar_points = (self.sugars_content - 1.1) // 3.9
        baseline_points = energy_points + sodium_points + sat_fat_points + sugar_points

        # Calculate modifying points (positively impact star rating)
        fibre_points = math.floor(self.fiber_content + 0.1)
        protein_points = self.proteins_content // 1.6
        modifying_points = fibre_points + protein_points

        # Get total points
        total_points = baseline_points - modifying_points

        # Convert points to health stars (Note: unsuitable for a mathematical equation due to differing distances)
        if total_points <= -11:
            health_stars = 5.0
        elif total_points <= -7:
            health_stars = 4.5
        elif total_points <= -2:
            health_stars = 4.0
        elif total_points <= 2:
            health_stars = 3.5
        elif total_points <= 6:
            health_stars = 3.0
        elif total_points <= 11:
            health_stars = 2.5
        elif total_points <= 15:
            health_stars = 2.0
        elif total_points <= 20:
            health_stars = 1.5
        elif total_points <= 24:
            health_stars = 1.0
        else:
            health_stars = 0.5

        return health_stars
