from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your  secret_key'


import json

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    with open('data/addons.json') as file:
        addons = json.load(file)
    return flowers, addons

@app.route('/')
def home():
    flowers, addons = load_data()
    cart = session.get('cart', {})
    cart_total = sum(
        details['price'] * details['quantity'] + details.get('addon_cost', 0)
        for details in cart.values()
    )
    return render_template('index1.html', flowers=flowers, addons=addons, cart=cart, cart_total=cart_total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    quantity = int(request.form['quantity'])
    selected_addons = request.form.getlist('addons')
    flowers, addons = load_data()
    cart = session.get('cart', {})

    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for('home'))

    if any(addon not in addons for addon in selected_addons):
        flash("Invalid add-on selected.")
        return redirect(url_for('home'))

    addon_cost = sum(addons[addon]['price'] for addon in selected_addons)
    if flower in cart:
        cart[flower]['quantity'] += quantity
        existing_addons = set(cart[flower].get('addons', []))
        all_addons = sorted(existing_addons.union(selected_addons))
        cart[flower]['addons'] = all_addons
        cart[flower]['addon_cost'] = sum(addons[addon]['price'] for addon in all_addons)
    else:
        cart[flower] = {
            'price': flowers[flower]['price'],
            'quantity': quantity,
            'addons': selected_addons,
            'addon_cost': addon_cost
        }

    session['cart'] = cart
    session.modified = True
    addons_text = f" with {', '.join(selected_addons)}" if selected_addons else ""
    flash(f"{quantity} {flower}(s){addons_text} added to cart.")
    return redirect(url_for('home'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    flower = request.form['flower']
    cart = session.get('cart', {})

    if flower in cart:
        del cart[flower]
        session['cart'] = cart
        session.modified = True
        flash(f"{flower} removed from cart.")
    else:
        flash("Item not found in cart.")

    return redirect(url_for('home'))




@app.route('/checkout', methods=['POST'])
def checkout():
    name = request.form.get('name', '').strip()
    cart = session.get('cart', {})

    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for('home'))

    if not name:
        flash("Please enter your name to checkout.")
        return redirect(url_for('home'))

    cart_total = sum(
        details['price'] * details['quantity'] + details.get('addon_cost', 0)
        for details in cart.values()
    )
    session.pop('cart', None)
    session.modified = True
    flash(f"Thank you, {name}! Your order total is ${cart_total:.2f}.")
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
    
