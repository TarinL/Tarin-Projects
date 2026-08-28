from recipe.adapters.filter import Filter
from recipe.domainmodel.author import Author
from recipe.domainmodel.category import Category
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User
from typing import List, Optional
import abc

# Shared global repo instance
repo_instance: "AbstractRepository | None" = None


class AbstractRepository(abc.ABC):
    #region Authors

    @abc.abstractmethod
    def add_author(self, author: Author):
        raise NotImplementedError

    @abc.abstractmethod
    def get_authors(self, sort_method: Optional[str] = None) -> List[Author]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_author_by_id(self, author_id: int) -> Optional[Author]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_number_of_authors(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def add_authors(self, authors: List[Author]):
        raise NotImplementedError

    #endregion

    #region Categories
    @abc.abstractmethod
    def add_category(self, category: Category):
        raise NotImplementedError

    @abc.abstractmethod
    def get_categories(self, sort_method: Optional[str] = None) -> List[Category]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_category_by_name(self, category_name: str) -> Optional[Category]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_number_of_categories(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipes_in_category(self, category_name: str) -> List[Recipe]:
        raise NotImplementedError

    @abc.abstractmethod
    def add_categories(self, categories: List[Category]):
        raise NotImplementedError

    #endregion

    #region Recipes

    @abc.abstractmethod
    def add_recipe(self, recipe: Recipe):
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_recipes(self, search_filter: Filter) -> List[Recipe]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipes(self, page: int, page_size: int, search_filter: Filter) -> List[Recipe]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_page(self, page: int, page_size: int, search_filter: Filter) -> tuple[List[Recipe], int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_number_of_recipes(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_reviews(self, recipe_id: int, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Review]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_random_recipe(self) -> Recipe:
        raise NotImplementedError

    @abc.abstractmethod
    def add_recipes(self, recipes: List[Recipe]):
        raise NotImplementedError

    #endregion

    #region Reviews

    @abc.abstractmethod
    def add_review(self, review: Review):
        raise NotImplementedError

    @abc.abstractmethod
    def get_all_reviews(self, sort_method: Optional[str] = None) -> List[Review]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_reviews(self, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Review]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        raise NotImplementedError

    @abc.abstractmethod
    def add_reviews(self, reviews: List[Review]):
        raise NotImplementedError

    #endregion

    #region User

    @abc.abstractmethod
    def add_user(self, user: User):
        """" Adds a User to the repository. """
        raise NotImplementedError

    @abc.abstractmethod
    def add_users(self, users: List[User]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_user(self, user_name: str) -> Optional[User]:
        """ Returns the User named user_name from the repository.

        If there is no User with the given user_name, this method returns None.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_reviews(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> tuple[List[Review], int]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipes_reviewed_by_user(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Recipe]:
        raise NotImplementedError

    #endregion

    #region Favourites

    @abc.abstractmethod
    def add_favourite_recipe(self, user: User, favourite: Favourite):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_favourite_recipe(self, user: User, recipe: Recipe):
        raise NotImplementedError

    def get_favourite_recipes(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Recipe]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_favourite_page(self, user: User, page: int, page_size: int, search_filter: Filter) -> tuple[List[Recipe], int]:
        raise NotImplementedError

    #endregion

    #region Nutrition

    def add_nutrition(self, nutrition: Nutrition):
        raise NotImplementedError

    def get_nutrition_by_id(self, recipe_id: int) -> Optional[Nutrition]:
        raise NotImplementedError

    def add_nutritions(self, nutritions: List[Nutrition]):
        raise NotImplementedError

    #endregion

    # region RecipeInstruction Methods
    @abc.abstractmethod
    def add_recipe_instruction(self, recipe_instruction: RecipeInstruction):
        raise NotImplementedError

    @abc.abstractmethod
    def add_multiple_recipe_instructions(self, recipe_instructions: List[RecipeInstruction]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_instructions(self, recipe_id: int) -> List[RecipeInstruction]:
        raise NotImplementedError

    # endregion

    # region RecipeIngredient Methods
    @abc.abstractmethod
    def add_recipe_ingredient(self, recipe_ingredient: RecipeIngredient):
        raise NotImplementedError

    @abc.abstractmethod
    def add_multiple_recipe_ingredients(self, recipe_ingredients: List[RecipeIngredient]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_ingredients(self, recipe_id: int) -> List[RecipeIngredient]:
        raise NotImplementedError

    # endregion

    # region RecipeImage Methods
    @abc.abstractmethod
    def add_recipe_image(self, recipe_image: RecipeImage):
        raise NotImplementedError

    @abc.abstractmethod
    def add_multiple_recipe_images(self, recipe_images: List[RecipeImage]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipe_images(self, recipe_id: int) -> List[RecipeImage]:
        raise NotImplementedError

    # endregion