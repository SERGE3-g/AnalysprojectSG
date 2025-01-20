from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QComboBox, QMessageBox,
    QStatusBar, QToolBar, QAction, QFileDialog, QSpinBox,
    QSplitter, QTableView, QHeaderView
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QTextCursor, QStandardItemModel, QStandardItem

from app.nlp import NLPProcessor
from app.query_generator import QueryGenerator
from app.database import DatabaseManager

import json
import os
from datetime import datetime


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chat_history = []
        self.init_ui()
        self.init_components()
        self.setup_status_bar()
        self.setup_toolbar()
        self.setup_shortcuts()
        self.load_settings()

    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        self.setWindowTitle("Query Generator Chatbot")
        self.setMinimumSize(1000, 700)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principale
        main_layout = QVBoxLayout(central_widget)

        # Splitter per dividere la chat e i risultati
        splitter = QSplitter(Qt.Vertical)

        # Container superiore per la chat
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)

        # Area chat con stile
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_area)

        # Container inferiore per l'input
        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)

        # Controlli query
        query_controls = QHBoxLayout()

        # Label per il tipo di query
        query_type_label = QLabel("Tipo di Query:")
        query_controls.addWidget(query_type_label)

        # Tipo di query
        self.query_type = QComboBox()
        self.query_type.addItems(['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'JOIN', 'GROUP BY'])
        self.query_type.currentTextChanged.connect(self.on_query_type_changed)
        query_controls.addWidget(self.query_type)

        # SpinBox Limite
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 1000)
        self.limit_spin.setValue(100)
        self.limit_spin.setPrefix("Limite: ")
        query_controls.addWidget(self.limit_spin)

        input_layout.addLayout(query_controls)

        # Area input con layout orizzontale
        input_area = QHBoxLayout()

        # Campo input con placeholder e stile
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Scrivi il tuo messaggio qui...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial;
                font-size: 12px;
            }
        """)
        input_area.addWidget(self.input_field)

        # Pulsante invio con icona e stile
        send_button = QPushButton("Invia")
        send_button.setIcon(QIcon("resources/icons/send.png"))
        send_button.setIconSize(QSize(16, 16))
        send_button.clicked.connect(self.process_input)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        input_area.addWidget(send_button)

        input_layout.addLayout(input_area)

        # Tabella risultati
        self.results_table = QTableView()
        self.results_table.setSelectionBehavior(QTableView.SelectRows)
        self.results_table.setSelectionMode(QTableView.SingleSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Aggiungi i widget al splitter
        splitter.addWidget(chat_container)
        splitter.addWidget(input_container)
        splitter.addWidget(self.results_table)

        # Imposta le proporzioni del splitter
        splitter.setSizes([300, 100, 200])

        main_layout.addWidget(splitter)

    def init_components(self):
        """Inizializza i componenti del backend"""
        try:
            self.nlp_processor = NLPProcessor()
            self.query_generator = QueryGenerator()
            self.db_manager = DatabaseManager("database.db")
            self.statusBar().showMessage("Componenti inizializzati con successo", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'inizializzazione dei componenti: {str(e)}")

    def setup_status_bar(self):
        """Configura la barra di stato"""
        self.statusBar().showMessage("Pronto")

        # Indicatore di stato della connessione
        self.connection_label = QLabel()
        self.connection_label.setStyleSheet("color: green;")
        self.connection_label.setText("⚫ Connesso")
        self.statusBar().addPermanentWidget(self.connection_label)

    def setup_toolbar(self):
        """Configura la barra degli strumenti"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Azione per salvare la chat
        save_action = QAction(QIcon("resources/icons/save.png"), "Salva Chat", self)
        save_action.triggered.connect(self.save_chat)
        toolbar.addAction(save_action)

        # Azione per caricare la chat
        load_action = QAction(QIcon("resources/icons/load.png"), "Carica Chat", self)
        load_action.triggered.connect(self.load_chat)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        # Azione per pulire la chat
        clear_action = QAction(QIcon("resources/icons/clear.png"), "Pulisci Chat", self)
        clear_action.triggered.connect(self.clear_chat)
        toolbar.addAction(clear_action)

    def setup_shortcuts(self):
        """Configura le scorciatoie da tastiera"""
        # Ctrl+Enter per inviare il messaggio (implementabile come event filter)
        self.input_field.installEventFilter(self)

    def eventFilter(self, source, event):
        """Event filter per catturare Ctrl+Invio"""
        if (event.type() == event.KeyPress and
            (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter) and
            (event.modifiers() & Qt.ControlModifier)):

            if source is self.input_field:
                self.process_input()
                return True
        return super().eventFilter(source, event)

    def on_query_type_changed(self, new_type):
        """Se cambia il tipo di query nel comboBox"""
        self.statusBar().showMessage(f"Tipo di Query selezionato: {new_type}", 3000)

    def process_input(self):
        """Elabora l'input dell'utente e genera una risposta"""
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            return

        # Aggiunge il messaggio dell'utente alla chat
        self.add_to_chat("👤 User:", user_input)

        try:
            # Analizza il testo
            nlp_result = self.nlp_processor.process_text(user_input)

            # Determina l'intento (esempio ipotetico, se avessi una get_query_intent)
            # Se non esiste, puoi sostituire con logiche personalizzate
            if hasattr(self.nlp_processor, "get_query_intent"):
                intent_result = self.nlp_processor.get_query_intent(user_input)
            else:
                intent_result = "select"  # fallback

            # Prepara i parametri della query
            query_params = self.prepare_query_params(nlp_result, intent_result)

            # Genera la query
            query_text = self.query_type.currentText().lower()
            query = self.query_generator.generate_query(query_text, query_params)

            # Esegue la query
            results = self.db_manager.execute_query(query)

            # Aggiunge la risposta alla chat
            self.add_to_chat("🤖 Bot:", "Ho generato la seguente query:")
            self.add_to_chat("📝 Query:", query)

            # Mostra i risultati nella tabella
            self.display_results(results)

        except Exception as e:
            self.add_to_chat("❌ Error:", f"Si è verificato un errore: {str(e)}")
            QMessageBox.warning(self, "Errore", str(e))

        # Pulisce il campo input
        self.input_field.clear()

    def prepare_query_params(self, nlp_result, intent_result):
        """Prepara i parametri della query basati sull'analisi NLP"""
        params = {
            'table': 'example_table',
            'columns': '*',
            'conditions': '1=1',
            # Ecc. Altri parametri a seconda dell'intento
        }

        # Se avessi entità riconosciute come "TABLE" o "COLUMN", potresti popolare param in base a nlp_result
        if 'entities' in nlp_result:
            for entity, label in nlp_result['entities']:
                if label == 'TABLE':
                    params['table'] = entity
                elif label == 'COLUMN':
                    if params['columns'] == '*':
                        params['columns'] = entity
                    else:
                        params['columns'] += f', {entity}'

        return params

    def display_results(self, results):
        """Mostra i risultati nella tabella"""
        if not results:
            self.add_to_chat("ℹ️ Info:", "Nessun risultato trovato")
            return

        # Crea il modello per la tabella
        model = QStandardItemModel()

        # Imposta le intestazioni
        headers = list(results[0].keys())
        model.setHorizontalHeaderLabels(headers)

        # Aggiunge i dati
        for row_data in results:
            row = []
            for column in headers:
                item = QStandardItem(str(row_data[column]))
                row.append(item)
            model.appendRow(row)

        self.results_table.setModel(model)
        self.add_to_chat("✅ Success:", f"Trovati {len(results)} risultati")

    def add_to_chat(self, prefix: str, message: str):
        """Aggiunge un messaggio all'area chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {prefix} {message}"

        # Aggiunge alla cronologia
        self.chat_history.append(formatted_message)

        # Aggiunge alla visualizzazione
        self.chat_area.append(formatted_message)
        self.chat_area.append("")  # Riga vuota per spaziatura

        # Scrolla in fondo
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_area.setTextCursor(cursor)

    def save_chat(self):
        """Salva la cronologia della chat"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Salva Chat",
                "",
                "JSON files (*.json);;Text files (*.txt)"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.chat_history, f, indent=2, ensure_ascii=False)
                self.statusBar().showMessage(f"Chat salvata in {filename}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel salvare la chat: {str(e)}")

    def load_chat(self):
        """Carica la cronologia della chat"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Carica Chat",
                "",
                "JSON files (*.json);;Text files (*.txt)"
            )

            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.chat_history = json.load(f)

                # Aggiorna la visualizzazione
                self.chat_area.clear()
                for message in self.chat_history:
                    self.chat_area.append(message)
                    self.chat_area.append("")

                self.statusBar().showMessage(f"Chat caricata da {filename}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricare la chat: {str(e)}")

    def clear_chat(self):
        """Pulisce la chat"""
        reply = QMessageBox.question(
            self,
            "Conferma",
            "Sei sicuro di voler cancellare la chat?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.chat_area.clear()
            self.chat_history.clear()
            self.statusBar().showMessage("Chat cancellata", 3000)

    def load_settings(self):
        """Carica le impostazioni dell'applicazione"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.resize(settings.get('window_size', [1000, 700])[0],
                                settings.get('window_size', [1000, 700])[1])
                    self.move(settings.get('window_position', [100, 100])[0],
                              settings.get('window_position', [100, 100])[1])
        except Exception as e:
            self.statusBar().showMessage(f"Errore nel caricamento delle impostazioni: {str(e)}")

    def save_settings(self):
        """Salva le impostazioni dell'applicazione"""
        try:
            settings = {
                'window_size': [self.width(), self.height()],
                'window_position': [self.x(), self.y()]
            }
            with open('settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            self.statusBar().showMessage("Impostazioni salvate", 2000)
        except Exception as e:
            self.statusBar().showMessage(f"Errore nel salvataggio delle impostazioni: {str(e)}")

    def closeEvent(self, event):
        """Evento chiamato alla chiusura della finestra"""
        # Salva le impostazioni prima di chiudere
        self.save_settings()
        super().closeEvent(event)
