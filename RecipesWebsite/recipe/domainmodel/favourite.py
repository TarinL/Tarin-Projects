from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recipe.domainmodel.recipe import Recipe
    from recipe.domainmodel.user import User


class Favourite:
    _id: int = 1

    def __init__(self, user: "User", recipe: "Recipe"):
        self.__id: int = Favourite._id
        Favourite._id += 1
        self.__user: "User" = user
        self.__recipe: "Recipe" = recipe

    @property
    def id(self) -> int:
        return self.__id

    @property
    def user(self) -> "User":
        return self.__user

    @property
    def recipe(self) -> "Recipe":
        return self.__recipe

    @recipe.setter
    def recipe(self, recipe: "Recipe"):
        self.__recipe = recipe

    def __eq__(self, other):
        if not isinstance(other, Favourite):
            return False
        return self.user == other.user and self.recipe == other.recipe

    def __hash__(self):
        return hash((self.user, self.recipe))
