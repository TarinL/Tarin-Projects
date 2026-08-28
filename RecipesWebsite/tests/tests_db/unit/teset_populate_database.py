from recipe.adapters.orm import metadata
from sqlalchemy import select, inspect

def test_database_populate_inspect_table_names(database_engine):
    inspector = inspect(database_engine)
    names = set(inspector.get_table_names())
    assert names == {"authors", "nutrition", "recipe_images", "recipes", "users"}

# user
def test_database_populate_select_all_users(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['users']])
        result = connection.execute(select_statement)

        all_users = []
        for row in result:
            all_users.append(row['username'])

        assert all_users == '''list of all usernames'''

# recipe
def test_database_populate_select_all_recipes(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['recipes']])
        result = connection.execute(select_statement)

        all_recipes = []
        for row in result:
            all_recipes.append([row['recipe_id'], row['name'], row['author_id'], row['description'], row['nutrition_id']])

        assert len(all_recipes) == 5

        assert all_recipes[0] == '''add list of recipe info for first recipe'''

# nutrition
def test_database_populate_select_all_nutrition(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['nutrition']])
        result = connection.execute(select_statement)

        all_nutrition = []
        for row in result:
            all_nutrition.append([row['nutrition_id'], row['calories'], row['fat'], row['saturated_fat'],
            row['cholesterol'], row['sodium'], row['carbohydrates'], row['fiber'], row['sugar'], row['protein']])

        number_recipes = len(all_nutrition)
        # assert number_recipes == insert number of recipes

        assert all_nutrition[0] == '''put stats of the first recipies nutrition'''

# authors
def test_database_populate_select_all_authors(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['authors']])
        result = connection.execute(select_statement)

        all_authors = []
        for row in result:
            all_authors.append((row['author_id'], row['author_name']))

        number_authors = len(all_authors)
        assert number_authors == '''put in number of authors'''

        assert all_authors[0] == '''put tuple in for first author'''

# recipe_image
def test_database_populate_select_all_recipe_images(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['recipe_images']])
        result = connection.execute(select_statement)

        all_recipe_images = []
        for row in result:
            all_recipe_images.append((row['recipe_id'], row['url']))

        number_recipe_images = len(all_recipe_images)
        assert number_recipe_images == '''put in number of recipes images'''

        assert all_recipe_images[0] == '''add recipe id and url as tuple'''

# category
def test_database_populate_select_all_categories(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['categories']])
        result = connection.execute(select_statement)

        all_categories = []
        for row in result:
            all_categories.append(row['name'])

        number_categories = len(all_categories)

        expected_categories = {'list all expected categories'}
        assert set(all_categories) == expected_categories
        assert number_categories == '''put in number of categories'''


# favourite
def test_database_populate_select_all_favourites(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['favourites']])
        result = connection.execute(select_statement)

        all_favourites = []
        for row in result:
            all_favourites.append((row['user'], row['recipe']))

        number_favourites = len(all_favourites)
        assert number_favourites == '''put in number of favourites'''
        assert all_favourites[0] == '''add recipe id and recipe name tuple'''

# instructions
def test_database_populate_select_all_instructions(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['instructions']])
        result = connection.execute(select_statement)

        all_instructions = []
        for row in result:
            all_instructions.append((row['recipe_id'], row['instructions']))

        number_instructions = len(all_instructions)
        assert number_instructions == '''put in number of instruction sets'''
        assert all_instructions[0][0] == '''add recipe id'''
        assert all_instructions[0][1] == '''add recipe instructions'''

# ingredients
def test_database_populate_select_all_ingredients(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['ingredients']])
        result = connection.execute(select_statement)

        all_ingredients = []
        for row in result:
            all_ingredients.append(row[['recipe_id'], row['ingredient'], row['quantity']])

        number_ingredients = len(all_ingredients)

        assert number_ingredients == '''put in number of ingredients'''
        assert all_ingredients[0][0] == '''add recipe id'''
        assert all_ingredients[0][1] == '''add recipe ingredient'''
        assert all_ingredients[0][2] == '''add recipe quantity'''

# reviews
def test_database_populate_select_all_reviews(database_engine):
    with database_engine.connect() as connection:
        select_statement = select([metadata.tables['reviews']])
        result = connection.execute(select_statement)

        all_reviews = []
        for row in result:
            all_reviews.append((row['rating'], row['comment']))

        number_reviews = len(all_reviews)
        assert number_reviews == '''put in number of reviews'''
        assert all_reviews[0][0] == '''add review rating'''
        assert all_reviews[0][1] == '''add recipe comment'''


