import json
import tkinter as tk

from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime
import webbrowser
from fiscal_analyzer import FiscalTab
from file_analyzer import FileTab
from inventory_manager import InventoryTab
from sla_analyzer import SLATab
from src.login_window import LoginWindow
from src.user_management import UserManagementWindow
#from test_analyzer_tab import TestAnalyzerTab

class MainApp:
    VERSION = "1.0"

    def __init__(self):
        """Inizializza l'applicazione principale"""
        try:
            # Inizializzazione variabili utente
            self.current_user = None
            self.user_role = None
            self.user_management_window = None
            self.root = None
            self.fiscal_tab = None
            self.file_tab = None
            self.inventory_tab = None
            self.sla_tab = None
            self.status_var = None
            self.search_var = None
            self.notebook = None

            # Avvia il login
            self.start_login()

        except Exception as e:
            messagebox.showerror("Errore di Inizializzazione",
                               f"Errore durante l'inizializzazione: {str(e)}")
            sys.exit(1)

    def start_login(self):
        """Avvia il processo di login"""
        try:
            login = LoginWindow(self.on_login_success)
            login.root.mainloop()
        except Exception as e:
            messagebox.showerror("Errore di Login",
                               f"Errore durante il login: {str(e)}")
            sys.exit(1)

    def on_login_success(self, username, role):
        """Callback per login riuscito"""
        try:
            self.current_user = username
            self.user_role = role
            if hasattr(self, 'root') and self.root is not None:
                self.root.destroy()
            self.create_main_window()
        except Exception as e:
            messagebox.showerror("Errore Post-Login",
                               f"Errore dopo il login: {str(e)}")
            sys.exit(1)

    def create_main_window(self):
        """Crea la finestra principale dopo il login"""
        try:
            self.root = tk.Tk()
            self.root.title(f"Multi-Tool Analyzer - {self.current_user}")

            # Configura finestra principale
            self.setup_main_window()

            # Inizializza variabili
            self.status_var = tk.StringVar(value=f"Utente: {self.current_user} ({self.user_role})")
            self.search_var = tk.StringVar()
            self.search_var.trace('w', self.global_search)

            # Setup interfaccia
            self.setup_style()
            self.create_menu()
            self.create_toolbar()
            self.create_gui()

            # Centra la finestra e avvia
            self.center_window()
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
            self.root.mainloop()

        except Exception as e:
            messagebox.showerror("Errore Interfaccia",
                               f"Errore nella creazione dell'interfaccia: {str(e)}")
            sys.exit(1)

    def setup_main_window(self):
        """Configura la finestra principale"""
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Configura il grid
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def setup_style(self):
        """Configura lo stile dell'applicazione"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configura stili personalizzati
        self.style.configure('Header.TLabel',
                           font=('Arial', 20, 'bold'),
                           padding=10)
        self.style.configure('Status.TLabel',
                           font=('Arial', 9),
                           padding=2)

    def create_menu(self):
        """Crea la barra dei menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        if self.user_role == 'admin':
            file_menu.add_command(label="Gestione Utenti",
                                command=self.show_user_management)
            file_menu.add_command(label="Impostazioni",
                                command=self.show_settings)
            file_menu.add_separator()

        file_menu.add_command(label="Logout", command=self.logout)
        file_menu.add_command(label="Esci", command=self.quit_app)

        # Menu Help
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentazione", command=self.show_docs)
        help_menu.add_command(label="Info", command=self.show_about)

        # Menu Supporto
        support_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Supporto", menu=support_menu)
        support_menu.add_command(label="Contattaci", command=self.show_contact)

        # Menu Versione
        version_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Versione", menu=version_menu)
        version_menu.add_command(label=f"Versione {self.VERSION}")

    def create_toolbar(self):
        """Crea la barra degli strumenti"""
        toolbar = ttk.Frame(self.root)
        toolbar.grid(row=0, column=0, sticky='ew', padx=5, pady=2)

        # Ricerca globale
        ttk.Label(toolbar, text="Cerca:").pack(side='left', padx=2)
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.pack(side='left', padx=2, expand=True, fill='x')

    def create_gui(self):
        """Crea l'interfaccia principale"""
        # Notebook per le schede
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Creazione delle schede
        self.fiscal_tab = FiscalTab(self.notebook)
        self.file_tab = FileTab(self.notebook)
        self.inventory_tab = InventoryTab(self.notebook)
        self.sla_tab = SLATab(self.notebook)

        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky='ew')

        status = ttk.Label(status_frame,
                          textvariable=self.status_var,
                          style='Status.TLabel')
        status.pack(side='left', fill='x', padx=5)

        # Footer con copyright
        ttk.Label(status_frame,
                 text="© 2025 SergeGuea | Tutti i diritti riservati",
                 style='Status.TLabel').pack(side='right', padx=5)

    def center_window(self):
        """Centra la finestra sullo schermo"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def show_user_management(self):
        """Mostra la finestra di gestione utenti (solo admin)"""
        if self.user_role != 'admin':
            messagebox.showerror("Errore", "Accesso non autorizzato")
            return

        if self.user_management_window is not None:
            try:
                self.user_management_window.window.lift()
                self.user_management_window.window.focus_force()
                return
            except tk.TclError:
                self.user_management_window = None

        self.user_management_window = UserManagementWindow(self.root)
        self.user_management_window.window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self.on_user_management_close()
        )

    def show_settings(self):
        """Mostra la finestra delle impostazioni"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Impostazioni")
        settings_window.geometry("600x400")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Frame principale
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Impostazioni applicazione
        app_frame = ttk.LabelFrame(main_frame, text="Impostazioni Applicazione", padding=10)
        app_frame.pack(fill=tk.X, pady=5)

        # Tema
        ttk.Label(app_frame, text="Tema:").pack(side=tk.LEFT, padx=5)
        theme_var = tk.StringVar(value="Chiaro")
        theme_combo = ttk.Combobox(app_frame,
                                 textvariable=theme_var,
                                 values=["Chiaro", "Scuro"],
                                 state='readonly')
        theme_combo.pack(side=tk.LEFT, padx=5)

        # Bottoni
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)

        ttk.Button(button_frame,
                  text="Salva",
                  command=lambda: self.save_settings(settings_window)
                  ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(button_frame,
                  text="Annulla",
                  command=settings_window.destroy
                  ).pack(side=tk.RIGHT, padx=5)

    def save_settings(self, window):
        """Salva le impostazioni e chiude la finestra"""
        messagebox.showinfo("Info", "Impostazioni salvate")
        window.destroy()

    def show_docs(self):
        """Mostra la documentazione"""
        webbrowser.open('https://github.com/SERGE3-g')

    def show_about(self):
        """Mostra informazioni sull'applicazione"""
        about_text = f"""
        Multi-Tool Analyzer v{self.VERSION}

        Sviluppato da SergeGuea
        © 2025 Tutti i diritti riservati

        Per supporto: 
        https://github.com/SERGE3-g
        """
        messagebox.showinfo("Info", about_text)

    def show_contact(self):
        """Mostra la finestra di contatto"""
        contact_window = tk.Toplevel(self.root)
        contact_window.title("Contattaci")
        contact_window.geometry("400x300")
        contact_window.transient(self.root)
        contact_window.grab_set()

        frame = ttk.Frame(contact_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame,
                 text="Contatti",
                 font=("Arial", 14, "bold")).pack(pady=10)

        contacts = [
            ("Email:", "gueaserge@gmail.com"),
            ("Telefono:", "+39 389-297-8507"),
            ("Sito Web:", "https://github.com/SERGE3-g"),
            ("Orari:", "Lun-Ven: 9:00-18:00"),
            ("Indirizzo:", "Via Virgilio , 19 - 04023, Formia (LT)"),
            ("Social:", "Facebook, Twitter, Instagram")

        ]

        for label, value in contacts:
            contact_frame = ttk.Frame(frame)
            contact_frame.pack(fill=tk.X, pady=5)
            ttk.Label(contact_frame,
                     text=label,
                     font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(contact_frame,
                     text=value).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame,
                  text="Chiudi",
                  command=contact_window.destroy).pack(side=tk.BOTTOM, pady=20)

    def on_user_management_close(self):
        """Gestisce la chiusura della finestra di gestione utenti"""
        if self.user_management_window is not None:
            self.user_management_window.window.destroy()
            self.user_management_window = None

    def global_search(self, *args):
        """Esegue una ricerca globale"""
        search_text = self.search_var.get().lower()
        if len(search_text) < 3:
            return

        self.status_var.set(f"Ricerca in corso: {search_text}")
        results = []

        # Cerca in ogni tab
        for tab in [self.fiscal_tab, self.file_tab, self.inventory_tab, self.sla_tab]:
            try:
                tab_results = tab.search(search_text)
                if tab_results:
                    results.extend(tab_results)
            except Exception as e:
                print(f"Errore nella ricerca: {str(e)}")

        if results:
            self.show_search_results(results)
        else:
            self.status_var.set("Nessun risultato trovato")

    def show_search_results(self, results):
        """Mostra i risultati della ricerca"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Risultati Ricerca")
        dialog.geometry("600x400")

        frame = ttk.Frame(dialog, padding="5")
        frame.pack(fill='both', expand=True)

        text = tk.Text(frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Configura i tag per la formattazione
        text.tag_configure('title', font=('Arial', 10, 'bold'))
        text.tag_configure('content', font=('Arial', 9))
        text.tag_configure('separator', font=('Arial', 9), foreground='gray')

        for title, content in results:
            text.insert('end', f"\n{title}\n", 'title')
            text.insert('end', f"{content}\n", 'content')
            text.insert('end', "─" * 50 + "\n", 'separator')

        # Rendi il testo non modificabile
        text.config(state='disabled')

        # Aggiungi pulsante per chiudere
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill='x', pady=5)

        ttk.Button(
            button_frame,
            text="Chiudi",
            command=dialog.destroy
        ).pack(side='right', padx=5)

        # Aggiungi pulsante per esportare i risultati
        ttk.Button(
            button_frame,
            text="Esporta Risultati",
            command=lambda: self.export_search_results(results)
        ).pack(side='right', padx=5)

        # Binding per chiusura con Escape
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # Rendi la finestra modale
        dialog.transient(self.root)
        dialog.grab_set()

        # Aggiorna la status bar
        self.status_var.set(f"Trovati {len(results)} risultati")

    def export_search_results(self, results):
        """Esporta i risultati della ricerca in un file di testo"""
        try:
            # Richiedi il percorso del file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialfile=f"ricerca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if not file_path:
                return

            # Scrivi i risultati nel file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("RISULTATI RICERCA\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")

                for title, content in results:
                    f.write(f"{title}\n")
                    f.write("-" * len(title) + "\n")
                    f.write(f"{content}\n\n")
                    f.write("=" * 50 + "\n\n")

            messagebox.showinfo(
                "Esportazione Completata",
                f"I risultati sono stati salvati in:\n{file_path}"
            )

        except Exception as e:
            messagebox.showerror(
                "Errore Esportazione",
                f"Si è verificato un errore durante l'esportazione:\n{str(e)}"
            )

    def logout(self):
            """Gestisce il logout"""
            if messagebox.askyesno("Logout", "Vuoi effettuare il logout?"):
                # Chiudi eventuali finestre aperte
                if self.user_management_window is not None:
                    self.user_management_window.window.destroy()
                    self.user_management_window = None

                # Pulisci lo stato corrente
                self.current_user = None
                self.user_role = None

                # Distruggi la finestra principale
                self.root.destroy()

                # Riavvia il processo di login
                self.start_login()

    def quit_app(self):
            """Chiude l'applicazione"""
            if messagebox.askokcancel("Esci", "Vuoi davvero uscire dall'applicazione?"):
                try:
                    # Chiudi eventuali finestre aperte
                    if self.user_management_window is not None:
                        self.user_management_window.window.destroy()

                    # Salva eventuali dati non salvati
                    self.save_application_state()

                    # Chiudi l'applicazione
                    self.root.quit()
                    sys.exit(0)
                except Exception as e:
                    messagebox.showerror(
                        "Errore",
                        f"Errore durante la chiusura dell'applicazione:\n{str(e)}"
                    )
                    sys.exit(1)

    def save_application_state(self):
            """Salva lo stato dell'applicazione"""
            try:
                # Crea la directory dei dati se non esiste
                data_dir = "data"
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir)

                # Prepara i dati da salvare
                app_state = {
                    "last_user": self.current_user,
                    "last_access": datetime.now().isoformat(),
                    "window_geometry": self.root.geometry(),
                    "active_tab": self.notebook.select(),
                    "theme": self.style.theme_use()
                }

                # Salva lo stato
                state_file = os.path.join(data_dir, "app_state.json")
                with open(state_file, 'w', encoding='utf-8') as f:
                    json.dump(app_state, f, indent=4)

            except Exception as e:
                print(f"Errore nel salvataggio dello stato: {str(e)}")
                # Non solleviamo l'errore per permettere la chiusura dell'app

    def restore_application_state(self):
            """Ripristina lo stato dell'applicazione"""
            try:
                state_file = os.path.join("data", "app_state.json")
                if os.path.exists(state_file):
                    with open(state_file, 'r', encoding='utf-8') as f:
                        app_state = json.load(f)

                    # Ripristina le impostazioni
                    if 'window_geometry' in app_state:
                        self.root.geometry(app_state['window_geometry'])
                    if 'theme' in app_state:
                        self.style.theme_use(app_state['theme'])
                    if 'active_tab' in app_state:
                        self.notebook.select(app_state['active_tab'])

            except Exception as e:
                print(f"Errore nel ripristino dello stato: {str(e)}")
                # Continua con le impostazioni predefinite

    def check_updates(self):
            """Controlla la disponibilità di aggiornamenti"""
            try:
                # Qui implementare la logica per il controllo degli aggiornamenti
                # Per ora è solo un placeholder
                updates_available = False

                if updates_available:
                    if messagebox.askyesno(
                            "Aggiornamenti",
                            "È disponibile una nuova versione. Vuoi scaricarla?"
                    ):
                        webbrowser.open('https://github.com/SERGE3-g')
            except Exception as e:
                print(f"Errore nel controllo aggiornamenti: {str(e)}")

    def show_error_dialog(self, title, message, error=None):
            """Mostra una finestra di dialogo per gli errori"""
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            dialog.geometry("500x300")
            dialog.transient(self.root)
            dialog.grab_set()

            frame = ttk.Frame(dialog, padding="10")
            frame.pack(fill='both', expand=True)

            # Icona errore
            ttk.Label(
                frame,
                text="⚠️",
                font=('Arial', 48)
            ).pack(pady=10)

            # Messaggio principale
            ttk.Label(
                frame,
                text=message,
                wraplength=400,
                justify='center'
            ).pack(pady=10)

            # Dettagli errore
            if error:
                text = tk.Text(frame, height=4, wrap='word')
                text.insert('1.0', str(error))
                text.config(state='disabled')
                text.pack(fill='x', pady=10)

            # Pulsante chiudi
            ttk.Button(
                frame,
                text="Chiudi",
                command=dialog.destroy
            ).pack(pady=10)

            # Pulsante copia negli appunti
            if error:
                ttk.Button(
                    frame,
                    text="Copia negli Appunti",
                    command=lambda: self.copy_to_clipboard(str(error))
                ).pack(pady=5)

    def copy_to_clipboard(self, text):
            """Copia il testo negli appunti"""
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()


if __name__ == "__main__":
        try:
            # Impostazioni di base per l'applicazione
            if sys.platform.startswith('win'):
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)

            # Creazione e avvio dell'applicazione

            app = MainApp()

        except Exception as e:
            messagebox.showerror(
                "Errore Critico",
                f"Errore durante l'avvio dell'applicazione:\n{str(e)}"
            )
            sys.exit(1)