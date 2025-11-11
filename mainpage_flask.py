from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Welcome to OpenGate.fm!</h1>"

@app.route('/<name>')
def user(name):
    return f"<h2>Hello, {name}! This is your user page.</h2>"

if __name__ == '__main__':
    app.run()