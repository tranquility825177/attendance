from flask import Flask
from routes import register_routes
# import os


app = Flask(__name__)
app.secret_key = "ditec_secret_key"

# app.secret_key = os.getenv(
#     "SECRET_KEY",
#     "ditec_dev_secret"
# )
register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)