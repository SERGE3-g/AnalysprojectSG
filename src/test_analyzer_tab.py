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


class TestAnalyzerTab:
    """Tab per l'analisi dei report di test"""

    def __init__(self, notebook):
        """Inizializza il tab di analisi test"""
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Test Analyzer')

        # Inizializza variabili
        self.current_results = None
        self.output_dir = Path("report_output")
        self.file_path_var = tk.StringVar()

        # Crea l'interfaccia
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

    def create_summary_tab(self):
        """Crea il tab del sommario"""
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text='Summary')

        self.summary_text = scrolledtext.ScrolledText(summary_frame)
        self.summary_text.pack(fill='both', expand=True)

    def create_details_tab(self):
        """Crea il tab dei dettagli"""
        details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(details_frame, text='Details')

        # Treeview per i dettagli
        columns = ('name', 'status', 'duration', 'tags')
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show='headings')

        # Configura colonne
        column_configs = {
            'name': 'Test Name',
            'status': 'Status',
            'duration': 'Duration',
            'tags': 'Tags'
        }

        for col, heading in column_configs.items():
            self.details_tree.heading(col, text=heading)
            self.details_tree.column(col, width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(details_frame, orient='vertical', command=self.details_tree.yview)
        self.details_tree.configure(yscrollcommand=scrollbar.set)

        # Layout
        self.details_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_visualization_tab(self):
        """Crea il tab delle visualizzazioni"""
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

    def browse_file(self):
        """Apre il dialogo di selezione file"""
        try:
            filename = filedialog.askopenfilename(
                title="Select Test Report",
                filetypes=[
                    ("All Supported Files", "*.xml;*.json;*.txt"),
                    ("XML files", "*.xml"),
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                self.file_path_var.set(filename)
        except Exception as e:
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

            # Parse basato sull'estensione
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
        """Parse del report XML"""
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
        """Parse del report JSON"""
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
        """Parse del report testuale"""
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
        """Crea un oggetto TestResult da un elemento XML"""
        try:
            name = element.get('name', 'Unknown Test')
            status = element.get('status', 'UNKNOWN').upper()
            message = element.findtext('msg', '')

            # Estrai i tempi
            times = TestTimes(
                start_time=element.get('starttime', ''),
                end_time=element.get('endtime', ''),
                elapsed_time=float(element.get('time', '0'))
            )

            # Estrai i tag
            tags = [tag.text for tag in element.findall('tag')]

            return TestResult(
                name=name,
                status=status,
                message=message,
                times=times,
                tags=tags,
                doc=element.findtext('doc', ''),
                is_critical=element.get('critical', 'no') == 'yes'
            )
        except Exception as e:
            logging.warning(f"Error creating test from XML: {str(e)}")
            return None

    def _create_test_from_dict(self, data):
        """Crea un oggetto TestResult da un dizionario"""
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
        """Crea un oggetto TestResult da una linea di testo"""
        try:
            name = re.search(r'test[:\s]+(.+)', line, re.I)
            name = name.group(1) if name else 'Unknown Test'

            status = 'PASS' if 'pass' in line.lower() else 'FAIL' if 'fail' in line.lower() else 'UNKNOWN'

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
        """Aggiorna un test con informazioni da una linea di testo"""
        try:
            line_lower = line.lower()

            # Cerca durata
            duration_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)', line_lower)
            if duration_match:
                test.times.elapsed_time = float(duration_match.group(1))

            # Cerca stato
            if 'pass' in line_lower:
                test.status = 'PASS'
            elif 'fail' in line_lower:
                test.status = 'FAIL'

            # Cerca messaggi
            if ':' in line and 'test' not in line_lower:
                test.message += line.split(':', 1)[1].strip() + '\n'

        except Exception as e:
            logging.warning(f"Error updating test from text: {str(e)}")

    def _create_suite_result(self, tests):
        """Crea un oggetto SuiteResult dai test analizzati"""
        passed = sum(1 for test in tests if test.status == 'PASS')

        self.current_results = SuiteResult(
            name="Test Suite",
            doc="",
            status="PASS" if passed == len(tests) else "FAIL",
            message="",
            start_time=datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f"),
            end_time=datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f"),
            elapsed_time=sum(test.times.elapsed_time for test in tests),
            tests=tests,
            total_tests=len(tests),
            passed_tests=passed,
            failed_tests=len(tests) - passed,
            metadata={}
        )

    def update_results_display(self):
        """Aggiorna tutti gli elementi di visualizzazione"""
        if not self.current_results:
            return

        self._update_summary()
        self._update_details()
        self.show_visualization('status')  # Mostra il grafico di stato di default

        def _update_summary(self):
            """Aggiorna il sommario"""
            self.summary_text.delete('1.0', tk.END)

            summary = f"""Test Suite Summary
    ====================
    Total Tests: {self.current_results.total_tests}
    Passed: {self.current_results.passed_tests}
    Failed: {self.current_results.failed_tests}
    Total Duration: {self.current_results.elapsed_time:.2f}s

    Pass Rate: {(self.current_results.passed_tests / self.current_results.total_tests * 100):.1f}%
    Average Duration: {(self.current_results.elapsed_time / self.current_results.total_tests):.2f}s

    Test Categories
    =============="""

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
                pass_rate = (stats['passed'] / stats['total'] * 100)
                summary += f"\n{tag}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)"

            self.summary_text.insert('1.0', summary)

        def _update_details(self):
            """Aggiorna la vista dettagliata"""
            # Pulisci la vista precedente
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            # Inserisci i nuovi dati
            for test in self.current_results.tests:
                self.details_tree.insert('', 'end',
                                         values=(
                                             test.name,
                                             test.status,
                                             f"{test.times.elapsed_time:.2f}s",
                                             ', '.join(test.tags)
                                         ),
                                         tags=(test.status.lower(),))

            # Configura i colori per lo stato
            self.details_tree.tag_configure('pass', foreground='green')
            self.details_tree.tag_configure('fail', foreground='red')

        def show_visualization(self, viz_type):
            """Mostra la visualizzazione selezionata"""
            if not self.current_results:
                messagebox.showwarning("No Data", "Please analyze a test report first.")
                return

            # Pulisci il container precedente
            for widget in self.viz_container.winfo_children():
                widget.destroy()

            fig, ax = plt.subplots(figsize=(10, 6))

            if viz_type == 'duration':
                self._create_duration_chart(ax)
            elif viz_type == 'status':
                self._create_status_chart(ax)

            # Crea il widget canvas
            canvas = FigureCanvasTkAgg(fig, master=self.viz_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

        def _create_duration_chart(self, ax):
            """Crea il grafico della distribuzione delle durate"""
            durations = [test.times.elapsed_time for test in self.current_results.tests]

            ax.hist(durations, bins=20, color='skyblue', edgecolor='black')
            ax.set_title('Test Duration Distribution')
            ax.set_xlabel('Duration (seconds)')
            ax.set_ylabel('Number of Tests')

            # Aggiungi linee verticali per media e mediana
            mean_duration = sum(durations) / len(durations)
            median_duration = sorted(durations)[len(durations) // 2]

            ax.axvline(mean_duration, color='red', linestyle='--', label=f'Mean: {mean_duration:.2f}s')
            ax.axvline(median_duration, color='green', linestyle='--', label=f'Median: {median_duration:.2f}s')
            ax.legend()

        def _create_status_chart(self, ax):
            """Crea il grafico della distribuzione degli stati"""
            status_counts = {
                'PASS': self.current_results.passed_tests,
                'FAIL': self.current_results.failed_tests
            }

            colors = ['green', 'red']
            explode = (0.1, 0)  # Evidenzia il settore PASS

            ax.pie(status_counts.values(),
                   explode=explode,
                   labels=status_counts.keys(),
                   colors=colors,
                   autopct='%1.1f%%',
                   shadow=True)

            ax.set_title('Test Status Distribution')

        def export_results(self):
            """Esporta i risultati in vari formati"""
            if not self.current_results:
                messagebox.showwarning("No Data", "No results to export.")
                return

            try:
                # Crea directory se non esiste
                self.output_dir.mkdir(exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                # Esporta report HTML
                html_file = self.output_dir / f"test_report_{timestamp}.html"
                self._export_html(html_file)

                # Esporta CSV
                csv_file = self.output_dir / f"test_results_{timestamp}.csv"
                self._export_csv(csv_file)

                # Esporta grafici
                self._export_visualizations(timestamp)

                messagebox.showinfo("Export Complete",
                                    f"Results exported to:\n{self.output_dir}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")

        def _export_html(self, filepath):
            """Esporta il report in formato HTML"""
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
                        <th>Duration</th>
                        <th>Tags</th>
                        <th>Message</th>
                    </tr>
                    {test_rows}
                </table>
            </body>
            </html>
            """

            # Genera le righe della tabella
            test_rows = []
            for test in self.current_results.tests:
                status_class = 'pass' if test.status == 'PASS' else 'fail'
                row = f"""
                    <tr>
                        <td>{test.name}</td>
                        <td class="{status_class}">{test.status}</td>
                        <td>{test.times.elapsed_time:.2f}s</td>
                        <td>{', '.join(test.tags)}</td>
                        <td>{test.message}</td>
                    </tr>
                """
                test_rows.append(row)

            # Compila il template
            html_content = html_template.format(
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total=self.current_results.total_tests,
                passed=self.current_results.passed_tests,
                failed=self.current_results.failed_tests,
                duration=self.current_results.elapsed_time,
                pass_rate=(self.current_results.passed_tests / self.current_results.total_tests * 100),
                test_rows='\n'.join(test_rows)
            )

            # Salva il file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

        def _export_csv(self, filepath):
            """Esporta i risultati in formato CSV"""
            import csv

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Intestazioni
                writer.writerow([
                    'Test Name', 'Status', 'Duration (s)', 'Tags',
                    'Message', 'Start Time', 'End Time', 'Critical'
                ])

                # Dati
                for test in self.current_results.tests:
                    writer.writerow([
                        test.name,
                        test.status,
                        f"{test.times.elapsed_time:.2f}",
                        ', '.join(test.tags),
                        test.message.replace('\n', ' '),
                        test.times.start_time,
                        test.times.end_time,
                        'Yes' if test.is_critical else 'No'
                    ])

        def _export_visualizations(self, timestamp):
            """Esporta i grafici come immagini"""
            plots_dir = self.output_dir / 'plots'
            plots_dir.mkdir(exist_ok=True)

            # Esporta grafico durata
            fig, ax = plt.subplots(figsize=(10, 6))
            self._create_duration_chart(ax)
            plt.savefig(plots_dir / f'duration_dist_{timestamp}.png')
            plt.close()

            # Esporta grafico stato
            fig, ax = plt.subplots(figsize=(8, 8))
            self._create_status_chart(ax)
            plt.savefig(plots_dir / f'status_dist_{timestamp}.png')
            plt.close()

        def search(self, query):
            """Funzionalità di ricerca per la ricerca globale"""
            if not self.current_results:
                return []

            results = []
            query = query.lower()

            for test in self.current_results.tests:
                if (query in test.name.lower() or
                        query in test.message.lower() or
                        query in ','.join(test.tags).lower()):
                    result_title = f"Test: {test.name}"
                    result_content = (
                        f"Status: {test.status}\n"
                        f"Duration: {test.times.elapsed_time:.2f}s\n"
                        f"Tags: {', '.join(test.tags)}\n"
                        f"Message: {test.message}"
                    )
                    results.append((result_title, result_content))

            return results