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


class MainApp:
    def __init__(self):
        # Inizializzazione variabili utente
        self.current_user = None
        self.user_role = None

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

    def logout(self):
        """Gestisce il logout"""
        if messagebox.askyesno("Logout", "Vuoi effettuare il logout?"):
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

    def show_settings(self):
        """Mostra la finestra delle impostazioni"""
        messagebox.showinfo("Info", "Funzionalità in sviluppo")

    def show_user_management(self):
        """Mostra la gestione utenti (solo admin)"""
        if self.user_role != 'admin':
            messagebox.showerror("Errore", "Accesso non autorizzato")
            return
        messagebox.showinfo("Info", "Gestione utenti in sviluppo")

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

            self.root.mainloop()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'esecuzione: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    app = MainApp()
