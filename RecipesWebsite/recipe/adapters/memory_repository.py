from recipe.adapters.filter import Filter
from recipe.adapters.repository import AbstractRepository
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
import math
import random

NO_SORT_METHOD = "none"
SORT_METHOD_AUTHOR = 'author'
SORT_METHOD_DATE = 'date'
SORT_METHOD_NAME = 'name'
SORT_METHOD_RATING = 'rating'
SORT_METHOD_RECIPE = 'recipe'
SORT_METHOD_RECIPES_COUNT = 'recipes_count'
SORT_METHOD_USER = 'user'


def _recipe_filter(recipe: Recipe, search_filter: Filter) -> bool:
    if recipe.rating < search_filter.min_rating:
        return False
    if recipe.rating > search_filter.max_rating:
        return False
    if recipe.nutrition.health_star_rating < search_filter.min_nutrition:
        return False
    if recipe.nutrition.health_star_rating > search_filter.max_nutrition:
        return False
    if not search_filter.search:
        return True
    if search_filter.search_type == "name":
        if not search_filter.search in recipe.name.lower():
            return False
    elif search_filter.search_type == "author":
        if not search_filter.search in recipe.author.name.lower():
            return False
    elif search_filter.search_type == "category":
        if not search_filter.search in recipe.category.name.lower():
            return False
    return True


class MemoryRepository(AbstractRepository):
    def __init__(self):
        self.__authors = list()
        self.__categories = list()
        self.__nutritions = list()
        self.__recipes = list()
        self.__reviews = list()
        self.__tags = list()
        self.__users = list()

        self._next_category_id = 1
        self._next_user_id = 1

    # region Authors

    def add_author(self, author: Author):
        self.__validate_author(author)
        self.__authors.append(author)
        pass

    def get_authors(self, sort_method: Optional[str] = None) -> List[Author]:
        if not sort_method:
            return self.__authors
        if sort_method == SORT_METHOD_NAME:
            return sorted(self.__authors, key=lambda a: a.name)
        elif sort_method == SORT_METHOD_RECIPES_COUNT:
            return sorted(self.__authors, key=lambda a: len(a.recipes))
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

    def get_author_by_id(self, author_id: int) -> Optional[Author]:
        return next(filter(lambda a: a.id == author_id, self.__authors), None)

    def get_number_of_authors(self) -> int:
        return len(self.__authors)

    def add_authors(self, authors: List[Author]):
        for author in authors:
            self.add_author(author)

    def __validate_author(self, author: Author):
        if author in self.__authors:
            raise FileExistsError(f"Author {author.name} already exists in repo")
        if not author.name:
            raise ValueError("Author name cannot be empty")
        if author.id < 0:
            raise ValueError("Author id cannot be negative")
        return

    # endregion

    # region Categories

    def add_category(self, category: Category):
        if not category.id:
            category.id = self._next_category_id
            self._next_category_id += 1
        self.__validate_category(category)
        self.__categories.append(category)

    def get_categories(self, sort_method: Optional[str] = None) -> List[Category]:
        if not sort_method:
            return self.__categories
        if sort_method == SORT_METHOD_NAME:
            return sorted(self.__categories, key=lambda c: c.name)
        elif sort_method == SORT_METHOD_RECIPES_COUNT:
            return sorted(self.__categories, key=lambda c: len(c.recipes))
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

    def get_category_by_name(self, category_name: str) -> Optional[Category]:
        return next(filter(lambda c: c.name == category_name, self.__categories), None)

    def get_number_of_categories(self) -> int:
        return len(self.__categories)

    def get_recipes_in_category(self, category_name: str) -> List[Recipe]:
        return list(filter(lambda r: r.category.name == category_name, self.__recipes))

    def add_categories(self, categories: List[Category]):
        for category in categories:
            self.add_category(category)

    def __validate_category(self, category: Category):
        """ Validates a category object, note: type checking in if statements in unnecessary. """
        if not category.name:
            raise ValueError("Category name cannot be empty")
        if self.get_category_by_name(category.name):
            raise FileExistsError(f"Category {category.name} already exists in repo")
        return

    # endregion

    # region Recipes

    def add_recipe(self, recipe: Recipe):
        self.__validate_recipe(recipe)
        self.__recipes.append(recipe)

    def get_all_recipes(self, search_filter: Filter) -> List[Recipe]:
        if search_filter.sort_method == NO_SORT_METHOD:
            recipes = self.__recipes
        elif search_filter.sort_method == SORT_METHOD_NAME:
            recipes = sorted(self.__recipes, key=lambda r: r.name)
        elif search_filter.sort_method == SORT_METHOD_DATE:
            recipes = sorted(self.__recipes, key=lambda r: r.date)
        elif search_filter.sort_method == SORT_METHOD_RATING:
            recipes = sorted(self.__recipes, key=lambda r: r.rating)
        else:
            raise ValueError(f"Invalid sort method: {search_filter.sort_method} for recipes")

        return list(filter(lambda r: _recipe_filter(r, search_filter), recipes))

    def get_recipes(self, page: int, page_size: int, search_filter: Filter) -> List[Recipe]:
        sorted_recipes = self.get_all_recipes(search_filter)

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return sorted_recipes[start_index:end_index]

    def get_recipe_page(self, page: int, page_size: int, search_filter: Filter) -> tuple[List[Recipe], int]:
        sorted_recipes = self.get_all_recipes(search_filter)

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return sorted_recipes[start_index:end_index], math.ceil(len(sorted_recipes) / page_size)

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        return next(filter(lambda r: r.id == recipe_id, self.__recipes), None)

    def get_number_of_recipes(self) -> int:
        return len(self.__recipes)

    def get_recipe_reviews(self, recipe_id: int, page: int, page_size: int, sort_method: Optional[str] = None) -> List[
        Review]:
        recipe = self.get_recipe_by_id(recipe_id)
        if not sort_method:
            reviews = recipe.reviews
        elif sort_method == SORT_METHOD_DATE:
            reviews = sorted(recipe.reviews, key=lambda r: r.timestamp)
        elif sort_method == SORT_METHOD_RATING:
            reviews = sorted(recipe.reviews, key=lambda r: r.rating)
        elif sort_method == SORT_METHOD_USER:
            reviews = sorted(recipe.reviews, key=lambda r: r.user)
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

        return reviews

    def get_random_recipe(self) -> Recipe:
        return self.__recipes[random.randint(0, len(self.__recipes) - 1)]

    def get_recipes_in_category(self, category_name: str) -> List[Recipe]:
        raise NotImplementedError

    def add_recipes(self, recipes: List[Recipe]):
        for recipe in recipes:
            self.add_recipe(recipe)

    def __validate_recipe(self, recipe: Recipe):
        if self.get_recipe_by_id(recipe.id) or recipe in self.__recipes:
            raise FileExistsError(f"Recipe {recipe.id} already exists in repo")
        if recipe.id < 0:
            raise ValueError("Recipe id cannot be negative")

        return

    # endregion

    # region Reviews

    def add_review(self, review: Review):
        self.__validate_review(review)
        self.__reviews.append(review)
        review.user.add_review(review)
        review.recipe.add_review(review)

    def get_all_reviews(self, sort_method: Optional[str] = None) -> List[Review]:
        if not sort_method:
            return self.__reviews
        if sort_method == SORT_METHOD_DATE:
            return sorted(self.__reviews, key=lambda r: r.date)
        elif sort_method == SORT_METHOD_RATING:
            return sorted(self.__reviews, key=lambda r: r.rating)
        elif sort_method == SORT_METHOD_USER:
            return sorted(self.__reviews, key=lambda r: r.user)
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

    def get_reviews(self, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Review]:
        sorted_reviews = self.get_all_reviews(sort_method=sort_method)

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return sorted_reviews[start_index:end_index]

    def get_review_by_id(self, review_id: int) -> Optional[Review]:
        return next(filter(lambda r: r.id == review_id, self.__reviews), None)

    def add_reviews(self, reviews: List[Review]):
        for review in reviews:
            self.add_review(review)

    def __validate_review(self, review: Review):
        if not self.get_recipe_by_id(review.recipe.id):
            raise ValueError(f"Recipe {review.recipe.name} not found in repo")
        if self.get_review_by_id(review.id):
            raise ValueError(f"Recipe {review} already exists in repo")
        if review.rating is None or not (0.0 <= review.rating <= 5.0):
            raise ValueError("Review rating must be between 0.0 and 5.0")
        if review.id < 0:
            raise ValueError("Review id cannot be negative")
        return

    # endregion

    # region Users

    def add_user(self, user: User):
        if not user.id:
            user.id = self._next_user_id
            self._next_user_id += 1
        self.__validate_user(user)
        self.__users.append(user)

    def add_users(self, users: List[User]):
        for user in users:
            self.add_user(user)

    def get_user(self, user_name: str) -> Optional[User]:
        return next(filter(lambda u: u.username == user_name, self.__users), None)

    def get_user_reviews(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> tuple[List[Review], int]:
        if not sort_method:
            reviews = user.reviews
        elif sort_method == SORT_METHOD_DATE:
            reviews = sorted(user.reviews, key=lambda r: r.date)
        elif sort_method == SORT_METHOD_RATING:
            reviews = sorted(user.reviews, key=lambda r: r.rating)
        elif sort_method == SORT_METHOD_USER:
            reviews = sorted(user.reviews, key=lambda r: r.user)
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return reviews[start_index:end_index], math.ceil(len(reviews) / page_size)

    def get_recipes_reviewed_by_user(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> \
    List[
        Recipe]:
        recipes = [review.recipe for review in user.reviews]
        if sort_method == SORT_METHOD_DATE:
            recipes = sorted(recipes, key=lambda r: r.date)
        elif sort_method == SORT_METHOD_RATING:
            recipes = sorted(recipes, key=lambda r: r.rating)
        elif sort_method == SORT_METHOD_USER:
            recipes = sorted(recipes, key=lambda r: r.user)
        elif sort_method:
            raise ValueError(f"Invalid sort method: {sort_method}")

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return recipes[start_index:end_index]

    def __validate_user(self, user: User):
        if self.get_user(user.username):
            raise ValueError(f"User {user.username} already exists in repo")
        if not user.username:
            raise ValueError(f"Username cannot be empty")
        if not user.password:
            raise ValueError(f"Password cannot be empty")
        return

    # endregion

    # region Favourites

    def add_favourite_recipe(self, user: User, favourite: Favourite):
        if favourite not in user.favourite_recipes:
            user.favourite_recipes.append(favourite)
        else:
            raise ValueError(f"Recipe {favourite.recipe.name} already exists in user's favourites")

    def remove_favourite_recipe(self, user: User, favourite: Favourite):
        if favourite in user.favourite_recipes:
            user.favourite_recipes.remove(favourite)
        else:
            raise ValueError(f"Recipe {favourite.recipe.name} does not exist in user's favourites")

    def get_favourite_recipes(self, user: User, search_filter: Filter) -> List[Recipe]:
        recipes = list(map(lambda f: f.recipe, user.favourite_recipes))
        if search_filter.sort_method == NO_SORT_METHOD:
            pass
        elif search_filter.sort_method == SORT_METHOD_NAME:
            recipes = sorted(recipes, key=lambda r: r.name)
        elif search_filter.sort_method == SORT_METHOD_DATE:
            recipes = sorted(recipes, key=lambda r: r.date)
        elif search_filter.sort_method == SORT_METHOD_RATING:
            recipes = sorted(recipes, key=lambda r: r.rating)
        else:
            raise ValueError(f"Invalid sort method: {search_filter.sort_method} for recipes")

        return list(filter(lambda r: _recipe_filter(r, search_filter), recipes))

    def get_favourite_page(self, user: User, page: int, page_size: int, search_filter: Filter) -> tuple[List[Recipe], int]:
        recipes = self.get_favourite_recipes(user, search_filter)

        page_start = (page - 1) * page_size
        page_end = page_start + page_size
        return recipes[page_start:page_end], math.ceil(len(recipes) / page_size)

    # endregion

    # region Nutrition

    def add_nutrition(self, nutrition: Nutrition):
        if nutrition not in self.__nutritions:
            self.__nutritions.append(nutrition)

    def get_nutrition_by_id(self, recipe_id: int) -> Optional[Nutrition]:
        return next(filter(lambda n: n.recipe_id == recipe_id, self.__nutritions), None)

    def add_nutritions(self, nutritions: List[Nutrition]):
        """ Does nothing intentionally """
        pass

    # endregion

    #TODO:
    def add_recipe_instruction(self, recipe_instruction: RecipeInstruction):
        """ Does nothing intentionally """
        pass


    def add_multiple_recipe_instructions(self, recipe_instructions: List[RecipeInstruction]):
        """ Does nothing intentionally """
        pass


    def get_recipe_instructions(self, recipe_id: int) -> List[RecipeInstruction]:
        """ Does nothing intentionally """
        pass

    # endregion

    # region RecipeIngredient Methods

    def add_recipe_ingredient(self, recipe_ingredient: RecipeIngredient):
        """ Does nothing intentionally """
        pass


    def add_multiple_recipe_ingredients(self, recipe_ingredients: List[RecipeIngredient]):
        """ Does nothing intentionally """
        pass

    def get_recipe_ingredients(self, recipe_id: int) -> List[RecipeIngredient]:
        """ Does nothing intentionally """
        pass

    # endregion

    # region RecipeImage Methods
    def add_recipe_image(self, recipe_image: RecipeImage):
        """ Does nothing intentionally """
        pass

    def add_multiple_recipe_images(self, recipe_images: List[RecipeImage]):
        """ Does nothing intentionally """
        pass

    def get_recipe_images(self, recipe_id: int) -> List[RecipeImage]:
        """ Does nothing intentionally """
        pass

    # endregion