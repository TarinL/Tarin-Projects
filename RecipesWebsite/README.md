# COMPSCI 235 Website Assignment
This project contains source code and supporting files for a lightweight Flask web application for discovering, 
browsing, and reviewing recipes. It includes the following files and folders:

- `recipe` - Code for the website including the python, html and css files.
- `tests` - Unit tests for the website code and end-to-end testing.

## Installation

**Installation via requirements.txt**

**Windows**
```shell
$ cd <project directory>
$ py -3 -m venv venv
$ venv\Scripts\activate
$ pip install -r requirements.txt
```

**MacOS**
```shell
$ cd <project directory>
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

When using PyCharm, set the virtual environment using 'File or PyCharm'->'Settings' and select your project from the left menu. Select 'Project Interpreter', click on the gearwheel button and select 'Add Interpreter'. Click the 'Existing environment' radio button to select the virtual environment. 

## Execution

**Running the application**
The project runs locally on port 5000 by default. To start the server, activate your virtual environment, install
dependencies, and run `flask run` in the terminal. Once running, the app is accessible at `http://127.0.0.1:5000/`.

````shell
$ flask run
```` 

## Testing

After you have configured pytest as the testing tool for PyCharm (File - Settings - Tools - Python Integrated Tools - Testing), you can then run tests from within PyCharm by right-clicking the tests folder and selecting "Run pytest in tests".

Alternatively, from a terminal in the root folder of the project, you can also call 'python -m pytest tests' to run all the tests. PyCharm also provides a built-in terminal, which uses the configured virtual environment. 

## Configuration

The *project directory/.env* file contains variable settings. They are set with appropriate values.

* `FLASK_APP`: Entry point of the application (should always be `wsgi.py`).
* `FLASK_ENV`: The environment in which to run the application (either `development` or `production`).
* `SECRET_KEY`: Secret key used to encrypt session data.
* `TESTING`: Set to False for running the application. Overridden and set to True automatically when testing the application.
* `WTF_CSRF_SECRET_KEY`: Secret key used by the WTForm library.
 
## Data sources

The data files are modified excerpts downloaded from:

https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews/

## Health Star Calculations

For the health star calculation formula we used the [Australian industry standard calculation](https://www.healthstarrating.gov.au/sites/default/files/2025-07/HSR%20System%20Calculator%20and%20Style%20Guide%20v8.1.pdf) assuming all foods are category 2, and leaving out missing information.
This calculation is **_not at all accurate_** as we miss crucial information such as the total weight of the food, the exact type of product produced by the recipe and the fruit/nut concentration of the recipe.
The tables and formula used for the calculation are derived from pages 19 and 24 as they had to modified to account for lack of information.


## References & Accreditation

- Nutrition health star rating was informed by: [healthstarrating.gov.au](https://www.healthstarrating.gov.au/sites/default/files/2025-07/HSR%20System%20Calculator%20and%20Style%20Guide%20v8.1.pdf)
- Star SVGs used for nutrition and rating stars from: [fontawesome.com](https://fontawesome.com) which are under a CC BY 4.0 license as seen [here](https://fontawesome.com/license/free#icons) and thus are free to use in this project with attribution.
- The main page's splash image comes from: [pexels.com](https://www.pexels.com/photo/variety-of-spices-and-vegetables-on-black-surface-1192031/) and is free to use without attribution as seen [here](https://www.pexels.com/license/).

