from dashboard_app.callbacks.deep_analysis import register_deep_analysis_callbacks


def register_callbacks(app):
    register_deep_analysis_callbacks(app)
