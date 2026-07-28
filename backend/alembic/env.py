"""
Alembic environment configuration.

Wired directly into the application's own settings and ORM metadata so
there is exactly one source of truth for the database URL and the schema:

    * Connection string  -> app.core.config.settings.DATABASE_URL
      (itself assembled from the POSTGRES_* env vars / .env file, or
      overridden directly via DATABASE_URL — see .env.example).
    * Target schema       -> app.db.base.Base.metadata, populated by
      importing app.models, which imports every ORM model module.

This means `alembic revision --autogenerate` will correctly diff the full
set of models against the database, and `alembic upgrade head` never needs
a duplicated/hardcoded connection string in alembic.ini.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure the project root (the directory containing `app/`) is importable
# regardless of the current working directory `alembic` is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402,F401  (populates Base.metadata as a side effect)

# Alembic Config object, providing access to the values within alembic.ini.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the runtime database URL from application settings. Doing this in
# code (rather than in alembic.ini) means a single .env / environment
# variable set controls both the running app and its migrations.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Model metadata used by 'autogenerate' to compare against the live DB.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping the Engine creation we
    don't even need a DBAPI to be available. Calls to context.execute()
    here emit the given string to the script output, useful for generating
    SQL scripts to hand off to a DBA (`alembic upgrade head --sql`).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
