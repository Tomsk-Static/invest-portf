from flask import Flask, render_template, url_for



app = Flask(__name__)

@app.route('/')
def main():
    return render_template('index.html')


@app.route('/share_valut')
def share_valut():
    return render_template('share_valut')


@app.route('/history')
def history():
    return render_template('history')


