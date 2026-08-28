from flask import Blueprint, render_template
from recipe.utilities.services import get_random_recipe

home_bp = Blueprint('home_bp', __name__)


@home_bp.route('/', methods=['GET'])
def home():
    """ Blueprint for the home page. """

    return render_template(
        'home/home.html',
        random_recipe=get_random_recipe()
    )
