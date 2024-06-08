# UnitTest the Database

## Database Config

- type

  `postgres`

- config

  user: `postgres`

  password: `root`,

  host: `localhost`,

  port: `5432`,

  dbname: `app`,

  db_schemas: `["information_schema", "public", "schema1", "schema2"]`

- Create Schemas and execute sql files

  Create schemas and xecute sql files for each schema.

  `public.sql`, `schema1.sql`, `schema2.sql`

  `information_schema` is built-in scheam, so didn't dump the sql.

## Python environment

copy `test_database.py` to `libs/tests/base/`.

- python version

  ```bash
    python3 --version
    Python 3.9.13
  ```

- install packages

```bash
  pip install poetry

  poetry install
```

## Run Test

```bash
python -m pytest libs/tests
```
