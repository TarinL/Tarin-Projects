from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from recipe import Author
from recipe.adapters.orm import users_table
from recipe.domainmodel.category import Category
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction
from recipe.domainmodel.user import User
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.review import Review
from tests.tests_db.conftest import empty_session

@pytest.fixture
def new_author():
    return Author(20, 'test author')
@pytest.fixture
def new_nutrition():
    return Nutrition(100, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
@pytest.fixture
def new_recipe(new_author, new_nutrition):
    return Recipe(
        recipe_id = 100,
        name = 'new recipe',
        author = new_author,
        nutrition = new_nutrition,
        category = Category("new category"),
        cook_time = 1,
        preparation_time = 1,
        created_date=datetime.now(),
        description = 'new description'
    )

def insert_users(empty_session, values):
    for value in values:
        empty_session.execute(text(f'INSERT INTO users (id, username, password) VALUES ({value[0]}, "{value[1]}", "{value[2]}")'))
    rows = list(empty_session.execute(text("SELECT id from users")))
    keys = tuple(row[0] for row in rows)
    return keys

def insert_recipe(empty_session):
    empty_session.execute(text(
        "INSERT INTO recipes (id, name, author_id, description, nutrition_id, category_id, date, rating) VALUES"
        " (1, 'Test recipe', 1, 'this is a test recipe', 1, 1, '2025-10-18T01:12:50.385882', 0)"
    ))
    row = empty_session.execute(text("SELECT id from recipes")).fetchone()
    return row[0]

def insert_authors(empty_session, value):
    empty_session.execute(
        "INSERT INTO authors (name) VALUES (:name)",
        {"name": value}
    )

def make_user():
    user = User("tarinlove", "1234", user_id=1)
    return user

# tests for orm
# user tests
def test_loading_users(empty_session):
    users = [(1, "tarinlove", "1234"), (2, "jacksondau", "5678")]
    insert_users(empty_session, users)
    got = empty_session.query(User).order_by(users_table.c.id).all()
    assert [(u.id, u.username, u.password) for u in got] == sorted(users)

def test_saving_users(empty_session):
    user = make_user()
    empty_session.add(user)
    empty_session.commit()
    rows = list(empty_session.execute(text("SELECT username, password FROM users")))
    assert rows == [("tarinlove", "1234")]

def test_saving_user_with_common_user_name(empty_session):
    user = make_user()
    empty_session.add(user)
    empty_session.commit()
    with pytest.raises(IntegrityError):
        dup = User("tarinlove", "5678", user_id=1)
        empty_session.add(dup)
        empty_session.commit()

# recipe tests
def test_loading_recipe(empty_session):
    recipe_key = insert_recipe(empty_session)
    fetched = empty_session.query(Recipe).one()
    assert fetched.id == recipe_key
    assert fetched.name == "Test recipe"
    assert fetched.author_id == 1
    assert fetched.description == "this is a test recipe"
    assert fetched.nutrition_id == 1

def test_for_saving_recipe(empty_session, new_recipe):
    recipe = new_recipe
    empty_session.add(recipe)
    empty_session.commit()

    row = empty_session.execute(
        text("SELECT * FROM recipes")).fetchone()

    assert row[0] == 100
    assert row[1] == "new recipe"
    assert row[3] == "new description"

# author tests
def test_for_loading_author(empty_session, new_author):
    author = new_author
    empty_session.execute(text(f"INSERT INTO authors (name) VALUES ('{author.name}')"))
    empty_session.commit()
    row = empty_session.query(Author).one()
    assert row.name == author.name


def test_for_saving_author(empty_session):
    author = Author(author_id=1, name="tarinlove")
    empty_session.add(author)
    empty_session.commit()
    row = empty_session.execute(text("SELECT id, name FROM authors")).one()
    assert row[1] == "tarinlove"
    assert isinstance(row[0], int) and row[0] > 0

# nutrition tests
def test_for_loading_nutrition(empty_session):
    empty_session.execute(text(
        "INSERT INTO nutrition (calories, fat, saturated_fat, cholesterol, sodium, "
        "carbohydrates, fiber, sugar, protein) "
        "VALUES (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0)"
    ))
    empty_session.commit()
    row: Nutrition = empty_session.query(Nutrition).one()
    values = [
        row.calories, row.fat_content, row.saturated_fat_content, row.cholesterol_content,
        row.sodium_content, row.carbohydrates_content, row.fiber_content, row.sugars_content, row.proteins_content
    ]
    assert values == [1.0] * 9

def test_for_saving_nutrition(empty_session):
    nutrition = Nutrition(
        recipe_id=1, calories=1.0, fat_content=1.0, saturated_fat_content=1.0, cholesterol_content=1.0,
        sodium_content=1.0, carbohydrates_content=1.0, fiber_content=1.0, sugars_content=1.0, proteins_content=1.0
    )
    empty_session.add(nutrition)
    empty_session.commit()
    row = empty_session.execute(
        text("SELECT calories, fat, saturated_fat, cholesterol, sodium, "
             "carbohydrates, fiber, sugar, protein FROM nutrition")
    ).fetchone()
    assert list(row) == [1.0] * 9

# recipe_image tests
def test_for_loading_recipe_images(empty_session):
    empty_session.execute(text(
        "INSERT INTO recipe_images (recipe_id, url, position) VALUES (1, 'www.testurl.com', 0)"
    ))
    empty_session.commit()
    row = empty_session.execute(text("SELECT id, url, position FROM recipe_images WHERE recipe_id = 1")).fetchone()
    assert row[0] == 1
    assert row[1] == "www.testurl.com"
    assert row[2] == 0

def test_for_saving_recipe_images(empty_session):
    recipe = RecipeImage(
        recipe_id=1,
        url="www.testurl.com",
        position=0
    )
    empty_session.add(recipe)
    empty_session.commit()

    row = empty_session.query(RecipeImage).one()
    recipe_image = row
    assert recipe_image.recipe_id == 1
    assert recipe_image.url == "www.testurl.com"
    assert recipe_image.position == 0

# category
def test_for_loading_category(empty_session):
    empty_session.execute(text(
        "INSERT INTO categories (name, id) VALUES ('Chowders', 1)"
    ))
    empty_session.commit()

    category = empty_session.query(Category).one()
    assert category.name == 'Chowders'
    assert category.id == 1

def test_for_saving_category(empty_session):
    category = Category(name="Chowders", category_id=1)
    empty_session.add(category)
    empty_session.commit()

    row = empty_session.execute(text(
        "SELECT * FROM categories WHERE name = 'Chowders'"
    )).fetchone()
    assert row[1] == 'Chowders'
    assert row[0] == 1

# favourite
def test_for_loading_favourites(empty_session):
    empty_session.execute(text(
        "INSERT INTO favourites (user_id, recipe_id) VALUES (1, 0)"
    ))
    empty_session.commit()

    favourite = empty_session.query(Favourite).one()
    assert favourite.user_id == 1
    assert favourite.recipe_id == 0

def test_for_saving_favourites(empty_session, new_recipe):
    favourite = Favourite(
        user=User(
            username='tarinlove',
            password='<PASSWORD>',
            user_id=1
        ),
        recipe=new_recipe
    )
    # not sure how the favourites table will be made but assume that it is using foreign keys for recipe_id and user_id
    empty_session.add(favourite)
    empty_session.commit()

    row = empty_session.execute(text(
        "SELECT * FROM favourites"
    )).fetchone()
    assert row[0] == 4 # user_id
    assert row[1] == 100 # recip_id

# instructions
def test_for_loading_instructions(empty_session):
    empty_session.execute(text(
        "INSERT INTO recipe_instructions (id, recipe_id, step, position) VALUES (1, 1, 'test recipe', 0)"
    ))
    empty_session.commit()

    instructions = empty_session.query(RecipeInstruction).one()
    assert instructions.recipe_id == 1
    assert instructions.step == 'test recipe'
    assert instructions.position == 0

def test_for_saving_instructions(empty_session):
    instructions = RecipeInstruction(
        recipe_id=1,
        step='test recipe',
        position=0
    )
    empty_session.add(instructions)
    empty_session.commit()

    instructions = empty_session.query(RecipeInstruction).one()
    assert instructions.step == 'test recipe'
    assert instructions.position == 0
    assert instructions.recipe_id == 1

# ingredients
def test_for_loading_ingredients(empty_session):
    empty_session.execute(text(
        "INSERT INTO recipe_ingredients (id, recipe_id, quantity, ingredient, position) VALUES (1, 1, '1 cup', 'flour', 5)"
    ))
    empty_session.commit()

    ingredient = empty_session.query(RecipeIngredient).one()
    assert ingredient.recipe_id == 1
    assert ingredient.quantity == '1 cup'
    assert ingredient.ingredient == 'flour'
    assert ingredient.position == 5

def test_for_saving_ingredients(empty_session):
    ingredient = RecipeIngredient(
        recipe_id=1,
        quantity='1 cup',
        ingredient='flour',
        position=0
    )

    empty_session.add(ingredient)
    empty_session.commit()

    row = empty_session.execute(text(
        "SELECT * FROM recipe_ingredients"
    )).fetchone()
    assert row[0] == 1
    assert row[1] == 1
    assert row[2] == '1 cup'
    assert row[3] == 'flour'
    assert row[4] == 0

# reviews
def test_for_loading_reviews(empty_session):
    empty_session.execute(text(
        "INSERT INTO reviews (id, recipe_id, user_id, rating, comment, timestamp) VALUES (1, 1, 2, 4.0, 'this is a test comment', '2025-10-18T01:12:50.385882')"
    ))
    empty_session.commit()

    review = empty_session.query(Review).one()
    assert review.rating == 4.0
    assert review.comment == 'this is a test comment'

def test_for_saving_reviews(empty_session, new_recipe):
    review = Review(
        user=User(
            username='tarinlove',
            password='<PASSWORD>',
        ),
        recipe=new_recipe,
        rating=4.0,
        comment='this is a test comment'
    )
    empty_session.add(review)
    empty_session.commit()

    row = empty_session.execute(text(
        "SELECT * FROM reviews"
    )).fetchone()

    assert row[0] == 3
    assert row[1] == 100
    assert row[2] == 1
    assert row[3] == 4.0
    assert row[4] == 'this is a test comment'

