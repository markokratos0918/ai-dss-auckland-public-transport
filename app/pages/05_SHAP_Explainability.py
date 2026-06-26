from __future__ import annotations

from components.operator_layout import page_header
from components.shap_explainability import render_shap_page
from services.support_data import top_features


page_header("shap_explainability")

features = top_features(15)
render_shap_page(features)