class RecipeIngredient:
    def __init__(self, recipe_id: int, quantity: str, ingredient: str, position: int):
        self.__recipe_id = recipe_id
        self.__quantity = quantity
        self.__ingredient = ingredient
        self.__position = position

    def __repr__(self) -> str:
        return f"<RecipeIngredient: Recipe {self.recipe_id}, Position {self.position}, {self.quantity} {self.ingredient}>"

    def __eq__(self, other):
        if not isinstance(other, RecipeIngredient):
            return False
        return self.recipe_id == other.recipe_id and self.position == other.position

    def __lt__(self, other):
        if not isinstance(other, RecipeIngredient):
            return NotImplemented
        return self.position < other.position

    def __hash__(self):
        return hash((self.recipe_id, self.position))

    @property
    def recipe_id(self) -> int:
        return self.__recipe_id

    @property
    def quantity(self) -> str:
        return self.__quantity

    @property
    def ingredient(self) -> str:
        return self.__ingredient

    @property
    def position(self) -> int:
        return self.__position
