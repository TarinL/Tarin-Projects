from recipe import Recipe
from recipe.adapters import repository
from recipe.adapters.filter import Filter
from recipe.adapters.repository import AbstractRepository
from recipe.domainmodel.user import User
from typing import List


class NonExistentRecipeException(Exception):
    pass


class UnknownUserException(Exception):
    pass


def get_user(user_name: str):
    """ Gets the current user from the repository """

    curr_user = repository.repo_instance.get_user(user_name)
    return curr_user


def get_user_favourites(user: User) -> List[Recipe]:
    """ Collects the user's favourites into a list """

    return [fav.recipe for fav in user.favourite_recipes]


def get_recipes(user: User, page: int, search_filter: Filter) -> tuple[List[Recipe], int]:
    """ Gets sorted and filtered list of recipes """

    page_size: int = 10
    return repository.repo_instance.get_favourite_page(user=user, page=page, page_size=page,
                                                       search_filter=search_filter)
