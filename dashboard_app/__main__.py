import os

import dash

from analysis_core.dataset_catalog import obtener_fases
from dashboard_app.callbacks import register_callbacks
from dashboard_app.pages import build_layout, register_page_callback


fases = obtener_fases()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = build_layout(fases)

register_page_callback(app, fases)
register_callbacks(app)


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    debug = os.getenv("DASH_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
