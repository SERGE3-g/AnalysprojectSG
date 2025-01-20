import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import webbrowser
from pathlib import Path

from login_window import LoginWindow
from init_db import initialize_database
# Se usi i test tab e altri, importali pure
from src.test_analyzer_tab import TestAnalyzerTab
from user_management import UserManagementWindow
from fiscal_analyzer import FiscalTab
from file_analyzer import FileTab
from inventory_manager import InventoryTab
from sla_analyzer import SLATab

# Imposta i path di progetto se necessario
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('application.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MainApp:
    VERSION = "1.0"

    def __init__(self):
        """Inizializza l'applicazione principale."""
        try:
            # Inizializza il sistema (database, cartelle, ecc.)
            self.initialize_system()

            # Variabili utente
            self.current_user = None
            self.user_role = None
            self.user_management_window = None
            self.root = None
            self.fiscal_tab = None
            self.file_tab = None
            self.inventory_tab = None
            self.sla_tab = None
            self.test_analyzer_tab = None
            self.status_var = None
            self.search_var = None
            self.notebook = None

            # Avvia la finestra di Login
            self.start_login()

        except Exception as e:
            logging.error(f"Errore di inizializzazione: {str(e)}")
            messagebox.showerror("Errore di Inizializzazione",
                                 f"Errore durante l'inizializzazione: {str(e)}")
            sys.exit(1)

    def initialize_system(self):
        """Inizializza il sistema e verifica il database."""
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent
            DATA_DIR = BASE_DIR / 'data'
            DB_FILE = DATA_DIR / 'users.db'

            logging.info(f"Directory base: {BASE_DIR}")
            logging.info(f"Directory data: {DATA_DIR}")
            logging.info(f"File database: {DB_FILE}")

            DATA_DIR.mkdir(exist_ok=True)  # Crea la dir 'data' se non esiste

            # Se il DB non esiste, inizializza
            if not DB_FILE.exists():
                logging.info("Database non trovato. Inizializzazione...")
                if not initialize_database():
                    raise Exception("Errore nell'inizializzazione del database")

            logging.info("Inizializzazione sistema completata")

        except Exception as e:
            logging.error(f"Errore inizializzazione sistema: {str(e)}")
            raise

    def start_login(self):
        """Avvia il processo di login."""
        try:
            login = LoginWindow(self.on_login_success)
            login.root.mainloop()
        except Exception as e:
            logging.error(f"Errore durante il login: {str(e)}")
            messagebox.showerror("Errore di Login",
                                 f"Errore durante il login: {str(e)}")
            sys.exit(1)

    def on_login_success(self, username, role):
        """Callback dopo un login riuscito."""
        try:
            logging.info(f"Login riuscito - Utente: {username}, Ruolo: {role}")
            self.current_user = username
            self.user_role = role
            if hasattr(self, 'root') and self.root is not None:
                self.root.destroy()
            self.create_main_window()
        except Exception as e:
            logging.error(f"Errore post-login: {str(e)}")
            messagebox.showerror("Errore Post-Login",
                                 f"Errore dopo il login: {str(e)}")
            sys.exit(1)

    def create_main_window(self):
        """Crea la finestra principale dell'applicazione."""
        try:
            self.root = tk.Tk()
            self.root.title(f"Business Intelligence Suite - v{self.VERSION}")
            self.root.geometry("1024x768")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Barra dei menu
            self.create_menu_bar()

            # Variabili di stato
            self.status_var = tk.StringVar(value=f"Benvenuto, {self.current_user} ({self.user_role})")
            self.search_var = tk.StringVar()

            # Notebook per i tab
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

            # Crea i vari tab
            self.create_tabs()

            # Barra di stato in basso
            status_bar = tk.Label(
                self.root,
                textvariable=self.status_var,
                bd=1,
                relief=tk.SUNKEN,
                anchor=tk.W
            )
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            self.root.mainloop()

        except Exception as e:
            logging.error(f"Errore creazione finestra principale: {str(e)}")
            messagebox.showerror("Errore",
                                 f"Impossibile creare la finestra principale: {str(e)}")
            sys.exit(1)

    def create_menu_bar(self):
        """Crea la barra dei menu."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Gestione utenti (solo admin)
        file_menu.add_command(
            label="Gestione Utenti",
            command=self.open_user_management,
            state='normal' if self.user_role == 'admin' else 'disabled'
        )
        file_menu.add_separator()

        # Logout e uscita
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Esci", command=self.on_closing)

        # Menu View
        #view_menu = tk.Menu(menu_bar, tearoff=0)
        #menu_bar.add_cascade(label="View", menu=view_menu)
        #view_menu.add_command(label="Impostazioni", command=self.open_settings)

        # Menu Strumenti
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="Cerca", command=self.open_search)
        tools_menu.add_command(label="Impostazioni", command=self.open_settings)
        # etc...

        # Menu Aiuto
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Manuale", command=self.open_manual)
        help_menu.add_command(label="Informazioni su", command=self.show_about)

    def create_tabs(self):
        """Crea e aggiunge i tab all'interno del notebook."""
        try:
            # Tab Analisi Fiscale
            self.fiscal_tab = FiscalTab(self.notebook, self.current_user, self.user_role)
            self.notebook.add(self.fiscal_tab, text="Analisi Fiscale")

            # Tab Analisi File
            self.file_tab = FileTab(self.notebook, self.current_user, self.user_role)
            self.notebook.add(self.file_tab, text="Analisi Check SDD")

            # Tab Gestione Inventario
            self.inventory_tab = InventoryTab(self.notebook, self.current_user, self.user_role)
            self.notebook.add(self.inventory_tab, text="Gestione Inventario")

            # Tab Analisi SLA
            self.sla_tab = SLATab(self.notebook, self.current_user, self.user_role)
            self.notebook.add(self.sla_tab, text="Analisi SLA")

            # Tab Test Analyzer
            self.test_analyzer_tab = TestAnalyzerTab(self.notebook)
            self.notebook.add(self.test_analyzer_tab.frame, text="Test Automatico")

        except Exception as e:
            logging.error(f"Errore creazione tab: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile creare i tab: {str(e)}")
            raise

    def logout(self):
        """Gestisce il logout dell'utente."""
        try:
            if messagebox.askyesno("Logout", "Vuoi davvero fare il logout?"):
                # Distrugge la finestra principale
                if self.root:
                    self.root.destroy()

                # Resetta i dati
                self.current_user = None
                self.user_role = None

                # Riapre la finestra di login
                from login_window import LoginWindow
                login = LoginWindow(self.on_login_success)
                login.root.mainloop()

        except Exception as e:
            logging.error(f"Errore durante il logout: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile effettuare il logout: {str(e)}")
            sys.exit(1)

    def on_closing(self):
        """Chiusura dell'applicazione."""
        try:
            if messagebox.askokcancel("Esci", "Vuoi davvero uscire dall'applicazione?"):
                logging.info(f"Applicazione chiusa dall'utente {self.current_user}")
                self.root.destroy()
                sys.exit(0)
        except Exception as e:
            logging.error(f"Errore durante la chiusura: {str(e)}")
            self.root.destroy()
            sys.exit(1)

    def open_user_management(self):
        """Apre la finestra di gestione utenti (solo admin)."""
        try:
            if self.user_role != 'admin':
                messagebox.showerror("Accesso Negato", "Solo gli admin possono gestire gli utenti.")
                return

            self.user_management_window = UserManagementWindow(self.root)

        except Exception as e:
            logging.error(f"Errore apertura gestione utenti: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire la gestione utenti: {str(e)}")

    def open_search(self):
        """Apre la finestra di ricerca."""
        try:
            search_window = tk.Toplevel(self.root)
            search_window.title("Cerca")
            search_window.geometry("400x300")

            search_label = tk.Label(search_window, text="Inserisci termine di ricerca:")
            search_label.pack(pady=10)

            search_entry = tk.Entry(search_window, textvariable=self.search_var, width=40)
            search_entry.pack(pady=10)

            search_button = tk.Button(search_window, text="Cerca",
                                      command=self.perform_search)
            search_button.pack(pady=10)

        except Exception as e:
            logging.error(f"Errore apertura ricerca: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire la ricerca: {str(e)}")

    def perform_search(self):
        """Esegue la ricerca su tutti i tab."""
        search_term = self.search_var.get()
        if not search_term:
            messagebox.showinfo("Ricerca", "Inserisci un termine di ricerca.")
            return

        try:
            results = []
            if self.fiscal_tab:
                results.extend(self.fiscal_tab.search(search_term))
            if self.file_tab:
                results.extend(self.file_tab.search(search_term))
            if self.inventory_tab:
                results.extend(self.inventory_tab.search(search_term))
            if self.sla_tab:
                results.extend(self.sla_tab.search(search_term))
            if self.test_analyzer_tab and hasattr(self.test_analyzer_tab, 'search'):
                found = self.test_analyzer_tab.search(search_term)
                if found:
                    results.extend(found)

            if results:
                result_window = tk.Toplevel(self.root)
                result_window.title(f"Risultati ricerca: {search_term}")
                result_window.geometry("600x400")

                result_text = tk.Text(result_window, wrap=tk.WORD)
                result_text.pack(expand=True, fill='both', padx=10, pady=10)

                for item in results:
                    # item potrebbe essere una tuple (title, content) o una string
                    # adattalo alle tue strutture
                    result_text.insert(tk.END, f"{item}\n")

                result_text.config(state=tk.DISABLED)
            else:
                messagebox.showinfo("Ricerca", "Nessun risultato trovato.")

        except Exception as e:
            logging.error(f"Errore durante la ricerca: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante la ricerca: {str(e)}")

    def open_settings(self):
        """Apre la finestra delle impostazioni."""
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Impostazioni")
            settings_window.geometry("400x300")

            theme_label = tk.Label(settings_window, text="Tema:")
            theme_label.pack(pady=10)

            themes = ["Chiaro", "Scuro", "Sistema"]
            theme_var = tk.StringVar(value="Sistema")
            theme_dropdown = ttk.Combobox(settings_window, textvariable=theme_var,
                                          values=themes, state="readonly")
            theme_dropdown.pack(pady=10)

            save_button = tk.Button(settings_window, text="Salva Impostazioni",
                                    command=lambda: self.save_settings(theme_var.get()))
            save_button.pack(pady=10)

        except Exception as e:
            logging.error(f"Errore apertura impostazioni: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire le impostazioni: {str(e)}")

    def save_settings(self, theme):
        """Salva le impostazioni (es. tema)."""
        try:
            logging.info(f"Impostazioni salvate - Tema: {theme}")
            messagebox.showinfo("Impostazioni", "Impostazioni salvate con successo")
        except Exception as e:
            logging.error(f"Errore salvataggio impostazioni: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile salvare le impostazioni: {str(e)}")

    def open_manual(self):
        """Apre il manuale (PDF)."""
        try:
            manual_path = os.path.join(os.path.dirname(__file__), 'docs', 'manuale.pdf')
            if os.path.exists(manual_path):
                webbrowser.open(manual_path)
            else:
                messagebox.showinfo("Manuale", "Manuale non trovato")
        except Exception as e:
            logging.error(f"Errore apertura manuale: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile aprire il manuale: {str(e)}")

    def show_about(self):
        """Mostra informazioni su (About)."""
        try:
            about_window = tk.Toplevel(self.root)
            about_window.title("Informazioni su")
            about_window.geometry("400x300")
            about_window.resizable(False, False)

            title_label = tk.Label(
                about_window,
                text="Business Intelligence Suite",
                font=("Arial", 16, "bold")
            )
            title_label.pack(pady=10)

            version_label = tk.Label(
                about_window,
                text=f"Versione {self.VERSION}",
                font=("Arial", 12)
            )
            version_label.pack(pady=5)

            info_text = tk.Text(
                about_window,
                height=10,
                width=50,
                wrap=tk.WORD,
                borderwidth=0,
                font=("Arial", 10)
            )
            info_text.insert(
                tk.END,
                "Applicazione di Business Intelligence integrata.\n\n"
                "Sviluppata per fornire analisi avanzate e strumenti "
                "di gestione per aziende moderne.\n\n"
                "© 2024 Tutti i diritti riservati."
            )
            info_text.config(state=tk.DISABLED)
            info_text.pack(pady=10)

            close_button = tk.Button(about_window, text="Chiudi", command=about_window.destroy)
            close_button.pack(pady=10)

        except Exception as e:
            logging.error(f"Errore nella finestra About: {str(e)}")
            messagebox.showerror("Errore", f"Impossibile mostrare le informazioni: {str(e)}")

def main():
    try:
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)

        logging.info("=== Avvio Applicazione ===")
        logging.info(f"Python versione: {sys.version}")
        logging.info(f"Sistema operativo: {os.name}")
        logging.info(f"Directory corrente: {os.getcwd()}")

        app = MainApp()

    except Exception as e:
        logging.critical(f"Errore critico durante l'avvio: {str(e)}")
        messagebox.showerror(
            "Errore Critico",
            f"Errore durante l'avvio dell'applicazione:\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()