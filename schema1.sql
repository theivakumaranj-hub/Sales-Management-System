-- ==========================================
-- 1. DATABASE STRUCTURE (TABLES)
-- ==========================================

-- Branches Table 
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100) NOT NULL
);

-- Users Table 
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    branch_id INT REFERENCES branches(branch_id),
    role VARCHAR(20) CHECK (role IN ('Super Admin', 'Admin')) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Customer Sales Table 
CREATE TABLE customer_sales (
    sale_id SERIAL PRIMARY KEY,
    branch_id INT REFERENCES branches(branch_id),
    date DATE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) UNIQUE NOT NULL,
    product_name VARCHAR(30) NOT NULL,
    gross_sales DECIMAL(12,2) NOT NULL,
    received_amount DECIMAL(12,2) DEFAULT 0.00,
    -- AUTO-CALCULATION: Handles financial math in the backend 
    pending_amount DECIMAL(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
    status VARCHAR(5) CHECK (status IN ('Open', 'Close')) NOT NULL
);

-- Payment Splits Table 
CREATE TABLE payment_splits (
    payment_id SERIAL PRIMARY KEY,
    sale_id INT REFERENCES customer_sales(sale_id),
    payment_date DATE NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL
);

-- ==========================================
-- 2. DATABASE AUTOMATION (TRIGGERS)
-- ==========================================

-- Trigger 1: Syncs received_amount when a payment is made (Your original code)
CREATE OR REPLACE FUNCTION update_received_amount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET received_amount = (
        SELECT COALESCE(SUM(amount_paid), 0) 
        FROM payment_splits 
        WHERE sale_id = NEW.sale_id
    )
    WHERE sale_id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_payment_insert
AFTER INSERT ON payment_splits
FOR EACH ROW
EXECUTE FUNCTION update_received_amount();


-- Trigger 2: Automatically flips the status from Open to Close (The new addition)
CREATE OR REPLACE FUNCTION update_sale_status()
RETURNS TRIGGER AS $$
BEGIN
    -- We do the math manually here to ensure the text flips at exactly 0
    IF (NEW.gross_sales - NEW.received_amount) <= 0 THEN
        NEW.status = 'Close';
    ELSE
        NEW.status = 'Open'; 
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_payment_status
BEFORE UPDATE ON customer_sales
FOR EACH ROW
EXECUTE FUNCTION update_sale_status();

-- ==========================================
-- 3. INITIAL DATA MAINTENANCE (OPTIONAL)
-- ==========================================

-- Syncing legacy data imported from CSV [cite: 5, 6]
UPDATE customer_sales SET status = 'Close' WHERE (gross_sales - received_amount) <= 0;
