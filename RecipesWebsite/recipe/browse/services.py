from recipe import Recipe
from recipe.adapters import repository
from recipe.adapters.filter import Filter
from typing import List


def get_recipes(page: int, search_filter: Filter) -> tuple[List[Recipe], int]:
    """ Gets sorted and filtered list of recipes """

    page_size: int = 10
    return repository.repo_instance.get_recipe_page(
        page=page,
        page_size=page_size,
        search_filter=search_filter
    )


def get_browse_text(search: str, search_type: str):
    """
    Makes the browse text to be shown on the browse page.
    Dependent on whether items were sorted or not
    """

    browse_text = "Browse All Recipes"

    # If there is a search term and stuff was filtered
    if search:
        browse_text = f'Showing Results for "{search}" '

        if search_type == 'category':
            browse_text += "in Categories"
        elif search_type == 'author':
            browse_text += "in Authors"

    return browse_text
