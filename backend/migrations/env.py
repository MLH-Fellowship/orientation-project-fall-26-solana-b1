from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def check_foreign_keys(connection):
    if connection.dialect.name == "sqlite":
        violations = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
        if violations:
            tables = ", ".join(sorted({row[0] for row in violations}))
            raise RuntimeError(
                f"SQLite foreign-key violations in: {tables}. "
                "Back up the database and repair invalid references before retrying; "
                "no automatic data cleanup is performed."
            )


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            is_sqlite = connection.dialect.name == "sqlite"
            if is_sqlite:
                # Batch rebuilds drop referenced tables; enforcement can cascade-delete rows.
                connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
                if connection.exec_driver_sql("PRAGMA foreign_keys").scalar() != 0:
                    raise RuntimeError("Cannot disable SQLite foreign keys for migration")
                connection.commit()

            with connection.begin():
                if is_sqlite:
                    # Explicit BEGIN makes SQLite DDL roll back if integrity checks fail.
                    connection.exec_driver_sql("BEGIN")
                check_foreign_keys(connection)
                context.configure(
                    connection=connection,
                    target_metadata=target_metadata,
                    render_as_batch=True,
                    transactional_ddl=True if is_sqlite else None,
                )

                with context.begin_transaction():
                    context.run_migrations()
                    check_foreign_keys(connection)
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
