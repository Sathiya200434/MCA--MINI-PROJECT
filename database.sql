-- ============================================================================
-- PLANT NURSERY & GARDENING SERVICES E-COMMERCE PLATFORM
-- MySQL 8.0 Complete Database Schema & Seed Data
-- Database Name: plant_nursery
-- ============================================================================

CREATE DATABASE IF NOT EXISTS plant_nursery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE plant_nursery;

-- Disable foreign key checks during initialization
SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables if re-creating
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS service_bookings;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart_items;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS plants;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- 1. USERS TABLE
-- Roles: 'customer', 'seller', 'admin'
-- Status: 'Active', 'Inactive'
-- ============================================================================
CREATE TABLE users (
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

-- ============================================================================
-- 2. CATEGORIES TABLE
-- ============================================================================
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. PLANTS TABLE
-- ============================================================================
CREATE TABLE plants (
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

-- ============================================================================
-- 4. CART TABLE (Customer Active Cart Session)
-- ============================================================================
CREATE TABLE cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_cart_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. CART ITEMS TABLE
-- ============================================================================
CREATE TABLE cart_items (
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

-- ============================================================================
-- 6. ORDERS TABLE
-- ============================================================================
CREATE TABLE orders (
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

-- ============================================================================
-- 7. ORDER ITEMS TABLE
-- ============================================================================
CREATE TABLE order_items (
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

-- ============================================================================
-- 8. SERVICES TABLE (Gardening Packages)
-- ============================================================================
CREATE TABLE services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(150) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    duration VARCHAR(50),
    image VARCHAR(255) DEFAULT 'default_service.jpg',
    status VARCHAR(50) DEFAULT 'Available',
    INDEX idx_service_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. SERVICE BOOKINGS TABLE
-- ============================================================================
CREATE TABLE service_bookings (
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

-- ============================================================================
-- 10. FEEDBACK TABLE
-- ============================================================================
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    rating INT NOT NULL DEFAULT 5,
    comments TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_feedback_customer (customer_id),
    INDEX idx_feedback_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 11. PAYMENTS TABLE
-- ============================================================================
CREATE TABLE payments (
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

-- ============================================================================
-- 12. NOTIFICATIONS TABLE
-- ============================================================================
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_notification_user (user_id),
    INDEX idx_notification_read (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SAMPLE DATA INSERTION (Passwords are hashed via Werkzeug pbkdf2:sha256)
-- Default passwords:
--   Admin:    admin@nursery.com    / admin123
--   Seller:   seller@nursery.com   / seller123
--   Customer: customer@nursery.com / customer123
-- ============================================================================

INSERT INTO users (user_id, name, email, password, phone, address, role, status) VALUES
(1, 'Platform Admin', 'admin@nursery.com', 'scrypt:32768:8:1$u7c8aB8YxKxW7w$e4803d6d0d7cfca142dbe5ea7f4d0a3dcaea31934c9c7f66a2cb979f4859aef82b9921f008453472ad9b19df6dafeefc32df510ec0483d8031d77a8344e45e7e', '+91 99999 88888', 'Nursery Platform HQ, Green City', 'admin', 'Active'),
(2, 'Green Leaf Nursery', 'seller@nursery.com', 'scrypt:32768:8:1$u7c8aB8YxKxW7w$e4803d6d0d7cfca142dbe5ea7f4d0a3dcaea31934c9c7f66a2cb979f4859aef82b9921f008453472ad9b19df6dafeefc32df510ec0483d8031d77a8344e45e7e', '+91 88888 77777', 'Plot 42, Botanical Farm Road, Chennai', 'seller', 'Active'),
(3, 'Priya Sharma', 'customer@nursery.com', 'scrypt:32768:8:1$u7c8aB8YxKxW7w$e4803d6d0d7cfca142dbe5ea7f4d0a3dcaea31934c9c7f66a2cb979f4859aef82b9921f008453472ad9b19df6dafeefc32df510ec0483d8031d77a8344e45e7e', '+91 98765 43210', 'Flat 302, Palm Meadows, Green Road, Chennai', 'customer', 'Active');

INSERT INTO categories (category_id, category_name, description) VALUES
(1, 'Indoor Plants', 'Shade-loving, air-purifying plants ideal for apartments and offices'),
(2, 'Outdoor Plants', 'Sunlight-thriving shrubs, foliage, and garden landscaping varieties'),
(3, 'Flower Plants', 'Fragrant, vibrantly blooming ornamental plants and seasonal flowers'),
(4, 'Fruit Plants', 'Healthy grafted saplings yielding sweet citrus and seasonal fruits'),
(5, 'Vegetable Plants', 'Heirloom organic kitchen garden vegetables and daily fresh herbs'),
(6, 'Medicinal Plants', 'Ayurvedic therapeutic herbs and natural wellness botanical species'),
(7, 'Succulents', 'Drought-tolerant, fleshy geometric rosettes for low-maintenance decor'),
(8, 'Cactus', 'Resilient desert-adapted spined varieties that require minimal watering');

INSERT INTO plants (plant_id, seller_id, category_id, plant_name, botanical_name, description, price, stock, image, availability, sunlight, watering, rating) VALUES
(1, 2, 1, 'Money Plant', 'Epipremnum aureum', 'A classic indoor favourite known for bringing good fortune and purifying household air.', 199.00, 50, 'money-plant.jpg', 'In Stock', 'Indirect Light', 'Weekly', 4.8),
(2, 2, 1, 'Snake Plant', 'Dracaena trifasciata', 'Extremely resilient architectural houseplant that purifies air even overnight.', 299.00, 40, 'snake-plant.jpg', 'In Stock', 'Low to Bright', 'Bi-weekly', 4.9),
(3, 2, 1, 'Peace Lily', 'Spathiphyllum', 'Air-purifying indoor flowering plant with stunning white spathe blooms and glossy foliage.', 349.00, 25, 'peace-lily.jpg', 'In Stock', 'Filtered Light', 'Weekly', 4.8),
(4, 2, 1, 'Jade Plant', 'Crassula ovata', 'Classic money-tree succulent symbolising luck and prosperity with fleshy emerald leaves.', 249.00, 45, 'jade-plant.jpg', 'In Stock', 'Bright Light', 'Bi-weekly', 4.9),
(5, 2, 1, 'Lucky Bamboo', 'Dracaena sanderiana', 'Symbolic Feng Shui arrangement bringing positive energy and harmony to workspaces.', 189.00, 50, 'lucky-bamboo.jpg', 'In Stock', 'Indirect Light', 'Weekly', 4.7),
(6, 2, 1, 'Spider Plant', 'Chlorophytum comosum', 'Fast-growing graceful hanging plant that eliminates indoor airborne pollutants efficiently.', 159.00, 40, 'spider-plant.jpg', 'In Stock', 'Medium Light', 'Weekly', 4.6),
(7, 2, 3, 'Rose Plant', 'Rosa', 'Classic aromatic blooming red roses that elevate gardens, patios, and flower beds.', 149.00, 60, 'rose.jpg', 'In Stock', 'Full Sun', 'Daily', 4.7),
(8, 2, 3, 'Marigold', 'Tagetes', 'Golden festive blooms that repel pests naturally and brighten gardens with cheerful colour.', 99.00, 80, 'marigold.jpg', 'In Stock', 'Full Sun', 'Daily', 4.5),
(9, 2, 3, 'Jasmine', 'Jasminum', 'Intensely fragrant star-shaped white blossoms favoured for morning pooja and balcony arches.', 199.00, 40, 'jasmine.jpg', 'In Stock', 'Full Sun', 'Daily', 4.7),
(10, 2, 3, 'Hibiscus', 'Hibiscus rosa-sinensis', 'Stunning large crimson tropical flowers that bloom continuously with minimal effort.', 179.00, 35, 'hibiscus.jpg', 'In Stock', 'Full Sun', 'Daily', 4.6),
(11, 2, 3, 'Bougainvillea', 'Bougainvillea spectabilis', 'Vibrant magenta flowering creeper ideal for sunny terraces, fences, and garden pergolas.', 229.00, 30, 'bougainvillea.jpg', 'In Stock', 'Direct Sunlight', 'Low', 4.5),
(12, 2, 4, 'Mango Sapling', 'Mangifera indica', 'Healthy grafted tropical mango sapling that yields sweet, aromatic fruit in season.', 399.00, 25, 'mango-sapling.jpg', 'In Stock', 'Full Sun', 'Twice a week', 4.6),
(13, 2, 4, 'Lemon Plant', 'Citrus limon', 'Fragrant citrus tree that produces abundant fresh juicy lemons all year round.', 249.00, 30, 'lemon-plant.jpg', 'In Stock', 'Full Sun', 'Twice a week', 4.7),
(14, 2, 5, 'Tomato Plant', 'Solanum lycopersicum', 'Vigorous heirloom tomato plant ideal for kitchen gardens and large balcony pots.', 79.00, 100, 'tomato-plant.jpg', 'In Stock', 'Full Sun', 'Daily', 4.4),
(15, 2, 5, 'Chilli Plant', 'Capsicum annuum', 'High-yielding spicy green chilli plant essential for every home culinary garden.', 69.00, 90, 'chilli-plant.jpg', 'In Stock', 'Full Sun', 'Daily', 4.5),
(16, 2, 6, 'Aloe Vera', 'Aloe barbadensis', 'Healing succulent revered for therapeutic gel, soothing skin burns and purifying air.', 129.00, 70, 'aloevera.jpg', 'In Stock', 'Bright Indirect', 'Bi-weekly', 4.9),
(17, 2, 6, 'Tulsi', 'Ocimum tenuiflorum', 'Sacred Ayurvedic herb celebrated for spiritual presence and potent herbal tea wellness.', 89.00, 85, 'tulsi.jpg', 'In Stock', 'Full Sun', 'Daily', 4.9),
(18, 2, 7, 'Echeveria Succulent', 'Echeveria elegans', 'Compact geometrical rosette succulent, drought-tolerant and perfect for tabletop decor.', 179.00, 45, 'succulent.jpg', 'In Stock', 'Bright Light', 'Bi-weekly', 4.8),
(19, 2, 8, 'Barrel Cactus', 'Echinocactus grusonii', 'Iconic golden-spined desert cactus that thrives on negligible maintenance and sunlight.', 219.00, 35, 'cactus.jpg', 'In Stock', 'Full Sun', 'Monthly', 4.7),
(20, 2, 2, 'Bonsai Ficus', 'Ficus microcarpa', 'Masterfully trained miniature bonsai tree creating a serene Zen atmosphere in any room.', 599.00, 15, 'bonsai-ficus.jpg', 'In Stock', 'Bright Indirect', 'Weekly', 4.9),
(21, 2, 2, 'Areca Palm', 'Dypsis lutescens', 'Luxurious feathery palm that adds tropical elegance and acts as a natural humidifier.', 449.00, 20, 'areca-palm.jpg', 'In Stock', 'Bright Indirect', 'Weekly', 4.8);

INSERT INTO services (service_id, service_name, description, price, duration, status, image) VALUES
(1, 'Garden Maintenance', 'Comprehensive scheduled garden upkeep including weeding, hedge trimming, organic fertilizing and cleanup.', 499.00, '2 hours', 'Available', 'garden-maintenance.jpg'),
(2, 'Plant Care', 'Expert botanical diagnostic inspection, pest control treatment, repotting advice and health boosting for plants.', 299.00, '1 hour', 'Available', 'plant-care.jpg'),
(3, 'Terrace Gardening', 'Complete design, waterproof planter setup, organic soil preparation, and planting tailored for terraces.', 999.00, '3 hours', 'Available', 'terrace-garden.jpg'),
(4, 'Balcony Garden Setup', 'Custom urban balcony transformation with hanging planters, vertical railing hooks and weather-resistant greens.', 799.00, '2-3 hours', 'Available', 'balcony-garden.jpg'),
(5, 'Lawn Maintenance', 'Professional precision mowing, edging, weed eradication, dethatching, and lawn nutrient enrichment.', 599.00, '2 hours', 'Available', 'lawn-maintenance.jpg'),
(6, 'Plant Pruning', 'Aesthetic and restorative pruning of ornamental shrubs, rose bushes, and fruit trees to encourage lush blooming.', 349.00, '1 hour', 'Available', 'plant-pruning.jpg'),
(7, 'Landscape Gardening', 'Architectural landscape design, stone pathways, flower beds, and premium garden overhaul by senior horticulturists.', 1999.00, '1 day', 'Available', 'landscape-design.jpg'),
(8, 'Vertical Garden Installation', 'Custom engineered living wall system for indoor and outdoor accent walls with built-in drip irrigation.', 2499.00, '1-2 days', 'Available', 'vertical-garden.jpg'),
(9, 'Garden Cleaning', 'Deep seasonal garden clearing, debris raking, weed removal, leaf mulching, and bed soil conditioning.', 599.00, '2-3 hours', 'Available', 'garden-cleaning.jpg'),
(10, 'Indoor Plant Setup', 'Curated interior plant styling, designer planter coordination, and light-optimized placement for apartments.', 899.00, '2 hours', 'Available', 'indoor-plant-setup.jpg'),
(11, 'Drip Irrigation Setup', 'Automated smart micro-drip irrigation system installation to save 70% water and ensure consistent hydration.', 1499.00, '4 hours', 'Available', 'drip-irrigation.jpg');

INSERT INTO orders (order_id, order_code, customer_id, total_amount, delivery_address, payment_method, payment_status, order_status, order_date) VALUES
(1, 'ORD98234120', 3, 498.00, 'Flat 302, Palm Meadows, Green Road, Chennai - 600028 | Ph: 9876543210', 'Cash on Delivery', 'Paid', 'Delivered', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(2, 'ORD78129034', 3, 349.00, 'Flat 302, Palm Meadows, Green Road, Chennai - 600028 | Ph: 9876543210', 'Cash on Delivery', 'Pending', 'Processing', NOW());

INSERT INTO order_items (order_item_id, order_id, plant_id, seller_id, quantity, price) VALUES
(1, 1, 1, 2, 1, 199.00),
(2, 1, 2, 2, 1, 299.00),
(3, 2, 3, 2, 1, 349.00);

INSERT INTO payments (payment_id, order_id, payment_method, amount, payment_status, transaction_date) VALUES
(1, 1, 'Cash on Delivery', 498.00, 'Paid', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(2, 2, 'Cash on Delivery', 349.00, 'Pending', NOW());

INSERT INTO service_bookings (booking_id, customer_id, service_id, customer_name, phone, booking_date, booking_time, address, requirements, booking_status) VALUES
(1, 3, 1, 'Priya Sharma', '+91 98765 43210', '2026-11-25', '09:00 AM - 11:00 AM', 'Flat 302, Palm Meadows, Green Road, Chennai', 'Pruning balcony bougainvillea and soil conditioning for money plants', 'Confirmed');

INSERT INTO feedback (feedback_id, customer_id, rating, comments) VALUES
(1, 3, 5, 'The plants arrived in immaculate condition! The packaging completely secured the soil and delicate stems. My snake plant and money plant are thriving on my workstation.');

INSERT INTO notifications (notification_id, user_id, message, is_read) VALUES
(1, 3, 'Welcome to Plant Nursery! Explore our thriving botanicals and book expert gardening visits.', TRUE),
(2, 3, 'Your order #ORD78129034 has been placed and is currently being processed by Green Leaf Nursery.', FALSE);
