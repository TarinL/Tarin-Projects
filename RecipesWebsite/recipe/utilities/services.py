from recipe import Recipe
from recipe.adapters import repository
from typing import List


def get_random_recipe() -> Recipe:
    """ Returns a random recipe from the repository """

    return repository.repo_instance.get_random_recipe()


def get_health_stars(recipes: List[Recipe]) -> List[float]:
    """ Returns the list of health stars from the given recipes """
    return list(map(lambda recipe: recipe.nutrition.health_star_rating, recipes))
