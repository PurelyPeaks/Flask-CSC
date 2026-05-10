from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your  secret_key'


import json

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    with open('data/addons.json') as file:
        addons = json.load(file)
    return {'flowers': flowers, 'addons': addons}

@app.route('/')
def home():
    data = load_data()
    return render_template('index1.html', **data)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = load_data()
    if 'cart' not in session:
        session['cart'] = []
    flower = request.form.get('flower')
    quantity = request.form.get('quantity', 1, type=int)
    if flower and flower in data['flowers']:
        session['cart'].append({'flower': flower, 'quantity': quantity})
        session.modified = True
        flash('Added to cart!')
    return render_template('index1.html', **data)




if __name__ == '__main__':
    app.run(debug=True)
    
