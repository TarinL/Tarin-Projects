from datetime import date, datetime
import pytest
import recipe.adapters.repository as repo
from recipe import Author
from recipe.adapters.filter import Filter
from recipe.domainmodel.category import Category
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.recipe import Recipe

from recipe.adapters.database_repository import SqlAlchemyRepository
from recipe.domainmodel.recipe_image import RecipeImage
from recipe.domainmodel.recipe_ingredient import RecipeIngredient
from recipe.domainmodel.recipe_instruction import RecipeInstruction
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User

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

# user
def test_repository_can_add_a_user(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    user = User('jamesbond', 'shakennotstirred')
    repo.add_user(user)

    user2 = repo.get_user('jamesbond')

    assert user2 == user and user2 is user

def test_repository_can_retrieve_a_user(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    user = repo.get_user('tarinlove')
    assert user == User('tarinlove', 'T@#0000021', user_id=1)

def test_repository_deos_not_retrieve_a_non_existing_user(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    user = repo.get_user('johndoe')
    assert user is None

# recipes
def test_repository_can_retrieve_all_recipes(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    number_of_recipes = repo.get_all_recipes(Filter())
    assert len(number_of_recipes) == 5

def test_repository_can_add_recipe(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)

    repo.add_recipe(new_recipe)

    assert repo.get_recipe_by_id(100) == new_recipe

def test_repository_can_retrieve_a_recipe(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe = repo.get_recipe_by_id(40)

    assert recipe.name == 'Best Lemonade'
    assert recipe.author.name == 'Stephen Little'

# author
def test_repository_can_add_author(session_factory, new_author):
    repo = SqlAlchemyRepository(session_factory)
    author = new_author
    repo.add_author(author)

    returned_author = repo.get_author_by_id(20)

    assert returned_author.id == 20
    assert returned_author.name == 'test author'

def test_repository_can_retrieve_all_authors(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    all_authors = repo.get_authors()
    assert len(all_authors) == 5
    assert all_authors[0].name == 'Dancer'

def test_repository_can_retrieve_author_by_id(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    author = repo.get_author_by_id(1533)
    assert author.id == 1533
    assert author.name == 'Dancer'

def test_repository_can_retrieve_number_of_authors(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    number_of_authors = repo.get_number_of_authors()
    assert number_of_authors == 5

def test_repository_can_add_multiple_authors(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    list_of_authors = [
        Author(name='test 1', author_id=10),
        Author(name='test 2', author_id=11)
    ]
    repo.add_authors(list_of_authors)
    number_of_authors = repo.get_number_of_authors()
    assert number_of_authors == 7

# category
    # repo can retrieve and add a category
def test_repository_can_add_category(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    category = Category(name='test category')
    repo.add_category(category)

    returned_category = repo.get_category_by_name(category.name)
    assert returned_category.name == 'test category'

def test_repository_can_get_all_categories(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    categories_list = repo.get_categories()
    number_of_categories = len(categories_list)
    assert number_of_categories == 5

def test_repository_can_get_category_by_name(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    category = repo.get_category_by_name('Frozen Desserts')
    assert category.name == 'Frozen Desserts'

def test_repository_does_not_retrieve_non_existing_category(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    category = repo.get_category_by_name('Unknown Category')
    assert category is None

def test_repository_can_get_number_of_categories(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    number_of_categories = repo.get_number_of_categories()
    assert number_of_categories == 5

def test_repository_can_get_recipes_in_category(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    recipes_list = repo.get_recipes_in_category('Frozen Desserts')
    number_of_categories = len(recipes_list)
    assert number_of_categories == 1
    assert recipes_list[0].name == "Low-Fat Berry Blue Frozen Dessert"

def test_repository_can_add_multiple_categories(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    list_categories = [Category(name='Category 1'), Category(name='Category 2')]
    repo.add_categories(list_categories)
    number_of_categories = repo.get_number_of_categories()
    assert number_of_categories == 7
    assert list_categories[-1].name == 'Category 2'


# reviews
def test_repository_can_add_review(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)
    review = Review(
        user=User(username='tarinlove', password='1234'),
        recipe=new_recipe,
        rating=1.0,
        comment='new comment'
        )
    repo.add_review(review)

    reviews = repo.get_reviews(1, 10)
    assert reviews[-1].comment == 'new comment'

def test_repository_can_get_all_reviews(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    reviews_list = repo.get_all_reviews()
    number_of_reviews = len(reviews_list)
    assert number_of_reviews == 0

def test_repository_can_get_review_by_id(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)
    review = Review(
        user=User(username='tarinlove', password='1234'),
        recipe=new_recipe,
        rating=1.0,
        comment='new comment'
    )
    repo.add_review(review)
    assert review.id == 2
    review = repo.get_review_by_id(2)

    assert review.id == 2
    assert review.rating == 1.0

# favourite
def test_repository_can_add_favourite_recipe(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)
    user = User(username='tarinlove', password='<PASSWORD>')
    favourite = Favourite(user, new_recipe)
    repo.add_favourite_recipe(user, favourite)
    fetched_favourite, _ = repo.get_favourite_page(user, 1, 1, Filter())
    assert fetched_favourite[0].id == 100
    assert fetched_favourite[0].name == 'new recipe'

def test_repository_can_delete_favourite_recipe(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)
    user = User(username='tarinlove', password='<PASSWORD>')
    favourite = Favourite(user, new_recipe)
    repo.add_favourite_recipe(user, favourite)

    repo.remove_favourite_recipe(user, new_recipe)
    favourites, _ = repo.get_favourite_page(user, 1, 1, Filter())
    assert len(favourites) == 0

def test_repository_can_get_favourite_recipes(session_factory, new_recipe):
    repo = SqlAlchemyRepository(session_factory)
    user = User(username='tarinlove', password='<PASSWORD>')
    favourite = Favourite(user, new_recipe)
    repo.add_favourite_recipe(user, favourite)
    _, favourites = repo.get_favourite_page(user, 1, 1, Filter())
    assert favourites == 1

# nutrition
def test_repository_can_add_nutrition(session_factory, new_nutrition):
    repo = SqlAlchemyRepository(session_factory)

    repo.add_nutrition(new_nutrition)

    fetched_nutrition = repo.get_nutrition_by_id(100)
    assert fetched_nutrition.recipe_id == 100
    assert fetched_nutrition.calories == 1.5;

def test_repository_can_get_nutrition_by_id(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    nutrition = repo.get_nutrition_by_id(38)
    assert nutrition.recipe_id == 38


# recipe_image
def test_repository_can_add_recipe_image(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe_image = RecipeImage(
        recipe_id=10,
        url="testurl",
        position=1
    )
    repo.add_recipe_image(recipe_image)

    fetched_recipe_image = repo.get_recipe_images(10)
    assert fetched_recipe_image[0].recipe_id == 10

def test_repository_can_add_multiple_recipe_images(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe_images = [
        RecipeImage(
        recipe_id=10,
        url="testurl",
        position=1
        ),
        RecipeImage(
            recipe_id=11,
            url="testurl",
            position=1
        )]

    repo.add_multiple_recipe_images(recipe_images)
    fetched_images1 = repo.get_recipe_images(10)
    fetched_images2 = repo.get_recipe_images(11)
    assert fetched_images1[-1].recipe_id == 10
    assert fetched_images2[-1].recipe_id == 11

def test_repository_can_get_recipe_images(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe_images_list = repo.get_recipe_images(10)
    assert len(recipe_images_list) == 0

# ingredients
def test_repository_can_add_recipe_ingredient(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    recipe_ingredient = RecipeIngredient(
        recipe_id=10,
        quantity='1',
        ingredient='test',
        position=1
    )

    repo.add_recipe_ingredient(recipe_ingredient)
    fetched_recipe_ingredient = repo.get_recipe_ingredients(10)
    assert fetched_recipe_ingredient[-1].recipe_id == 10

def test_repository_can_get_recipe_ingredients(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    recipe_ingredients_list = repo.get_recipe_ingredients(1)
    assert len(recipe_ingredients_list) == 0

def test_repository_can_add_multiple_recipie_ingredients(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe_ingredients_list = [RecipeIngredient(
        recipe_id=10,
        quantity='1',
        ingredient='test1',
        position=1
    ),
    RecipeIngredient(
        recipe_id=10,
        quantity='1',
        ingredient='test2',
        position=2
    )]

    repo.add_multiple_recipe_ingredients(recipe_ingredients_list)
    fetched_recipe_ingredients = repo.get_recipe_ingredients(10)
    assert fetched_recipe_ingredients[0].ingredient == 'test1'
    assert fetched_recipe_ingredients[1].ingredient == 'test2'

# instructions
def test_repository_can_add_recipe_instruction(session_factory):
    repo = SqlAlchemyRepository(session_factory)

    recipe_instruction = RecipeInstruction(recipe_id=10, step='test step', position=1)
    repo.add_recipe_instruction(recipe_instruction)
    fetched_recipe_instruction = repo.get_recipe_instructions(10)
    assert fetched_recipe_instruction[0].step == 'test step'

def test_repository_can_add_multiple_recipe_instructions(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    recipe_instructions_list = [RecipeInstruction(recipe_id=10, step='test step 1', position=1),
                                RecipeInstruction(recipe_id=10, step='test step 2', position=2)]
    repo.add_multiple_recipe_instructions(recipe_instructions_list)
    fetched_recipe_instructions = repo.get_recipe_instructions(10)
    assert fetched_recipe_instructions[0].step == 'test step 1'
    assert fetched_recipe_instructions[1].step == 'test step 2'

def test_repository_can_get_recipe_instructions(session_factory):
    repo = SqlAlchemyRepository(session_factory)
    recipe_instructions_list = repo.get_recipe_instructions(38)
    assert len(recipe_instructions_list) == 9



    