from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.review import Review
from typing import List


class User:
    def __init__(self, username: str, password: str, user_id: int = None):
        self.__id: int = user_id
        self.__username: str = username
        self.__password: str = password
        self.__favourite_recipes: List["Favourite"] = []
        self.__reviews: List["Review"] = []

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.username}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __lt__(self, other) -> bool:
        if not isinstance(other, User):
            raise TypeError("Comparison must be between User instances")
        return self.id < other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def id(self) -> int:
        return self.__id

    @id.setter
    def id(self, id: int):
        self.__id = id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password(self) -> str:
        return self.__password

    @property
    def favourite_recipes(self) -> list["Favourite"]:
        return self.__favourite_recipes

    @property
    def reviews(self) -> list["Review"]:
        return self.__reviews

    def add_review(self, review: "Review") -> None:
        """ Adds a review to the list of reviews. """

        if not isinstance(review, Review):
            raise TypeError("Expected a Review instance")
        self.__reviews.append(review)

    def remove_review(self, review: "Review") -> None:
        """ Removes a review from the list of reviews. """

        if review in self.__reviews:
            self.__reviews.remove(review)
        else:
            raise ValueError("Review not found in user's reviews")

    def check_password(self, password: str) -> bool:
        """ Checks if the password is correct. """

        from werkzeug.security import check_password_hash
        return check_password_hash(self.__password, password)
    # #add a recipe to a user fav list
    # def has_favorite(self, recipe: "Recipe") -> bool:
    #     return any(fav.recipe == recipe for fav in self.__favourite_recipes)
    # #I want to remove a recipe from a user fav list
    # def remove_favourite(self, recipe: "Recipe"):
    #     self.__favourite_recipes = [fav for fav in self.__favourite_recipes if fav.recipe != recipe]

    # maybe I should use the predefined methods of adding and removing fav
