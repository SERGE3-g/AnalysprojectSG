import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib
import os
from datetime import datetime


class LoginManager:
    def __init__(self):
        self.db_path = 'data/users.db'
        self.setup_database()

    def setup_database(self):
        """Verifica che il database esista"""
        if not os.path.exists(self.db_path):
            from init_db import initialize_database
            initialize_database()

    def verify_login(self, username, password):
        """Verifica le credenziali di login"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Hash della password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Verifica credenziali e stato attivo
            cursor.execute('''
                SELECT id, role 
                FROM users 
                WHERE username = ? 
                AND password = ? 
                AND is_active = 1
            ''', (username, hashed_password))

            result = cursor.fetchone()

            if result:
                user_id, role = result

                # Aggiorna last_login
                cursor.execute('''
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (user_id,))

                # Log dell'accesso
                cursor.execute('''
                    INSERT INTO access_logs (user_id, action)
                    VALUES (?, ?)
                ''', (user_id, 'login_success'))

                conn.commit()
                conn.close()
                return role

            # Log del tentativo fallito
            cursor.execute('''
                SELECT id FROM users WHERE username = ?
            ''', (username,))
            user_result = cursor.fetchone()
            if user_result:
                cursor.execute('''
                    INSERT INTO access_logs (user_id, action)
                    VALUES (?, ?)
                ''', (user_result[0], 'login_failed'))
                conn.commit()

            conn.close()
            return None

        except sqlite3.Error as e:
            print(f"Errore database: {e}")
            return None


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
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showerror("Errore", "Inserisci username e password")
            return

        role = self.login_manager.verify_login(username, password)

        if role:
            self.root.destroy()
            self.on_login_success(username, role)
        else:
            messagebox.showerror("Errore", "Credenziali non valide o account disattivato")
            self.password_var.set("")  # Pulisce solo la password

    def run(self):
        """Avvia la finestra di login"""
        self.root.mainloop()


# Test solo se eseguito direttamente
if __name__ == "__main__":
    def on_login_success(username, role):
        print(f"Login effettuato: {username} ({role})")


    login_window = LoginWindow(on_login_success)
    login_window.run()