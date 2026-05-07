from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your  secret_key'


import json

def load_data():
    with open('data/flowers.json') as file:
        flowers = json.load(file)
    return flowers

@app.route('/')
def home():
    flowers = load_data()
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
    
