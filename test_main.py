"""Интеграционные тесты API кулинарной книги."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
from main import app
from models import Base

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def override_get_db() -> Iterator[Session]:
    """Подменяет рабочую сессию БД на сессию тестовой in-memory SQLite."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database() -> Iterator[None]:
    """Создаёт чистую схему БД перед каждым тестом и удаляет её после."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_recipe(
    title: str = "Блины",
    cooking_time_minutes: int = 30,
    views_count: int = 0,
) -> dict:
    """Создаёт рецепт через API и возвращает JSON-ответ."""
    response = client.post(
        "/recipes",
        json={
            "title": title,
            "cooking_time_minutes": cooking_time_minutes,
            "description": f"Описание рецепта: {title}.",
            "ingredients": [
                {"name": "Мука", "amount": "200 г"},
                {"name": "Молоко", "amount": "500 мл"},
            ],
        },
    )
    assert response.status_code == 201
    recipe = response.json()

    if views_count:
        for _ in range(views_count):
            detail_response = client.get(f"/recipes/{recipe['id']}")
            assert detail_response.status_code == 200

    return recipe


def test_create_recipe_returns_201() -> None:
    """POST /recipes создаёт рецепт и возвращает его полные данные."""
    response = client.post(
        "/recipes",
        json={
            "title": "Паста карбонара",
            "cooking_time_minutes": 25,
            "description": "Классическая паста с соусом на основе яиц и сыра.",
            "ingredients": [
                {"name": "Спагетти", "amount": "200 г"},
                {"name": "Яйца", "amount": "2 штуки"},
                {"name": "Пармезан", "amount": "50 г"},
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Паста карбонара"
    assert data["cooking_time_minutes"] == 25
    assert data["views_count"] == 0
    assert len(data["ingredients"]) == 3
    assert data["ingredients"][0]["name"] == "Спагетти"
    assert data["ingredients"][0]["position"] == 0


def test_create_recipe_without_ingredients_returns_422() -> None:
    """POST /recipes отклоняет рецепт без ингредиентов."""
    response = client.post(
        "/recipes",
        json={
            "title": "Пустой рецепт",
            "cooking_time_minutes": 10,
            "description": "Рецепт без ингредиентов.",
            "ingredients": [],
        },
    )

    assert response.status_code == 422


def test_create_recipe_with_invalid_cooking_time_returns_422() -> None:
    """POST /recipes отклоняет нулевое или отрицательное время приготовления."""
    response = client.post(
        "/recipes",
        json={
            "title": "Некорректный рецепт",
            "cooking_time_minutes": 0,
            "description": "Время приготовления должно быть больше нуля.",
            "ingredients": [{"name": "Вода", "amount": "1 л"}],
        },
    )

    assert response.status_code == 422


def test_get_recipes_returns_empty_list() -> None:
    """GET /recipes возвращает пустой список, если рецептов нет."""
    response = client.get("/recipes")

    assert response.status_code == 200
    assert response.json() == []


def test_get_recipes_sorted_by_views_then_cooking_time() -> None:
    """GET /recipes сортирует рецепты по просмотрам, затем по времени."""
    create_recipe(title="Салат", cooking_time_minutes=10, views_count=1)
    create_recipe(title="Суп", cooking_time_minutes=40, views_count=5)
    create_recipe(title="Паста", cooking_time_minutes=25, views_count=5)
    create_recipe(title="Блины", cooking_time_minutes=30, views_count=5)

    response = client.get("/recipes")
    assert response.status_code == 200

    titles = [recipe["title"] for recipe in response.json()]
    assert titles == ["Паста", "Блины", "Суп", "Салат"]

def test_get_recipe_returns_detail_and_increments_views() -> None:
    """GET /recipes/{id} возвращает детали и увеличивает счётчик просмотров."""
    created = create_recipe(title="Блины", cooking_time_minutes=30)

    first_response = client.get(f"/recipes/{created['id']}")
    second_response = client.get(f"/recipes/{created['id']}")

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["views_count"] == 1
    assert second_data["views_count"] == 2
    assert first_data["description"] == "Описание рецепта: Блины."
    assert [item["name"] for item in first_data["ingredients"]] == [
        "Мука",
        "Молоко",
    ]


def test_get_nonexistent_recipe_returns_404() -> None:
    """GET /recipes/{id} возвращает 404 для несуществующего рецепта."""
    response = client.get("/recipes/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Рецепт с id=999 не найден."
