from datetime import datetime
from recipe.domainmodel.author import Author
from recipe.domainmodel.category import Category
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User
import pytest


# Fixtures
@pytest.fixture
def my_user():
    return User("test user", "password123", 1)


@pytest.fixture
def my_author():
    return Author(1, "Gordon Ramsay")


@pytest.fixture
def my_category():
    return Category("Italian", [], 1)


@pytest.fixture
def my_recipe(my_author, my_category):
    return Recipe(
        recipe_id=1,
        name="Spaghetti Carbonara",
        author=my_author,
        cook_time=20,
        preparation_time=15,
        created_date=datetime(2024, 1, 1),
        description="Classic Italian pasta dish",
        images=["image1.jpg"],
        category=my_category,
        ingredient_quantities=["200g pasta", "100g bacon"],
        ingredients=["pasta", "bacon", "eggs", "cheese"],
        rating=4.5,
        nutrition=None,
        servings="4",
        recipe_yield="4 portions",
        instructions=["Boil pasta", "Cook bacon", "Mix with eggs"]
    )


# User tests
def test_user_construction():
    user = User("john_doe", "secret123", 1)
    assert user.id == 1
    assert user.username == "john_doe"
    assert user.password == "secret123"
    assert user.favourite_recipes == []
    assert user.reviews == []


def test_user_construction_without_id():
    user = User("jane_doe", "password456")
    assert user.id is None
    assert user.username == "jane_doe"


def test_user_equality():
    user1 = User("test", "pass", 1)
    user2 = User("test", "pass", 1)
    user3 = User("test", "pass", 2)
    assert user1 == user2
    assert user1 != user3


def test_user_less_than():
    user1 = User("test", "pass", 1)
    user2 = User("test", "pass", 2)
    assert user1 < user2


def test_user_hash():
    user1 = User("test", "pass", 1)
    user2 = User("test", "pass", 1)
    user_set = {user1, user2}
    assert len(user_set) == 1


# Author tests
def test_author_construction():
    author = Author(1, "Jamie Oliver")
    assert author.id == 1
    assert author.name == "Jamie Oliver"
    assert author.recipes == []


def test_author_equality():
    author1 = Author(1, "Chef A")
    author2 = Author(1, "Chef B")
    author3 = Author(2, "Chef A")
    assert author1 == author2
    assert author1 != author3


def test_author_less_than():
    author1 = Author(1, "Chef A")
    author2 = Author(2, "Chef B")
    assert author1 < author2


def test_author_hash():
    author1 = Author(1, "Chef A")
    author2 = Author(1, "Chef B")
    author_set = {author1, author2}
    assert len(author_set) == 1


def test_author_add_recipe(my_author, my_recipe):
    my_author.remove_recipes()
    assert my_author.recipes == []
    my_author.add_recipe(my_recipe)
    assert my_recipe in my_author.recipes


def test_author_add_duplicate_recipe(my_author, my_recipe):
    my_author.remove_recipes()
    assert my_author.recipes == []
    my_author.add_recipe(my_recipe)
    with pytest.raises(ValueError):
        my_author.add_recipe(my_recipe)


# Category tests
def test_category_construction():
    category = Category("Desserts", [], 1)
    assert category.id == 1
    assert category.name == "Desserts"
    assert category.recipes == []


def test_category_construction_without_id():
    category = Category("Main Course")
    assert category.id is None
    assert category.name == "Main Course"


def test_category_equality():
    category1 = Category("Italian", [], 1)
    category2 = Category("French", [], 1)
    category3 = Category("Italian", [], 2)
    assert category1 == category2
    assert category1 != category3


def test_category_less_than():
    category1 = Category("A", [], 1)
    category2 = Category("B", [], 2)
    assert category1 < category2


def test_category_hash():
    category1 = Category("Italian", [], 1)
    category2 = Category("French", [], 1)
    category_set = {category1, category2}
    assert len(category_set) == 1


def test_category_add_recipe(my_category, my_recipe):
    my_category.add_recipe(my_recipe)
    assert my_recipe in my_category.recipes


def test_category_add_invalid_recipe(my_category):
    with pytest.raises(TypeError):
        my_category.add_recipe("not a recipe")


# Recipe tests
def test_recipe_construction(my_author, my_category):
    recipe = Recipe(
        recipe_id=1,
        name="Test Recipe",
        author=my_author,
        cook_time=30,
        preparation_time=15,
        created_date=datetime(2024, 1, 1),
        description="Test description",
        images=["test.jpg"],
        category=my_category,
        ingredient_quantities=["1 cup flour"],
        ingredients=["flour"],
        rating=4.0,
        nutrition=None,
        servings="2",
        recipe_yield="2 portions",
        instructions=["Mix ingredients"]
    )
    assert recipe.id == 1
    assert recipe.name == "Test Recipe"
    assert recipe.author == my_author


def test_recipe_equality():
    author = Author(1, "Chef")

    recipe1 = Recipe(1, "Recipe A", author)
    recipe2 = Recipe(1, "Recipe B", author)
    recipe3 = Recipe(2, "Recipe A", author)

    assert recipe1 == recipe2
    assert recipe1 != recipe3


def test_recipe_less_than():
    author = Author(1, "Chef")

    recipe1 = Recipe(1, "Recipe A", author)
    recipe2 = Recipe(2, "Recipe B", author)

    assert recipe1 < recipe2


def test_recipe_hash():
    author = Author(1, "Chef")

    recipe1 = Recipe(1, "Recipe A", author)
    recipe2 = Recipe(1, "Recipe B", author)

    recipe_set = {recipe1, recipe2}
    assert len(recipe_set) == 1


def test_author_set_recipe(my_author):
    new_recipe = Recipe(200, "New Recipe", my_author)

    my_author.remove_recipes()
    assert my_author.recipes == []
    my_author.add_recipe(new_recipe)
    assert new_recipe in my_author.recipes


def test_author_set_recipe_invalid_type(my_author):
    with pytest.raises(TypeError):
        my_author.add_recipe("not a recipe")


@pytest.fixture
def my_review(my_user, my_recipe):
    return Review(
        user=my_user,
        recipe=my_recipe,
        rating=4,
        comment="Test comment",
        timestamp=datetime(2024, 1, 1),
    )


def test_review_construction(my_user, my_recipe):
    review = Review(
        rev_id=1,
        user=my_user,
        recipe=my_recipe,
        rating=5,
        comment="Test comment",
        timestamp=datetime(2024, 2, 1),
    )
    assert review.id == 1
    assert review.user == my_user
    assert review.recipe == my_recipe
    assert review.comment == "Test comment"


def test_rating_setter(my_review):
    with pytest.raises(ValueError, match="rating must be between 0 and 5"):
        my_review.rating = 6


def test_comment_setter(my_review):
    my_review.comment = "new comment"
    assert my_review.comment == "new comment"


def test_review_equality(my_user, my_recipe):
    r1 = Review(my_user, my_recipe, 5, "Nice")
    r2 = Review(my_user, my_recipe, 3, "Not bad")
    # Different ids, so not equal
    assert r1 != r2
    # Force same id for testing equality
    r2._Review__id = r1.id
    assert r1 == r2


def test_review_not_equal_to_other_type(my_review):
    assert my_review != "not a review"


###Test favorite
@pytest.fixture
def my_favorite(my_user, my_recipe):
    return Favourite(my_user, my_recipe)


def test_favorite_construction(my_user, my_recipe):
    favorite = Favourite(my_user, my_recipe)
    assert favorite.user == my_user
    assert favorite.recipe == my_recipe


def test_favorite_recipe_setter(my_user, my_recipe, my_author):
    favorite = Favourite(my_user, my_recipe)
    recipe1 = Recipe(1, "Recipe A", my_author)
    favorite.recipe = recipe1
    assert favorite.recipe.name == "Recipe A"
    assert favorite.recipe.author == my_author
    assert favorite.recipe.id == 1


####Test nutrition

@pytest.fixture
def my_nutrition(my_recipe):
    return Nutrition(
        recipe_id=my_recipe.id,
        calories=200,
        fat_content=10,
        saturated_fat_content=3,
        cholesterol_content=30,
        sodium_content=150,
        carbohydrates_content=40,
        sugars_content=5,
        proteins_content=8,
        fiber_content=2
    )


def test_nutrition_construction_with_recipe(my_recipe):
    nutrition = Nutrition(
        recipe_id=my_recipe.id,
        calories=100,
        fat_content=5,
        saturated_fat_content=2,
        cholesterol_content=10,
        sodium_content=50,
        carbohydrates_content=20,
        sugars_content=3,
        proteins_content=6,
        fiber_content=1
    )
    assert nutrition.recipe_id == my_recipe.id
    assert nutrition.calories == 100
    assert nutrition.fat_content == 5
    assert nutrition.saturated_fat_content == 2
    assert nutrition.cholesterol_content == 10
    assert nutrition.sodium_content == 50
    assert nutrition.carbohydrates_content == 20
    assert nutrition.sugars_content == 3
    assert nutrition.proteins_content == 6
    assert nutrition.fiber_content == 1


def test_nutrition_construction_without_recipe():
    nutrition = Nutrition(
        recipe_id=0,
        calories=50,
        fat_content=1,
        saturated_fat_content=0,
        cholesterol_content=0,
        sodium_content=10,
        carbohydrates_content=12,
        sugars_content=1,
        proteins_content=2,
        fiber_content=0
    )
    assert nutrition.recipe_id is 0
    assert nutrition.calories == 50


def test_nutrition_property_setters(my_nutrition):
    my_nutrition.calories = 250
    my_nutrition.fat_content = 12
    my_nutrition.saturated_fat_content = 4
    my_nutrition.cholesterol_content = 35
    my_nutrition.sodium_content = 160
    my_nutrition.carbohydrates_content = 45
    my_nutrition.sugars_content = 6
    my_nutrition.proteins_content = 9
    my_nutrition.fiber_content = 3
    assert my_nutrition.calories == 250
    assert my_nutrition.fat_content == 12
    assert my_nutrition.saturated_fat_content == 4
    assert my_nutrition.cholesterol_content == 35
    assert my_nutrition.sodium_content == 160
    assert my_nutrition.carbohydrates_content == 45
    assert my_nutrition.sugars_content == 6
    assert my_nutrition.proteins_content == 9
    assert my_nutrition.fiber_content == 3


def test_nutrition_equality_and_hash(my_recipe):
    nutrition1 = Nutrition(my_recipe.id, 100, 5, 2, 10, 50, 20, 3, 6, 1)
    nutrition2 = Nutrition(my_recipe.id, 200, 6, 3, 12, 55, 25, 4, 7, 2)
    # same recipe id hash values are equal
    assert nutrition1 == nutrition2
    assert hash(nutrition1) == hash(nutrition2)


def test_nutrition_equality_invalid_type(my_nutrition):
    assert my_nutrition != "not a nutrition object"


def test_nutrition_less_than_comparison(my_recipe):
    n1 = Nutrition(my_recipe.id, 100, 5, 2, 10, 50, 20, 3, 6, 1)
    n2 = Nutrition(my_recipe.id, 200, 5, 2, 10, 50, 20, 3, 6, 1)
    assert n1 < n2


def test_nutrition_less_than_invalid_type(my_nutrition):
    with pytest.raises(TypeError):
        _ = my_nutrition < "not a nutrition object"


def test_nutrition_repr(my_nutrition):
    result = repr(my_nutrition)
    assert f"Calories={my_nutrition.calories}" in result
    assert f"Protein={my_nutrition.proteins_content}" in result
