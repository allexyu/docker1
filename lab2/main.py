import math
import hashlib
import uvicorn
from bitarray import bitarray
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Callable, Optional


class BloomFilter(object):
    def __init__(self, size: int,
                 number_expected_elements: int,
                 hash_function_names: Optional[list[str]] = None):

        # Инициализирует фильтр с заданными параметрами

        # size: Размер битового массива
        # number_expected_elements: Ожидаемое количество элементов
        # hash_function_names: Список имен хеш-функций из hashlib

        self.size = size
        self.number_expected_elements = number_expected_elements
        self.bloom_filter = bitarray(size)
        self.bloom_filter.setall(0)

        # Оптимальное количество хеш-функций
        self.number_hash_functions = round((self.size / self.number_expected_elements) * math.log(2))

        # Если хеш-функции не указаны, используем md5
        if hash_function_names is None:
            hash_function_names = ["md5"]

        # Проверяем, что указанные хеш-функции поддерживаются hashlib
        supported_hashes = hashlib.algorithms_available
        self.hash_functions: list[Callable[[str], int]] = []
        for name in hash_function_names:

            if name not in supported_hashes:
                raise ValueError(f"Хеш-функция '{name}' не поддерживается. Доступные: {supported_hashes}")

            def create_hash_func(algorithm = name) -> Callable[[str], int]:
                def hash_func(s: str) -> int:
                    hasher = hashlib.new(algorithm)
                    hasher.update(s.encode('utf-8'))
                    return int(hasher.hexdigest(), 16) % self.size
                return hash_func

            self.hash_functions.append(create_hash_func())

    def _hash(self, item: str, k: int) -> int:
        # Генерирует хеш-значение для элемента с использованием k-й хеш-функции
        # item: Элемент для хеширования
        # k: Индекс хеш-функции
        # Используем k-ю хеш-функцию из списка, добавляя индекс для разнообразия
        return self.hash_functions[k % len(self.hash_functions)](item + str(k))

    def add_to_filter(self, item: str) -> None:
        # Добавляет элемент в фильтр Блума
        for i in range(self.number_hash_functions):
            index = self._hash(item, i)
            self.bloom_filter[index] = 1

    def check_is_not_in_filter(self, item: str) -> bool:
        # Проверяет, отсутствует ли элемент в фильтре Блума
        # item: Элемент для проверки

        for i in range(self.number_hash_functions):
            index = self._hash(item, i)
            if self.bloom_filter[index] == 0:
                return True  # Элемент точно не в фильтре
        return False  # Элемент может быть в фильтре


class Item(BaseModel):
    key: str

class BloomFilterConfig(BaseModel):
    size: int
    number_expected_elements: int
    hash_function_names: list[str]


app = FastAPI()
bloom_filter: Optional[BloomFilter] = None


# Эндпоинт для инициализации фильтра Блума с заданными параметрами
@app.post("/init")
def init_bloom_filter(config: BloomFilterConfig):

    global bloom_filter
    try:
        bloom_filter = BloomFilter(
            size = config.size,
            number_expected_elements = config.number_expected_elements,
            hash_function_names = config.hash_function_names
        )
        return {"message": "Фильтр Блума успешно инициализирован"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Эндпоинт для добавления ключа в фильтр Блума
@app.post("/add")
def add_item(item: Item):

    if bloom_filter is None:
        raise HTTPException(status_code=400, detail="Фильтр Блума не инициализирован")

    bloom_filter.add_to_filter(item.key)
    return {"message": f"Ключ '{item.key}' успешно добавлен в фильтр"}


# Эндпоинт для проверки, может ли ключ присутствовать в фильтре Блума
@app.get("/check/{key}")
def check_item(key: str):

    if bloom_filter is None:
        raise HTTPException(status_code=400, detail="Фильтр Блума не инициализирован")

    if bloom_filter.check_is_not_in_filter(key):
        return {"message": f"Ключ '{key}' точно отсутствует в фильтре"}
    else:
        return {"message": f"Ключ '{key}' может присутствовать в фильтре"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)