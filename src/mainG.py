import logging
import os
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Optional, List

# Import personal modules
from init_db import initialize_database
from login_window import LoginWindow
from src.file_analyzer import FileTab
from src.fiscal_analyzer import FiscalTab
from src.inventory_manager import InventoryTab
from src.sla_analyzer import SLATab
from src.test_analyzer_tab import TestAnalyzerTab
from user_management import UserManagementWindow

# Impostazioni di base e setup logging
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..')
)
sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('application.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class MainApp:
    """
    Classe principale dell'applicazione.
    Gestisce login, creazione finestra principale e tab, menu, logout e chiusura.
    """
    VERSION = "1.0"

    def __init__(self) -> None:
        """
        Inizializza le componenti di base e avvia la finestra di login.
        """
        try:
            self.current_user: Optional[str] = None
            self.user_role: Optional[str] = None
            self.user_management_window: Optional[UserManagementWindow] = None

            # Variabili di stato per la GUI
            self.root: Optional[tk.Tk] = None
            self.fiscal_tab: Optional[FiscalTab] = None
            self.file_tab: Optional[FileTab] = None
            self.inventory_tab: Optional[InventoryTab] = None
            self.sla_tab: Optional[SLATab] = None
            self.test_analyzer_tab: Optional[TestAnalyzerTab] = None
            self.notebook: Optional[ttk.Notebook] = None

            self.status_var: Optional[tk.StringVar] = None
            self.search_var: Optional[tk.StringVar] = None

            self.initialize_system()
            self.start_login()

        except Exception as e:
            logging.error(f"Errore di inizializzazione: {str(e)}")
            messagebox.showerror("Errore", f"Errore inizializzazione: {str(e)}")
            sys.exit(1)

    def initialize_system(self) -> None:
        """
        Prepara il database e la struttura di cartelle necessaria.
        """
        try:
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / 'data'
            db_file = data_dir / 'users.db'

            data_dir.mkdir(exist_ok=True)

            if not db_file.exists():
                if not initialize_database():
                    raise Exception("Errore inizializzazione database")

            logging.info("Sistema inizializzato correttamente.")

        except Exception as e:
            logging.error(f"Errore inizializzazione sistema: {e}")
            raise

    def logout(self) -> None:
        """
        Effettua il logout dell'utente corrente, ripristinando la finestra di login.
        """
        try:
            if messagebox.askokcancel("Logout", "Vuoi effettuare il logout?"):
                logging.info(f"Logout utente: {self.current_user}")
                self.current_user = None
                self.user_role = None

                if self.root:
                    self.root.withdraw()

                self.start_login()

        except Exception as e:
            logging.error(f"Errore durante il logout: {e}")
            messagebox.showerror("Errore", f"Errore logout: {e}")

    def start_login(self) -> None:
        """
        Avvia la finestra di login e ne gestisce il ciclo di vita.
        """
        try:
            login_window = LoginWindow(self.on_login_success)
            login_window.root.protocol(
                "WM_DELETE_WINDOW",
                lambda: self.on_login_window_close(login_window)
            )
            login_window.run()

        except Exception as e:
            logging.error(f"Errore durante il login: {e}")
            messagebox.showerror("Errore", f"Errore login: {e}")
            sys.exit(1)

    def on_login_window_close(self, login_window: LoginWindow) -> None:
        """
        Gestisce la chiusura della finestra di login.
        """
        try:
            if messagebox.askokcancel("Chiudi", "Vuoi chiudere l'applicazione?"):
                login_window.root.destroy()
                if self.root:
                    self.root.destroy()
                sys.exit(0)

        except Exception as e:
            logging.error(f"Errore durante la chiusura: {e}")
            sys.exit(1)

    def on_login_success(self, username: str, role: str) -> None:
        """
        Callback invocata quando il login ha successo.
        Setta l'utente e il ruolo corrente, quindi prepara la finestra principale.
        """
        try:
            logging.info(f"Login riuscito - Utente: {username}, Ruolo: {role}")
            self.current_user = username
            self.user_role = role

            if self.root:
                self.root.deiconify()
                self.create_main_window()
            else:
                self.create_main_window()

        except Exception as e:
            logging.error(f"Errore post-login: {e}")
            messagebox.showerror("Errore", f"Errore post-login: {e}")
            sys.exit(1)

    def create_main_window(self) -> None:
        """
        Crea e configura la finestra principale dell'applicazione.
        """
        try:
            if not self.root:
                self.root = tk.Tk()

            self.root.title(f"Business Intelligence Suite - v{self.VERSION}")
            self.root.geometry("1024x768")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            self.create_menu_bar()

            self.status_var = tk.StringVar(
                value=f"Benvenuto, {self.current_user} ({self.user_role})"
            )
            self.search_var = tk.StringVar()

            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

            self.create_tabs()

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
            logging.error(f"Errore nella creazione della finestra: {e}")
            messagebox.showerror("Errore", f"Errore finestra: {e}")
            sys.exit(1)

    def on_closing(self) -> None:
        """
        Gestisce la chiusura dell'applicazione dall'interfaccia principale.
        """
        try:
            if messagebox.askokcancel("Chiudi", "Vuoi chiudere l'applicazione?"):
                if self.root:
                    self.root.destroy()
                sys.exit(0)

        except Exception as e:
            logging.error(f"Errore chiusura finestra principale: {e}")
            sys.exit(1)

    def create_menu_bar(self) -> None:
        """
        Crea la barra dei menu principale con voci File, Strumenti e Aiuto.
        """
        if not self.root:
            return

        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(
            label="Gestione Utenti",
            command=self.open_user_management,
            state='normal' if self.user_role == 'admin' else 'disabled'
        )
        file_menu.add_separator()
        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Esci", command=self.on_closing)

        # Menu Strumenti
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Strumenti", menu=tools_menu)
        tools_menu.add_command(label="Cerca", command=self.open_search)
        tools_menu.add_command(label="Impostazioni", command=self.open_settings)

        # Menu Aiuto
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Aiuto", menu=help_menu)
        help_menu.add_command(label="Manuale", command=self.open_manual)
        help_menu.add_command(label="Informazioni su", command=self.show_about)

    def create_tabs(self) -> None:
        """
        Inizializza e aggiunge le Tab dell’applicazione al Notebook principale.
        """
        if not self.notebook:
            return

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
            logging.error(f"Errore nella creazione dei Tab: {e}")
            messagebox.showerror("Errore", f"Impossibile creare i Tab: {e}")
            raise

    def open_user_management(self) -> None:
        """
        Apre la finestra di Gestione Utenti (disponibile solo per admin).
        """
        try:
            if self.user_role != 'admin':
                messagebox.showerror("Accesso Negato", "Solo gli admin possono gestire gli utenti.")
                return

            self.user_management_window = UserManagementWindow(self.root)

        except Exception as e:
            logging.error(f"Errore gestione utenti: {e}")
            messagebox.showerror("Errore", str(e))

    def open_search(self) -> None:
        """
        Mostra una finestra per inserire un termine di ricerca.
        """
        try:
            search_window = tk.Toplevel(self.root)
            search_window.title("Cerca")
            search_window.geometry("400x300")

            ttk.Label(search_window, text="Termine di ricerca:").pack(pady=10)
            search_entry = ttk.Entry(search_window, textvariable=self.search_var)
            search_entry.pack(pady=5)

            ttk.Button(search_window, text="Cerca", command=self.perform_search).pack(pady=10)

        except Exception as e:
            logging.error(f"Errore durante la creazione della finestra di ricerca: {e}")
            messagebox.showerror("Errore", str(e))

    def perform_search(self) -> None:
        """
        Esegue la ricerca sul testo inserito, interfacciandosi con i Tab che la supportano.
        """
        if not self.search_var:
            return

        search_term = self.search_var.get().strip()
        if not search_term:
            messagebox.showinfo("Info", "Inserisci un termine di ricerca")
            return

        results: List[str] = []
        for tab in [self.fiscal_tab, self.file_tab, self.inventory_tab, self.sla_tab]:
            if tab and hasattr(tab, 'search'):
                partial_result = tab.search(search_term)
                if partial_result:
                    results.extend(partial_result)

        self.show_search_results(results)

    def show_search_results(self, results: List[str]) -> None:
        """
        Mostra i risultati della ricerca in una nuova finestra.
        """
        if not results:
            messagebox.showinfo("Info", "Nessun risultato trovato")
            return

        results_window = tk.Toplevel(self.root)
        results_window.title("Risultati Ricerca")
        results_window.geometry("600x400")

        text_widget = tk.Text(results_window)
        text_widget.pack(fill=tk.BOTH, expand=True)

        for result in results:
            text_widget.insert(tk.END, f"{result}\n")

        text_widget.config(state=tk.DISABLED)

    def open_settings(self) -> None:
        """
        Apre la finestra delle Impostazioni dell'applicazione.
        """
        try:
            settings_window = tk.Toplevel(self.root)
            settings_window.title("Impostazioni")
            settings_window.geometry("400x300")

            theme_var = tk.StringVar(value="Sistema")

            ttk.Label(settings_window, text="Tema:").pack(pady=10)
            ttk.Combobox(
                settings_window,
                textvariable=theme_var,
                values=["Chiaro", "Scuro", "Sistema"]
            ).pack(pady=5)

            ttk.Button(
                settings_window,
                text="Salva",
                command=lambda: self.save_settings(theme_var.get())
            ).pack(pady=10)

        except Exception as e:
            logging.error(f"Errore durante l'apertura delle impostazioni: {e}")
            messagebox.showerror("Errore", str(e))

    def save_settings(self, theme: str) -> None:
        """
        Salva le impostazioni scelte dall’utente.
        Per ora mostra solo un messaggio di conferma.
        """
        try:
            # Qui potresti implementare il salvataggio effettivo su file/config.
            messagebox.showinfo("Successo", "Impostazioni salvate")
        except Exception as e:
            logging.error(f"Errore durante il salvataggio delle impostazioni: {e}")
            messagebox.showerror("Errore", str(e))

    def open_manual(self) -> None:
        """
        Apre il manuale dell'applicazione in un browser o lettore PDF di sistema.
        """
        manual_path = Path(__file__).parent / 'docs' / 'manuale.pdf'
        if manual_path.exists():
            webbrowser.open(str(manual_path))
        else:
            messagebox.showinfo("Info", "Manuale non trovato")

    def show_about(self) -> None:
        """
        Mostra una finestra con informazioni su autore e versione dell’app.
        """
        about = tk.Toplevel(self.root)
        about.title("Informazioni")
        about.geometry("400x300")

        ttk.Label(about, text="Business Intelligence Suite",
                  font=('Helvetica', 16, 'bold')).pack(pady=10)
        ttk.Label(about, text=f"Versione {self.VERSION}").pack()
        ttk.Label(about, text="© 2025 SergeGuea").pack(pady=20)

        ttk.Button(about, text="Chiudi", command=about.destroy).pack(pady=10)


def main() -> None:
    """
    Funzione principale di avvio dell’applicazione.
    """
    try:
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)

        logging.info("=== Avvio Applicazione ===")
        logging.info(f"Python versione: {sys.version}")
        logging.info(f"Sistema operativo: {os.name}")
        logging.info(f"Directory corrente: {os.getcwd()}")

        # Istanzia e lancia l'app
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
