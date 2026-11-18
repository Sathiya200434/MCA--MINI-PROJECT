"""
Script to generate README.docx for Plant Nursery & Gardening Services Platform.
Run: python gen_docs.py
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

OUTPUT_PATH = r"c:\Users\sathi\OneDrive\Attachments\plant_nursery\plant_nursery\README.docx"

doc = Document()

# ── Page setup: A4, 1-inch margins ──────────────────────────────────────────
section = doc.sections[0]
section.page_height = Cm(29.7)
section.page_width = Cm(21.0)
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)

# ── Default style: 12pt Times New Roman ─────────────────────────────────────
style = doc.styles['Normal']
font = style.font
font.name = 'Times New Roman'
font.size = Pt(12)

def set_font(run, bold=False, size=12, italic=False, color=None):
    run.font.name = 'Times New Roman'
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def add_heading(doc, text, level=1, center=False):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    sizes = {1: 16, 2: 14, 3: 12}
    set_font(run, bold=True, size=sizes.get(level, 12))
    return p

def add_para(doc, text, bold=False, italic=False, center=False, size=12, indent=False):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if indent:
        p.paragraph_format.left_indent = Inches(0.4)
    run = p.add_run(text)
    set_font(run, bold=bold, italic=italic, size=size)
    return p

def add_code_block(doc, code_text):
    """Add a monospace-formatted code block paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    # Light gray shading
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F0F0F0')
    pPr.append(shd)
    run = p.add_run(code_text)
    run.font.name = 'Courier New'
    run.font.size = Pt(10)
    return p

def set_table_borders(table):
    """Apply thin black borders to all cells of a table."""
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tblBorders.append(border)
    tblPr.append(tblBorders)

def shade_row(row, fill='2D6A4F'):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), fill)
        tcPr.append(shd)
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.bold = True

def add_table(doc, headers, rows, header_fill='2D6A4F'):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    set_table_borders(table)
    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                run.font.bold = True
    shade_row(hdr, header_fill)
    # Data rows
    for ri, row_data in enumerate(rows):
        row = table.rows[ri + 1]
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            cell.text = str(val)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(11)
    return table


# ════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("PLANT NURSERY & GARDENING SERVICES PLATFORM")
set_font(run, bold=True, size=20)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("A MINI PROJECT REPORT")
set_font(run, bold=True, size=16, italic=True)

doc.add_paragraph()
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Submitted in partial fulfilment of the requirements for the degree of")
set_font(run, size=12)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("MASTER OF COMPUTER APPLICATIONS")
set_font(run, bold=True, size=14)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Submitted by")
set_font(run, size=12)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("[Student Name]")
set_font(run, bold=True, size=13)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Reg No: [Reg No]")
set_font(run, bold=True, size=12)

doc.add_paragraph()
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Department of Computer Applications")
set_font(run, bold=True, size=13)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("[College Name]")
set_font(run, size=12)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Pondicherry University")
set_font(run, bold=True, size=13)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("November 2026")
set_font(run, bold=True, size=12)

doc.add_page_break()


# ════════════════════════════════════════════════════════════════════════════
# 1. PROJECT OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "1. PROJECT OVERVIEW", level=1)

add_para(doc,
    "The Plant Nursery & Gardening Services Platform is a full-stack web application "
    "developed using Python (Flask) and MySQL. It provides an end-to-end digital marketplace "
    "for buying plants, booking gardening services, and managing nursery operations. "
    "The platform supports three distinct roles — Customer, Seller, and Admin — each with "
    "a dedicated dashboard and feature set. Customers can browse plants by category, add items "
    "to the cart, place orders, and book gardening services. Sellers can list and manage their "
    "plant inventory and track orders. Administrators oversee the entire platform including "
    "users, products, services, orders, and generate sales reports."
)

doc.add_paragraph()
add_heading(doc, "1.1 Technology Stack", level=2)

add_table(doc,
    ["Component", "Technology / Library", "Version"],
    [
        ["Backend Framework", "Flask", "3.0.3"],
        ["ORM", "Flask-SQLAlchemy", "3.1.1"],
        ["Database Connector", "PyMySQL", "1.1.1"],
        ["Password Hashing", "Werkzeug Security", "3.0.4"],
        ["Frontend", "HTML5, Bootstrap 5, Jinja2", "—"],
        ["Database", "MySQL", "8.0+"],
        ["Language", "Python", "3.10+"],
        ["Document Generation", "python-docx", "1.1.0"],
    ]
)

doc.add_paragraph()

# ════════════════════════════════════════════════════════════════════════════
# 2. PREREQUISITES & INSTALLATION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "2. PREREQUISITES & INSTALLATION", level=1)

add_heading(doc, "2.1 Prerequisites", level=2)

prereqs = [
    "Python 3.10 or higher installed and added to PATH",
    "MySQL Server 8.0 or higher installed and running",
    "pip package manager",
    "Git (optional, for cloning the repository)",
]
for item in prereqs:
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Inches(0.4)
    run = p.add_run(item)
    set_font(run, size=12)

doc.add_paragraph()
add_heading(doc, "2.2 Step-by-Step Installation", level=2)

steps = [
    ("Step 1: Clone or Download the Repository",
     "git clone <repository-url>\ncd plant_nursery"),
    ("Step 2: Create a Virtual Environment",
     "python -m venv venv"),
    ("Step 3: Activate the Virtual Environment",
     "# Windows:\nvenv\\Scripts\\activate\n\n# macOS / Linux:\nsource venv/bin/activate"),
    ("Step 4: Install Required Packages",
     "pip install -r requirements.txt"),
    ("Step 5: Configure the Database Connection",
     "# Edit config.py and set your MySQL credentials:\n"
     "SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:<password>@localhost/plant_nursery_db'"),
    ("Step 6: Create Database and Import Schema",
     "mysql -u root -p < database.sql"),
    ("Step 7: Initialize the Application (create admin user)",
     "python app.py init-db"),
    ("Step 8: Run the Application",
     "python app.py\n\n# Application will start at: http://127.0.0.1:5000"),
]

for title, code in steps:
    add_para(doc, title, bold=True, size=12)
    add_code_block(doc, code)
    doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 3. DEMO LOGIN CREDENTIALS
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "3. DEMO LOGIN CREDENTIALS", level=1)

add_para(doc,
    "The following default accounts are created when you run the database initialization "
    "command (python app.py init-db):"
)
doc.add_paragraph()

add_table(doc,
    ["Role", "Email Address", "Password", "Access Level"],
    [
        ["Admin", "admin@nursery.com", "admin123", "Full platform administration"],
        ["Seller", "seller@nursery.com", "seller123", "Plant inventory & order management"],
        ["Customer", "customer@nursery.com", "customer123", "Browse, cart, orders & bookings"],
    ]
)

doc.add_paragraph()
add_para(doc,
    "Note: Passwords are stored using Werkzeug's generate_password_hash function (PBKDF2-SHA256). "
    "Change these credentials immediately in a production environment.",
    italic=True
)
doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 4. PROJECT FOLDER STRUCTURE
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "4. PROJECT FOLDER STRUCTURE", level=1)

folder_structure = """\
plant_nursery/
├── app.py                      # Main Flask application & all routes
├── config.py                   # Database and app configuration
├── database.sql                # MySQL schema + sample data
├── requirements.txt            # Python dependencies
├── README.docx                 # This project report
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom styles (Bootstrap extension)
│   ├── js/
│   │   └── script.js           # Client-side JavaScript
│   └── images/
│       ├── plants/             # Plant product images (uploaded)
│       ├── services/           # Service images (uploaded)
│       ├── hero/               # Homepage hero images
│       └── categories/         # Category thumbnails
│
└── templates/
    ├── base.html               # Base layout (navbar, footer, flash messages)
    ├── index.html              # Homepage
    ├── about.html              # About us page
    ├── contact.html            # Contact page
    ├── login.html              # Login form
    ├── register.html           # Registration form
    ├── plants.html             # Plant listing with filters
    ├── plant_details.html      # Individual plant detail page
    ├── cart.html               # Shopping cart
    ├── checkout.html           # Order checkout form
    ├── order_success.html      # Order confirmation page
    ├── orders.html             # Customer order history
    ├── services.html           # Service listing
    ├── service_details.html    # Individual service detail
    ├── booking.html            # Service booking form
    ├── bookings.html           # Customer booking history
    ├── feedback.html           # Feedback submission form
    ├── profile.html            # Customer profile management
    ├── 404.html                # Custom 404 error page
    │
    ├── seller/
    │   ├── _sidebar.html       # Seller navigation sidebar
    │   ├── dashboard.html      # Seller dashboard & stats
    │   ├── plants.html         # Seller plant inventory
    │   ├── add_plant.html      # Add new plant form
    │   ├── edit_plant.html     # Edit existing plant form
    │   └── orders.html         # Orders containing seller's plants
    │
    └── admin/
        ├── _sidebar.html       # Admin navigation sidebar
        ├── dashboard.html      # Admin dashboard & stats
        ├── categories.html     # Category management
        ├── plants.html         # All plant listings
        ├── customers.html      # Customer user management
        ├── sellers.html        # Seller user management
        ├── orders.html         # All orders management
        ├── services.html       # Service management
        ├── feedback.html       # Customer feedback review
        └── sales_report.html   # Sales analytics & reports"""

add_code_block(doc, folder_structure)
doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 5. MODULE DESCRIPTION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "5. MODULE DESCRIPTION", level=1)

modules = [
    ("5.1 Customer Module", [
        "User Registration & Login: Secure account creation with email validation and role selection.",
        "Plant Browsing: Filter plants by category, price range, rating, availability, and sort order.",
        "Plant Details: Detailed product page with botanical info, care tips, and related plants.",
        "Shopping Cart: Add to cart, update quantities, real-time subtotal calculation.",
        "Checkout: Multi-field address form with COD and Demo Online Payment options.",
        "Order Tracking: View order history with status (Processing → Packed → Shipped → Delivered).",
        "Service Booking: Book gardening services with preferred date, time, address, and notes.",
        "Booking Management: View all past and upcoming service bookings.",
        "Feedback Submission: Rate the platform (1–5 stars) and submit comments.",
        "Profile Management: Update personal details and change password.",
    ]),
    ("5.2 Seller Module", [
        "Seller Dashboard: At-a-glance stats — total plants, stock value, orders, and total sales.",
        "Plant Inventory: View, add, edit, and delete listed plants with image upload.",
        "Plant Form Validation: Stock cannot go negative; plants with active orders cannot be deleted.",
        "Order Management: View orders containing seller's plants; update order status.",
        "Image Uploads: Plant images stored in static/images/plants/ with secure filename handling.",
    ]),
    ("5.3 Admin Module", [
        "Admin Dashboard: Platform-wide statistics — customers, sellers, plants, orders, services, revenue.",
        "Category Management: Add, edit, delete categories (deletion blocked if plants are assigned).",
        "Plant Oversight: View all plants across sellers; delete with order-block safeguard.",
        "User Management: View and delete customer or seller accounts.",
        "Order Administration: View all platform orders across all sellers.",
        "Service Management: Add, edit, delete gardening services with image upload.",
        "Feedback Review: Moderate customer feedback and ratings.",
        "Sales Report: Comprehensive sales analytics with totals, averages, and order breakdown.",
    ]),
    ("5.4 Security Module", [
        "Password Hashing: Werkzeug PBKDF2-SHA256 hashing; passwords never stored in plaintext.",
        "Session Management: Flask server-side sessions with SECRET_KEY protection.",
        "Role-Based Access Control: Decorators restrict routes to customer/seller/admin only.",
        "CSRF Protection: Form tokens and POST-only mutations prevent cross-site request forgery.",
        "Input Validation: Server-side validation on all forms; SQL injection prevented by ORM.",
        "File Upload Security: Werkzeug secure_filename(); only image extensions allowed.",
    ]),
]

for mod_title, features in modules:
    add_heading(doc, mod_title, level=2)
    for f in features:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.left_indent = Inches(0.4)
        run = p.add_run(f)
        set_font(run, size=12)
    doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 6. DATABASE SCHEMA
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "6. DATABASE SCHEMA", level=1)

add_para(doc,
    "The application uses MySQL with 9 tables modelled via Flask-SQLAlchemy ORM. "
    "All tables use InnoDB engine for foreign-key support and UTF-8 character encoding."
)
doc.add_paragraph()

tables = [
    ("6.1 users — Stores all platform user accounts", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique user identifier"),
        ("name", "VARCHAR(100)", "NOT NULL", "Full name of the user"),
        ("email", "VARCHAR(120)", "UNIQUE, NOT NULL", "Login email address"),
        ("password", "VARCHAR(256)", "NOT NULL", "PBKDF2-hashed password"),
        ("phone", "VARCHAR(20)", "NULL", "Contact phone number"),
        ("address", "TEXT", "NULL", "Default delivery address"),
        ("role", "ENUM('customer','seller','admin')", "DEFAULT 'customer'", "User role"),
        ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Account creation timestamp"),
    ]),
    ("6.2 categories — Plant category taxonomy", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique category identifier"),
        ("name", "VARCHAR(100)", "UNIQUE, NOT NULL", "Category name (e.g., Indoor Plants)"),
        ("description", "TEXT", "NULL", "Brief description of the category"),
    ]),
    ("6.3 plants — Product listings by sellers", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique plant identifier"),
        ("seller_id", "INT", "FK → users(id)", "Seller who listed this plant"),
        ("category_id", "INT", "FK → categories(id)", "Plant category"),
        ("name", "VARCHAR(150)", "NOT NULL", "Common plant name"),
        ("price", "FLOAT", "NOT NULL", "Selling price in INR"),
        ("stock", "INT", "DEFAULT 0", "Available stock quantity"),
        ("image", "VARCHAR(255)", "NULL", "Filename of uploaded image"),
        ("description", "TEXT", "NULL", "Plant description and care guide"),
        ("botanical_name", "VARCHAR(150)", "NULL", "Scientific botanical name"),
        ("sunlight", "VARCHAR(100)", "NULL", "Sunlight requirement"),
        ("watering", "VARCHAR(100)", "NULL", "Watering frequency"),
        ("rating", "FLOAT", "DEFAULT 4.0", "Average product rating (1–5)"),
        ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Listing creation timestamp"),
    ]),
    ("6.4 cart — Active shopping cart items", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique cart item identifier"),
        ("user_id", "INT", "FK → users(id)", "Customer who owns this cart item"),
        ("plant_id", "INT", "FK → plants(id)", "Plant added to cart"),
        ("quantity", "INT", "DEFAULT 1", "Quantity of the plant in cart"),
    ]),
    ("6.5 orders — Customer order records", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique order identifier"),
        ("order_code", "VARCHAR(20)", "UNIQUE, NOT NULL", "Human-readable order code (ORD-XXXXXXXX)"),
        ("user_id", "INT", "FK → users(id)", "Customer who placed the order"),
        ("total_amount", "FLOAT", "NOT NULL", "Total order value in INR"),
        ("address", "TEXT", "NOT NULL", "Delivery address"),
        ("payment_method", "VARCHAR(50)", "NOT NULL", "COD or Demo Online Payment"),
        ("status", "ENUM(...)", "DEFAULT 'Processing'", "Order status (Processing/Packed/Shipped/Delivered/Cancelled)"),
        ("order_date", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Order placement timestamp"),
    ]),
    ("6.6 order_items — Line items within an order", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique order item identifier"),
        ("order_id", "INT", "FK → orders(id)", "Parent order"),
        ("plant_id", "INT", "FK → plants(id)", "Plant ordered"),
        ("quantity", "INT", "NOT NULL", "Quantity ordered"),
        ("price", "FLOAT", "NOT NULL", "Unit price at time of order"),
    ]),
    ("6.7 services — Gardening services offered", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique service identifier"),
        ("name", "VARCHAR(150)", "NOT NULL", "Service name"),
        ("description", "TEXT", "NULL", "Detailed service description"),
        ("price", "FLOAT", "NOT NULL", "Service price in INR"),
        ("duration", "VARCHAR(100)", "NULL", "Estimated service duration (e.g., 2 Hours)"),
        ("availability", "VARCHAR(50)", "DEFAULT 'Available'", "Availability status"),
        ("image", "VARCHAR(255)", "NULL", "Filename of service image"),
    ]),
    ("6.8 service_bookings — Customer service booking records", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique booking identifier"),
        ("user_id", "INT", "FK → users(id)", "Customer who made the booking"),
        ("service_id", "INT", "FK → services(id)", "Service booked"),
        ("customer_name", "VARCHAR(100)", "NOT NULL", "Customer name for booking"),
        ("phone", "VARCHAR(20)", "NOT NULL", "Contact phone for the booking"),
        ("booking_date", "DATE", "NOT NULL", "Scheduled date of service"),
        ("booking_time", "VARCHAR(20)", "NOT NULL", "Preferred time slot"),
        ("address", "TEXT", "NOT NULL", "Service delivery address"),
        ("notes", "TEXT", "NULL", "Special instructions or notes"),
        ("status", "ENUM(...)", "DEFAULT 'Pending'", "Booking status (Pending/Confirmed/Completed/Cancelled)"),
        ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Booking creation timestamp"),
    ]),
    ("6.9 feedback — Customer platform feedback", [
        ("id", "INT", "PK, AUTO_INCREMENT", "Unique feedback identifier"),
        ("user_id", "INT", "FK → users(id)", "Customer who submitted the feedback"),
        ("message", "TEXT", "NOT NULL", "Feedback message text"),
        ("rating", "INT", "DEFAULT 5", "Overall rating (1–5 stars)"),
        ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "Feedback submission timestamp"),
    ]),
]

for t_title, cols in tables:
    add_heading(doc, t_title, level=2)
    add_table(doc,
        ["Column", "Data Type", "Constraints", "Description"],
        cols
    )
    doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 7. API ROUTES
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "7. API ROUTES", level=1)

route_sections = [
    ("7.1 Public Routes", [
        ("GET", "/", "Homepage — featured plants, categories, services, feedback"),
        ("GET", "/about", "About Us page"),
        ("GET", "/contact", "Contact page"),
        ("GET/POST", "/register", "User registration form"),
        ("GET/POST", "/login", "User login — redirects to role dashboard"),
        ("GET", "/logout", "Session logout"),
        ("GET", "/plants", "Plant listing with search, filter, and sort"),
        ("GET", "/plants/<id>", "Plant detail page"),
        ("GET", "/services", "Service listing"),
        ("GET", "/services/<id>", "Service detail page"),
    ]),
    ("7.2 Customer Routes (login required, role=customer)", [
        ("GET", "/cart", "View shopping cart with totals"),
        ("POST", "/cart/add/<plant_id>", "Add plant to cart"),
        ("POST", "/cart/buy-now/<plant_id>", "Direct buy → checkout"),
        ("POST", "/cart/update/<item_id>", "Update cart item quantity"),
        ("GET", "/cart/remove/<item_id>", "Remove item from cart"),
        ("GET/POST", "/checkout", "Order checkout with address and payment"),
        ("GET", "/order-success/<order_id>", "Order confirmation page"),
        ("GET", "/orders", "Customer order history"),
        ("GET/POST", "/services/<id>/book", "Book a gardening service"),
        ("GET", "/my-bookings", "Customer service booking history"),
        ("GET/POST", "/feedback", "Submit platform feedback"),
        ("GET/POST", "/profile", "Edit profile details"),
        ("POST", "/change-password", "Change account password"),
    ]),
    ("7.3 Seller Routes (login required, role=seller)", [
        ("GET", "/seller/dashboard", "Seller dashboard with statistics"),
        ("GET", "/seller/plants", "Seller plant inventory list"),
        ("GET/POST", "/seller/plants/add", "Add new plant listing"),
        ("GET/POST", "/seller/plants/edit/<id>", "Edit existing plant"),
        ("GET", "/seller/plants/delete/<id>", "Delete plant (blocked if ordered)"),
        ("GET", "/seller/orders", "Orders containing seller's plants"),
        ("POST", "/seller/orders/update/<id>", "Update order status"),
    ]),
    ("7.4 Admin Routes (login required, role=admin)", [
        ("GET", "/admin/dashboard", "Admin dashboard with platform-wide stats"),
        ("GET/POST", "/admin/categories", "List and add categories"),
        ("POST", "/admin/categories/edit/<id>", "Edit category"),
        ("GET", "/admin/categories/delete/<id>", "Delete category (blocked if plants assigned)"),
        ("GET", "/admin/plants", "All plants across all sellers"),
        ("GET", "/admin/plants/delete/<id>", "Delete plant (blocked if ordered)"),
        ("GET", "/admin/customers", "Customer user list"),
        ("GET", "/admin/customers/delete/<id>", "Delete customer account"),
        ("GET", "/admin/sellers", "Seller user list"),
        ("GET", "/admin/sellers/delete/<id>", "Delete seller account"),
        ("GET", "/admin/orders", "All platform orders"),
        ("GET", "/admin/feedback", "All customer feedback"),
        ("GET", "/admin/sales-report", "Sales analytics and revenue report"),
        ("GET/POST", "/admin/services", "List and add gardening services"),
        ("POST", "/admin/services/edit/<id>", "Edit service"),
        ("GET", "/admin/services/delete/<id>", "Delete service"),
        ("GET/POST", "/admin/profile", "Admin profile management"),
        ("POST", "/admin/change-password", "Admin password change"),
    ]),
]

for sec_title, routes in route_sections:
    add_heading(doc, sec_title, level=2)
    add_table(doc,
        ["Method", "Route", "Description"],
        routes
    )
    doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 8. CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "8. CONFIGURATION (config.py)", level=1)

add_para(doc,
    "The application configuration is centralised in config.py. "
    "The following key environment variables are used:"
)
doc.add_paragraph()

add_table(doc,
    ["Parameter", "Default Value", "Description"],
    [
        ["SECRET_KEY", "nursery-secret-key-2024", "Flask session encryption key. Change in production."],
        ["SQLALCHEMY_DATABASE_URI", "mysql+pymysql://root:@localhost/plant_nursery_db", "Database connection string."],
        ["SQLALCHEMY_TRACK_MODIFICATIONS", "False", "Disable SQLAlchemy event system overhead."],
        ["MAX_CONTENT_LENGTH", "16 * 1024 * 1024 (16 MB)", "Maximum file upload size."],
        ["UPLOAD_FOLDER_PLANTS", "static/images/plants", "Directory for plant image uploads."],
        ["UPLOAD_FOLDER_SERVICES", "static/images/services", "Directory for service image uploads."],
    ]
)

doc.add_paragraph()

add_code_block(doc,
    "# config.py example\n"
    "class Config:\n"
    "    SECRET_KEY = 'nursery-secret-key-2024'  # Change this!\n"
    "    SQLALCHEMY_DATABASE_URI = (\n"
    "        'mysql+pymysql://root:<password>@localhost/plant_nursery_db'\n"
    "    )\n"
    "    SQLALCHEMY_TRACK_MODIFICATIONS = False\n"
    "    MAX_CONTENT_LENGTH = 16 * 1024 * 1024"
)
doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# 9. TROUBLESHOOTING
# ════════════════════════════════════════════════════════════════════════════
add_heading(doc, "9. TROUBLESHOOTING", level=1)

issues = [
    (
        "Issue: 'No module named flask' or ImportError",
        "Ensure the virtual environment is activated before running the application.\n"
        "Run: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)\n"
        "Then: pip install -r requirements.txt"
    ),
    (
        "Issue: MySQL connection refused / OperationalError",
        "1. Verify MySQL service is running.\n"
        "2. Check the database URI in config.py — hostname, username, password.\n"
        "3. Create the database manually if needed: CREATE DATABASE plant_nursery_db;"
    ),
    (
        "Issue: 'Table doesn't exist' error on first run",
        "Run the SQL schema: mysql -u root -p < database.sql\n"
        "Then initialise the app: python app.py init-db"
    ),
    (
        "Issue: Image upload returns 413 Request Entity Too Large",
        "Increase MAX_CONTENT_LENGTH in config.py, e.g., 32 * 1024 * 1024 for 32 MB."
    ),
    (
        "Issue: Flask debug mode shows 'Address already in use'",
        "Another process is using port 5000. Use a different port:\n"
        "python app.py --port 5001\n"
        "Or kill the existing process using that port."
    ),
    (
        "Issue: Static files (CSS/JS) not loading",
        "Ensure you are running app.py from the project root directory, not from a subdirectory."
    ),
    (
        "Issue: 'Access denied for user root@localhost'",
        "Update config.py with correct MySQL credentials.\n"
        "If using a password: 'mysql+pymysql://root:YourPassword@localhost/plant_nursery_db'"
    ),
]

for title, solution in issues:
    add_para(doc, title, bold=True)
    add_code_block(doc, solution)
    doc.add_paragraph()


# ════════════════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════════════════
doc.save(OUTPUT_PATH)
print(f"README.docx saved to: {OUTPUT_PATH}")
