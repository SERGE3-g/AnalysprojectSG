import json
import csv
import datetime
import re
from venv import logger

import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


@dataclass
class TestTimes:
    start_time: str
    end_time: str
    elapsed_time: float

@dataclass
class TestResult:
    name: str
    status: str
    message: str
    times: TestTimes
    tags: List[str]
    doc: str
    is_critical: bool

@dataclass
class SuiteResult:
    name: str
    doc: str
    status: str
    message: str
    start_time: str
    end_time: str
    elapsed_time: float
    tests: List[TestResult]
    total_tests: int
    passed_tests: int
    failed_tests: int
    metadata: Dict[str, str]


class ResultsAnalyzer:
    """Classe per analizzare i risultati dei test"""

    def __init__(self, suite_results: SuiteResult):
        self.suite_results = suite_results
        self.test_df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """Converte i risultati dei test in un DataFrame pandas"""
        data = []
        for test in self.suite_results.tests:
            data.append({
                'name': test.name,
                'status': test.status,
                'duration': test.times.elapsed_time,
                'tags': ','.join(test.tags),
                'is_critical': test.is_critical,
                'message': test.message,
                'start_time': test.times.start_time,
                'end_time': test.times.end_time
            })
        return pd.DataFrame(data)

    def get_slowest_tests(self, n: int = 5) -> pd.DataFrame:
        """Ottiene i test più lenti"""
        return self.test_df.nlargest(n, 'duration')

    def get_critical_test_stats(self) -> Dict:
        """Calcola le statistiche dei test critici"""
        critical_tests = self.test_df[self.test_df['is_critical']]
        return {
            'total': len(critical_tests),
            'passed': len(critical_tests[critical_tests['status'] == 'PASS']),
            'failed': len(critical_tests[critical_tests['status'] == 'FAIL']),
            'avg_duration': critical_tests['duration'].mean()
        }

    def get_tag_stats(self) -> Dict:
        """Calcola le statistiche per tag"""
        tag_stats = {}
        for test in self.suite_results.tests:
            for tag in test.tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {'total': 0, 'passed': 0, 'failed': 0}
                tag_stats[tag]['total'] += 1
                if test.status == 'PASS':
                    tag_stats[tag]['passed'] += 1
                else:
                    tag_stats[tag]['failed'] += 1
        return tag_stats


class TestAnalyzerGUI:
    """Classe per l'interfaccia grafica dell'analizzatore di report"""
    def __init__(self, root):
        self.root = root
        self.root.title("Test Report Analyzer Pro")
        self.root.geometry("1200x800")

        # Variabili
        self.current_results = None
        self.analyzer = None
        self.output_dir = Path("report_output")

        # Setup GUI
        self.create_notebook()
        self.create_menu()

        # Configurazione griglia
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def create_menu(self):
        """Crea la barra dei menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Report...", command=self.browse_file)
        file_menu.add_command(label="Export Results...", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Menu View
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Open Output Folder", command=self.open_output_folder)

    def create_notebook(self):
        """Crea il notebook con le schede"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Crea le schede
        self.create_analyzer_tab()
        self.create_filters_tab()
        self.create_visualization_tab()
        self.create_statistics_tab()

    def create_analyzer_tab(self):
        """Crea la scheda principale dell'analizzatore"""
        analyzer_frame = ttk.Frame(self.notebook)
        self.notebook.add(analyzer_frame, text='Analyzer')

        # File Selection Frame
        file_frame = ttk.LabelFrame(analyzer_frame, text="File Selection", padding="5")
        file_frame.pack(fill='x', padx=5, pady=5)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=80)
        file_entry.pack(side='left', padx=5)

        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side='left', padx=5)

        # Control Buttons
        control_frame = ttk.Frame(analyzer_frame)
        control_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(control_frame, text="Analyze Tests", command=self.analyze_tests).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export Results", command=self.export_results).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Clear Results", command=self.clear_results).pack(side='left', padx=5)

        # Results Frame
        results_frame = ttk.LabelFrame(analyzer_frame, text="Analysis Results")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=20)
        self.results_text.pack(fill='both', expand=True)

    def create_filters_tab(self):
        """Crea la scheda dei filtri"""
        filters_frame = ttk.Frame(self.notebook)
        self.notebook.add(filters_frame, text='Filters')

        # Filter Controls
        control_frame = ttk.LabelFrame(filters_frame, text="Filter Controls", padding="5")
        control_frame.pack(fill='x', padx=5, pady=5)

        # Status Filter
        ttk.Label(control_frame, text="Status:").grid(row=0, column=0, padx=5)
        self.status_var = tk.StringVar(value="all")
        ttk.Radiobutton(control_frame, text="All", variable=self.status_var,
                        value="all").grid(row=0, column=1)
        ttk.Radiobutton(control_frame, text="Passed", variable=self.status_var,
                        value="pass").grid(row=0, column=2)
        ttk.Radiobutton(control_frame, text="Failed", variable=self.status_var,
                        value="fail").grid(row=0, column=3)

        # Duration Filter
        ttk.Label(control_frame, text="Duration:").grid(row=1, column=0, padx=5)
        self.duration_var = tk.StringVar(value="all")
        ttk.Radiobutton(control_frame, text="All", variable=self.duration_var,
                        value="all").grid(row=1, column=1)
        ttk.Radiobutton(control_frame, text=">10s", variable=self.duration_var,
                        value=">10").grid(row=1, column=2)
        ttk.Radiobutton(control_frame, text=">30s", variable=self.duration_var,
                        value=">30").grid(row=1, column=3)

        # Tag Filter
        ttk.Label(control_frame, text="Tags:").grid(row=2, column=0, padx=5)
        self.tag_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.tag_var).grid(row=2, column=1,
                                                                 columnspan=2, sticky='ew')

        ttk.Button(control_frame, text="Apply Filters",
                   command=self.apply_filters).grid(row=2, column=3)

        # Filtered Results
        results_frame = ttk.LabelFrame(filters_frame, text="Filtered Results")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Treeview for filtered results
        self.filtered_tree = ttk.Treeview(results_frame,
                                          columns=('name', 'status', 'duration', 'tags'),
                                          show='headings')
        self.filtered_tree.heading('name', text='Test Name')
        self.filtered_tree.heading('status', text='Status')
        self.filtered_tree.heading('duration', text='Duration')
        self.filtered_tree.heading('tags', text='Tags')

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical',
                                  command=self.filtered_tree.yview)
        self.filtered_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.filtered_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_visualization_tab(self):
        """Crea la scheda delle visualizzazioni"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text='Visualizations')

        # Control Frame
        control_frame = ttk.LabelFrame(viz_frame, text="Visualization Controls")
        control_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(control_frame, text="Duration Histogram",
                   command=lambda: self.show_plot('histogram')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Status Pie Chart",
                   command=lambda: self.show_plot('pie')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Timeline",
                   command=lambda: self.show_plot('timeline')).pack(side='left', padx=5)

        # Plot Frame
        self.plot_frame = ttk.LabelFrame(viz_frame, text="Plot")
        self.plot_frame.pack(fill='both', expand=True, padx=5, pady=5)

    def create_statistics_tab(self):
        """Crea la scheda delle statistiche"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text='Statistics')

        # Summary Stats
        summary_frame = ttk.LabelFrame(stats_frame, text="Summary Statistics")
        summary_frame.pack(fill='x', padx=5, pady=5)

        self.stats_text = scrolledtext.ScrolledText(summary_frame, height=10)
        self.stats_text.pack(fill='both', expand=True)

        # Detailed Stats
        details_frame = ttk.LabelFrame(stats_frame, text="Detailed Statistics")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.stats_tree = ttk.Treeview(details_frame, columns=('metric', 'value'),
                                       show='headings')
        self.stats_tree.heading('metric', text='Metric')
        self.stats_tree.heading('value', text='Value')

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(details_frame, orient='vertical',
                                  command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.stats_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def browse_file(self):
        """Apri il dialogo di selezione file"""
        try:
            filename = filedialog.askopenfilename(
                title="Select File",
                filetypes=[
                    ("All Supported Files", "*.xml;*.json;*.txt;*.log"),
                    ("XML files", "*.xml"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("Log files", "*.log"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.file_path_var.set(filename)
        except Exception as e:
            messagebox.showerror("File Error", f"Error selecting file: {str(e)}")

    def analyze_tests(self):
        """Analizza il file selezionato"""
        try:
            filename = self.file_path_var.get()
            if not filename:
                messagebox.showwarning("No File", "Please select a file first.")
                return

            if not os.path.exists(filename):
                messagebox.showerror("File Error", "The selected file does not exist.")
                return

            file_extension = os.path.splitext(filename)[1].lower()

            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()
                    logger.info(f"File content preview: {content[:200]}")

                    if not content.strip():
                        messagebox.showerror("File Error", "The file is empty")
                        return

                    # Analizza il file in base all'estensione
                    if file_extension == '.xml':
                        self._analyze_xml(content)
                    elif file_extension == '.json':
                        self._analyze_json(content)
                    elif file_extension in ['.txt', '.log']:
                        self._analyze_text(content)
                    else:
                        # Prova a determinare il tipo di file dal contenuto
                        if content.strip().startswith('<?xml'):
                            self._analyze_xml(content)
                        elif content.strip().startswith('{') or content.strip().startswith('['):
                            self._analyze_json(content)
                        else:
                            self._analyze_text(content)

            except Exception as e:
                logger.error(f"Analysis error: {str(e)}", exc_info=True)
                messagebox.showerror("Analysis Error",
                                     f"Error analyzing file: {str(e)}\n\n"
                                     f"Please check the log file for more details.")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def _analyze_xml(self, content):
        """Analizza il contenuto XML"""
        tree = ET.fromstring(content)

        # Estrai informazioni della suite
        suite = tree.find('suite')
        if suite is None:
            # Crea una suite virtuale se non esiste
            tests = self._extract_generic_tests(tree)
        else:
            tests = self._extract_robot_tests(suite)

        self._create_suite_result(tests)
        self.update_results_display()
        self.update_statistics()

    def _analyze_json(self, content):
        """Analizza il contenuto JSON"""
        data = json.loads(content)

        # Gestisci sia array che oggetti JSON
        if isinstance(data, list):
            tests = self._extract_json_array_tests(data)
        else:
            tests = self._extract_json_object_tests(data)

        self._create_suite_result(tests)
        self.update_results_display()
        self.update_statistics()

    def _analyze_text(self, content):
        """Analizza il contenuto testuale"""
        lines = content.split('\n')
        tests = self._extract_text_tests(lines)

        self._create_suite_result(tests)
        self.update_results_display()
        self.update_statistics()

    def _create_suite_result(self, tests):
        """Crea un oggetto SuiteResult dai test analizzati"""
        passed_count = sum(1 for test in tests if test.status == 'PASS')
        failed_count = len(tests) - passed_count

        self.current_results = SuiteResult(
            name="Test Suite",
            doc="Automatically analyzed test results",
            status="PASS" if failed_count == 0 else "FAIL",
            message="",
            start_time="",
            end_time="",
            elapsed_time=sum(test.times.elapsed_time for test in tests),
            tests=tests,
            total_tests=len(tests),
            passed_tests=passed_count,
            failed_tests=failed_count,
            metadata={}
        )

    def _extract_generic_tests(self, element):
        """Estrae test da qualsiasi elemento XML"""
        tests = []

        # Cerca elementi che potrebbero essere test
        for child in element.iter():
            if any(key in child.attrib for key in ['test', 'name', 'status']):
                test_result = self._create_test_result_from_element(child)
                if test_result:
                    tests.append(test_result)

        return tests

    def _extract_json_array_tests(self, data):
        """Estrae test da un array JSON"""
        tests = []

        for item in data:
            if isinstance(item, dict):
                test_result = self._create_test_result_from_dict(item)
                if test_result:
                    tests.append(test_result)

        return tests

    def _extract_json_object_tests(self, data):
        """Estrae test da un oggetto JSON"""
        tests = []

        # Cerca oggetti che potrebbero essere test
        for key, value in data.items():
            if isinstance(value, dict):
                test_result = self._create_test_result_from_dict(value)
                if test_result:
                    tests.append(test_result)

        return tests

    def _extract_text_tests(self, lines):
        """Estrae test da linee di testo"""
        tests = []
        current_test = {}

        for line in lines:
            # Cerca pattern comuni nei log di test
            if 'test' in line.lower() or 'pass' in line.lower() or 'fail' in line.lower():
                if current_test and 'name' in current_test:
                    test_result = self._create_test_result_from_dict(current_test)
                    if test_result:
                        tests.append(test_result)
                    current_test = {}

                # Estrai informazioni dalla linea
                current_test = self._parse_test_line(line)

        # Aggiungi l'ultimo test se presente
        if current_test and 'name' in current_test:
            test_result = self._create_test_result_from_dict(current_test)
            if test_result:
                tests.append(test_result)

        return tests

    def _create_test_result_from_dict(self, data):
        """Crea un oggetto TestResult da un dizionario"""
        try:
            # Estrai i campi necessari con valori di default
            name = data.get('name', data.get('test_name', 'Unknown Test'))
            status = data.get('status', data.get('result', 'UNKNOWN')).upper()
            # Standardizza lo status
            status = 'PASS' if status in ['PASS', 'SUCCESS', 'OK'] else 'FAIL'

            # Gestisci i tempi
            times = TestTimes(
                start_time=data.get('start_time', ''),
                end_time=data.get('end_time', ''),
                elapsed_time=float(data.get('duration', data.get('elapsed_time', 0)))
            )

            # Gestisci i tag
            tags = data.get('tags', [])
            if isinstance(tags, str):
                tags = tags.split(',')

            return TestResult(
                name=name,
                status=status,
                message=str(data.get('message', '')),
                times=times,
                tags=tags,
                doc=str(data.get('doc', '')),
                is_critical=bool(data.get('critical', False))
            )
        except Exception as e:
            logger.warning(f"Error creating test result: {str(e)}")
            return None

    def _parse_test_line(self, line):
        """Analizza una linea di testo per estrarre informazioni del test"""
        test_info = {}

        # Cerca pattern comuni
        if ':' in line:
            parts = line.split(':')
            test_info['name'] = parts[0].strip()
            test_info['message'] = ':'.join(parts[1:]).strip()
        else:
            test_info['name'] = line.strip()

        # Determina lo status
        status_keywords = {
            'pass': ['pass', 'success', 'ok'],
            'fail': ['fail', 'error', 'failed']
        }

        line_lower = line.lower()
        for status, keywords in status_keywords.items():
            if any(keyword in line_lower for keyword in keywords):
                test_info['status'] = status.upper()
                break

        return test_info

    def export_plots(self, export_dir):
        """Esporta i grafici come immagini"""
        try:
            plots_dir = export_dir / 'plots'
            plots_dir.mkdir(exist_ok=True)

            # Histogram
            plt.figure(figsize=(10, 6))
            durations = [test.times.elapsed_time for test in self.current_results.tests]
            plt.hist(durations, bins=20)
            plt.title('Test Duration Distribution')
            plt.xlabel('Duration (seconds)')
            plt.ylabel('Number of Tests')
            plt.savefig(plots_dir / 'duration_histogram.png')
            plt.close()

            # Pie Chart
            plt.figure(figsize=(8, 8))
            status_counts = {}
            for test in self.current_results.tests:
                status_counts[test.status] = status_counts.get(test.status, 0) + 1
            plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
            plt.title('Test Status Distribution')
            plt.savefig(plots_dir / 'status_pie.png')
            plt.close()

            # Timeline
            plt.figure(figsize=(12, 6))
            tests = sorted(self.current_results.tests,
                           key=lambda x: datetime.datetime.strptime(x.times.start_time,
                                                                    "%Y%m%d %H:%M:%S.%f"))
            y_pos = range(len(tests))
            start_times = [(datetime.datetime.strptime(test.times.start_time, "%Y%m%d %H:%M:%S.%f") -
                            datetime.datetime.strptime(tests[0].times.start_time, "%Y%m%d %H:%M:%S.%f")).total_seconds()
                           for test in tests]
            durations = [test.times.elapsed_time for test in tests]
            colors = ['green' if test.status == 'PASS' else 'red' for test in tests]

            plt.barh(y_pos, durations, left=start_times, color=colors)
            plt.yticks(y_pos, [test.name for test in tests])
            plt.xlabel('Time (seconds)')
            plt.title('Test Execution Timeline')
            plt.tight_layout()
            plt.savefig(plots_dir / 'timeline.png', bbox_inches='tight')
            plt.close()

        except Exception as e:
            raise Exception(f"Error exporting plots: {str(e)}")

    def show_about(self):
        """Mostra informazioni sull'applicazione"""
        about_text = """
        Test Report Analyzer Pro
        Version 1.0

        Un'applicazione per analizzare e visualizzare 
        risultati di test automatici.

        Funzionalità:
        - Supporto per file XML, JSON, TXT, LOG
        - Analisi dettagliata dei risultati
        - Visualizzazione grafici
        - Filtri personalizzabili
        - Esportazione in vari formati

        Sviluppato con Python e Tkinter
        """

        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.resizable(False, False)

        # Centra la finestra
        about_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50))

        # Aggiungi il testo
        text = scrolledtext.ScrolledText(about_window, wrap=tk.WORD, padx=10, pady=10)
        text.insert('1.0', about_text)
        text.configure(state='disabled')
        text.pack(fill='both', expand=True)

        # Pulsante di chiusura
        ttk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)

    def create_menu(self):
        """Crea la barra dei menu completa"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Report...", command=self.browse_file)
        file_menu.add_command(label="Export Results...", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Menu View
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Open Output Folder", command=self.open_output_folder)

        # Menu Tools
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clear Results", command=self.clear_results)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self.show_settings)

        # Menu Help
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)

    def show_settings(self):
        """Mostra la finestra delle impostazioni"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")

        # Crea un notebook per le impostazioni
        settings_notebook = ttk.Notebook(settings_window)
        settings_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab General
        general_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(general_frame, text='General')

        # Output Directory
        ttk.Label(general_frame, text="Output Directory:").pack(anchor='w', padx=5, pady=5)
        output_frame = ttk.Frame(general_frame)
        output_frame.pack(fill='x', padx=5)

        output_entry = ttk.Entry(output_frame)
        output_entry.pack(side='left', fill='x', expand=True)
        output_entry.insert(0, str(self.output_dir))

        ttk.Button(output_frame, text="Browse",
                   command=lambda: self._browse_output_dir(output_entry)).pack(side='left', padx=5)

        # Auto-save results
        autosave_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(general_frame, text="Auto-save results",
                        variable=autosave_var).pack(anchor='w', padx=5, pady=5)

        # Tab Display
        display_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(display_frame, text='Display')

        # Theme selection
        ttk.Label(display_frame, text="Theme:").pack(anchor='w', padx=5, pady=5)
        theme_var = tk.StringVar(value='default')
        themes = ['default', 'light', 'dark']
        theme_combo = ttk.Combobox(display_frame, values=themes,
                                   textvariable=theme_var, state='readonly')
        theme_combo.pack(anchor='w', padx=5)

        # Font size
        ttk.Label(display_frame, text="Font Size:").pack(anchor='w', padx=5, pady=5)
        font_size_var = tk.StringVar(value='12')
        font_sizes = ['10', '12', '14', '16']
        font_combo = ttk.Combobox(display_frame, values=font_sizes,
                                  textvariable=font_size_var, state='readonly')
        font_combo.pack(anchor='w', padx=5)

        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill='x', padx=5, pady=10)

        ttk.Button(button_frame, text="Save",
                   command=lambda: self._save_settings(settings_window)).pack(side='right', padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=settings_window.destroy).pack(side='right', padx=5)

    def show_documentation(self):
        """Mostra la documentazione dell'applicazione"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")

        # Crea un notebook per la documentazione
        doc_notebook = ttk.Notebook(doc_window)
        doc_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab Getting Started
        start_frame = ttk.Frame(doc_notebook)
        doc_notebook.add(start_frame, text='Getting Started')

        start_text = scrolledtext.ScrolledText(start_frame, wrap=tk.WORD)
        start_text.pack(fill='both', expand=True, padx=5, pady=5)
        start_text.insert('1.0', """
        Getting Started with Test Report Analyzer Pro

        1. Opening Test Reports
           - Click 'File > Open Report' or use the Browse button
           - Select your test report file (XML, JSON, TXT, or LOG)
           - Click 'Analyze Tests' to process the file

        2. Viewing Results
           - The main tab shows a summary of all test results
           - Use the Filters tab to search specific tests
           - The Visualizations tab provides graphical views
           - Statistics tab shows detailed metrics

        3. Exporting Results
           - Click 'File > Export Results' to save
           - Choose from multiple export formats
           - Find exported files in the output directory
        """)
        start_text.configure(state='disabled')

        # Tab Features
        features_frame = ttk.Frame(doc_notebook)
        doc_notebook.add(features_frame, text='Features')

        features_text = scrolledtext.ScrolledText(features_frame, wrap=tk.WORD)
        features_text.pack(fill='both', expand=True, padx=5, pady=5)
        features_text.insert('1.0', """
        Key Features

        1. File Support
           - XML test reports
           - JSON test results
           - Text log files
           - Custom log formats

        2. Analysis Tools
           - Test status tracking
           - Duration analysis
           - Tag-based filtering
           - Critical test identification

        3. Visualizations
           - Duration histogram
           - Status pie chart
           - Execution timeline

        4. Export Options
           - HTML reports
           - CSV data export
           - Statistical summaries
           - Visualization exports
        """)
        features_text.configure(state='disabled')

        # Tab Troubleshooting
        trouble_frame = ttk.Frame(doc_notebook)
        doc_notebook.add(trouble_frame, text='Troubleshooting')

        trouble_text = scrolledtext.ScrolledText(trouble_frame, wrap=tk.WORD)
        trouble_text.pack(fill='both', expand=True, padx=5, pady=5)
        trouble_text.insert('1.0', """
        Troubleshooting Guide

        1. File Loading Issues
           - Verify file format is supported
           - Check file encoding (UTF-8 recommended)
           - Ensure file is not empty or corrupted

        2. Analysis Problems
           - Confirm file structure matches expected format
           - Check log file for detailed error messages
           - Verify all required data fields are present

        3. Export Issues
           - Ensure output directory is writable
           - Check available disk space
           - Close any open export files

        For additional help, check the log file or contact support.
        """)
        trouble_text.configure(state='disabled')

    def _browse_output_dir(self, entry_widget):
        """Seleziona la directory di output"""
        dir_path = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=str(self.output_dir)
        )
        if dir_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, dir_path)

    def _save_settings(self, settings_window):
        """Salva le impostazioni e chiude la finestra"""
        # Qui implementare il salvataggio delle impostazioni
        messagebox.showinfo("Settings", "Settings saved successfully!")
        settings_window.destroy()

    def update_results_display(self):
        """Aggiorna la visualizzazione dei risultati"""
        if not self.current_results:
            return

        # Aggiorna il testo dei risultati
        self.results_text.delete('1.0', tk.END)

        # Intestazione
        self.results_text.insert(tk.END, f"Test Suite: {self.current_results.name}\n")
        self.results_text.insert(tk.END, f"{'=' * 50}\n\n")

        # Sommario
        self.results_text.insert(tk.END, "Summary:\n")
        self.results_text.insert(tk.END, f"Total Tests: {self.current_results.total_tests}\n")
        self.results_text.insert(tk.END, f"Passed: {self.current_results.passed_tests}\n")
        self.results_text.insert(tk.END, f"Failed: {self.current_results.failed_tests}\n")
        self.results_text.insert(tk.END, f"Duration: {self.current_results.elapsed_time:.2f}s\n\n")

        # Dettagli dei test
        self.results_text.insert(tk.END, "Test Details:\n")
        self.results_text.insert(tk.END, f"{'-' * 50}\n")

        for test in self.current_results.tests:
            # Inserisci il nome del test
            self.results_text.insert(tk.END, f"\nTest: {test.name}\n")

            # Inserisci lo status con colore appropriato
            self.results_text.insert(tk.END, "Status: ")
            if test.status == 'PASS':
                self.results_text.insert(tk.END, "PASS\n", 'pass')
            else:
                self.results_text.insert(tk.END, "FAIL\n", 'fail')

            # Configura i tag di colore
            self.results_text.tag_configure('pass', foreground='green')
            self.results_text.tag_configure('fail', foreground='red')

            # Inserisci altri dettagli
            self.results_text.insert(tk.END, f"Duration: {test.times.elapsed_time:.2f}s\n")
            self.results_text.insert(tk.END, f"Tags: {', '.join(test.tags)}\n")
            if test.message:
                self.results_text.insert(tk.END, f"Message: {test.message}\n")

    def apply_filters(self):
        """Applica i filtri selezionati ai risultati dei test"""
        if not self.current_results:
            messagebox.showwarning("No Data", "Please analyze tests first.")
            return

        try:
            # Clear previous view
            for item in self.filtered_tree.get_children():
                self.filtered_tree.delete(item)

            status_filter = self.status_var.get()
            duration_filter = self.duration_var.get()
            tag_filter = self.tag_var.get().lower()

            filtered_tests = [test for test in self.current_results.tests
                              if self._passes_filters(test)]

            # Insert filtered tests
            for test in filtered_tests:
                status_tag = 'pass' if test.status == 'PASS' else 'fail'
                self.filtered_tree.insert('', 'end', values=(
                    test.name,
                    test.status,
                    f"{test.times.elapsed_time:.2f}s",
                    ', '.join(test.tags)
                ), tags=(status_tag,))

            # Configure colors
            self.filtered_tree.tag_configure('pass', foreground='green')
            self.filtered_tree.tag_configure('fail', foreground='red')

            # Show summary
            messagebox.showinfo("Filter Results",
                                f"Showing {len(filtered_tests)} of {len(self.current_results.tests)} tests")

        except Exception as e:
            messagebox.showerror("Filter Error", f"Error applying filters: {str(e)}")
            logger.error(f"Filter error: {str(e)}", exc_info=True)

    def _passes_filters(self, test):
        """Verifica se un test passa tutti i filtri impostati"""
        try:
            # Verifica filtro status
            status_filter = self.status_var.get()
            if status_filter != 'all':
                if status_filter == 'pass' and test.status != 'PASS':
                    return False
                if status_filter == 'fail' and test.status != 'FAIL':
                    return False

            # Verifica filtro durata
            duration_filter = self.duration_var.get()
            if duration_filter != 'all':
                threshold = float(duration_filter.replace('>', ''))
                if test.times.elapsed_time <= threshold:
                    return False

            # Verifica filtro tag
            tag_filter = self.tag_var.get().lower()
            if tag_filter:
                test_tags = [tag.lower() for tag in test.tags]
                if not any(tag_filter in tag for tag in test_tags):
                    return False

            return True
        except Exception as e:
            logger.error(f"Error in filter check: {str(e)}")
            return False

    def show_plot(self, plot_type):
                """Mostra il grafico selezionato"""
                if not self.current_results:
                    messagebox.showwarning("No Data", "Please analyze tests first.")
                    return

                try:
                    # Pulisci il frame del plot
                    for widget in self.plot_frame.winfo_children():
                        widget.destroy()

                    fig = plt.figure(figsize=(10, 6))

                    if plot_type == 'histogram':
                        durations = [test.times.elapsed_time for test in self.current_results.tests]
                        plt.hist(durations, bins=20)
                        plt.title('Test Duration Distribution')
                        plt.xlabel('Duration (seconds)')
                        plt.ylabel('Number of Tests')

                    elif plot_type == 'pie':
                        status_counts = {}
                        for test in self.current_results.tests:
                            status_counts[test.status] = status_counts.get(test.status, 0) + 1
                        plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
                        plt.title('Test Status Distribution')

                    elif plot_type == 'timeline':
                        tests = sorted(self.current_results.tests,
                                       key=lambda x: datetime.datetime.strptime(x.times.start_time,
                                                                                "%Y%m%d %H:%M:%S.%f"))
                        y_pos = range(len(tests))
                        start_times = [(datetime.datetime.strptime(test.times.start_time,
                                                                   "%Y%m%d %H:%M:%S.%f") -
                                        datetime.datetime.strptime(tests[0].times.start_time,
                                                                   "%Y%m%d %H:%M:%S.%f")).total_seconds()
                                       for test in tests]
                        durations = [test.times.elapsed_time for test in tests]
                        colors = ['green' if test.status == 'PASS' else 'red' for test in tests]

                        plt.barh(y_pos, durations, left=start_times, color=colors)
                        plt.yticks(y_pos, [test.name for test in tests])
                        plt.xlabel('Time (seconds)')
                        plt.title('Test Execution Timeline')

                    canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill='both', expand=True)

                except Exception as e:
                    messagebox.showerror("Plot Error", f"Error creating plot: {str(e)}")

    def export_results(self):
                """Esporta i risultati in vari formati"""
                try:
                    if not self.current_results:
                        messagebox.showwarning("No Data", "Please analyze tests first.")
                        return

                    # Crea directory per l'export se non esiste
                    export_dir = self.output_dir / 'exports'
                    export_dir.mkdir(exist_ok=True)

                    # Esporta HTML
                    self.generate_html_report(str(export_dir / 'report.html'))

                    # Esporta CSV
                    self.export_to_csv(export_dir / 'test_results.csv')

                    # Esporta grafici
                    self.export_plots(export_dir)

                    # Esporta statistiche
                    self.export_statistics(export_dir)

                    messagebox.showinfo("Export Complete",
                                        f"Results exported successfully to:\n{export_dir}")

                except Exception as e:
                    messagebox.showerror("Export Error", f"Error during export: {str(e)}")

    def export_to_csv(self, filepath):
                """Esporta i risultati dei test in formato CSV"""
                try:
                    with open(filepath, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Test Name', 'Status', 'Duration', 'Tags', 'Message',
                                         'Start Time', 'End Time'])
                        for test in self.current_results.tests:
                            writer.writerow([
                                test.name,
                                test.status,
                                f"{test.times.elapsed_time:.2f}",
                                ','.join(test.tags),
                                test.message,
                                test.times.start_time,
                                test.times.end_time
                            ])
                except Exception as e:
                    raise Exception(f"Error exporting to CSV: {str(e)}")

    def export_statistics(self, export_dir):
                """Esporta statistiche dettagliate"""
                try:
                    stats_path = export_dir / 'statistics.txt'
                    with open(stats_path, 'w') as f:
                        # Summary Statistics
                        f.write("=== Test Execution Summary ===\n\n")
                        f.write(f"Total Tests: {self.current_results.total_tests}\n")
                        f.write(f"Passed Tests: {self.current_results.passed_tests}\n")
                        f.write(f"Failed Tests: {self.current_results.failed_tests}\n")
                        f.write(f"Total Duration: {self.current_results.elapsed_time:.2f}s\n")
                        f.write(
                            f"Average Duration: {self.current_results.elapsed_time / self.current_results.total_tests:.2f}s\n\n")

                        # Tag Statistics
                        f.write("=== Tag Statistics ===\n\n")
                        tag_stats = {}
                        for test in self.current_results.tests:
                            for tag in test.tags:
                                if tag not in tag_stats:
                                    tag_stats[tag] = {'total': 0, 'passed': 0, 'failed': 0}
                                tag_stats[tag]['total'] += 1
                                if test.status == 'PASS':
                                    tag_stats[tag]['passed'] += 1
                                else:
                                    tag_stats[tag]['failed'] += 1

                        for tag, stats in tag_stats.items():
                            f.write(f"Tag: {tag}\n")
                            f.write(f"  Total: {stats['total']}\n")
                            f.write(f"  Passed: {stats['passed']}\n")
                            f.write(f"  Failed: {stats['failed']}\n")
                            f.write(f"  Pass Rate: {(stats['passed'] / stats['total']) * 100:.1f}%\n\n")

                        # Top 5 Slowest Tests
                        f.write("=== Top 5 Slowest Tests ===\n\n")
                        slowest_tests = sorted(self.current_results.tests,
                                               key=lambda x: x.times.elapsed_time,
                                               reverse=True)[:5]
                        for test in slowest_tests:
                            f.write(f"Test: {test.name}\n")
                            f.write(f"  Duration: {test.times.elapsed_time:.2f}s\n")
                            f.write(f"  Status: {test.status}\n\n")

                except Exception as e:
                    raise Exception(f"Error exporting statistics: {str(e)}")

    def generate_html_report(self, output_file: str):
                """Genera un report HTML formattato"""
                try:
                    html = """
                                <html>
                                <head>
                                    <title>Test Execution Report</title>
                                    <style>
                                        body { font-family: Arial, sans-serif; margin: 20px; }
                                        .pass { color: green; }
                                        .fail { color: red; }
                                        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                                        th { background-color: #f2f2f2; }
                                        tr:nth-child(even) { background-color: #f9f9f9; }
                                        .summary { margin: 20px 0; }
                                        .header { background-color: #4CAF50; color: white; padding: 10px; }
                                    </style>
                                </head>
                                <body>
                                    <div class="header">
                                        <h1>Test Execution Report</h1>
                                    </div>

                                    <div class="summary">
                                        <h2>Summary</h2>
                                        <p>Total Tests: {}</p>
                                        <p class="pass">Passed: {}</p>
                                        <p class="fail">Failed: {}</p>
                                        <p>Duration: {:.2f}s</p>
                                    </div>

                                    <h2>Test Results</h2>
                                    <table>
                                        <tr>
                                            <th>Name</th>
                                            <th>Status</th>
                                            <th>Duration</th>
                                            <th>Tags</th>
                                            <th>Message</th>
                                        </tr>
                                """.format(
                        self.current_results.total_tests,
                        self.current_results.passed_tests,
                        self.current_results.failed_tests,
                        self.current_results.elapsed_time
                    )

                    for test in self.current_results.tests:
                        status_class = 'pass' if test.status == 'PASS' else 'fail'
                        html += """
                                        <tr>
                                            <td>{}</td>
                                            <td class="{}">{}</td>
                                            <td>{:.2f}s</td>
                                            <td>{}</td>
                                            <td>{}</td>
                                        </tr>
                                    """.format(
                            test.name,
                            status_class,
                            test.status,
                            test.times.elapsed_time,
                            ', '.join(test.tags),
                            test.message
                        )

                    html += """
                                    </table>
                                </body>
                                </html>
                                """

                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(html)

                except Exception as e:
                    raise Exception(f"Error generating HTML report: {str(e)}")

    def update_statistics(self):
                """Aggiorna le statistiche visualizzate"""
                if not self.current_results:
                    return

                try:
                    # Aggiorna il sommario statistico
                    summary = f"""Summary Statistics:
                    Total Tests: {self.current_results.total_tests}
                    Passed Tests: {self.current_results.passed_tests}
                    Failed Tests: {self.current_results.failed_tests}
                    Total Duration: {self.current_results.elapsed_time:.2f}s
                    Average Duration: {self.current_results.elapsed_time / self.current_results.total_tests:.2f}s
                    """
                    self.stats_text.delete('1.0', tk.END)
                    self.stats_text.insert('1.0', summary)

                    # Pulisci la vista delle statistiche dettagliate
                    for item in self.stats_tree.get_children():
                        self.stats_tree.delete(item)

                    # Calcola e mostra statistiche dettagliate
                    stats = [
                        ('Pass Rate',
                         f"{(self.current_results.passed_tests / self.current_results.total_tests) * 100:.1f}%"),
                        ('Fail Rate',
                         f"{(self.current_results.failed_tests / self.current_results.total_tests) * 100:.1f}%"),
                        ('Average Duration',
                         f"{self.current_results.elapsed_time / self.current_results.total_tests:.2f}s"),
                        ('Maximum Duration',
                         f"{max(test.times.elapsed_time for test in self.current_results.tests):.2f}s"),
                        ('Minimum Duration',
                         f"{min(test.times.elapsed_time for test in self.current_results.tests):.2f}s"),
                        ('Total Tags', str(len(set(tag for test in self.current_results.tests for tag in test.tags)))),
                        ('Critical Tests', str(sum(1 for test in self.current_results.tests if test.is_critical)))
                    ]

                    for metric, value in stats:
                        self.stats_tree.insert('', 'end', values=(metric, value))

                except Exception as e:
                    messagebox.showerror("Statistics Error", f"Error updating statistics: {str(e)}")

    def clear_results(self):
        """Pulisci tutti i risultati"""
        try:
            self.current_results = None
            self.results_text.delete('1.0', tk.END)
            self.stats_text.delete('1.0', tk.END)

            # Clear trees
            for item in self.filtered_tree.get_children():
                self.filtered_tree.delete(item)
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)

            # Clear plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()

            messagebox.showinfo("Clear", "All results cleared successfully.")

        except Exception as e:
            messagebox.showerror("Clear Error", f"Error clearing results: {str(e)}")

    def open_output_folder(self):
        """Apri la cartella di output nel file explorer"""
        if self.output_dir.exists():
            os.startfile(str(self.output_dir))
        else:
            messagebox.showwarning("Folder Not Found", "Output folder does not exist yet.")

    def _analyze_file_content(self, content, file_extension):
        """Analizza il contenuto del file e restituisce informazioni dettagliate"""
        analysis_info = {
            'format_detected': '',
            'structure_valid': False,
            'errors': [],
            'warnings': [],
            'details': {}
        }

        try:
            # Analisi preliminare del contenuto
            content_preview = content[:200].strip()
            analysis_info['content_preview'] = content_preview

            # Verifica il formato
            if content.strip().startswith('<?xml'):
                analysis_info['format_detected'] = 'XML'
                self._validate_xml_structure(content, analysis_info)
            elif content.strip().startswith('{') or content.strip().startswith('['):
                analysis_info['format_detected'] = 'JSON'
                self._validate_json_structure(content, analysis_info)
            else:
                analysis_info['format_detected'] = 'TEXT'
                self._validate_text_structure(content, analysis_info)

            # Aggiunge statistiche generali
            analysis_info['details']['total_lines'] = len(content.splitlines())
            analysis_info['details']['file_size'] = len(content)

            return analysis_info

        except Exception as e:
            analysis_info['errors'].append(f"Analysis error: {str(e)}")
            return analysis_info

    def _validate_xml_structure(self, content, analysis_info):
        """Valida la struttura XML e aggiunge informazioni dettagliate"""
        try:
            tree = ET.fromstring(content)
            analysis_info['structure_valid'] = True

            # Analizza la struttura
            analysis_info['details']['root_tag'] = tree.tag
            analysis_info['details']['attributes'] = dict(tree.attrib)
            analysis_info['details']['children'] = [child.tag for child in tree]

            # Cerca elementi specifici dei test
            suite = tree.find('suite')
            if suite is None:
                analysis_info['warnings'].append("No 'suite' element found")
            else:
                analysis_info['details']['suite_name'] = suite.get('name', '')
                analysis_info['details']['total_tests'] = len(suite.findall('.//test'))

        except ET.ParseError as e:
            analysis_info['errors'].append(f"XML parsing error: {str(e)}")
            analysis_info['details']['error_line'] = e.position[0]
            analysis_info['details']['error_column'] = e.position[1]

    def _validate_json_structure(self, content, analysis_info):
        """Valida la struttura JSON e aggiunge informazioni dettagliate"""
        try:
            data = json.loads(content)
            analysis_info['structure_valid'] = True

            # Analizza la struttura
            if isinstance(data, list):
                analysis_info['details']['structure_type'] = 'array'
                analysis_info['details']['items_count'] = len(data)
            else:
                analysis_info['details']['structure_type'] = 'object'
                analysis_info['details']['top_level_keys'] = list(data.keys())

            # Cerca informazioni sui test
            self._analyze_json_test_structure(data, analysis_info)

        except json.JSONDecodeError as e:
            analysis_info['errors'].append(f"JSON parsing error: {str(e)}")
            analysis_info['details']['error_line'] = e.lineno
            analysis_info['details']['error_column'] = e.colno

    def _validate_text_structure(self, content, analysis_info):
        """Valida la struttura del testo e cerca pattern di test"""
        lines = content.splitlines()

        # Cerca pattern comuni nei log di test
        test_patterns = {
            'test_start': r'test\s+(?:case|suite|id)?\s*:?\s*(\w+)',
            'status': r'(pass(?:ed)?|fail(?:ed)?)',
            'duration': r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)',
        }

        pattern_matches = {k: 0 for k in test_patterns}

        for line in lines:
            for pattern_name, pattern in test_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    pattern_matches[pattern_name] += 1

        analysis_info['details']['pattern_matches'] = pattern_matches
        analysis_info['structure_valid'] = pattern_matches['test_start'] > 0

    def _create_analysis_report(self, analysis_info):
        """Crea un report dettagliato dell'analisi"""
        report = [
            "=== File Analysis Report ===\n",
            f"Format Detected: {analysis_info['format_detected']}",
            f"Structure Valid: {analysis_info['structure_valid']}\n"
        ]

        if analysis_info['errors']:
            report.append("Errors:")
            for error in analysis_info['errors']:
                report.append(f"- {error}")
            report.append("")

        if analysis_info['warnings']:
            report.append("Warnings:")
            for warning in analysis_info['warnings']:
                report.append(f"- {warning}")
            report.append("")

        report.append("Details:")
        for key, value in analysis_info['details'].items():
            report.append(f"{key}: {value}")

        return "\n".join(report)

    def analyze_tests(self):
        """Analizza il file selezionato con reporting dettagliato"""
        try:
            filename = self.file_path_var.get()
            if not filename:
                messagebox.showwarning("No File", "Please select a file first.")
                return

            if not os.path.exists(filename):
                messagebox.showerror("File Error", "The selected file does not exist.")
                return

            file_extension = os.path.splitext(filename)[1].lower()

            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    content = file.read()

                    # Analizza il contenuto
                    analysis_info = self._analyze_file_content(content, file_extension)

                    # Crea e mostra il report di analisi
                    report = self._create_analysis_report(analysis_info)
                    self.results_text.delete('1.0', tk.END)
                    self.results_text.insert('1.0', report)

                    # Se ci sono errori, ferma l'analisi
                    if analysis_info['errors']:
                        return

                    # Procedi con l'analisi in base al formato
                    if analysis_info['format_detected'] == 'XML':
                        self._analyze_xml(content)
                    elif analysis_info['format_detected'] == 'JSON':
                        self._analyze_json(content)
                    else:
                        self._analyze_text(content)

            except Exception as e:
                logger.error(f"Analysis error: {str(e)}", exc_info=True)
                messagebox.showerror("Analysis Error",
                                     f"Error analyzing file: {str(e)}\n\n"
                                     f"Please check the analysis report for details.")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    # Punto di ingresso principale
if __name__ == "__main__":
        root = tk.Tk()
        app = TestAnalyzerGUI(root)
        root.mainloop()