import csv
import os.path
from pathlib import Path

from werkzeug.security import generate_password_hash

from recipe.adapters.datareader.csv_parser import CSVDataReader
from recipe.adapters.repository import AbstractRepository
from recipe.domainmodel.user import User


def populate(data_path: Path, repo: AbstractRepository, database_mode:bool):
    recipe_csv_filename = os.path.abspath(data_path / "recipes.csv")
    users_csv_filename = os.path.abspath(data_path / "users.csv")

    reader = CSVDataReader(recipe_csv_filename, users_csv_filename)
    reader.read_csv()

    authors = reader.authors
    categories = reader.categories
    images = reader.recipe_images
    ingredients = reader.recipes_ingredients
    instructions = reader.recipe_instructions
    nutritions = reader.recipe_nutritions
    recipes = reader.recipes
    users = reader.users


    repo.add_authors(authors)
    repo.add_categories(categories)
    repo.add_multiple_recipe_images(images)
    repo.add_multiple_recipe_ingredients(ingredients)
    repo.add_multiple_recipe_instructions(instructions)
    repo.add_nutritions(nutritions)
    repo.add_recipes(recipes)
    repo.add_users(users)