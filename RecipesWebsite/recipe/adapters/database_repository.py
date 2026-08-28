import math
from typing import List, Type, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import scoped_session, joinedload
from sqlalchemy.orm.exc import NoResultFound

from recipe.adapters import orm
from recipe.adapters.filter import Filter
from recipe.adapters.orm import reviews_table, favourites_table, nutrition_table, recipes_table, authors_table, \
    users_table, categories_table
from recipe.adapters.repository import AbstractRepository
from utils import search_string
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.author import Author
from recipe.domainmodel.category import Category
from recipe.domainmodel.user import User
from recipe.domainmodel.review import Review
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction

NO_SORT_METHOD = "none"
SORT_METHOD_AUTHOR = 'author'
SORT_METHOD_DATE = 'date'
SORT_METHOD_NAME = 'name'
SORT_METHOD_RATING = 'rating'
SORT_METHOD_RECIPE = 'recipe'
SORT_METHOD_RECIPES_COUNT = 'recipes_count'
SORT_METHOD_USER = 'user'


# feature 1 test
class SessionContextManager:
    def __init__(self, session_factory):
        self.__session_factory = session_factory
        self.__session = scoped_session(self.__session_factory)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @property
    def session(self):
        return self.__session

    def commit(self) -> object:
        self.__session.commit()

    def rollback(self):
        self.__session.rollback()

    def reset_session(self):
        # this method can be used e.g. to allow Flask to start a new session for each http request,
        # via the 'before_request' callback
        self.close_current_session()
        self.__session = scoped_session(self.__session_factory)

    def close_current_session(self):
        if not self.__session is None:
            self.__session.close()


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session_factory):
        self._session_cm = SessionContextManager(session_factory)

    def close_session(self):
        self._session_cm.close_current_session()

    def reset_session(self):
        self._session_cm.reset_session()

    # region User_data Methods to manage Users
    def add_user(self, user: User):
        with self._session_cm as scm:
            scm.session.add(user)
            scm.commit()

    def add_users(self, users: List[User]):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                for user in users:
                    scm.session.add(user)
            scm.commit()

    def get_user(self, username: str) -> User:
        user = None
        try:
            user = self._session_cm.session.query(User).filter(users_table.c.username == username).first()
        except NoResultFound:
            print(f'User {username} was not found')

        return user

    # TODO: Check implementation
    def get_user_reviews(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> List[
        Review]:
        with self._session_cm as scm:
            offset = (page - 1) * page_size
            query = scm.session.query(Review).filter(reviews_table.c.user_id == user.id)
            if sort_method == NO_SORT_METHOD or not sort_method:
                pass
            elif sort_method == SORT_METHOD_DATE:
                query.order_by(Review.timestamp)
            elif sort_method == SORT_METHOD_RATING:
                query.order_by(Review.rating)
            else:
                raise ValueError(f"Invalid sort_method: {sort_method}")
            size = math.ceil(query.count() / page_size)
            return query.offset(offset).limit(page_size).all(), size

    # TODO: Check implementation
    def get_recipes_reviewed_by_user(self, user: User, page: int, page_size: int, sort_method: Optional[str] = None) -> \
            List[Recipe]:
        with self._session_cm as scm:
            offset = (page - 1) * page_size
            query = scm.session.query(Recipe).join(Review).filter(reviews_table.c.user_id == user.id)
            if sort_method == NO_SORT_METHOD:
                pass
            elif sort_method == SORT_METHOD_DATE:
                query.order_by(Review.timestamp)
            elif sort_method == SORT_METHOD_RATING:
                query.order_by(Review.rating)
            else:
                raise ValueError(f"Invalid sort_method: {sort_method}")
            return query.offset(offset).limit(page_size).all()

    # endregion

    # region Author_data Methods to manage Authors
    def add_author(self, author: Author):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                # Check if author already exists
                existing_author = scm.session.query(Author).filter(
                    Author.id == author.id).first()  # TODO: Author._Author__id or Author.id
                if not existing_author:
                    scm.session.add(author)
            scm.commit()

    # COMPLETE sorting by recipe counts
    def get_authors(self, sort_method: Optional[str] = None) -> List[Author]:
        authors = []
        if sort_method == NO_SORT_METHOD or not sort_method:
            authors = self._session_cm.session.query(Author).all()
        elif sort_method == SORT_METHOD_NAME:
            authors = self._session_cm.session.query(Author).order_by(Author.name).all()
        elif sort_method == SORT_METHOD_RECIPES_COUNT:
            # Join Author with Recipe, count recipes, group by author, order by count descending
            authors = (
                self._session_cm.session.query(Author)
                .outerjoin(Author.recipes)
                .group_by(Author.id)
                .order_by(func.count(Recipe.id).desc())
                .all()
            )
            return authors
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")
        return authors

    def get_author_by_id(self, author_id: int) -> Optional[Author]:
        author = None
        try:
            author = self._session_cm.session.query(Author).filter(authors_table.c.id == author_id).one()
        except NoResultFound:
            print(f'Recipe {author_id} was not found')

        return author

    def get_number_of_authors(self) -> int:
        num_authors = self._session_cm.session.query(Author).count()
        return num_authors

    def add_authors(self, authors: List[Author]):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                for author in authors:
                    # Check if author already exists
                    existing_author = scm.session.query(Author).filter(authors_table.c.id == author.id).first()
                    if not existing_author:
                        scm.session.add(author)
            scm.commit()

    # endregion

    # region Category_data Methods to manage Categories
    def add_category(self, category: Category):
        with self._session_cm as scm:
            scm.session.add(category)
            scm.commit()

    # Complete sort_recipe_count
    def get_categories(self, sort_method: Optional[str] = None) -> List[Category]:
        session = self._session_cm.session
        if not sort_method:
            categories = session.query(Category).all()
        elif sort_method == SORT_METHOD_NAME:
            categories = session.query(Category).order_by(Category._Category__name).all()
        elif sort_method == SORT_METHOD_RECIPES_COUNT:
            # Join Category with Recipe, count recipes per category, order descending
            categories = (
                session.query(Category)
                .outerjoin(Category._Category__recipes)
                .group_by(Category._Category__id)
                .order_by(func.count(Category._Category__recipes).desc())
                .all()
            )
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")
        return categories

    def get_category_by_name(self, name: str) -> Category:
        category = None
        try:
            category = self._session_cm.session.query(Category).filter(categories_table.c.name == name).first()
        except NoResultFound:
            pass
        return category

    def get_number_of_categories(self) -> int:
        return self._session_cm.session.query(Category).count()

    # Check this fuction, not sure it does what it supposed to
    def get_recipes_in_category(self, category_name: str) -> List[Recipe]:
        if category_name is None:
            recipes = self._session_cm.session.query(Recipe).all()
            return recipes
        else:
            recipes = self._session_cm.session.query(Recipe).join(Category).filter(
                categories_table.c.name == category_name).all()
            return recipes

    def add_categories(self, categories: List[Category]):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                for category in categories:
                    scm.session.add(category)
            scm.commit()

    # endregion

    # region Recipe_data Methods to manage Recipes

    def add_recipe(self, recipe: Recipe):
        with self._session_cm as scm:
            scm.session.add(recipe)
            scm.commit()

    def add_recipes(self, recipes: List[Recipe]):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                for recipe in recipes:
                    scm.session.add(recipe)
            scm.commit()

    def get_recipe_by_id(self, recipe_id: int) -> Recipe:
        recipe = None
        try:
            query = self._session_cm.session.query(Recipe).filter(recipes_table.c.id == recipe_id)
            recipe = query.one()
            # Populate the recipe with related data for consistent domain model interface
            self._populate_recipe_data(recipe)
        except NoResultFound:
            print(f'Recipe {recipe_id} was not found')

        return recipe

    # TODO: how does the sort_method apply in this function
    def get_recipes(self, page: int, page_size: int, search_filter: Filter) -> List[Recipe]:
        with self._session_cm as scm:
            query = scm.session.query(Recipe)

            # Filtering
            if search_filter.search:
                keyword = f"%{search_filter.search}%"
                if search_filter.search_type == "name":
                    query = query.filter(Recipe._Recipe__name.ilike(keyword))
                elif search_filter.search_type == "author":
                    query = query.join(Recipe._Recipe__author).filter(
                        Recipe._Recipe__author.name.ilike(keyword)
                    )
                elif search_filter.search_type == "category":
                    query = query.join(Recipe._Recipe__category).filter(
                        Recipe._Recipe__category.name.ilike(keyword)
                    )

            # Rating filter
            query = query.filter(
                Recipe._Recipe__rating >= search_filter.min_rating,
                Recipe._Recipe__rating <= search_filter.max_rating
            )

            # Sorting
            if search_filter.sort_method == SORT_METHOD_NAME:
                query = query.order_by(Recipe._Recipe__name)
            elif search_filter.sort_method == SORT_METHOD_DATE:
                query = query.order_by(Recipe._Recipe__date)
            elif search_filter.sort_method == SORT_METHOD_RATING:
                query = query.order_by(Recipe._Recipe__rating)
            else:
                raise ValueError(f"Invalid sort method: {search_filter.sort_method}")

            # Pagination
            start_index = (page - 1) * page_size
            recipes = query.offset(start_index).limit(page_size).all()

            # Optionally populate related data
            for recipe in recipes:
                self._populate_recipe_data(recipe)

            return recipes

    # TODO: This is incomplete
    def get_all_recipes(self, search_filter: Filter) -> List[Recipe]:
        with self._session_cm as scm:
            query = scm.session.query(Recipe)

            # Apply search filter
            if search_filter.search:
                keyword = f"%{search_filter.search}%"
                if search_filter.search_type == "name":
                    query = query.filter(Recipe._Recipe__name.ilike(keyword))
                elif search_filter.search_type == "author":
                    query = query.join(Recipe._Recipe__author).filter(
                        func.lower(Recipe._Recipe__author.name).ilike(keyword.lower())
                    )
                elif search_filter.search_type == "category":
                    query = query.join(Recipe._Recipe__category).filter(
                        func.lower(Recipe._Recipe__category.name).ilike(keyword.lower())
                    )

            # Apply rating/nutrition filters if needed
            query = query.filter(
                Recipe._Recipe__rating >= search_filter.min_rating,
                Recipe._Recipe__rating <= search_filter.max_rating
            )

            # Apply sorting
            if search_filter.sort_method == NO_SORT_METHOD or not search_filter.sort_method:
                pass
            elif search_filter.sort_method == SORT_METHOD_NAME:
                query = query.order_by(Recipe._Recipe__name)
            elif search_filter.sort_method == SORT_METHOD_DATE:
                query = query.order_by(Recipe._Recipe__date)
            elif search_filter.sort_method == SORT_METHOD_RATING:
                query = query.order_by(Recipe._Recipe__rating)
            else:
                raise ValueError(f"Invalid sort method: {search_filter.sort_method} for recipes")

            recipes = query.all()
            for recipe in recipes:
                self._populate_recipe_data(recipe)

            return recipes

    def get_number_of_recipes(self) -> int:
        num_recipes = self._session_cm.session.query(Recipe).count()
        return num_recipes

    # TODO: implement this function
    def get_recipe_page(self, page: int, page_size: int, search_filter: Filter) -> Tuple[List[Recipe], int]:
        with self._session_cm as scm:
            query = scm.session.query(Recipe)

            # Apply search filter
            if search_filter.search:
                keyword = f"%{search_filter.search}%"
                if search_filter.search_type == "name":
                    query = query.filter(Recipe._Recipe__name.ilike(keyword))
                elif search_filter.search_type == "author":
                    query = query.join(Recipe._Recipe__author).filter(Author._Author__name.ilike(keyword))
                elif search_filter.search_type == "category":
                    query = query.join(Recipe._Recipe__category).filter(Category._Category__name.ilike(keyword))

            # Apply rating filter (not populated i think?)
            query = query.filter(
                recipes_table.c.rating >= search_filter.min_rating,
                recipes_table.c.rating <= search_filter.max_rating
            )
            query = query.join(Nutrition).filter(
                nutrition_table.c.health_stars >= search_filter.min_nutrition,
                nutrition_table.c.health_stars <= search_filter.max_nutrition
            )

            # Apply sorting
            if search_filter.sort_method == "none":
                pass  # default, no sorting
            elif search_filter.sort_method == "name":
                query = query.order_by(Recipe._Recipe__name)
            elif search_filter.sort_method == "date":
                query = query.order_by(Recipe._Recipe__date)
            elif search_filter.sort_method == "rating":
                query = query.order_by(Recipe._Recipe__rating)
            else:
                raise ValueError(f"Invalid sort method: {search_filter.sort_method}")

            # Get total count for pagination
            total_count = query.count()
            total_pages = math.ceil(total_count / page_size)

            # Apply pagination
            offset = (page - 1) * page_size
            recipes = query.offset(offset).limit(page_size).all()

            # Optionally populate related data
            for recipe in recipes:
                self._populate_recipe_data(recipe)

            return recipes, total_pages

    def get_random_recipe(self) -> Recipe:
        return self.get_recipe_by_id(38)

    # TODO: implement this function
    def get_recipe_reviews(
            self,
            recipe_id: int,
            page: int,
            page_size: int,
            sort_method: Optional[str] = None
    ) -> List["Review"]:
        with self._session_cm as scm:
            query = scm.session.query(Review).filter(Review.recipe_id == recipe_id)

            # Apply sorting
            if sort_method is None:
                pass  # default, no sorting
            elif sort_method == SORT_METHOD_DATE:
                query = query.order_by(reviews_table.c.timestamp)
            elif sort_method == SORT_METHOD_RATING:
                query = query.order_by(Review.rating)
            elif sort_method == SORT_METHOD_USER:
                query = query.join(Review.user).order_by(User.username)
            else:
                raise ValueError(f"Invalid sort method: {sort_method}")

            # Apply pagination
            offset = (page - 1) * page_size
            reviews = query.offset(offset).limit(page_size).all()

            return reviews

    # endregion

    # region Review_data Methods to manage Reviews
    def add_review(self, review: Review):
        with self._session_cm as scm:
            scm.session.add(review)
            scm.commit()

            reviews = scm.session.query(Review).filter(reviews_table.c.recipe_id == review.recipe.id).all()
            avg = 0
            for rev in reviews:
                avg += rev.rating / len(reviews)

            recipe = scm.session.query(Recipe).filter(recipes_table.c.id == review.recipe.id).first()
            recipe.rating = avg
            scm.commit()

    # TODO: double check its function
    def get_all_reviews(self, sort_method: Optional[str] = None) -> List[Review]:
        session = self._session_cm.session
        query = session.query(Review)

        # If sorting by user, join the User table
        if sort_method == SORT_METHOD_USER:
            query = query.join(User).order_by(
                users_table.c.name)  # assuming 'name' is a User attribute
        elif sort_method == SORT_METHOD_DATE:
            query = query.order_by(Review.date)
        elif sort_method == SORT_METHOD_RATING:
            query = query.order_by(Review.rating)
        elif sort_method is None:
            pass  # no sorting
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

        # Eager-load related objects if needed

        return query.all()

    # TODO: implement with pagination
    def get_reviews(self, page: int, page_size: int, sort_method: Optional[str] = None) -> List[Review]:
        session = self._session_cm.session
        query = session.query(Review)

        # Apply sorting
        if sort_method == SORT_METHOD_DATE:
            query = query.order_by(Review.date)
        elif sort_method == SORT_METHOD_RATING:
            query = query.order_by(Review.rating)
        elif sort_method == SORT_METHOD_USER:
            query = query.join(Review.user).order_by(Review.user.name)
            query = query.options(joinedload(Review.user))  # eager-load user
        elif sort_method is None or sort_method == NO_SORT_METHOD:
            pass
        else:
            raise ValueError(f"Invalid sort method: {sort_method}")

        # Apply pagination
        start_index = (page - 1) * page_size
        query = query.offset(start_index).limit(page_size)

        return query.all()

    def get_review_by_id(self, review_id: int) -> Review:
        review = None
        try:
            review = self._session_cm.session.query(Review).filter(reviews_table.c.id == review_id).one()
        except NoResultFound:
            pass
        return review

    def add_reviews(self, reviews: List[Review]):
        with self._session_cm as scm:
            with scm.session.no_autoflush:
                for review in reviews:
                    scm.session.add(review)
            scm.commit()

    # endregion

    # region User_favourite_recipes Methods to manage User's favourite Recipes
    def add_favourite_recipe(self, user: User, favourite: Favourite):
        existing_fav = self._session_cm.session.query(Favourite).filter(
            (favourites_table.c.recipe_id == favourite.recipe.id)).first()

        if not existing_fav:
            self._session_cm.session.add(favourite)
            self._session_cm.session.commit()
        else:
            raise ValueError(f"Recipe {favourite.recipe.name} already exists in user's favourites")

    def remove_favourite_recipe(self, user: User, recipe: Recipe):
        with self._session_cm as scm:
            existing_fav = scm.session.query(Favourite).filter(
                Favourite._Favourite__recipe == recipe,
                Favourite._Favourite__user == user
            ).first()

            if existing_fav:
                scm.session.delete(existing_fav)
                scm.session.commit()
            else:
                raise ValueError(f"Recipe {recipe.name} does not exist in user's favourites")

    # TODO:Implement
    def get_favourite_recipes(self, page: int, page_size: int, user: User) -> List[Recipe]:
        pass

    def get_favourite_page(self, user: User, page: int, page_size: int, search_filter: Filter) -> tuple[
        List[Recipe], int]:
        session = self._session_cm.session
        query = session.query(Recipe).join(Favourite).filter(favourites_table.c.user_id == user.id)

        # Apply sorting
        if search_filter.sort_method == SORT_METHOD_DATE:
            query = query.order_by(Recipe.date)
        elif search_filter.sort_method == SORT_METHOD_RATING:
            query = query.order_by(Recipe.rating)
        elif search_filter.sort_method == SORT_METHOD_NAME:
            query = query.order_by(Recipe.name)
        elif search_filter.sort_method == NO_SORT_METHOD:
            pass
        else:
            raise ValueError(f"Invalid sort method: {search_filter.sort_method}")

        # Apply pagination
        start_index = (page - 1) * page_size
        count = query.count()
        query = query.offset(start_index).limit(page_size)

        recipes = query.all()

        for recipe in recipes:
            self._populate_recipe_data(recipe)

        return recipes, count

    # endregion

    # region Nutrition_data Methods to manage Nutrition
    def get_nutrition_by_id(self, recipe_id: int) -> Optional[Nutrition]:
        nutrition = None
        try:
            nutrition = self._session_cm.session.query(Nutrition).filter(
                nutrition_table.c.id == recipe_id).one()
        except NoResultFound:
            pass
        return nutrition

    def add_nutrition(self, nutrition: Nutrition):
        with self._session_cm as scm:
            scm.session.add(nutrition)
            scm.commit()

    def add_nutritions(self, nutritions: List[Nutrition]):
        with self._session_cm as scm:
            for nutrition in nutritions:
                scm.session.add(nutrition)
            scm.commit()

    # endregion

    def _populate_recipe_data(self, recipe: Recipe):
        """
        Populate a Recipe object with related data (images, ingredients, instructions)
        to maintain consistent domain model interface between memory and database repositories.
        """
        if recipe is None:
            return

        # Use the same session context
        with self._session_cm as scm:
            self._populate_recipe_data_in_session(recipe, scm.session)

    def _populate_recipe_data_in_session(self, recipe: Recipe, session):
        """
        Populate a Recipe object with related data using the provided session.
        """
        if recipe is None:
            return

        # Load and populate images
        recipe_images = session.query(RecipeImage).filter(
            RecipeImage._RecipeImage__recipe_id == recipe.id
        ).order_by(RecipeImage._RecipeImage__position).all()

        if recipe_images:
            image_urls = [img.url for img in recipe_images]
            recipe._Recipe__images = image_urls
        else:
            print(f"DEBUG: No images found for recipe {recipe.id}")

        # TODO: Load and populate ingredients

        # TODO: Load and populate instructions

    # region RecipeImage Methods
    def add_recipe_image(self, recipe_image: RecipeImage):
        with self._session_cm as scm:
            scm.session.add(recipe_image)
            scm.commit()

    def add_multiple_recipe_images(self, recipe_images: List[RecipeImage]):
        with self._session_cm as scm:
            for recipe_image in recipe_images:
                scm.session.add(recipe_image)
            scm.commit()

    def get_recipe_images(self, recipe_id: int) -> List[RecipeImage]:
        with self._session_cm as scm:
            images = scm.session.query(RecipeImage).filter(
                RecipeImage._RecipeImage__recipe_id == recipe_id).all()
        return images

    # endregion

    # region RecipeIngredient Methods
    def add_recipe_ingredient(self, recipe_ingredient: RecipeIngredient):
        with self._session_cm as scm:
            scm.session.add(recipe_ingredient)
            scm.commit()

    def add_multiple_recipe_ingredients(self, recipe_ingredients: List[RecipeIngredient]):
        with self._session_cm as scm:
            for r in recipe_ingredients:
                scm.session.add(r)
            scm.commit()

    def get_recipe_ingredients(self, recipe_id: int) -> List[RecipeIngredient]:
        with self._session_cm as scm:
            ingredients = scm.session.query(RecipeIngredient).filter(
                RecipeIngredient._RecipeIngredient__recipe_id == recipe_id).all()
        return ingredients

    # endregion

    # region RecipeInstruction Methods
    def add_recipe_instruction(self, recipe_instruction: RecipeInstruction):
        with self._session_cm as scm:
            scm.session.add(recipe_instruction)
            scm.commit()

    def add_multiple_recipe_instructions(self, recipe_instructions: List[RecipeInstruction]):
        with self._session_cm as scm:
            for r in recipe_instructions:
                scm.session.add(r)
            scm.commit()

    def get_recipe_instructions(self, recipe_id: int) -> List[RecipeInstruction]:
        with self._session_cm as scm:
            instructions = scm.session.query(RecipeInstruction).filter(
                RecipeInstruction._RecipeInstruction__recipe_id == recipe_id).all()
        return instructions

    # endregion
