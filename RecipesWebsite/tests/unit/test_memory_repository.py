from recipe.domainmodel.recipe import Recipe
from recipe.domainmodel.author import Author
from recipe.domainmodel.category import Category
from recipe.domainmodel.nutrition import Nutrition
from recipe.domainmodel.review import Review
from recipe.domainmodel.user import User
from tests.conftest import memory_repo

def test_repository_can_add_a_user(memory_repo):
    user = User('dave', '123456789')
    memory_repo.add_user(user)

    assert isinstance(memory_repo.get_user('dave'), User)


def test_repository_can_retrieve_a_user(memory_repo):
    user = memory_repo.get_user('tarinlove')
    assert user == User('tarinlove', 'T@#0000021', user_id=1)


def test_repository_does_not_retrieve_a_non_existent_user(memory_repo):
    user = memory_repo.get_user('elisa')
    assert user is None


def test_repository_can_add_a_recipe(memory_repo):
    recipe = Recipe(1, "Chicken Teriyaki")
    memory_repo.add_recipe(recipe)
    assert isinstance(memory_repo.get_recipe_by_id(1), Recipe)


def test_repository_can_retrieve_a_recipe(memory_repo):
    recipe = memory_repo.get_recipe_by_id(38)
    assert recipe.name == "Low-Fat Berry Blue Frozen Dessert"


def test_repository_can_add_a_nutrition(memory_repo):
    recipe = Recipe(1, "Chicken Teriyaki")
    nutrition = Nutrition(recipe.id, 100, 100, 100, 100, 100, 100, 100, 100, 100)
    memory_repo.add_nutrition(nutrition)
    assert memory_repo.get_nutrition_by_id(1) is nutrition
    assert memory_repo.get_nutrition_by_id(1).fat_content == 100


def test_repository_can_add_category(memory_repo):
    category = Category("Lunch")
    memory_repo.add_category(category)
    assert isinstance(memory_repo.get_category_by_name("Lunch"), Category)


def test_repository_can_add_author(memory_repo):
    author = Author(1, "jackson")
    memory_repo.add_author(author)
    assert memory_repo.get_author_by_id(1).name == "jackson"


def test_repository_can_add_review(memory_repo):
    user = User("dave", "123456789")
    recipe = Recipe(1, "Chicken Teriyaki")
    rating = 4.2
    comment = "It's okay"
    review = Review(user, recipe, rating, comment)
    memory_repo.add_recipe(recipe)
    memory_repo.add_review(review)
    assert isinstance(memory_repo.get_all_reviews()[0], Review)
