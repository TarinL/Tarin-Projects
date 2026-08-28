class RecipeImage:
    def __init__(self, recipe_id: int, url: str, position: int):
        self.__recipe_id = recipe_id
        self.__url = url
        self.__position = position

    def __repr__(self) -> str:
        return f"<RecipeImage: Recipe {self.recipe_id}, Position {self.position}, URL: {self.url}>"

    def __eq__(self, other):
        if not isinstance(other, RecipeImage):
            return False
        return self.recipe_id == other.recipe_id and self.position == other.position

    def __lt__(self, other):
        if not isinstance(other, RecipeImage):
            return NotImplemented
        return self.position < other.position

    def __hash__(self):
        return hash((self.recipe_id, self.position))

    @property
    def recipe_id(self) -> int:
        return self.__recipe_id

    @property
    def url(self) -> str:
        return self.__url

    @property
    def position(self) -> int:
        return self.__position
