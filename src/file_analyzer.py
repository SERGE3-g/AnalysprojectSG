import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import xml.etree.ElementTree as ET
import os
import pandas as pd
from datetime import datetime
import re
import threading
from queue import Queue


class FileTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Analisi File')

        # Inizializzazione variabili
        self.current_files = []
        self.result_queue = Queue()

        # Setup interfaccia
        self.create_gui()

    def create_gui(self):
        """Crea l'interfaccia grafica"""
        # Frame superiore per caricamento file
        self.create_upload_frame()

        # Frame centrale per opzioni analisi
        self.create_options_frame()

        # Frame per la progress bar
        self.create_progress_frame()

        # Frame inferiore per risultati
        self.create_results_frame()

    def create_upload_frame(self):
        """Crea il frame per il caricamento dei file"""
        upload_frame = ttk.LabelFrame(self.frame, text="Carica File", padding=10)
        upload_frame.pack(fill='x', padx=5, pady=5)

        # Entry per i file selezionati
        self.file_entry = ttk.Entry(upload_frame)
        self.file_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))

        # Bottoni
        btn_frame = ttk.Frame(upload_frame)
        btn_frame.pack(side='right')

        ttk.Button(btn_frame, text="Sfoglia",
                   command=self.browse_files).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Pulisci",
                   command=self.clear_files).pack(side='left', padx=2)

    def create_options_frame(self):
        """Crea il frame per le opzioni di analisi"""
        options_frame = ttk.LabelFrame(self.frame, text="Opzioni Analisi", padding=10)
        options_frame.pack(fill='x', padx=5, pady=5)

        # Tipo di analisi
        ttk.Label(options_frame, text="Tipo analisi:").pack(side='left')
        self.analysis_type = tk.StringVar(value="auto")
        analysis_combo = ttk.Combobox(options_frame,
                                      textvariable=self.analysis_type,
                                      values=["auto", "xml", "json", "txt"],
                                      state="readonly")
        analysis_combo.pack(side='left', padx=5)

        # Checkbox per opzioni
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Analisi ricorsiva",
                        variable=self.recursive_var).pack(side='left', padx=5)

        self.extract_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Estrai numeri",
                        variable=self.extract_numbers_var).pack(side='left', padx=5)

        # Bottone analisi
        ttk.Button(options_frame, text="Analizza",
                   command=self.start_analysis).pack(side='right', padx=5)

    def create_progress_frame(self):
        """Crea il frame per la barra di progresso"""
        progress_frame = ttk.Frame(self.frame)
        progress_frame.pack(fill='x', padx=5, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame,
                                        variable=self.progress_var,
                                        maximum=100)
        self.progress.pack(fill='x')

        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack()

    def create_results_frame(self):
        """Crea il frame per i risultati"""
        results_frame = ttk.LabelFrame(self.frame, text="Risultati", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Notebook per diversi tipi di risultati
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill='both', expand=True)

        # Tab per testo
        text_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(text_frame, text='Testo')

        # Scrollbar per il testo
        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side='right', fill='y')

        self.result_text = tk.Text(text_frame, wrap='word',
                                   yscrollcommand=text_scroll.set)
        self.result_text.pack(fill='both', expand=True)
        text_scroll.config(command=self.result_text.yview)

        # Tab per struttura
        tree_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(tree_frame, text='Struttura')

        # Treeview per struttura
        self.tree = ttk.Treeview(tree_frame, show='tree')
        tree_scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side='left', fill='both', expand=True)
        tree_scroll.pack(side='right', fill='y')

        # Bottoni azione
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill='x', pady=5)

        ttk.Button(action_frame, text="Esporta Excel",
                   command=self.export_excel).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Salva Report",
                   command=self.save_report).pack(side='left', padx=2)
        ttk.Button(action_frame, text="Copia",
                   command=self.copy_results).pack(side='left', padx=2)

    def browse_files(self):
        """Apre il dialogo per selezionare i file"""
        files = filedialog.askopenfilenames(
            title="Seleziona file da analizzare",
            filetypes=[
                ("Tutti i file", "*.*"),
                ("File XML", "*.xml"),
                ("File JSON", "*.json"),
                ("File di testo", "*.txt")
            ]
        )
        if files:
            self.current_files = files
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, "; ".join(files))

    def clear_files(self):
        """Pulisce la selezione dei file"""
        self.current_files = []
        self.file_entry.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.progress_var.set(0)
        self.progress_label.config(text="")

    def start_analysis(self):
        """Avvia l'analisi dei file"""
        if not self.current_files:
            messagebox.showwarning("Attenzione", "Seleziona almeno un file!")
            return

        # Pulisci risultati precedenti
        self.result_text.delete(1.0, tk.END)
        self.tree.delete(*self.tree.get_children())

        # Avvia thread di analisi
        threading.Thread(target=self.analyze_files, daemon=True).start()

    def analyze_files(self):
        """Analizza i file selezionati"""
        try:
            total_files = len(self.current_files)
            for i, file_path in enumerate(self.current_files, 1):
                # Aggiorna progresso
                progress = (i / total_files) * 100
                self.update_progress(progress, f"Analisi file {i} di {total_files}")

                # Analizza file
                filename = os.path.basename(file_path)
                file_type = self.detect_file_type(file_path)

                try:
                    if file_type == "xml":
                        self.analyze_xml(file_path)
                    elif file_type == "json":
                        self.analyze_json(file_path)
                    else:
                        self.analyze_text(file_path)
                except Exception as e:
                    self.result_queue.put(("error", f"Errore nell'analisi di {filename}: {str(e)}"))

            self.update_progress(100, "Analisi completata")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'analisi: {str(e)}")

    def detect_file_type(self, file_path):
        """Rileva il tipo di file"""
        if self.analysis_type.get() != "auto":
            return self.analysis_type.get()

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".xml":
            return "xml"
        elif ext == ".json":
            return "json"
        return "txt"

    def analyze_xml(self, file_path):
        """Analizza un file XML"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Analisi struttura
            def process_element(element, parent=""):
                info = {
                    "tag": element.tag,
                    "attributes": element.attrib,
                    "text": element.text.strip() if element.text else "",
                    "children": []
                }

                for child in element:
                    info["children"].append(process_element(child))

                return info

            structure = process_element(root)

            # Inserisci nella treeview
            def add_to_tree(data, parent=""):
                tag = data["tag"]
                if data["attributes"]:
                    tag += f" {data['attributes']}"
                if data["text"]:
                    tag += f": {data['text']}"

                item = self.tree.insert(parent, "end", text=tag)
                for child in data["children"]:
                    add_to_tree(child, item)

            self.result_queue.put(("tree", structure))

            # Aggiungi al testo
            filename = os.path.basename(file_path)
            summary = f"\nAnalisi XML: {filename}\n"
            summary += f"Numero elementi: {len(root.findall('.//*')) + 1}\n"
            summary += f"Profondità massima: {self.get_xml_depth(root)}\n"

            self.result_queue.put(("text", summary))

        except ET.ParseError as e:
            self.result_queue.put(("error", f"Errore nel parsing XML: {str(e)}"))

    def analyze_json(self, file_path):
        """Analizza un file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Analisi struttura
            def process_json(obj, parent=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        item = self.tree.insert(parent, "end", text=key)
                        process_json(value, item)
                elif isinstance(obj, list):
                    for i, value in enumerate(obj):
                        item = self.tree.insert(parent, "end", text=f"[{i}]")
                        process_json(value, item)
                else:
                    self.tree.insert(parent, "end", text=str(obj))

            self.result_queue.put(("json", data))

            # Statistiche
            filename = os.path.basename(file_path)
            summary = f"\nAnalisi JSON: {filename}\n"
            summary += f"Dimensione: {os.path.getsize(file_path)} bytes\n"
            summary += self.analyze_json_structure(data)

            self.result_queue.put(("text", summary))

        except json.JSONDecodeError as e:
            self.result_queue.put(("error", f"Errore nel parsing JSON: {str(e)}"))

    def analyze_text(self, file_path):
        """Analizza un file di testo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Statistiche base
            filename = os.path.basename(file_path)
            summary = f"\nAnalisi testo: {filename}\n"
            summary += f"Numero righe: {len(content.splitlines())}\n"
            summary += f"Numero parole: {len(content.split())}\n"
            summary += f"Numero caratteri: {len(content)}\n"

            # Estrai numeri se richiesto
            if self.extract_numbers_var.get():
                numbers = re.findall(r'\b\d+(?:\.\d+)?\b', content)
                if numbers:
                    summary += f"\nNumeri trovati: {len(numbers)}\n"
                    if len(numbers) <= 10:  # Mostra solo i primi 10 numeri
                        summary += "Valori: " + ", ".join(numbers) + "\n"

            self.result_queue.put(("text", summary))

        except Exception as e:
            self.result_queue.put(("error", f"Errore nell'analisi del testo: {str(e)}"))

    def get_xml_depth(self, element, level=1):
        """Calcola la profondità massima di un elemento XML"""
        return max([level] + [self.get_xml_depth(child, level + 1)
                              for child in element])

    def analyze_json_structure(self, data, level=0):
        """Analizza la struttura di un oggetto JSON"""
        summary = ""
        if isinstance(data, dict):
            summary += f"Oggetto con {len(data)} chiavi\n"
            for key, value in data.items():
                summary += "  " * level + f"- {key}: "
                summary += self.analyze_json_structure(value, level + 1)
        elif isinstance(data, list):
            summary += f"Array con {len(data)} elementi\n"
            if len(data) > 0:
                summary += self.analyze_json_structure(data[0], level + 1)
        else:
            summary += f"Valore di tipo {type(data).__name__}\n"
        return summary

    def update_progress(self, value, text):
        """Aggiorna la barra di progresso"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.frame.update_idletasks()

    def export_excel(self):
        """Esporta i risultati in Excel"""
        try:
            if not self.result_text.get(1.0, tk.END).strip():
                messagebox.showwarning("Attenzione", "Non ci sono risultati da esportare!")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"analisi_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )

            if file_path:
                # Crea DataFrame
                data = []
                current_file = None

                for line in self.result_text.get(1.0, tk.END).split('\n'):
                    if line.startswith('Analisi'):
                        current_file = line.split(': ')[1]
                    elif ':' in line and current_file:
                        key, value = line.split(':', 1)
                        data.append({
                            'File': current_file,
                            'Parametro': key.strip(),
                            'Valore': value.strip()
                        })

                df = pd.DataFrame(data)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Successo", "Report Excel salvato con successo!")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'esportazione: {str(e)}")

    def save_report(self):
        """Salva il report in formato testo"""
        try:
            if not self.result_text.get(1.0, tk.END).strip():
                messagebox.showwarning("Attenzione", "Non ci sono risultati da salvare!")
                return

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=f"report_analisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.get(1.0, tk.END))
                messagebox.showinfo("Successo", "Report salvato con successo!")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio: {str(e)}")

    def copy_results(self):
        """Copia i risultati negli appunti"""
        text = self.result_text.get(1.0, tk.END).strip()
        if text:
            self.frame.clipboard_clear()
            self.frame.clipboard_append(text)
            self.frame.update()
            messagebox.showinfo("Info", "Risultati copiati negli appunti!")
        else:
            messagebox.showwarning("Attenzione", "Non ci sono risultati da copiare!")

    def search(self, text):
        """Ricerca nel contenuto (per ricerca globale)"""
        results = []

        # Cerca nei risultati testuali
        content = self.result_text.get(1.0, tk.END).lower()
        if text.lower() in content:
            matches = []
            for line in content.split('\n'):
                if text.lower() in line.lower():
                    matches.append(line.strip())
            if matches:
                results.append(("Analisi File", "\n".join(matches)))

        # Cerca nella struttura ad albero
        def search_tree(item=""):
            found = []
            item_text = self.tree.item(item, "text").lower()

            if text.lower() in item_text:
                found.append(item_text)

            for child in self.tree.get_children(item):
                found.extend(search_tree(child))

            return found

        tree_results = search_tree()
        if tree_results:
            results.append(("Struttura File", "\n".join(tree_results)))

        return results

    def process_result_queue(self):
        """Processa i risultati nella coda"""
        try:
            while True:
                result_type, data = self.result_queue.get_nowait()

                if result_type == "text":
                    self.result_text.insert(tk.END, data)
                elif result_type == "tree":
                    self.update_tree(data)
                elif result_type == "json":
                    self.update_tree_json(data)
                elif result_type == "error":
                    self.result_text.insert(tk.END, f"\nErrore: {data}\n")

                self.result_text.see(tk.END)

        except Queue.Empty:
            pass
        finally:
            # Programma il prossimo controllo della coda
            self.frame.after(100, self.process_result_queue)

    def update_tree(self, data, parent=""):
        """Aggiorna la struttura ad albero per XML"""
        item = self.tree.insert(parent, "end", text=data["tag"])

        # Aggiungi attributi
        if data["attributes"]:
            attrs = self.tree.insert(item, "end", text="Attributi")
            for key, value in data["attributes"].items():
                self.tree.insert(attrs, "end", text=f"{key}: {value}")

        # Aggiungi testo
        if data["text"]:
            self.tree.insert(item, "end", text=f"Testo: {data['text']}")

        # Aggiungi figli ricorsivamente
        for child in data["children"]:
            self.update_tree(child, item)

    def update_tree_json(self, data, parent=""):
        """Aggiorna la struttura ad albero per JSON"""
        if isinstance(data, dict):
            for key, value in data.items():
                item = self.tree.insert(parent, "end", text=key)
                self.update_tree_json(value, item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = self.tree.insert(parent, "end", text=f"[{i}]")
                self.update_tree_json(value, item)
        else:
            self.tree.insert(parent, "end", text=str(data))

    def get_file_info(self, file_path):
        """Ottiene informazioni base sul file"""
        try:
            stats = os.stat(file_path)
            return {
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime),
                "modified": datetime.fromtimestamp(stats.st_mtime),
                "accessed": datetime.fromtimestamp(stats.st_atime)
            }
        except Exception as e:
            return {"error": str(e)}