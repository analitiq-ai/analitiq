# Running tests

run the complete pipeline with:
```python
poetry run nox
```

specific tests for unit tests alone:
```python
poetry run nox -s pytest
```

for e2e tests:
```python
poetry run nox -s pytest_e2e
```

combine them like
```python
poetry run nox -s pytest, pytest_e2e
```