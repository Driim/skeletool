install:
	poetry install

format:
	poetry run black src tests

lint:
	poetry run flake8 src tests

test:
	poetry run pytest