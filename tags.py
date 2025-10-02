import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json


class TagsTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_tags)
        self.tag_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        # Main container with full width
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)

        self.create_search_section(main_frame)
        self.create_tags_grid(main_frame)


    def create_search_section(self, parent):
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(search_frame, text="🔍 Buscar tag:", font=('Segoe UI', 11, 'bold')).pack(side='left')
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, 
                                font=('Segoe UI', 11), width=30)
        search_entry.pack(side='left', padx=(10, 0))
        
        clear_btn = ttk.Button(search_frame, text="Limpiar", 
                              command=lambda: self.search_var.set(''),
                              style='secondary.TButton')
        clear_btn.pack(side='left', padx=(10, 0))

    def create_tags_grid(self, parent):
        # Container for the grid
        grid_container = ttk.Frame(parent)
        grid_container.pack(fill='both', expand=True)

        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(grid_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(grid_container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", 
                                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Grid layout with 2 columns
        self.create_tags_cards()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def create_tags_cards(self):
        self.tags_policy = {
            "Name": {"required": True, "type": "text", "description": "Nombre descriptivo del recurso", "example": "webserver-prod-01"},
            "Area": {"required": True, "type": "select", "options": ["Infraestructura", "Demanda", "Aplicaciones", "Ciberseguridad","Comunicaciones", "Other"], "description": "Área responsable del recurso"},
            "Requester": {"required": True, "type": "text", "description": "Persona que solicita el recurso", "example": "juan.perez@company.com"},
            "Risk": {"required": True, "type": "select", "options": ["low", "medium", "high", "critical"], "description": "Nivel de riesgo del recurso"},
            "Project": {"required": False, "type": "fixed", "value": "MOA Cloud", "description": "Proyecto al que pertenece el recurso"},
            "Application": {"required": True, "type": "select", "options": ["Data Agro", "Pañol", "Scato Puerto", "Scato Logística", "Scato Mobile", "MOA Operaciones", "SAP", "MOA", "Other"], "description": "Aplicación que utiliza el recurso"},
            "Environment": {"required": True, "type": "select", "options": ["DEV", "QA", "UAT", "PRD", "DRP"], "description": "Ambiente donde se ejecuta el recurso"},
            "Autopoweron": {"required": False, "type": "select", "options": ["true", "false"], "description": "Encendido automático programado"},
            "Autopoweroff": {"required": False, "type": "select", "options": ["true", "false"], "description": "Apagado automático programado"},
            "Costcenter": {"required": False, "type": "text", "description": "Centro de costos para facturación", "example": "CC-001"},
            "Dataclass": {"required": False, "type": "select", "options": ["Restrictive(Apps)", "Confidential(DB)", "critical"], "description": "Clasificación de datos"},
            "TTL": {"required": False, "type": "text", "description": "Tiempo de vida (MMAAAA o 000000 para permanente)", "example": "062025"},
            "BackupPolicy": {"required": True, "type": "select", "options": ["NoBackup", "DiarioR7", "DiarioR15", "DiarioR30", "SemanalR7", "SemanalR15", "SemanalR30", "MensualR30", "AnualR365"], "description": "Frecuencia de Backup"}
        
        }

        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.tag_widgets.clear()

        # Create cards in grid layout
        row = 0
        col = 0
        
        # Required tags first
        required_tags = {k: v for k, v in self.tags_policy.items() if v['required']}
        optional_tags = {k: v for k, v in self.tags_policy.items() if not v['required']}
        
        # Section headers
        if required_tags:
            req_header = ttk.Label(self.scrollable_frame, text="🔴 Tags Obligatorios", 
                                  font=('Segoe UI', 16, 'bold'), foreground='red')
            req_header.grid(row=row, column=0, columnspan=2, sticky='w', pady=(0, 10))
            row += 1
            
            for tag, info in required_tags.items():
                card = self.create_tag_card(self.scrollable_frame, tag, info)
                card.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
                self.tag_widgets[tag] = card
                
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
            
            if col != 0:
                row += 1
                col = 0

        # Optional tags
        if optional_tags:
            opt_header = ttk.Label(self.scrollable_frame, text="🟡 Tags Opcionales", 
                                  font=('Segoe UI', 16, 'bold'), foreground='orange')
            opt_header.grid(row=row, column=0, columnspan=2, sticky='w', pady=(20, 10))
            row += 1
            
            for tag, info in optional_tags.items():
                card = self.create_tag_card(self.scrollable_frame, tag, info)
                card.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
                self.tag_widgets[tag] = card
                
                col += 1
                if col >= 2:
                    col = 0
                    row += 1

        # Configure grid weights for responsive design
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

    def create_tag_card(self, parent, tag, info):
        # Card frame with border
        card = ttk.Frame(parent, style='Card.TFrame')
        
        # Header with tag name
        header = ttk.Frame(card)
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        
        name_label = ttk.Label(header, text=tag, 
                              font=('Segoe UI', 14, 'bold'))
        name_label.pack(side='left')
        
        # Copy button
        copy_btn = ttk.Button(header, text="📋", width=3,
                             command=lambda: self.copy_text(tag),
                             style='secondary.TButton')
        copy_btn.pack(side='right')
        
        # Description
        desc_label = ttk.Label(card, text=info['description'], 
                              font=('Segoe UI', 10), 
                              wraplength=300, justify='left')
        desc_label.pack(fill='x', padx=15, pady=(0, 10))
        
        # Values section
        values_frame = ttk.Frame(card)
        values_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        if info['type'] == 'select':
            ttk.Label(values_frame, text="Valores disponibles:", 
                     font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            
            for opt in info['options']:
                btn = ttk.Button(values_frame, text=opt, 
                               command=lambda val=opt: self.copy_text(val),
                               style='outline.TButton')
                btn.pack(side='left', padx=(0, 5), pady=(5, 0))
                
        elif info['type'] == 'fixed':
            ttk.Label(values_frame, text="Valor fijo:", 
                     font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            btn = ttk.Button(values_frame, text=info['value'],
                           command=lambda: self.copy_text(info['value']),
                           style='success.outline.TButton')
            btn.pack(anchor='w', pady=(5, 0))
            
        elif info['type'] == 'text' and 'example' in info:
            ttk.Label(values_frame, text="Ejemplo:", 
                     font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            btn = ttk.Button(values_frame, text=info['example'],
                           command=lambda: self.copy_text(info['example']),
                           style='info.outline.TButton')
            btn.pack(anchor='w', pady=(5, 0))
        
        return card

    def filter_tags(self, *args):
        """Filter tags based on search input"""
        search_term = self.search_var.get().lower()
        
        for tag, widget in self.tag_widgets.items():
            if search_term in tag.lower() or search_term in self.tags_policy[tag]['description'].lower():
                widget.grid()
            else:
                widget.grid_remove()

    def copy_text(self, text):
        """Copy text to clipboard with improved feedback"""
        try:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(text)
            self.show_copy_notification(text)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar: {e}")

    def show_copy_notification(self, text):
        """Show a modern toast notification"""
        notif = tk.Toplevel(self.app.root)
        notif.wm_overrideredirect(True)
        notif.attributes('-topmost', True)
        
        # Position in bottom right
        x = self.app.root.winfo_x() + self.app.root.winfo_width() - 300
        y = self.app.root.winfo_y() + self.app.root.winfo_height() - 100
        notif.geometry(f"280x60+{x}+{y}")
        
        # Styling
        notif.configure(bg='#2d3748')
        
        # Icon and message
        frame = tk.Frame(notif, bg='#2d3748')
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        icon = tk.Label(frame, text="✅", bg='#2d3748', fg='#48bb78', font=('Segoe UI', 16))
        icon.pack(side='left')
        
        msg = text if len(text) <= 25 else text[:25] + "..."
        label = tk.Label(frame, text=f"Copiado: {msg}", bg='#2d3748', fg='white', 
                        font=('Segoe UI', 10, 'bold'), wraplength=200)
        label.pack(side='left', padx=(10, 0))
        
        # Auto-close
        notif.after(2000, notif.destroy)