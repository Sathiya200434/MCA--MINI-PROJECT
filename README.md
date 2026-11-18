# 🌿 Plant Nursery & Gardening Services Platform

An e-commerce platform for purchasing plants and booking expert gardening services, built with **Python Flask**, **MySQL 8.0**, and responsive botanical UI styling.

---

## 🏗️ Technology Stack

- **Backend:** Python Flask 3.0.3, Jinja2 template engine
- **Database:** MySQL 8.0 (Database: `plant_nursery`)
- **Database Connectors:** `mysql-connector-python` 26.7+ & `PyMySQL` 1.1+ (via `Flask-SQLAlchemy` 3.1+)
- **Security & Forms:** `python-dotenv`, `Werkzeug` password hashing, `Flask-WTF`, session-based RBAC
- **Frontend:** HTML5, CSS3 (Botanical Green palette: `#0D2818`, `#1B4332`, `#2D6A4F`, `#52B788`, `#D8F3DC`), Vanilla JavaScript

---

## 📁 Project Structure

```
plant_nursery/
│
├── .env                    # MySQL credentials and secret key (loaded securely)
├── .env.example            # Template for environment configuration
├── database.py             # Reusable MySQL connection, pooling, cursor & query module
├── database.sql            # Full MySQL 8.0 schema and seed dataset (12 core tables)
├── test_db.py              # Automated 8-step MySQL connection & module verification suite
├── config.py               # Flask configuration & environment variable loader
├── app.py                  # Full application routes, models, auth & business logic
├── requirements.txt        # Python package dependencies
│
├── static/
│   ├── css/style.css       # Clean botanical green UI styles & responsive grid layouts
│   ├── js/script.js        # Search, filters, modals, and dynamic interaction logic
│   └── images/             # Botanical plant and service image assets
│
└── templates/              # Jinja2 presentation templates
    ├── base.html, index.html, plants.html, plant_details.html
    ├── cart.html, checkout.html, order_success.html, orders.html, order_details.html
    ├── services.html, service_details.html, booking.html, bookings.html
    ├── feedback.html, profile.html, login.html, register.html, about.html, contact.html
    ├── seller/             # Seller dashboard, plant management, stock & order tracking
    └── admin/              # Admin dashboard, category, customer, seller, service & sales reports
```

---

## 🗄️ MySQL Database Setup

1. **Verify MySQL Server:**
   Ensure your local MySQL 8.0 service is running on `localhost:3306`.

2. **Configure `.env` File:**
   Ensure `.env` exists in the project root with your credentials:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=Root
   MYSQL_DB=plant_nursery
   SECRET_KEY=plant-nursery-production-secure-key-2026
   ```

3. **Verify Connection & Tables:**
   Run the automated database test suite:
   ```bash
   python test_db.py
   ```
   This performs all 8 checks:
   - MySQL server connection on localhost:3306
   - Database selection (`plant_nursery`)
   - Table verification for all 12 core tables
   - Record insertion (parameterized SQL)
   - Record retrieval
   - Record update & mutation
   - Safe deletion & transaction rollback
   - Flask application module connectivity

---

## 🚀 Running the Application

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize / Seed Data (Optional if already populated):**
   ```bash
   flask --app app.py init-db
   ```

3. **Start the Web Application:**
   ```bash
   python app.py
   ```
   Or via Flask CLI:
   ```bash
   flask run --host=127.0.0.1 --port=5000
   ```

4. **Access the Application in Browser:**
   Open **http://127.0.0.1:5000**

---

## 🔑 Demo User Credentials

| Role | Email | Password | Access / Capabilities |
|---|---|---|---|
| **Platform Admin** | `admin@nursery.com` | `admin123` | Platform analytics, users, categories, services, feedback & sales reports |
| **Seller** | `seller@nursery.com` | `seller123` | Plant catalog CRUD, stock management, order tracking & seller profile |
| **Customer** | `customer@nursery.com` | `customer123` | Plant catalog browsing, shopping cart, checkout (COD), service booking & feedback |

---

## 🛡️ Database Schema (12 Core Tables)

1. `users` — Customers, sellers, and administrators with role-based status and hashed passwords.
2. `categories` — Botanical categories (Indoor, Outdoor, Flower, Fruit, Medicinal, Succulents, Cactus, etc.).
3. `plants` — Plant inventory with botanical names, pricing, stock levels, sunlight/watering criteria, and ratings.
4. `cart` — Customer active cart session records.
5. `cart_items` — Relational cart lines linking customers/carts to specific plants and quantities.
6. `orders` — Customer orders with generated unique order tracking codes and delivery addresses.
7. `order_items` — Itemized line records linking orders, plants, and individual sellers.
8. `services` — Gardening and landscaping service packages with pricing, durations, and descriptions.
9. `service_bookings` — Customer service appointments with date/time slots and visit locations.
10. `feedback` — Customer 1–5 star reviews and written experiences.
11. `payments` — Transaction records with payment methods (Cash on Delivery) and payment states.
12. `notifications` — Role-based customer order updates and system notifications.
