from flask import Blueprint, render_template, session, request
from recipe import Recipe
from recipe.adapters.filter import Filter
from recipe.authentication.authentication import login_required
from recipe.profile import services
from recipe.utilities.services import get_random_recipe, get_health_stars
from typing import List
import recipe.adapters.repository as repository

profile_bp = Blueprint('profile_bp', __name__)


@profile_bp.route('/profile')
@login_required
def profile():
    # Get requested page
    page: int = request.args.get('page', 1, type=int)
    reviews_page: int = request.args.get('reviews_page', 1, type=int)

    # Get current user and their favourite recipes
    user_name = session['user_name']
    current_user = services.get_user(user_name)

    favourite_recipes, total_pages = services.get_recipes(current_user, page, Filter())

    reviews, total_reviews_pages = repository.repo_instance.get_user_reviews(current_user, reviews_page, 20)
    print(reviews)

    # Get the health star ratings
    nutrition_info: List[float] = get_health_stars(favourite_recipes)

    return render_template(
        'profile/profile.html',
        page=page,
        total_pages=total_pages,
        recipes=favourite_recipes,
        random_recipe=get_random_recipe(),
        health_stars=nutrition_info,
        profile=True,
        reviews_page=reviews_page,
        reviews=reviews,
        total_reviews_pages=total_reviews_pages,
    )
