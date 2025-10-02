import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import threading
import time
from obtener_recursos import obtener_instancias_ec2
from widgets import DetailWindow

class EC2Tab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.tree_ec2 = None
        self.ec2_count_label = None
        self.ec2_context_menu = None
        self.ec2_data = []
        
        self.crear_tab_ec2()
    
    def crear_tab_ec2(self):
        top_frame = ttk.Frame(self.parent_frame)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        info_frame = ttk.Frame(top_frame)
        info_frame.pack(side='left')
        
        ttk.Label(info_frame, text="Instancias EC2", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        
        self.ec2_count_label = ttk.Label(info_frame, text="0 instancias encontradas",
                                        font=('Segoe UI', 10))
        self.ec2_count_label.pack(anchor='w')
        
        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="🔄 Actualizar", command=self.refrescar_ec2,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        ttk.Button(btn_frame, text="▶️ Iniciar Seleccionadas", command=self.iniciar_ec2_multiple,
                  style="Large.success.TButton").pack(side='left', padx=2)
        ttk.Button(btn_frame, text="⏹️ Detener Seleccionadas", command=self.detener_ec2_multiple,
                  style="Large.danger.TButton").pack(side='left', padx=2)
        
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))
        
        # Crear Treeview con scrollbar
        columns = ["ID", "Nombre", "Estado", "Tipo", "IP Privada", "Lanzado"]
        self.tree_ec2 = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                    selectmode="extended", height=15)
        
        # Scrollbar
        scrollbar_ec2 = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ec2.yview)
        self.tree_ec2.configure(yscrollcommand=scrollbar_ec2.set)
        
        # Configurar columnas
        column_widths = [180, 200, 100, 120, 120, 150]
        for i, col in enumerate(columns):
            self.tree_ec2.heading(col, text=col)
            self.tree_ec2.column(col, width=column_widths[i], anchor="center")
        
        # Pack treeview y scrollbar
        self.tree_ec2.pack(side="left", expand=True, fill='both')
        scrollbar_ec2.pack(side="right", fill='y')
        
        self.tree_ec2.bind('<Double-1>', self.on_ec2_double_click)
        self.tree_ec2.bind('<Button-3>', self.show_ec2_context_menu)
        
        # Menú contextual EC2
        self.ec2_context_menu = tk.Menu(self.main_app.root, tearoff=0)
        self.ec2_context_menu.add_command(label="▶️ Iniciar", command=self.iniciar_ec2_single)
        self.ec2_context_menu.add_command(label="⏹️ Detener", command=self.detener_ec2_single)
        self.ec2_context_menu.add_separator()
        self.ec2_context_menu.add_command(label="📋 Ver Detalles", command=self.ver_detalles_ec2)
        self.ec2_context_menu.add_command(label="📄 Copiar ID", command=self.copiar_id_ec2)
        self.ec2_context_menu.add_command(label="📄 Copiar Nombre", command=self.copiar_nombre_ec2)
        self.ec2_context_menu.add_command(label="📄 Copiar IP", command=self.copiar_ip_ec2)
    
    def refrescar_ec2(self):
        if not self.main_app.ec2_client:
            return
        # Actualizar status durante la carga
        self.main_app.status_bar.set_status("Cargando EC2...", "info", f"Cuenta: {self.main_app.cuenta_actual}")

        def cargar_datos():
            try:
                instancias = obtener_instancias_ec2(self.main_app.ec2_client)
                self.main_app.root.after(0, self.actualizar_tree_ec2, instancias)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error al cargar EC2: {str(e)}"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
        self.main_app.status_bar.set_status("Conectado", "success", f"Cuenta: {self.main_app.cuenta_actual}")

    def actualizar_tree_ec2(self, instancias):
        for item in self.tree_ec2.get_children():
            self.tree_ec2.delete(item)
        
        self.ec2_data = instancias
        for inst in instancias:
            color_tag = self.main_app.obtener_color_estado(inst["state"])
            self.tree_ec2.insert("", "end", values=(
                inst["id"], inst["name"], inst["state"], inst["type"], inst["private_ip"], inst["launch_time"]
            ), tags=(color_tag,))
        
        self.main_app.configurar_colores_tree(self.tree_ec2)
        self.ec2_count_label.config(text=f"{len(instancias)} instancias encontradas")
    
    # Funciones para EC2 - Selección múltiple
    def iniciar_ec2_multiple(self):
        self.toggle_ec2_instances_multiple(action="start")
    
    def detener_ec2_multiple(self):
        self.toggle_ec2_instances_multiple(action="stop")
    
    def toggle_ec2_instances_multiple(self, action):
        selected = self.tree_ec2.selection()
        if not selected:
            messagebox.showwarning("Sin selección", "Por favor selecciona al menos una instancia EC2")
            return
        
        valid_instances = []
        for item_id in selected:
            item = self.tree_ec2.item(item_id)
            id_, name, state = item["values"][:3]
            
            # Validar estado
            if action == "start" and state == "stopped":
                valid_instances.append((id_, name))
            elif action == "stop" and state == "running":
                valid_instances.append((id_, name))
        
        if not valid_instances:
            estado_requerido = "detenidas" if action == "start" else "ejecutándose"
            messagebox.showinfo("Sin instancias válidas", 
                              f"No hay instancias {estado_requerido} para {'iniciar' if action == 'start' else 'detener'}")
            return

        def ejecutar():
            try:
                ids = [id_ for id_, _ in valid_instances]
                self.main_app.loading.show(f"{'Iniciando' if action == 'start' else 'Deteniendo'} {len(ids)} instancias...")
                
                if action == "start":
                    self.main_app.ec2_client.start_instances(InstanceIds=ids)
                else:
                    self.main_app.ec2_client.stop_instances(InstanceIds=ids)
                
                time.sleep(2)
                self.main_app.root.after(0, self.refrescar_ec2)
                    
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
            finally:
                self.main_app.root.after(0, self.main_app.loading.hide)
        
        threading.Thread(target=ejecutar, daemon=True).start()
    
    # Funciones del menú contextual - EC2
    def show_ec2_context_menu(self, event):
        item = self.tree_ec2.identify_row(event.y)
        if item:
            self.tree_ec2.selection_set(item)
            self.ec2_context_menu.post(event.x_root, event.y_root)
    
    def iniciar_ec2_single(self):
        self.toggle_ec2_instance_single(action="start")
    
    def detener_ec2_single(self):
        self.toggle_ec2_instance_single(action="stop")
    
    def toggle_ec2_instance_single(self, action):
        selected = self.tree_ec2.selection()
        if not selected:
            return
        
        item = self.tree_ec2.item(selected[0])
        id_, name, state = item["values"][:3]
        
        # Validar estado
        if action == "start" and state != "stopped":
            messagebox.showinfo("Estado no válido", "La instancia debe estar detenida para iniciarla")
            return
        elif action == "stop" and state != "running":
            messagebox.showinfo("Estado no válido", "La instancia debe estar ejecutándose para detenerla")
            return
        
        def ejecutar():
            try:
                self.main_app.loading.show(f"{'Iniciando' if action == 'start' else 'Deteniendo'} instancia...")
                if action == "start":
                    self.main_app.ec2_client.start_instances(InstanceIds=[id_])
                else:
                    self.main_app.ec2_client.stop_instances(InstanceIds=[id_])
                
                time.sleep(2)
                self.main_app.root.after(0, self.refrescar_ec2)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
            finally:
                self.main_app.root.after(0, self.main_app.loading.hide)
        
        threading.Thread(target=ejecutar, daemon=True).start()
    
    def ver_detalles_ec2(self):
        selected = self.tree_ec2.selection()
        if not selected:
            return
        
        item = self.tree_ec2.item(selected[0])
        id_ = item["values"][0]
        
        # Buscar datos completos
        data = next((inst for inst in self.ec2_data if inst["id"] == id_), None)
        if data:
            DetailWindow(self.main_app.root, f"Detalles de EC2 - {data['name']}", data, "ec2")
    
    def copiar_id_ec2(self):
        selected = self.tree_ec2.selection()
        if not selected:
            return
        
        item = self.tree_ec2.item(selected[0])
        id_ = item["values"][0]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(id_)

    def copiar_nombre_ec2(self):
        selected = self.tree_ec2.selection()
        if not selected:
            return
        
        item = self.tree_ec2.item(selected[0])
        name_ = item["values"][1]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(name_)

    def copiar_ip_ec2(self):
        selected = self.tree_ec2.selection()
        if not selected:
            return
        
        item = self.tree_ec2.item(selected[0])
        ip_ = item["values"][4]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(ip_)     
    
    # Funciones para doble clic
    def on_ec2_double_click(self, event):
        self.ver_detalles_ec2()