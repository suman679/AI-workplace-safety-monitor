from alembic import context
from sqlalchemy import create_engine

import app.models  # noqa: F401  (register all tables)
from app.core.config import get_settings
from app.database.base import Base

target_metadata = Base.metadata
url = get_settings().DATABASE_URL


def run_migrations_offline():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
