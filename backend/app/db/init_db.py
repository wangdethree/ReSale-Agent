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
            description TEXT NOT NULL
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


def seed_reference_items(conn: Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) AS count FROM reference_items").fetchone()["count"]
    if existing:
        return

    items = get_seed_items()
    conn.executemany(
        """
        INSERT INTO reference_items (
            category, product_type, brand, model, condition_level, age_months,
            original_price, listing_price, sold_price, accessories_complete, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            )
            for item in items
        ],
    )


def init_database() -> None:
    with get_connection() as conn:
        create_tables(conn)
        seed_reference_items(conn)
        conn.commit()


if __name__ == "__main__":
    init_database()
    print("ReSale Agent 数据库初始化完成。")

