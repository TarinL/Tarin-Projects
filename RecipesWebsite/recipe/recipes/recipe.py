from flask import Blueprint, render_template, request, session, url_for, redirect
from recipe import Recipe
from recipe.authentication.authentication import login_required
from recipe.domainmodel.favourite import Favourite
from recipe.domainmodel.user import User
from recipe.recipes import services
from recipe.utilities.services import get_random_recipe
from typing import Optional
import recipe.adapters.repository as repository

recipe_bp = Blueprint('recipe_bp', __name__)


@recipe_bp.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe(recipe_id: int):
    # Get the current recipe
    curr_recipe: Optional[Recipe] = repository.repo_instance.get_recipe_by_id(recipe_id)

    # Get nutrition info for each recipe
    nutrition_info = curr_recipe.nutrition.health_star_rating

    # Create the review form
    review_form = services.ReviewForm()

    # chua lam cai nay
    recipe_reviews = services.get_reviews(recipe_id, repository.repo_instance)

    # Page to redirect to after
    back_to = request.args.get('back_to')

    user_name = session.get('user_name')  # get logged-in user
    current_user: Optional[User] = repository.repo_instance.get_user(user_name)
    fav_status = False

    if current_user is not None:
        # Check if this recipe is in the user's favorites
        fav_status = any(fav.recipe == curr_recipe for fav in current_user.favourite_recipes)

    # Render the template and pass the form
    return render_template(
        'recipe/recipe.html',
        recipe=curr_recipe,
        review_form=review_form,
        reviews=recipe_reviews,  # pass the reviews
        fav_status=fav_status,
        nutrition_info=nutrition_info,
        random_recipe=get_random_recipe(),
        back_to=back_to,
    )


@recipe_bp.route('/add_review/<int:recipe_id>', methods=['POST'])
@login_required
def add_review(recipe_id):
    user_name: str = session['user_name']
    form = services.ReviewForm()

    if form.validate_on_submit():
        comment: str = form.comment.data
        rating = float(form.rating.data)

        services.add_review(recipe_id, comment, user_name, rating, repository.repo_instance)

    # After adding the review, redirect back to the recipe page
    return redirect(url_for('recipe_bp.recipe', recipe_id=recipe_id))


@recipe_bp.route('/favorite/<int:recipe_id>', methods=['POST'])
@login_required
def favorite(recipe_id):
    # Never None
    curr_recipe: Recipe = repository.repo_instance.get_recipe_by_id(recipe_id)

    user_name: str = session['user_name']
    current_user: Optional[User] = repository.repo_instance.get_user(user_name)
    fav = Favourite(current_user, curr_recipe)

    if fav in current_user.favourite_recipes:
        repository.repo_instance.remove_favourite_recipe(current_user, curr_recipe)
    else:
        repository.repo_instance.add_favourite_recipe(current_user, fav)

    return redirect(url_for('recipe_bp.recipe', recipe_id=recipe_id))
