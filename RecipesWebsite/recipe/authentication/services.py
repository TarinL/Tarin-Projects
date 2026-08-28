from recipe.adapters.repository import AbstractRepository
from recipe.domainmodel.user import User
from typing import Dict
from werkzeug.security import generate_password_hash, check_password_hash


class NameAlreadyExistsException(Exception):
    pass


class UserDoesNotExistException(Exception):
    pass


class AuthenticationException(Exception):
    pass


def add_user(username: str, password: str, repo: AbstractRepository):
    """ Checks and adds a new user to the repository """

    user = repo.get_user(username)

    if user is not None:
        raise NameAlreadyExistsException

    password_hashed = generate_password_hash(password)
    user = User(username=username, password=password_hashed)
    repo.add_user(user)


def get_user(user_name: str, repo: AbstractRepository) -> Dict:
    """ Gets a user from the repository """

    user = repo.get_user(user_name)

    if user is None:
        raise UserDoesNotExistException

    return user_to_dict(user)


def authenticate_user(username: str, password: str, repo: AbstractRepository):
    """ Checks if the given username and password are valid """

    user = repo.get_user(username)
    authenticated = None

    if user is not None:
        authenticated = check_password_hash(user.password, password)

    if not authenticated:
        raise AuthenticationException


def user_to_dict(user: User) -> Dict:
    """ Converts a user object into a dictionary """

    return {
        "username": user.username,
        "password": user.password
    }
