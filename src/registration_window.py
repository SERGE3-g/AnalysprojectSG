import tkinter as tk
from tkinter import ttk, messagebox
import re
from src.login_manager import LoginManager


class RegistrationWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Registrazione Nuovo Utente")
        self.top.geometry("500x750")
        self.top.resizable(False, False)
        self.top.configure(bg='#2E2E2E')  # Sfondo scuro

        self.login_manager = LoginManager()
        self.setup_style()
        self.create_gui()
        self.center_window()

    def setup_style(self):
        """Configura gli stili personalizzati"""
        style = ttk.Style()

        # Configurazione stile dark
        style.configure('Dark.TFrame', background='#2E2E2E')
        style.configure('Dark.TLabel',
                        background='#2E2E2E',
                        foreground='white',
                        font=('Arial', 12))
        style.configure('DarkTitle.TLabel',
                        background='#2E2E2E',
                        foreground='white',
                        font=('Helvetica', 20, 'bold'))
        style.configure('Dark.TEntry',
                        fieldbackground='#3E3E3E',
                        foreground='white',
                        insertcolor='white',
                        font=('Arial', 11))
        style.configure('Dark.TButton',
                        background='#4A90E2',
                        foreground='white',
                        font=('Arial', 11, 'bold'),
                        padding=10)
        style.configure('Dark.TLabelframe',
                        background='#2E2E2E',
                        foreground='white')
        style.configure('Dark.TLabelframe.Label',
                        background='#2E2E2E',
                        foreground='white',
                        font=('Arial', 12, 'bold'))
        style.configure('Dark.TCheckbutton',
                        background='#2E2E2E',
                        foreground='white')

    def create_gui(self):
        """Crea l'interfaccia di registrazione"""
        # Frame principale
        main_frame = ttk.Frame(self.top, style='Dark.TFrame', padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titolo
        ttk.Label(
            main_frame,
            text="Registrazione",
            style='DarkTitle.TLabel'
        ).pack(pady=20)

        # Frame form con sfondo scuro
        form_frame = ttk.LabelFrame(
            main_frame,
            text="Dati Utente",
            style='Dark.TLabelframe',
            padding=20
        )
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Campi del form
        self.fields = {}
        field_configs = [
            ("Nome:", "first_name", ""),
            ("Cognome:", "last_name", ""),
            ("Email:", "email", ""),
            ("Username:", "username", ""),
            ("Password:", "password", "●"),
            ("Conferma Password:", "confirm_password", "●")
        ]

        for label_text, field_name, show in field_configs:
            # Container per ogni campo
            field_frame = ttk.Frame(form_frame, style='Dark.TFrame')
            field_frame.pack(fill=tk.X, pady=10)

            # Label
            ttk.Label(
                field_frame,
                text=label_text,
                style='Dark.TLabel'
            ).pack(fill=tk.X, pady=(0, 5))

            # Entry field
            var = tk.StringVar()
            self.fields[field_name] = var

            entry = ttk.Entry(
                field_frame,
                textvariable=var,
                show=show if show else "",
                style='Dark.TEntry',
                font=('Arial', 11)
            )
            entry.pack(fill=tk.X)

            # Validazione email
            if field_name == 'email':
                entry.bind('<FocusOut>', self.validate_email)

        # Checkbox termini e condizioni
        terms_frame = ttk.Frame(form_frame, style='Dark.TFrame')
        terms_frame.pack(fill=tk.X, pady=20)

        self.accept_terms = tk.BooleanVar()
        ttk.Checkbutton(
            terms_frame,
            text="Accetto i termini e le condizioni",
            variable=self.accept_terms,
            style='Dark.TCheckbutton'
        ).pack(pady=5)

        # Frame bottoni
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.pack(fill=tk.X, pady=20)

        # Bottoni
        ttk.Button(
            button_frame,
            text="Registrati",
            command=self.register,
            style='Dark.TButton'
        ).pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Annulla",
            command=self.top.destroy,
            style='Dark.TButton'
        ).pack(fill=tk.X)

    def validate_email(self, event=None):
        """Valida il formato dell'email"""
        email = self.fields['email'].get()
        if email:
            pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(pattern, email):
                messagebox.showwarning("Attenzione", "Formato email non valido")
                return False
        return True

    def validate_fields(self):
        """Valida tutti i campi del form"""
        # Verifica campi vuoti
        field_names = {
            'first_name': 'Nome',
            'last_name': 'Cognome',
            'email': 'Email',
            'username': 'Username',
            'password': 'Password',
            'confirm_password': 'Conferma Password'
        }

        for field_name, display_name in field_names.items():
            if not self.fields[field_name].get().strip():
                messagebox.showerror("Errore", f"Il campo {display_name} è obbligatorio")
                return False

        # Verifica email
        if not self.validate_email():
            return False

        # Verifica password
        password = self.fields['password'].get()
        if len(password) < 8:
            messagebox.showerror("Errore", "La password deve essere di almeno 8 caratteri")
            return False

        if password != self.fields['confirm_password'].get():
            messagebox.showerror("Errore", "Le password non coincidono")
            return False

        # Verifica termini e condizioni
        if not self.accept_terms.get():
            messagebox.showerror("Errore", "Devi accettare i termini e le condizioni")
            return False

        return True

    def register(self):
        """Gestisce il processo di registrazione"""
        if not self.validate_fields():
            return

        success, message = self.login_manager.register_user(
            username=self.fields['username'].get(),
            password=self.fields['password'].get(),
            email=self.fields['email'].get(),
            first_name=self.fields['first_name'].get(),
            last_name=self.fields['last_name'].get()
        )

        if success:
            messagebox.showinfo("Successo", message)
            self.top.destroy()
        else:
            messagebox.showerror("Errore", message)

    def center_window(self):
        """Centra la finestra sullo schermo"""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f'{width}x{height}+{x}+{y}')


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    registration = RegistrationWindow(root)
    root.mainloop()