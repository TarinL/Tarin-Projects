class RecipeInstruction:
    def __init__(self, recipe_id: int, step: str, position: int):
        self.__recipe_id = recipe_id
        self.__step = step
        self.__position = position

    def __repr__(self) -> str:
        return f"<RecipeInstruction: Recipe {self.recipe_id}, Step {self.position}: {self.step[:50]}...>"

    def __eq__(self, other):
        if not isinstance(other, RecipeInstruction):
            return False
        return self.recipe_id == other.recipe_id and self.position == other.position

    def __lt__(self, other):
        if not isinstance(other, RecipeInstruction):
            return NotImplemented
        return self.position < other.position

    def __hash__(self):
        return hash((self.recipe_id, self.position))

    @property
    def recipe_id(self) -> int:
        return self.__recipe_id

    @property
    def step(self) -> str:
        return self.__step

    @property
    def position(self) -> int:
        return self.__position
