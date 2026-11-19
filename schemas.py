"""Pydantic-схемы: контракт API для фронтенда."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngredientCreate(BaseModel):
    """Данные для создания одного ингредиента."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Мука"],
        description="Название ингредиента.",
    )
    amount: str | None = Field(
        default=None,
        max_length=255,
        examples=["200 г"],
        description="Количество ингредиента, например '200 г' или '2 штуки'.",
    )


class IngredientRead(IngredientCreate):
    """Ингредиент в ответе API."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ..., examples=[1], description="Уникальный идентификатор ингредиента."
    )
    position: int = Field(
        ...,
        ge=0,
        examples=[0],
        description="Порядковый номер ингредиента в рецепте.",
    )


class RecipeListItem(BaseModel):
    """Краткая информация о рецепте для первого экрана."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., examples=[1], description="Идентификатор рецепта.")
    title: str = Field(..., examples=["Блины"], description="Название блюда.")
    cooking_time_minutes: int = Field(
        ...,
        ge=1,
        examples=[30],
        description="Время приготовления в минутах.",
    )
    views_count: int = Field(
        ...,
        ge=0,
        examples=[12],
        description="Количество открытий детальной страницы рецепта.",
    )


class RecipeCreate(BaseModel):
    """Данные для создания нового рецепта."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Блины"],
        description="Название блюда.",
    )
    cooking_time_minutes: int = Field(
        ...,
        ge=1,
        examples=[30],
        description="Время приготовления в минутах.",
    )
    description: str = Field(
        ...,
        min_length=1,
        examples=["Смешайте ингредиенты и обжарьте блины на сковороде."],
        description="Текстовое описание приготовления.",
    )
    ingredients: list[IngredientCreate] = Field(
        default_factory=list,
        min_length=1,
        description="Список ингредиентов рецепта.",
    )


class RecipeDetail(RecipeListItem):
    """Полная информация о рецепте для второго экрана."""

    ingredients: list[IngredientRead] = Field(
        ...,
        description="Ингредиенты в порядке их добавления.",
    )
    description: str = Field(
        ...,
        examples=["Смешайте ингредиенты и обжарьте блины на сковороде."],
        description="Текстовое описание приготовления.",
    )
    created_at: datetime = Field(
        ...,
        description="Дата и время создания рецепта в формате ISO 8601.",
    )
    updated_at: datetime = Field(
        ...,
        description="Дата и время последнего обновления рецепта в формате ISO 8601.",
    )
