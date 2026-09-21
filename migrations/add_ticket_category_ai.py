"""Safe MySQL migration for AI ticket category metadata.

Run this once against the existing database before deploying the new backend.
It checks information_schema first, so existing columns are not recreated.
"""

import os

from sqlalchemy import create_engine, text


def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required")

    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+mysqlconnector://", 1)

    engine = create_engine(database_url)

    statements = [
        (
            "category_confidence",
            "ALTER TABLE tickets ADD COLUMN category_confidence FLOAT NULL",
        ),
        (
            "category_source",
            "ALTER TABLE tickets ADD COLUMN category_source VARCHAR(20) NOT NULL DEFAULT 'manual'",
        ),
    ]

    with engine.begin() as connection:
        for column_name, statement in statements:
            exists = connection.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'tickets'
                      AND column_name = :column_name
                    """
                ),
                {"column_name": column_name},
            ).scalar()

            if not exists:
                connection.execute(text(statement))
                print(f"Added tickets.{column_name}")
            else:
                print(f"tickets.{column_name} already exists; skipped")


if __name__ == "__main__":
    main()
