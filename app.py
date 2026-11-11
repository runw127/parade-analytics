import os

from dash import Dash

from callbacks import register_callbacks
from data import load_data
from layout import build_layout


def create_app() -> Dash:
    app = Dash(
        __name__,
        title="Parade Visitor Analysis",
        compress=True,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    )
    app.layout = build_layout()
    register_callbacks(app)
    load_data()
    return app


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 8050)))
