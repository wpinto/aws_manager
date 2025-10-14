import tkinter as tk
from tkinter import messagebox, ttk
from ttkbootstrap.constants import *
import threading
import cliente as cliente
from datetime import datetime

class FSxTab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.fsx_client = None
        self.fsx_data = []
        self.tree_fsx = None
        self.fsx_count_label = None
        self.details_text = None
        self.selected_fs = None
        
        self.crear_tab_fsx()

    def crear_tab_fsx(self):
        """Crear la interfaz principal del tab de FSx"""
        # Panel principal dividido
        panel_principal = ttk.PanedWindow(self.parent_frame, orient='horizontal')
        panel_principal.pack(fill='both', expand=True, padx=10, pady=10)

        # Panel izquierdo
        panel_izquierdo = ttk.Frame(panel_principal)
        panel_principal.add(panel_izquierdo, weight=2)
        
        # Frame superior con título y controles
        top_frame = ttk.Frame(panel_izquierdo)
        top_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(top_frame, text="🗄️ FSx File Systems", 
                 font=('Segoe UI', 16, 'bold')).pack(side='left')
        
        self.fsx_count_label = ttk.Label(top_frame, text="0 File Systems",
                                       font=('Segoe UI', 10))
        self.fsx_count_label.pack(side='left', padx=(20, 0))
        
        # Frame de acciones
        actions_frame = ttk.Frame(top_frame)
        actions_frame.pack(side='right')
        
        ttk.Button(actions_frame, text="🔄 Actualizar", 
                  command=self.refrescar_fsx,
                  style='primary.TButton').pack(side='left', padx=5)

        # TreeView para File Systems
        tree_frame = ttk.Frame(panel_izquierdo)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ["ID", "Nombre", "Tipo", "Estado", "Tamaño (GB)", "IOPS", "Throughput (MB/s)"]
        self.tree_fsx = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                   selectmode="browse")
        
        widths = [150, 200, 100, 100, 100, 100, 120]
        for col, width in zip(columns, widths):
            self.tree_fsx.heading(col, text=col)
            self.tree_fsx.column(col, width=width, minwidth=50)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_fsx.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_fsx.xview)
        self.tree_fsx.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree_fsx.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Panel derecho
        panel_derecho = ttk.Frame(panel_principal)
        panel_principal.add(panel_derecho, weight=1)
        
        # Notebook para detalles
        self.detail_tabs = ttk.Notebook(panel_derecho)
        self.detail_tabs.pack(fill='both', expand=True)
        
        # Tab de Detalles
        tab_detalles = ttk.Frame(self.detail_tabs)
        self.detail_tabs.add(tab_detalles, text="Detalles")
        
        self.details_text = tk.Text(tab_detalles, wrap='word', font=('Segoe UI', 10),
                                  bg='#2b2b2b', fg='white')
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab de Acciones
        tab_acciones = ttk.Frame(self.detail_tabs)
        self.detail_tabs.add(tab_acciones, text="Acciones")
        
        # Botones de acciones
        ttk.Button(tab_acciones, text="🔄 Crear Backup", 
                  command=self.crear_backup).pack(fill='x', padx=10, pady=5)
        
        ttk.Button(tab_acciones, text="📊 Ver Métricas", 
                  command=self.ver_metricas).pack(fill='x', padx=10, pady=5)
        
        ttk.Button(tab_acciones, text="⚙️ Modificar", 
                  command=self.modificar_fs).pack(fill='x', padx=10, pady=5)
        
        # Eventos
        self.tree_fsx.bind('<<TreeviewSelect>>', self.mostrar_detalles)
        self.tree_fsx.bind('<Double-1>', self.ver_metricas)
        self.tree_fsx.bind('<Button-3>', self.mostrar_menu_contextual)

    def refrescar_fsx(self):
        if not self.main_app.fsx_client:
            messagebox.showwarning("Sin conexión", "Conecta a una cuenta AWS primero")
            return
            
        self.main_app.status_bar.set_status("Cargando File Systems FSx...", "info")
        
        def cargar_datos():
            try:
                self.main_app.loading.show("Cargando FSx...")
                fsx_filesystems = self.obtener_fsx_filesystems()
                self.main_app.root.after(0, self.actualizar_tree_fsx, fsx_filesystems)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Error al cargar File Systems FSx: {str(e)}"))
            finally:
                self.main_app.root.after(0, self.main_app.loading.hide)
                self.main_app.root.after(0, lambda: self.main_app.status_bar.set_status(
                    "Conectado", "success"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()

    def obtener_fsx_filesystems(self):
        """Obtiene todos los file systems FSx con detalles adicionales"""
        if not self.fsx_client:
            self.fsx_client = cliente.crear("fsx", self.main_app.cuenta_actual)
        
        response = self.fsx_client.describe_file_systems()
        fsx_filesystems = []
        
        for fsx in response['FileSystems']:
            name = "N/A"
            for tag in fsx.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            fsx_data = {
                'id': fsx['FileSystemId'],
                'name': name,
                'type': fsx['FileSystemType'],
                'lifecycle': fsx['Lifecycle'],
                'storage_capacity': fsx['StorageCapacity'],
                'subnet_ids': fsx.get('SubnetIds', []),
                'network_interface_ids': fsx.get('NetworkInterfaceIds', []),
                'vpc_id': fsx.get('VpcId', 'N/A'),
                'kms_key_id': fsx.get('KmsKeyId', 'N/A'),
                'storage_type': fsx.get('StorageType', 'N/A'),
                'deployment_type': fsx.get('WindowsConfiguration', {}).get('DeploymentType', 'N/A'),
                'throughput_capacity': fsx.get('WindowsConfiguration', {}).get('ThroughputCapacity', 0),
                'maintenance_window': fsx.get('WindowsConfiguration', {}).get('WeeklyMaintenanceStartTime', 'N/A'),
                'automatic_backup_retention_days': fsx.get('WindowsConfiguration', {}).get('AutomaticBackupRetentionDays', 0),
                'daily_automatic_backup_start_time': fsx.get('WindowsConfiguration', {}).get('DailyAutomaticBackupStartTime', 'N/A'),
                'copy_tags_to_backups': fsx.get('WindowsConfiguration', {}).get('CopyTagsToBackups', False),
                'iops': fsx.get('WindowsConfiguration', {}).get('Iops', 0),
                'creation_time': fsx['CreationTime'].strftime('%Y-%m-%d %H:%M:%S'),
            }
            fsx_filesystems.append(fsx_data)
        
        return fsx_filesystems

    def actualizar_tree_fsx(self, fsx_filesystems):
        """Actualizar el TreeView con los datos de FSx"""
        self.fsx_data = fsx_filesystems
        
        # Limpiar tree
        for item in self.tree_fsx.get_children():
            self.tree_fsx.delete(item)
        
        # Insertar datos
        for fsx in fsx_filesystems:
            values = (
                fsx['id'],
                fsx['name'],
                fsx['type'],
                fsx['lifecycle'],
                fsx['storage_capacity'],
                fsx['iops'],
                fsx['throughput_capacity']
            )
            
            tag = self.obtener_tag_estado(fsx['lifecycle'])
            self.tree_fsx.insert("", "end", values=values, tags=(tag,))
        
        # Configurar colores
        self.tree_fsx.tag_configure("success", foreground="#28a745")
        self.tree_fsx.tag_configure("warning", foreground="#ffc107")
        self.tree_fsx.tag_configure("danger", foreground="#dc3545")
        
        # Actualizar contador
        count = len(fsx_filesystems)
        self.fsx_count_label.config(text=f"{count} File Systems")

    def obtener_tag_estado(self, estado):
        """Determina el tag de color según el estado"""
        if estado == "AVAILABLE":
            return "success"
        elif estado in ["CREATING", "UPDATING"]:
            return "warning"
        else:
            return "danger"

    def mostrar_detalles(self, event=None):
        """Muestra los detalles del file system seleccionado"""
        selection = self.tree_fsx.selection()
        if not selection:
            return
        
        item = selection[0]
        fs_id = self.tree_fsx.item(item)['values'][0]
        
        # Buscar datos completos
        fs_data = next((fs for fs in self.fsx_data if fs['id'] == fs_id), None)
        if not fs_data:
            return
        
        self.selected_fs = fs_data
        
        # Formatear detalles
        details = f"""📁 File System Details

🔹 ID: {fs_data['id']}
🔹 Nombre: {fs_data['name']}
🔹 Tipo: {fs_data['type']}
🔹 Estado: {fs_data['lifecycle']}
🔹 Capacidad: {fs_data['storage_capacity']} GB
🔹 Tipo de Almacenamiento: {fs_data['storage_type']}
🔹 IOPS: {fs_data['iops']}
🔹 Throughput: {fs_data['throughput_capacity']} MB/s

🌐 Network Configuration
🔹 VPC: {fs_data['vpc_id']}
🔹 Subnets: {', '.join(fs_data['subnet_ids'])}
🔹 Network Interfaces: {', '.join(fs_data['network_interface_ids'])}

🔒 Security
🔹 KMS Key: {fs_data['kms_key_id']}

⚙️ Backup Configuration
🔹 Retention Days: {fs_data['automatic_backup_retention_days']}
🔹 Backup Start Time: {fs_data['daily_automatic_backup_start_time']}
🔹 Copy Tags to Backups: {fs_data['copy_tags_to_backups']}

🕒 Maintenance
🔹 Maintenance Window: {fs_data['maintenance_window']}
🔹 Creation Time: {fs_data['creation_time']}
"""
        
        # Actualizar texto
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert('1.0', details)

    def mostrar_menu_contextual(self, event):
        """Muestra el menú contextual"""
        item = self.tree_fsx.identify_row(event.y)
        if item:
            self.tree_fsx.selection_set(item)
            menu = tk.Menu(self.parent_frame, tearoff=0)
            menu.add_command(label="Ver Detalles", command=lambda: self.mostrar_detalles())
            menu.add_command(label="Ver Métricas", command=self.ver_metricas)
            menu.add_separator()
            menu.add_command(label="Crear Backup", command=self.crear_backup)
            menu.add_command(label="Modificar", command=self.modificar_fs)
            menu.tk_popup(event.x_root, event.y_root)

    def crear_backup(self):
        """Crear backup del file system seleccionado"""
        if not self.selected_fs:
            messagebox.showwarning("Sin selección", "Selecciona un file system primero")
            return
        
        # Implementar lógica de backup
        messagebox.showinfo("Crear Backup", 
                          f"Iniciando backup del file system: {self.selected_fs['name']}\n\n"
                          "Esta función está en desarrollo.")

    def ver_metricas(self):
        """Ver métricas del file system seleccionado"""
        if not self.selected_fs:
            messagebox.showwarning("Sin selección", "Selecciona un file system primero")
            return
        
        # Implementar visualización de métricas
        messagebox.showinfo("Ver Métricas", 
                          f"Métricas del file system: {self.selected_fs['name']}\n\n"
                          "Esta función está en desarrollo.")

    def modificar_fs(self):
        """Modificar configuración del file system seleccionado"""
        if not self.selected_fs:
            messagebox.showwarning("Sin selección", "Selecciona un file system primero")
            return
        
        # Implementar modificación de configuración
        messagebox.showinfo("Modificar File System", 
                          f"Modificando file system: {self.selected_fs['name']}\n\n"
                          "Esta función está en desarrollo.")
