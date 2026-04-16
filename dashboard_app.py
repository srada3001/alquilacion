import os

import dash

from dashboard_app.callbacks import register_callbacks
from dashboard_app.data import obtener_fases
from dashboard_app.layout import build_layout


app = dash.Dash(__name__)
app.layout = build_layout(obtener_fases())

register_callbacks(app)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    debug = os.getenv("DASH_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    app.run(host=host, port=port, debug=debug)
