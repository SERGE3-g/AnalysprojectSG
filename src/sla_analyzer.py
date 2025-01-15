import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from datetime import datetime
import os
from docx import Document
from docx.shared import RGBColor
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


class SLATab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Analisi SLA')

        # Variabili per i file
        self.files = {
            'SLA1_IN': {'path': None, 'label': None, 'button': None},
            'SLA4_IN': {'path': None, 'label': None, 'button': None},
            'SLA5_IN': {'path': None, 'label': None, 'button': None},
            'SLA6_IN': {'path': None, 'label': None, 'button': None},
            'SLA1_OUT': {'path': None, 'label': None, 'button': None},
            'SLA2_OUT': {'path': None, 'label': None, 'button': None},
            'SLA3_OUT': {'path': None, 'label': None, 'button': None}
        }

        # Thresholds per ogni SLA
        self.thresholds = {
            'SLA2': 1400,
            'SLA3': 600,
            'SLA4': 800,
            'SLA5': 600,
            'SLA6': 800
        }

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """Crea tutti i widget necessari"""
        # Titolo
        self.title = ttk.Label(
            self.frame,
            text="Analisi SLA",
            font=('Helvetica', 16, 'bold')
        )

        # Frame per file selection
        self.file_frame = ttk.LabelFrame(self.frame, text="Selezione File", padding=10)

        # Creazione labels e buttons per ogni file
        for sla_key in self.files.keys():
            self.files[sla_key]['label'] = ttk.Label(self.file_frame, text=f"{sla_key}:")
            self.files[sla_key]['button'] = ttk.Button(
                self.file_frame,
                text="Seleziona File",
                command=lambda k=sla_key: self.select_file(k)
            )

        # Frame per le opzioni
        self.options_frame = ttk.LabelFrame(self.frame, text="Opzioni", padding=10)

        # Selezione mese
        self.month_label = ttk.Label(self.options_frame, text="Mese:")
        self.month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        self.month_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.month_var,
            values=[datetime.strptime(str(i), "%m").strftime("%B") for i in range(1, 13)],
            state="readonly",
            width=15
        )

        # Selezione anno
        self.year_label = ttk.Label(self.options_frame, text="Anno:")
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.year_entry = ttk.Entry(
            self.options_frame,
            textvariable=self.year_var,
            width=6
        )

        # Frame per i bottoni
        self.buttons_frame = ttk.Frame(self.frame)
        self.generate_button = ttk.Button(
            self.buttons_frame,
            text="Genera Report",
            command=self.generate_report
        )
        self.export_csv_btn = ttk.Button(
            self.buttons_frame,
            text="Esporta CSV",
            command=self.export_to_csv
        )
        self.preview_btn = ttk.Button(
            self.buttons_frame,
            text="Anteprima",
            command=self.show_preview
        )
        self.plot_btn = ttk.Button(
            self.buttons_frame,
            text="Mostra Grafico",
            command=self.plot_data
        )

        # Crea frame visualizzazione
        self.viz_frame = ttk.Notebook(self.frame)

        # Tab per il log
        self.log_frame = ttk.Frame(self.viz_frame)
        self.viz_frame.add(self.log_frame, text="Log")

        # Text widget per il log con scrollbar
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(
            self.log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        # Configura tag per il log
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")

        # Tab per anteprima
        self.preview_frame = ttk.Frame(self.viz_frame)
        self.viz_frame.add(self.preview_frame, text="Anteprima")

        # Treeview per anteprima con scrollbars
        self.preview_tree = ttk.Treeview(self.preview_frame)
        preview_scroll_y = ttk.Scrollbar(
            self.preview_frame,
            orient="vertical",
            command=self.preview_tree.yview
        )
        preview_scroll_x = ttk.Scrollbar(
            self.preview_frame,
            orient="horizontal",
            command=self.preview_tree.xview
        )
        self.preview_tree.configure(
            yscrollcommand=preview_scroll_y.set,
            xscrollcommand=preview_scroll_x.set
        )

        # Layout per preview
        self.preview_tree.pack(side='left', fill='both', expand=True)
        preview_scroll_y.pack(side='right', fill='y')
        preview_scroll_x.pack(side='bottom', fill='x')

        # Tab per grafico
        self.graph_frame = ttk.Frame(self.viz_frame)
        self.viz_frame.add(self.graph_frame, text="Grafico")

    def setup_layout(self):
        """Organizza il layout dei widget"""
        # Titolo
        self.title.pack(pady=10)

        # Frame file selection
        self.file_frame.pack(fill='x', padx=10, pady=5)
        for i, (_, widgets) in enumerate(self.files.items()):
            widgets['label'].grid(row=i, column=0, sticky='w', padx=5, pady=2)
            widgets['button'].grid(row=i, column=1, sticky='w', padx=5, pady=2)

        # Frame opzioni
        self.options_frame.pack(fill='x', padx=10, pady=5)
        self.month_label.pack(side='left', padx=5)
        self.month_combo.pack(side='left', padx=5)
        self.year_label.pack(side='left', padx=5)
        self.year_entry.pack(side='left', padx=5)

        # Frame bottoni
        self.buttons_frame.pack(fill='x', padx=10, pady=5)
        self.generate_button.pack(side='left', padx=5)
        self.export_csv_btn.pack(side='left', padx=5)
        self.preview_btn.pack(side='left', padx=5)
        self.plot_btn.pack(side='left', padx=5)

        # Frame log e visualizzazioni
        self.viz_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.log_text.pack(side='left', fill='both', expand=True)
        self.log_scroll.pack(side='right', fill='y')

    def show_preview(self):
        """Mostra l'anteprima dei dati"""
        try:
            # Pulisci la vista precedente
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)

            # Seleziona il tab dell'anteprima
            self.viz_frame.select(self.preview_frame)

            # Cerca il primo file disponibile
            for file_key, file_data in self.files.items():
                if file_data['path']:
                    df = pd.read_csv(file_data['path'], sep=';', nrows=100)

                    # Configura le colonne
                    self.preview_tree['columns'] = list(df.columns)
                    for col in df.columns:
                        self.preview_tree.heading(col, text=col)
                        self.preview_tree.column(col, width=100)

                    # Inserisci i dati
                    for idx, row in df.iterrows():
                        self.preview_tree.insert('', 'end', values=list(row))

                    self.log(f"Anteprima caricata per {file_key}", "success")
                    return

            self.log("Nessun file disponibile per l'anteprima", "warning")

        except Exception as e:
            self.log(f"Errore nell'anteprima: {str(e)}", "error")

    def plot_data(self):
        """Visualizza i dati in un grafico"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            # Pulisci il frame del grafico
            for widget in self.graph_frame.winfo_children():
                widget.destroy()

            # Seleziona il tab del grafico
            self.viz_frame.select(self.graph_frame)

            # Crea figura
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plotta dati per ogni SLA
            legend_items = []
            for sla_name, threshold in self.thresholds.items():
                file_key = f"{sla_name}_OUT" if sla_name in ['SLA2', 'SLA3'] else f"{sla_name}_IN"
                if self.files[file_key]['path']:
                    try:
                        df = pd.read_csv(self.files[file_key]['path'], sep=';')
                        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M', dayfirst=True)
                        df[sla_name] = pd.to_numeric(df[sla_name], errors='coerce')

                        # Plotta linea e threshold
                        line = ax.plot(df['Time'], df[sla_name], label=f"SLA {sla_name}", marker='o', markersize=2)
                        ax.axhline(y=threshold, color=line[0].get_color(), linestyle='--', alpha=0.5)
                        legend_items.append(f"{sla_name} (Soglia: {threshold})")

                    except Exception as e:
                        self.log(f"Errore nel plotting di {sla_name}: {str(e)}", "error")
                        continue

            # Configura grafico
            ax.set_title('Analisi SLA', pad=20, fontsize=14)
            ax.set_xlabel('Data/Ora', labelpad=10)
            ax.set_ylabel('Valore', labelpad=10)
            ax.legend(legend_items)
            ax.grid(True, linestyle='--', alpha=0.7)

            # Ruota etichette date
            fig.autofmt_xdate()

            # Personalizza aspetto
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Crea canvas e mostra
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

            self.log("Grafico generato con successo", "success")

        except Exception as e:
            self.log(f"Errore nella generazione del grafico: {str(e)}", "error")

    def export_to_csv(self):
        """Esporta i risultati in CSV"""
        try:
            # Richiedi il percorso per il salvataggio
            output_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"SLA_Analysis_{self.month_var.get()}_{self.year_var.get()}.csv"
            )

            if not output_path:
                return

            # Preparazione dati
            all_data = []
            for sla_name, threshold in self.thresholds.items():
                file_key = f"{sla_name}_OUT" if sla_name in ['SLA2', 'SLA3'] else f"{sla_name}_IN"
                if self.files[file_key]['path']:
                    df = pd.read_csv(self.files[file_key]['path'], sep=';')
                    df['SLA_Name'] = sla_name
                    df['Threshold'] = threshold
                    df['Source_File'] = os.path.basename(self.files[file_key]['path'])
                    all_data.append(df)

            if all_data:
                # Combina tutti i dati
                final_df = pd.concat(all_data, ignore_index=True)

                # Aggiunge info aggiuntive
                final_df['Analysis_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                final_df['Month'] = self.month_var.get()
                final_df['Year'] = self.year_var.get()

                # Salva CSV
                final_df.to_csv(output_path, index=False, sep=';')
                self.log(f"Dati esportati in: {output_path}", "success")
                messagebox.showinfo("Successo", f"Dati esportati in: {output_path}")
            else:
                self.log("Nessun dato da esportare", "warning")

        except Exception as e:
            self.log(f"Errore nell'esportazione CSV: {str(e)}", "error")
            messagebox.showerror("Errore", str(e))

    def generate_docx_report(self, results, output_path):
        """Genera il report Word"""
        try:
            # Debug log per vedere la struttura dei dati
            self.log(f"Struttura results: {results}")

            doc = Document()

            # Titolo
            doc.add_heading(
                f'Report SLA - {self.month_var.get()} {self.year_var.get()}', 0
            ).alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Data generazione
            doc.add_paragraph(f"Data generazione: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            doc.add_paragraph()

            # Analisi per ogni SLA
            for sla_name, data in results.items():
                try:
                    # Verifica che data contenga tutte le chiavi necessarie
                    required_keys = ['total_records', 'compliant_records', 'non_compliant_records']
                    missing_keys = [key for key in required_keys if key not in data]
                    if missing_keys:
                        self.log(f"Dati mancanti per {sla_name}: {missing_keys}", "error")
                        continue  # Salta questo SLA e continua con il prossimo

                    # Prova prima con _IN
                    file_key = f"{sla_name}_IN"
                    if file_key not in self.files:
                        file_key = f"{sla_name}_OUT"

                    if file_key not in self.files:
                        self.log(f"Nessun file trovato per {sla_name} (cercato {file_key})", "error")
                        continue  # Salta questo SLA e continua con il prossimo

                    # Log per debug
                    self.log(f"Generando report per {sla_name} con chiave {file_key}")

                    # Intestazione sezione
                    doc.add_heading(f'Analisi {sla_name}', level=1)

                    # Informazioni generali
                    doc.add_paragraph(f"Soglia: {self.thresholds[sla_name]}")
                    doc.add_paragraph(f"File analizzato: {os.path.basename(self.files[file_key]['path'])}")
                    doc.add_paragraph()

                    # Statistiche principali
                    doc.add_paragraph(f"Totale record analizzati: {data['total_records']}")
                    doc.add_paragraph(f"Record conformi: {data['compliant_records']}")
                    doc.add_paragraph(f"Record non conformi: {data['non_compliant_records']}")
                    doc.add_paragraph()

                    # Percentuale di conformità
                    if data['total_records'] > 0:
                        compliance_percentage = (data['compliant_records'] / data['total_records'] * 100)
                    else:
                        compliance_percentage = 0
                    doc.add_paragraph(f"Percentuale di conformità: {compliance_percentage:.2f}%")

                    # Stato SLA
                    threshold = float(self.thresholds[sla_name])
                    status = "RISPETTATO" if compliance_percentage >= threshold else "NON RISPETTATO"
                    p = doc.add_paragraph(f"Stato SLA: {status}")

                    # Applica formattazione colorata allo stato
                    run = p.runs[-1]
                    run.font.color.rgb = RGBColor(0, 128, 0) if status == "RISPETTATO" else RGBColor(255, 0, 0)
                    run.font.bold = True

                    # Aggiungi una linea vuota tra le sezioni
                    doc.add_paragraph()

                    # Se ci sono record non conformi, aggiungi i dettagli
                    if data.get('non_compliant_records', 0) > 0 and 'non_compliant_details' in data and data[
                        'non_compliant_details']:
                        doc.add_heading("Dettaglio record non conformi", level=2)

                        # Verifica che ci siano dettagli e che abbiano la struttura corretta
                        if data['non_compliant_details'] and isinstance(data['non_compliant_details'], list):
                            # Crea tabella per i dettagli
                            table = doc.add_table(rows=1, cols=len(data['non_compliant_details'][0]))
                            table.style = 'Table Grid'

                            # Intestazioni tabella
                            headers = list(data['non_compliant_details'][0].keys())
                            header_cells = table.rows[0].cells
                            for i, header in enumerate(headers):
                                header_cells[i].text = header
                                header_cells[i].paragraphs[0].runs[0].font.bold = True

                            # Aggiungi righe con i dettagli
                            for detail in data['non_compliant_details']:
                                row_cells = table.add_row().cells
                                for i, key in enumerate(headers):
                                    row_cells[i].text = str(detail[key])

                        doc.add_paragraph()

                except Exception as e:
                    self.log(f"Errore nella generazione della sezione per {sla_name}: {str(e)}", "error")
                    # Continua con il prossimo SLA invece di interrompere tutto
                    continue

            # Salva il documento solo se abbiamo generato almeno una sezione
            doc.save(output_path)
            return True

        except Exception as e:
            self.log(f"Errore nella generazione del report Word: {str(e)}", "error")
            raise

    def select_file(self, sla_key):
        """Gestisce la selezione dei file"""
        filename = filedialog.askopenfilename(
            title=f"Seleziona file {sla_key}",
            filetypes=[("CSV files", "*.csv"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.files[sla_key]['path'] = filename
            self.log(f"Selezionato {sla_key}: {filename}", "success")

    def log(self, message, level="info"):
        """Aggiunge un messaggio al log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"{timestamp}: {message}\n", level)
        self.log_text.see(tk.END)

    def generate_report(self):
        """Genera il report completo"""
        try:
            # Verifica file
            missing_files = [key for key, data in self.files.items() if data['path'] is None]
            if missing_files:
                self.log(f"File mancanti: {', '.join(missing_files)}", "error")
                messagebox.showerror("Errore", "Seleziona tutti i file richiesti")
                return

            self.log("Inizio generazione report...", "info")

            # Crea directory reports se non esiste
            reports_dir = "reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)

            # Analisi dei dati
            results = {}
            for sla_name, threshold in self.thresholds.items():
                # Correggi la logica per determinare il file corretto
                file_key = f"{sla_name}_OUT" if sla_name in ['SLA2', 'SLA3'] else f"{sla_name}_IN"
                file_path = self.files[file_key]['path']

                try:
                    # Leggi e prepara i dati
                    df = pd.read_csv(file_path, sep=';')
                    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M', dayfirst=True)
                    df[sla_name] = pd.to_numeric(df[sla_name], errors='coerce')
                    df.set_index('Time', inplace=True)

                    # Analizza i dati
                    self.log(f"Analisi {sla_name}...", "info")
                    results[sla_name] = self.analyze_sla_data(df, threshold, sla_name)

                except Exception as e:
                    self.log(f"Errore nell'analisi di {sla_name}: {str(e)}", "error")
                    raise

            # Genera report
            output_path = os.path.join(reports_dir, f"SLA_Report_{self.month_var.get()}_{self.year_var.get()}.docx")
            self.generate_docx_report(results, output_path)

            self.log(f"Report generato con successo: {output_path}", "success")
            messagebox.showinfo("Successo", f"Report generato: {output_path}")

        except Exception as e:
            self.log(f"Errore nella generazione del report: {str(e)}", "error")
            messagebox.showerror("Errore", str(e))

    def analyze_sla_data(self, df, threshold, column_name):
        """Analizza i dati SLA"""
        try:
            # Log per debug
            self.log(f"Analisi dati per {column_name}")
            self.log(f"Dimensioni dataset: {df.shape}")
            self.log(f"Colonne presenti: {df.columns.tolist()}")

            daily_stats = []
            grouped = df.groupby(df.index.date)

            for date, group in grouped:
                total_minutes = len(group)
                # Assicurati che i valori siano numerici
                over_threshold = len(group[pd.to_numeric(group[column_name], errors='coerce') > threshold])
                percentage = ((total_minutes - over_threshold) / total_minutes) * 100

                daily_stats.append({
                    'Data': date,
                    'Min con Operatività oltre soglia': over_threshold,
                    'Min con Operatività': total_minutes,
                    '%': percentage
                })

            return pd.DataFrame(daily_stats)

        except Exception as e:
            self.log(f"Errore nell'analisi dei dati per {column_name}: {str(e)}", "error")
            raise

    def analyze_sla_data(self, df, threshold, column_name):
        """Analizza i dati SLA"""
        daily_stats = []
        grouped = df.groupby(df.index.date)

        for date, group in grouped:
            total_minutes = len(group)
            over_threshold = len(group[group[column_name] > threshold])
            percentage = ((total_minutes - over_threshold) / total_minutes) * 100

            daily_stats.append({
                'Data': date,
                'Min con Operatività oltre soglia': over_threshold,
                'Min con Operatività': total_minutes,
                '%': percentage
            })

        return pd.DataFrame(daily_stats)

    def search(self, text):
        """Implementa la ricerca globale nei dati SLA"""
        results = []
        search_text = text.lower()

        # Ricerca nel log
        log_content = self.log_text.get(1.0, tk.END).lower()
        if search_text in log_content:
            # Estrai le linee rilevanti che contengono il testo cercato
            relevant_lines = [line for line in log_content.split('\n') if search_text in line.lower()]
            if relevant_lines:
                results.append(("Log SLA", "\n".join(relevant_lines)))

        # Ricerca nei file caricati
        for file_key, file_data in self.files.items():
            if file_data['path']:
                try:
                    df = pd.read_csv(file_data['path'], sep=';')

                    # Cerca nelle colonne
                    for column in df.columns:
                        matches = df[df[column].astype(str).str.contains(search_text, case=False, na=False)]
                        if not matches.empty:
                            results.append((
                                f"File {file_key} - Colonna {column}",
                                f"Trovate {len(matches)} corrispondenze\n" +
                                matches.head().to_string()
                            ))

                except Exception as e:
                    self.log(f"Errore nella ricerca nel file {file_key}: {str(e)}", "error")

        # Ricerca nei risultati SLA
        try:
            for sla_name, threshold in self.thresholds.items():
                # Cerca nel nome SLA
                if search_text in sla_name.lower():
                    results.append((
                        "Configurazione SLA",
                        f"SLA: {sla_name}\nSoglia: {threshold}"
                    ))
        except Exception as e:
            self.log(f"Errore nella ricerca delle configurazioni SLA: {str(e)}", "error")

        # Ricerca nelle statistiche se disponibili
        try:
            stats_content = self.stats_text.get(1.0, tk.END).lower() if hasattr(self, 'stats_text') else ""
            if search_text in stats_content:
                relevant_stats = [line for line in stats_content.split('\n') if search_text in line.lower()]
                if relevant_stats:
                    results.append(("Statistiche SLA", "\n".join(relevant_stats)))
        except Exception as e:
            self.log(f"Errore nella ricerca delle statistiche: {str(e)}", "error")

        # Ricerca nel report generato più recentemente
        try:
            report_name = f"SLA_Report_{self.month_var.get()}_{self.year_var.get()}.docx"
            if os.path.exists(report_name):
                doc = Document(report_name)
                matching_paragraphs = []

                for paragraph in doc.paragraphs:
                    if search_text in paragraph.text.lower():
                        matching_paragraphs.append(paragraph.text)

                if matching_paragraphs:
                    results.append((
                        "Report SLA",
                        f"Trovate {len(matching_paragraphs)} corrispondenze nel report:\n" +
                        "\n".join(matching_paragraphs[:5]) +  # Mostra solo i primi 5 risultati
                        "\n..." if len(matching_paragraphs) > 5 else ""
                    ))
        except Exception as e:
            self.log(f"Errore nella ricerca nel report: {str(e)}", "error")

        # Se non ci sono risultati, aggiungi un messaggio informativo
        if not results:
            results.append(("Info", f"Nessun risultato trovato per: {text}"))

        # Aggiunge un log della ricerca
        self.log(f"Ricerca eseguita per: {text} - Trovati {len(results)} risultati", "info")

        return results