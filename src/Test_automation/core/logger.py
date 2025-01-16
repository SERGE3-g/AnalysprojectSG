import logging
import os
import sys
import json
import yaml
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from elasticsearch import Elasticsearch
from prometheus_client import Counter, Gauge, push_to_gateway
import logging.config


class LoggerConfig:
    """Classe per gestire la configurazione del logger"""

    DEFAULT_CONFIG_FILE = "config/logger_config.yaml"

    @classmethod
    def load_config(cls, config_file: Optional[str] = None) -> Dict:
        """Carica configurazione da file YAML"""
        config_file = config_file or cls.DEFAULT_CONFIG_FILE

        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Errore nel caricamento della configurazione: {str(e)}")
            return {}


class Logger:
    """Logger avanzato con supporto per diversi formati e integrazioni"""

    _loggers = {}
    _metrics = {}
    _config = None

    @classmethod
    def initialize(cls, config_file: Optional[str] = None):
        """Inizializza il logger con configurazione"""
        cls._config = LoggerConfig.load_config(config_file)
        if cls._config:
            logging.config.dictConfig(cls._config)

        # Inizializza metriche
        cls._init_metrics()

    @classmethod
    def _init_metrics(cls):
        """Inizializza contatori e metriche"""
        cls._metrics['test_counter'] = Counter('test_executions_total',
                                               'Total test executions')
        cls._metrics['test_duration'] = Gauge('test_duration_seconds',
                                              'Test execution duration')
        cls._metrics['error_counter'] = Counter('test_errors_total',
                                                'Total test errors')

    @classmethod
    def get_logger(cls, name: str, level: Optional[int] = None) -> logging.Logger:
        """Get logger instance with advanced configuration"""
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)

        # Configura handlers se non già presenti
        if not logger.handlers:
            cls._configure_handlers(logger, name)

        if level:
            logger.setLevel(level)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def _configure_handlers(cls, logger: logging.Logger, name: str):
        """Configura handlers per diversi output"""
        # Console Handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(cls._get_formatter())
        logger.addHandler(console)

        # File Handler
        file_handler = logging.FileHandler(
            f"logs/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setFormatter(cls._get_formatter())
        logger.addHandler(file_handler)

        # Elastic Handler (se configurato)
        if cls._config and cls._config.get('elastic'):
            cls._add_elastic_handler(logger)

    @staticmethod
    def _get_formatter():
        """Ottiene formatter personalizzato"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        )

    @classmethod
    def log_test_result(cls, test_name: str, status: str,
                        details: Dict[str, Any], duration: float):
        """Log test result with metrics"""
        logger = cls.get_logger('TestResults')

        # Aggiorna metriche
        cls._metrics['test_counter'].inc()
        cls._metrics['test_duration'].set(duration)
        if status == 'FAIL':
            cls._metrics['error_counter'].inc()

        # Salva risultato
        result = {
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }

        # Salva in diversi formati
        cls._save_json_result(result)
        cls._save_xml_result(result)

        # Push metriche a Prometheus
        if cls._config.get('prometheus'):
            cls._push_metrics_prometheus()

    @classmethod
    def _save_json_result(cls, result: Dict):
        """Salva risultato in formato JSON"""
        results_file = f"logs/test_runs/results_{datetime.now().strftime('%Y%m%d')}.json"

        try:
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    results = json.load(f)
            else:
                results = []

            results.append(result)

            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            cls.get_logger('Logger').error(f"Error saving JSON result: {str(e)}")

    @classmethod
    def _save_xml_result(cls, result: Dict):
        """Salva risultato in formato XML"""
        xml_file = f"logs/test_runs/results_{datetime.now().strftime('%Y%m%d')}.xml"

        try:
            if os.path.exists(xml_file):
                tree = ET.parse(xml_file)
                root = tree.getroot()
            else:
                root = ET.Element('test_results')

            test = ET.SubElement(root, 'test')
            for key, value in result.items():
                if isinstance(value, dict):
                    sub = ET.SubElement(test, key)
                    for k, v in value.items():
                        ET.SubElement(sub, k).text = str(v)
                else:
                    ET.SubElement(test, key).text = str(value)

            tree = ET.ElementTree(root)
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            cls.get_logger('Logger').error(f"Error saving XML result: {str(e)}")

    @classmethod
    def create_pdf_report(cls, output_file: str):
        """Genera report PDF dei test"""
        try:
            # Carica risultati
            results = cls._load_test_results()

            doc = SimpleDocTemplate(output_file, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Titolo
            story.append(Paragraph("Test Execution Report", styles['Title']))

            # Summary
            total = len(results)
            passed = sum(1 for r in results if r['status'] == 'PASS')
            failed = total - passed

            summary_data = [
                ['Total Tests', str(total)],
                ['Passed', str(passed)],
                ['Failed', str(failed)]
            ]

            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)

            # Dettagli test
            test_data = [['Test Name', 'Status', 'Duration', 'Timestamp']]
            for result in results:
                test_data.append([
                    result['test_name'],
                    result['status'],
                    f"{result['duration']:.2f}s",
                    result['timestamp']
                ])

            test_table = Table(test_data)
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(test_table)

            # Crea grafici
            cls._add_charts_to_report(story, results)

            doc.build(story)

        except Exception as e:
            cls.get_logger('Logger').error(f"Error creating PDF report: {str(e)}")

    @classmethod
    def _add_charts_to_report(cls, story: List, results: List[Dict]):
        """Aggiunge grafici al report PDF"""
        # Converti risultati in DataFrame
        df = pd.DataFrame(results)

        # Grafico a torta Pass/Fail
        plt.figure(figsize=(6, 6))
        status_counts = df['status'].value_counts()
        plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
        plt.title('Test Results Distribution')
        plt.savefig('temp_pie.png')
        plt.close()

        # Grafico durata test
        plt.figure(figsize=(8, 4))
        df['duration'].plot(kind='bar')
        plt.title('Test Duration Distribution')
        plt.tight_layout()
        plt.savefig('temp_bar.png')
        plt.close()

        # Aggiungi grafici al report
        story.append(Paragraph("Test Results Distribution", getSampleStyleSheet()['Heading2']))
        story.append(Image('temp_pie.png'))
        story.append(Paragraph("Test Duration Distribution", getSampleStyleSheet()['Heading2']))
        story.append(Image('temp_bar.png'))

        # Pulisci file temporanei
        os.remove('temp_pie.png')
        os.remove('temp_bar.png')

    @classmethod
    def _push_metrics_prometheus(cls):
        """Push metrics to Prometheus Gateway"""
        if cls._config.get('prometheus', {}).get('gateway'):
            try:
                push_to_gateway(
                    cls._config['prometheus']['gateway'],
                    job='test_metrics',
                    registry=cls._metrics
                )
            except Exception as e:
                cls.get_logger('Logger').error(f"Error pushing metrics: {str(e)}")

    @classmethod
    def _add_elastic_handler(cls, logger: logging.Logger):
        """Aggiunge handler per Elasticsearch"""
        try:
            elastic_config = cls._config['elastic']
            es = Elasticsearch([elastic_config['host']])

            class ElasticHandler(logging.Handler):
                def emit(self, record):
                    try:
                        es.index(
                            index=elastic_config['index'],
                            document={
                                'timestamp': datetime.utcnow(),
                                'level': record.levelname,
                                'message': record.getMessage(),
                                'logger': record.name
                            }
                        )
                    except Exception:
                        self.handleError(record)

            logger.addHandler(ElasticHandler())

        except Exception as e:
            cls.get_logger('Logger').error(f"Error adding Elastic handler: {str(e)}")

    @classmethod
    def generate_metrics_report(cls, output_file: str):
        """Genera report dettagliato delle metriche"""
        try:
            results = cls._load_test_results()
            df = pd.DataFrame(results)

            # Calcola metriche
            metrics = {
                'total_tests': len(df),
                'pass_rate': (df['status'] == 'PASS').mean() * 100,
                'avg_duration': df['duration'].mean(),
                'max_duration': df['duration'].max(),
                'min_duration': df['duration'].min(),
                'std_duration': df['duration'].std()
            }

            # Analisi temporale
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Crea report
            with pd.ExcelWriter(output_file) as writer:
                # Summary sheet
                pd.DataFrame([metrics]).to_excel(writer, sheet_name='Summary')

                # Results sheet
                df.to_excel(writer, sheet_name='Test Results')

                # Temporal analysis
                daily_stats = df.resample('D').agg({
                    'status': lambda x: (x == 'PASS').mean() * 100,
                    'duration': ['mean', 'std']
                })
                daily_stats.to_excel(writer, sheet_name='Daily Stats')

        except Exception as e:
            cls.get_logger('Logger').error(f"Error generating metrics report: {str(e)}")

    @classmethod
    def cleanup_old_logs(cls, days: int = 30):
        """Pulisce i log più vecchi di X giorni"""
        try:
            current_time = datetime.now()
            log_dirs = ['logs', 'logs/test_runs', 'logs/error']

            for directory in log_dirs:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        )
                        if (current_time - file_time).days > days:
                            os.remove(file_path)

        except Exception as e:
            cls.get_logger('Logger').error(f"Error cleaning old logs: {str(e)}")

    @classmethod
    def backup_logs(cls, backup_dir: str):
        """Backup dei log in una directory esterna"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'logs_backup_{timestamp}')

            # Crea directory di backup
            os.makedirs(backup_path, exist_ok=True)

            # Copia tutti i file di log
            for root, dirs, files in os.walk('logs'):