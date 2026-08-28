from typing import Optional


class Filter:
    def __init__(self, sort_method: str = 'none', search: Optional[str] = None, search_type: str = 'name',
                 rating_range: tuple[float, float] = (0.0, 5.0), nutrition_range: tuple[float, float] = (0.0, 5.0)):
        self.__nutrition_range: tuple[float, float] = nutrition_range
        self.__rating_range: tuple[float, float] = rating_range
        self.__search: Optional[str] = search.lower() if search else None
        self.__search_type: str = search_type.lower()
        self.__sort_method: str = sort_method.lower()

        self.__validate()

    @property
    def min_nutrition(self) -> float:
        return self.__nutrition_range[0]

    @property
    def max_nutrition(self) -> float:
        return self.__nutrition_range[1]

    @property
    def min_rating(self) -> float:
        return self.__rating_range[0]

    @property
    def max_rating(self) -> float:
        return self.__rating_range[1]

    @property
    def search(self) -> Optional[str]:
        return self.__search

    @property
    def search_type(self) -> str:
        return self.__search_type

    @property
    def sort_method(self) -> str:
        return self.__sort_method

    def __validate(self):
        sort_methods = ['none', 'author', 'date', 'name', 'rating', 'recipe', 'recipes_count', 'user']
        if self.sort_method not in sort_methods:
            raise ValueError(f"Sort method '{self.sort_method}' is not supported. Must be one of {sort_methods}.")

        search_types = ['name', 'author', 'category']
        if self.search_type not in search_types:
            raise ValueError(f"Search type '{self.search_type}' is not supported. Must be one of {search_types}.")

        if self.min_rating > self.max_rating:
            raise ValueError(f"Rating range invalid, min_rating={self.min_rating} exceeds max_rating={self.max_rating}")

        if self.min_nutrition > self.max_nutrition:
            raise ValueError(
                f"Nutrition star range invalid, min_nutrition={self.min_nutrition} exceeds max_nutrition={self.max_nutrition}")
