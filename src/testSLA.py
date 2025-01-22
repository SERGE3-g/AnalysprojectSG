import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import logging


class ModernSLAAnalyzer(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # Configure logging
        self.setup_logging()

        # Initialize variables
        self.initialize_variables()

        # Setup styles
        self.setup_styles()

        # Create GUI elements
        self.create_gui()

        # Layout elements
        self.setup_layout()

    def setup_logging(self):
        """Configure logging with custom formatting"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger('SLAAnalyzer')

    def initialize_variables(self):
        """Initialize all variables and configurations"""
        # SLA configurations
        self.sla_config = {
            'SLA2': {'threshold': 1400, 'description': 'Response Time'},
            'SLA3': {'threshold': 600, 'description': 'Processing Time'},
            'SLA4': {'threshold': 800, 'description': 'Network Latency'},
            'SLA5': {'threshold': 600, 'description': 'Database Access'},
            'SLA6': {'threshold': 800, 'description': 'API Response'}
        }

        # File tracking
        self.files = {
            'SLA1_IN': {'path': None, 'status': 'pending'},
            'SLA4_IN': {'path': None, 'status': 'pending'},
            'SLA5_IN': {'path': None, 'status': 'pending'},
            'SLA6_IN': {'path': None, 'status': 'pending'},
            'SLA1_OUT': {'path': None, 'status': 'pending'},
            'SLA2_OUT': {'path': None, 'status': 'pending'},
            'SLA3_OUT': {'path': None, 'status': 'pending'}
        }

        # Data storage
        self.analysis_results = {}

        # Current period
        self.current_month = datetime.now().strftime("%B")
        self.current_year = str(datetime.now().year)

    def setup_styles(self):
        """Configure custom styles for the GUI"""
        style = ttk.Style()

        # Configure main theme
        style.configure("Modern.TFrame", background="#ffffff")
        style.configure("Modern.TLabel", background="#ffffff", font=('Segoe UI', 10))
        style.configure("Header.TLabel", font=('Segoe UI', 12, 'bold'))

        # Configure custom button styles
        style.configure(
            "Action.TButton",
            padding=10,
            font=('Segoe UI', 10),
            background="#007bff"
        )

        # Configure treeview
        style.configure(
            "Modern.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            font=('Segoe UI', 9)
        )

        # Configure progress bar
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor="#f0f0f0",
            background="#28a745"
        )

    def create_gui(self):
        """Create all GUI elements"""
        self.create_header()
        self.create_toolbar()
        self.create_file_section()
        self.create_notebook()
        self.create_status_bar()

    def create_header(self):
        """Create header section with title and period selection"""
        self.header_frame = ttk.Frame(self, style="Modern.TFrame")

        # Title
        title_label = ttk.Label(
            self.header_frame,
            text="SLA Analysis Dashboard",
            style="Header.TLabel"
        )

        # Period selection
        self.period_frame = ttk.LabelFrame(
            self.header_frame,
            text="Analysis Period",
            padding=10
        )

        # Month combobox
        months = [datetime.strptime(str(i), "%m").strftime("%B") for i in range(1, 13)]
        self.month_var = tk.StringVar(value=self.current_month)
        self.month_combo = ttk.Combobox(
            self.period_frame,
            textvariable=self.month_var,
            values=months,
            width=15,
            state="readonly"
        )

        # Year entry
        self.year_var = tk.StringVar(value=self.current_year)
        self.year_entry = ttk.Entry(
            self.period_frame,
            textvariable=self.year_var,
            width=6
        )

        # Layout header elements
        title_label.pack(side="left", padx=10, pady=10)
        self.period_frame.pack(side="right", padx=10, pady=5)
        ttk.Label(self.period_frame, text="Month:").pack(side="left")
        self.month_combo.pack(side="left", padx=5)
        ttk.Label(self.period_frame, text="Year:").pack(side="left", padx=5)
        self.year_entry.pack(side="left")

    def create_toolbar(self):
        """Create toolbar with main action buttons"""
        self.toolbar = ttk.Frame(self, style="Modern.TFrame")

        # Create main action buttons
        self.buttons = {
            'generate': ttk.Button(
                self.toolbar,
                text="Generate Report",
                style="Action.TButton",
                command=self.generate_report
            ),
            'preview': ttk.Button(
                self.toolbar,
                text="Preview Data",
                command=self.show_preview
            ),
            'export': ttk.Button(
                self.toolbar,
                text="Export Data",
                command=self.export_data
            ),
            'settings': ttk.Button(
                self.toolbar,
                text="Settings",
                command=self.show_settings
            )
        }

        # Layout buttons
        for button in self.buttons.values():
            button.pack(side="left", padx=5, pady=5)

    def create_file_section(self):
        """Create file selection section"""
        self.files_frame = ttk.LabelFrame(
            self,
            text="Input Files",
            padding=10
        )

        # Create file selection widgets
        self.file_widgets = {}
        for file_key in self.files.keys():
            frame = ttk.Frame(self.files_frame)

            label = ttk.Label(frame, text=f"{file_key}:", width=10)
            status = ttk.Label(frame, text="Not selected", width=30)
            button = ttk.Button(
                frame,
                text="Select File",
                command=lambda k=file_key: self.select_file(k)
            )

            # Store widgets for later access
            self.file_widgets[file_key] = {
                'frame': frame,
                'label': label,
                'status': status,
                'button': button
            }

            # Layout file widgets
            label.pack(side="left", padx=5)
            status.pack(side="left", padx=5)
            button.pack(side="left", padx=5)
            frame.pack(fill="x", pady=2)

    def create_notebook(self):
        """Create notebook with different views"""
        self.notebook = ttk.Notebook(self)

        # Create tabs
        self.tabs = {
            'preview': self.create_preview_tab(),
            'graph': self.create_graph_tab(),
            'log': self.create_log_tab()
        }

        # Add tabs to notebook
        self.notebook.add(self.tabs['preview'], text="Data Preview")
        self.notebook.add(self.tabs['graph'], text="Graphs")
        self.notebook.add(self.tabs['log'], text="Log")

    def create_preview_tab(self):
        """Create data preview tab"""
        frame = ttk.Frame(self.notebook)

        # Create treeview for data preview
        self.preview_tree = ttk.Treeview(
            frame,
            style="Modern.Treeview",
            selectmode="extended"
        )

        # Add scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.preview_tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout preview elements
        self.preview_tree.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        return frame

    def create_graph_tab(self):
        """Create graphs tab"""
        frame = ttk.Frame(self.notebook)

        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    def create_log_tab(self):
        """Create log tab"""
        frame = ttk.Frame(self.notebook)

        # Create text widget for log
        self.log_text = tk.Text(
            frame,
            wrap=tk.WORD,
            height=10,
            font=('Consolas', 9)
        )

        # Add scrollbar
        log_scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scroll.set)

        # Configure tags for different message types
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")

        # Layout log elements
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        return frame

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self, style="Modern.TFrame")

        # Status label
        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            style="Modern.TLabel"
        )
        self.status_label.pack(side="left", padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.status_bar,
            style="Modern.Horizontal.TProgressbar",
            length=200,
            mode='determinate'
        )
        self.progress.pack(side="right", padx=5)

    def setup_layout(self):
        """Layout all main sections"""
        # Pack main sections
        self.header_frame.pack(fill="x", padx=10, pady=5)
        self.toolbar.pack(fill="x", padx=10, pady=5)
        self.files_frame.pack(fill="x", padx=10, pady=5)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.status_bar.pack(fill="x", side="bottom", padx=10, pady=5)

    def select_file(self, file_key):
        """Handle file selection"""
        filename = filedialog.askopenfilename(
            title=f"Select {file_key} file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            self.files[file_key]['path'] = filename
            self.files[file_key]['status'] = 'loaded'

            # Update status label
            self.file_widgets[file_key]['status'].configure(
                text=Path(filename).name
            )

            # Log success
            self.log_message(f"Loaded {file_key}: {Path(filename).name}", "success")

            # Update progress
            self.update_progress()

    def log_message(self, message, level="info"):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert("end", f"{timestamp}: {message}\n", level)
        self.log_text.see("end")

        # Also log to Python logger
        self.logger.info(message)

    def update_progress(self):
        """Update progress bar based on loaded files"""
        loaded_files = sum(1 for f in self.files.values() if f['status'] == 'loaded')
        progress = (loaded_files / len(self.files)) * 100
        self.progress['value'] = progress

        # Update status label
        self.status_label.configure(
            text=f"Loaded {loaded_files} of {len(self.files)} files"
        )

    def generate_report(self):
        """Generate SLA analysis report"""
        if not all(f['status'] == 'loaded' for f in self.files.values()):
            messagebox.showwarning(
                "Missing Files",
                "Please load all required files before generating the report."
            )
            return

        try:
            # Implementation of report generation logic
            self.log_message("Generating report...", "info")
            # ... report generation code ...
            self.log_message("Report generated successfully", "success")

        except Exception as e:
            self.log_message(f"Error generating report: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def show_preview(self):
        """Show data preview in treeview"""
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        # Find first loaded file for preview
        for file_key, file_info in self.files.items():
            if file_info['status'] == 'loaded':
                try:
                    df = pd.read_csv(file_info['path'], sep=';', nrows=100)

                    # Configure columns
                    self.preview_tree['columns'] = list(df.columns