from flask import Flask
from flask_cors import CORS
from routes.testing import testing_bp

app = Flask(__name__)
CORS(app)  # Enable CORS globally

# Register blueprint with a URL prefix
app.register_blueprint(testing_bp, url_prefix="/testing")

@app.route('/')
def home():
    return "Welcome to the Flask!"

if __name__ == '__main__':
    app.run(debug=True)
