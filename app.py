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
    return render_template('index1.html', flowers=flowers, addons=addons)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower']
    quantity = int(request.form['quantity'])
    flowers, addons = load_data()
    cart = session.get('cart', {})

    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for('home'))

    if flower in cart:
        cart[flower]['quantity'] += quantity
    else:
        cart[flower] = {
            'price': flowers[flower]['price'],
            'quantity': quantity
        }

    session['cart'] = cart
    session.modified = True
    flash(f"{quantity} {flower}(s) added to cart.")
    return redirect(url_for('home'))




if __name__ == '__main__':
    app.run(debug=True)
    
