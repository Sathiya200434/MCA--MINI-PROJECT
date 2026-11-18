"""
=============================================================================
PLANT NURSERY & GARDENING SERVICES E-COMMERCE PLATFORM
MySQL 8.0 Database Connection & Query Execution Module (database.py)
=============================================================================
This module provides a direct, production-grade MySQL connection using
`mysql-connector-python`. It reads credentials securely from `.env`, provides
connection pooling/handling, safe parameterized query execution, transactions
(commit/rollback), cursor management, and automated database/table verification.
"""

import os
import sys
import logging
from contextlib import contextmanager
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

# Set up logger
logger = logging.getLogger("plant_nursery.database")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Load environment variables from .env file
# Look in current working directory and project root
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Database Configuration (Read strictly from environment / .env)
# ---------------------------------------------------------------------------
MYSQL_HOST     = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER     = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Root")
MYSQL_DB       = os.environ.get("MYSQL_DB", "plant_nursery")


def get_connection_config(use_database=True):
    """
    Returns MySQL connection parameter dictionary.
    """
    config = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connect_timeout": 10,
        "autocommit": False,
    }
    if use_database and MYSQL_DB:
        config["database"] = MYSQL_DB
    return config


def get_db_connection(use_database=True):
    """
    Establishes and returns a direct connection to the MySQL 8.0 server.
    Handles connection errors with actionable error reporting.
    """
    cfg = get_connection_config(use_database=use_database)
    try:
        conn = mysql.connector.connect(**cfg)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("MySQL Auth Failed: Invalid username or password in .env (user='%s')", MYSQL_USER)
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("MySQL Database '%s' does not exist.", MYSQL_DB)
        else:
            logger.error("MySQL Connection Error [%s]: %s", err.errno, err.msg)
        raise


@contextmanager
def get_db_cursor(dictionary=True, commit=False):
    """
    Context manager for database connections and cursors.
    Ensures safe transaction commit, rollback on error, and proper closing.
    
    Usage:
        with get_db_cursor(dictionary=True, commit=True) as (conn, cur):
            cur.execute("INSERT INTO feedback (customer_id, rating, comments) VALUES (%s, %s, %s)", (1, 5, 'Great'))
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection(use_database=True)
        cur = conn.cursor(dictionary=dictionary)
        yield conn, cur
        if commit:
            conn.commit()
    except Exception as exc:
        if conn and conn.is_connected():
            try:
                conn.rollback()
                logger.warning("Transaction rolled back due to error: %s", exc)
            except Exception as rb_err:
                logger.error("Rollback failed: %s", rb_err)
        raise exc
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False, dictionary=True):
    """
    Executes a safe parameterized SQL query with automatic connection/cursor
    lifecycle, commit/rollback, and result retrieval.
    
    :param query: SQL statement with '%s' parameter placeholders.
    :param params: Tuple or list of parameters (prevents SQL injection).
    :param fetchone: If True, returns a single dictionary row or None.
    :param fetchall: If True, returns a list of dictionary rows.
    :param commit: If True, commits the transaction (INSERT, UPDATE, DELETE).
    :param dictionary: If True, results are mapped as dictionaries {col_name: val}.
    :return: Row, rows, or lastrowid / rowcount depending on parameters.
    """
    with get_db_cursor(dictionary=dictionary, commit=commit) as (conn, cur):
        cur.execute(query, params or ())
        if commit:
            return {
                "lastrowid": cur.lastrowid,
                "rowcount": cur.rowcount
            }
        if fetchone:
            return cur.fetchone()
        if fetchall:
            return cur.fetchall()
        return None


# ===========================================================================
# DATABASE CREATION & VERIFICATION (Step 3)
# ===========================================================================

def verify_and_create_database():
    """
    Checks whether 'plant_nursery' database exists on the MySQL server.
    If it does not exist, creates it with utf8mb4 encoding.
    """
    conn = None
    try:
        conn = get_db_connection(use_database=False)
        cur = conn.cursor()
        cur.execute("SHOW DATABASES LIKE %s", (MYSQL_DB,))
        exists = cur.fetchone()
        if not exists:
            logger.info("Database '%s' does not exist. Creating database...", MYSQL_DB)
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            logger.info("Database '%s' created successfully.", MYSQL_DB)
        else:
            logger.info("Database '%s' verified (already exists).", MYSQL_DB)
        cur.close()
        return True
    finally:
        if conn and conn.is_connected():
            conn.close()


REQUIRED_TABLES_SQL = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(20),
            address VARCHAR(255),
            role ENUM('customer', 'seller', 'admin') NOT NULL DEFAULT 'customer',
            status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_email (email),
            INDEX idx_user_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "categories": """
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            INDEX idx_category_name (category_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "plants": """
        CREATE TABLE IF NOT EXISTS plants (
            plant_id INT AUTO_INCREMENT PRIMARY KEY,
            seller_id INT NOT NULL,
            category_id INT NOT NULL,
            plant_name VARCHAR(150) NOT NULL,
            botanical_name VARCHAR(150),
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL DEFAULT 0,
            image VARCHAR(255) DEFAULT 'default_plant.jpg',
            availability VARCHAR(50) DEFAULT 'In Stock',
            sunlight VARCHAR(100),
            watering VARCHAR(100),
            rating DECIMAL(2,1) DEFAULT 4.5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
            INDEX idx_plant_seller (seller_id),
            INDEX idx_plant_category (category_id),
            INDEX idx_plant_price (price),
            INDEX idx_plant_stock (stock)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "cart": """
        CREATE TABLE IF NOT EXISTS cart (
            cart_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_cart_customer (customer_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "cart_items": """
        CREATE TABLE IF NOT EXISTS cart_items (
            cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
            cart_id INT NULL,
            customer_id INT NULL,
            plant_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cart_id) REFERENCES cart(cart_id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE CASCADE,
            INDEX idx_cart_item_cart (cart_id),
            INDEX idx_cart_item_customer (customer_id),
            INDEX idx_cart_item_plant (plant_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            order_code VARCHAR(30) UNIQUE,
            customer_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            delivery_address VARCHAR(255) NOT NULL,
            payment_method VARCHAR(50) NOT NULL DEFAULT 'Cash on Delivery',
            payment_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            order_status VARCHAR(30) NOT NULL DEFAULT 'Processing',
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_orders_customer (customer_id),
            INDEX idx_orders_status (order_status),
            INDEX idx_orders_date (order_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "order_items": """
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            plant_id INT NOT NULL,
            seller_id INT,
            quantity INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (plant_id) REFERENCES plants(plant_id) ON DELETE RESTRICT,
            FOREIGN KEY (seller_id) REFERENCES users(user_id) ON DELETE SET NULL,
            INDEX idx_order_item_order (order_id),
            INDEX idx_order_item_plant (plant_id),
            INDEX idx_order_item_seller (seller_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "services": """
        CREATE TABLE IF NOT EXISTS services (
            service_id INT AUTO_INCREMENT PRIMARY KEY,
            service_name VARCHAR(150) NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            duration VARCHAR(50),
            image VARCHAR(255) DEFAULT 'default_service.jpg',
            status VARCHAR(50) DEFAULT 'Available',
            INDEX idx_service_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "service_bookings": """
        CREATE TABLE IF NOT EXISTS service_bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            service_id INT NOT NULL,
            customer_name VARCHAR(120),
            phone VARCHAR(20),
            booking_date VARCHAR(20) NOT NULL,
            booking_time VARCHAR(20) NOT NULL,
            address VARCHAR(255) NOT NULL,
            requirements TEXT,
            booking_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
            INDEX idx_booking_customer (customer_id),
            INDEX idx_booking_status (booking_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "feedback": """
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            rating INT NOT NULL DEFAULT 5,
            comments TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_feedback_customer (customer_id),
            INDEX idx_feedback_rating (rating)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "payments": """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            INDEX idx_payment_order (order_id),
            INDEX idx_payment_status (payment_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """,
    "notifications": """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_notification_user (user_id),
            INDEX idx_notification_read (is_read)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
}


def verify_and_create_tables():
    """
    Verifies that all 12 required tables exist in 'plant_nursery'.
    Creates any missing table safely without modifying or deleting existing data.
    Also ensures required compatibility columns (e.g. cart_items.customer_id) exist.
    """
    verify_and_create_database()

    with get_db_cursor(dictionary=False, commit=True) as (conn, cur):
        # 1. Create any missing tables from the 12 core tables
        for table_name, create_sql in REQUIRED_TABLES_SQL.items():
            cur.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not cur.fetchone():
                logger.info("Table '%s' not found. Creating table...", table_name)
                cur.execute(create_sql)
                logger.info("Table '%s' created successfully.", table_name)
            else:
                logger.info("Table '%s' verified.", table_name)

        # 2. Check compatibility columns on cart_items
        cur.execute("SHOW COLUMNS FROM cart_items LIKE 'customer_id'")
        if not cur.fetchone():
            logger.info("Adding 'customer_id' column to 'cart_items' for direct user cart compatibility...")
            cur.execute("""
                ALTER TABLE cart_items 
                ADD COLUMN customer_id INT NULL AFTER cart_id,
                ADD CONSTRAINT fk_cart_items_customer FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE
            """)

        cur.execute("SHOW COLUMNS FROM cart_items LIKE 'cart_id'")
        cart_id_col = cur.fetchone()
        if cart_id_col and cart_id_col[2] == 'NO':  # If cart_id was NOT NULL, make it nullable
            try:
                cur.execute("ALTER TABLE cart_items MODIFY COLUMN cart_id INT NULL")
            except Exception:
                pass

        cur.execute("SHOW COLUMNS FROM cart_items LIKE 'created_at'")
        if not cur.fetchone():
            try:
                cur.execute("ALTER TABLE cart_items ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            except Exception:
                pass

    logger.info("All 12 tables and schemas verified successfully in MySQL.")
    return True


def seed_sample_data_if_empty():
    """
    Seeds initial records for categories, default users, plants, and services
    if the tables are currently empty, without overriding any existing data.
    """
    from werkzeug.security import generate_password_hash

    with get_db_cursor(dictionary=True, commit=True) as (conn, cur):
        # Check users
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        if cur.fetchone()["cnt"] == 0:
            logger.info("Seeding initial users...")
            hashed_pwd = generate_password_hash("password123")
            users_data = [
                ('Platform Admin', 'admin@nursery.com', hashed_pwd, '+91 99999 88888', 'HQ Green City', 'admin', 'Active'),
                ('Green Leaf Nursery', 'seller@nursery.com', hashed_pwd, '+91 88888 77777', 'Plot 42 Botanical Road, Chennai', 'seller', 'Active'),
                ('Priya Sharma', 'customer@nursery.com', hashed_pwd, '+91 98765 43210', 'Flat 302 Palm Meadows, Chennai', 'customer', 'Active')
            ]
            cur.executemany("""
                INSERT INTO users (name, email, password, phone, address, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, users_data)

        # Check categories
        cur.execute("SELECT COUNT(*) AS cnt FROM categories")
        if cur.fetchone()["cnt"] == 0:
            logger.info("Seeding initial categories...")
            cats = [
                ('Indoor Plants', 'Shade-loving, air-purifying plants ideal for apartments'),
                ('Outdoor Plants', 'Sunlight-thriving shrubs and landscaping varieties'),
                ('Flower Plants', 'Fragrant, blooming ornamental plants and seasonal flowers'),
                ('Fruit Plants', 'Healthy grafted saplings yielding fresh fruits'),
                ('Vegetable Plants', 'Heirloom organic kitchen garden vegetables and fresh herbs'),
                ('Medicinal Plants', 'Ayurvedic therapeutic herbs and natural wellness plants'),
                ('Succulents', 'Drought-tolerant, low-maintenance geometric rosettes'),
                ('Cactus', 'Resilient desert-adapted spined varieties')
            ]
            cur.executemany("INSERT INTO categories (category_name, description) VALUES (%s, %s)", cats)

    logger.info("Database verification and seeding complete.")


def test_connection():
    """
    Comprehensive diagnostic test function for terminal verification.
    """
    results = {
        "server_connected": False,
        "database_selected": False,
        "tables_verified": False,
        "tables_count": 0,
        "error": None
    }
    try:
        conn = get_db_connection(use_database=True)
        results["server_connected"] = True
        cur = conn.cursor()
        cur.execute("SELECT DATABASE()")
        db_name = cur.fetchone()[0]
        if db_name == MYSQL_DB:
            results["database_selected"] = True
        cur.execute("SHOW TABLES")
        tables = [r[0] for r in cur.fetchall()]
        results["tables_count"] = len(tables)
        results["tables"] = tables
        cur.close()
        conn.close()
        results["tables_verified"] = all(
            tbl in tables for tbl in REQUIRED_TABLES_SQL.keys()
        )
    except Exception as e:
        results["error"] = str(e)
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("PLANT NURSERY — DIRECT MYSQL 8.0 CONNECTION & VERIFICATION")
    print("=" * 70)
    try:
        verify_and_create_tables()
        seed_sample_data_if_empty()
        res = test_connection()
        print(f"Server Connection: {'[SUCCESS]' if res['server_connected'] else '[FAILED]'}")
        print(f"Database Selected: {MYSQL_DB} ({'YES' if res['database_selected'] else 'NO'})")
        print(f"Required Tables  : {'[ALL VERIFIED]' if res['tables_verified'] else '[INCOMPLETE]'}")
        print(f"Total Tables     : {res['tables_count']}")
    except Exception as err:
        print(f"[ERROR] Database initialization failed: {err}")
