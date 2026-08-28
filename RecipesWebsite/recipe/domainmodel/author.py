from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from recipe.domainmodel.recipe import Recipe


class Author:
    def __init__(self, author_id: int, name: str, recipes: List["Recipe"] = None):
        self.__id: int = author_id
        self.__name: str = name
        self.__recipes: List["Recipe"] = recipes if recipes is not None else []

    def __repr__(self) -> str:
        return f"<Author {self.id}: {self.name}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Author):
            return False
        return self.id == other.id

    def __lt__(self, other) -> bool:
        if not isinstance(other, Author):
            raise TypeError("Comparison must be between Author instances")
        return self.id < other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def recipes(self) -> List["Recipe"]:
        return self.__recipes

    def add_recipe(self, recipe) -> None:
        """ Adds a recipe to the author's list of recipes. """

        from recipe.domainmodel.recipe import Recipe
        if not isinstance(recipe, Recipe):
            raise TypeError("Expected a Recipe instance")

        if recipe.id not in [r.id for r in self.__recipes]:
            self.__recipes.append(recipe)
        else:
            raise ValueError("Recipe already exists for this author")

    def remove_recipes(self):
        self.__recipes = []