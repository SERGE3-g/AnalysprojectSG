import hashlib
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

# Calcolo percorso DB in base alla directory di questo file .py
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # crea la cartella data se non c'è

DB_FILE = DATA_DIR / "users.db"

class UserManagementWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Gestione Utenti")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        self.create_gui()
        self.load_users()

    def create_gui(self):
        # Frame principale
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame per creazione utente
        create_frame = ttk.LabelFrame(main_frame, text="Crea Nuovo Utente", padding=10)
        create_frame.pack(fill=tk.X, padx=5, pady=5)

        # Griglia per input
        grid_frame = ttk.Frame(create_frame)
        grid_frame.pack(fill=tk.X, padx=5, pady=5)

        # Username
        ttk.Label(grid_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.username_var).grid(row=0, column=1, padx=5, pady=5)

        # Password
        ttk.Label(grid_frame, text="Password:").grid(row=0, column=2, padx=5, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.password_var, show="●").grid(row=0, column=3, padx=5, pady=5)

        # Ruolo
        ttk.Label(grid_frame, text="Ruolo:").grid(row=0, column=4, padx=5, pady=5)
        self.role_var = tk.StringVar(value="user")
        role_combo = ttk.Combobox(grid_frame, textvariable=self.role_var, values=["user", "admin"], state='readonly')
        role_combo.grid(row=0, column=5, padx=5, pady=5)

        # Email
        ttk.Label(grid_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.email_var).grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

        # Nome
        ttk.Label(grid_frame, text="Nome:").grid(row=1, column=3, padx=5, pady=5)
        self.first_name_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.first_name_var).grid(row=1, column=4, sticky='ew', padx=5, pady=5)

        # Cognome
        ttk.Label(grid_frame, text="Cognome:").grid(row=1, column=5, padx=5, pady=5)
        self.last_name_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.last_name_var).grid(row=1, column=6, sticky='ew', padx=5, pady=5)

        # Bottone crea
        ttk.Button(create_frame, text="Crea Utente", command=self.create_user).pack(pady=10)

        # Frame lista utenti
        list_frame = ttk.LabelFrame(main_frame, text="Lista Utenti", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Definizione colonne
        columns = (
            'ID', 'Username', 'Ruolo',
            'Email', 'Nome', 'Cognome',
            'Created', 'Last Login', 'Status'
        )
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        # Impostazione intestazione e larghezza colonne
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Ruolo':
                self.tree.column(col, width=120, stretch=True)
            else:
                self.tree.column(col, width=100, stretch=True)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Frame bottoni azioni
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="Elimina Utente", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Modifica Password", command=self.change_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Attiva/Disattiva", command=self.toggle_user_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Aggiorna Lista", command=self.load_users).pack(side=tk.LEFT, padx=5)

    def create_user(self):
        # Validazione input
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        role = self.role_var.get()
        email = self.email_var.get().strip()
        first_name = self.first_name_var.get().strip()
        last_name = self.last_name_var.get().strip()

        if not all([username, password, role, email, first_name, last_name]):
            messagebox.showerror("Errore", "Compila tutti i campi obbligatori (username, password, email, nome, cognome).")
            return

        try:
            conn = sqlite3.connect(str(DB_FILE))  # Usa il percorso assoluto
            cursor = conn.cursor()

            # Verifica se l'username esiste già
            cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                messagebox.showerror("Errore", f"Username '{username}' già esistente.")
                return

            # Hash della password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Inserimento nuovo utente
            cursor.execute('''
                INSERT INTO users (
                    username, password, role, email,
                    first_name, last_name
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, role, email, first_name, last_name))

            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", f"Utente '{username}' creato con successo.")
            self.clear_form()
            self.load_users()

        except sqlite3.Error as e:
            messagebox.showerror("Errore Database", str(e))

    def load_users(self):
        try:
            # Pulisci la lista esistente
            for item in self.tree.get_children():
                self.tree.delete(item)

            conn = sqlite3.connect(str(DB_FILE))
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    id, username, role, email,
                    first_name, last_name,
                    created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            ''')

            for row in cursor.fetchall():
                row = list(row)  # convert tuple in list

                # Format date/time
                row[6] = row[6][:19] if row[6] else "Mai"  # created_at
                row[7] = row[7][:19] if row[7] else "Mai"  # last_login

                # is_active -> "Attivo"/"Disattivato"
                row[8] = "Attivo" if row[8] == 1 else "Disattivato"

                self.tree.insert("", tk.END, values=row)

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Errore Database", str(e))

    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un utente da eliminare")
            return

        user = self.tree.item(selected[0])['values']
        username = user[1]

        if username == 'admin':
            messagebox.showerror("Errore", "Non puoi eliminare l'utente admin")
            return

        if messagebox.askyesno("Conferma", f"Vuoi davvero eliminare l'utente {username}?"):
            try:
                conn = sqlite3.connect(str(DB_FILE))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", f"Utente '{username}' eliminato.")
                self.load_users()

            except sqlite3.Error as e:
                messagebox.showerror("Errore Database", str(e))

    def change_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un utente")
            return

        user = self.tree.item(selected[0])['values']
        username = user[1]

        dialog = tk.Toplevel(self.window)
        dialog.title("Cambia Password")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Nuova password per {username}:").pack(pady=10)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="●").pack(pady=10)

        def update_password():
            new_password = password_var.get()
            if not new_password:
                messagebox.showerror("Errore", "Inserisci una password")
                return

            try:
                conn = sqlite3.connect(str(DB_FILE))
                cursor = conn.cursor()

                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
                cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))

                conn.commit()
                conn.close()

                messagebox.showinfo("Successo", "Password aggiornata con successo")
                dialog.destroy()

            except sqlite3.Error as e:
                messagebox.showerror("Errore Database", str(e))

        ttk.Button(dialog, text="Aggiorna", command=update_password).pack(pady=10)

    def toggle_user_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Attenzione", "Seleziona un utente")
            return

        user = self.tree.item(selected[0])['values']
        username = user[1]
        current_status = user[8]

        if username == 'admin':
            messagebox.showerror("Errore", "Non puoi disattivare l'utente admin")
            return

        new_status = 0 if current_status == "Attivo" else 1

        try:
            conn = sqlite3.connect(str(DB_FILE))
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = ? WHERE username = ?", (new_status, username))
            conn.commit()
            conn.close()

            messagebox.showinfo("Successo", "Stato utente aggiornato con successo")
            self.load_users()

        except sqlite3.Error as e:
            messagebox.showerror("Errore Database", str(e))

    def clear_form(self):
        self.username_var.set("")
        self.password_var.set("")
        self.role_var.set("user")
        self.email_var.set("")
        self.first_name_var.set("")
        self.last_name_var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = UserManagementWindow(root)
    root.mainloop()