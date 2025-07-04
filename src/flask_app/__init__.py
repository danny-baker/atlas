"""Initialize Flask app."""
from flask import Flask

def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('flask_app.config.Config')

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes

         # Import Dash application
        from .dash_app.app import init_dashboard
        app = init_dashboard(app)

        return app
    
def main():
    # app entry point
    # Spin up the intialised app on a webserver (i.e. run!)
    init_app().run(host='0.0.0.0', debug=False)
