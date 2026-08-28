from sqlalchemy import (
    Table, Column, Integer, Float, String, DateTime, ForeignKey, Text, UniqueConstraint, MetaData,
)
from sqlalchemy.orm import registry, relationship

from recipe.domainmodel.category import Category
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.author import Author
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User

# Global variable giving access to the MetaData (schema) information of the database
metadata = MetaData()
mapper_registry = registry()

# Favourite table
favourites_table = Table(
    "favourites", mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("user_id", ForeignKey("users.id")),
)

# Review table
reviews_table = Table(
    "reviews", mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("user_id", ForeignKey("users.id")),
    Column("rating", Float, nullable=False ),
    Column("comment", String(500), nullable=False),
    Column("timestamp", DateTime, nullable=False),
)

# Users table

users_table = Table(
    "users", mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, nullable=False),
    Column("password", String, nullable=False),
)

# Recipe ingredients table
recipe_ingredients_table = Table(
    "recipe_ingredients", mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("quantity", String(255)), #No nullable?
    Column("ingredient", String(255)), #No nullable?
    Column("position",Integer),
)

# Recipe instruction table
recipe_instructions_table = Table(
    "recipe_instructions", mapper_registry.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("step", String(255)),
    Column("position", Integer),
)


# Authors table
authors_table = Table(
    'authors', mapper_registry.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False)
)

# Category table
categories_table = Table(
    'categories', mapper_registry.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False,unique=True),
)

# Nutrition table
nutrition_table = Table(
    'nutrition', mapper_registry.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('calories', Float),
    Column('fat', Float),
    Column('saturated_fat', Float),
    Column('cholesterol', Float),
    Column('sodium', Float),
    Column('carbohydrates', Float),
    Column('fiber', Float),
    Column('sugar', Float),
    Column('protein', Float),
    Column('health_stars', Float)
)

# Recipes table
recipes_table = Table(
    'recipes', mapper_registry.metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),
    Column('author_id', Integer, ForeignKey('authors.id'), nullable=False),
    Column('description', Text, nullable=False),
    Column('nutrition_id', Integer, ForeignKey('nutrition.id'), unique=True),
    Column('category_id', Integer, ForeignKey('categories.id')),
    Column('date', DateTime, nullable=False),
    Column('rating', Float, nullable=True)
)

# Recipe images table
recipe_images_table = Table(
    'recipe_images', mapper_registry.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('recipe_id', Integer, ForeignKey('recipes.id'), nullable=False),
    Column('url', String(500), nullable=False),
    Column('position', Integer, nullable=False)
)




# ORM Mappings
def map_model_to_tables():

    # Author mapping
    mapper_registry.map_imperatively(Author, authors_table, properties={
        '_Author__id': authors_table.c.id,
        '_Author__name': authors_table.c.name,
        '_Author__recipes': relationship(Recipe, back_populates='_Recipe__author')
    })

    # Nutrition mapping
    mapper_registry.map_imperatively(Nutrition, nutrition_table, properties={
        '_Nutrition__recipe_id': nutrition_table.c.id,
        '_Nutrition__calories': nutrition_table.c.calories,
        '_Nutrition__fat_content': nutrition_table.c.fat,
        '_Nutrition__sat_fat_content': nutrition_table.c.saturated_fat,
        '_Nutrition__cholesterol_content': nutrition_table.c.cholesterol,
        '_Nutrition__sodium_content': nutrition_table.c.sodium,
        '_Nutrition__carbohydrates_content': nutrition_table.c.carbohydrates,
        '_Nutrition__fiber_content': nutrition_table.c.fiber,
        '_Nutrition__sugars_content': nutrition_table.c.sugar,
        '_Nutrition__proteins_content': nutrition_table.c.protein,
        '_Nutrition__health_stars': nutrition_table.c.health_stars,
        '_Nutrition__recipe': relationship(Recipe, back_populates='_Recipe__nutrition', uselist=False)
    })

    # Recipe mapping
    #TODO: check if all recipe properties are mapped
    mapper_registry.map_imperatively(Recipe, recipes_table, properties={
        '_Recipe__id': recipes_table.c.id,
        '_Recipe__name': recipes_table.c.name,
        '_Recipe__description': recipes_table.c.description,
        '_Recipe__author': relationship(Author, back_populates='_Author__recipes'),
        '_Recipe__nutrition': relationship(Nutrition, back_populates='_Nutrition__recipe',uselist=False),
        '_Recipe__reviews': relationship(Review, back_populates='_Review__recipe'),
        '_Recipe__category': relationship(Category, back_populates='_Category__recipes'),
        '_Recipe__favourites': relationship(Favourite, back_populates='_Favourite__recipe'),
        '_Recipe__date': recipes_table.c.date,
        '_Recipe__rating': recipes_table.c.rating,
    })

    # RecipeImage mapping
    mapper_registry.map_imperatively(RecipeImage, recipe_images_table, properties={
        '_RecipeImage__id': recipe_images_table.c.id,
        '_RecipeImage__recipe_id': recipe_images_table.c.recipe_id,
        '_RecipeImage__url': recipe_images_table.c.url,
        '_RecipeImage__position': recipe_images_table.c.position,

    })

    #Favourite mapping
    mapper_registry.map_imperatively(Favourite, favourites_table, properties={
        '_Favourite__id': favourites_table.c.id,
        '_Favourite__user': relationship(User, back_populates='_User__favourite_recipes'),
        '_Favourite__recipe': relationship(Recipe, back_populates='_Recipe__favourites')

    })

    #User mapping
    mapper_registry.map_imperatively(User, users_table, properties={
        '_User__id': users_table.c.id,
        '_User__username': users_table.c.username,
        '_User__password': users_table.c.password,
        '_User__reviews': relationship(Review, back_populates='_Review__user'),
        '_User__favourite_recipes': relationship(Favourite, back_populates='_Favourite__user')
    })

    #Review mapping
    mapper_registry.map_imperatively(Review, reviews_table, properties={
        '_Review__id': reviews_table.c.id,
        '_Review__rating': reviews_table.c.rating,
        '_Review__comment': reviews_table.c.comment,
        '_Review__timestamp': reviews_table.c.timestamp,
        '_Review__user': relationship(User, back_populates='_User__reviews'),
        '_Review__recipe': relationship(Recipe, back_populates='_Recipe__reviews')
    })

    #Category mapping
    mapper_registry.map_imperatively(Category, categories_table, properties={
        '_Category__id': categories_table.c.id,
        '_Category__name': categories_table.c.name,
        '_Category__recipes': relationship(Recipe, back_populates='_Recipe__category')
    })

    # Recipe ingredient mapping
    mapper_registry.map_imperatively(RecipeIngredient, recipe_ingredients_table, properties={
        '_RecipeIngredient__id': recipe_ingredients_table.c.id,
        '_RecipeIngredient__recipe_id': recipe_ingredients_table.c.recipe_id,
        '_RecipeIngredient__quantity': recipe_ingredients_table.c.quantity,
        '_RecipeIngredient__ingredient': recipe_ingredients_table.c.ingredient,
        '_RecipeIngredient__position': recipe_ingredients_table.c.position,
    })

    # Recipe instruction mapping
    mapper_registry.map_imperatively(RecipeInstruction, recipe_instructions_table, properties={
        '_RecipeInstruction__id': recipe_instructions_table.c.id,
        '_RecipeInstruction__recipe_id': recipe_instructions_table.c.recipe_id,
        '_RecipeInstruction__step': recipe_instructions_table.c.step,
        '_RecipeInstruction__position': recipe_instructions_table.c.position,

    })