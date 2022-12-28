test:
	poetry run pytest --cov='proxyx' tests/


# https://python-poetry.org/docs/cli/#version
bump:
	poetry version patch
