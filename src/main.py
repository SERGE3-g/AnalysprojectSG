import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime
import webbrowser
from dataclasses import dataclass
from pathlib import Path
import logging
from test_analyzer_tab import TestAnalyzerTab

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_tool.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


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
            self.test_analyzer_tab = None
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
        self.test_analyzer_tab = TestAnalyzerTab(self.notebook)

        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky='ew')

        status = ttk.Label(status_frame,
                           textvariable=self.status_var,
                           style='Status.TLabel')
        status.pack(side='left', fill='x', padx=5)

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
            self.user_management_window.window.lift()
            self.user_management_window.window.focus_force()
        else:
            self.user_management_window = UserManagementWindow(self.root)

    def show_settings(self):
        """Mostra la finestra delle impostazioni"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Impostazioni")
        settings_window.geometry("600x400")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Implementa il contenuto delle impostazioni
        ttk.Label(settings_window, text="Impostazioni").pack(pady=20)

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

        contacts = [
            ("Email:", "gueaserge@gmail.com"),
            ("GitHub:", "https://github.com/SERGE3-g")
        ]

        for label, value in contacts:
            ttk.Label(frame, text=f"{label} {value}").pack(pady=5)

    def global_search(self, *args):
        """Esegue una ricerca globale"""
        search_text = self.search_var.get().lower()
        if len(search_text) < 3:
            return

        results = []
        for tab in [self.fiscal_tab, self.file_tab, self.inventory_tab,
                    self.sla_tab, self.test_analyzer_tab]:
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

        text = tk.Text(dialog, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(dialog, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        for title, content in results:
            text.insert('end', f"\n{title}\n", 'title')
            text.insert('end', f"{content}\n", 'content')
            text.insert('end', "-" * 50 + "\n", 'separator')

        text.config(state='disabled')

    def logout(self):
        """Gestisce il logout"""
        if messagebox.askyesno("Logout", "Vuoi effettuare il logout?"):
            self.root.destroy()
            self.start_login()

    def quit_app(self):
        """Chiude l'applicazione"""
        if messagebox.askokcancel("Esci", "Vuoi davvero uscire dall'applicazione?"):
            self.root.quit()
            sys.exit(0)


class LoginWindow:
    def __init__(self, callback):
        self.root = tk.Tk()
        self.root.title("Login")
        self.callback = callback
        self.create_gui()

    def create_gui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:").pack(pady=5)
        self.username = ttk.Entry(frame)
        self.username.pack(pady=5)

        ttk.Label(frame, text="Password:").pack(pady=5)
        self.password = ttk.Entry(frame, show="*")
        self.password.pack(pady=5)

        ttk.Button(frame, text="Login", command=self.login).pack(pady=20)

    def login(self):
        # Simulazione login - in produzione implementare autenticazione reale
        username = self.username.get()
        if username:
            self.root.destroy()
            self.callback(username, 'admin' if username == 'admin' else 'user')
        else:
            messagebox.showerror("Errore", "Inserire username")


class UserManagementWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Gestione Utenti")
        self.window.geometry("800x600")
        self.create_gui()

    def create_gui(self):
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Gestione Utenti").pack()


# Classi stub per le altre tab (da implementare)
class FiscalTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Fiscal')
        ttk.Label(self.frame, text="Fiscal Analysis Tab").pack()

    def search(self, query):
        return []


class FileTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='File')
        ttk.Label(self.frame, text="File Analysis Tab").pack()

    def search(self, query):
        return []


class InventoryTab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='Inventory')
        ttk.Label(self.frame, text="Inventory Management Tab").pack()

    def search(self, query):
        return []


class SLATab:
    def __init__(self, notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='SLA')
        self.create_gui()

    def create_gui(self):
        """Crea l'interfaccia grafica del tab SLA"""
        # Frame principale
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sezione metriche SLA
        metrics_frame = ttk.LabelFrame(main_frame, text="Metriche SLA", padding=10)
        metrics_frame.pack(fill=tk.X, pady=5)

        # Grid per le metriche
        metrics = [
            ("Tempo di Risposta", "4h", "95%"),
            ("Risoluzione Ticket", "24h", "90%"),
            ("Disponibilità Sistema", "99.9%", "99.95%"),
            ("Customer Satisfaction", "4.5/5", "4.8/5")
        ]

        for i, (metric, target, actual) in enumerate(metrics):
            ttk.Label(metrics_frame, text=metric).grid(row=i, column=0, padx=5, pady=2, sticky='w')
            ttk.Label(metrics_frame, text=f"Target: {target}").grid(row=i, column=1, padx=5, pady=2)
            ttk.Label(metrics_frame, text=f"Attuale: {actual}").grid(row=i, column=2, padx=5, pady=2)

        # Sezione report
        report_frame = ttk.LabelFrame(main_frame, text="Report SLA", padding=10)
        report_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview per i report
        columns = ('periodo', 'compliance', 'violazioni', 'note')
        self.report_tree = ttk.Treeview(report_frame, columns=columns, show='headings')

        # Configura colonne
        self.report_tree.heading('periodo', text='Periodo')
        self.report_tree.heading('compliance', text='Compliance')
        self.report_tree.heading('violazioni', text='Violazioni')
        self.report_tree.heading('note', text='Note')

        # Inserisci dati di esempio
        sample_data = [
            ('Gen 2025', '98%', '2', 'Nessuna criticità'),
            ('Feb 2025', '97%', '3', 'Manutenzione pianificata'),
            ('Mar 2025', '99%', '1', 'Performance ottimale')
        ]

        for item in sample_data:
            self.report_tree.insert('', tk.END, values=item)

        # Scrollbar
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)

        # Layout
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottoni azioni
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Genera Report", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Esporta Dati", command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Configura Alert", command=self.configure_alerts).pack(side=tk.LEFT, padx=5)

    def generate_report(self):
        """Genera un nuovo report SLA"""
        messagebox.showinfo("Report", "Generazione report in corso...")

    def export_data(self):
        """Esporta i dati SLA"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Export", f"Dati esportati in: {filename}")

    def configure_alerts(self):
        """Configura gli alert SLA"""
        alert_window = tk.Toplevel(self.frame)
        alert_window.title("Configurazione Alert")
        alert_window.geometry("400x300")

        ttk.Label(alert_window, text="Configurazione Alert SLA", font=('Arial', 12, 'bold')).pack(pady=10)

        # Form configurazione
        form_frame = ttk.Frame(alert_window, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Soglia Compliance:").pack(anchor='w')
        ttk.Entry(form_frame).pack(fill=tk.X, pady=5)

        ttk.Label(form_frame, text="Email Notifica:").pack(anchor='w')
        ttk.Entry(form_frame).pack(fill=tk.X, pady=5)

        ttk.Label(form_frame, text="Frequenza Check:").pack(anchor='w')
        ttk.Combobox(form_frame, values=['1h', '4h', '12h', '24h']).pack(fill=tk.X, pady=5)

        ttk.Button(form_frame, text="Salva Configurazione",
                   command=lambda: alert_window.destroy()).pack(pady=20)

    def search(self, query):
        """Implementa la ricerca nel tab SLA"""
        results = []
        query = query.lower()

        # Cerca nei report
        for item in self.report_tree.get_children():
            values = self.report_tree.item(item)['values']
            if any(query in str(value).lower() for value in values):
                results.append((
                    f"SLA Report - {values[0]}",
                    f"Compliance: {values[1]}\nViolazioni: {values[2]}\nNote: {values[3]}"
                ))

        return results


def main():
    """Funzione principale per l'avvio dell'applicazione"""
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


if __name__ == "__main__":
    main()