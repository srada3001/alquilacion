from dashboard_app.pages.comparacion_variables.callbacks import (
    register_callbacks as register_comparacion_variables_callbacks,
)
from dashboard_app.pages.relaciones_no_lineales.callbacks import (
    register_callbacks as register_relaciones_no_lineales_callbacks,
)
from dashboard_app.pages.series_temporales.callbacks import (
    register_callbacks as register_series_temporales_callbacks,
)


def register_callbacks(app):
    register_series_temporales_callbacks(app)
    register_comparacion_variables_callbacks(app)
    register_relaciones_no_lineales_callbacks(app)
