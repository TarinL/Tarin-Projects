import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from recipe import mapper_registry
from recipe.adapters import database_repository, populate_repository
from recipe.adapters.orm import metadata, map_model_to_tables

from utils import get_project_root

TEST_DATA_PATH_DATABASE_FULL = get_project_root() / "recipe" / "adapters" / "data"
TEST_DATA_PATH_DATABASE_LIMITED = get_project_root() / "tests" / "data"

TEST_DATABASE_URI_IN_MEMORY = 'sqlite://'
TEST_DATABASE_URI_FILE = 'sqlite:///recipes-test.db'

@pytest.fixture
def database_engine():
    clear_mappers()
    engine = create_engine(TEST_DATABASE_URI_IN_MEMORY)
    metadata.create_all(engine)
    for table in reversed(metadata.sorted_tables):
        engine.execute(table.delete())
    map_model_to_tables()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    repo_instance = database_repository.SqlAlchemyRepository(session_factory)
    database_mode = True
    populate_repository.populate(TEST_DATA_PATH_DATABASE_LIMITED, repo_instance, database_mode)
    yield engine
    metadata.drop_all(engine)

@pytest.fixture
def session_factory():
    clear_mappers()
    engine = create_engine(TEST_DATABASE_URI_IN_MEMORY)
    mapper_registry.metadata.create_all(engine)
    for table in reversed(mapper_registry.metadata.sorted_tables):
        with engine.connect() as connection:
            connection.execute(table.delete())

    map_model_to_tables()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    repo_instance = database_repository.SqlAlchemyRepository(session_factory)
    database_mode = True
    populate_repository.populate(TEST_DATA_PATH_DATABASE_LIMITED, repo_instance, database_mode)
    yield session_factory
    mapper_registry.metadata.drop_all(engine)

@pytest.fixture
def empty_session():
    clear_mappers()
    engine = create_engine(TEST_DATABASE_URI_IN_MEMORY)
    mapper_registry.metadata.create_all(engine)
    for table in reversed(mapper_registry.metadata.sorted_tables):
        with engine.connect() as connection:
            connection.execute(table.delete())
    map_model_to_tables()
    session_factory = sessionmaker(bind=engine)
    yield session_factory()
    mapper_registry.metadata.drop_all(engine)
