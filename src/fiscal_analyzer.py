import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import os
from datetime import datetime


class FiscalTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Codici Fiscali')

        # Dizionario dei comuni italiani con codici catastali
        self.load_city_codes()

        # Setup GUI
        self.create_gui()

    def load_city_codes(self):
        """Carica i codici dei comuni"""
        self.city_codes = {
            "Roma": "H501", "Milano": "F205", "Napoli": "F839",
            "Torino": "L219", "Palermo": "G273", "Genova": "D969",
            "Bologna": "A944", "Firenze": "D612", "Bari": "A662",
            "Catania": "C351", "Venezia": "L736", "Verona": "L781",
            "Latina": "E472", "Aprilia": "A341", "Bassiano": "A707",
            # Aggiungi altri comuni...
        }

    def create_gui(self):
        """Crea l'interfaccia grafica"""
        # Notebook interno per le sotto-schede
        self.tabs = ttk.Notebook(self.frame)
        self.tabs.pack(expand=True, fill='both', padx=5, pady=5)

        # Crea le sotto-schede
        self.create_generator_tab()
        self.create_analyzer_tab()
        self.create_validator_tab()

    def create_generator_tab(self):
        """Crea la scheda per la generazione del codice fiscale"""
        gen_frame = ttk.Frame(self.tabs)
        self.tabs.add(gen_frame, text='Genera Codice')

        # Frame principale con padding
        main_frame = ttk.LabelFrame(gen_frame, text="Dati Personali", padding=10)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Campi di input
        self.entries = {}
        fields = [
            ("Nome:", "name"),
            ("Cognome:", "surname"),
            ("Data Nascita (DD/MM/YYYY):", "birth_date")
        ]

        for i, (label, key) in enumerate(fields):
            frame = ttk.Frame(main_frame)
            frame.pack(fill='x', pady=2)
            ttk.Label(frame, text=label).pack(side='left')
            self.entries[key] = ttk.Entry(frame)
            self.entries[key].pack(side='right', expand=True, fill='x')

        # Genere
        gender_frame = ttk.Frame(main_frame)
        gender_frame.pack(fill='x', pady=2)
        ttk.Label(gender_frame, text="Genere:").pack(side='left')
        self.gender_var = tk.StringVar(value="M")
        ttk.Radiobutton(gender_frame, text="M", variable=self.gender_var,
                        value="M").pack(side='left')
        ttk.Radiobutton(gender_frame, text="F", variable=self.gender_var,
                        value="F").pack(side='left')

        # Comune
        city_frame = ttk.Frame(main_frame)
        city_frame.pack(fill='x', pady=2)
        ttk.Label(city_frame, text="Comune:").pack(side='left')
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(city_frame, textvariable=self.city_var,
                                       values=sorted(self.city_codes.keys()))
        self.city_combo.pack(side='right', expand=True, fill='x')

        # Campo ricerca comune
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=2)
        ttk.Label(search_frame, text="Cerca Comune:").pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_cities)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side='right',
                                                                   expand=True,
                                                                   fill='x')

        # Bottoni
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(button_frame, text="Genera",
                   command=self.generate_fiscal_code).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Pulisci",
                   command=self.clear_fields).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Copia",
                   command=self.copy_to_clipboard).pack(side='left', padx=5)

        # Area risultato
        result_frame = ttk.LabelFrame(gen_frame, text="Risultato", padding=10)
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.result_text = tk.Text(result_frame, height=8, wrap='word')
        self.result_text.pack(fill='both', expand=True)

    def create_analyzer_tab(self):
        """Crea la scheda per l'analisi dei file"""
        analyze_frame = ttk.Frame(self.tabs)
        self.tabs.add(analyze_frame, text='Analizza File Codice Fiscal')

        # Frame per caricamento file
        load_frame = ttk.LabelFrame(analyze_frame, text="Carica File", padding=10)
        load_frame.pack(fill='x', padx=5, pady=5)

        self.file_entry = ttk.Entry(load_frame)
        self.file_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))

        ttk.Button(load_frame, text="Sfoglia",
                   command=self.browse_files).pack(side='right')

        # Area risultati
        result_frame = ttk.LabelFrame(analyze_frame, text="Risultati", padding=10)
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbar per i risultati
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side='right', fill='y')

        self.analyze_text = tk.Text(result_frame, wrap='word',
                                    yscrollcommand=scrollbar.set)
        self.analyze_text.pack(fill='both', expand=True)
        scrollbar.config(command=self.analyze_text.yview)

    def create_validator_tab(self):
        """Crea la scheda per la validazione dei codici fiscali"""
        validate_frame = ttk.Frame(self.tabs)
        self.tabs.add(validate_frame, text='Valida Codice')

        # Frame per input
        input_frame = ttk.LabelFrame(validate_frame, text="Inserisci Codice",
                                     padding=10)
        input_frame.pack(fill='x', padx=5, pady=5)

        self.validate_entry = ttk.Entry(input_frame)
        self.validate_entry.pack(side='left', expand=True, fill='x', padx=(0, 5))

        ttk.Button(input_frame, text="Valida",
                   command=self.validate_fiscal_code).pack(side='right')

        # Area risultato validazione
        result_frame = ttk.LabelFrame(validate_frame, text="Risultato", padding=10)
        result_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.validate_text = tk.Text(result_frame, height=8, wrap='word')
        self.validate_text.pack(fill='both', expand=True)

    def filter_cities(self, *args):
        """Filtra i comuni in base al testo inserito"""
        search_text = self.search_var.get().lower()
        filtered_cities = [city for city in self.city_codes.keys()
                           if search_text in city.lower()]
        self.city_combo['values'] = sorted(filtered_cities)

    def generate_fiscal_code(self):
        """Genera il codice fiscale"""
        try:
            name = self.entries['name'].get().strip()
            surname = self.entries['surname'].get().strip()
            birth_date = self.entries['birth_date'].get().strip()
            gender = self.gender_var.get()
            city = self.city_var.get()

            # Validazione input
            if not all([name, surname, birth_date, gender, city]):
                raise ValueError("Tutti i campi sono obbligatori")

            # Validazione data
            try:
                day, month, year = map(int, birth_date.split('/'))
                if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                    raise ValueError()
            except:
                raise ValueError("Data non valida. Usa il formato DD/MM/YYYY")

            def get_consonants(s):
                return ''.join(c.upper() for c in s
                               if c.isalpha() and c.upper() not in 'AEIOU')

            def get_vowels(s):
                return ''.join(c.upper() for c in s
                               if c.isalpha() and c.upper() in 'AEIOU')

            # Calcola cognome
            consonants_surname = get_consonants(surname)
            vowels_surname = get_vowels(surname)
            surname_code = (consonants_surname + vowels_surname + 'XXX')[:3]

            # Calcola nome
            consonants_name = get_consonants(name)
            if len(consonants_name) > 3:
                name_code = consonants_name[0] + consonants_name[2] + consonants_name[3]
            else:
                vowels_name = get_vowels(name)
                name_code = (consonants_name + vowels_name + 'XXX')[:3]

            # Calcola anno
            year_code = str(year)[-2:]

            # Calcola mese
            month_codes = 'ABCDEHLMPRST'
            month_code = month_codes[month - 1]

            # Calcola giorno
            day_code = str(day + 40 if gender == 'F' else day).zfill(2)

            # Ottieni codice comune
            city_code = self.city_codes.get(city)
            if not city_code:
                raise ValueError(f"Codice comune non trovato per {city}")

            # Genera codice parziale
            partial_code = f"{surname_code}{name_code}{year_code}{month_code}{day_code}{city_code}"

            # Calcola carattere di controllo
            def calc_control_char(code):
                even_sum = sum(ord(c) for i, c in enumerate(code) if i % 2 == 1)
                odd_map = {
                    '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17,
                    '8': 19, '9': 21, 'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13,
                    'G': 15, 'H': 17, 'I': 19, 'J': 21, 'K': 2, 'L': 4, 'M': 18, 'N': 20,
                    'O': 11, 'P': 3, 'Q': 6, 'R': 8, 'S': 12, 'T': 14, 'U': 16, 'V': 10,
                    'W': 22, 'X': 25, 'Y': 24, 'Z': 23
                }
                odd_sum = sum(odd_map[c] for i, c in enumerate(code) if i % 2 == 0)
                total = odd_sum + even_sum
                return chr(65 + (total % 26))

            control_char = calc_control_char(partial_code)
            fiscal_code = f"{partial_code}{control_char}"

            # Mostra risultato
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END,
                                    f"Codice Fiscale generato:\n"
                                    f"{fiscal_code}\n\n"
                                    f"Dettagli:\n"
                                    f"Cognome: {surname} → {surname_code}\n"
                                    f"Nome: {name} → {name_code}\n"
                                    f"Data: {birth_date} → {year_code}{month_code}{day_code}\n"
                                    f"Genere: {gender}\n"
                                    f"Comune: {city} → {city_code}\n"
                                    f"Carattere controllo: {control_char}")

            return fiscal_code

        except Exception as e:
            messagebox.showerror("Errore", str(e))
            return None

    def validate_fiscal_code(self):
        """Valida un codice fiscale"""
        code = self.validate_entry.get().strip().upper()
        self.validate_text.delete(1.0, tk.END)

        try:
            if not code:
                raise ValueError("Inserisci un codice fiscale")

            if not re.match(r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$', code):
                raise ValueError("Formato codice fiscale non valido")

            # Estrai componenti
            surname_code = code[:3]
            name_code = code[3:6]
            year_code = code[6:8]
            month_code = code[8]
            day_code = code[9:11]
            city_code = code[11:15]
            control_char = code[15]

            # Verifica mese
            month_codes = 'ABCDEHLMPRST'
            if month_code not in month_codes:
                raise ValueError("Codice mese non valido")

            # Verifica giorno
            day = int(day_code)
            if day > 40:
                day -= 40
                gender = 'F'
            else:
                gender = 'M'

            if not (1 <= day <= 31):
                raise ValueError("Giorno non valido")

            # Verifica carattere di controllo
            def calc_control_char(code):
                even_sum = sum(ord(c) for i, c in enumerate(code) if i % 2 == 1)
                odd_map = {
                    '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17,
                    '8': 19, '9': 21, 'A': 1, 'B': 0, 'C': 5, 'D': 7,'8':19, '9':21, 'A':1, 'B':0, 'C':5, 'D':7, 'E':9, 'F':13,
                    'G':15, 'H':17, 'I':19, 'J':21, 'K':2, 'L':4, 'M':18, 'N':20,
                    'O':11, 'P':3, 'Q':6, 'R':8, 'S':12, 'T':14, 'U':16, 'V':10,
                    'W':22, 'X':25, 'Y':24, 'Z':23
                }
                odd_sum = sum(odd_map[c] for i, c in enumerate(code) if i % 2 == 0)
                total = odd_sum + even_sum
                return chr(65 + (total % 26))

            expected_control = calc_control_char(code[:15])
            if control_char != expected_control:
                raise ValueError("Carattere di controllo non valido")

            self.validate_text.insert(tk.END,
                f"Il codice fiscale è valido!\n\n"
                f"Analisi:\n"
                f"Cognome: {surname_code}\n"
                f"Nome: {name_code}\n"
                f"Anno: {year_code}\n"
                f"Mese: {month_code}\n"
                f"Giorno: {day} ({gender})\n"
                f"Comune: {city_code}\n"
                f"Controllo: {control_char}")

        except Exception as e:
            self.validate_text.insert(tk.END, f"Codice non valido: {str(e)}")

    def browse_files(self):
        """Apre il dialogo per selezionare i file"""
        files = filedialog.askopenfilenames(
            title="Seleziona file da analizzare",
            filetypes=[
                ("Tutti i file", "*.*"),
                ("File di testo", "*.txt"),
                ("File XML", "*.xml"),
                ("File JSON", "*.json")
            ]
        )
        if files:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, "; ".join(files))
            self.analyze_files(files)

    def analyze_files(self, files):
        """Analizza i file per trovare codici fiscali"""
        self.analyze_text.delete(1.0, tk.END)

        total_found = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Trova tutti i possibili codici fiscali
                pattern = r'[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]'
                found_codes = re.finditer(pattern, content, re.IGNORECASE)

                filename = os.path.basename(file_path)
                self.analyze_text.insert(tk.END, f"\nFile: {filename}\n")

                file_count = 0
                for match in found_codes:
                    code = match.group().upper()
                    try:
                        # Valida ogni codice trovato
                        self.validate_entry.delete(0, tk.END)
                        self.validate_entry.insert(0, code)
                        self.validate_fiscal_code()
                        status = "✓ Valido"
                    except Exception as e:
                        status = "✗ Non valido"

                    # Mostra risultato con posizione nel file
                    pos = match.start()
                    self.analyze_text.insert(tk.END,
                        f"Posizione {pos}: {code} - {status}\n")
                    file_count += 1

                if file_count == 0:
                    self.analyze_text.insert(tk.END,
                        "Nessun codice fiscale trovato\n")
                else:
                    self.analyze_text.insert(tk.END,
                        f"Trovati {file_count} codici fiscali\n")
                    total_found += file_count

            except Exception as e:
                messagebox.showerror("Errore",
                    f"Errore nell'analisi del file {file_path}: {str(e)}")

        if total_found > 0:
            self.analyze_text.insert(tk.END,
                f"\nTotale codici fiscali trovati: {total_found}")

    def clear_fields(self):
        """Pulisce tutti i campi di input"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.city_var.set('')
        self.gender_var.set('M')
        self.search_var.set('')
        self.result_text.delete(1.0, tk.END)

    def copy_to_clipboard(self):
        """Copia il codice fiscale negli appunti"""
        text = self.result_text.get(1.0, tk.END)
        code = re.search(r'[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]', text)
        if code:
            self.frame.clipboard_clear()
            self.frame.clipboard_append(code.group(0))
            self.frame.update()
            messagebox.showinfo("Info", "Codice fiscale copiato negli appunti!")
        else:
            messagebox.showwarning("Attenzione",
                "Genera prima un codice fiscale!")

    def search(self, text):
        """Ricerca nel tab (per ricerca globale)"""
        results = []

        # Cerca nei risultati generati
        result_content = self.result_text.get(1.0, tk.END)
        if text in result_content.lower():
            results.append(("Codice Fiscale", result_content.strip()))

        # Cerca nei risultati delle analisi
        analyze_content = self.analyze_text.get(1.0, tk.END)
        if text in analyze_content.lower():
            results.append(("Analisi File", analyze_content.strip()))

        return results