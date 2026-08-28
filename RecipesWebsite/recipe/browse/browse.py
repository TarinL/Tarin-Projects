from __future__ import annotations

import recipe
from flask import Blueprint, render_template, request
from recipe.adapters.filter import Filter
from recipe.utilities.services import get_random_recipe, get_health_stars
from typing import List
import recipe.browse.services as services

browse_bp = Blueprint('browse_bp', __name__)


@browse_bp.route('/browse', methods=['GET'])
def browse():
    """
    Blueprint for the browse page that shows pages based off the query
    value.
    """

    # Get requested page number
    page: int = request.args.get('page', 1, type=int)

    # Get search parameters
    search: str = request.args.get('search', '').strip().lower()
    search: str = search if search else None
    search_type: str = request.args.get('search_type', 'name').strip().lower()

    # Get rating range
    min_rating: float = request.args.get('min_rating', 0.0, type=float)
    max_rating: float = request.args.get('max_rating', 5.0, type=float)
    rating_range = (min_rating, max_rating)

    # Get nutrition value range
    min_nutrition: float = request.args.get('min_nutrition', 0.0, type=float)
    max_nutrition: float = request.args.get('max_nutrition', 5.0, type=float)
    nutrition_range = (min_nutrition, max_nutrition)

    try:
        search_filter = Filter(
            sort_method='name',
            search=search,
            search_type=search_type,
            rating_range=rating_range,
            nutrition_range=nutrition_range
        )
    except ValueError as error:
        search_filter = Filter()
        print(f"ERROR: Invalid Filter: '{error}'")

    # Get all recipes, sort and filter them
    recipes, total_pages = services.get_recipes(page, search_filter)
    health_stars: List[float] = get_health_stars(recipes)

    # Get the splash header of the browse page
    browse_text = services.get_browse_text(search, search_type)

    return render_template(
        'browse/browse.html',
        # Page information
        page=page,
        total_pages=total_pages,
        # Recipes information to display
        recipes=recipes,
        health_stars=health_stars,
        # Misc page items
        random_recipe=get_random_recipe(),
        browse_text=browse_text,
        # Search data
        search=search if search else '',
        search_type=search_type,
        rating_range=rating_range,
        nutrition_range=nutrition_range,
    )
