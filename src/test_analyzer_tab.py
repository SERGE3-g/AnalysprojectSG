import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import json
import datetime
import logging
import os
import sys
import re
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dataclasses import dataclass
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../static/test_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


@dataclass
class ErrorPattern:
    pattern: str  # Pattern regex
    description: str  # Descrizione del pattern
    severity: str  # High/Medium/Low
    suggested_fix: str  # Suggerimento per la risoluzione


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


class ErrorAnalysis:
    """Classe per l'analisi degli errori nei test"""

    def __init__(self):
        # Pattern comuni di errori
        self.error_patterns = [
            ErrorPattern(
                r"AssertionError",
                "Fallimento di un'asserzione nel test",
                "High",
                "Verificare i valori attesi e ottenuti nel test"
            ),
            ErrorPattern(
                r"TimeoutError|timed out",
                "Timeout durante l'esecuzione",
                "High",
                "Aumentare il timeout o ottimizzare l'operazione"
            ),
            ErrorPattern(
                r"ImportError|ModuleNotFoundError",
                "Errore di importazione moduli",
                "High",
                "Verificare le dipendenze e il virtual environment"
            ),
            ErrorPattern(
                r"Connection(?:Error|Refused|TimedOut)",
                "Problemi di connessione",
                "Medium",
                "Verificare la connettività e i servizi dipendenti"
            ),
            ErrorPattern(
                r"Permission(?:Error|Denied)",
                "Errore di permessi",
                "Medium",
                "Verificare i permessi di accesso alle risorse"
            ),
            ErrorPattern(
                r"TypeError|ValueError",
                "Errore di tipo o valore",
                "Medium",
                "Verificare i tipi di dati e le conversioni"
            )
        ]

    def analyze_test_results(self, test_results: List[TestResult]) -> List[dict]:
        """Analizza i risultati dei test per trovare pattern di errori"""
        error_analyses = []

        for test in test_results:
            if test.status == 'FAIL':
                found_patterns = self._identify_error_patterns(test.message)
                if found_patterns:
                    error_analyses.append({
                        'test_name': test.name,
                        'message': test.message,
                        'patterns': found_patterns,
                        'duration': test.times.elapsed_time,
                        'tags': test.tags,
                        'is_critical': test.is_critical
                    })

        return error_analyses

    def _identify_error_patterns(self, message: str) -> List[ErrorPattern]:
        """Identifica i pattern di errore nel messaggio"""
        found_patterns = []
        for pattern in self.error_patterns:
            if re.search(pattern.pattern, message, re.IGNORECASE):
                found_patterns.append(pattern)
        return found_patterns

    def get_error_summary(self, analyses: List[dict]) -> dict:
        """Genera un sommario degli errori trovati"""
        summary = {
            'total_errors': len(analyses),
            'pattern_frequency': {},
            'critical_errors': 0,
            'patterns_by_severity': {
                'High': 0,
                'Medium': 0,
                'Low': 0
            }
        }

        for analysis in analyses:
            if analysis['is_critical']:
                summary['critical_errors'] += 1

            for pattern in analysis['patterns']:
                pattern_name = pattern.description
                summary['pattern_frequency'][pattern_name] = \
                    summary['pattern_frequency'].get(pattern_name, 0) + 1
                summary['patterns_by_severity'][pattern.severity] += 1

        return summary


class TestAnalyzerTab:
    """Tab per l'analisi dei report di test"""

    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Test Analyzer')

        # Variabili
        self.current_results: SuiteResult | None = None
        self.output_dir = Path("report_output")
        self.file_path_var = tk.StringVar()
        self.error_analyzer = ErrorAnalysis()

        # UI
        self.create_gui()

    def create_gui(self):
        """Crea gli elementi dell'interfaccia grafica"""
        # Frame selezione file
        file_frame = ttk.LabelFrame(self.frame, text="Test Report File", padding=5)
        file_frame.pack(fill='x', padx=5, pady=5)

        ttk.Entry(file_frame, textvariable=self.file_path_var).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='left', padx=5)
        ttk.Button(file_frame, text="Analyze", command=self.analyze_file).pack(side='left', padx=5)

        # Notebook dei risultati
        self.results_notebook = ttk.Notebook(self.frame)
        self.results_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Tab Sommario
        self.create_summary_tab()

        # Tab Dettagli
        self.create_details_tab()

        # Tab Visualizzazione
        self.create_visualization_tab()

        # Tab Analisi Errori
        self.add_error_analysis_tab()

    def create_summary_tab(self):
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text='Summary')

        self.summary_text = scrolledtext.ScrolledText(summary_frame)
        self.summary_text.pack(fill='both', expand=True)

    def create_details_tab(self):
        details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(details_frame, text='Details')

        columns = ('name', 'status', 'duration', 'tags')
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show='headings')

        column_configs = {
            'name': 'Test Name',
            'status': 'Status',
            'duration': 'Duration',
            'tags': 'Tags'
        }

        for col, heading in column_configs.items():
            self.details_tree.heading(col, text=heading)
            self.details_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_tree.yview)
        self.details_tree.configure(yscrollcommand=scrollbar.set)

        self.details_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_visualization_tab(self):
        viz_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(viz_frame, text='Visualization')

        # Controlli visualizzazione
        viz_controls = ttk.Frame(viz_frame)
        viz_controls.pack(fill='x')

        ttk.Button(viz_controls, text="Duration Chart",
                   command=lambda: self.show_visualization('duration')).pack(side='left', padx=5)
        ttk.Button(viz_controls, text="Status Chart",
                   command=lambda: self.show_visualization('status')).pack(side='left', padx=5)

        # Container per il grafico
        self.viz_container = ttk.Frame(viz_frame)
        self.viz_container.pack(fill='both', expand=True)

    def add_error_analysis_tab(self):
        """Aggiunge il tab per l'analisi degli errori"""
        error_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(error_frame, text='Error Analysis')

        # Sezione superiore per il sommario degli errori
        summary_frame = ttk.LabelFrame(error_frame, text="Error Summary")
        summary_frame.pack(fill='x', padx=5, pady=5)

        self.error_summary_text = scrolledtext.ScrolledText(summary_frame, height=6)
        self.error_summary_text.pack(fill='x', padx=5, pady=5)

        # Sezione inferiore con TreeView per i dettagli
        details_frame = ttk.LabelFrame(error_frame, text="Error Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        columns = ('test_name', 'error_type', 'severity', 'suggestion')
        self.error_tree = ttk.Treeview(details_frame, columns=columns, show='headings')

        # Configurazione colonne
        column_configs = {
            'test_name': ('Test Name', 200),
            'error_type': ('Error Type', 150),
            'severity': ('Severity', 100),
            'suggestion': ('Suggested Fix', 300)
        }

        for col, (heading, width) in column_configs.items():
            self.error_tree.heading(col, text=heading)
            self.error_tree.column(col, width=width)

        # Scrollbar
        scrollbar = ttk.Scrollbar(details_frame, orient='vertical',
                                  command=self.error_tree.yview)
        self.error_tree.configure(yscrollcommand=scrollbar.set)

        self.error_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Bind del doppio click per i dettagli
        self.error_tree.bind('<Double-1>', self._show_error_details)

    def browse_file(self):
        """Apre il dialogo di selezione file"""
        try:
            filename = filedialog.askopenfilename(
                title="Select Test Report",
                filetypes=[
                    ("All Supported Files", ("*.xml", "*.json", "*.txt")),
                    ("XML files", "*.xml"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.file_path_var.set(filename)
        except Exception as e:
            logging.error(f"FileDialog error: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Error selecting file: {str(e)}")

    def analyze_file(self):
        """Analizza il file selezionato"""
        try:
            filename = self.file_path_var.get()
            if not filename:
                messagebox.showwarning("No File", "Please select a file first.")
                return

            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()

            ext = os.path.splitext(filename)[1].lower()
            if ext == '.xml':
                self._parse_xml(content)
            elif ext == '.json':
                self._parse_json(content)
            else:
                self._parse_text(content)

            self.update_results_display()

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error analyzing file: {str(e)}")
            logging.error(f"Analysis error: {str(e)}", exc_info=True)

    def _parse_xml(self, content):
        try:
            root = ET.fromstring(content)
            tests = []
            for test_elem in root.findall('.//test'):
                test = self._create_test_from_xml(test_elem)
                if test:
                    tests.append(test)
            self._create_suite_result(tests)
        except ET.ParseError as e:
            raise Exception(f"XML parsing error: {str(e)}")

    def _parse_json(self, content):
        try:
            data = json.loads(content)
            tests = []

            if isinstance(data, list):
                for test_data in data:
                    test = self._create_test_from_dict(test_data)
                    if test:
                        tests.append(test)
            elif isinstance(data, dict):
                if 'tests' in data:
                    for test_data in data['tests']:
                        test = self._create_test_from_dict(test_data)
                        if test:
                            tests.append(test)

            self._create_suite_result(tests)
        except json.JSONDecodeError as e:
            raise Exception(f"JSON parsing error: {str(e)}")

    def _parse_text(self, content):
        try:
            lines = content.splitlines()
            tests = []
            current_test = None

            for line in lines:
                if line.strip():
                    if 'test' in line.lower():
                        if current_test:
                            tests.append(current_test)
                        current_test = self._create_test_from_text(line)
                    elif current_test:
                        self._update_test_from_text(current_test, line)

            if current_test:
                tests.append(current_test)

            self._create_suite_result(tests)
        except Exception as e:
            raise Exception(f"Text parsing error: {str(e)}")

    def _create_test_from_xml(self, element):
        try:
            name = element.get('name', 'Unknown Test')
            status = element.get('status', 'UNKNOWN').upper()
            message = element.findtext('msg', '')

            times = TestTimes(
                start_time=element.get('starttime', ''),
                end_time=element.get('endtime', ''),
                elapsed_time=float(element.get('time', '0'))
            )

            tags = [tag.text for tag in element.findall('tag')]

            return TestResult(
                name=name,
                status=status,
                message=message,
                times=times,
                tags=tags,
                doc=element.findtext('doc', ''),
                is_critical=(element.get('critical', 'no') == 'yes')
            )
        except Exception as e:
            logging.warning(f"Error creating test from XML: {str(e)}")
            return None

    def _create_test_from_dict(self, data):
        try:
            name = data.get('name', 'Unknown Test')
            status = data.get('status', 'UNKNOWN').upper()

            times = TestTimes(
                start_time=data.get('startTime', ''),
                end_time=data.get('endTime', ''),
                elapsed_time=float(data.get('duration', 0))
            )

            tags = data.get('tags', [])
            if isinstance(tags, str):
                tags = tags.split(',')

            return TestResult(
                name=name,
                status=status,
                message=data.get('message', ''),
                times=times,
                tags=tags,
                doc=data.get('documentation', ''),
                is_critical=data.get('critical', False)
            )
        except Exception as e:
            logging.warning(f"Error creating test from dict: {str(e)}")
            return None

    def _create_test_from_text(self, line):
        try:
            name_match = re.search(r'test[:\s]+(.+)', line, re.I)
            if name_match:
                name = name_match.group(1)
            else:
                name = "Unknown Test"

            status = "PASS" if 'pass' in line.lower() else ("FAIL" if 'fail' in line.lower() else "UNKNOWN")

            return TestResult(
                name=name,
                status=status,
                message='',
                times=TestTimes('', '', 0.0),
                tags=[],
                doc='',
                is_critical=False
            )
        except Exception as e:
            logging.warning(f"Error creating test from text: {str(e)}")
            return None

    def _update_test_from_text(self, test, line):
        try:
            line_lower = line.lower()

            # Durata
            duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)', line_lower)
            if duration_match:
                test.times.elapsed_time = float(duration_match.group(1))

            # Stato
            if 'pass' in line_lower:
                test.status = 'PASS'
            elif 'fail' in line_lower:
                test.status = 'FAIL'

            # Messaggi
            if ':' in line and 'test' not in line_lower:
                test.message += line.split(':', 1)[1].strip() + '\n'

        except Exception as e:
            logging.warning(f"Error updating test from text: {str(e)}")

    def _create_suite_result(self, tests):
        passed = sum(1 for test in tests if test.status == 'PASS')
        suite_name = "Test Suite"

        self.current_results = SuiteResult(
            name=suite_name,
            doc="",
            status="PASS" if passed == len(tests) else "FAIL",
            message="",
            start_time=datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f"),
            end_time=datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f"),
            elapsed_time=sum(t.times.elapsed_time for t in tests),
            tests=tests,
            total_tests=len(tests),
            passed_tests=passed,
            failed_tests=len(tests) - passed,
            metadata={}
        )

    def update_results_display(self):
        """Aggiorna tutti gli elementi di visualizzazione."""
        if not self.current_results:
            return

        self._update_summary()
        self._update_details()
        self.update_error_analysis()

        # Mostra il grafico "status" di default
        self.show_visualization('status')

    def _update_summary(self):
        """Aggiorna il sommario"""
        self.summary_text.delete('1.0', tk.END)

        total = self.current_results.total_tests
        passed = self.current_results.passed_tests
        failed = self.current_results.failed_tests
        duration = self.current_results.elapsed_time

        summary = f"""Test Suite Summary
        ====================
        Total Tests: {total}
        Passed: {passed}
        Failed: {failed}
        Total Duration: {duration:.2f}s

        Pass Rate: {(passed / total * 100) if total else 0:.1f}%
        Average Duration: {(duration / total) if total else 0:.2f}s

        Test Categories
        =====================
        """

        # Aggiungi statistiche per tag
        tag_stats = {}
        for test in self.current_results.tests:
            for tag in test.tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {'total': 0, 'passed': 0}
                tag_stats[tag]['total'] += 1
                if test.status == 'PASS':
                    tag_stats[tag]['passed'] += 1

        for tag, stats in tag_stats.items():
            pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] else 0
            summary += f"\n{tag}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)"

        self.summary_text.insert('1.0', summary)

    def _update_details(self):
        """Aggiorna la vista dettagliata"""
        # Pulisce la vista precedente
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        # Popola la TreeView
        for test in self.current_results.tests:
            self.details_tree.insert('', 'end',
                                     values=(
                                         test.name,
                                         test.status,
                                         f"{test.times.elapsed_time:.2f}s",
                                         ', '.join(test.tags)
                                     ),
                                     tags=(test.status.lower(),))

        # Colori per lo stato
        self.details_tree.tag_configure('pass', foreground='green')
        self.details_tree.tag_configure('fail', foreground='red')

    def update_error_analysis(self):
        """Aggiorna l'analisi degli errori"""
        if not self.current_results:
            return

        error_analyzer = self.error_analyzer
        analyses = error_analyzer.analyze_test_results(self.current_results.tests)
        summary = error_analyzer.get_error_summary(analyses)

        # Aggiorna il sommario
        self.error_summary_text.delete('1.0', tk.END)
        summary_text = f"""Error Analysis Summary
        =====================
        Total Errors Found: {summary['total_errors']}
        Critical Errors: {summary['critical_errors']}

        Error Pattern Frequency:
        """

        for pattern, count in summary['pattern_frequency'].items():
            summary_text += f"- {pattern}: {count}\n"

        summary_text += "\nSeverity Distribution:\n"
        for severity, count in summary['patterns_by_severity'].items():
            summary_text += f"- {severity}: {count}\n"

        self.error_summary_text.insert('1.0', summary_text)

        # Aggiorna la TreeView
        for item in self.error_tree.get_children():
            self.error_tree.delete(item)

        for analysis in analyses:
            for pattern in analysis['patterns']:
                self.error_tree.insert('', 'end', values=(
                    analysis['test_name'],
                    pattern.description,
                    pattern.severity,
                    pattern.suggested_fix
                ), tags=(pattern.severity.lower(),))

        # Configurazione colori per severità
        self.error_tree.tag_configure('high', foreground='red')
        self.error_tree.tag_configure('medium', foreground='orange')
        self.error_tree.tag_configure('low', foreground='blue')

    def _show_error_details(self, event):
        """Mostra i dettagli dell'errore selezionato"""
        selection = self.error_tree.selection()
        if not selection:
            return

        item = selection[0]
        test_name = self.error_tree.item(item)['values'][0]

        # Trova il test corrispondente
        test = next((t for t in self.current_results.tests
                     if t.name == test_name), None)
        if not test:
            return

        # Crea una finestra di dialogo con i dettagli
        dialog = tk.Toplevel()
        dialog.title(f"Error Details - {test_name}")
        dialog.geometry("600x400")

        details_text = scrolledtext.ScrolledText(dialog)
        details_text.pack(fill='both', expand=True, padx=5, pady=5)

        details = f"""Test Name: {test.name}
            Status: {test.status}
            Duration: {test.times.elapsed_time:.2f}s
            Tags: {', '.join(test.tags)}
            Critical: {'Yes' if test.is_critical else 'No'}

            Error Message:
            {test.message}

            Start Time: {test.times.start_time}
            End Time: {test.times.end_time}
            """

        details_text.insert('1.0', details)
        details_text.configure(state='disabled')

    def show_visualization(self, viz_type):
        """Mostra la visualizzazione selezionata (duration o status)"""
        if not self.current_results:
            messagebox.showwarning("No Data", "Please analyze a test report first.")
            return

        # Pulisce eventuali canvas preesistenti
        for widget in self.viz_container.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(8, 5))

        if viz_type == 'duration':
            self._create_duration_chart(ax)
        elif viz_type == 'status':
            self._create_status_chart(ax)

        canvas = FigureCanvasTkAgg(fig, master=self.viz_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _create_duration_chart(self, ax):
        """Crea il grafico della distribuzione delle durate"""
        durations = [t.times.elapsed_time for t in self.current_results.tests]
        if not durations:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=14)
            return

        ax.hist(durations, bins=20, color='skyblue', edgecolor='black')
        ax.set_title('Test Duration Distribution')
        ax.set_xlabel('Duration (seconds)')
        ax.set_ylabel('Number of Tests')

        mean_duration = sum(durations) / len(durations)
        durations_sorted = sorted(durations)
        median_duration = durations_sorted[len(durations_sorted) // 2]

        ax.axvline(mean_duration, color='red', linestyle='--', label=f'Mean: {mean_duration:.2f}s')
        ax.axvline(median_duration, color='green', linestyle='--', label=f'Median: {median_duration:.2f}s')
        ax.legend()

    def _create_status_chart(self, ax):
        """Crea il grafico della distribuzione degli stati"""
        status_counts = {
            'PASS': self.current_results.passed_tests,
            'FAIL': self.current_results.failed_tests
        }

        total = self.current_results.total_tests
        if total == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', fontsize=14)
            return

        colors = ['green', 'red']
        labels = ['PASS', 'FAIL']
        counts = [status_counts['PASS'], status_counts['FAIL']]

        explode = (0.1, 0)  # enfatizzare il settore PASS
        ax.pie(counts, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True)
        ax.set_title('Test Status Distribution')

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------
    def export_results(self):
        """Esempio di esportazione dei risultati"""
        if not self.current_results:
            messagebox.showwarning("No Data", "No results to export.")
            return

        try:
            self.output_dir.mkdir(exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Esempio: esporta in HTML e CSV
            html_file = self.output_dir / f"test_report_{timestamp}.html"
            self._export_html(html_file)

            csv_file = self.output_dir / f"test_results_{timestamp}.csv"
            self._export_csv(csv_file)

            # Grafici
            self._export_visualizations(timestamp)

            messagebox.showinfo("Export Complete", f"Results exported to:\n{self.output_dir}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")

    def _export_html(self, filepath: Path):
        """Salva un report HTML"""
        html_template = """
        <html>
        <head>
            <title>Test Execution Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background-color: #4CAF50; color: white; padding: 20px; }
                .summary { margin: 20px 0; }
                .pass { color: green; }
                .fail { color: red; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Execution Report</h1>
                <p>Generated: {timestamp}</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {total}</p>
                <p class="pass">Passed: {passed}</p>
                <p class="fail">Failed: {failed}</p>
                <p>Total Duration: {duration:.2f}s</p>
                <p>Pass Rate: {pass_rate:.1f}%</p>
            </div>

            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (s)</th>
                    <th>Tags</th>
                    <th>Message</th>
                </tr>
                {test_rows}
            </table>

            <h2>Error Analysis</h2>
            <div class="error-analysis">
                <h3>Error Patterns</h3>
                <table>
                    <tr>
                        <th>Error Type</th>
                        <th>Count</th>
                        <th>Severity</th>
                    </tr>
                    {error_rows}
                </table>
            </div>
        </body>
        </html>
        """

        test_rows = []
        for test in self.current_results.tests:
            status_class = 'pass' if test.status == 'PASS' else 'fail'
            row = f"""
            <tr>
                <td>{test.name}</td>
                <td class="{status_class}">{test.status}</td>
                <td>{test.times.elapsed_time:.2f}</td>
                <td>{', '.join(test.tags)}</td>
                <td>{test.message}</td>
            </tr>
            """
            test_rows.append(row)

        # Analisi errori
        analyses = self.error_analyzer.analyze_test_results(self.current_results.tests)
        summary = self.error_analyzer.get_error_summary(analyses)

        error_rows = []
        for pattern, count in summary['pattern_frequency'].items():
            row = f"""
            <tr>
                <td>{pattern}</td>
                <td>{count}</td>
                <td>{next((p.severity for p in self.error_analyzer.error_patterns if p.description == pattern), 'Unknown')}</td>
            </tr>
            """
            error_rows.append(row)

        total = self.current_results.total_tests
        passed = self.current_results.passed_tests
        failed = self.current_results.failed_tests
        duration = self.current_results.elapsed_time
        pass_rate = (passed / total * 100) if total else 0

        html_content = html_template.format(
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=total,
            passed=passed,
            failed=failed,
            duration=duration,
            pass_rate=pass_rate,
            test_rows='\n'.join(test_rows),
            error_rows='\n'.join(error_rows)
        )

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _export_csv(self, filepath: Path):
        """Salva i risultati in CSV"""
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Test Name', 'Status', 'Duration (s)', 'Tags',
                'Message', 'Start Time', 'End Time', 'Critical',
                'Error Type', 'Error Severity', 'Suggested Fix'
            ])

            # Analizziamo gli errori prima dell'esportazione
            analyses = self.error_analyzer.analyze_test_results(self.current_results.tests)
            error_dict = {analysis['test_name']: analysis for analysis in analyses}

            for test in self.current_results.tests:
                error_info = error_dict.get(test.name, None)
                error_type = ''
                error_severity = ''
                suggested_fix = ''

                if error_info and error_info['patterns']:
                    pattern = error_info['patterns'][0]  # Prendiamo il primo pattern trovato
                    error_type = pattern.description
                    error_severity = pattern.severity
                    suggested_fix = pattern.suggested_fix

                writer.writerow([
                    test.name,
                    test.status,
                    f"{test.times.elapsed_time:.2f}",
                    ', '.join(test.tags),
                    test.message.replace('\n', ' '),
                    test.times.start_time,
                    test.times.end_time,
                    'Yes' if test.is_critical else 'No',
                    error_type,
                    error_severity,
                    suggested_fix
                ])

    def _export_visualizations(self, timestamp: str):
        """Esporta i grafici in PNG"""
        plots_dir = self.output_dir / 'plots'
        plots_dir.mkdir(exist_ok=True)

        # Duration chart
        plt.figure(figsize=(10, 6))
        self._create_duration_chart(plt.gca())
        plt.savefig(plots_dir / f'duration_dist_{timestamp}.png')
        plt.close()

        # Status chart
        plt.figure(figsize=(8, 8))
        self._create_status_chart(plt.gca())
        plt.savefig(plots_dir / f'status_dist_{timestamp}.png')
        plt.close()

        # Error analysis chart
        analyses = self.error_analyzer.analyze_test_results(self.current_results.tests)
        summary = self.error_analyzer.get_error_summary(analyses)

        plt.figure(figsize=(10, 6))
        patterns = list(summary['pattern_frequency'].keys())
        counts = list(summary['pattern_frequency'].values())

        if patterns and counts:
            plt.bar(patterns, counts)
            plt.xticks(rotation=45, ha='right')
            plt.title('Error Pattern Distribution')
            plt.xlabel('Error Type')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.savefig(plots_dir / f'error_dist_{timestamp}.png')
        plt.close()