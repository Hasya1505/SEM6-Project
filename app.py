"""
Medical Store Billing and Inventory Management System
Flask Application - Main Entry Point
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
import mysql.connector
from datetime import datetime, timedelta
import hashlib
import csv
import io
import os
from werkzeug.utils import secure_filename
from config import Config
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
import uuid
from flask_mail import Mail, Message
app = Flask(__name__)
app.config.from_object(Config)

# ============================================
# DATABASE CONNECTION
# ============================================
def get_db():
    """Create MySQL database connection"""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_setting(key, default=None):
    """Get a single setting value from database"""
    db = get_db()
    if not db:
        return default
    
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
        result = cursor.fetchone()
        db.close()
        
        if result:
            return result['setting_value']
        return default
    except:
        return default


def get_all_settings():
    """Get all settings as a dictionary"""
    db = get_db()
    if not db:
        return {}
    
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        results = cursor.fetchall()
        db.close()
        
        settings_dict = {}
        for row in results:
            settings_dict[row['setting_key']] = row['setting_value']
        return settings_dict
    except:
        return {}

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_bill_number():
    """Generate unique bill number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    # invoice_prefix = get_setting('invoice_prefix', 'INV')
    invoice_prefix = 'INV'
    return f"{invoice_prefix}-{timestamp}"

def calculate_gst(amount):
    """Calculate GST amount using rate from settings"""
    # gst_rate = float(get_setting('gst_rate', '12.0'))
    gst_rate = 12.0

    return round(amount * gst_rate / 100, 2)

def generate_purchase_number():
    """Generate unique purchase order number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"PO-{timestamp}"

# ============================================
# AUTHENTICATION ROUTES
# ============================================
@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        if session.get('role') == 'owner':
            return redirect(url_for('dashboard'))
        return redirect(url_for('billing'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    # If user is already logged in, redirect to appropriate page
    if 'user_id' in session:
        if session.get('role') == 'owner':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('billing'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = hash_password(password)
        
        db = get_db()
        if db:
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, hashed_password)
            )
            user = cursor.fetchone()
            db.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                
                if user['role'] == 'owner':
                    return redirect(url_for('dashboard'))
                return redirect(url_for('billing'))
            
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')
@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')
@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))
@app.route('/signup', methods=['GET','POST'])
def signup():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        hashed_password = hash_password(password)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO users (username,password,full_name,role)
            VALUES (%s,%s,%s,'staff')
        """,(username,hashed_password,full_name))

        db.commit()
        db.close()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')
# ============================================
# DASHBOARD ROUTES
# ============================================
@app.route('/dashboard')
def dashboard():
    """Owner dashboard with analytics - Updated for new Supplier Schema"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # --- SALES & INVENTORY METRICS ---
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM bills")
    total_revenue = cursor.fetchone()['total_revenue']
    
    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0) as today_sales 
        FROM bills WHERE DATE(bill_date) = CURDATE()
    """)
    today_sales = cursor.fetchone()['today_sales']
    
    cursor.execute("SELECT COUNT(*) as total_products FROM products")
    total_products = cursor.fetchone()['total_products']
    
    cursor.execute("""
        SELECT COUNT(*) as low_stock_count FROM products 
        WHERE stock_quantity < min_stock_level
    """)
    low_stock_count = cursor.fetchone()['low_stock_count']

    # --- EXPIRY ALERTS ---
    cursor.execute("""
        SELECT COUNT(*) as count FROM products 
        WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 50 DAY)
    """)
    expiring_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM products WHERE expiry_date < CURDATE()")
    expired_count = cursor.fetchone()['count']
    
    # --- RECENT ACTIVITY ---
    cursor.execute("SELECT * FROM bills ORDER BY bill_date DESC LIMIT 10")
    recent_bills = cursor.fetchall()
    
    cursor.execute("""
        SELECT bi.medicine_name, SUM(bi.quantity) as total_sold, 
               SUM(bi.total_amount) as revenue
        FROM bill_items bi
        GROUP BY bi.medicine_name ORDER BY total_sold DESC LIMIT 5
    """)
    top_products = cursor.fetchall()
    
    # --- CHART DATA ---
    cursor.execute("""
        SELECT DATE(bill_date) as date, COALESCE(SUM(total_amount), 0) as daily_sales
        FROM bills WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(bill_date) ORDER BY date
    """)
    sales_chart = cursor.fetchall()
    
    cursor.execute("""
        SELECT DATE_FORMAT(bill_date, '%Y-%m') as month, COALESCE(SUM(total_amount), 0) as monthly_sales
        FROM bills WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(bill_date, '%Y-%m') ORDER BY month
    """)
    monthly_sales = cursor.fetchall()
    
    # --- SUPPLIER & PROCUREMENT INTEL (FIXED FOR NEW SCHEMA) ---
    
    # 1. Total Purchase Value (Lifetime)
    cursor.execute("""
        SELECT COALESCE(SUM(total_purchase_value), 0) as total_purchase_amount
        FROM supplier_purchases WHERE received_count > 0
    """)
    total_purchase_amount = cursor.fetchone()['total_purchase_amount']
    
    # 2. Today's Procurement Cost
    cursor.execute("""
        SELECT COALESCE(SUM(total_purchase_value), 0) as today_purchase
        FROM supplier_purchases 
        WHERE DATE(last_updated) = CURDATE() AND received_count > 0
    """)
    today_purchase = cursor.fetchone()['today_purchase']
    
    # 3. Pending Orders (Logic change: No 'status' column)
    cursor.execute("SELECT COUNT(*) as count FROM supplier_purchases WHERE pending_orders > 0")
    pending_orders_count = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT sp.id as purchase_id, sp.medicine_name, sp.total_orders as quantity, 
               sp.medicine_price * sp.total_orders as total_amount,
               sp.order_date, sp.expected_delivery_date, sp.supplier_id,
               s.name as supplier_name, s.company_name, s.phone
        FROM supplier_purchases sp
        JOIN suppliers s ON sp.supplier_id = s.id
        WHERE sp.pending_orders > 0 ORDER BY sp.expected_delivery_date ASC
    """)
    pending_orders = cursor.fetchall()

    # --- FINANCIAL ANALYTICS ---
    cursor.execute("SELECT COALESCE(SUM(stock_quantity * price), 0) as inventory_value FROM products")
    inventory_value = cursor.fetchone()['inventory_value']
    
    # Data Conversion
    total_revenue = float(total_revenue)
    total_purchase_amount = float(total_purchase_amount)
    inventory_value = float(inventory_value)
    today_sales = float(today_sales)
    today_purchase = float(today_purchase)
    
    # Profit & KPIs
    gross_profit = total_revenue - total_purchase_amount
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    today_profit = today_sales - today_purchase
    inventory_turnover = (total_purchase_amount / inventory_value) if inventory_value > 0 else 0
    
    # GST (18% logic)
    GST_RATE = 0.18
    gst_collected = total_revenue * GST_RATE / (1 + GST_RATE)
    gst_paid = total_purchase_amount * GST_RATE / (1 + GST_RATE)
    net_gst_liability = gst_collected - gst_paid
    
    # --- MONTHLY PROFIT TREND (FIXED) ---
    cursor.execute("""
        SELECT DATE_FORMAT(bill_date, '%Y-%m') as month, COALESCE(SUM(total_amount), 0) as rev
        FROM bills WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY month ORDER BY month
    """)
    rev_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT DATE_FORMAT(last_updated, '%Y-%m') as month, COALESCE(SUM(total_purchase_value), 0) as pur
        FROM supplier_purchases 
        WHERE received_count > 0 AND last_updated >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY month ORDER BY month
    """)
    pur_data = cursor.fetchall()
    
    monthly_profit = {r['month']: {'revenue': float(r['rev']), 'purchase': 0} for r in rev_data}
    for p in pur_data:
        if p['month'] in monthly_profit:
            monthly_profit[p['month']]['purchase'] = float(p['pur'])
        else:
            monthly_profit[p['month']] = {'revenue': 0, 'purchase': float(p['pur'])}
    
    # Additional Analytics
    cursor.execute("""
        SELECT manufacturer, COUNT(*) as product_count, SUM(stock_quantity) as total_stock,
               SUM(stock_quantity * price) as stock_value
        FROM products WHERE manufacturer IS NOT NULL AND manufacturer != ''
        GROUP BY manufacturer ORDER BY total_stock DESC LIMIT 10
    """)
    company_stock = cursor.fetchall()
    
    cursor.execute("""
        SELECT bi.medicine_name, SUM(bi.quantity) as total_sold, SUM(bi.total_amount) as revenue
        FROM bill_items bi GROUP BY bi.medicine_name ORDER BY revenue DESC LIMIT 10
    """)
    top_selling_medicines = cursor.fetchall()
    
    db.close()
    
    return render_template('dashboard.html',
                         total_revenue=total_revenue,
                         today_sales=today_sales,
                         total_products=total_products,
                         low_stock_count=low_stock_count,
                         expiring_soon_count=expiring_count, 
                         expired_count=expired_count,
                         recent_bills=recent_bills,
                         top_products=top_products,
                         sales_chart=sales_chart,
                         monthly_sales=monthly_sales,
                         company_stock=company_stock,
                         top_selling_medicines=top_selling_medicines,
                         pending_orders_count=pending_orders_count,
                         pending_orders=pending_orders,
                         total_purchase_amount=total_purchase_amount,
                         inventory_value=inventory_value,
                         gross_profit=gross_profit,
                         profit_margin=profit_margin,
                         gst_collected=gst_collected,
                         gst_paid=gst_paid,
                         net_gst_liability=net_gst_liability,
                         today_purchase=today_purchase,
                         today_profit=today_profit,
                         inventory_turnover=inventory_turnover,
                         monthly_profit=monthly_profit,
                         settings={"currency_symbol": "₹"})
@app.context_processor
def inject_expiry_counts():
    """Automatically provides expiry counts to all templates (base.html)"""
    # Check if user is logged in before running the query
    if 'user_id' in session:
        db = get_db()
        if db:
            try:
                cursor = db.cursor(dictionary=True)
                # Query for items expiring within 50 days
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM products 
                    WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 50 DAY)
                """)
                result = cursor.fetchone()
                db.close()
                
                # This name MUST match what is in your base.html
                return dict(expiring_soon_count=result['count'] if result else 0)
            except Exception as e:
                print(f"Context Processor Error: {e}")
                if db: db.close()
    
    # Default value if not logged in or database error occurs
    return dict(expiring_soon_count=0)
# ============================================
# BILLING ROUTES
# ============================================
@app.route('/billing')
def billing():
    """Billing page - search and add to cart"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('billing.html', 
                         cart=session.get('cart', []),
                         search_results=session.get('search_results', []))

@app.route('/search_medicine', methods=['POST'])
def search_medicine():
    """Search medicines by name, manufacturer, category, or price (Multi-term support)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_query = request.form.get('search', '').strip()
    
    if not search_query:
        flash('Please enter a search term', 'warning')
        return redirect(url_for('billing'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('billing'))
    
    cursor = db.cursor(dictionary=True)
    
    # 1. Split search query into individual terms (handling spaces and commas)
    # Example: "Paracetamol 150" becomes ['Paracetamol', '150']
    terms = search_query.replace(',', ' ').split()
    
    if not terms:
        terms = [search_query] # Fallback

    # 2. Build dynamic SQL query
    # We want rows that match Term1 OR Term2 OR Term3...
    conditions = []
    params = []
    
    for term in terms:
        # Create a group check for this specific term against all columns
        # (Name matches Term OR Manufacturer matches Term OR Price matches Term...)
        term_condition = "(name LIKE %s OR manufacturer LIKE %s OR category LIKE %s OR price LIKE %s)"
        conditions.append(term_condition)
        
        # Add the parameter 4 times (one for each ? in the line above)
        search_pattern = f'%{term}%'
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    # 3. Join all term groups with OR
    # This ensures "Para Dolo" returns both Paracetamol AND Dolo results
    where_clause = " OR ".join(conditions)
    
    query = f"""
        SELECT * FROM products 
        WHERE ({where_clause})
        LIMIT 50
    """
    
    cursor.execute(query, tuple(params))
    
    results = cursor.fetchall()
    db.close()
    
    session['search_results'] = results
    
    if not results:
        flash(f'No medicines found for "{search_query}"', 'info')
    
    return redirect(url_for('billing'))\
# ============================================
# EXPIRY MANAGEMENT ROUTES
# ============================================

@app.route('/expiry_alerts')
def expiry_alerts():
    """View medicines nearing expiry"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash("Database connection error", "danger")
        return redirect(url_for('dashboard'))
        
    cursor = db.cursor(dictionary=True)
    
    # Fetch expiring items for the table
    cursor.execute("""
        SELECT *, DATEDIFF(expiry_date, CURDATE()) as days_left
        FROM products 
        WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 50 DAY)
        ORDER BY expiry_date ASC
    """)
    expiring_soon = cursor.fetchall()
    
    # Fetch already expired items
    cursor.execute("""
        SELECT *, DATEDIFF(CURDATE(), expiry_date) as days_past
        FROM products 
        WHERE expiry_date < CURDATE()
        ORDER BY expiry_date DESC
    """)
    expired_items = cursor.fetchall()
    
    db.close()
    
    # You no longer need to pass expiring_soon_count here manually!
    return render_template('expiry_alerts.html', 
                         expiring_soon=expiring_soon, 
                         expired_items=expired_items)
    
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add medicine to cart"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('billing'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    db.close()
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('billing'))
    
    cart = session.get('cart', [])
    
    # Check if product already in cart
    existing_item = next((item for item in cart if item['id'] == product_id), None)
    
    if existing_item:
        # Check if total quantity (existing + new) exceeds stock
        total_quantity = existing_item['quantity'] + quantity
        if total_quantity > product['stock_quantity']:
            flash(f'Cannot add {quantity} more! Only {product["stock_quantity"]} units available and {existing_item["quantity"]} already in cart', 'warning')
            return redirect(url_for('billing'))
        existing_item['quantity'] = total_quantity
        existing_item['stock_quantity'] = product['stock_quantity']  # Update stock info
    else:
        # New item - check if requested quantity exceeds stock
        if quantity > product['stock_quantity']:
            flash(f'Insufficient stock! Only {product["stock_quantity"]} units available', 'warning')
            return redirect(url_for('billing'))
        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': float(product['price']),
            'quantity': quantity,
            'stock_quantity': product['stock_quantity']
        })
    
    session['cart'] = cart
    session.pop('search_results', None)  # Clear search results after adding to cart
    flash(f'{product["name"]} added to cart', 'success')
    
    return redirect(url_for('billing'))

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    """Remove item from cart"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['id'] != product_id]
    flash('Item removed from cart', 'info')
    
    return redirect(url_for('billing'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    """Update cart quantities"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart = session.get('cart', [])
    
    for item in cart:
        qty_key = f'quantity_{item["id"]}'
        if qty_key in request.form:
            new_qty = int(request.form.get(qty_key, 1))
            if new_qty <= item['stock_quantity']:
                item['quantity'] = new_qty
            else:
                flash(f'Quantity for {item["name"]} exceeds stock!', 'warning')
    
    session['cart'] = cart
    flash('Cart updated', 'success')
    
    return redirect(url_for('billing'))

# --- Line 727: Full Corrected Checkout Function ---
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout and generate bill with advanced payment mode support"""
    # 1. Check Authentication
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # 2. Validate Cart
    cart = session.get('cart', [])
    if not cart:
        flash('Cart is empty!', 'warning')
        return redirect(url_for('billing'))
    
    # 3. Get Store Settings (Fixes Jinja2 UndefinedError)
    store_settings = get_all_settings()
    if not store_settings: 
        # Safety fallback if settings table is empty
        store_settings = {
            "store_name": "My Medical Store",
            "upi_id": "pharmacy@upi",
            "gst_rate": "12.0"
        }
    
    # 4. Handle Final Bill Generation (POST)
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        customer_address = request.form.get('customer_address', '').strip()
        customer_id = request.form.get('customer_id', '')
        
        # Capture the new Payment Mode from the radio buttons
        payment_mode = request.form.get('payment_mode', 'cash') 
        
        # Handle walk-in defaults
        if not customer_phone:
            customer_phone = '0000000000'
        if not customer_name:
            customer_name = 'Walk-in Customer'
        
        db = get_db()
        if not db:
            flash('Database connection error', 'danger')
            return redirect(url_for('billing'))
        
        try:
            cursor = db.cursor(dictionary=True)
            
            # Find or create customer
            if customer_id:
                customer_id = int(customer_id)
            else:
                cursor.execute("SELECT id FROM customers WHERE phone = %s", (customer_phone,))
                existing = cursor.fetchone()
                if existing:
                    customer_id = existing['id']
                else:
                    cursor.execute("""
                        INSERT INTO customers (name, phone, email, address)
                        VALUES (%s, %s, %s, %s)
                    """, (customer_name, customer_phone, customer_email, customer_address))
                    customer_id = cursor.lastrowid
            
            # Calculate Totals
            subtotal = sum(item['price'] * item['quantity'] for item in cart)
            gst_amount = calculate_gst(subtotal)
            total_amount = subtotal + gst_amount
            bill_number = generate_bill_number()
            
            # Insert bill with the NEW payment_mode column
            cursor.execute("""
                INSERT INTO bills (bill_number, customer_id, customer_name, phone, 
                                 subtotal, gst, total_amount, created_by, payment_mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (bill_number, customer_id, customer_name, customer_phone, 
                  subtotal, gst_amount, total_amount, session.get('user_id'), payment_mode))
            
            bill_id = cursor.lastrowid
            
            # Insert items and update stock
            for item in cart:
                cursor.execute("""
                    INSERT INTO bill_items (bill_id, product_id, medicine_name, price, quantity, total_amount) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (bill_id, item['id'], item['name'], item['price'], item['quantity'], 
                      item['price'] * item['quantity']))
                
                cursor.execute("UPDATE products SET stock_quantity = stock_quantity - %s WHERE id = %s", 
                              (item['quantity'], item['id']))
            
            db.commit()
            session['cart'] = [] # Clear cart after success
            flash(f'Bill {bill_number} generated successfully via {payment_mode.upper()}!', 'success')
            return redirect(url_for('invoice', bill_id=bill_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Error processing checkout: {str(e)}', 'danger')
            return redirect(url_for('billing'))
        finally:
            db.close()
    
    # 5. Display Checkout Page (GET)
    # Re-calculate totals for display
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    gst_amount = calculate_gst(subtotal)
    total_amount = subtotal + gst_amount
    
    # Pass 'settings' here to fix the UndefinedError in the frontend
    return render_template('checkout.html', 
                         cart=cart,
                         subtotal=subtotal,
                         gst_amount=gst_amount,
                         total_amount=total_amount,
                         customer_info=session.get('customer_info'),
                         settings=store_settings)

# --- Line 832: Full Corrected Invoice Function ---
@app.route('/invoice/<int:bill_id>')
def invoice(bill_id):
    """Display official invoice with dynamic payment mode and UPI QR code"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    try:
        cursor = db.cursor(dictionary=True)
        
        # 1. Fetch Bill Details (Includes the new payment_mode column)
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        bill = cursor.fetchone()
        
        if not bill:
            flash('Bill not found', 'danger')
            return redirect(url_for('billing'))
        
        # 2. Fetch Items for this specific bill
        cursor.execute("SELECT * FROM bill_items WHERE bill_id = %s", (bill_id,))
        bill_items = cursor.fetchall()
        
        # 3. Prepare Store Settings for Template
        # We fetch all settings to ensure upi_id, store_name, and address are available
        store_settings = get_all_settings()
        
        # Fallback values if specific settings are missing in the database
        if 'upi_id' not in store_settings:
            store_settings['upi_id'] = 'pharmacy@upi'
        if 'store_name' not in store_settings:
            store_settings['store_name'] = 'My Medical Store'
        if 'gst_rate' not in store_settings:
            store_settings['gst_rate'] = '12.0'

        # 4. Render the Template
        return render_template('invoice.html', 
                             bill=bill, 
                             bill_items=bill_items, 
                             settings=store_settings)
                             
    except Exception as e:
        flash(f'Error generating invoice: {str(e)}', 'danger')
        return redirect(url_for('bills'))
    finally:
        db.close()

# ============================================
# INVENTORY ROUTES
# ============================================
@app.route('/inventory')
def inventory():
    """View all products"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products ORDER BY name")
    products = cursor.fetchall()
    db.close()
    
    # Get settings for display
    store_settings = get_all_settings()
    
    return render_template('inventory.html', products=products, settings=store_settings)
    return render_template('inventory.html', products=products)
# ============================================
# CATEGORY ANALYSIS ROUTES
# ============================================

@app.route('/category_analysis')
def category_analysis():
    """Medicine Category-Based Sales and Inventory View"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # 1. Category Sales Analysis & Graph Data
    # Calculates total units sold and revenue per category
    cursor.execute("""
        SELECT 
            p.category, 
            COALESCE(SUM(bi.quantity), 0) as total_units_sold,
            COALESCE(SUM(bi.total_amount), 0) as category_revenue
        FROM products p
        LEFT JOIN bill_items bi ON p.id = bi.product_id
        WHERE p.category IS NOT NULL AND p.category != ''
        GROUP BY p.category
        ORDER BY total_units_sold DESC
    """)
    category_summary = cursor.fetchall()
    
    # 2. Category-Based Medicine Grouping
    # Fetches detailed medicine data grouped by category
    cursor.execute("""
        SELECT 
            p.category, p.name, p.manufacturer, 
            p.stock_quantity, p.shelf_location,
            (SELECT COALESCE(SUM(quantity), 0) FROM bill_items WHERE product_id = p.id) as units_sold
        FROM products p
        WHERE p.category IS NOT NULL AND p.category != ''
        ORDER BY p.category ASC, units_sold DESC
    """)
    raw_medicines = cursor.fetchall()
    
    # Organize medicines into a dictionary: { 'Category Name': [List of Medicines] }
    grouped_medicines = {}
    for med in raw_medicines:
        cat = med['category']
        if cat not in grouped_medicines:
            grouped_medicines[cat] = []
        grouped_medicines[cat].append(med)
        
    db.close()
    
    return render_template('category_analysis.html', 
                         category_summary=category_summary,
                         grouped_medicines=grouped_medicines)
    
@app.route('/low_stock')
def low_stock():
    """View low stock items"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM products 
        WHERE stock_quantity < min_stock_level 
        ORDER BY stock_quantity ASC
    """)
    low_stock_items = cursor.fetchall()
    db.close()
    
    # Get settings for display
    store_settings = get_all_settings()
    
    return render_template('low_stock.html', products=low_stock_items, settings=store_settings)
    return render_template('low_stock.html', products=low_stock_items)
# ============================================
# REFUND & RETURN ROUTES
# ============================================

@app.route('/process_return/<int:bill_id>', methods=['POST'])
def process_return(bill_id):
    """Process a full or partial return of a previous bill"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # 1. Fetch the original bill
        cursor.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
        original_bill = cursor.fetchone()

        if not original_bill or original_bill['type'] == 'return':
            flash('Original bill not found or already returned.', 'danger')
            return redirect(url_for('bills'))

        # 2. Fetch original items
        cursor.execute("SELECT * FROM bill_items WHERE bill_id = %s", (bill_id,))
        original_items = cursor.fetchall()

        # 3. Generate a Refund Bill Number
        refund_bill_number = "REF-" + original_bill['bill_number'].split('-')[-1]
        
        # 4. Insert the Refund Bill (Negative amounts for accounting)
        cursor.execute("""
            INSERT INTO bills (bill_number, customer_id, customer_name, phone, 
                             subtotal, gst, total_amount, created_by, payment_mode, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'return')
        """, (
            refund_bill_number, 
            original_bill['customer_id'], 
            original_bill['customer_name'], 
            original_bill['phone'],
            -abs(original_bill['subtotal']), 
            -abs(original_bill['gst']), 
            -abs(original_bill['total_amount']), 
            session.get('user_id'), 
            original_bill['payment_mode']
        ))
        
        refund_id = cursor.lastrowid

        # 5. Reverse Stock and Record Items
        for item in original_items:
            # Re-add items to inventory
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + %s 
                WHERE id = %s
            """, (item['quantity'], item['product_id']))

            # Record item in refund bill
            cursor.execute("""
                INSERT INTO bill_items (bill_id, product_id, medicine_name, price, quantity, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (refund_id, item['product_id'], item['medicine_name'], item['price'], item['quantity'], -abs(item['total_amount'])))

        db.commit()
        flash(f'Refund Bill {refund_bill_number} generated successfully! Stock updated.', 'success')
        return redirect(url_for('invoice', bill_id=refund_id))

    except Exception as e:
        db.rollback()
        flash(f'Error processing return: {str(e)}', 'danger')
        return redirect(url_for('bills'))
    finally:
        db.close()
        
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """Add new product"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        db = get_db()
        if not db:
            flash('Database connection error', 'danger')
            return redirect(url_for('add_product'))
        
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO products (name, manufacturer, price, stock_quantity, 
                                shelf_location, category, usage_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            request.form.get('name'),
            request.form.get('manufacturer'),
            float(request.form.get('price')),
            int(request.form.get('stock_quantity', 0)),
            request.form.get('shelf_location'),
            request.form.get('category'),
            request.form.get('usage_type')
        ))
        
        db.commit()
        db.close()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('inventory'))
    
    return render_template('add_product.html')

@app.route('/import_csv')
def import_csv_page():
    """CSV Import page"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    return render_template('import_csv.html')

@app.route('/download_template')
def download_template():
    """Download CSV template file"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    # Create CSV template in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['name', 'manufacturer', 'price', 'stock_quantity', 'shelf_location', 'category', 'usage_type', 'min_stock_level'])
    
    # Write sample data
    writer.writerow(['Paracetamol 500mg', 'Sun Pharma', '15.00', '100', 'A1', 'Pain Relief', 'Fever, Headache', '15'])
    writer.writerow(['Cetirizine 10mg', 'Cipla', '25.00', '80', 'A2', 'Antihistamine', 'Allergy', '15'])
    writer.writerow(['Amoxicillin 250mg', 'Dr. Reddy', '120.00', '50', 'B1', 'Antibiotic', 'Infection', '15'])
    
    # Create bytes buffer
    output.seek(0)
    byte_output = io.BytesIO()
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    return send_file(
        byte_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='products_template.csv'
    )

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    """Upload and import CSV file"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    if 'csv_file' not in request.files:
        flash('No file selected!', 'danger')
        return redirect(url_for('import_csv_page'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected!', 'danger')
        return redirect(url_for('import_csv_page'))
    
    if not file.filename.endswith('.csv'):
        flash('Please upload a CSV file!', 'danger')
        return redirect(url_for('import_csv_page'))
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        db = get_db()
        if not db:
            flash('Database connection error!', 'danger')
            return redirect(url_for('import_csv_page'))
        
        cursor = db.cursor()
        success_count = 0
        error_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validate required fields
                if not row.get('name') or not row.get('price'):
                    errors.append(f"Row {row_num}: Missing required fields (name or price)")
                    error_count += 1
                    continue
                
                # Insert product
                cursor.execute("""
                    INSERT INTO products (name, manufacturer, price, stock_quantity, 
                                        shelf_location, category, usage_type, min_stock_level)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row.get('name', ''),
                    row.get('manufacturer', ''),
                    float(row.get('price', 0)),
                    int(row.get('stock_quantity', 0)),
                    row.get('shelf_location', ''),
                    row.get('category', ''),
                    row.get('usage_type', ''),
                    int(row.get('min_stock_level', 15))
                ))
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1
        
        db.commit()
        db.close()
        
        # Show results
        if success_count > 0:
            flash(f'Successfully imported {success_count} products!', 'success')
        
        if error_count > 0:
            flash(f'{error_count} rows failed to import.', 'warning')
            for error in errors[:5]:  # Show first 5 errors
                flash(error, 'danger')
        
        return redirect(url_for('inventory'))
        
    except Exception as e:
        flash(f'Error processing CSV file: {str(e)}', 'danger')
        return redirect(url_for('import_csv_page'))

@app.route('/update_stock/<int:product_id>', methods=['POST'])
def update_stock(product_id):
    """Update product stock"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Handle empty or invalid quantity input
    quantity_str = request.form.get('quantity', '0').strip()
    if not quantity_str or quantity_str == '':
        quantity = 0
    else:
        try:
            quantity = int(quantity_str)
        except ValueError:
            flash('Invalid quantity value!', 'danger')
            return redirect(url_for('inventory'))
    
    # Don't update if quantity is 0
    if quantity == 0:
        flash('Please enter a valid quantity!', 'warning')
        return redirect(url_for('inventory'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('inventory'))
    
    cursor = db.cursor()
    cursor.execute("""
        UPDATE products 
        SET stock_quantity = stock_quantity + %s 
        WHERE id = %s
    """, (quantity, product_id))
    
    db.commit()
    db.close()
    
    flash('Stock updated successfully!', 'success')
    return redirect(url_for('inventory'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    """Delete a product"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('inventory'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('inventory'))
    
    try:
        cursor = db.cursor()
        # Check if product exists
        cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            flash('Product not found!', 'danger')
            return redirect(url_for('inventory'))
        
        # Delete product
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        db.commit()
        db.close()
        
        flash(f'Product "{product[0]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'danger')
    
    return redirect(url_for('inventory'))

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """Edit product details"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('inventory'))
    
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        try:
            cursor.execute("""
                UPDATE products 
                SET name = %s, manufacturer = %s, price = %s, 
                    stock_quantity = %s, shelf_location = %s, 
                    category = %s, usage_type = %s, min_stock_level = %s
                WHERE id = %s
            """, (
                request.form.get('name'),
                request.form.get('manufacturer'),
                float(request.form.get('price')),
                int(request.form.get('stock_quantity', 0)),
                request.form.get('shelf_location'),
                request.form.get('category'),
                request.form.get('usage_type'),
                int(request.form.get('min_stock_level', 15)),
                product_id
            ))
            
            db.commit()
            db.close()
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'danger')
            return redirect(url_for('edit_product', product_id=product_id))
    
    # GET request - show edit form
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    db.close()
    
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('inventory'))
    
    return render_template('edit_product.html', product=product)

@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    """View product details"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('inventory'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        flash('Product not found!', 'danger')
        db.close()
        return redirect(url_for('inventory'))
    
    # Get sales statistics for this product
    cursor.execute("""
        SELECT COUNT(*) as times_sold, 
               COALESCE(SUM(quantity), 0) as total_quantity,
               COALESCE(SUM(total_amount), 0) as total_revenue
        FROM bill_items 
        WHERE product_id = %s
    """, (product_id,))
    stats = cursor.fetchone()
    
    # Get purchase records for this product
    cursor.execute("""
        SELECT sp.id, sp.purchase_number, sp.quantity, sp.unit_price, sp.total_amount,
               sp.status, sp.order_date, sp.expected_delivery_date, sp.received_date,
               s.name as supplier_name, s.company_name, s.phone
        FROM supplier_purchases sp
        JOIN suppliers s ON sp.supplier_id = s.id
        WHERE sp.product_id = %s
        ORDER BY sp.created_at DESC
    """, (product_id,))
    purchase_records = cursor.fetchall()
    
    db.close()
    
    return render_template('view_product.html', product=product, stats=stats, purchase_records=purchase_records)

# ============================================
# REPORTS ROUTES
# ============================================
@app.route('/reports')
def reports():
    """Sales reports"""
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Today's report
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bills, 
            COALESCE(SUM(total_amount), 0) as total_sales
            FROM bills
            WHERE DATE(bill_date) = CURDATE()
    """)
    today_report = cursor.fetchone()
    
    # This month's report
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bills, 
            COALESCE(SUM(total_amount), 0) as total_sales
            FROM bills
            WHERE MONTH(bill_date) = MONTH(CURDATE()) 
            AND YEAR(bill_date) = YEAR(CURDATE())
    """)
    month_report = cursor.fetchone()
    
    # Additional statistics
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total_products = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM customers")
    total_customers = cursor.fetchone()['total']
    
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total FROM bills")
    total_revenue = cursor.fetchone()['total']
    
    db.close()
    
    # Get settings for display
    store_settings = get_all_settings()
    currency = store_settings.get('currency_symbol', '₹')
    
    return render_template('reports.html', 
                         today_report=today_report,
                         month_report=month_report,
                         total_products=total_products,
                         total_customers=total_customers,
                         total_revenue=f"{currency}{total_revenue:,.2f}",
                         settings=store_settings)

@app.route('/download_sales_report')
def download_sales_report():
    """Generate and download professional PDF sales report with modern styling"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    period = request.args.get('period', 'today')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('reports'))
    
    cursor = db.cursor(dictionary=True)
    
    # Determine date range
    if period == 'today':
        date_condition = "DATE(bill_date) = CURDATE()"
        report_title = f"Daily Sales Report"
        report_period = datetime.now().strftime('%d %B %Y')
    elif period == 'month':
        date_condition = "MONTH(bill_date) = MONTH(CURDATE()) AND YEAR(bill_date) = YEAR(CURDATE())"
        report_title = f"Monthly Sales Report"
        report_period = datetime.now().strftime('%B %Y')
    elif period == 'year':
        date_condition = "YEAR(bill_date) = YEAR(CURDATE())"
        report_title = f"Yearly Sales Report"
        report_period = datetime.now().strftime('%Y')
    elif period == 'custom' and from_date and to_date:
        date_condition = f"DATE(bill_date) BETWEEN '{from_date}' AND '{to_date}'"
        report_title = f"Custom Sales Report"
        report_period = f"{from_date} to {to_date}"
    else:
        flash('Invalid period or missing dates!', 'danger')
        return redirect(url_for('reports'))
    
    # Get summary data
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_bills,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(AVG(total_amount), 0) as avg_bill,
            COALESCE(SUM(subtotal), 0) as total_subtotal,
            COALESCE(SUM(gst), 0) as total_gst
        FROM bills
        WHERE {date_condition}
    """)
    summary = cursor.fetchone()
    
    # Get top selling products
    cursor.execute(f"""
        SELECT bi.medicine_name, 
               SUM(bi.quantity) as total_quantity,
               SUM(bi.total_amount) as revenue
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE {date_condition}
        GROUP BY bi.medicine_name
        ORDER BY revenue DESC
        LIMIT 10
    """)
    top_products = cursor.fetchall()
    
    # Get top customers
    cursor.execute(f"""
        SELECT b.customer_name,
               COUNT(*) as bill_count,
               SUM(b.total_amount) as total_spent
        FROM bills b
        WHERE {date_condition} AND b.customer_name != 'Walk-in Customer'
        GROUP BY b.customer_name
        ORDER BY total_spent DESC
        LIMIT 10
    """)
    top_customers = cursor.fetchall()
    
    # Get purchase data for profit calculation
    cursor.execute(f"""
        SELECT COALESCE(SUM(total_amount), 0) as total_purchase
        FROM supplier_purchases sp
        WHERE status = 'received' AND DATE(received_date) >= (
            SELECT MIN(DATE(bill_date)) FROM bills WHERE {date_condition}
        ) AND DATE(received_date) <= (
            SELECT MAX(DATE(bill_date)) FROM bills WHERE {date_condition}
        )
    """)
    purchase_data = cursor.fetchone()
    
    # Get daily sales breakdown (for monthly/yearly reports)
    if period in ['month', 'year', 'custom']:
        cursor.execute(f"""
            SELECT DATE(bill_date) as sale_date,
                   COUNT(*) as bills,
                   SUM(total_amount) as revenue
            FROM bills
            WHERE {date_condition}
            GROUP BY DATE(bill_date)
            ORDER BY sale_date DESC
            LIMIT 31
        """)
        daily_breakdown = cursor.fetchall()
    else:
        daily_breakdown = []
    
    db.close()
    
    # Get store settings
    store_name = get_setting('store_name', 'MediStore Pro')
    store_address = get_setting('store_address', '')
    store_phone = get_setting('store_phone', '')
    store_email = get_setting('store_email', '')
    store_gstin = get_setting('store_gstin', '')
    currency_symbol = get_setting('currency_symbol', '₹')
    
    # Calculate profit
    gross_profit = float(summary['total_revenue']) - float(purchase_data['total_purchase'])
    profit_margin = (gross_profit / float(summary['total_revenue']) * 100) if float(summary['total_revenue']) > 0 else 0
    
    # Generate Professional PDF
    buffer = io.BytesIO()
    
    # Custom page template with header and footer
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []
    
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
    
        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_decorations(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)
    
        def draw_page_decorations(self, page_count):
            self.saveState()
            
            # Header area with brand color
            self.setFillColor(colors.HexColor('#4f46e5'))
            self.rect(0, A4[1] - 0.5*cm, A4[0], 0.5*cm, fill=1, stroke=0)
            
            # Footer
            self.setFont('Helvetica', 8)
            self.setFillColor(colors.HexColor('#6b7280'))
            
            # Page number
            page_num = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(A4[0] - 1*cm, 1*cm, page_num)
            
            # Footer text
            footer_text = f"Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}"
            self.drawString(1*cm, 1*cm, footer_text)
            
            # Center company name
            self.setFont('Helvetica-Bold', 8)
            self.drawCentredString(A4[0]/2, 1*cm, store_name)
            
            self.restoreState()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=1.5*cm, 
        leftMargin=1.5*cm,
        topMargin=1.5*cm, 
        bottomMargin=2*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=28,
        textColor=colors.HexColor('#1f2937'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontSize=20,
        textColor=colors.HexColor('#4f46e5'),
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    report_period_style = ParagraphStyle(
        'ReportPeriod',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        fontName='Helvetica-Bold',
        spaceBefore=15,
        spaceAfter=10,
        borderWidth=0,
        borderColor=colors.HexColor('#4f46e5'),
        borderPadding=5,
        leftIndent=0
    )
    
    info_text_style = ParagraphStyle(
        'InfoText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4b5563'),
        alignment=TA_CENTER,
        spaceAfter=3
    )
    
    # === HEADER SECTION ===
    elements.append(Paragraph(store_name, company_name_style))
    
    if store_address or store_phone or store_email:
        contact_info = []
        if store_address:
            contact_info.append(store_address)
        if store_phone:
            contact_info.append(f"Phone: {store_phone}")
        if store_email:
            contact_info.append(f"Email: {store_email}")
        if store_gstin:
            contact_info.append(f"GSTIN: {store_gstin}")
        
        for info in contact_info:
            elements.append(Paragraph(info, info_text_style))
    
    elements.append(Spacer(1, 0.3*cm))
    
    # Horizontal line
    elements.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor('#4f46e5'),
        spaceBefore=5,
        spaceAfter=10
    ))
    
    # Report Title
    elements.append(Paragraph(report_title, report_title_style))
    elements.append(Paragraph(report_period, report_period_style))
    
    # === KEY METRICS SECTION ===
    elements.append(Paragraph("📊 Executive Summary", section_heading_style))
    elements.append(Spacer(1, 0.2*cm))
    
    # Create metrics cards with modern styling
    metrics_data = [
        ['Total Revenue', 'Total Bills', 'Average Bill', 'Gross Profit'],
        [
            f"{currency_symbol}{summary['total_revenue']:,.2f}",
            str(summary['total_bills']),
            f"{currency_symbol}{summary['avg_bill']:,.2f}",
            f"{currency_symbol}{gross_profit:,.2f}"
        ],
        ['GST Collected', 'Net Sales', 'Profit Margin', 'Items Sold'],
        [
            f"{currency_symbol}{summary['total_gst']:,.2f}",
            f"{currency_symbol}{summary['total_subtotal']:,.2f}",
            f"{profit_margin:.1f}%",
            str(sum([p['total_quantity'] for p in top_products]) if top_products else 0)
        ]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    metrics_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Value row 1
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#1f2937')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        
        # Header row 2
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 2), (-1, 2), 9),
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
        ('VALIGN', (0, 2), (-1, 2), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 8),
        ('TOPPADDING', (0, 2), (-1, 2), 8),
        
        # Value row 2
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#d1fae5')),
        ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#1f2937')),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 3), (-1, 3), 14),
        ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
        ('TOPPADDING', (0, 3), (-1, 3), 10),
        ('BOTTOMPADDING', (0, 3), (-1, 3), 10),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#d1d5db')),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.5*cm))
    
    # === TOP SELLING PRODUCTS ===
    if top_products:
        elements.append(Paragraph("🏆 Top 10 Best-Selling Products", section_heading_style))
        elements.append(Spacer(1, 0.2*cm))
        
        products_data = [['Rank', 'Product Name', 'Qty', 'Revenue', 'Share %']]
        total_revenue_products = sum([p['revenue'] for p in top_products])
        
        for idx, product in enumerate(top_products, 1):
            share = (product['revenue'] / total_revenue_products * 100) if total_revenue_products > 0 else 0
            products_data.append([
                str(idx),
                product['medicine_name'],
                str(product['total_quantity']),
                f"{currency_symbol}{product['revenue']:,.2f}",
                f"{share:.1f}%"
            ])
        
        products_table = Table(products_data, colWidths=[1.5*cm, 7*cm, 2*cm, 3*cm, 2*cm])
        products_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows - alternating colors
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Rank center
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Product name left
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Numbers right
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#9ca3af')),
        ]))
        
        # Add alternating row colors
        for i in range(1, len(products_data)):
            if i % 2 == 1:
                products_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#fef3c7'))
                ]))
            else:
                products_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.white)
                ]))
        
        elements.append(products_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # === TOP CUSTOMERS ===
    if top_customers:
        elements.append(Paragraph("👥 Top 10 Valued Customers", section_heading_style))
        elements.append(Spacer(1, 0.2*cm))
        
        customers_data = [['Rank', 'Customer Name', 'Bills', 'Total Spent', 'Avg/Bill']]
        for idx, customer in enumerate(top_customers, 1):
            avg_per_bill = customer['total_spent'] / customer['bill_count'] if customer['bill_count'] > 0 else 0
            customers_data.append([
                str(idx),
                customer['customer_name'][:30],
                str(customer['bill_count']),
                f"{currency_symbol}{customer['total_spent']:,.2f}",
                f"{currency_symbol}{avg_per_bill:,.2f}"
            ])
        
        customers_table = Table(customers_data, colWidths=[1.5*cm, 7*cm, 2*cm, 3*cm, 2*cm])
        customers_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#9ca3af')),
        ]))
        
        # Alternating row colors
        for i in range(1, len(customers_data)):
            if i % 2 == 1:
                customers_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ede9fe'))
                ]))
            else:
                customers_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.white)
                ]))
        
        elements.append(customers_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # === DAILY BREAKDOWN ===
    if daily_breakdown and period != 'today':
        elements.append(PageBreak())
        elements.append(Paragraph("📅 Daily Sales Breakdown", section_heading_style))
        elements.append(Spacer(1, 0.2*cm))
        
        daily_data = [['Date', 'Day', 'Bills', 'Revenue', 'Avg/Bill']]
        for day in daily_breakdown:
            day_name = day['sale_date'].strftime('%A')[:3]
            avg_bill = day['revenue'] / day['bills'] if day['bills'] > 0 else 0
            daily_data.append([
                day['sale_date'].strftime('%d %b %Y'),
                day_name,
                str(day['bills']),
                f"{currency_symbol}{day['revenue']:,.2f}",
                f"{currency_symbol}{avg_bill:,.2f}"
            ])
        
        daily_table = Table(daily_data, colWidths=[3.5*cm, 2*cm, 2.5*cm, 4*cm, 3.5*cm])
        daily_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            
            # Data
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#9ca3af')),
        ]))
        
        # Alternating row colors
        for i in range(1, len(daily_data)):
            if i % 2 == 1:
                daily_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#cffafe'))
                ]))
            else:
                daily_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), colors.white)
                ]))
        
        elements.append(daily_table)
    
    # === FOOTER NOTE ===
    elements.append(Spacer(1, 0.7*cm))
    
    footer_note_style = ParagraphStyle(
        'FooterNote',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        borderWidth=1,
        borderColor=colors.HexColor('#e5e7eb'),
        borderPadding=8,
        backColor=colors.HexColor('#f9fafb')
    )
    
    elements.append(Paragraph(
        "This is a computer-generated report. "
        "For any discrepancies or queries, please contact the store management.",
        footer_note_style
    ))
    
    # Build PDF with custom canvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    
    # Generate filename
    filename = f"sales_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
    
    # Generate filename
    filename = f"sales_report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# ============================================
# CUSTOMER MANAGEMENT ROUTES
# ============================================
@app.route('/customers')
def customers():
    """Customer management page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, COUNT(DISTINCT b.id) as total_bills,
               COALESCE(SUM(b.total_amount), 0) as total_spent
        FROM customers c
        LEFT JOIN bills b ON c.id = b.customer_id
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)
    customers_list = cursor.fetchall()
    db.close()
    
    return render_template('customers.html', customers=customers_list)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    """Add new customer"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('customers'))
    
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address)
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, address))
        db.commit()
        flash(f'Customer {name} added successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Phone number already exists!', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('customers'))

@app.route('/customer_lookup', methods=['GET', 'POST'])
def customer_lookup():
    """Look up customer by phone number"""
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        
        if not phone:
            flash('Please enter a phone number', 'warning')
            return redirect(url_for('index'))
        
        db = get_db()
        if not db:
            flash('Database connection error', 'danger')
            return redirect(url_for('index'))
        
        cursor = db.cursor(dictionary=True)
        
        # Get customer details
        cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('Customer not found! Please contact staff to register.', 'warning')
            db.close()
            return redirect(url_for('index'))
        
        # Get regular purchases
        cursor.execute("""
            SELECT rp.*, p.price, p.stock_quantity, p.id as product_id
            FROM regular_purchases rp
            LEFT JOIN products p ON rp.product_id = p.id
            WHERE rp.customer_id = %s
            ORDER BY rp.added_at DESC
        """, (customer['id'],))
        regular_purchases = cursor.fetchall()
        
        # Get purchase history
        cursor.execute("""
            SELECT b.*, COUNT(bi.id) as item_count
            FROM bills b
            LEFT JOIN bill_items bi ON b.id = bi.bill_id
            WHERE b.customer_id = %s
            GROUP BY b.id
            ORDER BY b.bill_date DESC
            LIMIT 10
        """, (customer['id'],))
        recent_bills = cursor.fetchall()
        
        # Get statistics
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM bills WHERE customer_id = %s) as total_bills,
                (SELECT COALESCE(SUM(total_amount), 0) FROM bills WHERE customer_id = %s) as total_spent,
                (SELECT COUNT(DISTINCT medicine_name) FROM bill_items bi 
                 JOIN bills b ON bi.bill_id = b.id WHERE b.customer_id = %s) as unique_medicines
        """, (customer['id'], customer['id'], customer['id']))
        stats = cursor.fetchone()
        
        db.close()
        
        return render_template('customer_history.html',
                             customer=customer,
                             regular_purchases=regular_purchases,
                             recent_bills=recent_bills,
                             stats=stats)
    
    return render_template('customer_lookup.html')

@app.route('/manage_regular_purchases/<int:customer_id>')
def manage_regular_purchases(customer_id):
    """Manage customer's regular purchases"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Get customer details
    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!', 'danger')
        db.close()
        return redirect(url_for('customers'))
    
    # Get regular purchases
    cursor.execute("""
        SELECT rp.*, p.price, p.stock_quantity
        FROM regular_purchases rp
        LEFT JOIN products p ON rp.product_id = p.id
        WHERE rp.customer_id = %s
    """, (customer_id,))
    regular_purchases = cursor.fetchall()
    
    db.close()
    
    return render_template('manage_regular_purchases.html',
                         customer=customer,
                         regular_purchases=regular_purchases)

@app.route('/add_regular_purchase/<int:customer_id>', methods=['POST'])
def add_regular_purchase(customer_id):
    """Add medicine to customer's regular purchases"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    medicine_name = request.form.get('medicine_name')
    default_quantity = int(request.form.get('default_quantity', 1))
    
    # Find product by name
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('manage_regular_purchases', customer_id=customer_id))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM products WHERE name LIKE %s LIMIT 1", (f'%{medicine_name}%',))
    product = cursor.fetchone()
    
    product_id = product['id'] if product else None
    
    try:
        cursor.execute("""
            INSERT INTO regular_purchases (customer_id, product_id, medicine_name, default_quantity)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE default_quantity = %s
        """, (customer_id, product_id, medicine_name, default_quantity, default_quantity))
        db.commit()
        flash('Regular purchase added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding regular purchase: {str(e)}', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('manage_regular_purchases', customer_id=customer_id))
 
@app.route('/remove_regular_purchase/<int:purchase_id>')
def remove_regular_purchase(purchase_id):
    """Remove medicine from regular purchases"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('customers'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT customer_id FROM regular_purchases WHERE id = %s", (purchase_id,))
    result = cursor.fetchone()
    
    if result:
        customer_id = result['customer_id']
        cursor.execute("DELETE FROM regular_purchases WHERE id = %s", (purchase_id,))
        db.commit()
        flash('Regular purchase removed successfully!', 'success')
        db.close()
        return redirect(url_for('manage_regular_purchases', customer_id=customer_id))
    
    db.close()
    flash('Regular purchase not found!', 'danger')
    return redirect(url_for('customers'))

@app.route('/quick_billing/<int:customer_id>')
def quick_billing(customer_id):
    """Quick billing with customer's regular purchases"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('billing'))
    
    cursor = db.cursor(dictionary=True)
    
    # Get customer
    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!', 'danger')
        db.close()
        return redirect(url_for('billing'))
    
    # Get regular purchases and add to cart
    cursor.execute("""
        SELECT rp.*, p.*
        FROM regular_purchases rp
        INNER JOIN products p ON rp.product_id = p.id
        WHERE rp.customer_id = %s AND p.stock_quantity > 0
    """, (customer_id,))
    regular_items = cursor.fetchall()
    
    db.close()
    
    # Clear cart and add regular purchases
    cart = []
    for item in regular_items:
        cart_item = {
            'id': item['id'],
            'name': item['name'],
            'price': float(item['price']),
            'quantity': item['default_quantity'],
            'stock_quantity': item['stock_quantity']
        }
        cart.append(cart_item)
    
    session['cart'] = cart
    session['customer_info'] = {
        'id': customer['id'],
        'name': customer['name'],
        'phone': customer['phone']
    }
    
    flash(f'Added {len(cart)} regular items to cart for {customer["name"]}', 'success')
    return redirect(url_for('billing'))

@app.route('/search_medicine_names')
def search_medicine_names():
    """Get all medicine names for autocomplete"""
    db = get_db()
    if not db:
        return jsonify([])
    
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT name FROM products WHERE stock_quantity > 0 ORDER BY name")
    names = [row[0] for row in cursor.fetchall()]
    db.close()
    
    return jsonify(names)

@app.route('/clear_search_cache')
def clear_search_cache():
    session['search_results'] = None
    return jsonify({'status': 'success'})


@app.route('/api/search_customers')
def api_search_customers():
    """API endpoint to search customers by partial phone number"""
    phone = request.args.get('phone', '')
    
    if len(phone) < 4:
        return jsonify({'customers': []})
    
    db = get_db()
    if not db:
        return jsonify({'customers': []})
    
    cursor = db.cursor(dictionary=True)
    # Search for phone numbers that contain the digits
    cursor.execute(
        "SELECT id, name, phone, email, address FROM customers WHERE phone LIKE %s ORDER BY phone LIMIT 10",
        (f'%{phone}%',)
    )
    customers = cursor.fetchall()
    db.close()
    
    return jsonify({'customers': customers})

@app.route('/api/customer/<phone>')
def api_get_customer(phone):
    """API endpoint to fetch customer by phone"""
    db = get_db()
    if not db:
        return jsonify({'found': False})
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
    customer = cursor.fetchone()
    db.close()
    
    if customer:
        return jsonify({
            'found': True,
            'customer': {
                'id': customer['id'],
                'name': customer['name'],
                'phone': customer['phone'],
                'email': customer['email'] or '',
                'address': customer['address'] or ''
            }
        })
    else:
        return jsonify({'found': False})

@app.route('/bills')
def bills():
    """All bills page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Build query
    query = """
        SELECT b.*, 
               COUNT(bi.id) as item_count,
               c.name as customer_full_name
        FROM bills b
        LEFT JOIN bill_items bi ON b.id = bi.bill_id
        LEFT JOIN customers c ON b.customer_id = c.id
    """
    
    conditions = []
    params = []
    
    if search:
        conditions.append("(b.bill_number LIKE %s OR b.customer_name LIKE %s OR b.phone LIKE %s)")
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if date_from:
        conditions.append("DATE(b.bill_date) >= %s")
        params.append(date_from)
    
    if date_to:
        conditions.append("DATE(b.bill_date) <= %s")
        params.append(date_to)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " GROUP BY b.id ORDER BY b.bill_date DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(DISTINCT b.id) as total FROM bills b"
    if conditions:
        count_query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(count_query, params)
    total_bills = cursor.fetchone()['total']
    
    # Add pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
    
    cursor.execute(query, params)
    bills_list = cursor.fetchall()
    
    # Get summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bills,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(AVG(total_amount), 0) as avg_bill_amount
        FROM bills
    """)
    stats = cursor.fetchone()
    
    db.close()
    
    total_pages = (total_bills + per_page - 1) // per_page
    
    return render_template('bills.html',
                         bills=bills_list,
                         stats=stats,
                         page=page,
                         total_pages=total_pages,
                         search=search,
                         date_from=date_from,
                         date_to=date_to)

# ============================================
# SUPPLIER MANAGEMENT ROUTES
# ============================================
@app.route('/suppliers')
def suppliers():
    """Supplier management page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM suppliers
        ORDER BY name
    """)
    suppliers_list = cursor.fetchall()
    db.close()
    
    return render_template('suppliers.html', suppliers=suppliers_list)

@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    if 'user_id' not in session or session.get('role') != 'owner':
        return redirect(url_for('login'))
    
    # Matching field names from corrected HTML
    name = request.form.get('name')
    company = request.form.get('company_name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    gstin = request.form.get('gstin', '')
    
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO suppliers (name, company_name, phone, email, address, gstin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, company, phone, email, address, gstin))
        db.commit()
        flash('Supplier registered successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('suppliers'))

@app.route('/add_supplier_purchase', methods=['POST'])
def add_supplier_purchase():
    # Capture IDs and values
    supplier_id = request.form.get('supplier_id')
    med_name = request.form.get('medicine_name')
    qty = request.form.get('quantity')
    price = request.form.get('unit_price')
    delivery = request.form.get('expected_delivery_date')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Fetch parent and product data
        cursor.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        s = cursor.fetchone()
        cursor.execute("SELECT id, manufacturer FROM products WHERE name = %s", (med_name,))
        p = cursor.fetchone()
        
        # INSERT into NEW schema (mapping qty to ordered_count and pending_orders)
        cursor.execute("""
            INSERT INTO supplier_purchases (
                supplier_id, supplier_name, contact_number, email, gstin, office_address,
                product_id, medicine_name, manufacturer, medicine_price, order_date, 
                expected_delivery_date, total_orders, pending_orders, ordered_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), %s, %s, %s, %s)
        """, (
            s['id'], s['name'], s['phone'], s['email'], s['gstin'], s['address'],
            p['id'], med_name, p['manufacturer'], float(price),
            delivery, int(qty), int(qty), int(qty)
        ))
        db.commit()
        flash('New Order Placed!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('supplier_purchases', supplier_id=supplier_id))

@app.route('/edit_supplier/<int:supplier_id>', methods=['POST'])
def edit_supplier(supplier_id):
    """Edit existing supplier and sync details with purchase history"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('suppliers'))
    
    # Capture data from the Edit Modal
    name = request.form.get('name')
    company = request.form.get('company_name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    gstin = request.form.get('gstin', '')
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('suppliers'))
    
    try:
        cursor = db.cursor()
        
        # 1. Update the parent Suppliers table
        cursor.execute("""
            UPDATE suppliers 
            SET name = %s, company_name = %s, phone = %s, email = %s, address = %s, gstin = %s
            WHERE id = %s
        """, (name, company, phone, email, address, gstin, supplier_id))
        
        # 2. SYNC: Update contact details in the purchases history table
        # This ensures the Intelligence page stays accurate
        cursor.execute("""
            UPDATE supplier_purchases 
            SET supplier_name = %s, contact_number = %s, email = %s, gstin = %s, office_address = %s
            WHERE supplier_id = %s
        """, (name, phone, email, gstin, address, supplier_id))
        
        db.commit()
        flash(f'Supplier "{company}" updated and history synced!', 'success')
        
    except mysql.connector.IntegrityError:
        db.rollback()
        flash('Update failed: This phone number is already assigned to another supplier.', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'System Error: {str(e)}', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('suppliers'))

# ============================================
# UPDATED SUPPLIER INTELLIGENCE ROUTE
# ============================================

@app.route('/supplier_purchases/<int:supplier_id>')
def supplier_purchases(supplier_id):
    """View supplier's comprehensive history and intelligence"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 1. Fetch Primary Supplier Info (From the parent table)
        cursor.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cursor.fetchone()
        
        # 2. Fetch All Detailed History (Using your NEW table structure)
        # We fetch the specific historical rows for this supplier
        cursor.execute("""
            SELECT * FROM supplier_purchases 
            WHERE supplier_id = %s 
            ORDER BY order_date DESC
        """, (supplier_id,))
        history = cursor.fetchall()
        
        # 3. Calculate Intelligence Stats for Top Tiles
        # We aggregate data from the new columns to show "High-Level" numbers
        cursor.execute("""
            SELECT 
                COALESCE(SUM(total_orders), 0) as lifetime_orders,
                COALESCE(SUM(received_count), 0) as lifetime_received,
                COALESCE(SUM(pending_orders), 0) as current_pending,
                COALESCE(SUM(total_purchase_value), 0) as lifetime_spend
            FROM supplier_purchases 
            WHERE supplier_id = %s
        """, (supplier_id,))
        intel_stats = cursor.fetchone()

        # 4. Fetch list of products for the "New Order" dropdown
        cursor.execute("SELECT id, name FROM products ORDER BY name")
        products = cursor.fetchall()

        return render_template('supplier_purchases.html',
                             supplier=supplier, 
                             history=history, 
                             stats=intel_stats,
                             products=products)
    finally:
        db.close()
@app.route('/update_purchase_status/<int:purchase_id>/<new_status>')    
def update_purchase_status(purchase_id, new_status):
    """Update purchase order counters and status"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('suppliers'))
    
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT supplier_id FROM supplier_purchases WHERE id = %s", (purchase_id,))
        result = cursor.fetchone()
        
        if not result:
            flash('Purchase record not found!', 'danger')
            return redirect(url_for('suppliers'))
        
        supplier_id = result['supplier_id']
        
        # When moving to 'ordered', we increment the counts
        if new_status == 'ordered':
            cursor.execute("""
                UPDATE supplier_purchases 
                SET order_date = CURDATE(),
                    ordered_count = 1,
                    pending_orders = 1
                WHERE id = %s
            """, (purchase_id,))
        
        db.commit()
        flash('Purchase record updated!', 'success')
    except Exception as e:
        flash(f'Error updating status: {str(e)}', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('supplier_purchases', supplier_id=supplier_id))
@app.route('/receive_purchase/<int:purchase_id>')
def receive_purchase(purchase_id):
    """Confirm receipt, update stock, and finalize purchase value"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('suppliers'))
    
    try:
        cursor = db.cursor(dictionary=True)
        
        # 1. Fetch record to get Price, Quantity, and Product ID
        cursor.execute("SELECT * FROM supplier_purchases WHERE id = %s", (purchase_id,))
        purchase = cursor.fetchone()
        
        if not purchase:
            flash('Purchase record not found!', 'danger')
            return redirect(url_for('suppliers'))
        
        supplier_id = purchase['supplier_id']
        
        # 2. Calculate the value of this specific delivery
        # We assume total_orders for this row is 1 for the logic
        total_val = float(purchase['medicine_price'] or 0) * float(purchase['total_orders'] or 1)

        # 3. Update the Supplier Purchase Record
        cursor.execute("""
            UPDATE supplier_purchases 
            SET pending_orders = 0,
                received_count = 1,
                total_purchase_value = %s,
                expected_delivery_date = CURDATE()
            WHERE id = %s
        """, (total_val, purchase_id))
        
        # 4. Update the actual Inventory Stock
        if purchase['product_id']:
            # We use total_orders as the quantity ordered in this context
            quantity_to_add = int(purchase['total_orders'] or 0)
            cursor.execute("""
                UPDATE products 
                SET stock_quantity = stock_quantity + %s 
                WHERE id = %s
            """, (quantity_to_add, purchase['product_id']))
        
        db.commit()
        flash(f'Stock updated! Received {purchase["medicine_name"]} worth ₹{total_val:,.2f}', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error finalizing purchase: {str(e)}', 'danger')
    finally:
        db.close()
    
    return redirect(url_for('supplier_purchases', supplier_id=supplier_id))

# ============================================
# SETTINGS ROUTES
# ============================================
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Store settings management"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Only owners can access settings!', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash('Database connection error', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            cursor = db.cursor()
            
            # Get all settings to update
            cursor.execute("SELECT setting_key, is_editable FROM settings")
            all_settings = cursor.fetchall()
            
            # Update each editable setting
            for setting_key, is_editable in all_settings:
                if is_editable and setting_key in request.form:
                    new_value = request.form.get(setting_key)
                    cursor.execute("""
                        UPDATE settings 
                        SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE setting_key = %s
                    """, (new_value, setting_key))
            
            db.commit()
            flash('Settings updated successfully!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
        finally:
            db.close()
        
        return redirect(url_for('settings'))
    
    # GET request - display settings
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings ORDER BY setting_key")
    settings_list = cursor.fetchall()
    db.close()
    
    return render_template('settings.html', settings=settings_list)

# ============================================
# STAFF MANAGEMENT ROUTES (OWNER ONLY)
# ============================================
@app.route('/staff')
def staff():
    """View all staff accounts - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied! Owner privileges required.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, username, full_name, role, email, phone, 
               created_at, is_active 
        FROM users 
        ORDER BY created_at DESC
    """)
    staff_list = cursor.fetchall()
    db.close()
    
    return render_template('staff.html', staff_list=staff_list)

@app.route('/staff/add', methods=['POST'])
def add_staff():
    """Create new staff account - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    if not username or not password or not full_name or not role:
        flash('Username, password, full name, and role are required!', 'danger')
        return redirect(url_for('staff'))
    
    hashed_password = hash_password(password)
    
    db = get_db()
    if not db:
        flash('Database connection error!', 'danger')
        return redirect(url_for('staff'))
    
    try:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (username, password, full_name, role, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, hashed_password, full_name, role, email, phone))
        db.commit()
        db.close()
        flash(f'Staff account "{username}" created successfully!', 'success')
    except mysql.connector.IntegrityError:
        db.close()
        flash('Username already exists! Please choose a different username.', 'danger')
    except Exception as e:
        db.close()
        flash(f'Error creating staff account: {str(e)}', 'danger')
    
    return redirect(url_for('staff'))

@app.route('/staff/edit/<int:staff_id>', methods=['POST'])
def edit_staff(staff_id):
    """Edit staff account details - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    full_name = request.form.get('full_name')
    role = request.form.get('role')
    email = request.form.get('email')
    phone = request.form.get('phone')
    is_active = request.form.get('is_active') == '1'
    
    if not full_name or not role:
        flash('Full name and role are required!', 'danger')
        return redirect(url_for('staff'))
    
    db = get_db()
    if not db:
        flash('Database connection error!', 'danger')
        return redirect(url_for('staff'))
    
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE users 
            SET full_name = %s, role = %s, email = %s, phone = %s, is_active = %s
            WHERE id = %s
        """, (full_name, role, email, phone, is_active, staff_id))
        db.commit()
        db.close()
        flash('Staff account updated successfully!', 'success')
    except Exception as e:
        db.close()
        flash(f'Error updating staff account: {str(e)}', 'danger')
    
    return redirect(url_for('staff'))

@app.route('/staff/change-password/<int:staff_id>', methods=['POST'])
def change_staff_password(staff_id):
    """Change staff password - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 4:
        flash('Password must be at least 4 characters long!', 'danger')
        return redirect(url_for('staff'))
    
    hashed_password = hash_password(new_password)
    
    db = get_db()
    if not db:
        flash('Database connection error!', 'danger')
        return redirect(url_for('staff'))
    
    try:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE users 
            SET password = %s
            WHERE id = %s
        """, (hashed_password, staff_id))
        db.commit()
        db.close()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        db.close()
        flash(f'Error changing password: {str(e)}', 'danger')
    
    return redirect(url_for('staff'))

@app.route('/staff/delete/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    """Delete staff account - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))
    
    # Prevent owner from deleting their own account
    if staff_id == session.get('user_id'):
        flash('You cannot delete your own account!', 'warning')
        return redirect(url_for('staff'))
    
    db = get_db()
    if not db:
        flash('Database connection error!', 'danger')
        return redirect(url_for('staff'))
    
    try:
        cursor = db.cursor(dictionary=True)
        # Get username before deleting
        cursor.execute("SELECT username FROM users WHERE id = %s", (staff_id,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("DELETE FROM users WHERE id = %s", (staff_id,))
            db.commit()
            flash(f'Staff account "{user["username"]}" deleted successfully!', 'success')
        else:
            flash('Staff account not found!', 'danger')
        
        db.close()
    except Exception as e:
        db.close()
        flash(f'Error deleting staff account: {str(e)}', 'danger')
    
    return redirect(url_for('staff'))

# ============================================
# STAFF ANALYSIS ROUTES
# ============================================
@app.route('/staff-analysis')
def staff_analysis():
    """View staff performance analysis - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied! Owner privileges required.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Get staff analytics with bill counts and total sales
    cursor.execute("""
        SELECT 
            u.id,
            u.full_name,
            u.username,
            u.role,
            u.is_active,
            COUNT(DISTINCT b.id) as total_bills,
            COALESCE(SUM(b.total_amount), 0) as total_sales,
            MAX(b.bill_date) as last_bill_date,
            MIN(b.bill_date) as first_bill_date
        FROM users u
        LEFT JOIN bills b ON u.id = b.created_by
        GROUP BY u.id, u.full_name, u.username, u.role, u.is_active
        ORDER BY total_sales DESC
    """)
    staff_analytics = cursor.fetchall()
    
    db.close()
    
    return render_template('staff_analysis.html', staff_analytics=staff_analytics)

@app.route('/staff-analysis/<int:staff_id>')
def staff_bills_detail(staff_id):
    """View detailed bills for a specific staff member - Owner only"""
    if 'user_id' not in session or session.get('role') != 'owner':
        flash('Access denied! Owner privileges required.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Get staff details
    cursor.execute("SELECT id, full_name, username, role FROM users WHERE id = %s", (staff_id,))
    staff = cursor.fetchone()
    
    if not staff:
        flash('Staff member not found!', 'danger')
        db.close()
        return redirect(url_for('staff_analysis'))
    
    # Get all bills created by this staff member
    cursor.execute("""
        SELECT 
            b.id,
            b.bill_number,
            b.customer_name,
            b.phone,
            b.subtotal,
            b.gst,
            b.total_amount,
            b.bill_date,
            COUNT(bi.id) as item_count
        FROM bills b
        LEFT JOIN bill_items bi ON b.id = bi.bill_id
        WHERE b.created_by = %s
        GROUP BY b.id
        ORDER BY b.bill_date DESC
    """, (staff_id,))
    bills = cursor.fetchall()
    
    # Get summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bills,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_sale,
            MAX(bill_date) as last_sale,
            MIN(bill_date) as first_sale
        FROM bills
        WHERE created_by = %s
    """, (staff_id,))
    summary = cursor.fetchone()
    
    db.close()
    
    return render_template('staff_bills_detail.html', 
                          staff=staff, 
                          bills=bills, 
                          summary=summary)

# ============================================
# CUSTOMER BILLING HISTORY ROUTES
# ============================================
@app.route('/customer-billing-history/<int:customer_id>')
def customer_billing_history(customer_id):
    """View detailed billing history for a specific customer"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return "Database connection error", 500
    
    cursor = db.cursor(dictionary=True)
    
    # Get customer details
    cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
    customer = cursor.fetchone()
    
    if not customer:
        flash('Customer not found!', 'danger')
        db.close()
        return redirect(url_for('customers'))
    
    # Get all bills for this customer
    cursor.execute("""
        SELECT 
            b.id,
            b.bill_number,
            b.subtotal,
            b.gst,
            b.total_amount,
            b.bill_date,
            b.created_by,
            u.full_name as staff_name,
            COUNT(bi.id) as item_count
        FROM bills b
        LEFT JOIN bill_items bi ON b.id = bi.bill_id
        LEFT JOIN users u ON b.created_by = u.id
        WHERE b.customer_id = %s
        GROUP BY b.id
        ORDER BY b.bill_date DESC
    """, (customer_id,))
    bills = cursor.fetchall()
    
    # Get summary statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_bills,
            COALESCE(SUM(total_amount), 0) as total_spent,
            COALESCE(AVG(total_amount), 0) as avg_bill,
            MAX(bill_date) as last_purchase,
            MIN(bill_date) as first_purchase
        FROM bills
        WHERE customer_id = %s
    """, (customer_id,))
    summary = cursor.fetchone()
    
    # Get top purchased medicines
    cursor.execute("""
        SELECT 
            bi.medicine_name,
            SUM(bi.quantity) as total_quantity,
            COUNT(DISTINCT bi.bill_id) as purchase_count,
            SUM(bi.total_amount) as total_spent
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE b.customer_id = %s
        GROUP BY bi.medicine_name
        ORDER BY total_quantity DESC
        LIMIT 10
    """, (customer_id,))
    top_medicines = cursor.fetchall()
    
    db.close()
    
    return render_template('customer_billing_history.html', 
                          customer=customer, 
                          bills=bills, 
                          summary=summary,
                          top_medicines=top_medicines)

# ============================================
# RUN APPLICATION
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
