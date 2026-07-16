from __future__ import annotations

from sqlite3 import Connection

from backend.app.db.connection import get_connection
from backend.app.db.seed_data import get_seed_items


def create_tables(conn: Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sale_sessions (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            current_step TEXT NOT NULL,
            state_json TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reference_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            product_type TEXT NOT NULL,
            brand TEXT,
            model TEXT,
            condition_level TEXT NOT NULL,
            age_months INTEGER NOT NULL,
            original_price REAL NOT NULL,
            listing_price REAL NOT NULL,
            sold_price REAL NOT NULL,
            accessories_complete BOOLEAN NOT NULL,
            description TEXT NOT NULL,
            source_name TEXT DEFAULT '内置模拟数据',
            source_type TEXT DEFAULT 'seed',
            source_url TEXT,
            imported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            user_notes TEXT,
            disabled_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS negotiation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            buyer_message TEXT NOT NULL,
            intent TEXT NOT NULL,
            suggested_reply TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sale_sessions(id) ON DELETE CASCADE
        );
        """
    )


def migrate_reference_items(conn: Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(reference_items)").fetchall()}
    migrations = {
        "source_name": "ALTER TABLE reference_items ADD COLUMN source_name TEXT DEFAULT '内置模拟数据'",
        "source_type": "ALTER TABLE reference_items ADD COLUMN source_type TEXT DEFAULT 'seed'",
        "source_url": "ALTER TABLE reference_items ADD COLUMN source_url TEXT",
        "imported_at": "ALTER TABLE reference_items ADD COLUMN imported_at DATETIME",
        "active": "ALTER TABLE reference_items ADD COLUMN active BOOLEAN DEFAULT 1",
        "user_notes": "ALTER TABLE reference_items ADD COLUMN user_notes TEXT",
        "disabled_at": "ALTER TABLE reference_items ADD COLUMN disabled_at DATETIME",
    }
    for column, statement in migrations.items():
        if column not in columns:
            conn.execute(statement)
    conn.execute("UPDATE reference_items SET source_name = '内置模拟数据' WHERE source_name IS NULL")
    conn.execute("UPDATE reference_items SET source_type = 'seed' WHERE source_type IS NULL")
    conn.execute("UPDATE reference_items SET active = 1 WHERE active IS NULL")


def seed_reference_items(conn: Connection) -> None:
    existing_rows = conn.execute(
        """
        SELECT category, product_type, brand, model, condition_level
        FROM reference_items
        """
    ).fetchall()
    existing_keys = {
        (
            row["category"],
            row["product_type"],
            row["brand"],
            row["model"],
            row["condition_level"],
        )
        for row in existing_rows
    }

    items = [
        item
        for item in get_seed_items()
        if (item.category, item.product_type, item.brand, item.model, item.condition_level) not in existing_keys
    ]
    if not items:
        return
    conn.executemany(
        """
        INSERT INTO reference_items (
            category, product_type, brand, model, condition_level, age_months,
            original_price, listing_price, sold_price, accessories_complete, description,
            source_name, source_type, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                item.category,
                item.product_type,
                item.brand,
                item.model,
                item.condition_level,
                item.age_months,
                item.original_price,
                item.listing_price,
                item.sold_price,
                int(item.accessories_complete),
                item.description,
                "内置模拟数据",
                "seed",
                None,
            )
            for item in items
        ],
    )


def init_database() -> None:
    with get_connection() as conn:
        create_tables(conn)
        migrate_reference_items(conn)
        seed_reference_items(conn)
        conn.commit()


if __name__ == "__main__":
    init_database()
    print("ReSale Agent 数据库初始化完成。")
