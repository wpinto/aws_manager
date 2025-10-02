import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import threading
import time
from obtener_recursos import obtener_instancias_rds
from widgets import DetailWindow

class RDSTab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.tree_rds = None
        self.rds_count_label = None
        self.rds_context_menu = None
        self.rds_data = []
        
        self.crear_tab_rds()
    
    def crear_tab_rds(self):
        top_frame = ttk.Frame(self.parent_frame)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        info_frame = ttk.Frame(top_frame)
        info_frame.pack(side='left')
        
        ttk.Label(info_frame, text="Bases de datos RDS", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        
        self.rds_count_label = ttk.Label(info_frame, text="0 bases de datos encontradas",
                                        font=('Segoe UI', 10))
        self.rds_count_label.pack(anchor='w')
        
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="🔄 Actualizar", command=self.refrescar_rds,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        ttk.Button(btn_frame, text="▶️ Iniciar Seleccionadas", command=self.iniciar_rds_multiple,
                  style="Large.success.TButton").pack(side='left', padx=2)
        ttk.Button(btn_frame, text="⏹️ Detener Seleccionadas", command=self.detener_rds_multiple,
                  style="Large.danger.TButton").pack(side='left', padx=2)
        
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))
        
        # Crear Treeview con scrollbar
        columns = ["ID", "Estado", "Motor", "Clase", "Endpoint"]
        self.tree_rds = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                    selectmode="extended", height=15)
        
        # Scrollbar
        scrollbar_rds = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_rds.yview)
        self.tree_rds.configure(yscrollcommand=scrollbar_rds.set)
        
        # Configurar columnas
        column_widths = [150, 100, 150, 100, 400]
        for i, col in enumerate(columns):
            self.tree_rds.heading(col, text=col)
            self.tree_rds.column(col, width=column_widths[i], anchor="center")
        
        # Pack treeview y scrollbar
        self.tree_rds.pack(side="left", expand=True, fill='both')
        scrollbar_rds.pack(side="right", fill='y')
        
        self.tree_rds.bind('<Double-1>', self.on_rds_double_click)
        self.tree_rds.bind('<Button-3>', self.show_rds_context_menu)
        
        # Menú contextual RDS
        self.rds_context_menu = tk.Menu(self.main_app.root, tearoff=0)
        self.rds_context_menu.add_command(label="▶️ Iniciar", command=self.iniciar_rds_single)
        self.rds_context_menu.add_command(label="⏹️ Detener", command=self.detener_rds_single)
        self.rds_context_menu.add_separator()
        self.rds_context_menu.add_command(label="📋 Ver Detalles", command=self.ver_detalles_rds)
        self.rds_context_menu.add_command(label="📄 Copiar ID", command=self.copiar_id_rds)
        self.rds_context_menu.add_command(label="📄 Copiar Endpoint", command=self.copiar_endpoint_rds)
    
    def refrescar_rds(self):
        if not self.main_app.rds_client:
            return
        self.main_app.status_bar.set_status("Cargando RDS...", "info", f"Cuenta: {self.main_app.cuenta_actual}")
        def cargar_datos():
            try:
                instancias = obtener_instancias_rds(self.main_app.rds_client)
                self.main_app.root.after(0, self.actualizar_tree_rds, instancias)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error al cargar RDS: {str(e)}"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
        self.main_app.status_bar.set_status("Conectado", "success", f"Cuenta: {self.main_app.cuenta_actual}")

    def actualizar_tree_rds(self, instancias):
        for item in self.tree_rds.get_children():
            self.tree_rds.delete(item)
        
        self.rds_data = instancias
        for inst in instancias:
            color_tag = self.main_app.obtener_color_estado(inst["state"])
            self.tree_rds.insert("", "end", values=(
                inst["id"], inst["state"], inst["engine"], inst["class"], inst["endpoint"]
            ), tags=(color_tag,))
        
        self.main_app.configurar_colores_tree(self.tree_rds)
        self.rds_count_label.config(text=f"{len(instancias)} bases de datos encontradas")
    
    # Funciones para RDS - Selección múltiple
    def iniciar_rds_multiple(self):
        self.toggle_rds_instances_multiple(action="start")
    
    def detener_rds_multiple(self):
        self.toggle_rds_instances_multiple(action="stop")
    
    def toggle_rds_instances_multiple(self, action):
        selected = self.tree_rds.selection()
        if not selected:
            messagebox.showwarning("Sin selección", "Por favor selecciona al menos una base de datos RDS")
            return
        
        valid_instances = []
        for item_id in selected:
            item = self.tree_rds.item(item_id)
            id_, state = item["values"][:2]
            name = id_
            # Validar estado
            if action == "start" and state == "stopped":
                valid_instances.append((id_, name))
            elif action == "stop" and state == "available":
                valid_instances.append((id_, name))
        
        if not valid_instances:
            estado_requerido = "detenidas" if action == "start" else "disponibles"
            messagebox.showinfo("Sin instancias válidas", 
                              f"No hay bases de datos {estado_requerido} para {'iniciar' if action == 'start' else 'detener'}")
            return
    
        def ejecutar():
            try:
                self.main_app.loading.show(f"{'Iniciando' if action == 'start' else 'Deteniendo'} {len(valid_instances)} bases de datos...")
                
                for id_, name in valid_instances:
                    if action == "start":
                        self.main_app.rds_client.start_db_instance(DBInstanceIdentifier=id_)
                    else:
                        self.main_app.rds_client.stop_db_instance(DBInstanceIdentifier=id_)
                    time.sleep(1)  # Pequeña pausa entre operaciones
                
                time.sleep(2)
                self.main_app.root.after(0, self.refrescar_rds)
                    
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
            finally:
                self.main_app.root.after(0, self.main_app.loading.hide)
        
        threading.Thread(target=ejecutar, daemon=True).start()
    
    # Funciones del menú contextual - RDS
    def show_rds_context_menu(self, event):
        item = self.tree_rds.identify_row(event.y)
        if item:
            self.tree_rds.selection_set(item)
            self.rds_context_menu.post(event.x_root, event.y_root)
    
    def iniciar_rds_single(self):
        self.toggle_rds_instance_single(action="start")
    
    def detener_rds_single(self):
        self.toggle_rds_instance_single(action="stop")
    
    def toggle_rds_instance_single(self, action):
        selected = self.tree_rds.selection()
        if not selected:
            return
        
        item = self.tree_rds.item(selected[0])
        id_, state = item["values"][:2]
        
        # Validar estado
        if action == "start" and state != "stopped":
            messagebox.showinfo("Estado no válido", "La base de datos debe estar detenida para iniciarla")
            return
        elif action == "stop" and state != "available":
            messagebox.showinfo("Estado no válido", "La base de datos debe estar disponible para detenerla")
            return
        
        def ejecutar():
            try:
                self.main_app.loading.show(f"{'Iniciando' if action == 'start' else 'Deteniendo'} base de datos...")
                if action == "start":
                    self.main_app.rds_client.start_db_instance(DBInstanceIdentifier=id_)
                else:
                    self.main_app.rds_client.stop_db_instance(DBInstanceIdentifier=id_)
                
                time.sleep(2)
                self.main_app.root.after(0, self.refrescar_rds)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
            finally:
                self.main_app.root.after(0, self.main_app.loading.hide)
        
        threading.Thread(target=ejecutar, daemon=True).start()
    
    def ver_detalles_rds(self):
        selected = self.tree_rds.selection()
        if not selected:
            return
        
        item = self.tree_rds.item(selected[0])
        id_ = item["values"][0]
        
        # Buscar datos completos
        data = next((inst for inst in self.rds_data if inst["id"] == id_), None)
        if data:
            DetailWindow(self.main_app.root, f"Detalles de RDS - {data['name']}", data, "rds")
    
    def copiar_id_rds(self):
        selected = self.tree_rds.selection()
        if not selected:
            return
        
        item = self.tree_rds.item(selected[0])
        id_ = item["values"][0]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(id_)

    def copiar_endpoint_rds(self):
        selected = self.tree_rds.selection()
        if not selected:
            return
        
        item = self.tree_rds.item(selected[0])
        endpoint_ = item["values"][4] 
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(endpoint_)
    
    # Funciones para doble clic
    def on_rds_double_click(self, event):
        self.ver_detalles_rds()