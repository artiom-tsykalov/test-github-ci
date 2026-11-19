"""HTTP API кулинарной книги.

Запуск:
    uvicorn main:app --reload

Документация:
    http://127.0.0.1:8000/docs
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from crud import create_recipe, get_recipe, get_recipes, increment_recipe_views
from database import engine, get_db
from models import Base, Recipe
from schemas import RecipeCreate, RecipeDetail, RecipeListItem


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Создаёт таблицы при старте приложения.

    В учебном проекте таблицы создаются автоматически.
    В production обычно применяют Alembic-миграции.
    """
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Cookbook API",
    description=(
        "API кулинарной книги. "
        "Позволяет получать список рецептов, открывать детальную информацию "
        "и создавать новые рецепты."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/recipes",
    response_model=list[RecipeListItem],
    status_code=status.HTTP_200_OK,
    summary="Получить список рецептов",
    description=(
        "Возвращает рецепты для таблицы на первом экране.\n\n"
        "Сортировка:\n"
        "1. По убыванию количества просмотров.\n"
        "2. При равном количестве просмотров — по возрастанию времени приготовления.\n"
        "3. При полном совпадении — по идентификатору рецепта."
    ),
    response_description="Список кратких карточек рецептов.",
    tags=["Рецепты"],
)
def read_recipes(
    db: Session = Depends(get_db),
) -> list[Recipe]:
    """Возвращает список всех рецептов в порядке популярности."""
    return get_recipes(db)


@app.get(
    "/recipes/{recipe_id}",
    response_model=RecipeDetail,
    status_code=status.HTTP_200_OK,
    summary="Получить детальную информацию о рецепте",
    description=(
        "Возвращает полную карточку рецепта: название, время приготовления, "
        "ингредиенты и описание.\n\n"
        "Каждый успешный вызов увеличивает `views_count` рецепта на 1."
    ),
    response_description="Полная информация о рецепте.",
    tags=["Рецепты"],
    responses={
        404: {
            "description": "Рецепт с указанным идентификатором не найден.",
        },
    },
)
def read_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
) -> Recipe:
    """Возвращает детальную информацию о рецепте и увеличивает просмотры."""
    recipe = get_recipe(db, recipe_id)

    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецепт с id={recipe_id} не найден.",
        )

    return increment_recipe_views(db, recipe)


@app.post(
    "/recipes",
    response_model=RecipeDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый рецепт",
    description=(
        "Создаёт рецепт с названием, временем приготовления, описанием "
        "и списком ингредиентов.\n\n"
        "Новый рецепт получает `views_count = 0`."
    ),
    response_description="Созданный рецепт.",
    tags=["Рецепты"],
    responses={
        201: {
            "description": "Рецепт успешно создан.",
        },
        422: {
            "description": "Тело запроса не соответствует схеме RecipeCreate.",
        },
    },
)
def create_new_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
) -> Recipe:
    """Создаёт новый рецепт в кулинарной книге."""
    return create_recipe(db, recipe_data)
