from dashboard_app.callbacks.analysis import register_analysis_callbacks
from dashboard_app.callbacks.filters import register_filters_callbacks
from dashboard_app.callbacks.selectors import register_selectors_callbacks
from dashboard_app.callbacks.timeseries import register_timeseries_callbacks


def register_callbacks(app):
    register_selectors_callbacks(app)
    register_filters_callbacks(app)
    register_timeseries_callbacks(app)
    register_analysis_callbacks(app)
