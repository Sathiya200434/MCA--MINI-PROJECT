"""
Plant Nursery & Gardening Services E-Commerce Platform
Full-Stack Python Flask + MySQL 8.0 Integration
Role-Based Architecture: Customer, Seller, Admin, Security Modules
"""

import os
import random
import socket
import string
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, abort)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config

# ---------------------------------------------------------------------------
# App & Database Configuration with MySQL 8.0 & Graceful Fallback
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# Check if MySQL 8.0 server is reachable on the configured host/port
def is_mysql_reachable(host, port, timeout=1.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0
    except Exception:
        return False

# Use MySQL 8.0 if accessible; otherwise fallback to SQLite for offline/sandboxed development
if not is_mysql_reachable(Config.MYSQL_HOST, Config.MYSQL_PORT):
    sqlite_path = os.path.join(app.root_path, "plant_nursery.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "images", "plants")
app.config["SERVICE_UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "images", "services")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["SERVICE_UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(os.path.join(app.root_path, "static", "images", "categories"), exist_ok=True)

db = SQLAlchemy(app)


# ===========================================================================
# 12 DATABASE MODELS (MATCHING MYSQL 8.0 ARCHITECTURE & PROJECT DOCS)
# ===========================================================================

class User(db.Model):
    __tablename__ = "users"
    id         = db.Column("user_id", db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    phone      = db.Column(db.String(20))
    address    = db.Column(db.String(255))
    role       = db.Column(db.Enum("customer", "seller", "admin", name="user_role"),
                           nullable=False, default="customer")
    status     = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    plants        = db.relationship("Plant", backref="seller", lazy=True, cascade="all, delete-orphan")
    orders        = db.relationship("Order", backref="customer", lazy=True)
    carts         = db.relationship("Cart", backref="cart_customer", lazy=True, cascade="all, delete-orphan")
    cart_items    = db.relationship("CartItem", backref="user", lazy=True, cascade="all, delete-orphan")
    bookings      = db.relationship("ServiceBooking", backref="user", lazy=True)
    feedbacks     = db.relationship("Feedback", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    @property
    def user_id(self):
        return self.id


class Category(db.Model):
    __tablename__ = "categories"
    id          = db.Column("category_id", db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column("category_name", db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    plants = db.relationship("Plant", backref="category", lazy=True)

    @property
    def category_id(self):
        return self.id

    @property
    def category_name(self):
        return self.name


class Plant(db.Model):
    __tablename__ = "plants"
    id             = db.Column("plant_id", db.Integer, primary_key=True, autoincrement=True)
    seller_id      = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    category_id    = db.Column(db.Integer, db.ForeignKey("categories.category_id"), nullable=False)
    name           = db.Column("plant_name", db.String(150), nullable=False)
    botanical_name = db.Column(db.String(150))
    description    = db.Column(db.Text)
    price          = db.Column(db.Float, nullable=False)
    stock          = db.Column(db.Integer, default=0)
    image          = db.Column(db.String(255), default="default_plant.jpg")
    availability   = db.Column(db.String(50), default="In Stock")
    sunlight       = db.Column(db.String(100))
    watering       = db.Column(db.String(100))
    rating         = db.Column(db.Float, default=4.5)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    cart_entries  = db.relationship("CartItem", backref="plant", lazy=True)
    order_entries = db.relationship("OrderItem", backref="plant", lazy=True)

    @property
    def plant_id(self):
        return self.id

    @property
    def plant_name(self):
        return self.name


class Cart(db.Model):
    __tablename__ = "cart"
    id          = db.Column("cart_id", db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column("customer_id", db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("CartItem", backref="cart_rel", lazy=True, cascade="all, delete-orphan")

    @property
    def cart_id(self):
        return self.id

    @property
    def user_id(self):
        return self.customer_id


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id         = db.Column("cart_item_id", db.Integer, primary_key=True, autoincrement=True)
    cart_id    = db.Column("cart_id", db.Integer, db.ForeignKey("cart.cart_id"), nullable=True)
    user_id    = db.Column("customer_id", db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    plant_id   = db.Column(db.Integer, db.ForeignKey("plants.plant_id"), nullable=False)
    quantity   = db.Column(db.Integer, default=1, nullable=False)
    price      = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def cart_item_id(self):
        return self.id

    @property
    def customer_id(self):
        return self.user_id


class Order(db.Model):
    __tablename__ = "orders"
    id               = db.Column("order_id", db.Integer, primary_key=True, autoincrement=True)
    order_code       = db.Column(db.String(30), unique=True)
    customer_id      = db.Column("customer_id", db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    total_amount     = db.Column(db.Float, nullable=False)
    delivery_address = db.Column("delivery_address", db.String(255), nullable=False)
    payment_method   = db.Column(db.String(50), default="Cash on Delivery")
    payment_status   = db.Column(db.String(30), default="Pending")
    order_status     = db.Column("order_status", db.String(30), default="Processing")
    order_date       = db.Column(db.DateTime, default=datetime.utcnow)

    items    = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="order", lazy=True, cascade="all, delete-orphan")

    @property
    def order_id(self):
        return self.id

    @property
    def user_id(self):
        return self.customer_id

    @property
    def address(self):
        return self.delivery_address

    @address.setter
    def address(self, val):
        self.delivery_address = val

    @property
    def status(self):
        return self.order_status

    @status.setter
    def status(self, val):
        self.order_status = val


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id        = db.Column("order_item_id", db.Integer, primary_key=True, autoincrement=True)
    order_id  = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    plant_id  = db.Column(db.Integer, db.ForeignKey("plants.plant_id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    quantity  = db.Column(db.Integer, nullable=False)
    price     = db.Column(db.Float, nullable=False)

    seller = db.relationship("User", foreign_keys=[seller_id], lazy=True)

    @property
    def order_item_id(self):
        return self.id


class Service(db.Model):
    __tablename__ = "services"
    id          = db.Column("service_id", db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column("service_name", db.String(150), nullable=False)
    description = db.Column(db.Text)
    price       = db.Column(db.Float, nullable=False)
    duration    = db.Column(db.String(50))
    status      = db.Column("status", db.String(50), default="Available")
    image       = db.Column(db.String(255), default="default_service.jpg")

    bookings = db.relationship("ServiceBooking", backref="service", lazy=True)

    @property
    def service_id(self):
        return self.id

    @property
    def service_name(self):
        return self.name

    @property
    def availability(self):
        return self.status

    @availability.setter
    def availability(self, val):
        self.status = val


class ServiceBooking(db.Model):
    __tablename__ = "service_bookings"
    id             = db.Column("booking_id", db.Integer, primary_key=True, autoincrement=True)
    customer_id    = db.Column("customer_id", db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    service_id     = db.Column(db.Integer, db.ForeignKey("services.service_id"), nullable=False)
    customer_name  = db.Column(db.String(120))
    phone          = db.Column(db.String(20))
    booking_date   = db.Column(db.String(20), nullable=False)
    booking_time   = db.Column(db.String(20), nullable=False)
    address        = db.Column(db.String(255), nullable=False)
    requirements   = db.Column(db.Text)
    booking_status = db.Column("booking_status", db.String(30), default="Pending")
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def booking_id(self):
        return self.id

    @property
    def user_id(self):
        return self.customer_id

    @property
    def status(self):
        return self.booking_status

    @status.setter
    def status(self, val):
        self.booking_status = val

    @property
    def notes(self):
        return self.requirements

    @notes.setter
    def notes(self, val):
        self.requirements = val


class Feedback(db.Model):
    __tablename__ = "feedback"
    id          = db.Column("feedback_id", db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column("customer_id", db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    rating      = db.Column(db.Integer, default=5, nullable=False)
    comments    = db.Column("comments", db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def feedback_id(self):
        return self.id

    @property
    def user_id(self):
        return self.customer_id

    @property
    def message(self):
        return self.comments

    @message.setter
    def message(self, val):
        self.comments = val


class Payment(db.Model):
    __tablename__ = "payments"
    id               = db.Column("payment_id", db.Integer, primary_key=True, autoincrement=True)
    order_id         = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    payment_method   = db.Column(db.String(50), nullable=False)
    amount           = db.Column(db.Float, nullable=False)
    payment_status   = db.Column(db.String(30), default="Pending")
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def payment_id(self):
        return self.id


class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column("notification_id", db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def notification_id(self):
        return self.id


# ===========================================================================
# SECURITY & RBAC HELPERS
# ===========================================================================

def login_required(role=None):
    """Decorator: verifies session auth and Role-Based Access Control."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Unauthorized access. You do not have permissions for this page.", "error")
                abort(403)
            # Verify user account is still active
            user = db.session.get(User, session["user_id"])
            if not user or user.status == "Inactive":
                session.clear()
                flash("Your account has been deactivated. Please contact administrator.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator


def current_user():
    """Return the currently authenticated User model object or None."""
    if "user_id" in session:
        return db.session.get(User, session["user_id"])
    return None


def generate_order_code():
    """Generate a clean unique order tracking code (e.g. ORD84729103)."""
    return "ORD" + "".join(random.choices(string.digits, k=8))


def allowed_file(filename):
    """Validate file extension against allowed image types."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def save_upload(file_obj, folder):
    """Securely save an uploaded image file with collision prevention."""
    clean_name = secure_filename(file_obj.filename)
    unique_name = f"{int(datetime.utcnow().timestamp())}_{clean_name}"
    file_obj.save(os.path.join(folder, unique_name))
    return unique_name


# ===========================================================================
# TEMPLATE FILTERS & CONTEXT INJECTION
# ===========================================================================

@app.template_filter("plant_image")
def plant_image_filter(filename):
    if not filename:
        return url_for("static", filename="images/plants/default_plant.jpg")
    fname = os.path.basename(str(filename).replace("\\", "/"))
    full_path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    if not os.path.exists(full_path):
        return url_for("static", filename="images/plants/default_plant.jpg")
    return url_for("static", filename="images/plants/" + fname)


@app.template_filter("service_image")
def service_image_filter(filename):
    if not filename:
        return url_for("static", filename="images/services/default_service.jpg")
    fname = os.path.basename(str(filename).replace("\\", "/"))
    full_path = os.path.join(app.config["SERVICE_UPLOAD_FOLDER"], fname)
    if not os.path.exists(full_path):
        return url_for("static", filename="images/services/default_service.jpg")
    return url_for("static", filename="images/services/" + fname)


@app.template_filter("category_image")
def category_image_filter(cat_name):
    slug_map = {
        "Indoor Plants":    "indoor-plants.jpg",
        "Outdoor Plants":   "outdoor-plants.jpg",
        "Flower Plants":    "flower-plants.jpg",
        "Fruit Plants":     "fruit-plants.jpg",
        "Vegetable Plants": "vegetable-plants.jpg",
        "Medicinal Plants": "medicinal-plants.jpg",
        "Succulents":       "succulents.jpg",
        "Cactus":           "cactus.jpg",
    }
    img = slug_map.get(cat_name, "indoor-plants.jpg")
    return url_for("static", filename="images/categories/" + img)


@app.context_processor
def inject_globals():
    cart_count = 0
    unread_notifs = 0
    if "user_id" in session and session.get("role") == "customer":
        cart_count = CartItem.query.filter_by(user_id=session["user_id"]).count()
        unread_notifs = Notification.query.filter_by(user_id=session["user_id"], is_read=False).count()
    return dict(
        current_user=current_user(),
        cart_count=cart_count,
        unread_notifs=unread_notifs,
        today_date=datetime.utcnow().strftime("%Y-%m-%d"),
    )


# ===========================================================================
# PUBLIC ROUTES (HOME, ABOUT, CONTACT)
# ===========================================================================

@app.route("/")
def index():
    featured   = Plant.query.order_by(Plant.rating.desc()).limit(8).all()
    categories = Category.query.all()
    services   = Service.query.limit(4).all()
    feedbacks  = Feedback.query.order_by(Feedback.created_at.desc()).limit(6).all()
    return render_template("index.html",
                           plants=featured,
                           categories=categories,
                           services=services,
                           feedbacks=feedbacks)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ===========================================================================
# 1. CUSTOMER MODULE: REGISTRATION, AUTH & SEARCH
# ===========================================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone            = request.form.get("phone", "").strip()
        address          = request.form.get("address", "").strip()
        role             = request.form.get("role", "customer")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("This email is already registered. Please log in.", "error")
            return redirect(url_for("login"))

        if role not in ("customer", "seller"):
            role = "customer"

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            address=address,
            role=role,
            status="Active",
        )
        db.session.add(user)
        db.session.flush()

        # Create welcome notification
        db.session.add(Notification(
            user_id=user.id,
            message="Welcome to Plant Nursery! Your account has been registered successfully."
        ))
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        if user.status == "Inactive":
            flash("Your account has been deactivated. Please contact support.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["role"]    = user.role
        session["user_name"] = user.name
        session["name"]    = user.name

        flash(f"Welcome back, {user.name}!", "success")

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if user.role == "seller":
            return redirect(url_for("seller_dashboard"))
        return redirect(url_for("customer_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been securely logged out.", "success")
    return redirect(url_for("index"))


# ===========================================================================
# 1B. PLANT SEARCH & FILTERING (INDOOR/OUTDOOR, CATEGORY, PRICE, AVAILABILITY)
# ===========================================================================

@app.route("/plants")
def plants():
    query        = Plant.query
    search       = request.args.get("q", "").strip()
    category_id  = request.args.get("category", type=int)
    environment  = request.args.get("environment", "").strip().lower()
    sort         = request.args.get("sort", "")
    availability = request.args.get("availability", "")
    min_price    = request.args.get("min_price", type=float)
    max_price    = request.args.get("max_price", type=float)
    min_rating   = request.args.get("min_rating", type=float)

    # Keyword search across name, botanical name, and description
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                Plant.name.ilike(search_filter),
                Plant.botanical_name.ilike(search_filter),
                Plant.description.ilike(search_filter)
            )
        )

    # Category filter
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Environment filter (Indoor / Outdoor)
    if environment == "indoor":
        query = query.join(Category).filter(
            db.or_(
                Category.name.ilike("%indoor%"),
                Plant.sunlight.ilike("%indirect%"),
                Plant.sunlight.ilike("%low%"),
                Plant.description.ilike("%indoor%")
            )
        )
    elif environment == "outdoor":
        query = query.join(Category).filter(
            db.or_(
                Category.name.ilike("%outdoor%"),
                Plant.sunlight.ilike("%full sun%"),
                Plant.sunlight.ilike("%direct%"),
                Plant.description.ilike("%outdoor%")
            )
        )

    # Stock availability filter
    if availability == "in_stock":
        query = query.filter(Plant.stock > 0)
    elif availability == "out_stock":
        query = query.filter(Plant.stock == 0)

    # Price range filter
    if min_price is not None:
        query = query.filter(Plant.price >= min_price)
    if max_price is not None:
        query = query.filter(Plant.price <= max_price)

    # Rating filter
    if min_rating is not None:
        query = query.filter(Plant.rating >= min_rating)

    # Sorting
    if sort == "price_low":
        query = query.order_by(Plant.price.asc())
    elif sort == "price_high":
        query = query.order_by(Plant.price.desc())
    elif sort == "rating":
        query = query.order_by(Plant.rating.desc())
    elif sort == "name_asc":
        query = query.order_by(Plant.name.asc())
    else:  # newest
        query = query.order_by(Plant.created_at.desc())

    plant_list = query.all()
    categories = Category.query.all()

    return render_template(
        "plants.html",
        plants=plant_list,
        categories=categories,
        search=search,
        category_id=category_id,
        environment=environment,
        sort=sort,
        availability=availability,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
    )


@app.route("/plants/<int:plant_id>")
def plant_details(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    related = (Plant.query
               .filter_by(category_id=plant.category_id)
               .filter(Plant.id != plant.id)
               .limit(4).all())
    return render_template("plant_details.html", plant=plant, related=related)


# ===========================================================================
# 1D. SHOPPING CART & CHECKOUT (PERSISTENT IN MYSQL)
# ===========================================================================

def get_or_create_cart(customer_id):
    c = Cart.query.filter_by(customer_id=customer_id).first()
    if not c:
        c = Cart(customer_id=customer_id)
        db.session.add(c)
        db.session.flush()
    return c


@app.route("/cart")
@login_required(role="customer")
def cart():
    items    = CartItem.query.filter_by(user_id=session["user_id"]).all()
    subtotal = sum(item.plant.price * item.quantity for item in items)
    delivery = 0 if subtotal == 0 or subtotal >= 999 else 49
    total    = subtotal + delivery
    return render_template("cart.html",
                           items=items,
                           subtotal=subtotal,
                           delivery=delivery,
                           total=total)


@app.route("/cart/add/<int:plant_id>", methods=["POST"])
@login_required(role="customer")
def add_to_cart(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    qty   = request.form.get("qty", request.form.get("quantity", 1, type=int), type=int)
    if qty < 1:
        qty = 1

    if plant.stock <= 0:
        flash(f"{plant.name} is currently out of stock.", "error")
        return redirect(request.referrer or url_for("plants"))

    user_cart = get_or_create_cart(session["user_id"])
    item = CartItem.query.filter_by(user_id=session["user_id"], plant_id=plant_id).first()
    new_qty = (item.quantity if item else 0) + qty

    if new_qty > plant.stock:
        new_qty = plant.stock
        flash(f"Only {plant.stock} units of {plant.name} are available.", "info")

    if item:
        item.cart_id = user_cart.id
        item.quantity = new_qty
        item.price = plant.price
    else:
        db.session.add(CartItem(
            cart_id=user_cart.id,
            user_id=session["user_id"],
            plant_id=plant_id,
            quantity=new_qty,
            price=plant.price
        ))

    db.session.commit()
    flash(f"{plant.name} added to your cart.", "success")
    return redirect(request.referrer or url_for("plants"))


@app.route("/cart/buy-now/<int:plant_id>", methods=["POST"])
@login_required(role="customer")
def buy_now(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    qty   = request.form.get("qty", request.form.get("quantity", 1, type=int), type=int)

    if plant.stock <= 0:
        flash(f"{plant.name} is currently out of stock.", "error")
        return redirect(url_for("plant_details", plant_id=plant_id))

    qty = min(qty, plant.stock)
    user_cart = get_or_create_cart(session["user_id"])
    item = CartItem.query.filter_by(user_id=session["user_id"], plant_id=plant_id).first()
    if item:
        item.cart_id = user_cart.id
        item.quantity = min(item.quantity + qty, plant.stock)
        item.price = plant.price
    else:
        db.session.add(CartItem(
            cart_id=user_cart.id,
            user_id=session["user_id"],
            plant_id=plant_id,
            quantity=qty,
            price=plant.price
        ))

    db.session.commit()
    return redirect(url_for("checkout"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required(role="customer")
def update_cart(item_id):
    item = db.session.get(CartItem, item_id) or abort(404)
    if item.user_id != session["user_id"]:
        flash("Unauthorized action.", "error")
        return redirect(url_for("cart"))

    qty = request.form.get("quantity", 1, type=int)
    if qty < 1:
        db.session.delete(item)
    elif qty > item.plant.stock:
        flash(f"Only {item.plant.stock} units available for {item.plant.name}.", "info")
        item.quantity = item.plant.stock
    else:
        item.quantity = qty

    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>")
@login_required(role="customer")
def remove_from_cart(item_id):
    item = db.session.get(CartItem, item_id) or abort(404)
    if item.user_id == session["user_id"]:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required(role="customer")
def checkout():
    items = CartItem.query.filter_by(user_id=session["user_id"]).all()
    if not items:
        flash("Your shopping cart is empty.", "error")
        return redirect(url_for("plants"))

    subtotal = sum(item.plant.price * item.quantity for item in items)
    delivery = 0 if subtotal >= 999 else 49
    total    = subtotal + delivery

    if request.method == "POST":
        name           = request.form.get("name", "").strip()
        mobile         = request.form.get("mobile", "").strip()
        address        = request.form.get("address", "").strip()
        city           = request.form.get("city", "").strip()
        state          = request.form.get("state", "").strip()
        pincode        = request.form.get("pincode", "").strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")

        if not all([name, mobile, address, city, state, pincode]):
            flash("Please fill in all required delivery fields.", "error")
            return redirect(url_for("checkout"))

        # Re-verify stock atomically
        for item in items:
            if item.quantity > item.plant.stock:
                flash(f"Insufficient stock for {item.plant.name}. Only {item.plant.stock} left.", "error")
                return redirect(url_for("cart"))

        full_address = f"{address}, {city}, {state} - {pincode} | Ph: {mobile}"
        order_code   = generate_order_code()

        # Create Order
        order = Order(
            order_code=order_code,
            customer_id=session["user_id"],
            total_amount=total,
            delivery_address=full_address,
            payment_method=payment_method,
            payment_status="Pending" if payment_method == "Cash on Delivery" else "Paid",
            order_status="Processing",
        )
        db.session.add(order)
        db.session.flush()

        # Add Order Items, update stock, and delete cart items
        for item in items:
            db.session.add(OrderItem(
                order_id=order.id,
                plant_id=item.plant_id,
                seller_id=item.plant.seller_id,
                quantity=item.quantity,
                price=item.plant.price,
            ))
            # Decrement stock and update availability if 0
            item.plant.stock -= item.quantity
            if item.plant.stock == 0:
                item.plant.availability = "Out of Stock"
            db.session.delete(item)

        # Create Payment Record
        db.session.add(Payment(
            order_id=order.id,
            payment_method=payment_method,
            amount=total,
            payment_status="Pending" if payment_method == "Cash on Delivery" else "Paid",
        ))

        # Create Customer Notification
        db.session.add(Notification(
            user_id=session["user_id"],
            message=f"Order #{order_code} placed successfully! Amount: ₹{total:.2f}. Method: {payment_method}."
        ))

        db.session.commit()
        flash("Order placed successfully!", "success")
        return redirect(url_for("order_success", order_id=order.id))

    user = current_user()
    return render_template("checkout.html",
                           items=items,
                           subtotal=subtotal,
                           delivery=delivery,
                           total=total,
                           user=user)


@app.route("/order-success/<int:order_id>")
@login_required(role="customer")
def order_success(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    if order.customer_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        return redirect(url_for("index"))
    return render_template("order_success.html", order=order)


@app.route("/orders")
@login_required(role="customer")
def orders():
    my_orders = (Order.query
                 .filter_by(customer_id=session["user_id"])
                 .order_by(Order.order_date.desc())
                 .all())
    return render_template("orders.html", orders=my_orders)


@app.route("/orders/<int:order_id>")
@login_required()
def order_details(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    # Check access permission: customer who placed order, seller who sold item, or admin
    if session.get("role") == "customer" and order.customer_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        abort(403)
    if session.get("role") == "seller":
        seller_plant_ids = [p.id for p in Plant.query.filter_by(seller_id=session["user_id"]).all()]
        order_has_plant = any(item.plant_id in seller_plant_ids for item in order.items)
        if not order_has_plant:
            flash("Unauthorized access.", "error")
            abort(403)
    return render_template("order_details.html", order=order)


# ===========================================================================
# 1G & 1H. SERVICES, BOOKINGS & FEEDBACK
# ===========================================================================

@app.route("/services")
def services():
    all_services = Service.query.all()
    return render_template("services.html", services=all_services)


@app.route("/services/<int:service_id>")
def service_details(service_id):
    service = db.session.get(Service, service_id) or abort(404)
    return render_template("service_details.html", service=service)


@app.route("/services/<int:service_id>/book", methods=["GET", "POST"])
@app.route("/book-service/<int:service_id>", methods=["GET", "POST"])
@login_required(role="customer")
def book_service(service_id):
    service = db.session.get(Service, service_id) or abort(404)
    user    = current_user()

    if request.method == "POST":
        customer_name = request.form.get("customer_name", user.name if user else "").strip()
        phone         = request.form.get("phone", user.phone if user else "").strip()
        booking_date  = request.form.get("booking_date", "").strip()
        booking_time  = request.form.get("booking_time", "").strip()
        address       = request.form.get("address", "").strip()
        notes         = request.form.get("notes", request.form.get("requirements", "")).strip()

        if not all([customer_name, phone, booking_date, booking_time, address]):
            flash("Please fill in all required fields to book the appointment.", "error")
            return redirect(url_for("book_service", service_id=service_id))

        booking = ServiceBooking(
            customer_id=session["user_id"],
            service_id=service_id,
            customer_name=customer_name,
            phone=phone,
            booking_date=booking_date,
            booking_time=booking_time,
            address=address,
            requirements=notes,
            booking_status="Pending",
        )
        db.session.add(booking)
        db.session.add(Notification(
            user_id=session["user_id"],
            message=f"Your booking for '{service.name}' on {booking_date} ({booking_time}) has been requested."
        ))
        db.session.commit()
        flash("Service booking requested successfully!", "success")
        return redirect(url_for("my_bookings"))

    return render_template("booking.html", service=service, user=user, current_user=user)


@app.route("/my-bookings")
@login_required(role="customer")
def my_bookings():
    bookings = (ServiceBooking.query
                .filter_by(customer_id=session["user_id"])
                .order_by(ServiceBooking.created_at.desc())
                .all())
    return render_template("bookings.html", bookings=bookings)


@app.route("/feedback", methods=["GET", "POST"])
@login_required(role="customer")
def feedback():
    if request.method == "POST":
        message = request.form.get("message", request.form.get("comments", "")).strip()
        rating  = request.form.get("rating", 5, type=int)
        rating  = max(1, min(5, rating))

        if not message:
            flash("Feedback message cannot be blank.", "error")
        else:
            db.session.add(Feedback(
                customer_id=session["user_id"],
                comments=message,
                rating=rating,
            ))
            db.session.commit()
            flash("Thank you! Your feedback has been submitted.", "success")
        return redirect(url_for("feedback"))

    my_feedback = (Feedback.query
                   .filter_by(customer_id=session["user_id"])
                   .order_by(Feedback.created_at.desc())
                   .all())
    return render_template("feedback.html", feedback_list=my_feedback)


@app.route("/customer/dashboard")
@login_required(role="customer")
def customer_dashboard():
    user = current_user()
    orders = Order.query.filter_by(customer_id=user.id).order_by(Order.order_date.desc()).all()
    active_orders_count = sum(1 for o in orders if o.status in ("Processing", "Packed", "Shipped"))
    bookings = ServiceBooking.query.filter_by(customer_id=user.id).order_by(ServiceBooking.created_at.desc()).all()
    cart_count = CartItem.query.filter_by(user_id=user.id).count()
    return render_template(
        "customer/dashboard.html",
        user=user,
        orders=orders,
        active_orders_count=active_orders_count,
        bookings=bookings,
        cart_count=cart_count
    )


@app.route("/dashboard")
def general_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    if role == "seller":
        return redirect(url_for("seller_dashboard"))
    return redirect(url_for("customer_dashboard"))


@app.route("/profile", methods=["GET", "POST"])
@login_required()
def profile():
    user = current_user()
    if request.method == "POST":
        user.name    = request.form.get("name", user.name).strip()
        user.phone   = request.form.get("phone", user.phone or "").strip()
        user.address = request.form.get("address", user.address or "").strip()
        db.session.commit()
        session["user_name"] = user.name
        session["name"]      = user.name
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)


@app.route("/change-password", methods=["POST"])
@login_required()
def change_password():
    user   = current_user()
    old_pw = request.form.get("old_password", "")
    new_pw = request.form.get("new_password", "")

    if not check_password_hash(user.password, old_pw):
        flash("Current password is incorrect.", "error")
    elif len(new_pw) < 4:
        flash("New password must be at least 4 characters.", "error")
    else:
        user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))


# ===========================================================================
# 2. SELLER MODULE: DASHBOARD, INVENTORY & STOCK CONTROL
# ===========================================================================

@app.route("/seller/dashboard")
@login_required(role="seller")
def seller_dashboard():
    seller_id = session["user_id"]
    my_plants = Plant.query.filter_by(seller_id=seller_id).all()
    plant_ids = [p.id for p in my_plants]

    if plant_ids:
        order_items = OrderItem.query.filter(OrderItem.plant_id.in_(plant_ids)).all()
        order_ids   = list({oi.order_id for oi in order_items})
        my_orders   = (Order.query
                       .filter(Order.id.in_(order_ids))
                       .order_by(Order.order_date.desc())
                       .all() if order_ids else [])
    else:
        order_items = []
        my_orders   = []

    total_sales    = sum(oi.price * oi.quantity for oi in order_items)
    pending_orders = len([o for o in my_orders if o.status not in ("Delivered", "Cancelled")])
    total_stock    = sum(p.stock for p in my_plants)
    low_stock      = [p for p in my_plants if p.stock <= 5]

    return render_template(
        "seller/dashboard.html",
        total_plants=len(my_plants),
        total_stock=total_stock,
        total_orders=len(my_orders),
        pending_orders=pending_orders,
        total_sales=total_sales,
        low_stock_plants=low_stock,
        recent_orders=my_orders[:5],
        recent_plants=my_plants[:5],
    )


@app.route("/seller/plants")
@login_required(role="seller")
def seller_plants():
    my_plants = (Plant.query
                 .filter_by(seller_id=session["user_id"])
                 .order_by(Plant.created_at.desc())
                 .all())
    return render_template("seller/plants.html", plants=my_plants)


@app.route("/seller/plants/add", methods=["GET", "POST"])
@login_required(role="seller")
def add_plant():
    categories = Category.query.all()
    if request.method == "POST":
        name           = request.form.get("name", "").strip()
        category_id    = request.form.get("category_id", type=int)
        price          = request.form.get("price", type=float)
        stock          = request.form.get("stock", type=int)
        description    = request.form.get("description", "").strip()
        botanical_name = request.form.get("botanical_name", "").strip()
        sunlight       = request.form.get("sunlight", "").strip()
        watering       = request.form.get("watering", "").strip()
        availability   = request.form.get("availability", "In Stock" if (stock and stock > 0) else "Out of Stock")

        if not name or not category_id or price is None or stock is None:
            flash("Please fill in all required plant fields.", "error")
            return redirect(url_for("add_plant"))

        image_filename = "default_plant.jpg"
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            image_filename = save_upload(file, app.config["UPLOAD_FOLDER"])

        plant = Plant(
            seller_id=session["user_id"],
            category_id=category_id,
            name=name,
            price=price,
            stock=stock,
            description=description,
            botanical_name=botanical_name,
            sunlight=sunlight,
            watering=watering,
            availability=availability if stock > 0 else "Out of Stock",
            image=image_filename,
        )
        db.session.add(plant)
        db.session.commit()
        flash(f"Plant variety '{name}' listed successfully.", "success")
        return redirect(url_for("seller_plants"))

    return render_template("seller/add_plant.html", categories=categories)


@app.route("/seller/plants/edit/<int:plant_id>", methods=["GET", "POST"])
@login_required(role="seller")
def edit_plant(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    if plant.seller_id != session["user_id"]:
        flash("Unauthorized access to this plant record.", "error")
        abort(403)

    categories = Category.query.all()
    if request.method == "POST":
        plant.name           = request.form.get("name", plant.name).strip()
        plant.category_id    = request.form.get("category_id", plant.category_id, type=int)
        plant.price          = request.form.get("price", plant.price, type=float)
        plant.stock          = request.form.get("stock", plant.stock, type=int)
        plant.description    = request.form.get("description", plant.description or "").strip()
        plant.botanical_name = request.form.get("botanical_name", plant.botanical_name or "").strip()
        plant.sunlight       = request.form.get("sunlight", plant.sunlight or "").strip()
        plant.watering       = request.form.get("watering", plant.watering or "").strip()
        plant.availability   = "In Stock" if plant.stock > 0 else "Out of Stock"

        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            plant.image = save_upload(file, app.config["UPLOAD_FOLDER"])

        db.session.commit()
        flash(f"Plant '{plant.name}' updated successfully.", "success")
        return redirect(url_for("seller_plants"))

    return render_template("seller/edit_plant.html", plant=plant, categories=categories)


@app.route("/seller/plants/update-stock/<int:plant_id>", methods=["POST"])
@login_required(role="seller")
def seller_update_stock(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    if plant.seller_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        abort(403)

    new_stock = request.form.get("stock", type=int)
    if new_stock is not None and new_stock >= 0:
        plant.stock = new_stock
        plant.availability = "In Stock" if new_stock > 0 else "Out of Stock"
        db.session.commit()
        flash(f"Stock for '{plant.name}' updated to {new_stock} units.", "success")
    return redirect(url_for("seller_plants"))


@app.route("/seller/plants/delete/<int:plant_id>")
@login_required(role="seller")
def delete_plant(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    if plant.seller_id != session["user_id"]:
        flash("Unauthorized access.", "error")
        return redirect(url_for("seller_plants"))

    if OrderItem.query.filter_by(plant_id=plant.id).first():
        flash(f"Cannot delete '{plant.name}' because it exists in past customer orders. Stock has been set to 0 instead.", "info")
        plant.stock = 0
        plant.availability = "Out of Stock"
        db.session.commit()
        return redirect(url_for("seller_plants"))

    CartItem.query.filter_by(plant_id=plant.id).delete()
    try:
        db.session.delete(plant)
        db.session.commit()
        flash(f"Plant '{plant.name}' deleted successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not delete plant due to database constraint.", "error")
    return redirect(url_for("seller_plants"))


@app.route("/seller/orders")
@login_required(role="seller")
def seller_orders():
    seller_id = session["user_id"]
    plant_ids = [p.id for p in Plant.query.filter_by(seller_id=seller_id).all()]
    if plant_ids:
        order_items = OrderItem.query.filter(OrderItem.plant_id.in_(plant_ids)).all()
        order_ids   = list({oi.order_id for oi in order_items})
        my_orders   = (Order.query
                       .filter(Order.id.in_(order_ids))
                       .order_by(Order.order_date.desc())
                       .all() if order_ids else [])
    else:
        my_orders = []
    return render_template("seller/orders.html", orders=my_orders)


@app.route("/seller/orders/update/<int:order_id>", methods=["POST"])
@login_required(role="seller")
def update_order_status(order_id):
    order  = db.session.get(Order, order_id) or abort(404)
    status = request.form.get("status")
    valid  = ["Processing", "Packed", "Shipped", "Delivered", "Cancelled"]
    if status in valid:
        order.status = status
        # If delivered, update payment status for COD
        if status == "Delivered" and order.payment_method == "Cash on Delivery":
            order.payment_status = "Paid"
        db.session.add(Notification(
            user_id=order.customer_id,
            message=f"Status update for order #{order.order_code}: {status}."
        ))
        db.session.commit()
        flash(f"Order #{order.order_code} updated to '{status}'.", "success")
    else:
        flash("Invalid status value.", "error")
    return redirect(url_for("seller_orders"))


@app.route("/seller/inventory")
@login_required(role="seller")
def seller_inventory():
    seller = current_user()
    query = request.args.get("q", "").strip()
    filter_status = request.args.get("status", "")

    plants_query = Plant.query.filter_by(seller_id=seller.id)
    if query:
        plants_query = plants_query.filter(
            (Plant.name.ilike(f"%{query}%")) | (Plant.botanical_name.ilike(f"%{query}%"))
        )

    all_plants = Plant.query.filter_by(seller_id=seller.id).all()
    total_units = sum(p.stock for p in all_plants)
    in_stock_count = sum(1 for p in all_plants if p.stock > 10)
    low_stock_count = sum(1 for p in all_plants if 0 < p.stock <= 10)
    out_of_stock_count = sum(1 for p in all_plants if p.stock <= 0)

    if filter_status == "in_stock":
        plants_query = plants_query.filter(Plant.stock > 10)
    elif filter_status == "low_stock":
        plants_query = plants_query.filter(Plant.stock > 0, Plant.stock <= 10)
    elif filter_status == "out_of_stock":
        plants_query = plants_query.filter(Plant.stock <= 0)

    plants = plants_query.order_by(Plant.stock.asc()).all()

    return render_template(
        "seller/inventory.html",
        plants=plants,
        total_units=total_units,
        in_stock_count=in_stock_count,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        query=query,
        filter_status=filter_status
    )


@app.route("/seller/sales-report")
@login_required(role="seller")
def seller_sales_report():
    seller = current_user()
    order_items = OrderItem.query.filter_by(seller_id=seller.id).all()
    total_revenue = sum(oi.price * oi.quantity for oi in order_items)
    units_sold = sum(oi.quantity for oi in order_items)
    
    distinct_order_ids = {oi.order_id for oi in order_items}
    total_orders_count = len(distinct_order_ids)
    avg_order_value = (total_revenue / total_orders_count) if total_orders_count > 0 else 0.0

    seller_plants = Plant.query.filter_by(seller_id=seller.id).all()
    plant_sales = []
    for p in seller_plants:
        p_items = [oi for oi in order_items if oi.plant_id == p.id]
        sold_qty = sum(oi.quantity for oi in p_items)
        rev = sum(oi.price * oi.quantity for oi in p_items)
        plant_sales.append({
            "name": p.name,
            "botanical_name": p.botanical_name,
            "category_name": p.category.name if p.category else "General",
            "price": p.price,
            "stock": p.stock,
            "image": p.image,
            "sold_qty": sold_qty,
            "revenue": rev
        })
    plant_sales.sort(key=lambda x: x["revenue"], reverse=True)

    return render_template(
        "seller/sales_report.html",
        total_revenue=total_revenue,
        total_orders_count=total_orders_count,
        units_sold=units_sold,
        avg_order_value=avg_order_value,
        plant_sales=plant_sales
    )


# ===========================================================================
# 3. ADMIN MODULE: COMPLETE DASHBOARD & MANAGEMENT CONSOLE
# ===========================================================================

@app.route("/admin/dashboard")
@login_required(role="admin")
def admin_dashboard():
    total_customers = User.query.filter_by(role="customer").count()
    total_sellers   = User.query.filter_by(role="seller").count()
    total_plants    = Plant.query.count()
    total_orders    = Order.query.count()
    total_services  = Service.query.count()
    total_bookings  = ServiceBooking.query.count()
    total_sales     = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0

    recent_orders   = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    recent_plants   = Plant.query.order_by(Plant.created_at.desc()).limit(5).all()
    recent_services = Service.query.limit(4).all()
    recent_feedback = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_customers=total_customers,
        total_sellers=total_sellers,
        total_plants=total_plants,
        total_orders=total_orders,
        total_services=total_services,
        total_bookings=total_bookings,
        total_sales=total_sales,
        recent_orders=recent_orders,
        recent_plants=recent_plants,
        recent_services=recent_services,
        recent_feedback=recent_feedback,
    )


@app.route("/admin/categories", methods=["GET", "POST"])
@login_required(role="admin")
def admin_categories():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name:
            flash("Category name is required.", "error")
        elif Category.query.filter_by(name=name).first():
            flash("Category name already exists.", "error")
        else:
            db.session.add(Category(name=name, description=description))
            db.session.commit()
            flash(f"Category '{name}' created.", "success")
        return redirect(url_for("admin_categories"))

    categories = Category.query.all()
    return render_template("admin/categories.html", categories=categories)


@app.route("/admin/categories/edit/<int:cat_id>", methods=["POST"])
@login_required(role="admin")
def edit_category(cat_id):
    category = db.session.get(Category, cat_id) or abort(404)
    category.name        = request.form.get("name", category.name).strip()
    category.description = request.form.get("description", category.description or "").strip()
    db.session.commit()
    flash(f"Category '{category.name}' updated.", "success")
    return redirect(url_for("admin_categories"))


@app.route("/admin/categories/delete/<int:cat_id>")
@login_required(role="admin")
def delete_category(cat_id):
    category = db.session.get(Category, cat_id) or abort(404)
    if Plant.query.filter_by(category_id=cat_id).first():
        flash("Cannot delete a category that currently has plants assigned.", "error")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted.", "success")
    return redirect(url_for("admin_categories"))


@app.route("/admin/plants")
@app.route("/admin/products")
@login_required(role="admin")
def admin_plants():
    all_plants = Plant.query.order_by(Plant.created_at.desc()).all()
    return render_template("admin/plants.html", plants=all_plants)


@app.route("/admin/plants/edit/<int:plant_id>", methods=["GET", "POST"])
@login_required(role="admin")
def admin_edit_plant(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    categories = Category.query.all()
    if request.method == "POST":
        plant.name           = request.form.get("name", plant.name).strip()
        plant.category_id    = request.form.get("category_id", plant.category_id, type=int)
        plant.price          = request.form.get("price", plant.price, type=float)
        plant.stock          = request.form.get("stock", plant.stock, type=int)
        plant.description    = request.form.get("description", plant.description or "").strip()
        plant.botanical_name = request.form.get("botanical_name", plant.botanical_name or "").strip()
        plant.sunlight       = request.form.get("sunlight", plant.sunlight or "").strip()
        plant.watering       = request.form.get("watering", plant.watering or "").strip()
        plant.availability   = request.form.get("availability", "In Stock" if plant.stock > 0 else "Out of Stock")

        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            plant.image = save_upload(file, app.config["UPLOAD_FOLDER"])

        db.session.commit()
        flash(f"Plant '{plant.name}' updated by Admin.", "success")
        return redirect(url_for("admin_plants"))

    return render_template("admin/edit_plant.html", plant=plant, categories=categories)


@app.route("/admin/plants/delete/<int:plant_id>")
@login_required(role="admin")
def admin_delete_plant(plant_id):
    plant = db.session.get(Plant, plant_id) or abort(404)
    if OrderItem.query.filter_by(plant_id=plant.id).first():
        flash(f"Cannot delete '{plant.name}' as customers have ordered it. Stock set to 0 instead.", "info")
        plant.stock = 0
        plant.availability = "Out of Stock"
        db.session.commit()
        return redirect(url_for("admin_plants"))

    CartItem.query.filter_by(plant_id=plant.id).delete()
    try:
        db.session.delete(plant)
        db.session.commit()
        flash("Plant deleted from catalog.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not delete plant due to database constraint.", "error")
    return redirect(url_for("admin_plants"))


@app.route("/admin/customers")
@login_required(role="admin")
def admin_customers():
    customers = User.query.filter_by(role="customer").all()
    return render_template("admin/customers.html", customers=customers)


@app.route("/admin/sellers")
@login_required(role="admin")
def admin_sellers():
    sellers = User.query.filter_by(role="seller").all()
    return render_template("admin/sellers.html", sellers=sellers)


@app.route("/admin/users/toggle-status/<int:user_id>")
@login_required(role="admin")
def admin_toggle_user_status(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == session["user_id"]:
        flash("Cannot deactivate your own admin account.", "error")
        return redirect(request.referrer or url_for("admin_dashboard"))

    user.status = "Inactive" if user.status == "Active" else "Active"
    db.session.commit()
    flash(f"Account for '{user.name}' has been set to '{user.status}'.", "success")
    return redirect(request.referrer or url_for("admin_customers"))


@app.route("/admin/customers/delete/<int:user_id>")
@login_required(role="admin")
def admin_delete_customer(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role != "customer":
        flash("Target user is not a customer.", "error")
        return redirect(url_for("admin_customers"))
    db.session.delete(user)
    db.session.commit()
    flash(f"Customer '{user.name}' deleted.", "success")
    return redirect(url_for("admin_customers"))


@app.route("/admin/sellers/delete/<int:user_id>")
@login_required(role="admin")
def admin_delete_seller(user_id):
    user = db.session.get(User, user_id) or abort(404)
    if user.role != "seller":
        flash("Target user is not a seller.", "error")
        return redirect(url_for("admin_sellers"))
    db.session.delete(user)
    db.session.commit()
    flash(f"Seller '{user.name}' deleted.", "success")
    return redirect(url_for("admin_sellers"))


@app.route("/admin/orders")
@login_required(role="admin")
def admin_orders():
    all_orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template("admin/orders.html", orders=all_orders)


@app.route("/admin/orders/update/<int:order_id>", methods=["POST"])
@login_required(role="admin")
def admin_update_order(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    status         = request.form.get("status")
    payment_status = request.form.get("payment_status")

    if status in ["Processing", "Packed", "Shipped", "Delivered", "Cancelled"]:
        order.status = status
    if payment_status in ["Pending", "Paid", "Failed"]:
        order.payment_status = payment_status

    db.session.add(Notification(
        user_id=order.customer_id,
        message=f"Order #{order.order_code} update: Status is {order.status}, Payment is {order.payment_status}."
    ))
    db.session.commit()
    flash(f"Order #{order.order_code} updated.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/feedback")
@login_required(role="admin")
def admin_feedback():
    all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    return render_template("admin/feedback.html", feedback_list=all_feedback)


@app.route("/admin/feedback/delete/<int:feedback_id>")
@login_required(role="admin")
def admin_delete_feedback(feedback_id):
    fb = db.session.get(Feedback, feedback_id) or abort(404)
    db.session.delete(fb)
    db.session.commit()
    flash("Feedback review removed.", "success")
    return redirect(url_for("admin_feedback"))


@app.route("/admin/sales-report")
@login_required(role="admin")
def admin_sales_report():
    orders_list  = Order.query.order_by(Order.order_date.desc()).all()
    total_sales  = sum(o.total_amount for o in orders_list)
    total_orders = len(orders_list)
    avg_order    = total_sales / total_orders if total_orders else 0.0

    # Aggregate Daily Sales Breakdown
    daily_dict = {}
    for o in orders_list:
        d_str = o.order_date.strftime("%d %b %Y")
        if d_str not in daily_dict:
            daily_dict[d_str] = {"date": d_str, "orders": 0, "revenue": 0.0}
        daily_dict[d_str]["orders"] += 1
        daily_dict[d_str]["revenue"] += o.total_amount
    daily_sales = list(daily_dict.values())

    # Aggregate Monthly Sales Breakdown
    monthly_dict = {}
    for o in orders_list:
        m_str = o.order_date.strftime("%b %Y")
        if m_str not in monthly_dict:
            monthly_dict[m_str] = {"month": m_str, "orders": 0, "revenue": 0.0}
        monthly_dict[m_str]["orders"] += 1
        monthly_dict[m_str]["revenue"] += o.total_amount
    monthly_sales = list(monthly_dict.values())

    return render_template(
        "admin/sales_report.html",
        orders=orders_list,
        total_sales=total_sales,
        total_orders=total_orders,
        avg_order=avg_order,
        daily_sales=daily_sales,
        monthly_sales=monthly_sales,
    )


@app.route("/admin/services", methods=["GET", "POST"])
@login_required(role="admin")
def admin_services():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price       = request.form.get("price", type=float)
        duration    = request.form.get("duration", "").strip()

        if not name or price is None:
            flash("Service name and price are required.", "error")
            return redirect(url_for("admin_services"))

        image_filename = "default_service.jpg"
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename):
            image_filename = save_upload(file, app.config["SERVICE_UPLOAD_FOLDER"])

        db.session.add(Service(
            name=name,
            description=description,
            price=price,
            duration=duration,
            image=image_filename,
        ))
        db.session.commit()
        flash(f"Gardening service '{name}' created.", "success")
        return redirect(url_for("admin_services"))

    all_services = Service.query.all()
    return render_template("admin/services.html", services=all_services)


@app.route("/admin/services/edit/<int:service_id>", methods=["POST"])
@login_required(role="admin")
def admin_edit_service(service_id):
    service = db.session.get(Service, service_id) or abort(404)
    service.name         = request.form.get("name", service.name).strip()
    service.description  = request.form.get("description", service.description or "").strip()
    service.price        = request.form.get("price", service.price, type=float)
    service.duration     = request.form.get("duration", service.duration or "").strip()
    service.availability = request.form.get("availability", service.availability or "Available").strip()

    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        service.image = save_upload(file, app.config["SERVICE_UPLOAD_FOLDER"])

    db.session.commit()
    flash(f"Service '{service.name}' updated.", "success")
    return redirect(url_for("admin_services"))


@app.route("/admin/services/delete/<int:service_id>")
@login_required(role="admin")
def admin_delete_service(service_id):
    service = db.session.get(Service, service_id) or abort(404)
    db.session.delete(service)
    db.session.commit()
    flash("Service deleted.", "success")
    return redirect(url_for("admin_services"))


@app.route("/admin/bookings")
@login_required(role="admin")
def admin_bookings():
    bookings = ServiceBooking.query.order_by(ServiceBooking.created_at.desc()).all()
    pending_count = sum(1 for b in bookings if b.status == "Pending")
    confirmed_count = sum(1 for b in bookings if b.status == "Confirmed")
    completed_count = sum(1 for b in bookings if b.status == "Completed")
    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        completed_count=completed_count
    )


@app.route("/admin/bookings/<int:booking_id>/status", methods=["POST"])
@login_required(role="admin")
def admin_update_booking_status(booking_id):
    booking = db.session.get(ServiceBooking, booking_id) or abort(404)
    new_status = request.form.get("status")
    if new_status in ("Pending", "Confirmed", "Completed", "Cancelled"):
        booking.status = new_status
        db.session.commit()
        flash(f"Booking status updated to '{new_status}'.", "success")
    return redirect(url_for("admin_bookings"))


@app.route("/admin/security")
@app.route("/security")
@login_required(role="admin")
def admin_security():
    users = User.query.order_by(User.id.asc()).all()
    return render_template("admin/security.html", users=users)


# ===========================================================================
# ERROR HANDLERS
# ===========================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    flash("Unauthorized access. Access denied.", "error")
    return render_template("404.html"), 403


# ===========================================================================
# CLI COMMAND: flask --app app.py init-db
# ===========================================================================

@app.cli.command("init-db")
def init_db():
    """Create all 12 tables and seed comprehensive sample data."""
    try:
        from database import verify_and_create_tables
        verify_and_create_tables()
    except Exception as e:
        print(f"Direct MySQL verification note: {e}")
    db.create_all()

    # 1. Users
    admin = User.query.filter_by(email="admin@nursery.com").first()
    if not admin:
        admin = User(
            name="Platform Admin",
            email="admin@nursery.com",
            password=generate_password_hash("admin123"),
            phone="+91 99999 88888",
            address="Nursery Platform HQ, Green City",
            role="admin",
            status="Active",
        )
        db.session.add(admin)

    seller = User.query.filter_by(email="seller@nursery.com").first()
    if not seller:
        seller = User(
            name="Green Leaf Nursery",
            email="seller@nursery.com",
            password=generate_password_hash("seller123"),
            phone="+91 88888 77777",
            address="Plot 42, Botanical Farm Road, Chennai",
            role="seller",
            status="Active",
        )
        db.session.add(seller)

    customer = User.query.filter_by(email="customer@nursery.com").first()
    if not customer:
        customer = User(
            name="Priya Sharma",
            email="customer@nursery.com",
            password=generate_password_hash("customer123"),
            phone="+91 98765 43210",
            address="Flat 302, Palm Meadows, Green Road, Chennai",
            role="customer",
            status="Active",
        )
        db.session.add(customer)

    db.session.commit()

    # Re-fetch users
    seller = User.query.filter_by(email="seller@nursery.com").first()
    customer = User.query.filter_by(email="customer@nursery.com").first()

    # 2. Categories
    cat_data = [
        ("Indoor Plants", "Shade-loving, air-purifying plants ideal for apartments and offices"),
        ("Outdoor Plants", "Sunlight-thriving shrubs, foliage, and garden landscaping varieties"),
        ("Flower Plants", "Fragrant, vibrantly blooming ornamental plants and seasonal flowers"),
        ("Fruit Plants", "Healthy grafted saplings yielding sweet citrus and seasonal fruits"),
        ("Vegetable Plants", "Heirloom organic kitchen garden vegetables and daily fresh herbs"),
        ("Medicinal Plants", "Ayurvedic therapeutic herbs and natural wellness botanical species"),
        ("Succulents", "Drought-tolerant, fleshy geometric rosettes for low-maintenance decor"),
        ("Cactus", "Resilient desert-adapted spined varieties that require minimal watering"),
    ]
    cats = {}
    for cname, cdesc in cat_data:
        c = Category.query.filter_by(name=cname).first()
        if not c:
            c = Category(name=cname, description=cdesc)
            db.session.add(c)
            db.session.flush()
        cats[cname] = c

    db.session.commit()
    cats = {c.name: c for c in Category.query.all()}

    # 3. Plants
    sample_plants = [
        ("Money Plant", "Indoor Plants", 199.0, 50, "Epipremnum aureum", "Indirect Light", "Weekly", "money-plant.jpg", 4.8, "A classic indoor favourite known for bringing good fortune and purifying household air."),
        ("Snake Plant", "Indoor Plants", 299.0, 40, "Dracaena trifasciata", "Low to Bright", "Bi-weekly", "snake-plant.jpg", 4.9, "Extremely resilient architectural houseplant that purifies air even overnight."),
        ("Peace Lily", "Indoor Plants", 349.0, 25, "Spathiphyllum", "Filtered Light", "Weekly", "peace-lily.jpg", 4.8, "Air-purifying indoor flowering plant with stunning white spathe blooms and glossy foliage."),
        ("Jade Plant", "Indoor Plants", 249.0, 45, "Crassula ovata", "Bright Light", "Bi-weekly", "jade-plant.jpg", 4.9, "Classic money-tree succulent symbolising luck and prosperity with fleshy emerald leaves."),
        ("Lucky Bamboo", "Indoor Plants", 189.0, 50, "Dracaena sanderiana", "Indirect Light", "Weekly", "lucky-bamboo.jpg", 4.7, "Symbolic Feng Shui arrangement bringing positive energy and harmony to workspaces."),
        ("Spider Plant", "Indoor Plants", 159.0, 40, "Chlorophytum comosum", "Medium Light", "Weekly", "spider-plant.jpg", 4.6, "Fast-growing graceful hanging plant that eliminates indoor airborne pollutants efficiently."),
        ("Rose Plant", "Flower Plants", 149.0, 60, "Rosa", "Full Sun", "Daily", "rose.jpg", 4.7, "Classic aromatic blooming red roses that elevate gardens, patios, and flower beds."),
        ("Marigold", "Flower Plants", 99.0, 80, "Tagetes", "Full Sun", "Daily", "marigold.jpg", 4.5, "Golden festive blooms that repel pests naturally and brighten gardens with cheerful colour."),
        ("Jasmine", "Flower Plants", 199.0, 40, "Jasminum", "Full Sun", "Daily", "jasmine.jpg", 4.7, "Intensely fragrant star-shaped white blossoms favoured for morning pooja and balcony arches."),
        ("Hibiscus", "Flower Plants", 179.0, 35, "Hibiscus rosa-sinensis", "Full Sun", "Daily", "hibiscus.jpg", 4.6, "Stunning large crimson tropical flowers that bloom continuously with minimal effort."),
        ("Bougainvillea", "Flower Plants", 229.0, 30, "Bougainvillea spectabilis", "Direct Sunlight", "Low", "bougainvillea.jpg", 4.5, "Vibrant magenta flowering creeper ideal for sunny terraces, fences, and garden pergolas."),
        ("Mango Sapling", "Fruit Plants", 399.0, 25, "Mangifera indica", "Full Sun", "Twice a week", "mango-sapling.jpg", 4.6, "Healthy grafted tropical mango sapling that yields sweet, aromatic fruit in season."),
        ("Lemon Plant", "Fruit Plants", 249.0, 30, "Citrus limon", "Full Sun", "Twice a week", "lemon-plant.jpg", 4.7, "Fragrant citrus tree that produces abundant fresh juicy lemons all year round."),
        ("Tomato Plant", "Vegetable Plants", 79.0, 100, "Solanum lycopersicum", "Full Sun", "Daily", "tomato-plant.jpg", 4.4, "Vigorous heirloom tomato plant ideal for kitchen gardens and large balcony pots."),
        ("Chilli Plant", "Vegetable Plants", 69.0, 90, "Capsicum annuum", "Full Sun", "Daily", "chilli-plant.jpg", 4.5, "High-yielding spicy green chilli plant essential for every home culinary garden."),
        ("Aloe Vera", "Medicinal Plants", 129.0, 70, "Aloe barbadensis", "Bright Indirect", "Bi-weekly", "aloevera.jpg", 4.9, "Healing succulent revered for therapeutic gel, soothing skin burns and purifying air."),
        ("Tulsi", "Medicinal Plants", 89.0, 85, "Ocimum tenuiflorum", "Full Sun", "Daily", "tulsi.jpg", 4.9, "Sacred Ayurvedic herb celebrated for spiritual presence and potent herbal tea wellness."),
        ("Echeveria Succulent", "Succulents", 179.0, 45, "Echeveria elegans", "Bright Light", "Bi-weekly", "succulent.jpg", 4.8, "Compact geometrical rosette succulent, drought-tolerant and perfect for tabletop decor."),
        ("Barrel Cactus", "Cactus", 219.0, 35, "Echinocactus grusonii", "Full Sun", "Monthly", "cactus.jpg", 4.7, "Iconic golden-spined desert cactus that thrives on negligible maintenance and sunlight."),
        ("Bonsai Ficus", "Outdoor Plants", 599.0, 15, "Ficus microcarpa", "Bright Indirect", "Weekly", "bonsai-ficus.jpg", 4.9, "Masterfully trained miniature bonsai tree creating a serene Zen atmosphere in any room."),
        ("Areca Palm", "Outdoor Plants", 449.0, 20, "Dypsis lutescens", "Bright Indirect", "Weekly", "areca-palm.jpg", 4.8, "Luxurious feathery palm that adds tropical elegance and acts as a natural humidifier."),
    ]

    for (pname, cat, price, stock, botanical, sun, water, img, rating, desc) in sample_plants:
        p = Plant.query.filter_by(name=pname).first()
        if not p and cat in cats:
            db.session.add(Plant(
                seller_id=seller.id,
                category_id=cats[cat].id,
                name=pname,
                price=price,
                stock=stock,
                botanical_name=botanical,
                sunlight=sun,
                watering=water,
                rating=rating,
                image=img,
                description=desc,
                availability="In Stock" if stock > 0 else "Out of Stock"
            ))

    # 4. Services
    sample_services = [
        ("Garden Maintenance", "Comprehensive scheduled garden upkeep including weeding, hedge trimming, organic fertilizing and cleanup.", 499.0, "2 hours", "garden-maintenance.jpg"),
        ("Plant Care", "Expert botanical diagnostic inspection, pest control treatment, repotting advice and health boosting for plants.", 299.0, "1 hour", "plant-care.jpg"),
        ("Terrace Gardening", "Complete design, waterproof planter setup, organic soil preparation, and planting tailored for terraces.", 999.0, "3 hours", "terrace-garden.jpg"),
        ("Balcony Garden Setup", "Custom urban balcony transformation with hanging planters, vertical railing hooks and weather-resistant greens.", 799.0, "2-3 hours", "balcony-garden.jpg"),
        ("Lawn Maintenance", "Professional precision mowing, edging, weed eradication, dethatching, and lawn nutrient enrichment.", 599.0, "2 hours", "lawn-maintenance.jpg"),
        ("Plant Pruning", "Aesthetic and restorative pruning of ornamental shrubs, rose bushes, and fruit trees to encourage lush blooming.", 349.0, "1 hour", "plant-pruning.jpg"),
        ("Landscape Gardening", "Architectural landscape design, stone pathways, flower beds, and premium garden overhaul by senior horticulturists.", 1999.0, "1 day", "landscape-design.jpg"),
        ("Vertical Garden Installation", "Custom engineered living wall system for indoor and outdoor accent walls with built-in drip irrigation.", 2499.0, "1-2 days", "vertical-garden.jpg"),
        ("Garden Cleaning", "Deep seasonal garden clearing, debris raking, weed removal, leaf mulching, and bed soil conditioning.", 599.0, "2-3 hours", "garden-cleaning.jpg"),
        ("Indoor Plant Setup", "Curated interior plant styling, designer planter coordination, and light-optimized placement for apartments.", 899.0, "2 hours", "indoor-plant-setup.jpg"),
        ("Drip Irrigation Setup", "Automated smart micro-drip irrigation system installation to save 70% water and ensure consistent hydration.", 1499.0, "4 hours", "drip-irrigation.jpg"),
    ]

    for sname, desc, price, duration, img in sample_services:
        s = Service.query.filter_by(name=sname).first()
        if not s:
            db.session.add(Service(
                name=sname,
                description=desc,
                price=price,
                duration=duration,
                image=img,
                status="Available"
            ))

    db.session.commit()

    # 5. Sample Order, OrderItems & Payment
    if not Order.query.first():
        p1 = Plant.query.filter_by(name="Money Plant").first()
        p2 = Plant.query.filter_by(name="Snake Plant").first()
        if p1 and p2 and customer:
            order = Order(
                order_code="ORD98234120",
                customer_id=customer.id,
                total_amount=498.0,
                delivery_address="Flat 302, Palm Meadows, Green Road, Chennai - 600028 | Ph: 9876543210",
                payment_method="Cash on Delivery",
                payment_status="Paid",
                order_status="Delivered",
            )
            db.session.add(order)
            db.session.flush()

            db.session.add(OrderItem(order_id=order.id, plant_id=p1.id, seller_id=seller.id, quantity=1, price=p1.price))
            db.session.add(OrderItem(order_id=order.id, plant_id=p2.id, seller_id=seller.id, quantity=1, price=p2.price))
            db.session.add(Payment(order_id=order.id, payment_method="Cash on Delivery", amount=498.0, payment_status="Paid"))

    # 6. Sample Service Booking
    if not ServiceBooking.query.first():
        svc = Service.query.filter_by(name="Garden Maintenance").first()
        if svc and customer:
            db.session.add(ServiceBooking(
                customer_id=customer.id,
                service_id=svc.id,
                customer_name=customer.name,
                phone=customer.phone,
                booking_date="2026-11-25",
                booking_time="09:00 AM - 11:00 AM",
                address="Flat 302, Palm Meadows, Green Road, Chennai",
                requirements="Pruning balcony bougainvillea and soil conditioning for money plants",
                booking_status="Confirmed",
            ))

    # 7. Sample Feedback
    if not Feedback.query.first() and customer:
        db.session.add(Feedback(
            customer_id=customer.id,
            rating=5,
            comments="The plants arrived in immaculate condition! The packaging completely secured the soil and delicate stems. My snake plant and money plant are thriving on my workstation."
        ))

    # 8. Sample Notifications
    if not Notification.query.first() and customer:
        db.session.add(Notification(
            user_id=customer.id,
            message="Welcome to Plant Nursery! Explore our thriving botanicals and book expert gardening visits.",
            is_read=True
        ))

    db.session.commit()
    print("✅  Plant Nursery Database initialized with complete 12 tables and seed data.")
    print("    Admin    → admin@nursery.com    / admin123")
    print("    Seller   → seller@nursery.com   / seller123")
    print("    Customer → customer@nursery.com / customer123")


# ===========================================================================
# APPLICATION ENTRYPOINT
# ===========================================================================

if __name__ == "__main__":
    app.run(debug=True)
