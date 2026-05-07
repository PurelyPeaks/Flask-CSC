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
    return render_template('index.html', flowers=data['flowers'], addons=data['addons'])


if __name__ == '__main__':
    app.run(debug=True)
    
