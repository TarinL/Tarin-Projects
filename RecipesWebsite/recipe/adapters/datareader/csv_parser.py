from __future__ import annotations

import os.path
from datetime import datetime
from pathlib import Path

from pygments.lexers import q

from recipe.adapters.repository import AbstractRepository
from recipe.domainmodel.author import Author
from recipe.domainmodel.category import Category
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash
import ast
import csv
import re

def _parse_int(row, row_name: str, default=None):
    val = row.get(row_name)

    val = (val or "").strip()
    if not val or val.upper() == "NA":
        return default
    try:
        return int(val)
    except ValueError:
        return default

def _parse_float(row, row_name: str, default=None):
    val = row.get(row_name)

    val = (val or "").strip()
    if not val or val.upper() == "NA":
        return default
    try:
        return float(val)
    except ValueError:
        return default

def _parse_list_string(row, row_name: str):
    val = row.get(row_name)

    val = (val or "").strip()
    if not val:
        return []
    try:
        output_list = ast.literal_eval(val)
        return [str(val).strip() for val in output_list if str(val).strip()]
    except (ValueError, SyntaxError):
        return [val]

def _strip_or_default(row, row_name: str, default=None):
    val = row.get(row_name)

    val = (val or "").strip()
    if not val or val.upper() == "NA":
        return default
    return val

def _parse_date(row, row_name: str) -> datetime:
    val = row.get(row_name)

    s = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', (val or "").strip())
    return datetime.strptime(s, "%d %b %Y")

class CSVDataReader:
    """ An in memory repository that stores data read from a csv file. """

    def __init__(self, recipes_filename: str, users_filename: str):
        self.__recipes_filename: str = recipes_filename
        self.__users_filename: str = users_filename
        self.__recipes: List[Recipe] = list()
        self.__authors: List[Author] = list()
        self.__categories: List[Category] = list()
        self.__users: List[User] = list()
        self.__recipe_images: List[RecipeImage] = list()
        self.__recipe_instructions: List[RecipeInstruction] = list()
        self.__recipes_ingredients: List[RecipeIngredient] = list()
        self.__nutritions: List[Nutrition] = list()

    @property
    def recipes(self) -> List[Recipe]:
        return self.__recipes

    @property
    def authors(self) -> List[Author]:
        return self.__authors

    def get_author(self, author_id: int) -> Optional[Author]:
        return next((a for a in self.__authors if a.id == author_id), None)

    @property
    def categories(self) -> List[Category]:
        return self.__categories

    def get_category(self, category_name: str) -> Optional[Category]:
        return next((c for c in self.__categories if c.name == category_name), None)

    @property
    def users(self) -> List[User]:
        return self.__users

    @property
    def recipe_images(self) -> List[RecipeImage]:
        return self.__recipe_images

    @property
    def recipe_instructions(self) -> List[RecipeInstruction]:
        return self.__recipe_instructions

    @property
    def recipes_ingredients(self) -> List[RecipeIngredient]:
        return self.__recipes_ingredients

    @property
    def recipe_nutritions(self) -> List[Nutrition]:
        return self.__nutritions

    def read_csv(self):
        """ Reads in all CSV files' (recipes and users) data removing bad entries and duplicates. """

        self.read_recipes_csv()
        self.read_users_csv()

    def read_recipes_csv(self):
        """ Reads in all recipes from CSV, removing bad and duplicate entries. """

        if not os.path.exists(self.__recipes_filename):
            print(f"File {self.__recipes_filename} does not exist.")
            return

        with open(self.__recipes_filename, "r", encoding="utf-8-sig") as f:
            rows = csv.DictReader(f)
            author_count = 1
            category_count = 1

            for row in rows:
                try:
                    # Get basic recipe information
                    recipe_id: int = _parse_int(row, "RecipeId")
                    recipe_name: Optional[str] = _strip_or_default(row, "Name")

                    # Skip if malformed
                    if not recipe_name:
                        continue

                    # Get Author info
                    author_name: Optional[str] = _strip_or_default(row, "AuthorName")
                    author_id: int = _parse_int(row, "AuthorId")

                    # Default if empty
                    if not author_name:
                        author_name = "Unknown Author"
                        print(f"WARN: Default author name used for author id <{author_id}>, recipe <{recipe_id}>:'{recipe_name}'")

                    # Check for existing author
                    author_obj: Optional[Author] = self.get_author(author_id)
                    if not author_obj:
                        if author_id:
                            candidate_author = Author(author_id, author_name, None)
                        else:
                            candidate_author = Author(author_count, author_name, None)
                            author_count += 1
                        self.__authors.append(candidate_author)
                        author_obj = candidate_author

                    # Get category info
                    category_name: str = _strip_or_default(row, "RecipeCategory", default="")
                    category_obj: Optional[Category] = self.get_category(category_name)
                    if not category_obj:
                        category_obj = Category(category_name, None, category_count)
                        self.__categories.append(category_obj)
                        category_count += 1

                    # Get more recipe info
                    cook_time: int = _parse_int(row, "CookTime", default=0)
                    prep_time: int = _parse_int(row, "PrepTime", default=0)
                    date_published: datetime = _parse_date(row, "DatePublished")
                    description: str = _strip_or_default(row, "Description", default="")
                    images: List[str] = _parse_list_string(row, "Images")
                    ingredient_quantities: List[str] = _parse_list_string(row, "RecipeIngredientQuantities")
                    ingredients: List[str] = _parse_list_string(row, "RecipeIngredientParts")
                    instructions: List[str] = _parse_list_string(row, "RecipeInstructions")
                    servings: Optional[int] = _parse_int(row, "RecipeServings")
                    recipe_yield: Optional[str] = _strip_or_default(row, "RecipeYield")

                    # Get nutrition info
                    calories: float = _parse_float(row, "Calories", default=0.0)
                    fats: float = _parse_float(row, "FatContent", default=0.0)
                    saturated_fats = _parse_float(row, "SaturatedFatContent", default=0.0)
                    cholesterol: float = _parse_float(row, "CholesterolContent", default=0.0)
                    sodium: float = _parse_float(row, "SodiumContent", default=0.0)
                    carbohydrates: float = _parse_float(row, "CarbohydrateContent", default=0.0)
                    fibre: float = _parse_float(row, "FiberContent", default=0.0)
                    sugars: float = _parse_float(row, "SugarContent", default=0.0)
                    protein: float = _parse_float(row, "ProteinContent", default=0.0)

                    # Make nutrition object
                    nutrition_obj: Nutrition = Nutrition(
                        recipe_id=recipe_id,
                        calories=calories,
                        fat_content=fats,
                        saturated_fat_content=saturated_fats,
                        cholesterol_content=cholesterol,
                        sodium_content=sodium,
                        carbohydrates_content=carbohydrates,
                        fiber_content=fibre,
                        sugars_content=sugars,
                        proteins_content=protein,
                    )
                    self.__nutritions.append(nutrition_obj)

                    #TODO
                    # Make recipe image object:
                    for i in range(len(images)):
                        image_obj: RecipeImage = RecipeImage(recipe_id,images[i],i)
                        self.__recipe_images.append(image_obj)


                    #TODO: make recipe ingredients
                    for i, ingredient in enumerate(ingredients):
                        # If the quantity is missing, use "0" as default
                        quantity = ingredient_quantities[i] if i < len(ingredient_quantities) else "0"

                        # Create the RecipeIngredient object
                        ingredient_obj = RecipeIngredient(recipe_id, quantity, ingredient, i)

                        # Add to your list or repository
                        self.__recipes_ingredients.append(ingredient_obj)

                    #TODO: make recipe instruction
                    for i in range(len(instructions)):
                        instruction_obj: RecipeInstruction = RecipeInstruction(recipe_id, instructions[i],i)
                        self.__recipe_instructions.append(instruction_obj)

                    # Make recipe
                    recipe: Recipe = Recipe(
                        recipe_id=recipe_id,
                        name=recipe_name,
                        author=author_obj,
                        cook_time=cook_time,
                        preparation_time=prep_time,
                        created_date=date_published,
                        description=description,
                        images=images,
                        category=category_obj,
                        ingredient_quantities=ingredient_quantities,
                        ingredients=ingredients,
                        rating=None,
                        nutrition=nutrition_obj,
                        servings=servings,
                        recipe_yield=recipe_yield,
                        instructions=instructions,
                    )

                    # Link recipe to author
                    author_obj.recipes.append(recipe)

                    # Append
                    self.__recipes.append(recipe)
                except (ValueError, KeyError) as e:
                    print(f"ERROR: Skipping malformed row: {e}")
                    continue

    def read_users_csv(self):
        """ Reads in all users from CSV, removing bad and duplicate entries. """

        if not os.path.exists(self.__users_filename):
            print(f"ERROR: File {self.__users_filename} does not exist.")
            return

        with open(self.__users_filename, "r", encoding="utf-8-sig") as f:
            rows = csv.DictReader(f)

            for row in rows:
                username = _strip_or_default(row, "username")
                password = _strip_or_default(row, "password")
                user_id = _parse_int(row, "id")

                if not username or not password or not user_id:
                    print(f"ERROR: Malformed user (ID/NAME/PASS) {user_id}/{username}/{password} in CSV.")
                    continue

                user = User(
                    username=username,
                    password=generate_password_hash(password),
                    user_id=user_id
                )

                if next(filter(lambda u: u.username == user.username, self.__users), None):
                    print(f"ERROR: User {user.username} already exists in repository.")
                else:
                    self.__users.append(user)
