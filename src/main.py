import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from datetime import datetime
import webbrowser
from fiscal_analyzer import FiscalTab
from file_analyzer import FileTab
from inventory_manager import InventoryTab
from sla_analyzer import SLATab
from login import LoginWindow
from user_management import UserManagementWindow


class MainApp:
    VERSION = "1.0"

    def __init__(self):
        # Inizializzazione variabili utente
        self.current_user = None
        self.user_role = None
        self.user_management_window = None

        # Avvia il login
        self.start_login()

    def start_login(self):
        """Avvia il processo di login"""
        login = LoginWindow(self.on_login_success)
        login.run()

    def on_login_success(self, username, role):
        """Callback per login riuscito"""
        self.current_user = username
        self.user_role = role
        self.create_main_window()

    def create_main_window(self):
        """Crea la finestra principale dopo il login"""
        self.root = tk.Tk()
        self.root.title(f"Multi-Tool Analyzer - {self.current_user}")
        self.root.geometry("1200x800")

        # Inizializza variabili
        self.status_var = tk.StringVar(value=f"Utente: {self.current_user} ({self.user_role})")

        # Setup interfaccia
        self.setup_style()
        self.create_menu()
        self.create_toolbar()
        self.create_gui()

        # Avvia l'applicazione
        self.run()

    def setup_style(self):
        """Configura lo stile dell'applicazione"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Header
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
        version_menu.add_command(label="Versione " + self.VERSION, command=self.show_version)

    def create_toolbar(self):
        """Crea la barra degli strumenti"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', pady=1)

        # Ricerca globale
        ttk.Label(toolbar, text="Cerca:").pack(side='left', padx=2)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.global_search)
        ttk.Entry(toolbar, textvariable=self.search_var).pack(side='left', padx=2, expand=True, fill='x')

    def create_gui(self):
        """Crea l'interfaccia principale"""
        # Notebook per le schede
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # Creazione delle schede
        self.fiscal_tab = FiscalTab(self.notebook)
        self.file_tab = FileTab(self.notebook)
        self.inventory_tab = InventoryTab(self.notebook)
        self.sla_tab = SLATab(self.notebook)

        # Status bar
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
        theme_combo = ttk.Combobox(app_frame, textvariable=theme_var,
                                   values=["Chiaro", "Scuro"], state='readonly')
        theme_combo.pack(side=tk.LEFT, padx=5)

        # Lingua
        ttk.Label(app_frame, text="Lingua:").pack(side=tk.LEFT, padx=5)
        lang_var = tk.StringVar(value="Italiano")
        lang_combo = ttk.Combobox(app_frame, textvariable=lang_var,
                                  values=["Italiano", "English"], state='readonly')
        lang_combo.pack(side=tk.LEFT, padx=5)

        # Impostazioni notifiche
        notif_frame = ttk.LabelFrame(main_frame, text="Notifiche", padding=10)
        notif_frame.pack(fill=tk.X, pady=5)

        email_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Notifiche email",
                        variable=email_var).pack(anchor=tk.W)

        desktop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Notifiche desktop",
                        variable=desktop_var).pack(anchor=tk.W)

        # Bottoni
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)

        ttk.Button(button_frame, text="Salva",
                   command=lambda: messagebox.showinfo("Info", "Impostazioni salvate")).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Annulla",
                   command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)

    def show_contact(self):
        """Mostra la finestra di contatto"""
        contact_window = tk.Toplevel(self.root)
        contact_window.title("Contattaci")
        contact_window.geometry("400x300")
        contact_window.transient(self.root)
        contact_window.grab_set()

        frame = ttk.Frame(contact_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Info di contatto
        ttk.Label(frame, text="Contatti",
                  font=("Arial", 14, "bold")).pack(pady=10)

        contacts = [
            ("Email:", "gueaserge@gmail.com"),
            ("Telefono:", "+39 389-297-8507"),
            ("Sito Web:", "https://github.com/SERGE3-g"),
            ("Orari:", "Lun-Ven: 9:00-18:00")
        ]

        for label, value in contacts:
            contact_frame = ttk.Frame(frame)
            contact_frame.pack(fill=tk.X, pady=5)
            ttk.Label(contact_frame, text=label,
                      font=("Arial", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(contact_frame, text=value).pack(side=tk.LEFT, padx=5)

        ttk.Button(frame, text="Chiudi",
                   command=contact_window.destroy).pack(side=tk.BOTTOM, pady=20)

    def show_version(self):
        """Mostra informazioni sulla versione"""
        version_info = f"""
        Multi-Tool Analyzer
        Versione {self.VERSION}

        Data rilascio: 16 Gennaio 2025
        Build: 2025.01.16.001

        Sviluppato da: SergeGuea
        Sistema: Python {sys.version_info.major}.{sys.version_info.minor}

        Copyright © 2025
        Tutti i diritti riservati
        """
        messagebox.showinfo("Informazioni Versione", version_info)

    def show_user_management(self):
        """Mostra la gestione utenti (solo admin)"""
        if self.user_role != 'admin':
            messagebox.showerror("Errore", "Accesso non autorizzato")
            return

        # Se la finestra è già aperta, la porta in primo piano
        if self.user_management_window is not None:
            try:
                self.user_management_window.window.lift()
                self.user_management_window.window.focus_force()
                return
            except tk.TclError:
                # Se la finestra è stata chiusa, il riferimento non è più valido
                self.user_management_window = None

        # Crea una nuova finestra di gestione utenti
        self.user_management_window = UserManagementWindow(self.root)

        # Configura il callback per quando la finestra viene chiusa
        self.user_management_window.window.protocol("WM_DELETE_WINDOW",
                                                    lambda: self.on_user_management_close())

    def on_user_management_close(self):
        """Gestisce la chiusura della finestra di gestione utenti"""
        if self.user_management_window is not None:
            self.user_management_window.window.destroy()
            self.user_management_window = None

    def show_docs(self):
        """Mostra la documentazione"""
        webbrowser.open('https://github.com/SERGE3-g')

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

    def logout(self):
        """Gestisce il logout"""
        if messagebox.askyesno("Logout", "Vuoi effettuare il logout?"):
            # Chiudi eventuali finestre aperte
            if self.user_management_window is not None:
                self.user_management_window.window.destroy()
                self.user_management_window = None

            self.root.destroy()
            self.start_login()

    def quit_app(self):
        """Chiude l'applicazione"""
        if messagebox.askokcancel("Esci", "Vuoi davvero uscire dall'applicazione?"):
            try:
                self.root.quit()
                sys.exit(0)
            except:
                sys.exit(0)

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

        # Text widget con scrollbar
        frame = ttk.Frame(dialog, padding="5")
        frame.pack(fill='both', expand=True)

        text = tk.Text(frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for title, content in results:
            text.insert('end', f"\n=== {title} ===\n{content}\n")

        text.config(state='disabled')

        def run(self):
            """Avvia l'applicazione"""
            try:
                # Centra la finestra
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                x = (screen_width - 1200) // 2
                y = (screen_height - 800) // 2
                self.root.geometry(f"1200x800+{x}+{y}")

                # Imposta il protocollo di chiusura
                self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

                # Avvia il mainloop
                self.root.mainloop()

            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'esecuzione: {str(e)}")
                sys.exit(1)

if __name__ == "__main__":
        try:
            app = MainApp()
        except Exception as e:
            messagebox.showerror("Errore Critico",
                                 f"Errore durante l'avvio dell'applicazione:\n{str(e)}")
            sys.exit(1)
