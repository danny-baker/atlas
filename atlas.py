# Application entry point.
from src.flask_app import init_app

app = init_app()

if __name__ == "__main__": app.run(host='0.0.0.0', debug=False)