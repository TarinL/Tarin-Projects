import pytest

from recipe.adapters import memory_repository
from recipe.adapters.filter import Filter
from recipe.authentication import services as auth_services
from recipe.authentication.services import AuthenticationException
from recipe.recipes import services as recipe_services
from recipe.browse import services as browse_services
from tests.conftest import memory_repo


def test_add_user(memory_repo):
    new_user_name = 'abc123'
    new_password = 'abcd1A23'

    auth_services.add_user(new_user_name, new_password, memory_repo)
    user_as_dict = auth_services.get_user(new_user_name, memory_repo)
    assert user_as_dict['username'] == new_user_name


def test_authentication_with_valid_credentials(memory_repo):
    new_user_name = 'jackson'
    new_password = 'Jackson123'

    auth_services.add_user(new_user_name, new_password, memory_repo)

    try:
        auth_services.authenticate_user(new_user_name, new_password, memory_repo)
    except AuthenticationException:
        assert False


def test_authentication_with_invalid_credentials(memory_repo):
    new_user_name = 'jackson'
    new_password = 'jackson123'

    auth_services.add_user(new_user_name, new_password, memory_repo)

    with pytest.raises(auth_services.AuthenticationException):
        auth_services.authenticate_user(new_user_name, '0987654321', memory_repo)


def test_cannot_add_user_with_existing_name(memory_repo):
    user_name = 'tarinlove'
    password = 'aAtkfsa3'

    with pytest.raises(auth_services.NameAlreadyExistsException):
        auth_services.add_user(user_name, password, memory_repo)


def test_adding_review(memory_repo):
    recipe_id = 40
    comment_text = 'This is a good recipe'
    user_name = 'ellefleming'
    rating = 4.5

    recipe_services.add_review(recipe_id, comment_text, user_name, rating, memory_repo)
    assert recipe_services.get_reviews(40, memory_repo)[0].comment == comment_text
    assert recipe_services.get_reviews(40, memory_repo)[0].rating == rating


def test_review_on_non_exist_recipe(memory_repo):
    recipe_id = 0
    comment_text = "I like this recipe"
    user_name = 'tarinlove'
    rating = 4.5
    with pytest.raises(recipe_services.NonExistentRecipeException):
        recipe_services.add_review(recipe_id, comment_text, user_name, rating, memory_repo)


def test_unknown_user_review(memory_repo):
    recipe_id = 40
    comment_text = 'This recipe is not a good recipe'
    user_name = 'ksadnm1'
    rating = 4.5
    with pytest.raises(recipe_services.UnknownUserException):
        recipe_services.add_review(recipe_id, comment_text, user_name, rating, memory_repo)


# testing browse services
# test for sort_recipes

def test_sort_recipes_by_name(memory_repo):
    sorted_recipes = memory_repo.get_all_recipes(Filter(sort_method='name'))

    assert [r.name for r in sorted_recipes] == ["Best Lemonade", "Cabbage Soup", "Carina's Tofu-Vegetable Kebabs",
                                                "Low-Fat Berry Blue Frozen Dessert", "Warm Chicken A La King"]


# test recipe_filter

@pytest.mark.parametrize(('recipe_id', 'search', 'search_type'), (
        (38, "Low-Fat Berry Blue Frozen Dessert", "name"),
        (38, "Frozen Desserts", "category"),
        (38, "Dancer", "author"),
))
def test_recipe_filter(memory_repo, recipe_id: int, search: str, search_type: str):
    recipe = memory_repo.get_recipe_by_id(recipe_id)
    search_filter = Filter(search=search, search_type=search_type, rating_range=(0.0, 4.0), nutrition_range=(1.0, 4.0))

    result = memory_repository._recipe_filter(recipe, search_filter)

    assert result is True
