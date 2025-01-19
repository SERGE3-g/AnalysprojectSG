import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from pathlib import Path

from registration_window import RegistrationWindow

class LoginWindow:
    def __init__(self, on_login_success, db_path=None):
        """
        :param on_login_success: callback da eseguire dopo login riuscito
        :param db_path: percorso del file .db da usare, se il LoginManager lo supporta
        """
        self.root = tk.Tk()
        self.root.title("Login - Multi-Tool Analyzer")
        self.root.geometry("400x600")
        self.root.resizable(False, False)

        # Se il tuo LoginManager accetta un percorso DB personalizzato
        from src.login_manager import LoginManager
        self.login_manager = LoginManager()  # o: LoginManager(db_path=db_path)

        # Stampa/Log del DB usato (se esposto dal LoginManager)
        try:
            current_db = getattr(self.login_manager, 'db_path', 'Percorso DB non definito in LoginManager')
            print(f"[LoginWindow] Using DB: {current_db}")
        except Exception as e:
            print(f"[LoginWindow] Impossibile ottenere db_path: {e}")

        self.on_login_success = on_login_success

        # Configura lo stile
        self.setup_style()
        # Crea l’interfaccia
        self.create_gui()
        self.center_window()

    def setup_style(self):
        """Configura gli stili personalizzati"""
        style = ttk.Style()
        style.configure('Login.TFrame', background='#f0f0f0')
        style.configure('Accent.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=10)
        style.configure('Register.TButton',
                        font=('Arial', 10),
                        padding=10)

    def create_gui(self):
        """Crea l'interfaccia di login"""
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
        username_entry = ttk.Entry(
            login_frame,
            textvariable=self.username_var,
            font=('Arial', 12)
        )
        username_entry.pack(fill=tk.X, pady=(0, 10))
        username_entry.bind('<FocusOut>', self.show_last_login)

        # Password
        ttk.Label(login_frame, text="Password:").pack(fill=tk.X)
        self.password_var = tk.StringVar()
        ttk.Entry(
            login_frame,
            textvariable=self.password_var,
            show="●",
            font=('Arial', 12)
        ).pack(fill=tk.X, pady=(0, 5))

        # Link "Password dimenticata?"
        forgot_label = tk.Label(login_frame, text="Password dimenticata?",
                                fg="blue", cursor="hand2")
        forgot_label.pack(anchor="e", pady=(0, 10))
        forgot_label.bind("<Button-1>", lambda e: self.forgot_password_dialog())

        # Frame per le informazioni sull'ultimo accesso
        self.last_login_frame = ttk.LabelFrame(login_frame, text="Ultimo Accesso", padding=10)
        self.last_login_frame.pack(fill=tk.X, pady=(0, 20))
        self.last_login_label = ttk.Label(self.last_login_frame, text="")
        self.last_login_label.pack(fill=tk.X)

        # Bottone login
        ttk.Button(
            login_frame,
            text="Login",
            command=self.login,
            style='Accent.TButton'
        ).pack(fill=tk.X, pady=10)

        # Separatore
        ttk.Separator(login_frame, orient='horizontal').pack(fill=tk.X, pady=10)

        # Bottone registrazione
        ttk.Button(
            login_frame,
            text="Registrati",
            command=self.show_registration,
            style='Register.TButton'
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

    def forgot_password_dialog(self):
        """Mostra un piccolo dialog per resettare la password"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Reset Password")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Inserisci il tuo username:", font=("Arial", 11)).pack(pady=(20,5))
        user_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=user_var).pack(fill="x", padx=20)

        # Chiediamo anche la nuova password (oppure generiamo in automatico)
        ttk.Label(dialog, text="Nuova Password:", font=("Arial", 11)).pack(pady=(10,5))
        newpass_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=newpass_var, show="●").pack(fill="x", padx=20)

        # Bottone conferma
        def do_reset():
            username = user_var.get().strip()
            newpass = newpass_var.get().strip()
            if not username or not newpass:
                messagebox.showerror("Errore", "Compila username e nuova password!")
                return

            # Proviamo a resettare:
            try:
                # ipotizziamo tu abbia un metodo di login_manager tipo:
                # success, msg = self.login_manager.reset_password(username, newpass)
                # se non ce l'hai, puoi copiare la logica di "change_password" su un determinato user
                hashed = self.login_manager.hash_password(newpass)  # se hai un helper
                # Oppure:
                # import hashlib
                # hashed = hashlib.sha256(newpass.encode()).hexdigest()

                # Esecuzione del reset sul DB:
                # In mancanza di un vero "reset_password", usiamo la change logic:
                conn = self.login_manager.get_connection()  # se esiste
                # altrimenti: import sqlite3; conn = sqlite3.connect(...)

                cursor = conn.cursor()
                # Verifica utente esiste
                cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                row = cursor.fetchone()
                if not row:
                    messagebox.showwarning("Attenzione", f"L'utente '{username}' non esiste.")
                    return

                # Aggiorna password
                cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"Password per '{username}' reimpostata.")
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile resettare la password: {e}")

        ttk.Button(dialog, text="Reset Password", command=do_reset).pack(pady=15)

    def show_error_dialog(self, message):
        messagebox.showerror("Errore", message)

    def show_info_dialog(self, message):
        messagebox.showinfo("Informazione", message)

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

    def login(self):
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get().strip()

            if not username or not password:
                self.show_error_dialog("Inserisci username e password")
                return

            role = self.login_manager.verify_login(username, password)
            if role:
                self.root.destroy()
                self.on_login_success(username, role)
            else:
                self.show_error_dialog("Credenziali non valide o account disattivato")
                self.password_var.set("")

        except Exception as e:
            self.show_error_dialog(f"Errore durante il login: {str(e)}")
            print(f"Errore login: {str(e)}")

    def show_registration(self):
        try:
            RegistrationWindow(self.root)
        except Exception as e:
            self.show_error_dialog(f"Errore apertura registrazione: {str(e)}")
            print(f"Errore registrazione: {str(e)}")

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

            if os.path.exists('assets/icon.ico'):
                try:
                    self.root.iconbitmap('assets/icon.ico')
                except:
                    pass

            self.root.mainloop()
        except Exception as e:
            self.show_error_dialog(f"Errore durante l'avvio: {str(e)}")
            print(f"Errore avvio: {str(e)}")
            sys.exit(1)


# Test
if __name__ == "__main__":
    def on_login_success(username, role):
        print(f"Login effettuato: {username} ({role})")

    try:
        login_window = LoginWindow(on_login_success)
        login_window.run()
    except Exception as e:
        print(f"Errore critico: {str(e)}")
        sys.exit(1)
