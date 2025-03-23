import sqlite3
from datetime import datetime, timedelta

class FoodDatabase:
    def __init__(self, db_name="food_inventory.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER DEFAULT 1,
            expiration_date TEXT,
            barcode TEXT UNIQUE,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def add_item(self, name, category, quantity, expiration_date, barcode=None):
        query = """
        INSERT INTO food_items (name, category, quantity, expiration_date, barcode)
        VALUES (?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (name, category, quantity, expiration_date, barcode))
        self.conn.commit()

    def get_all_items(self):
        query = "SELECT * FROM food_items WHERE date('now') <= expiration_date"
        return self.conn.execute(query).fetchall()

    def get_expiring_items(self):
        query = "SELECT * FROM food_items WHERE expiration_date <= date('now', '+3 days')"
        return self.conn.execute(query).fetchall()

    def delete_item(self, item_id):
        query = "DELETE FROM food_items WHERE id = ?"
        self.conn.execute(query, (item_id,))
        self.conn.commit()
