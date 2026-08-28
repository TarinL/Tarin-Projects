"""Initialize Flask app."""
from __future__ import annotations
from flask import Flask
from pathlib import Path

from recipe.adapters import database_repository
from recipe.adapters.memory_repository import MemoryRepository
from recipe.adapters.populate_repository import populate
from recipe.domainmodel.author import Author
from recipe.domainmodel.recipe import Recipe
import recipe.adapters.repository as repo
from sqlalchemy.pool import NullPool
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, clear_mappers
from recipe.adapters.orm import metadata, map_model_to_tables, mapper_registry


def create_app(test_config=None):
    """Construct the core application."""

    # Create the Flask app object.
    app = Flask(__name__)

    # Configure the app from configuration-file settings.
    app.config.from_object('config.Config')
    data_path = Path('recipe') / 'adapters' / 'data'

    if test_config is not None:
        app.config.from_mapping(test_config)
        data_path = app.config['TEST_DATA_PATH']

    if app.config['REPOSITORY'] == 'memory':
        # create the memory repository
        repo.repo_instance = MemoryRepository()
        # Populate memory repo
        database_mode = False
        populate(data_path, repo.repo_instance,database_mode)
    elif app.config['REPOSITORY'] == 'database':
        database_uri = app.config['SQLALCHEMY_DATABASE_URI']
        database_echo = app.config['SQLALCHEMY_ECHO']
        database_engine = create_engine(database_uri, connect_args={"check_same_thread": False},poolclass=NullPool, echo=database_echo)
        session_factory = sessionmaker(autocommit=False, autoflush=True, bind=database_engine)
        repo.repo_instance = database_repository.SqlAlchemyRepository(session_factory)

        if app.config['TESTING'] == 'True' or len(inspect(database_engine).get_table_names()) == 0:
            print("REPOPULATING DATABASE...")
            clear_mappers()
            mapper_registry.metadata.create_all(database_engine)
            for table in reversed(mapper_registry.metadata.sorted_tables):
                with database_engine.connect() as conn:
                    conn.execute(table.delete())

            map_model_to_tables()
            database_mode = True
            populate(data_path, repo.repo_instance, database_mode)
            print("REPOPULATING DATABASE... FINISHED")
        else:
            clear_mappers()
            map_model_to_tables()

    with app.app_context():
        # register blueprints
        from .home import home
        app.register_blueprint(home.home_bp)

        from .browse import browse
        app.register_blueprint(browse.browse_bp)

        from .recipes import recipe
        app.register_blueprint(recipe.recipe_bp)

        from .authentication import authentication
        app.register_blueprint(authentication.authentication_blueprint)

        from .profile import profile
        app.register_blueprint(profile.profile_bp)

    #     Register callback to make sure that database sessions are with
    #       http requests
        @app.before_request
        def before_flask_http_request_function():
            if isinstance(repo.repo_instance, database_repository.SqlAlchemyRepository):
                repo.repo_instance.reset_session()

    #     Register a tear-down method that will be called after each request has been processed
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            if isinstance(repo.repo_instance, database_repository.SqlAlchemyRepository):
                repo.repo_instance.close_session()
    return app
