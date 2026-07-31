import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DB_PATH = BASE_DIR / 'orders.db'

app = Flask(__name__)
app.secret_key = 'pizza-secret'
MAX_PIZZAS_PER_ORDER = 20


def load_data():
    with open(DATA_DIR / 'pizzas.json') as file:
        pizzas = json.load(file)
    with open(DATA_DIR / 'toppings.json') as file:
        toppings = json.load(file)
    return pizzas, toppings


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute(
            '''
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                items TEXT NOT NULL,
                total REAL NOT NULL,
                delivery_method TEXT,
                address TEXT,
                phone_number TEXT,
                delivery_charge REAL,
                created_at TEXT
            )
            '''
        )
    else:
        cursor.execute('PRAGMA table_info(orders)')
        columns = {row[1] for row in cursor.fetchall()}
        if 'delivery_method' not in columns:
            cursor.execute('ALTER TABLE orders ADD COLUMN delivery_method TEXT')
        if 'address' not in columns:
            cursor.execute('ALTER TABLE orders ADD COLUMN address TEXT')
        if 'phone_number' not in columns:
            cursor.execute('ALTER TABLE orders ADD COLUMN phone_number TEXT')
        if 'delivery_charge' not in columns:
            cursor.execute('ALTER TABLE orders ADD COLUMN delivery_charge REAL')

    conn.commit()
    conn.close()


def calculate_cart_total(cart):
    return round(sum(
        details['price'] * details['quantity'] + details.get('topping_cost', 0)
        for details in cart.values()
    ), 2)


@app.route('/')
def home():
    pizzas, toppings = load_data()
    cart = session.get('cart', {})
    cart_total = calculate_cart_total(cart)
    return render_template('index1.html', pizzas=pizzas, toppings=toppings, cart=cart, cart_total=cart_total)


@app.route('/orders')
def orders():
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT id, customer_name, items, total, delivery_method, address, phone_number, delivery_charge, created_at FROM orders ORDER BY created_at DESC'
    ).fetchall()
    conn.close()

    parsed_orders = []
    for row in rows:
        try:
            items = json.loads(row['items'])
        except (TypeError, json.JSONDecodeError):
            items = {}

        parsed_orders.append({
            'id': row['id'],
            'customer_name': row['customer_name'],
            'items': items,
            'total': row['total'],
            'delivery_method': row['delivery_method'],
            'address': row['address'],
            'phone_number': row['phone_number'],
            'delivery_charge': row['delivery_charge'],
            'created_at': row['created_at']
        })

    return render_template('orders.html', orders=parsed_orders)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    pizza = request.form['pizza']
    quantity = int(request.form['quantity'])
    selected_toppings = request.form.getlist('toppings')
    pizzas, toppings = load_data()
    cart = session.get('cart', {})

    if pizza not in pizzas:
        flash('Invalid pizza selected.')
        return redirect(url_for('home'))

    if any(topping not in toppings for topping in selected_toppings):
        flash('Invalid topping selected.')
        return redirect(url_for('home'))

    current_quantity = cart.get(pizza, {}).get('quantity', 0)
    if current_quantity + quantity > MAX_PIZZAS_PER_ORDER:
        flash(f'You can only purchase up to {MAX_PIZZAS_PER_ORDER} pizzas of {pizza} per order.')
        return redirect(url_for('home'))

    topping_cost = round(sum(toppings[topping]['price'] for topping in selected_toppings), 2)
    if pizza in cart:
        cart[pizza]['quantity'] += quantity
        existing_toppings = set(cart[pizza].get('toppings', []))
        all_toppings = sorted(existing_toppings.union(selected_toppings))
        cart[pizza]['toppings'] = all_toppings
        cart[pizza]['topping_cost'] = round(sum(toppings[topping]['price'] for topping in all_toppings), 2)
    else:
        cart[pizza] = {
            'price': pizzas[pizza]['price'],
            'quantity': quantity,
            'toppings': selected_toppings,
            'topping_cost': topping_cost
        }

    session['cart'] = cart
    session.modified = True
    toppings_text = f" with {', '.join(selected_toppings)}" if selected_toppings else ""
    flash(f'{quantity} {pizza} pizza(s){toppings_text} added to cart.')
    return redirect(url_for('home'))


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    pizza = request.form['pizza']
    cart = session.get('cart', {})

    if pizza in cart:
        del cart[pizza]
        session['cart'] = cart
        session.modified = True
        flash(f'{pizza} removed from cart.')
    else:
        flash('Item not found in cart.')

    return redirect(url_for('home'))


@app.route('/checkout', methods=['POST'])
def checkout():
    name = request.form.get('name', '').strip()
    delivery_method = request.form.get('delivery_method', 'pickup').strip().lower()
    address = request.form.get('address', '').strip()
    phone_number = request.form.get('phone_number', '').strip()
    cart = session.get('cart', {})

    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('home'))

    if not name:
        flash('Please enter your name to checkout.')
        return redirect(url_for('home'))

    if delivery_method == 'delivery':
        if not address or not phone_number:
            flash('Please provide your address and phone number for delivery.')
            return redirect(url_for('home'))
    elif delivery_method != 'pickup':
        flash('Please choose pickup or delivery.')
        return redirect(url_for('home'))

    cart_total = calculate_cart_total(cart)
    delivery_charge = 3.0 if delivery_method == 'delivery' else 0.0
    final_total = round(cart_total + delivery_charge, 2)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO orders (customer_name, items, total, delivery_method, address, phone_number, delivery_charge, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            name,
            json.dumps(cart),
            final_total,
            delivery_method,
            address if delivery_method == 'delivery' else '',
            phone_number if delivery_method == 'delivery' else '',
            delivery_charge,
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()
    conn.close()

    session.pop('cart', None)
    session.modified = True
    if delivery_method == 'delivery':
        flash(f'Thank you, {name}! Your delivery order total is ${final_total:.2f}.')
    else:
        flash(f'Thank you, {name}! Your pickup order total is ${final_total:.2f}.')
    return redirect(url_for('orders'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    
