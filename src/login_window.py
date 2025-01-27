import logging
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from pathlib import Path

from registration_window import RegistrationWindow
from login_manager import LoginManager

class LoginWindow:
    def __init__(self, on_login_success, db_path=None):
        self.root = tk.Tk()
        self.root.title("Login - Multi-Tool Analyzer")
        self.root.geometry("400x600")
        self.root.resizable(False, False)

        self.login_manager = LoginManager()
        self.on_login_success = on_login_success
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.setup_style()
        self.create_gui()
        self.center_window()

    def setup_style(self):
        style = ttk.Style()
        style.configure('Login.TFrame', background='#f0f0f0')
        style.configure('Accent.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=10)
        style.configure('Register.TButton',
                        font=('Arial', 10),
                        padding=10)

    def create_gui(self):
        main_frame = ttk.Frame(self.root, style='Login.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Logo/Title
        ttk.Label(
            main_frame,
            text="Multi-Tool Analyzer",
            font=('Helvetica', 20, 'bold'),
            background='#f0f0f0'
        ).pack(pady=20)

        # Login Frame
        login_frame = ttk.LabelFrame(main_frame, text="Login", padding=20)
        login_frame.pack(fill=tk.X, padx=20, pady=20)

        # Username
        ttk.Label(login_frame, text="Username:").pack(fill=tk.X)
        username_entry = ttk.Entry(
            login_frame,
            textvariable=self.username_var,
            font=('Arial', 12)
        )
        username_entry.pack(fill=tk.X, pady=(0, 10))
        username_entry.bind('<FocusOut>', self.show_last_login)

        # Password
        ttk.Label(login_frame, text="Password:").pack(fill=tk.X)
        password_entry = ttk.Entry(
            login_frame,
            textvariable=self.password_var,
            show="●",
            font=('Arial', 12)
        )
        password_entry.pack(fill=tk.X, pady=(0, 5))

        # Bind Enter key to both entries
        username_entry.bind('<Return>', lambda e: self.login())
        password_entry.bind('<Return>', lambda e: self.login())

        # Reset Password Link
        forgot_label = tk.Label(login_frame, text="Password dimenticata?",
                               fg="blue", cursor="hand2")
        forgot_label.pack(anchor="e", pady=(0, 10))
        forgot_label.bind("<Button-1>", lambda e: self.forgot_password_dialog())

        # Last Login Info
        self.last_login_frame = ttk.LabelFrame(login_frame, text="Ultimo Accesso", padding=10)
        self.last_login_frame.pack(fill=tk.X, pady=(0, 20))
        self.last_login_label = ttk.Label(self.last_login_frame, text="")
        self.last_login_label.pack(fill=tk.X)

        # Login Button
        ttk.Button(
            login_frame,
            text="Login",
            command=self.login,
            style='Accent.TButton'
        ).pack(fill=tk.X, pady=10)

        ttk.Separator(login_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Register Button
        ttk.Button(
            login_frame,
            text="Registrati",
            command=self.show_registration,
            style='Register.TButton'
        ).pack(fill=tk.X)

        # Footer
        ttk.Label(
            main_frame,
            text="© 2025 SergeGuea | Tutti i diritti riservati",
            font=('Arial', 8),
            background='#f0f0f0'
        ).pack(side=tk.BOTTOM, pady=10)

    def login(self):
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get().strip()

            if not username or not password:
                messagebox.showerror("Errore", "Inserisci username e password")
                return

            role = self.login_manager.verify_login(username, password)
            if role:
                logging.info(f"Login riuscito per l'utente: {username}")
                self.root.withdraw()  # Hide instead of destroy
                self.on_login_success(username, role)
            else:
                messagebox.showerror("Errore", "Credenziali non valide")
                self.password_var.set("")
                logging.warning(f"Tentativo di login fallito per l'utente: {username}")

        except Exception as e:
            logging.error(f"Errore durante il login: {e}")
            messagebox.showerror("Errore", str(e))
            self.password_var.set("")

    def show_last_login(self, event=None):
        username = self.username_var.get().strip()
        if username:
            last_login = self.login_manager.get_last_login_details(username)
            if last_login:
                info_text = f"""Ultimo accesso: {last_login['last_login']}
IP: {last_login['ip_address']}
Sistema: {last_login['user_agent']}"""
                self.last_login_label.config(text=info_text)
            else:
                self.last_login_label.config(text="Nessun accesso precedente")

    def forgot_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Reset Password")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Inserisci il tuo username:", font=("Arial", 11)).pack(pady=(20,5))
        user_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=user_var).pack(fill="x", padx=20)

        ttk.Label(dialog, text="Nuova Password:", font=("Arial", 11)).pack(pady=(10,5))
        newpass_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=newpass_var, show="●").pack(fill="x", padx=20)

        def do_reset():
            username = user_var.get().strip()
            newpass = newpass_var.get().strip()
            if not username or not newpass:
                messagebox.showerror("Errore", "Compila username e nuova password!")
                return

            try:
                ok, msg = self.login_manager.request_password_reset(username)
                if ok:
                    ok, msg = self.login_manager.reset_forgotten_password(username, newpass)
                    if ok:
                        messagebox.showinfo("Successo", "Password reimpostata con successo")
                        dialog.destroy()
                    else:
                        messagebox.showerror("Errore", msg)
                else:
                    messagebox.showerror("Errore", msg)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile resettare la password: {e}")

        ttk.Button(dialog, text="Reset Password", command=do_reset).pack(pady=15)

    def show_registration(self):
        try:
            RegistrationWindow(self.root)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore apertura registrazione: {str(e)}")
            logging.error(f"Errore registrazione: {str(e)}")

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def run(self):
        try:
            if sys.platform.startswith('win'):
                self.root.tk.call('tk', 'scaling', 1.5)
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante l'avvio: {str(e)}")
            logging.error(f"Errore avvio: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    def on_login_success(username, role):
        print(f"Login effettuato: {username} ({role})")

    login_window = LoginWindow(on_login_success)
    login_window.run()