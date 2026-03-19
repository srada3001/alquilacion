import dash

from dashboard_app.callbacks import register_callbacks
from dashboard_app.data import obtener_fases
from dashboard_app.layout import build_layout


app = dash.Dash(__name__)
app.layout = build_layout(obtener_fases())

register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True)
