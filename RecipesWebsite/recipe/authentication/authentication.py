from flask import Blueprint, render_template, redirect, url_for, session
from flask import request, flash
from flask_wtf import FlaskForm
from functools import wraps
from password_validator import PasswordValidator
from recipe.utilities.services import get_random_recipe
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
import recipe.adapters.repository as repo
import recipe.authentication.services as services

authentication_blueprint = Blueprint(
    'authentication_bp', __name__, url_prefix='/authentication')


@authentication_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    """blueprint for registering a new user"""

    form = RegistrationForm()
    user_name_not_unique = None

    if form.validate_on_submit():
        try:
            services.add_user(
                form.user_name.data,
                form.password.data,
                repo.repo_instance)

            # if user is added, redirect to login page
            flash('User registered successfully', 'success')
            return redirect(url_for('authentication_bp.login'))
        except services.NameAlreadyExistsException:
            user_name_not_unique = 'Your user name already exists. Please' \
                ' provide a different user name'

    return render_template(
        'authentication/credentials.html',
        title='Register',
        form=form,
        user_name_error_message=user_name_not_unique,
        password_error_message=None,
        random_recipe=get_random_recipe()
    )


@authentication_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    """Blueprint for logging in"""

    form = LoginForm()
    user_name_not_recognised = None
    password_does_not_match = None
    status_code = 200

    if form.validate_on_submit():
        try:
            user = services.get_user(form.user_name.data, repo.repo_instance)

            # authentication
            services.authenticate_user(
                user['username'], form.password.data, repo.repo_instance)

            session.clear()
            session['user_name'] = user['username']
            flash('Login successful', 'success')
            next_page = request.args.get('next', '')
            if next_page != '':
                return redirect(next_page)
            else:
                return redirect(url_for('home_bp.home'))

        except services.UserDoesNotExistException:
            user_name_not_recognised = 'User name does not exist'
            status_code = 401

        except services.AuthenticationException:
            password_does_not_match = 'Password does not match'
            status_code = 401

    return render_template(
        'authentication/credentials.html',
        user_name_error_message=user_name_not_recognised,
        password_error_message=password_does_not_match,
        title='Login',
        form=form,
        random_recipe=get_random_recipe(),
    ), status_code


@authentication_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home_bp.home'))


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_name' not in session:
            double_redirect = request.path if request.method == 'GET' else ''
            return redirect(url_for(
                'authentication_bp.login',
                next=double_redirect
            ))
        return view(**kwargs)

    return wrapped_view


class PasswordValid:
    def __init__(self, message=None):
        if not message:
            message = 'Your password must have at least 8 characters, contain'\
                ' an upper case letter, a lower case letter, and a digit'
        self.message = message

    def __call__(self, form, field):
        check = (PasswordValidator()
                 .min(8)
                 .has().uppercase()
                 .has().lowercase()
                 .has().digits()
                 )

        if not check.validate(field.data):
            raise ValidationError(self.message)


class RegistrationForm(FlaskForm):
    user_name = StringField('Username', [
        DataRequired(message='User name is required'),
        Length(min=3, message='User name must be at least 3 characters')
    ])
    password = PasswordField('Password', [
        DataRequired(message='Password is required'),
        PasswordValid()
    ])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    user_name = StringField('Username', [
        DataRequired()])
    password = PasswordField('Password', [
        DataRequired()])
    submit = SubmitField('Login')
