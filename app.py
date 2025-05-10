from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Minecraft Admin UI is working! *** TEST DEPLOY 3 ***"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
