from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from recipe.domainmodel.recipe import Recipe
    from recipe.domainmodel.user import User


class Review:
    _comment_id: int = 1

    def __init__(self, user: "User", recipe: "Recipe", rating: float, comment: str, timestamp: Optional[datetime] = None, rev_id: int = None):
        self.__id: int = Review._comment_id if not rev_id else rev_id
        Review._comment_id += 1
        self.__user: "User" = user
        self.__recipe: "Recipe" = recipe
        self.rating: float = rating
        self.__comment: str = comment
        self.__timestamp: datetime = timestamp or datetime.now()

    @property
    def id(self):
        return self.__id

    @property
    def comment(self):
        return self.__comment

    @comment.setter
    def comment(self, new_comment):
        self.__comment = new_comment

    @property
    def rating(self) -> float:
        return self.__rating if self.__rating else 0.0

    @rating.setter
    def rating(self, new_rating):
        if new_rating < 0 or new_rating > 5:
            raise ValueError('rating must be between 0 and 5')
        self.__rating = new_rating

    @property
    def timestamp(self) -> datetime:
        return self.__timestamp

    @property
    def user(self) -> "User":
        return self.__user

    @property
    def recipe(self) -> "Recipe":
        return self.__recipe

    def __eq__(self, other):
        if not isinstance(other, Review):
            return False
        return self.__id == other.id

    def __repr__(self):
        return 'Review(id={}, user={}, recipe={}, rating={}, comment={})'.format(self.id, self.user, self.recipe,
                                                                                 self.rating, self.comment)
