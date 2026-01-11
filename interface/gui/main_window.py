import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTabWidget, QFileDialog,
                             QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit, QScrollArea,
                             QComboBox, QLineEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from core.api_adapter import api_adapter
from core.project_manager import project_manager
from core.code_analyzer import code_analyzer
from core.structure_visualizer import structure_visualizer
from core.language_manager import lang_manager
from core.code_graph_builder import code_graph_builder
from core.project_analyzer import project_analyzer
from interface.gui.components.code_editor import CodeEditor
from interface.gui.components.node_graph import NodeGraphWidget
from interface.gui.components.node_toolbox import NodeToolbox
from interface.gui.components.options_widget import OptionsWidget
from engine.node_engine import execution_engine
from core.options_manager import options_manager
from utils.logger import logger
from ai.plugin_manager import AIPluginRegistry
import ai.plugins.layout_optimizer
import ai.plugins.code_analyzer
import ai.plugins.smart_search
import ai.plugins.risk_assessor
import ai.plugins.node_generator
from interface.gui.utils.worker import WorkerThread
from interface.gui.styles import AppTheme
from PyQt6.QtWidgets import QProgressBar
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("General Visual Programming Assistant (GVPA)")
        self.resize(1200, 800)
        
        # Subscribe to language changes
        lang_manager.add_observer(self.update_texts)
        
        self.create_menu()
        self.setup_ui()
        self.update_texts() # Initial text update

    def create_menu(self):
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu('File')
        
        self.open_action = QAction('Open Project', self)
        self.open_action.setShortcut('Ctrl+O')
        self.open_action.triggered.connect(self.open_project_dialog)
        self.file_menu.addAction(self.open_action)

        self.exit_action = QAction('Exit', self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        # Language Switcher in Menu
        lang_menu = self.menubar.addMenu('Language')
        en_action = QAction('English', self)
        en_action.triggered.connect(lambda: lang_manager.set_language('en'))
        lang_menu.addAction(en_action)
        
        zh_action = QAction('中文', self)
        zh_action.triggered.connect(lambda: lang_manager.set_language('zh'))
        lang_menu.addAction(zh_action)
        
        # Options as top-level menu
        self.options_menu = self.menubar.addMenu('Options')
        act_open_opts = QAction('Open Options', self)
        act_open_opts.triggered.connect(self.show_options_dialog)
        self.options_menu.addAction(act_open_opts)
        act_undo = QAction('Undo Option Change', self)
        act_undo.triggered.connect(lambda: options_manager.undo())
        self.options_menu.addAction(act_undo)
        act_redo = QAction('Redo Option Change', self)
        act_redo.triggered.connect(lambda: options_manager.redo())
        self.options_menu.addAction(act_redo)

        # AI Menu
        self.ai_menu = self.menubar.addMenu('AI Assistant')
        
        opt_layout_action = QAction('Smart Layout Optimization', self)
        opt_layout_action.setShortcut('Ctrl+L')
        opt_layout_action.triggered.connect(self.run_ai_layout_optimization)
        self.ai_menu.addAction(opt_layout_action)
        
        code_analysis_action = QAction('Deep Code Analysis', self)
        code_analysis_action.triggered.connect(self.run_ai_code_analysis)
        self.ai_menu.addAction(code_analysis_action)
        
        # Priority 3
        smart_search_action = QAction('Smart Search', self)
        smart_search_action.setShortcut('Ctrl+F')
        smart_search_action.triggered.connect(self.run_ai_smart_search)
        self.ai_menu.addAction(smart_search_action)

        # Priority 4
        risk_check_action = QAction('Risk Governance Check', self)
        risk_check_action.triggered.connect(self.run_ai_risk_check)
        self.ai_menu.addAction(risk_check_action)

        # Priority 5
        node_gen_action = QAction('Generate Node Code', self)
        node_gen_action.triggered.connect(self.run_ai_node_generation)
        self.ai_menu.addAction(node_gen_action)

    def setup_ui(self):
        # Main Layout: Splitter (Project Tree | Main Content)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout(self.central_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 1. Project Explorer (Left)
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Project Explorer")
        self.project_tree.setFixedWidth(250)
        self.project_tree.itemClicked.connect(self.on_file_clicked)
        splitter.addWidget(self.project_tree)
        
        # 2. Main Content Area (Right)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)
        
        # Create Tabs - Order matters, and we catch errors
        try:
            self.create_structure_tab()
            self.create_code_tab()
            self.create_visual_prog_tab()
            self.create_options_tab()
        except Exception as e:
            logger.error(f"Error creating tabs: {e}")
        
        # Observe options changes for real-time apply
        options_manager.add_observer(self.apply_options)
        # Apply initial settings
        self.apply_options(options_manager.settings)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 4)

    def create_structure_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- Top Control Bar (Features) ---
        top_bar = QHBoxLayout()
        
        self.btn_analyze_project = QPushButton("Analyze Project")
        self.btn_analyze_project.clicked.connect(self.analyze_and_visualize_project)
        self.btn_analyze_project.setStyleSheet(AppTheme.get_btn_style(AppTheme.BTN_PRIMARY))
        top_bar.addWidget(self.btn_analyze_project)
        
        self.btn_convert_graph = QPushButton("Convert File")
        self.btn_convert_graph.clicked.connect(self.convert_current_code_to_graph)
        top_bar.addWidget(self.btn_convert_graph)
        
        self.btn_check_arch = QPushButton("Check Arch")
        self.btn_check_arch.clicked.connect(self.check_architecture)
        top_bar.addWidget(self.btn_check_arch)
        
        self.btn_load_trace = QPushButton("Load Trace")
        self.btn_load_trace.clicked.connect(self.load_trace_and_visualize)
        top_bar.addWidget(self.btn_load_trace)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.setFixedWidth(200)
        top_bar.addWidget(self.progress_bar)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # --- Content Area (Splitter) ---
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)
        
        # Left: Analysis Text (Read-Only)
        self.analysis_view = QTextEdit()
        self.analysis_view.setReadOnly(True)
        content_splitter.addWidget(self.analysis_view)
        
        # Center: Graphical View
        self.graph_scroll = QScrollArea()
        self.graph_view = QLabel("Select a python file to visualize structure")
        self.graph_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_view.setStyleSheet("background-color: white;")
        self.graph_scroll.setWidget(self.graph_view)
        self.graph_scroll.setWidgetResizable(True)
        content_splitter.addWidget(self.graph_scroll)
        
        # Right: AI Assistant (New Visible Dock)
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setContentsMargins(0, 0, 0, 0)
        
        ai_label = QLabel("AI Architecture Assistant")
        ai_label.setStyleSheet("font-weight: bold; color: #5E81AC; margin-bottom: 5px;")
        ai_layout.addWidget(ai_label)
        
        self.ai_log = QTextEdit()
        self.ai_log.setReadOnly(True)
        self.ai_log.setPlaceholderText("AI responses will appear here...")
        ai_layout.addWidget(self.ai_log)
        
        ai_input_layout = QHBoxLayout()
        self.chat_query = QLineEdit()
        self.chat_query.setPlaceholderText("Ask e.g. 'Find circular dependencies'...")
        self.chat_query.returnPressed.connect(self.on_chat_query)
        ai_input_layout.addWidget(self.chat_query)
        
        btn_ask = QPushButton("Ask")
        btn_ask.clicked.connect(self.on_chat_query)
        ai_input_layout.addWidget(btn_ask)
        
        ai_layout.addLayout(ai_input_layout)
        
        content_splitter.addWidget(ai_widget)
        
        # Set Splitter Ratios (Text : Graph : AI)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setStretchFactor(2, 1)
        
        self.tabs.addTab(tab, "Structure & Logic")

    def create_code_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.code_editor = CodeEditor()
        layout.addWidget(self.code_editor)
        self.tabs.addTab(tab, "Code Viewer")

    def create_visual_prog_tab(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        
        # Splitter for Toolbox | Graph
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Toolbox
        self.toolbox = NodeToolbox()
        splitter.addWidget(self.toolbox)
        
        # Graph Area
        graph_area = QWidget()
        graph_layout = QVBoxLayout(graph_area)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_save_graph = QPushButton("Save Graph")
        self.btn_save_graph.clicked.connect(self.save_graph)
        self.btn_load_graph = QPushButton("Load Graph")
        self.btn_load_graph.clicked.connect(self.load_graph)
        self.btn_run_graph = QPushButton("Run Graph")
        self.btn_run_graph.clicked.connect(self.run_graph)
        self.btn_run_graph.setStyleSheet(AppTheme.get_btn_style(AppTheme.BTN_SUCCESS))
        
        # View Controls
        self.btn_center = QPushButton("Auto Center")
        self.btn_center.clicked.connect(lambda: self.node_graph.center_view())
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter Nodes (File/Func)...")
        self.search_bar.textChanged.connect(lambda text: self.node_graph.filter_nodes(text))
        
        toolbar.addWidget(self.btn_save_graph)
        toolbar.addWidget(self.btn_load_graph)
        toolbar.addWidget(self.btn_run_graph)
        toolbar.addSpacing(20)
        toolbar.addWidget(self.btn_center)
        toolbar.addWidget(self.search_bar)
        
        toolbar.addStretch()
        graph_layout.addLayout(toolbar)
        
        # Node Graph Widget
        self.node_graph = NodeGraphWidget()
        graph_layout.addWidget(self.node_graph)
        
        # Connect Signals for Bidirectional Linking
        self.node_graph.node_selected.connect(self.on_node_selected)
        self.code_editor.cursorPositionChanged.connect(self.on_code_cursor_moved)
        
        splitter.addWidget(graph_area)
        splitter.setStretchFactor(1, 4)
        
        self.tabs.addTab(tab, "Visual Programming")

    def create_options_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.options_widget = OptionsWidget()
        layout.addWidget(self.options_widget)
        self.tabs.addTab(tab, "Options")
    
    def show_options_dialog(self):
        # Reuse embedded widget in a simple dialog container
        from PyQt6.QtWidgets import QDialog
        dlg = QDialog(self)
        dlg.setWindowTitle("Options")
        v = QVBoxLayout(dlg)
        ow = OptionsWidget()
        v.addWidget(ow)
        dlg.resize(480, 540)
        dlg.exec()

    def update_texts(self):
        """Update UI texts based on current language"""
        self.setWindowTitle(lang_manager.get("app_title"))
        self.file_menu.setTitle(lang_manager.get("file"))
        self.open_action.setText(lang_manager.get("open_project"))
        self.exit_action.setText(lang_manager.get("exit"))
        
        self.tabs.setTabText(0, lang_manager.get("tabs.structure"))
        self.tabs.setTabText(1, lang_manager.get("tabs.code_viewer"))
        self.tabs.setTabText(2, lang_manager.get("tabs.visual_prog"))
        self.tabs.setTabText(3, "Options") # No lang key yet
        
        self.btn_save_graph.setText(lang_manager.get("node_graph.save"))
        self.btn_load_graph.setText(lang_manager.get("node_graph.load"))
        


    # --- Actions ---

    def open_project_dialog(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if dir_path:
            if project_manager.open_project(dir_path):
                self.populate_project_tree()

    def populate_project_tree(self):
        self.project_tree.clear()
        structure = project_manager.get_file_structure()
        if not structure:
            return

        root_item = QTreeWidgetItem([structure["name"]])
        root_item.setData(0, Qt.ItemDataRole.UserRole, structure["path"])
        self.project_tree.addTopLevelItem(root_item)
        
        self._add_tree_items(root_item, structure.get("children", []))
        root_item.setExpanded(True)

    def _add_tree_items(self, parent_item, children):
        for child in children:
            item = QTreeWidgetItem([child["name"]])
            item.setData(0, Qt.ItemDataRole.UserRole, child["path"])
            parent_item.addChild(item)
            if child.get("children"):
                self._add_tree_items(item, child["children"])

    def on_file_clicked(self, item, column):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not file_path:
            return
        self.load_file(file_path)

    def load_file(self, file_path):
        self.current_file_path = file_path # Store for later use

        # 1. Load file content into Code Editor
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.code_editor.setPlainText(content)
                # Determine language for highlighting
                ext = os.path.splitext(file_path)[1].lower()
                lang = "python" if ext == ".py" else "text"
                if ext in [".json", ".js", ".html", ".css", ".md", ".xml", ".yaml", ".yml"]:
                    lang = ext[1:]
                self.code_editor.set_language(lang)
            except Exception as e:
                self.code_editor.setPlainText(f"Error reading file: {e}")

        # 2. Analyze if Python (Async)
        if file_path.endswith('.py'):
            self.start_file_analysis(file_path)

    def start_file_analysis(self, file_path):
        logger.info(f"Starting async analysis for: {file_path}")
        self.analysis_view.setHtml("<i>Analyzing...</i>")
        
        self.file_analysis_thread = WorkerThread(code_analyzer.analyze_file, file_path)
        self.file_analysis_thread.finished.connect(lambda result: self.on_file_analysis_finished(file_path, result))
        self.file_analysis_thread.start()

    def on_file_analysis_finished(self, file_path, result):
        # Check if the user is still looking at this file
        if not hasattr(self, 'current_file_path') or self.current_file_path != file_path:
            return
            
        self.current_analysis = result
        if result:
            self.display_analysis(file_path, result)
        else:
            self.analysis_view.setHtml("<i>Analysis failed or empty.</i>")

    def on_node_selected(self, file_path, lineno):
        if getattr(self, 'updating_from_code', False):
            logger.debug("Skip on_node_selected due to updating_from_code")
            return
        
        self.updating_from_graph = True
        try:
            if hasattr(self, 'current_file_path') and self.current_file_path != file_path:
                 self.load_file(file_path)
            
            self.code_editor.goto_line(lineno)
        finally:
            self.updating_from_graph = False

    def on_code_cursor_moved(self):
        if getattr(self, 'updating_from_graph', False):
            logger.debug("Skip on_code_cursor_moved due to updating_from_graph")
            return
        
        self.updating_from_code = True
        try:
            cursor = self.code_editor.textCursor()
            lineno = cursor.blockNumber() + 1
            if hasattr(self, 'current_file_path'):
                self.node_graph.select_node_by_code_location(self.current_file_path, lineno)
        finally:
            self.updating_from_code = False
    
    def apply_options(self, settings: dict):
        try:
            # Theme and canvas
            self.node_graph.apply_options(settings)
            
            # Apply Global App Theme
            app = QApplication.instance()
            if app:
                AppTheme.apply_theme(app, settings.get("theme", "Nord"))

            # Language bridge
            lang_text = settings.get("language", "English")
            if lang_text.lower().startswith("ch"):
                lang_manager.set_language('zh')
            else:
                lang_manager.set_language('en')
        except Exception as e:
            logger.error(f"Apply options in MainWindow failed: {e}")

    def display_analysis(self, file_path, analysis):
        # 1. Update Text View
        text = f"<h1>Analysis: {file_path.split(os.sep)[-1]}</h1>"
        
        text += "<h2>Imports</h2><ul>"
        for imp in analysis.get("imports", []):
            text += f"<li>{imp}</li>"
        text += "</ul>"
        
        text += "<h2>Classes</h2>"
        for cls in analysis.get("classes", []):
            text += f"<h3>class {cls['name']}({', '.join(cls['bases'])})</h3>"
            text += "<ul>"
            for method in cls['methods']:
                text += f"<li>def {method['name']}({', '.join(method['args'])})</li>"
            text += "</ul>"
            
        text += "<h2>Global Functions</h2><ul>"
        for func in analysis.get("functions", []):
            text += f"<li>def {func['name']}({', '.join(func['args'])})</li>"
        text += "</ul>"
        
        self.analysis_view.setHtml(text)

        # 2. Update Graph View
        img_buf = structure_visualizer.create_class_diagram(analysis)
        if img_buf:
            pixmap = QPixmap()
            pixmap.loadFromData(img_buf.getvalue())
            self.graph_view.setPixmap(pixmap)
            self.graph_view.adjustSize()
        else:
            self.graph_view.setText(lang_manager.get("msg.no_graph"))

    def convert_current_code_to_graph(self):
        """Convert the currently analyzed code to a node graph"""
        if not hasattr(self, 'current_analysis') or not self.current_analysis:
            return
            
        logger.info("Converting code analysis to node graph...")
        graph_data = code_graph_builder.build_graph(self.current_analysis)
        
        if graph_data:
            self.node_graph.scene.deserialize(graph_data)
            self.tabs.setCurrentIndex(2) # Switch to Visual Prog tab
            logger.info("Graph generated and loaded.")
        else:
            logger.warning("Failed to generate graph data.")

    def analyze_and_visualize_project(self):
        """Analyze the entire project and generate a graph (Async)"""
        root_item = self.project_tree.topLevelItem(0)
        if root_item:
            project_path = root_item.data(0, Qt.ItemDataRole.UserRole)
        else:
            project_path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
            
        if not project_path:
            return

        logger.info(f"Starting async analysis for: {project_path}")
        self.analysis_view.setHtml("<h1>Analyzing project... please wait.</h1>")
        
        # UI State
        self.btn_analyze_project.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Start Thread
        self.analysis_thread = WorkerThread(self._run_analysis_task, project_path)
        self.analysis_thread.finished.connect(self._on_analysis_finished)
        self.analysis_thread.error.connect(self._on_analysis_error)
        self.analysis_thread.start()

    def _run_analysis_task(self, project_path):
        """Task running in background thread"""
        analysis = project_analyzer.analyze_project(project_path)
        graph_data = code_graph_builder.build_graph(analysis)
        return {"analysis": analysis, "graph_data": graph_data, "path": project_path}

    def _on_analysis_finished(self, result):
        """Called on main thread when analysis completes"""
        self.btn_analyze_project.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        analysis = result["analysis"]
        graph_data = result["graph_data"]
        project_path = result["path"]
        
        logger.info(f"Project analysis complete. Functions: {len(analysis['functions'])}, Calls: {len(analysis['calls'])}")
        
        # Display Stats
        text = f"<h1>Project Analysis: {os.path.basename(project_path)}</h1>"
        text += f"<p>Total Functions/Methods: {len(analysis['functions'])}</p>"
        text += f"<p>Total Calls Detected: {len(analysis['calls'])}</p>"
        self.analysis_view.setHtml(text)
        
        if graph_data:
            self.node_graph.scene.deserialize(graph_data)
            self.tabs.setCurrentIndex(2) # Switch to Visual Prog tab
            logger.info("Project graph generated.")
        else:
            logger.error("Failed to generate project graph.")

    def _on_analysis_error(self, error_msg):
        self.btn_analyze_project.setEnabled(True)
        self.progress_bar.setVisible(False)
        logger.error(f"Analysis failed: {error_msg}")
        self.analysis_view.setHtml(f"<h1>Error</h1><p>{error_msg}</p>")


    # --- Time Travel ---
    # Removed as per user request
    # def on_time_travel_changed(self, commit_hash): ...

    def on_chat_query(self):
        query = self.chat_query.text()
        if not query: return
        
        # Display User Query
        self.ai_log.append(f"<b>You:</b> {query}")
        self.chat_query.clear()
        
        logger.info(f"AI Query: {query}")
        
        # Get current graph data (serialized)
        graph_data = self.node_graph.scene.serialize()
        
        # UI State
        self.ai_log.append("<i>Thinking...</i>")
        
        # Start Thread
        self.ai_thread = WorkerThread(self._run_ai_query_task, graph_data, query)
        self.ai_thread.finished.connect(self._on_ai_query_finished)
        self.ai_thread.error.connect(self._on_ai_query_error)
        self.ai_thread.start()

    def _run_ai_query_task(self, graph_data, query):
        from core.ai_manager import ai_manager
        return ai_manager.query_graph(graph_data, query)

    def _on_ai_query_finished(self, result):
        # Remove "Thinking..." (Approximation, just append new result)
        # Better: use a cursor or replace last line, but appending is safe enough for now.
        
        titles = result.get("node_titles", [])
        if titles:
            self.node_graph.highlight_nodes_by_titles(titles)
            self.tabs.setCurrentIndex(2) # Switch to Visual Prog tab
            msg = f"Highlighted {len(titles)} nodes: {', '.join(titles[:5])}..."
            logger.info(msg)
            self.ai_log.append(f"<b>AI:</b> Found matches. {msg}")
        else:
            logger.info("AI found no matching nodes")
            self.ai_log.append("<b>AI:</b> No matching nodes found in the current graph.")

    def _on_ai_query_error(self, error_msg):
        self.ai_log.append(f"<b>AI Error:</b> {error_msg}")


    def check_architecture(self):
        """Run architecture rules check"""
        from core.architecture_guard import architecture_guard
        from PyQt6.QtWidgets import QMessageBox
        
        graph_data = self.node_graph.scene.serialize()
        violations = architecture_guard.check_graph(graph_data)
        
        if violations:
            msg = f"Found {len(violations)} Architecture Violations:\n\n"
            for v in violations[:10]:
                msg += f"- {v['source']} -> {v['target']}: {v['message']}\n"
            if len(violations) > 10:
                msg += f"... and {len(violations)-10} more."
            
            QMessageBox.warning(self, "Architecture Check", msg)
        else:
            QMessageBox.information(self, "Architecture Check", "No violations found. Architecture is clean.")

    def load_trace_and_visualize(self):
        """Load runtime trace JSON and update graph"""
        import json
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Trace JSON", "", "JSON Files (*.json)")
        if not file_path: return
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                trace_data = json.load(f)
            
            logger.info(f"Loaded trace data with {len(trace_data)} entries")
            
            # Rebuild graph with trace data
            if hasattr(self, 'current_analysis'):
                graph_data = code_graph_builder.build_graph(self.current_analysis, trace_data=trace_data)
                self.node_graph.scene.deserialize(graph_data)
                self.tabs.setCurrentIndex(2)
                logger.info("Graph updated with Dead Code Detection")
        except Exception as e:
            logger.error(f"Failed to load trace: {e}")

    # --- Node Graph Methods ---
    def save_graph(self):
        self.node_graph.save_state()

    def load_graph(self):
        self.node_graph.load_state()

    def run_graph(self):
        self.save_graph() # Save before run
        data = self.node_graph.scene.serialize()
        logger.info("Starting graph execution...")
        success = execution_engine.run_graph(data)
        if success:
            logger.info("Graph executed successfully.")
        else:
            logger.error("Graph execution failed.")

    # --- Vis Methods ---
    # Visualization methods removed as part of cleanup

    def run_ai_layout_optimization(self):
        logger.info("Starting AI Layout Optimization...")
        nodes = []
        for n in self.node_graph.scene.nodes:
            # Get existing params or fallback to object id for mapping
            nid = n.params.get("id", str(id(n)))
            nodes.append({
                "id": nid,
                "x": n.pos().x(),
                "y": n.pos().y(),
                "width": n.width,
                "height": n.height
            })
        edges = []
        for e in self.node_graph.scene.edges:
             src_node = e.source_socket.parent_node
             tgt_node = e.target_socket.parent_node
             src = src_node.params.get("id", str(id(src_node)))
             tgt = tgt_node.params.get("id", str(id(tgt_node)))
             edges.append({"source": src, "target": tgt})
             
        context = {"nodes": nodes, "edges": edges}
        result = AIPluginRegistry.execute_plugin("AI Graph Optimizer", context)
        
        if result and result.get("status") == "success":
            updates = result.get("updates", {})
            # Apply updates
            for n in self.node_graph.scene.nodes:
                nid = n.params.get("id", str(id(n)))
                if nid in updates:
                    pos = updates[nid]
                    n.setPos(pos["x"], pos["y"])
            logger.info(result.get("message"))
            # self.node_graph.center_view() 
            
    def run_ai_code_analysis(self):
        project_path = project_manager.current_project_path
        if not project_path:
            logger.warning("No project loaded for analysis.")
            return
            
        logger.info(f"Starting AI Code Analysis on {project_path}...")
        context = {"project_path": project_path}
        result = AIPluginRegistry.execute_plugin("AI Code Analyzer", context)
        
        if result and result.get("status") == "success":
            findings = result.get("findings", [])
            logger.info(f"AI found {len(findings)} potential dynamic links.")
            # Visualize findings in log for now
            if findings:
                msg = "AI Analysis Findings:\n"
                for f in findings[:10]:
                    msg += f"- [{f['type']}] {os.path.basename(f['file'])}:{f['line']} -> {f['target']}\n"
                if len(findings) > 10:
                    msg += f"... and {len(findings)-10} more."
                
                # Show in AI Log
                if hasattr(self, 'ai_log'):
                    self.ai_log.append(f"<b>AI Code Analysis:</b><br><pre>{msg}</pre>")

    def run_ai_smart_search(self):
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "AI Smart Search", "Enter query (e.g., 'Find image nodes'):")
        if ok and text:
            # Prepare Context
            nodes = []
            for n in self.node_graph.scene.nodes:
                nodes.append({
                    "id": n.params.get("id", str(id(n))),
                    "title": n.title,
                    "type": n.node_type,
                    "params": n.params
                })
            edges = []
            for e in self.node_graph.scene.edges:
                 src_node = e.source_socket.parent_node
                 tgt_node = e.target_socket.parent_node
                 src = src_node.params.get("id", str(id(src_node)))
                 tgt = tgt_node.params.get("id", str(id(tgt_node)))
                 edges.append({"source": src, "target": tgt})

            context = {"query": text, "nodes": nodes, "edges": edges}
            result = AIPluginRegistry.execute_plugin("AI Interaction Assistant", context)
            
            if result and result.get("status") == "success":
                # Highlight logic
                target_ids = result.get("highlight_ids", [])
                
                # Convert back to titles if needed or iterate nodes to find match
                # Since we don't have a direct ID map in GUI easily without rebuilding map:
                titles_to_select = []
                for n in self.node_graph.scene.nodes:
                    nid = n.params.get("id", str(id(n)))
                    if nid in target_ids:
                        n.setSelected(True)
                        titles_to_select.append(n.title)
                    else:
                        n.setSelected(False)
                        n.setOpacity(0.2) # Dim others
                
                # Center on first match
                for n in self.node_graph.scene.nodes:
                    if n.isSelected():
                        self.node_graph.centerOn(n)
                        n.setOpacity(1.0)
                        break
                        
                msg = result.get("message")
                logger.info(msg)
                if hasattr(self, 'ai_log'):
                    self.ai_log.append(f"<b>AI Search:</b> {msg}")

    def run_ai_risk_check(self):
        from PyQt6.QtWidgets import QMessageBox
        # Prepare Context
        nodes = []
        for n in self.node_graph.scene.nodes:
            nodes.append({
                "id": n.params.get("id", str(id(n))),
                "title": n.title
            })
        edges = []
        for e in self.node_graph.scene.edges:
             src_node = e.source_socket.parent_node
             tgt_node = e.target_socket.parent_node
             src = src_node.params.get("id", str(id(src_node)))
             tgt = tgt_node.params.get("id", str(id(tgt_node)))
             edges.append({"source": src, "target": tgt})
             
        context = {"nodes": nodes, "edges": edges}
        result = AIPluginRegistry.execute_plugin("AI Risk Governor", context)
        
        if result and result.get("status") == "success":
            risks = result.get("risks", [])
            suggestions = result.get("suggestions", [])
            
            msg = f"Found {len(risks)} Risks:\n\n"
            for r in risks[:5]:
                msg += f"[{r['level']}] {r['type']}: {r['description']}\n"
            
            if suggestions:
                msg += "\nSuggestions:\n"
                for s in suggestions[:3]:
                    msg += f"- {s}\n"
            
            QMessageBox.information(self, "AI Risk Governance", msg)
            if hasattr(self, 'ai_log'):
                self.ai_log.append(f"<b>AI Risk Check:</b><br><pre>{msg}</pre>")

    def run_ai_node_generation(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QTextEdit
        
        # Simple Dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Node Generator")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        name_edit = QLineEdit()
        inputs_edit = QLineEdit("image, threshold")
        outputs_edit = QLineEdit("edges")
        desc_edit = QLineEdit("Detects edges using Canny algorithm")
        
        form.addRow("Node Name:", name_edit)
        form.addRow("Inputs (comma sep):", inputs_edit)
        form.addRow("Outputs (comma sep):", outputs_edit)
        form.addRow("Description:", desc_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            # Run Plugin
            context = {
                "name": name_edit.text(),
                "inputs": [x.strip() for x in inputs_edit.text().split(",") if x.strip()],
                "outputs": [x.strip() for x in outputs_edit.text().split(",") if x.strip()],
                "description": desc_edit.text()
            }
            
            result = AIPluginRegistry.execute_plugin("Smart Node Generator", context)
            
            if result and result.get("status") == "success":
                code = result.get("code")
                
                # Show Code
                code_dialog = QDialog(self)
                code_dialog.setWindowTitle("Generated Node Code")
                code_dialog.resize(600, 400)
                vbox = QVBoxLayout(code_dialog)
                text_view = QTextEdit()
                text_view.setPlainText(code)
                vbox.addWidget(text_view)
                code_dialog.exec()


def main():
    app = QApplication(sys.argv)
    AppTheme.apply_dark_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
