from typing import Optional, List
from better_profanity import profanity
from flask_wtf import FlaskForm
from wtforms import ValidationError, TextAreaField, RadioField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length

from recipe.adapters import repository
from recipe.adapters.repository import AbstractRepository
from recipe.domainmodel.review import Review


class NonExistentRecipeException(Exception):
    pass


class UnknownUserException(Exception):
    pass


class ProfanityFree:
    def __init__(self, message=None):
        if not message:
            message = u'Field must not contain profanity'
        self.message = message

    def __call__(self, form, field):
        if profanity.contains_profanity(field.data):
            raise ValidationError(self.message)


class ReviewForm(FlaskForm):
    comment = TextAreaField('Comment', [
        DataRequired(),
        Length(min=4, message='Your comment is too short'),
        ProfanityFree(message='Your comment must not contain profanity')
    ])

    rating = RadioField(
        'Rating',
        choices=[('0', '0'), ('0.5', '0.5'), ('1', '1'), ('1.5', '1.5'), ('2', '2'), ('2.5', '2.5'), ('3', '3'),
                 ('3.5', '3.5'), ('4', '4'), ('4.5', '4.5'), ('5', '5')],
        validators=[DataRequired(message="Please give a rating")]
    )

    recipe_id = HiddenField("Recipe id")
    submit = SubmitField('Post Review Publicly')


def add_review(recipe_id: int, comment_text: str, user_name: str, rating: float, repo: AbstractRepository):
    """ Validates and adds a review to a recipe in the repository """

    # Check that the article exists.
    curr_recipe = repo.get_recipe_by_id(recipe_id)
    if curr_recipe is None:
        raise NonExistentRecipeException

    curr_user = repo.get_user(user_name)
    if curr_user is None:
        raise UnknownUserException

    # Create review.
    new_review = Review(curr_user, curr_recipe, rating, comment_text)  # can be a bug

    # Update the repository.
    repo.add_review(new_review)


def get_reviews(recipe_id: int, repo: AbstractRepository) -> List[Review]:
    """ Gets all reviews for a recipe. """

    reviews = repo.get_recipe_reviews(recipe_id, 1, 20, sort_method='date')
    return reviews