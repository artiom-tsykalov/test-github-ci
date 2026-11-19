"""Функции доступа к данным: создание и чтение рецептов."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Ingredient, Recipe
from schemas import RecipeCreate


def create_recipe(db: Session, recipe_data: RecipeCreate) -> Recipe:
    """Создаёт рецепт и связанные с ним ингредиенты.

    Args:
        db: Активная сессия SQLAlchemy.
        recipe_data: Валидированные данные рецепта из тела POST-запроса.

    Returns:
        Созданный объект `Recipe` с заполненным списком ингредиентов.
    """

    recipe = Recipe(
        title=recipe_data.title,
        cooking_time_minutes=recipe_data.cooking_time_minutes,
        description=recipe_data.description,
    )

    for position, ingredient in enumerate(recipe_data.ingredients):
        recipe.ingredients.append(
            Ingredient(
                name=ingredient.name,
                amount=ingredient.amount,
                position=position,
            )
        )

    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def get_recipes(db: Session) -> list[Recipe]:
    """Возвращает все рецепты, отсортированные для первого экрана.

    Сортировка:
    1. По убыванию количества просмотров.
    2. При равном количестве просмотров — по возрастанию времени приготовления.
    3. При полном совпадении — по идентификатору, чтобы результат был стабильным.
    """
    statement = select(Recipe).order_by(
        Recipe.views_count.desc(),
        Recipe.cooking_time_minutes.asc(),
        Recipe.id.asc(),
    )
    return list(db.scalars(statement))


def get_recipe(db: Session, recipe_id: int) -> Recipe | None:
    """Находит рецепт по идентификатору.

    Args:
        db: Активная сессия SQLAlchemy.
        recipe_id: Идентификатор рецепта из пути запроса.

    Returns:
        Объект `Recipe` либо `None`, если рецепт не найден.
    """
    statement = select(Recipe).where(Recipe.id == recipe_id)
    return db.scalar(statement)


def increment_recipe_views(db: Session, recipe: Recipe) -> Recipe:
    """Увеличивает счётчик просмотров рецепта на 1.

    Вызывается только при успешном открытии детальной информации.
    """
    recipe.views_count += 1
    db.commit()
    db.refresh(recipe)
    return recipe
