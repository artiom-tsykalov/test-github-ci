## CI

В проекте настроен GitHub Actions. При каждом push в любую ветку и при создании Pull Request автоматически запускаются:

- `isort --check-only`
- `black --check`
- `flake8`
- `mypy`
- `pytest`
