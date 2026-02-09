# -*- coding: utf-8 -*-
"""Analiz sekmesi: Roi_Temizle, model seçimi, model parametreleri slider, Hesapla."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton, QComboBox,
    QSlider, QLabel, QMessageBox, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal

from config import (
    ANALYSIS_MODELS, DEFAULT_ANALYSIS_MODEL,
    YOUNG_LAPLACE_PARAMS, WENZEL_PARAMS, CIRCLE_FITTING_PARAMS,
    CASSIE_BAXTER_PARAMS, POLYNOMIAL_FITTING_PARAMS,
)


class AnalysisTab(QWidget):
    roi_clear_requested = pyqtSignal()
    calculate_requested = pyqtSignal(dict)  # model name + params

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.btn_roi_clear = QPushButton("Roi_Temizle")
        self.btn_roi_clear.clicked.connect(self.roi_clear_requested.emit)
        layout.addWidget(self.btn_roi_clear)

        model_group = QGroupBox("Modelleme")
        model_layout = QVBoxLayout(model_group)
        self.model_combo = QComboBox()
        self.model_combo.addItems(ANALYSIS_MODELS)
        self.model_combo.setCurrentText(DEFAULT_ANALYSIS_MODEL)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_layout.addWidget(QLabel("Model:"))
        model_layout.addWidget(self.model_combo)
        layout.addWidget(model_group)

        params_group = QGroupBox("Model parametreleri")
        self.params_layout = QVBoxLayout(params_group)
        self.param_sliders = {}
        self.param_labels = {}
        layout.addWidget(params_group)

        self.btn_calc = QPushButton("Hesapla")
        self.btn_calc.clicked.connect(self._on_calculate)
        layout.addWidget(self.btn_calc)

        self.result_label = QLabel("Sonuç: --")
        layout.addWidget(self.result_label)
        layout.addStretch()

        self._build_param_widgets()
        self._on_model_changed()

    def _build_param_widgets(self):
        all_params = {
            "Young_Laplace": YOUNG_LAPLACE_PARAMS,
            "Wenzel": WENZEL_PARAMS,
            "Circle_Fitting": CIRCLE_FITTING_PARAMS,
            "Cassie_Baxter": CASSIE_BAXTER_PARAMS,
            "Polynominal_Fitting": POLYNOMIAL_FITTING_PARAMS,
        }
        for model_name, params in all_params.items():
            for param_name, (min_v, max_v, default) in params.items():
                key = f"{model_name}.{param_name}"
                if key in self.param_sliders:
                    continue
                if isinstance(default, float):
                    scale = 100
                    s = QSlider(Qt.Horizontal)
                    s.setRange(int(min_v * scale), int(max_v * scale))
                    s.setValue(int(default * scale))
                    s.valueChanged.connect(lambda v, k=key: self._param_label_update(k, v / scale))
                    self.param_labels[key] = QLabel(f"{default:.2f}")
                else:
                    s = QSlider(Qt.Horizontal)
                    s.setRange(int(min_v), int(max_v))
                    s.setValue(int(default))
                    s.valueChanged.connect(lambda v, k=key: self._param_label_update(k, v))
                    self.param_labels[key] = QLabel(str(default))
                self.param_sliders[key] = (s, 100 if isinstance(default, float) else 1)

    def _param_label_update(self, key, value):
        if key in self.param_labels:
            if isinstance(value, float):
                self.param_labels[key].setText(f"{value:.2f}")
            else:
                self.param_labels[key].setText(str(value))

    def _on_model_changed(self):
        model = self.model_combo.currentText()
        for i in reversed(range(self.params_layout.count())):
            w = self.params_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        scale_map = {
            "Young_Laplace": YOUNG_LAPLACE_PARAMS,
            "Wenzel": WENZEL_PARAMS,
            "Circle_Fitting": CIRCLE_FITTING_PARAMS,
            "Cassie_Baxter": CASSIE_BAXTER_PARAMS,
            "Polynominal_Fitting": POLYNOMIAL_FITTING_PARAMS,
        }
        params = scale_map.get(model, {})
        for param_name, (min_v, max_v, default) in params.items():
            key = f"{model}.{param_name}"
            if key not in self.param_sliders:
                continue
            s, div = self.param_sliders[key]
            lbl = self.param_labels[key]
            if div != 1:
                s.setRange(int(min_v * div), int(max_v * div))
                s.setValue(int(default * div))
                lbl.setText(f"{default:.2f}")
            else:
                s.setRange(int(min_v), int(max_v))
                s.setValue(int(default))
                lbl.setText(str(default))
            self.params_layout.addWidget(QLabel(param_name))
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(s)
            row_layout.addWidget(lbl)
            self.params_layout.addWidget(row)
            s.setVisible(True)
            lbl.setVisible(True)

    def get_model_and_params(self):
        model = self.model_combo.currentText()
        scale_map = {
            "Young_Laplace": YOUNG_LAPLACE_PARAMS,
            "Wenzel": WENZEL_PARAMS,
            "Circle_Fitting": CIRCLE_FITTING_PARAMS,
            "Cassie_Baxter": CASSIE_BAXTER_PARAMS,
            "Polynominal_Fitting": POLYNOMIAL_FITTING_PARAMS,
        }
        params = scale_map.get(model, {})
        out = {}
        for param_name in params:
            key = f"{model}.{param_name}"
            if key in self.param_sliders:
                s, div = self.param_sliders[key]
                out[param_name] = s.value() / div if div != 1 else s.value()
        return {"model": model, "params": out}

    def _on_calculate(self):
        self.calculate_requested.emit(self.get_model_and_params())

    def set_result(self, text):
        self.result_label.setText(f"Sonuç: {text}")
