import pytest
from flask import session
from tests.conftest import client
from tests.conftest import auth

def test_register(client):
    # Check that we retrieve the register page.
    response_code = client.get('/authentication/register').status_code
    assert response_code == 200

    # Check that we can register a user successfully, supplying a valid user name and password.
    response = client.post(
        '/authentication/register',
        data={'user_name': 'gmichael', 'password': 'CarelessWhisper1984'}
    )
    assert response.status_code == 200


@pytest.mark.parametrize(('user_name', 'password', 'message'), (
        ('', '', b'User name is required'),
        ('cj', '', b'User name must be at least 3 characters'),
        ('test', '', b'Password is required'),
        ('test', 'test',
         b'Your password must have at least 8 characters, contain an upper case letter, a lower case letter, and a digit'),
        ('ellefleming', 'Test#6^0', b'Your user name already exists. Please provide a different user name'),
))
def test_register_with_invalid_input(client, user_name, password, message):
    # Check that attempting to register with invalid combinations of user name and password generate appropriate error
    # messages.
    response = client.post(
        '/authentication/register',
        data={'user_name': user_name, 'password': password},
        follow_redirects=True
    )
    assert message in response.data


def test_login(client, auth):
    # Check that we can retrieve the login page.
    status_code = client.get('/authentication/login').status_code
    assert status_code == 200

    # Check that a successful login generates a redirect to the homepage.
    response = auth.login(user_name='ellefleming', password='E1230$@#')
    assert response.status_code == 200

    # Check that a session has been created for the logged-in user.
    with client.session_transaction() as sess:
        assert sess['user_name'] == 'ellefleming'


def test_logout(client, auth):
    # Login a user.
    auth.login(user_name='ellefleming', password='E1230$@#')

    with client.session_transaction() as sess:
        # Check that logging out clears the user's session.
        auth.logout()
        assert 'user_id' not in sess


def test_index(client):
    # Check that we can retrieve the home page.
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to' in response.data  #### b'': meaning byte stream, everything will be treated in the response object as bytes


def test_browse(client):
    response = client.get('/browse')
    assert response.status_code == 200


def test_login_required_to_review(client):
    response = client.post('/add_review/40')
    assert response.headers['Location'] == '/authentication/login?next='


def test_browse_with_id(client):
    response = client.get('/recipe/38')
    assert response.status_code == 200

    assert b'Low-Fat Berry Blue Frozen Dessert' in response.data
