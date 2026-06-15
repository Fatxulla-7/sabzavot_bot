import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "sabzavot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Ma'lumotlar bazasini yaratish va jadvallarni sozlash"""
    conn = get_connection()
    cursor = conn.cursor()

    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,
            chat_id     INTEGER UNIQUE NOT NULL,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            phone       TEXT NOT NULL,
            address     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    # Sabzavotlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            price      INTEGER NOT NULL,
            photo_id   TEXT NOT NULL,
            is_active  INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    # Buyurtmalar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            product_id     INTEGER NOT NULL,
            quantity        REAL NOT NULL,
            total_price    INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(chat_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Ma'lumotlar bazasi tayyor!")

# ===================== FOYDALANUVCHILAR =====================

def save_user(chat_id, first_name, last_name, phone, address):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO users (chat_id, first_name, last_name, phone, address, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (chat_id, first_name, last_name, phone, address, now))
    conn.commit()
    conn.close()

def get_user(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ===================== SABZAVOTLAR =====================

def add_product(name, price, photo_id):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO products (name, price, photo_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (name, price, photo_id, now))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_product_name(product_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
    conn.commit()
    conn.close()

def update_product_price(product_id, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
    conn.commit()
    conn.close()

def update_product_photo(product_id, photo_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET photo_id = ? WHERE id = ?", (photo_id, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

# ===================== BUYURTMALAR =====================

def save_order(user_id, product_id, quantity, total_price, payment_method):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO orders (user_id, product_id, quantity, total_price, payment_method, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, product_id, quantity, total_price, payment_method, now))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, p.name as product_name
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    """, (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, u.first_name, u.last_name, u.phone, u.address, p.name as product_name
        FROM orders o
        JOIN users u ON o.user_id = u.chat_id
        JOIN products p ON o.product_id = p.id
        ORDER BY o.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]