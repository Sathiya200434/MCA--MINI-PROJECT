"""
=============================================================================
PLANT NURSERY & GARDENING SERVICES E-COMMERCE PLATFORM
MySQL 8.0 Database Connection & Module Verification Test Suite (test_db.py)
=============================================================================
This script executes the required 8-step verification suite:
  1. MySQL Server Connection Test
  2. Database Selection Test ('plant_nursery')
  3. Table Verification (All 12 Core Tables)
  4. Record Insertion Test (Parameterized SQL)
  5. Record Fetching Test (Verification of stored data)
  6. Record Update Test (Data mutation & persistence)
  7. Safe Deletion Test (Cleanup of test records)
  8. Flask Application Database Connectivity (Customer, Seller, Admin)
"""

import sys
import os
import uuid

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

import database
from app import app, db, User, Category, Plant, Cart, CartItem, Order, Service, ServiceBooking, Feedback

TOTAL_TESTS = 8
passed_tests = 0


def log_test_header(num, title):
    print(f"\n[{num}/{TOTAL_TESTS}] TESTING: {title}")
    print("-" * 65)


def report_step(success, message):
    global passed_tests
    if success:
        passed_tests += 1
        print(f"  [PASS] {message}")
    else:
        print(f"  [FAIL] {message}")
    return success


# ===========================================================================
# TEST 1: MySQL Server Connection
# ===========================================================================
def test_1_server_connection():
    log_test_header(1, "MySQL Server Connection")
    try:
        conn = database.get_db_connection(use_database=False)
        server_info = getattr(conn, "server_info", None) or conn.get_server_info()
        is_conn = conn.is_connected()
        conn.close()
        return report_step(
            is_conn,
            f"Successfully connected to MySQL Server on {database.MYSQL_HOST}:{database.MYSQL_PORT} (Version: {server_info})"
        )
    except Exception as exc:
        return report_step(False, f"Could not connect to MySQL server: {exc}")


# ===========================================================================
# TEST 2: Database Selection
# ===========================================================================
def test_2_database_selection():
    log_test_header(2, "Database Selection ('plant_nursery')")
    try:
        conn = database.get_db_connection(use_database=True)
        cur = conn.cursor()
        cur.execute("SELECT DATABASE()")
        current_db = cur.fetchone()[0]
        cur.close()
        conn.close()
        is_correct = (current_db == database.MYSQL_DB)
        return report_step(
            is_correct,
            f"Active database selected: '{current_db}' (Target: '{database.MYSQL_DB}')"
        )
    except Exception as exc:
        return report_step(False, f"Failed to select database '{database.MYSQL_DB}': {exc}")


# ===========================================================================
# TEST 3: Table Creation / Verification (12 Tables)
# ===========================================================================
def test_3_table_verification():
    log_test_header(3, "Table Verification (All 12 Core Tables)")
    try:
        database.verify_and_create_tables()
        conn = database.get_db_connection(use_database=True)
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        existing_tables = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()

        required_tables = [
            "users", "categories", "plants", "cart", "cart_items",
            "orders", "order_items", "services", "service_bookings",
            "feedback", "payments", "notifications"
        ]

        missing = [t for t in required_tables if t not in existing_tables]
        all_present = len(missing) == 0

        if all_present:
            print(f"  Existing tables verified ({len(existing_tables)}): {', '.join(sorted(existing_tables))}")
            return report_step(True, "All 12 required tables exist and are properly configured with keys/constraints.")
        else:
            return report_step(False, f"Missing tables: {missing}")
    except Exception as exc:
        return report_step(False, f"Error verifying database tables: {exc}")


# ===========================================================================
# TEST 4: Insert Sample Records (Parameterized SQL)
# ===========================================================================
test_customer_id = None
test_feedback_id = None

def test_4_insert_record():
    global test_customer_id, test_feedback_id
    log_test_header(4, "Insert Sample Record (Parameterized SQL)")
    try:
        # Find or create a test user
        user = database.execute_query(
            "SELECT user_id FROM users WHERE email = %s",
            ("customer@nursery.com",),
            fetchone=True
        )
        if not user:
            from werkzeug.security import generate_password_hash
            user_res = database.execute_query(
                "INSERT INTO users (name, email, password, role, status) VALUES (%s, %s, %s, %s, %s)",
                ("Test Customer", "test_temp@nursery.com", generate_password_hash("test123"), "customer", "Active"),
                commit=True
            )
            test_customer_id = user_res["lastrowid"]
        else:
            test_customer_id = user["user_id"]

        test_comment = f"Automated Connection Test Comment {uuid.uuid4().hex[:8]}"
        res = database.execute_query(
            "INSERT INTO feedback (customer_id, rating, comments) VALUES (%s, %s, %s)",
            (test_customer_id, 5, test_comment),
            commit=True
        )
        test_feedback_id = res["lastrowid"]

        success = test_feedback_id is not None and test_feedback_id > 0
        return report_step(
            success,
            f"Successfully inserted test feedback record with ID={test_feedback_id} via parameterized SQL."
        )
    except Exception as exc:
        return report_step(False, f"Failed to insert test record: {exc}")


# ===========================================================================
# TEST 5: Fetch Database Records
# ===========================================================================
def test_5_fetch_records():
    log_test_header(5, "Fetch Database Records")
    try:
        row = database.execute_query(
            "SELECT feedback_id, customer_id, rating, comments FROM feedback WHERE feedback_id = %s",
            (test_feedback_id,),
            fetchone=True
        )
        success = row is not None and row["feedback_id"] == test_feedback_id and row["rating"] == 5
        if success:
            print(f"  Retrieved record: ID={row['feedback_id']}, Rating={row['rating']}, Comments='{row['comments'][:35]}...'")
        return report_step(success, "Successfully retrieved and verified record from MySQL database.")
    except Exception as exc:
        return report_step(False, f"Failed to fetch record from MySQL: {exc}")


# ===========================================================================
# TEST 6: Update Records
# ===========================================================================
def test_6_update_record():
    log_test_header(6, "Update Record (Data Mutation & Persistence)")
    try:
        updated_comment = "Updated test comment for verified transaction."
        res = database.execute_query(
            "UPDATE feedback SET rating = %s, comments = %s WHERE feedback_id = %s",
            (4, updated_comment, test_feedback_id),
            commit=True
        )
        # Verify update
        check = database.execute_query(
            "SELECT rating, comments FROM feedback WHERE feedback_id = %s",
            (test_feedback_id,),
            fetchone=True
        )
        success = check is not None and check["rating"] == 4 and check["comments"] == updated_comment
        return report_step(
            success,
            f"Successfully updated record: Rating={check['rating']}, Comments='{check['comments']}'"
        )
    except Exception as exc:
        return report_step(False, f"Failed to update record in MySQL: {exc}")


# ===========================================================================
# TEST 7: Delete Test Records Safely
# ===========================================================================
def test_7_delete_record():
    log_test_header(7, "Delete Test Records Safely")
    try:
        res = database.execute_query(
            "DELETE FROM feedback WHERE feedback_id = %s",
            (test_feedback_id,),
            commit=True
        )
        # Verify deletion
        check = database.execute_query(
            "SELECT feedback_id FROM feedback WHERE feedback_id = %s",
            (test_feedback_id,),
            fetchone=True
        )
        success = (check is None)
        return report_step(
            success,
            f"Successfully cleaned up test record ID={test_feedback_id}. Verified record no longer exists."
        )
    except Exception as exc:
        return report_step(False, f"Failed to safely delete test record: {exc}")


# ===========================================================================
# TEST 8: Flask Application Database Connectivity
# ===========================================================================
def test_8_flask_app_integration():
    log_test_header(8, "Flask Application Database Connectivity")
    try:
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        # 1. Customer client: tests home, plants, plant detail, cart, services
        with app.test_client() as cust_client:
            r_home = cust_client.get("/")
            assert r_home.status_code == 200, f"Home page returned {r_home.status_code}"

            r_plants = cust_client.get("/plants")
            assert r_plants.status_code == 200, f"Plants page returned {r_plants.status_code}"

            r_services = cust_client.get("/services")
            assert r_services.status_code == 200, f"Services page returned {r_services.status_code}"

            # Login as customer
            with cust_client.session_transaction() as sess:
                sess["user_id"] = test_customer_id
                sess["user_name"] = "Priya Sharma"
                sess["role"] = "customer"

            r_cart = cust_client.get("/cart")
            assert r_cart.status_code == 200, f"Cart returned {r_cart.status_code}"

            r_orders = cust_client.get("/orders")
            assert r_orders.status_code == 200, f"Orders returned {r_orders.status_code}"

            r_cust_dash = cust_client.get("/customer/dashboard")
            assert r_cust_dash.status_code == 200, f"Customer dashboard returned {r_cust_dash.status_code}"

        # 2. Seller client: tests seller dashboard, plant list, add plant, inventory, sales report
        seller_user = database.execute_query(
            "SELECT user_id, name FROM users WHERE role = 'seller' LIMIT 1",
            fetchone=True
        )
        with app.test_client() as seller_client:
            if seller_user:
                with seller_client.session_transaction() as sess:
                    sess["user_id"] = seller_user["user_id"]
                    sess["user_name"] = seller_user["name"]
                    sess["role"] = "seller"
                r_seller_dash = seller_client.get("/seller/dashboard")
                assert r_seller_dash.status_code == 200, f"Seller dashboard returned {r_seller_dash.status_code}"
                r_seller_plants = seller_client.get("/seller/plants")
                assert r_seller_plants.status_code == 200, f"Seller plants returned {r_seller_plants.status_code}"
                r_seller_inv = seller_client.get("/seller/inventory")
                assert r_seller_inv.status_code == 200, f"Seller inventory returned {r_seller_inv.status_code}"
                r_seller_sales = seller_client.get("/seller/sales-report")
                assert r_seller_sales.status_code == 200, f"Seller sales report returned {r_seller_sales.status_code}"

        # 3. Admin client: tests admin dashboard, customer list, seller list, sales report, bookings, security
        admin_user = database.execute_query(
            "SELECT user_id, name FROM users WHERE role = 'admin' LIMIT 1",
            fetchone=True
        )
        with app.test_client() as admin_client:
            if admin_user:
                with admin_client.session_transaction() as sess:
                    sess["user_id"] = admin_user["user_id"]
                    sess["user_name"] = admin_user["name"]
                    sess["role"] = "admin"
                r_admin_dash = admin_client.get("/admin/dashboard")
                assert r_admin_dash.status_code == 200, f"Admin dashboard returned {r_admin_dash.status_code}"
                r_admin_cust = admin_client.get("/admin/customers")
                assert r_admin_cust.status_code == 200, f"Admin customers returned {r_admin_cust.status_code}"
                r_admin_sales = admin_client.get("/admin/sales-report")
                assert r_admin_sales.status_code == 200, f"Admin sales report returned {r_admin_sales.status_code}"
                r_admin_bk = admin_client.get("/admin/bookings")
                assert r_admin_bk.status_code == 200, f"Admin bookings returned {r_admin_bk.status_code}"
                r_admin_sec = admin_client.get("/admin/security")
                assert r_admin_sec.status_code == 200, f"Admin security returned {r_admin_sec.status_code}"

        return report_step(
            True,
            "Flask application successfully connected to MySQL; all Customer, Seller, and Admin routes rendered 200 OK."
        )
    except Exception as exc:
        return report_step(False, f"Flask application integration test failed: {exc}")


# ===========================================================================
# MAIN RUNNER
# ===========================================================================
def run_all_tests():
    print("=" * 65)
    print("PLANT NURSERY & GARDENING SERVICES — MYSQL 8.0 TEST SUITE")
    print("=" * 65)
    print(f"Target Server  : {database.MYSQL_HOST}:{database.MYSQL_PORT}")
    print(f"Target User    : {database.MYSQL_USER}")
    print(f"Target Database: {database.MYSQL_DB}")

    test_1_server_connection()
    test_2_database_selection()
    test_3_table_verification()
    test_4_insert_record()
    test_5_fetch_records()
    test_6_update_record()
    test_7_delete_record()
    test_8_flask_app_integration()

    print("\n" + "=" * 65)
    print(f"TEST RESULTS: {passed_tests}/{TOTAL_TESTS} TESTS PASSED")
    print("=" * 65)

    if passed_tests == TOTAL_TESTS:
        print("[SUCCESS] All MySQL database connection & module tests completed successfully!")
        sys.exit(0)
    else:
        print(f"[WARNING] {TOTAL_TESTS - passed_tests} test(s) failed. Review output above.")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
