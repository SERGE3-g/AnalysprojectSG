from cx_Freeze import setup, Executable
import os

# Inclusione di file e moduli personalizzati
include_files = [
    'data/new_users.db',                 # Database
    'docs/manuale.pdf',              # Manuale PDF
    ('src/', 'src/'),                # Include la directory "src" con moduli personalizzati
    ('assets/', 'assets/'),          # Include la directory "assets" con immagini o file
]

# Inclusione delle librerie usate
packages = [
    "tkinter", "traceback", "threading", "datetime", "pandas", "openpyxl",
    "os", "re", "json", "queue", "matplotlib", "sqlite3", "hashlib", "sys",
    "logging", "pathlib", "qrcode", "reportlab", "requests", "socket", "random",
    "string", "docx", "xml", "dataclasses", "typing"
]

# Configurazione delle opzioni di build
build_exe_options = {
    "packages": packages,         # Pacchetti richiesti
    "include_files": include_files,  # File aggiuntivi richiesti
    "excludes": ["pytest", "unittest"],  # Moduli da escludere
    "optimize": 2                 # Ottimizzazione del codice (opzionale)
}

# Configurazione dell'eseguibile
executables = [
    Executable(
        "main.py",                # File principale
        base="Win32GUI" if os.name == 'nt' else None,  # Base GUI per Windows
        target_name="BusinessIntelligenceSuite",  # Nome dell'eseguibile
        icon="assets/icon.ico"    # Icona personalizzata (opzionale)
    )
]

# Configurazione finale di cx_Freeze
setup(
    name="Business Intelligence Suite",
    version="1.0",
    description="Applicazione di Business Intelligence per analisi avanzate",
    options={"build_exe": build_exe_options},
    executables=executables
)
