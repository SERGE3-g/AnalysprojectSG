import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
import json
import configparser
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import colorchooser
import shutil
import webbrowser
from tkcalendar import Calendar
import subprocess

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    # Fallback if tkinterdnd2 is not installed
    class TkinterDnD:
        def __init__(self):
            pass

        @staticmethod
        def Tk():
            return tk.Tk()


class SLAConfig:
    def __init__(self):
        self.config_file = 'sla_config.ini'
        self.load_config()

    def load_config(self):
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def create_default_config(self):
        self.config['Thresholds'] = {
            'SLA2': '1400',
            'SLA3': '600',
            'SLA4': '800',
            'SLA5': '600',
            'SLA6': '800'
        }
        self.config['Targets'] = {
            'SLA2': '95',
            'SLA3': '95',
            'SLA4': '95',
            'SLA5': '95',
            'SLA6': '95'
        }
        self.config['Colors'] = {
            'graph_line': '#1f77b4',
            'graph_target': '#d62728',
            'background': '#ffffff'
        }
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)


class SLAGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SLA Report Generator Pro")
        self.root.geometry("1200x800")

        # Load configuration
        self.config = SLAConfig()

        # Initialize variables before creating UI elements
        self.init_variables()

        # Create UI elements
        self.create_menu()
        self.create_notebook()
        self.create_main_tab()
        self.create_preview_tab()
        self.create_batch_tab()
        self.create_template_tab()

        # Load last session at the end
        self.load_session_from_file('last_session.json')

    def init_variables(self):
        """Initialize all necessary variables"""
        self.file_paths = {
            'SLA2': tk.StringVar(),
            'SLA3': tk.StringVar(),
            'SLA4': tk.StringVar(),
            'SLA5': tk.StringVar(),
            'SLA6': tk.StringVar()
        }
        self.output_dir = tk.StringVar()
        self.detailed_graphs = tk.BooleanVar(value=True)
        self.generate_pdf = tk.BooleanVar(value=False)
        self.send_email = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar()
        self.batch_files = []
        self.current_template = None

    def create_notebook(self):
        """Create the notebook for tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create frames for each tab
        self.main_tab = ttk.Frame(self.notebook)
        self.preview_tab = ttk.Frame(self.notebook)
        self.batch_tab = ttk.Frame(self.notebook)
        self.template_tab = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.main_tab, text="Report Generator")
        self.notebook.add(self.preview_tab, text="Preview")
        self.notebook.add(self.batch_tab, text="Batch Processing")
        self.notebook.add(self.template_tab, text="Template Manager")

    def load_session_from_file(self, filename):
        """Load session data from a file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    session_data = json.load(f)

                for name, path in session_data.get('files', {}).items():
                    if name in self.file_paths:
                        self.file_paths[name].set(path)

                if 'output_dir' in session_data:
                    self.output_dir.set(session_data['output_dir'])

        except Exception as e:
            print(f"Error loading session from {filename}: {e}")

    def save_session_to_file(self, filename):
        """Save current session data to a file"""
        session_data = {
            'files': {name: path.get() for name, path in self.file_paths.items()},
            'output_dir': self.output_dir.get()
        }

        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f)
        except Exception as e:
            print(f"Error saving session to {filename}: {e}")

    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Report", command=self.clear_fields)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def create_main_tab(self):
        """Create the main tab content"""
        main_frame = ttk.Frame(self.main_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Add main tab widgets...
        pass

    def create_preview_tab(self):
        """Create the preview tab content"""
        preview_frame = ttk.Frame(self.preview_tab)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        # Add preview tab widgets...
        pass

    def create_batch_tab(self):
        """Create the batch processing tab content"""
        batch_frame = ttk.Frame(self.batch_tab)
        batch_frame.pack(fill=tk.BOTH, expand=True)
        # Add batch tab widgets...
        pass

    def create_template_tab(self):
        """Create the template manager tab content"""
        template_frame = ttk.Frame(self.template_tab)
        template_frame.pack(fill=tk.BOTH, expand=True)
        # Add template tab widgets...
        pass

    def load_session(self):
        """Load a saved session"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.load_session_from_file(file_path)

    def save_session(self):
        """Save the current session"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.save_session_to_file(file_path)

    def clear_fields(self):
        """Clear all form fields"""
        for path_var in self.file_paths.values():
            path_var.set('')
        self.output_dir.set('')
        self.detailed_graphs.set(True)
        self.generate_pdf.set(False)
        self.send_email.set(False)
        self.progress_var.set(0)


# Main function moved outside the class
def main():
    root = TkinterDnD.Tk()
    app = SLAGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

    '''' 
    def browse_batch_folder(self):
    """Open dialog to select batch input folder"""
    folder = filedialog.askdirectory(title="Seleziona cartella input")
    if folder:
        self.batch_input_var.set(folder)
        self.scan_batch_folder(folder)

def browse_output_folder(self):
    """Open dialog to select output folder"""
    folder = filedialog.askdirectory(title="Seleziona cartella output")
    if folder:
        self.batch_output_var.set(folder)

def scan_batch_folder(self, folder):
    """Scan the selected folder for CSV files"""
    self.batch_listbox.delete(0, tk.END)
    try:
        for file in os.listdir(folder):
            if file.endswith('.csv'):
                self.batch_listbox.insert(tk.END, file)
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nella scansione della cartella: {str(e)}")

def process_batch_all(self):
    """Process all files in the batch list"""
    if self.batch_listbox.size() == 0:
        messagebox.showinfo("Info", "Nessun file da processare")
        return

    if not self.batch_output_var.get():
        messagebox.showerror("Errore", "Seleziona una cartella di output")
        return

    total_files = self.batch_listbox.size()
    for i in range(total_files):
        filename = self.batch_listbox.get(i)
        self.process_single_file(filename, i, total_files)

def process_batch_selected(self):
    """Process only selected files in the batch list"""
    selected = self.batch_listbox.curselection()
    if not selected:
        messagebox.showinfo("Info", "Nessun file selezionato")
        return

    if not self.batch_output_var.get():
        messagebox.showerror("Errore", "Seleziona una cartella di output")
        return

    total_selected = len(selected)
    for i, index in enumerate(selected):
        filename = self.batch_listbox.get(index)
        self.process_single_file(filename, i, total_selected)

def process_single_file(self, filename, current, total):
    """Process a single file from the batch"""
    try:
        input_path = os.path.join(self.batch_input_var.get(), filename)
        output_path = os.path.join(self.batch_output_var.get(), f"processed_{filename}")

        # Update progress
        progress = int((current + 1) / total * 100)
        self.batch_progress['value'] = progress
        self.batch_status_label['text'] = f"Processando {filename}... ({current + 1}/{total})"
        self.batch_tab.update()

        # Process the file (example processing)
        df = pd.read_csv(input_path, sep=';')
        # Add your processing logic here
        df.to_csv(output_path, sep=';', index=False)

        self.batch_status_label['text'] = f"Completato: {filename}"
    except Exception as e:
        self.batch_status_label['text'] = f"Errore nel processare {filename}"
        messagebox.showerror("Errore", f"Errore nel processare {filename}: {str(e)}")

def remove_selected_files(self):
    """Remove selected files from the batch list"""
    selected = self.batch_listbox.curselection()
    if not selected:
        return

    # Remove in reverse order to maintain correct indices
    for index in sorted(selected, reverse=True):
        self.batch_listbox.delete(index)

def browse_template(self):
    """Open dialog to select a template file"""
    file_path = filedialog.askopenfilename(
        filetypes=[("Word files", "*.docx"), ("All files", "*.*")]
    )
    if file_path:
        self.template_path_var.set(file_path)
        self.load_template_preview(file_path)

def load_template_preview(self, template_path):
    """Load and display template preview"""
    try:
        # Here you would implement logic to read the template
        # For now, just display the template path
        self.template_text.delete('1.0', tk.END)
        self.template_text.insert(tk.END, f"Template caricato: {template_path}\n\n")
        self.template_text.insert(tk.END, "Anteprima non disponibile per file DOCX.")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel caricamento del template: {str(e)}")

def new_template(self):
    """Create a new empty template"""
    self.template_path_var.set("")
    self.template_text.delete('1.0', tk.END)

def save_template(self):
    """Save the current template"""
    if not self.template_path_var.get():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word files", "*.docx"), ("All files", "*.*")]
        )
        if file_path:
            self.template_path_var.set(file_path)
    try:
        # Here you would implement the actual template saving logic
        messagebox.showinfo("Success", "Template salvato con successo")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel salvare il template: {str(e)}")

def preview_template(self):
    """Preview the current template"""
    if not self.template_path_var.get():
        messagebox.showwarning("Attenzione", "Nessun template selezionato")
        return

    try:
        # Here you would implement the actual preview logic
        # For now, just try to open the file with the default application
        if os.name == 'nt':  # Windows
            os.startfile(self.template_path_var.get())
        else:  # macOS and Linux
            subprocess.call(('open', self.template_path_var.get()))
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nell'apertura del template: {str(e)}")
    '''