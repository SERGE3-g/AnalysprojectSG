import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os


class LoginManager:
    def __init__(self):
        self.setup_database()

    def setup_database(self):
        """Inizializza il database per gli utenti"""
        if not os.path.exists('data'):
            os.makedirs('data')

        conn = sqlite3.connect('data/users.db')
        cursor = conn.cursor()

        # Crea tabella utenti se non esiste
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Crea utente admin di default se non esiste
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', ('admin', hashed_password, 'admin'))

        conn.commit()
        conn.close()

    def verify_login(self, username, password):
        """Verifica le credenziali di login"""
        conn = sqlite3.connect('data/users.db')
        cursor = conn.cursor()

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('''
            SELECT role FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_password))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None


class LoginWindow:
    def __init__(self, on_login_success):
        self.root = tk.Tk()
        self.root.title("Login - Multi-Tool Analyzer")
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        self.login_manager = LoginManager()
        self.on_login_success = on_login_success

        self.create_gui()
        self.center_window()

    def create_gui(self):
        """Crea l'interfaccia di login"""
        style = ttk.Style()
        style.configure('Login.TFrame', background='#f0f0f0')

        # Frame principale
        main_frame = ttk.Frame(self.root, style='Login.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo o Titolo
        ttk.Label(
            main_frame,
            text="Multi-Tool Analyzer",
            font=('Helvetica', 20, 'bold'),
            background='#f0f0f0'
        ).pack(pady=20)

        # Frame login
        login_frame = ttk.LabelFrame(main_frame, text="Login", padding=20)
        login_frame.pack(fill=tk.X, padx=20, pady=20)

        # Username
        ttk.Label(login_frame, text="Username:").pack(fill=tk.X)
        self.username_var = tk.StringVar()
        ttk.Entry(
            login_frame,
            textvariable=self.username_var,
            font=('Arial', 12)
        ).pack(fill=tk.X, pady=(0, 10))

        # Password
        ttk.Label(login_frame, text="Password:").pack(fill=tk.X)
        self.password_var = tk.StringVar()
        ttk.Entry(
            login_frame,
            textvariable=self.password_var,
            show="●",
            font=('Arial', 12)
        ).pack(fill=tk.X, pady=(0, 20))

        # Bottone login
        ttk.Button(
            login_frame,
            text="Login",
            command=self.login,
            style='Accent.TButton'
        ).pack(fill=tk.X)

        # Info o link utili
        info_frame = ttk.Frame(main_frame, style='Login.TFrame')
        info_frame.pack(fill=tk.X, pady=20)

        ttk.Label(
            info_frame,
            text="Credenziali default: admin/admin123",
            font=('Arial', 9),
            background='#f0f0f0'
        ).pack()

        # Footer
        ttk.Label(
            main_frame,
            text="© 2025 SergeGuea | Tutti i diritti riservati",
            font=('Arial', 8),
            background='#f0f0f0'
        ).pack(side=tk.BOTTOM, pady=10)

        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.login())

    def center_window(self):
        """Centra la finestra sullo schermo"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def login(self):
        """Gestisce il processo di login"""
        username = self.username_var.get()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showerror("Errore", "Inserisci username e password")
            return

        role = self.login_manager.verify_login(username, password)

        if role:
            self.root.destroy()
            self.on_login_success(username, role)
        else:
            messagebox.showerror("Errore", "Credenziali non valide")
            self.password_var.set("")  # Pulisce solo la password

    def run(self):
        """Avvia la finestra di login"""
        self.root.mainloop()