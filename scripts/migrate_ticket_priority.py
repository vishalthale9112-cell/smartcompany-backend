"""Idempotent one-time migration for live SmartCompany databases.

Run from the repository root:
    python scripts/migrate_ticket_priority.py
"""

from pathlib import Path
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app
from models import db


REQUIRED_COLUMNS = {
    'priority': "VARCHAR(20) NOT NULL DEFAULT 'medium'",
    'priority_confidence': 'FLOAT NULL',
    'priority_source': "VARCHAR(20) NOT NULL DEFAULT 'manual'",
}


def migrate():
    with app.app_context():
        existing = {column['name'] for column in inspect(db.engine).get_columns('tickets')}
        with db.engine.begin() as connection:
            for name, definition in REQUIRED_COLUMNS.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE tickets ADD COLUMN {name} {definition}'))
                    print(f'Added tickets.{name}')
                else:
                    print(f'Skipped tickets.{name}; already exists')


if __name__ == '__main__':
    migrate()
