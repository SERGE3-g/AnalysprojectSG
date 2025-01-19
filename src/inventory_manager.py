import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from datetime import datetime
import qrcode
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from openpyxl import Workbook
from openpyxl.drawing.image import Image
import os

class InventoryTab(ttk.Frame):
    def __init__(self, parent, current_user, user_role):
        """
        Inizializza il tab inventario come Frame, ereditando da ttk.Frame.
        """
        super().__init__(parent)
        self.current_user = current_user
        self.user_role = user_role

        # Configurazione database
        self.DB_NAME = "data/inventario.db"
        self.create_database()

        # Liste per dropdown
        self.categorie = [
            "Giocattoli per la prima infanzia", "Bambole e accessori", "Veicoli",
            "Costruzioni", "Giochi creativi", "Giochi di società",
            "Giocattoli scientifici", "Giocattoli elettronici", "Giocattoli all'aperto",
            "Peluche", "Figurines", "Giocattoli di ruolo"
        ]
        self.marche = [
            "LEGO", "Mattel", "Hasbro", "Clementoni", "Chicco", "Ravensburger",
            "Playmobil", "Giochi Preziosi"
        ]

        # Costruisce interfaccia
        self.create_gui()

        # Carica in tabella
        self.refresh_table()

    def create_database(self):
        """Crea il database e la tabella inventario se non esiste."""
        os.makedirs('data', exist_ok=True)
        conn = sqlite3.connect(self.DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT NOT NULL,
                marca TEXT,
                quantita INTEGER NOT NULL,
                prezzo_acquisto REAL NOT NULL,
                prezzo_vendita REAL NOT NULL,
                iva REAL NOT NULL,
                scaffale TEXT NOT NULL,
                data_controllo TEXT NOT NULL,
                codice_barre TEXT NOT NULL,
                note TEXT
            )
        """)

        conn.commit()
        conn.close()

    def create_gui(self):
        """Costruisce l'interfaccia grafica all'interno del frame."""
        # Form di inserimento
        self.create_input_form()

        # Tabella prodotti
        self.create_products_table()

        # Pulsanti di azione
        self.create_action_buttons()

    def create_input_form(self):
        """Crea il form di inserimento prodotti."""
        input_frame = ttk.LabelFrame(self, text="Inserimento Prodotto", padding=10)
        input_frame.pack(fill='x', padx=5, pady=5)

        self.entries = {}
        row = 0

        # Nome
        ttk.Label(input_frame, text="Nome:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['nome'] = ttk.Entry(input_frame)
        self.entries['nome'].grid(row=row, column=1, sticky='ew')

        # Categoria
        row += 1
        ttk.Label(input_frame, text="Categoria:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['categoria'] = ttk.Combobox(input_frame, values=self.categorie)
        self.entries['categoria'].grid(row=row, column=1, sticky='ew')

        # Marca
        row += 1
        ttk.Label(input_frame, text="Marca:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['marca'] = ttk.Combobox(input_frame, values=self.marche)
        self.entries['marca'].grid(row=row, column=1, sticky='ew')

        # Quantità
        row += 1
        ttk.Label(input_frame, text="Quantità:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['quantita'] = ttk.Entry(input_frame)
        self.entries['quantita'].grid(row=row, column=1, sticky='ew')

        # Prezzo acquisto
        row += 1
        ttk.Label(input_frame, text="Prezzo Acquisto:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['prezzo_acquisto'] = ttk.Entry(input_frame)
        self.entries['prezzo_acquisto'].grid(row=row, column=1, sticky='ew')

        # IVA
        row += 1
        ttk.Label(input_frame, text="IVA (%):").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['iva'] = ttk.Entry(input_frame)
        self.entries['iva'].grid(row=row, column=1, sticky='ew')

        # Scaffale
        row += 1
        ttk.Label(input_frame, text="Scaffale:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['scaffale'] = ttk.Entry(input_frame)
        self.entries['scaffale'].grid(row=row, column=1, sticky='ew')

        # Data controllo
        row += 1
        ttk.Label(input_frame, text="Data Controllo:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['data_controllo'] = ttk.Entry(input_frame)
        self.entries['data_controllo'].insert(0, datetime.now().strftime('%d/%m/%Y'))
        self.entries['data_controllo'].grid(row=row, column=1, sticky='ew')

        # Note
        row += 1
        ttk.Label(input_frame, text="Note:").grid(row=row, column=0, sticky='e', padx=5, pady=2)
        self.entries['note'] = ttk.Entry(input_frame)
        self.entries['note'].grid(row=row, column=1, sticky='ew')

        # Configurazione griglia
        input_frame.columnconfigure(1, weight=1)

    def create_products_table(self):
        """Crea la tabella dei prodotti."""
        table_frame = ttk.LabelFrame(self, text="Prodotti", padding=10)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        columns = (
            'id', 'nome', 'categoria', 'marca', 'quantita',
            'prezzo_acquisto', 'prezzo_vendita', 'iva',
            'scaffale', 'data_controllo', 'codice_barre'
        )

        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=100)

        y_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

    def create_action_buttons(self):
        """Crea i pulsanti delle azioni."""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(button_frame, text="Aggiungi",
                   command=self.add_product).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Modifica",
                   command=self.edit_product).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Elimina",
                   command=self.delete_product).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Genera PDF",
                   command=self.generate_pdf).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Esporta Excel",
                   command=self.export_excel).pack(side='left', padx=2)

    def refresh_table(self):
        """Aggiorna la tabella dei prodotti dal database."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(self.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventario ORDER BY id DESC")
        for row in cursor.fetchall():
            self.tree.insert("", 0, values=row)

        conn.close()

    def add_product(self):
        """Aggiunge un nuovo prodotto nel database e aggiorna la tabella."""
        try:
            nome = self.entries['nome'].get().strip()
            categoria = self.entries['categoria'].get().strip()
            marca = self.entries['marca'].get().strip()
            quantita = int(self.entries['quantita'].get())
            prezzo_acquisto = float(self.entries['prezzo_acquisto'].get())
            iva = float(self.entries['iva'].get())
            scaffale = self.entries['scaffale'].get().strip()
            data_controllo = self.entries['data_controllo'].get().strip()
            note = self.entries['note'].get().strip()

            if not all([nome, categoria, quantita, prezzo_acquisto, iva, scaffale, data_controllo]):
                raise ValueError("Tutti i campi sono obbligatori (tranne Note).")

            # Calcola prezzo di vendita
            prezzo_vendita = round(prezzo_acquisto + (prezzo_acquisto * iva / 100), 2)

            # Genera codice a barre
            codice_barre = self.generate_barcode()

            # Inserisci nel DB
            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inventario (
                    nome, categoria, marca, quantita, 
                    prezzo_acquisto, prezzo_vendita, iva, 
                    scaffale, data_controllo, codice_barre, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nome, categoria, marca, quantita,
                prezzo_acquisto, prezzo_vendita, iva,
                scaffale, data_controllo, codice_barre, note
            ))
            conn.commit()
            conn.close()

            # Genera il QR code
            self.generate_qrcode(codice_barre, nome)

            self.refresh_table()
            messagebox.showinfo("Successo", "Prodotto aggiunto con successo!")

        except ValueError as e:
            messagebox.showerror("Errore", str(e))
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'inserimento: {str(e)}")

    def generate_barcode(self):
        """Genera un codice a barre univoco (stringa)."""
        conn = sqlite3.connect(self.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventario")
        count = cursor.fetchone()[0]
        conn.close()
        return str(100000000000 + count + 1)

    def generate_qrcode(self, code, name):
        """Genera un QR code e lo salva in /qrcodes."""
        os.makedirs('qrcodes', exist_ok=True)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        file_path = f"qrcodes/{name}_{code}.png"
        img.save(file_path)

    def edit_product(self):
        """Modifica un prodotto selezionato."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un prodotto da modificare.")
            return

        item = self.tree.item(selected[0])
        product_id = item['values'][0]

        edit_window = tk.Toplevel(self)
        edit_window.title("Modifica Prodotto")
        edit_window.geometry("500x600")

        edit_frame = ttk.LabelFrame(edit_window, text="Modifica Dati", padding=10)
        edit_frame.pack(fill='both', expand=True, padx=5, pady=5)

        row = 0
        edit_entries = {}

        # Mappa campo->indice in item['values']
        field_index = {
            'nome': 1,
            'categoria': 2,
            'marca': 3,
            'quantita': 4,
            'prezzo_acquisto': 5,
            'prezzo_vendita': 6,  # non lo modifichiamo direttamente
            'iva': 7,
            'scaffale': 8,
            'data_controllo': 9,
            'codice_barre': 10,  # non lo modifichiamo direttamente
            'note': 11
        }

        # Campi da modificare
        fields_to_edit = [
            'nome', 'categoria', 'marca', 'quantita',
            'prezzo_acquisto', 'iva', 'scaffale',
            'data_controllo', 'note'
        ]

        for field in fields_to_edit:
            ttk.Label(edit_frame, text=field.title() + ":").grid(
                row=row, column=0, sticky='e', padx=5, pady=2
            )
            if field in ['categoria']:
                widget = ttk.Combobox(edit_frame, values=self.categorie)
            elif field in ['marca']:
                widget = ttk.Combobox(edit_frame, values=self.marche)
            else:
                widget = ttk.Entry(edit_frame)

            # Inserisci valore esistente
            index = field_index[field]
            old_value = item['values'][index]
            if old_value is not None:
                widget.insert(0, str(old_value))

            widget.grid(row=row, column=1, sticky='ew', padx=5)
            edit_entries[field] = widget
            row += 1

        edit_frame.columnconfigure(1, weight=1)

        def save_changes():
            try:
                nome = edit_entries['nome'].get().strip()
                categoria = edit_entries['categoria'].get().strip()
                marca = edit_entries['marca'].get().strip()
                quantita = int(edit_entries['quantita'].get())
                prezzo_acquisto = float(edit_entries['prezzo_acquisto'].get())
                iva = float(edit_entries['iva'].get())
                scaffale = edit_entries['scaffale'].get().strip()
                data_controllo = edit_entries['data_controllo'].get().strip()
                note = edit_entries['note'].get().strip()

                if not all([nome, categoria, quantita, prezzo_acquisto, iva, scaffale, data_controllo]):
                    raise ValueError("Tutti i campi sono obbligatori (tranne Note).")

                # Calcolo nuovo prezzo di vendita
                prezzo_vendita = round(prezzo_acquisto + (prezzo_acquisto * iva / 100), 2)

                # Aggiorna DB
                conn = sqlite3.connect(self.DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE inventario 
                    SET nome=?, categoria=?, marca=?, quantita=?,
                        prezzo_acquisto=?, prezzo_vendita=?, iva=?,
                        scaffale=?, data_controllo=?, note=?
                    WHERE id=?
                """, (
                    nome, categoria, marca, quantita,
                    prezzo_acquisto, prezzo_vendita, iva,
                    scaffale, data_controllo, note, product_id
                ))
                conn.commit()
                conn.close()

                self.refresh_table()
                edit_window.destroy()
                messagebox.showinfo("Successo", "Prodotto aggiornato con successo!")
            except ValueError as e:
                messagebox.showerror("Errore", str(e))
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'aggiornamento: {str(e)}")

        button_frame = ttk.Frame(edit_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Salva",
                   command=save_changes).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Annulla",
                   command=edit_window.destroy).pack(side='left')

    def delete_product(self):
        """Elimina il prodotto selezionato."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un prodotto da eliminare.")
            return

        item = self.tree.item(selected[0])
        product_id = item['values'][0]

        response = messagebox.askyesno(
            "Conferma eliminazione",
            "Sei sicuro di voler eliminare il prodotto selezionato?"
        )
        if not response:
            return

        try:
            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()

            self.refresh_table()
            messagebox.showinfo("Successo", "Prodotto eliminato con successo!")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'eliminazione: {str(e)}")

    def generate_pdf(self):
        """Genera un report PDF dell'inventario."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            if not file_path:
                return

            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome, categoria, marca, quantita,
                       prezzo_acquisto, prezzo_vendita, iva,
                       scaffale, data_controllo
                FROM inventario
                ORDER BY categoria, nome
            """)
            data = cursor.fetchall()
            conn.close()

            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib import colors

            doc = SimpleDocTemplate(file_path)
            elements = []

            headers = [
                "Nome", "Categoria", "Marca", "Quantità",
                "Prezzo Acquisto", "Prezzo Vendita", "IVA",
                "Scaffale", "Data Controllo"
            ]
            table_data = [headers]
            table_data.extend(data)

            # Calcolo totali
            total_items = sum(row[3] for row in data)
            total_value = sum(row[3] * row[4] for row in data)  # quantità * prezzo_acquisto
            table_data.append([
                "TOTALE", "", "", total_items,
                total_value, "", "", "", ""
            ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BOX', (0, 0), (-1, -1), 2, colors.black),
            ]))

            elements.append(table)
            doc.build(elements)

            messagebox.showinfo("Successo", "Report PDF generato con successo!")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nella generazione del PDF: {str(e)}")

    def export_excel(self):
        """Esporta l'inventario in un file Excel."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            if not file_path:
                return

            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventario ORDER BY categoria, nome")
            data = cursor.fetchall()
            conn.close()

            from openpyxl import Workbook
            from openpyxl.drawing.image import Image

            wb = Workbook()
            ws = wb.active
            ws.title = "Inventario"

            headers = [
                "ID", "Nome", "Categoria", "Marca", "Quantità",
                "Prezzo Acquisto", "Prezzo Vendita", "IVA",
                "Scaffale", "Data Controllo", "Codice Barre", "Note"
            ]
            ws.append(headers)

            # Aggiunge i dati
            for row in data:
                ws.append(row)

            # Inserisce i QR code se presenti
            for idx, row in enumerate(data, start=2):
                nome = row[1]
                codice = row[10]
                qr_path = f"qrcodes/{nome}_{codice}.png"
                if os.path.exists(qr_path):
                    img = Image(qr_path)
                    cell = ws.cell(row=idx, column=len(headers)+1)
                    ws.add_image(img, cell.coordinate)

            # Adatta larghezza colonne
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) for cell in column_cells if cell.value)
                ws.column_dimensions[column_cells[0].column_letter].width = length + 2

            wb.save(file_path)
            messagebox.showinfo("Successo", "File Excel generato con successo!")

        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'esportazione Excel: {str(e)}")

    def clear_form(self):
        """Pulisce i campi di input."""
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.delete(0, tk.END)
            elif isinstance(entry, ttk.Combobox):
                entry.set("")

        self.entries['data_controllo'].delete(0, tk.END)
        self.entries['data_controllo'].insert(0, datetime.now().strftime('%d/%m/%Y'))

    def search(self, text):
        """
        Ricerca nei prodotti per la 'ricerca globale'
        e ritorna una lista di tuple (nome_area, risultato).
        """
        results = []

        conn = sqlite3.connect(self.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM inventario 
            WHERE nome LIKE ? OR categoria LIKE ? OR marca LIKE ? OR note LIKE ?
        """, (f"%{text}%", f"%{text}%", f"%{text}%", f"%{text}%"))

        for row in cursor.fetchall():
            # row: (id, nome, categoria, marca, quantita, prezzo_acquisto, ...)
            results.append((
                "Prodotto",
                f"{row[1]} (Cat: {row[2]}) - Marca: {row[3]} - Prezzo: {row[6]:.2f}"
            ))

        conn.close()
        return results
