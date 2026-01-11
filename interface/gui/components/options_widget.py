from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QCheckBox, 
                             QComboBox, QSpinBox, QLabel, QPushButton, QGroupBox, QHBoxLayout,
                             QTabWidget, QPlainTextEdit, QTextEdit, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
import json
import os
import networkx as nx
from utils.logger import logger
from core.options_manager import options_manager
from interface.gui.utils.worker import WorkerThread

class OptionsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = options_manager.settings
        self.init_ui()
        # Listen to external changes to update UI if needed (omitted for brevity, but recommended)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Settings
        self.settings_tab = QWidget()
        self.init_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Tab 2: Relations & Risk
        self.relations_tab = QWidget()
        self.init_relations_tab()
        self.tabs.addTab(self.relations_tab, "Relations & Risk")
        
        # Tab 3: AI Configuration
        self.ai_tab = QWidget()
        self.init_ai_tab()
        self.tabs.addTab(self.ai_tab, "AI Config")

    def init_ai_tab(self):
        layout = QVBoxLayout(self.ai_tab)
        
        provider_group = QGroupBox("AI Provider")
        prov_layout = QFormLayout()
        
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["openai", "ollama"])
        self.ai_provider.setCurrentText(self.settings.get("ai_provider", "openai"))
        prov_layout.addRow("Provider:", self.ai_provider)
        
        self.ai_model = QLineEdit()
        self.ai_model.setText(self.settings.get("ai_model", "gpt-3.5-turbo"))
        self.ai_model.setPlaceholderText("e.g. gpt-4, llama2")
        prov_layout.addRow("Model Name:", self.ai_model)
        
        self.ai_key = QLineEdit()
        self.ai_key.setText(self.settings.get("ai_api_key", ""))
        self.ai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key.setPlaceholderText("sk-...")
        prov_layout.addRow("API Key:", self.ai_key)
        
        self.ai_base_url = QLineEdit()
        self.ai_base_url.setText(self.settings.get("ai_base_url", "https://api.openai.com/v1"))
        self.ai_base_url.setPlaceholderText("https://api.openai.com/v1")
        prov_layout.addRow("Base URL:", self.ai_base_url)
        
        provider_group.setLayout(prov_layout)
        layout.addWidget(provider_group)
        
        # Connect
        self.ai_provider.currentTextChanged.connect(self._update_ai_config)
        self.ai_model.textChanged.connect(self._update_ai_config)
        self.ai_key.textChanged.connect(self._update_ai_config)
        self.ai_base_url.textChanged.connect(self._update_ai_config)
        
        layout.addStretch()

    def _update_ai_config(self):
        options_manager.set_option("ai_provider", self.ai_provider.currentText())
        options_manager.set_option("ai_model", self.ai_model.text())
        options_manager.set_option("ai_api_key", self.ai_key.text())
        options_manager.set_option("ai_base_url", self.ai_base_url.text())
        
        from core.ai_manager import ai_manager
        ai_manager.reload_config()

    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        
        # 1. General Settings
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Nord", "Dark", "Light", "Tactical"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Nord"))
        general_layout.addRow("Theme:", self.theme_combo)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Chinese"])
        self.lang_combo.setCurrentText(self.settings.get("language", "English"))
        general_layout.addRow("Language:", self.lang_combo)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        style_group = QGroupBox("Visual Style")
        style_layout = QFormLayout()
        self.style_combo = QComboBox()
        self.style_combo.addItems(["minimal", "nord"])
        self.style_combo.setCurrentText(self.settings.get("visual_style", "minimal"))
        style_layout.addRow("Style:", self.style_combo)
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)
        
        # 2. Analysis Settings
        analysis_group = QGroupBox("Code Analysis")
        analysis_layout = QFormLayout()
        
        self.auto_analyze_check = QCheckBox()
        self.auto_analyze_check.setChecked(self.settings.get("auto_analyze", True))
        analysis_layout.addRow("Auto-analyze on open:", self.auto_analyze_check)
        
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setRange(1, 100)
        self.max_depth_spin.setValue(self.settings.get("max_recursion_depth", 10))
        analysis_layout.addRow("Max Recursion Depth:", self.max_depth_spin)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # 3. Visualization Settings
        vis_group = QGroupBox("Visualization")
        vis_layout = QFormLayout()
        
        self.show_minimap_check = QCheckBox()
        self.show_minimap_check.setChecked(self.settings.get("show_minimap", False))
        vis_layout.addRow("Show Minimap (Experimental):", self.show_minimap_check)
        
        self.infinite_canvas_check = QCheckBox()
        self.infinite_canvas_check.setChecked(self.settings.get("infinite_canvas", True))
        vis_layout.addRow("Infinite Canvas:", self.infinite_canvas_check)
        
        self.min_spacing_spin = QSpinBox()
        self.min_spacing_spin.setRange(10, 200)
        self.min_spacing_spin.setValue(int(self.settings.get("min_spacing", 30)))
        vis_layout.addRow("Minimum Spacing (px):", self.min_spacing_spin)
        
        vis_group.setLayout(vis_layout)
        layout.addWidget(vis_group)
        
        fmt_group = QGroupBox("Number Format")
        fmt_layout = QFormLayout()
        self.decimals_spin = QSpinBox()
        self.decimals_spin.setRange(0, 6)
        self.decimals_spin.setValue(int(self.settings.get("number_decimals", 2)))
        fmt_layout.addRow("Decimals:", self.decimals_spin)
        self.thousand_check = QCheckBox()
        self.thousand_check.setChecked(bool(self.settings.get("thousand_sep", True)))
        fmt_layout.addRow("Thousand Separator:", self.thousand_check)
        fmt_group.setLayout(fmt_layout)
        layout.addWidget(fmt_group)
        
        # Undo/Redo
        undo_redo_bar = QHBoxLayout()
        self.btn_undo = QPushButton("Undo")
        self.btn_redo = QPushButton("Redo")
        undo_redo_bar.addWidget(self.btn_undo)
        undo_redo_bar.addWidget(self.btn_redo)
        layout.addLayout(undo_redo_bar)
        
        layout.addStretch()

        # Connect real-time apply
        self.theme_combo.currentTextChanged.connect(lambda v: options_manager.set_option("theme", v))
        self.lang_combo.currentTextChanged.connect(lambda v: options_manager.set_option("language", v))
        self.style_combo.currentTextChanged.connect(lambda v: options_manager.set_option("visual_style", v))
        self.auto_analyze_check.stateChanged.connect(lambda _: options_manager.set_option("auto_analyze", self.auto_analyze_check.isChecked()))
        self.max_depth_spin.valueChanged.connect(lambda v: options_manager.set_option("max_recursion_depth", int(v)))
        self.show_minimap_check.stateChanged.connect(lambda _: options_manager.set_option("show_minimap", self.show_minimap_check.isChecked()))
        self.infinite_canvas_check.stateChanged.connect(lambda _: options_manager.set_option("infinite_canvas", self.infinite_canvas_check.isChecked()))
        self.min_spacing_spin.valueChanged.connect(lambda v: options_manager.set_option("min_spacing", int(v)))
        self.decimals_spin.valueChanged.connect(lambda v: options_manager.set_option("number_decimals", int(v)))
        self.thousand_check.stateChanged.connect(lambda _: options_manager.set_option("thousand_sep", self.thousand_check.isChecked()))

        self.btn_undo.clicked.connect(lambda: options_manager.undo())
        self.btn_redo.clicked.connect(lambda: options_manager.redo())

    def init_relations_tab(self):
        layout = QVBoxLayout(self.relations_tab)
        
        layout.addWidget(QLabel("<b>relations.json Editor</b>"))
        
        self.rel_editor = QPlainTextEdit()
        self.load_relations() # Initial load
        layout.addWidget(self.rel_editor)
        
        btn_layout = QHBoxLayout()
        self.btn_load_rel = QPushButton("Reload from File")
        self.btn_save_rel = QPushButton("Save to File")
        self.btn_validate = QPushButton("Validate JSON")
        btn_layout.addWidget(self.btn_load_rel)
        btn_layout.addWidget(self.btn_save_rel)
        btn_layout.addWidget(self.btn_validate)
        layout.addLayout(btn_layout)
        
        layout.addWidget(QLabel("<b>Risk Analysis Report</b>"))
        self.risk_report = QTextEdit()
        self.risk_report.setReadOnly(True)
        self.risk_report.setMaximumHeight(150)
        layout.addWidget(self.risk_report)
        
        self.btn_analyze = QPushButton("Analyze Risks & Cycles")
        layout.addWidget(self.btn_analyze)
        
        # Connect
        self.btn_load_rel.clicked.connect(self.load_relations)
        self.btn_save_rel.clicked.connect(self.save_relations)
        self.btn_validate.clicked.connect(self.validate_relations)
        self.btn_analyze.clicked.connect(self.analyze_risk)
        
    def load_relations(self):
        try:
            rel_path = os.path.join(os.getcwd(), "relations.json")
            if os.path.exists(rel_path):
                with open(rel_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.rel_editor.setPlainText(content)
            else:
                # Default template
                default_rel = [
                    {
                        "source": "FrontendModule",
                        "target": "BackendAPI",
                        "type": "default",
                        "weight": 1,
                        "risk_level": "low",
                        "layer": "FRONTEND"
                    }
                ]
                self.rel_editor.setPlainText(json.dumps(default_rel, indent=2))
        except Exception as e:
            logger.error(f"Failed to load relations: {e}")

    def save_relations(self):
        try:
            content = self.rel_editor.toPlainText()
            # Validate first
            json.loads(content)
            
            rel_path = os.path.join(os.getcwd(), "relations.json")
            with open(rel_path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Success", "relations.json saved!")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Invalid JSON: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def validate_relations(self):
        try:
            content = self.rel_editor.toPlainText()
            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError("Root must be a list")
            for item in data:
                if "source" not in item or "target" not in item:
                    raise ValueError("Items must have source and target")
            QMessageBox.information(self, "Valid", "JSON is valid!")
        except Exception as e:
            QMessageBox.warning(self, "Invalid", str(e))

    def analyze_risk(self):
        content = self.rel_editor.toPlainText()
        
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("Analyzing...")
        self.risk_report.setHtml("<i>Analysis in progress...</i>")
        
        # Use WorkerThread to prevent UI blocking
        worker = WorkerThread(self._run_analysis, content)
        worker.signals.result.connect(self._on_analysis_result)
        worker.signals.finished.connect(self._on_analysis_finished)
        
        self._worker = worker # Prevent GC
        worker.start()

    @staticmethod
    def _run_analysis(content):
        report = []
        try:
            data = json.loads(content)
            
            G = nx.DiGraph()
            node_count = 0
            edge_count = 0
            
            for item in data:
                src = item.get("source")
                tgt = item.get("target")
                if src and tgt:
                    G.add_edge(src, tgt)
                    edge_count += 1
            
            node_count = G.number_of_nodes()
            
            # Simple Cycles
            cycles = list(nx.simple_cycles(G))
            
            report.append(f"<h3>Analysis Result</h3>")
            report.append(f"Nodes: {node_count}, Edges: {edge_count}<br>")
            
            if cycles:
                report.append(f"<h4 style='color:red'>Found {len(cycles)} Cycles:</h4>")
                for c in cycles:
                    report.append(f"<li style='color:red'>{' -> '.join(c)} -> {c[0]}</li>")
            else:
                report.append("<h4 style='color:green'>No cycles found.</h4>")
                
            report.append("<br><b>Note:</b> This only analyzes manual relations. Full project risk analysis is available in the Graph View.")
            
            return "".join(report)
            
        except Exception as e:
            return f"<span style='color:red'>Analysis failed: {str(e)}</span>"

    def _on_analysis_result(self, report_html):
        self.risk_report.setHtml(report_html)
        
    def _on_analysis_finished(self):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("Analyze Risks & Cycles")
