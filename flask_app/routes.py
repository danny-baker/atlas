"""Routes for parent Flask app."""
from flask import current_app as flask_app
from flask import render_template


@flask_app.route("/dashapp")
def dash():
    """Dash page."""
    return render_template(
        "dash.jinja2",
        template="home-template",        
    )

