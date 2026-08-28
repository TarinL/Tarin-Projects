from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from recipe.domainmodel.recipe import Recipe


class Category:
    def __init__(self, name: str, recipes: List["Recipe"] = None, category_id: int = None):
        self.__id: int = category_id
        self.__name: str = name
        self.__recipes: List["Recipe"] = recipes if recipes is not None else []

    def __repr__(self) -> str:
        return f"<Category {self.id}: {self.name}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Category):
            return False
        return self.id == other.id

    def __lt__(self, other) -> bool:
        if not isinstance(other, Category):
            raise TypeError("Comparison must be between Category instances")
        return self.id < other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def id(self) -> int:
        return self.__id

    @id.setter
    def id(self, id: int):
        self.__id = id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def recipes(self) -> List["Recipe"]:
        return self.__recipes

    def add_recipe(self, recipe) -> None:
        """ Adds a recipe to the category's list of recipes. """

        from recipe.domainmodel.recipe import Recipe
        if isinstance(recipe, Recipe):
            self.__recipes.append(recipe)
        else:
            raise TypeError("Expected a Recipe instance")
