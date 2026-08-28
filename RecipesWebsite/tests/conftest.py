import pytest
from recipe import create_app, populate, MemoryRepository
from utils import get_project_root

# Testing file directory
TEST_DATA_PATH = get_project_root() / "tests" / "Data"


# the csv files in the test folder are different from the csv files in the covid/adapters/data folder!
# tests are written against the csv files in tests, this data path is used to override default path for testing

@pytest.fixture
def memory_repo():
    repo = MemoryRepository()
    populate(TEST_DATA_PATH, repo, False)
    return repo


@pytest.fixture
def client():
    my_app = create_app({
        'TESTING': True,
        'TEST_DATA_PATH': TEST_DATA_PATH,
        'WTF_CSRF_ENABLED': False
    })
    return my_app.test_client()


class AuthenticationManager:
    def __init__(self, client):
        self.__client = client

    def login(self, user_name, password):
        return self.__client.post(
            '/authentication/login',
            data={'user_name': user_name, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self.__client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthenticationManager(client)
