from __future__ import annotations

from components.operator_layout import page_header
from components.shap_explainability import render_shap_page
from services.support_data import shap_beeswarm, shap_feature_set


page_header("shap_explainability")

render_shap_page(shap_feature_set(), shap_beeswarm())
