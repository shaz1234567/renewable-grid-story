"""Application entry point for the 2025 renewable-grid story."""

from dash import Dash

from src.app_data import load_data
from src.callbacks import register_callbacks
from src.views import create_layout

data = load_data()

app = Dash(
    __name__,
    title="The Renewable Grid, Hour by Hour",
    update_title="Updating the grid story…",
)
app.layout = create_layout(data)
register_callbacks(app, data)

# WSGI entry point used by Gunicorn and Render.
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
