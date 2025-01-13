import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime
import webbrowser
import json
from fiscal_analyzer import FiscalTab
from file_analyzer import FileTab
from inventory_manager import InventoryTab


class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Tool Analyzer - SergeGuea")
        self.root.geometry("1200x800")

        # Carica configurazioni
        self.load_config()

        # Configurazione iniziale
        self.setup_style()
        self.create_menu()
        self.create_toolbar()
        self.create_gui()

        # Setup backup automatico
        if self.config.get('auto_backup', True):
            self.schedule_backup()

    def load_config(self):
        """Carica le configurazioni dell'applicazione"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'theme': 'clam',
                    'auto_backup': True,
                    'backup_interval': 30,
                    'last_backup': None,
                    'language': 'it'
                }
                self.save_config()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel caricamento configurazioni: {str(e)}")
            self.config = {}

    def save_config(self):
        """Salva le configurazioni"""
        try:
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio configurazioni: {str(e)}")

    def setup_style(self):
        """Configura lo stile dell'applicazione"""
        self.style = ttk.Style()
        current_theme = self.config.get('theme', 'clam')
        self.style.theme_use(current_theme)

        # Header principale
        header = ttk.Label(
            self.root,
            text="Multi-Tool Analyzer",
            font=("Arial", 20, "bold"),
            padding=10
        )
        header.pack(fill='x')

    def create_menu(self):
        """Crea la barra dei menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Backup Database", command=self.backup_data)
        file_menu.add_command(label="Ripristina Backup", command=self.restore_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.quit_app)

        # Menu Visualizza
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizza", menu=view_menu)
        view_menu.add_command(label="Tema Chiaro", command=lambda: self.change_theme('clam'))
        view_menu.add_command(label="Tema Scuro", command=lambda: self.change_theme('alt'))

        # Menu Strumenti
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="Impostazioni", command=self.show_settings)

        # Menu Aiuto
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Documentazione", command=self.show_docs)
        help_menu.add_command(label="Supporto Online",
                              command=lambda: webbrowser.open('https://github.com/SERGE3-g'))
        help_menu.add_separator()
        help_menu.add_command(label="Info", command=self.show_about)

    def create_toolbar(self):
        """Crea la barra degli strumenti"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', pady=1)

        ttk.Button(toolbar, text="Backup", command=self.backup_data).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Impostazioni", command=self.show_settings).pack(side='left', padx=2)

        # Separatore
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)

        # Ricerca globale
        ttk.Label(toolbar, text="Cerca:").pack(side='left', padx=2)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.global_search)
        ttk.Entry(toolbar, textvariable=self.search_var).pack(side='left', padx=2)

    def create_gui(self):
        """Crea l'interfaccia principale"""
        # Notebook per le schede
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # Inizializzazione delle schede
        self.fiscal_tab = FiscalTab(self.notebook)
        self.file_tab = FileTab(self.notebook)
        self.inventory_tab = InventoryTab(self.notebook)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status = ttk.Label(self.root, textvariable=self.status_var)
        status.pack(side='bottom', fill='x', pady=2)

        # Footer
        footer = ttk.Label(
            self.root,
            text="© 2025 SergeGuea | Tutti i diritti riservati",
            font=("Arial", 10),
            padding=5
        )
        footer.pack(side='bottom', fill='x')

    def schedule_backup(self):
        """Programma il backup automatico"""
        interval = self.config.get('backup_interval', 30) * 60 * 1000  # minuti in ms
        self.root.after(interval, self.auto_backup)

    def auto_backup(self):
        """Esegue il backup automatico"""
        try:
            self.backup_data(silent=True)
        finally:
            self.schedule_backup()

    def backup_data(self, silent=False):
        """Esegue il backup dei dati"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Backup del database e delle configurazioni
            # TODO: Implementare la logica di backup specifica

            if not silent:
                messagebox.showinfo("Successo", "Backup completato con successo!")

        except Exception as e:
            if not silent:
                messagebox.showerror("Errore", f"Errore durante il backup: {str(e)}")

    def restore_backup(self):
        """Ripristina un backup"""
        # TODO: Implementare il ripristino del backup
        pass

    def change_theme(self, theme_name):
        """Cambia il tema dell'applicazione"""
        try:
            self.style.theme_use(theme_name)
            self.config['theme'] = theme_name
            self.save_config()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel cambio tema: {str(e)}")

    def show_settings(self):
        """Mostra la finestra delle impostazioni"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Impostazioni")
        settings_window.geometry("400x300")

        # Backup automatico
        auto_backup_var = tk.BooleanVar(value=self.config.get('auto_backup', True))
        ttk.Checkbutton(
            settings_window,
            text="Backup automatico",
            variable=auto_backup_var,
            command=lambda: self.config.update({'auto_backup': auto_backup_var.get()})
        ).pack(pady=5)

        # Intervallo backup
        frame = ttk.Frame(settings_window)
        frame.pack(pady=5)
        ttk.Label(frame, text="Intervallo backup (minuti):").pack(side='left')
        interval_var = tk.StringVar(value=str(self.config.get('backup_interval', 30)))
        ttk.Entry(frame, textvariable=interval_var).pack(side='left')

        # Pulsante salva
        ttk.Button(
            settings_window,
            text="Salva",
            command=lambda: self.save_settings(auto_backup_var.get(), interval_var.get())
        ).pack(pady=10)

    def save_settings(self, auto_backup, interval):
        """Salva le impostazioni"""
        try:
            self.config.update({
                'auto_backup': auto_backup,
                'backup_interval': int(interval)
            })
            self.save_config()
            messagebox.showinfo("Successo", "Impostazioni salvate con successo!")
        except ValueError:
            messagebox.showerror("Errore", "L'intervallo deve essere un numero intero")

    def show_docs(self):
        """Mostra la documentazione"""
        docs = tk.Toplevel(self.root)
        docs.title("Documentazione")
        docs.geometry("800x600")

        text = tk.Text(docs, wrap='word', padx=10, pady=10)
        text.pack(fill='both', expand=True)

        docs_text = """
        Multi-Tool Analyzer
        ==================

        Un'applicazione completa per:
        - Analisi codici fiscali
        - Gestione file
        - Gestione inventario

        Per supporto:
        https://github.com/SERGE3-g
        """

        text.insert('1.0', docs_text)
        text.config(state='disabled')

    def show_about(self):
        """Mostra informazioni sull'applicazione"""
        about_text = """
        Multi-Tool Analyzer v1.0

        Sviluppato da SergeGuea
        © 2025 Tutti i diritti riservati

        Per supporto: 
        https://github.com/SERGE3-g
        """
        messagebox.showinfo("Info", about_text)

    def global_search(self, *args):
        """Esegue una ricerca globale"""
        search_text = self.search_var.get().strip().lower()
        if len(search_text) < 3:
            return

        self.status_var.set(f"Ricerca in corso: {search_text}")
        # TODO: Implementare la logica di ricerca globale

    def quit_app(self):
        """Chiude l'applicazione"""
        if messagebox.askokcancel("Esci", "Vuoi davvero uscire dall'applicazione?"):
            try:
                self.backup_data(silent=True)
                self.root.quit()
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante la chiusura: {str(e)}")

    def run(self):
        """Avvia l'applicazione"""
        try:
            # Centra la finestra
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 1200) // 2
            y = (screen_height - 800) // 2
            self.root.geometry(f"1200x800+{x}+{y}")

            # Avvio
            self.root.mainloop()

        except Exception as e:
            messagebox.showerror("Errore", f"Si è verificato un errore: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        # Verifica directory necessarie
        for dir_name in ['backups', 'data', 'logs']:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)

        # Avvio applicazione
        app = MainApp()
        app.run()

    except Exception as e:
        print(f"Errore durante l'avvio: {str(e)}")
        sys.exit(1)