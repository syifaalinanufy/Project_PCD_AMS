from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def landing():
    return render_template('landingpage.html')

@app.route('/app')
def editor():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)