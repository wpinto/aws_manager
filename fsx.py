import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading


class FSxTab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.tree_fsx = None
        self.fsx_count_label = None
        self.fsx_data = []
        
        self.crear_tab_fsx()
    
    def crear_tab_fsx(self):
        """Crear la interfaz principal del tab de FSx"""
        # Frame superior
        top_frame = ttk.Frame(self.parent_frame)
        top_frame.pack(fill='x', padx=20, pady=15)
        
        # Título
        title_label = ttk.Label(top_frame, text="💾 Amazon FSx File Systems", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.pack(side='left')
        
        # Contador
        self.fsx_count_label = ttk.Label(top_frame, text="0 file systems",
                                       font=('Segoe UI', 10))
        self.fsx_count_label.pack(side='left', padx=(20, 0))
        
        # Botón actualizar
        refresh_btn = ttk.Button(top_frame, text="🔄 Actualizar", 
                               command=self.refrescar_fsx)
        refresh_btn.pack(side='right')
        
        # TreeView
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(expand=True, fill='both', padx=20, pady=(0, 20))
        
        columns = ["ID", "Nombre", "Estado", "Tamaño (GB)", "IP Addresses", "VPC", "Creación"]
        self.tree_fsx = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                   selectmode="browse")
        
        # Configurar columnas
        widths = [150, 180, 80, 80, 350, 200, 140]
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
        
        # Eventos
        self.tree_fsx.bind('<Double-1>', self.ver_detalles_fsx)
    
    def refrescar_fsx(self):
        """Refrescar la lista de FSx file systems"""
        if not self.main_app.fsx_client:
            messagebox.showwarning("Sin conexión", "Conecta a una cuenta AWS primero")
            return
            
        self.main_app.status_bar.set_status("Cargando FSx file systems...", "info")
        
        def cargar_datos():
            try:
                fsx_list = self.obtener_fsx_filesystems()
                self.main_app.root.after(0, self.actualizar_tree_fsx, fsx_list)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Error al cargar FSx: {str(e)}"))
            finally:
                self.main_app.root.after(0, lambda: self.main_app.status_bar.set_status(
                    "Conectado", "success"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
    
    def obtener_fsx_filesystems(self):
        """Obtiene todos los file systems de FSx"""
        response = self.main_app.fsx_client.describe_file_systems()
        fsx_list = []
        
        for fs in response['FileSystems']:
            # Obtener nombre del tag Name
            fs_name = fs.get('FileSystemId', 'N/A')
            if 'Tags' in fs:
                for tag in fs['Tags']:
                    if tag['Key'] == 'Name' and tag['Value']:
                        fs_name = tag['Value']
                        break
            
            # Obtener tamaño según el tipo
            storage_capacity = fs.get('StorageCapacity', 0)
            
            # Determinar tipo de FS
            fs_type = fs.get('FileSystemType', 'UNKNOWN')
            
            # Obtener VPC ID
            vpc_id = 'N/A'
            if 'VpcId' in fs:
                vpc_id = fs['VpcId']
            elif 'SubnetIds' in fs and fs['SubnetIds']:
                vpc_id = 'Múltiples subnets'
            
            # Obtener direcciones IP
            ip_addresses = self.obtener_ip_addresses(fs)
            
            # Fecha de creación
            creation_time = fs.get('CreationTime', '')
            if creation_time:
                creation_time = creation_time.strftime('%Y-%m-%d %H:%M')
            
            fs_data = {
                'id': fs['FileSystemId'],
                'name': fs_name,
                'type': fs_type,
                'lifecycle': fs.get('Lifecycle', 'UNKNOWN'),
                'storage_capacity': storage_capacity,
                'vpc_id': vpc_id,
                'ip_addresses': ip_addresses,
                'creation_time': creation_time,
                'dns_name': fs.get('DNSName', 'N/A'),
                'owner_id': fs.get('OwnerId', 'N/A'),
                'resource_arn': fs.get('ResourceARN', 'N/A'),
                'subnet_ids': fs.get('SubnetIds', []),
                'tags': fs.get('Tags', []),
                'windows_config': fs.get('WindowsConfiguration', {}),
                'lustre_config': fs.get('LustreConfiguration', {}),
                'ontap_config': fs.get('OntapConfiguration', {}),
                'openzfs_config': fs.get('OpenZFSConfiguration', {})
            }
            fsx_list.append(fs_data)
        
        return sorted(fsx_list, key=lambda x: x['name'])
    
    def obtener_ip_addresses(self, fs):
        """Extrae las direcciones IP del file system según su tipo"""
        ip_addresses = []
        
        # Para Windows FSx
        if 'WindowsConfiguration' in fs:
            if 'PreferredFileServerIp' in fs['WindowsConfiguration']:
                ip_addresses.append(fs['WindowsConfiguration']['PreferredFileServerIp'])
            if 'RemoteAdministrationEndpoint' in fs['WindowsConfiguration']:
                endpoint = fs['WindowsConfiguration']['RemoteAdministrationEndpoint']
                if isinstance(endpoint, str):
                    # Extraer IP si está en formato IP:puerto
                    ip = endpoint.split(':')[0]
                    if ip not in ip_addresses:
                        ip_addresses.append(ip)
        
        # Para Lustre FSx
        if 'LustreConfiguration' in fs:
            if 'MountName' in fs['LustreConfiguration']:
                # Lustre usa DNS, pero podemos mostrar el mount name
                mount = fs['LustreConfiguration']['MountName']
                if mount and mount not in ip_addresses:
                    ip_addresses.append(f"Mount: {mount}")
        
        # Para ONTAP FSx
        if 'OntapConfiguration' in fs:
            if 'Endpoints' in fs['OntapConfiguration']:
                endpoints = fs['OntapConfiguration']['Endpoints']
                if 'Management' in endpoints and 'IpAddresses' in endpoints['Management']:
                    ip_addresses.extend(endpoints['Management']['IpAddresses'])
                if 'Intercluster' in endpoints and 'IpAddresses' in endpoints['Intercluster']:
                    ip_addresses.extend(endpoints['Intercluster']['IpAddresses'])
        
        # Para OpenZFS FSx
        if 'OpenZFSConfiguration' in fs:
            if 'EndpointIpAddress' in fs['OpenZFSConfiguration']:
                ip = fs['OpenZFSConfiguration']['EndpointIpAddress']
                if ip and ip not in ip_addresses:
                    ip_addresses.append(ip)
        
        # Si no se encontraron IPs específicas, intentar obtener desde network interfaces
        if not ip_addresses and 'NetworkInterfaceIds' in fs:
            # Nota: Aquí necesitarías hacer una llamada adicional a EC2 para obtener las IPs
            # de las network interfaces, pero eso requeriría el cliente EC2
            pass
        
        return ', '.join(ip_addresses) if ip_addresses else 'N/A'
    
    def actualizar_tree_fsx(self, fsx_list):
        """Actualizar el TreeView con los datos"""
        self.fsx_data = fsx_list
        self.mostrar_fsx()
    
    def mostrar_fsx(self):
        """Mostrar FSx file systems"""
        # Limpiar tree
        for item in self.tree_fsx.get_children():
            self.tree_fsx.delete(item)
        
        # Insertar datos
        for fs in self.fsx_data:
            # Color según estado
            estado = fs['lifecycle']
            tag = ''
            if estado == 'AVAILABLE':
                tag = 'available'
            elif estado in ['CREATING', 'UPDATING']:
                tag = 'updating'
            elif estado in ['FAILED', 'DELETING', 'DELETED']:
                tag = 'failed'
            
            item_id = self.tree_fsx.insert("", "end", values=(
                fs['id'],
                fs['name'],
                estado,
                fs['storage_capacity'],
                fs['ip_addresses'],
                fs['vpc_id'],
                fs['creation_time']
            ), tags=(tag,))
        
        # Configurar tags de colores
        self.tree_fsx.tag_configure('available', foreground='white')
        self.tree_fsx.tag_configure('updating', foreground='orange')
        self.tree_fsx.tag_configure('failed', foreground='red')
        
        # Actualizar contador
        count = len(self.fsx_data)
        total_storage = sum(fs['storage_capacity'] for fs in self.fsx_data)
        self.fsx_count_label.config(
            text=f"{count} file systems | {total_storage:,} GB total"
        )
    
    def ver_detalles_fsx(self, event=None):
        """Ver los detalles del FSx file system seleccionado"""
        selected = self.tree_fsx.selection()
        if not selected:
            return
        
        item = self.tree_fsx.item(selected[0])
        fs_id = item["values"][0]
        
        # Buscar datos completos
        fs_data = next((fs for fs in self.fsx_data if fs["id"] == fs_id), None)
        if fs_data:
            FSxDetailsViewer(self.main_app.root, fs_data)


class FSxDetailsViewer:
    """Ventana para visualizar detalles de un FSx file system"""
    
    def __init__(self, parent, fs_data):
        self.fs_data = fs_data
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Detalles FSx - {fs_data['name']}")
        self.window.geometry("700x850")
        self.window.transient(parent)
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crear la interfaz de la ventana"""
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text=f"💾 {self.fs_data['name']}", 
                 font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        
        ttk.Label(header_frame, text=f"ID: {self.fs_data['id']}").pack(anchor='w', pady=(5, 0))
        ttk.Label(header_frame, text=f"Tipo: {self.fs_data['type']}").pack(anchor='w')
        ttk.Label(header_frame, text=f"Estado: {self.fs_data['lifecycle']}").pack(anchor='w')
        
        # Separador
        ttk.Separator(self.window, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill='both', padx=20, pady=(0, 20))
        
        # Tab General
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="General")
        self.crear_tab_general(general_frame)
        
        # Tab Configuración específica
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text=f"Configuración {self.fs_data['type']}")
        self.crear_tab_configuracion(config_frame)
        
        # Tab Red
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Red")
        self.crear_tab_red(network_frame)
        
        # Tab Tags
        tags_frame = ttk.Frame(notebook)
        notebook.add(tags_frame, text=f"Tags ({len(self.fs_data['tags'])})")
        self.crear_tab_tags(tags_frame)
        
        # Botón cerrar
        ttk.Button(self.window, text="Cerrar", 
                  command=self.window.destroy).pack(pady=(0, 20))
    
    def crear_tab_general(self, parent):
        """Crear pestaña de información general"""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        info = [
            ("File System ID:", self.fs_data['id']),
            ("Nombre:", self.fs_data['name']),
            ("Tipo:", self.fs_data['type']),
            ("Estado:", self.fs_data['lifecycle']),
            ("Capacidad:", f"{self.fs_data['storage_capacity']:,} GB"),
            ("IP Addresses:", self.fs_data['ip_addresses']),
            ("DNS Name:", self.fs_data['dns_name']),
            ("Owner ID:", self.fs_data['owner_id']),
            ("Creación:", self.fs_data['creation_time']),
            ("ARN:", self.fs_data['resource_arn'])
        ]
        
        for i, (label, value) in enumerate(info):
            ttk.Label(frame, text=label, font=('Segoe UI', 10, 'bold')).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            
            # Para campos largos, usar un Text widget
            if label in ["ARN:", "DNS Name:", "File System ID:", "IP Addresses:"]:
                text_widget = tk.Text(frame, height=2, width=60, wrap='word')
                text_widget.insert('1.0', value)
                text_widget.config(state='disabled')
                text_widget.grid(row=i, column=1, sticky='w', pady=5)
            else:
                ttk.Label(frame, text=value).grid(row=i, column=1, sticky='w', pady=5)
    
    def crear_tab_configuracion(self, parent):
        """Crear pestaña de configuración específica del tipo"""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        fs_type = self.fs_data['type']
        
        if fs_type == 'WINDOWS':
            self.mostrar_config_windows(frame)
        elif fs_type == 'LUSTRE':
            self.mostrar_config_lustre(frame)
        elif fs_type == 'ONTAP':
            self.mostrar_config_ontap(frame)
        elif fs_type == 'OPENZFS':
            self.mostrar_config_openzfs(frame)
        else:
            ttk.Label(frame, text="Configuración no disponible").pack()
    
    def mostrar_config_windows(self, parent):
        """Mostrar configuración de Windows FSx"""
        config = self.fs_data['windows_config']
        if not config:
            ttk.Label(parent, text="No hay configuración disponible").pack()
            return
        
        info = []
        if 'ThroughputCapacity' in config:
            info.append(("Throughput Capacity:", f"{config['ThroughputCapacity']} MB/s"))
        if 'DeploymentType' in config:
            info.append(("Deployment Type:", config['DeploymentType']))
        if 'ActiveDirectoryId' in config:
            info.append(("Active Directory ID:", config['ActiveDirectoryId']))
        if 'AutomaticBackupRetentionDays' in config:
            info.append(("Backup Retention:", f"{config['AutomaticBackupRetentionDays']} días"))
        if 'DailyAutomaticBackupStartTime' in config:
            info.append(("Backup Start Time:", config['DailyAutomaticBackupStartTime']))
        if 'CopyTagsToBackups' in config:
            info.append(("Copy Tags to Backups:", str(config['CopyTagsToBackups'])))
        if 'PreferredFileServerIp' in config:
            info.append(("Preferred File Server IP:", config['PreferredFileServerIp']))
        
        for i, (label, value) in enumerate(info):
            ttk.Label(parent, text=label, font=('Segoe UI', 10, 'bold')).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            ttk.Label(parent, text=value).grid(row=i, column=1, sticky='w', pady=5)
    
    def mostrar_config_lustre(self, parent):
        """Mostrar configuración de Lustre FSx"""
        config = self.fs_data['lustre_config']
        if not config:
            ttk.Label(parent, text="No hay configuración disponible").pack()
            return
        
        info = []
        if 'DeploymentType' in config:
            info.append(("Deployment Type:", config['DeploymentType']))
        if 'PerUnitStorageThroughput' in config:
            info.append(("Per Unit Throughput:", f"{config['PerUnitStorageThroughput']} MB/s/TiB"))
        if 'MountName' in config:
            info.append(("Mount Name:", config['MountName']))
        if 'DataRepositoryConfiguration' in config:
            repo = config['DataRepositoryConfiguration']
            if 'ImportPath' in repo:
                info.append(("Import Path:", repo['ImportPath']))
            if 'ExportPath' in repo:
                info.append(("Export Path:", repo['ExportPath']))
        
        for i, (label, value) in enumerate(info):
            ttk.Label(parent, text=label, font=('Segoe UI', 10, 'bold')).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            ttk.Label(parent, text=value).grid(row=i, column=1, sticky='w', pady=5)
    
    def mostrar_config_ontap(self, parent):
        """Mostrar configuración de ONTAP FSx"""
        config = self.fs_data['ontap_config']
        if not config:
            ttk.Label(parent, text="No hay configuración disponible").pack()
            return
        
        info = []
        if 'DeploymentType' in config:
            info.append(("Deployment Type:", config['DeploymentType']))
        if 'ThroughputCapacity' in config:
            info.append(("Throughput Capacity:", f"{config['ThroughputCapacity']} MB/s"))
        if 'AutomaticBackupRetentionDays' in config:
            info.append(("Backup Retention:", f"{config['AutomaticBackupRetentionDays']} días"))
        if 'DailyAutomaticBackupStartTime' in config:
            info.append(("Backup Start Time:", config['DailyAutomaticBackupStartTime']))
        if 'Endpoints' in config:
            endpoints = config['Endpoints']
            if 'Management' in endpoints and 'IpAddresses' in endpoints['Management']:
                ips = ', '.join(endpoints['Management']['IpAddresses'])
                info.append(("Management IPs:", ips))
        
        for i, (label, value) in enumerate(info):
            ttk.Label(parent, text=label, font=('Segoe UI', 10, 'bold')).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            ttk.Label(parent, text=value).grid(row=i, column=1, sticky='w', pady=5)
    
    def mostrar_config_openzfs(self, parent):
        """Mostrar configuración de OpenZFS FSx"""
        config = self.fs_data['openzfs_config']
        if not config:
            ttk.Label(parent, text="No hay configuración disponible").pack()
            return
        
        info = []
        if 'DeploymentType' in config:
            info.append(("Deployment Type:", config['DeploymentType']))
        if 'ThroughputCapacity' in config:
            info.append(("Throughput Capacity:", f"{config['ThroughputCapacity']} MB/s"))
        if 'AutomaticBackupRetentionDays' in config:
            info.append(("Backup Retention:", f"{config['AutomaticBackupRetentionDays']} días"))
        if 'CopyTagsToBackups' in config:
            info.append(("Copy Tags to Backups:", str(config['CopyTagsToBackups'])))
        if 'CopyTagsToVolumes' in config:
            info.append(("Copy Tags to Volumes:", str(config['CopyTagsToVolumes'])))
        if 'EndpointIpAddress' in config:
            info.append(("Endpoint IP Address:", config['EndpointIpAddress']))
        
        for i, (label, value) in enumerate(info):
            ttk.Label(parent, text=label, font=('Segoe UI', 10, 'bold')).grid(
                row=i, column=0, sticky='w', pady=5, padx=(0, 10))
            ttk.Label(parent, text=value).grid(row=i, column=1, sticky='w', pady=5)
    
    def crear_tab_red(self, parent):
        """Crear pestaña de información de red"""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        ttk.Label(frame, text="VPC:", font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        ttk.Label(frame, text=self.fs_data['vpc_id']).grid(
            row=0, column=1, sticky='w', pady=5)
        
        ttk.Label(frame, text="IP Addresses:", font=('Segoe UI', 10, 'bold')).grid(
            row=1, column=0, sticky='w', pady=5, padx=(0, 10))
        ttk.Label(frame, text=self.fs_data['ip_addresses']).grid(
            row=1, column=1, sticky='w', pady=5)
        
        ttk.Label(frame, text="Subnet IDs:", font=('Segoe UI', 10, 'bold')).grid(
            row=2, column=0, sticky='nw', pady=5, padx=(0, 10))
        
        if self.fs_data['subnet_ids']:
            subnets_text = '\n'.join(self.fs_data['subnet_ids'])
            text_widget = tk.Text(frame, height=len(self.fs_data['subnet_ids']) + 1, width=50, wrap='none')
            text_widget.insert('1.0', subnets_text)
            text_widget.config(state='disabled')
            text_widget.grid(row=2, column=1, sticky='w', pady=5)
        else:
            ttk.Label(frame, text="N/A").grid(row=2, column=1, sticky='w', pady=5)
        
        ttk.Label(frame, text="DNS Name:", font=('Segoe UI', 10, 'bold')).grid(
            row=3, column=0, sticky='w', pady=5, padx=(0, 10))
        ttk.Label(frame, text=self.fs_data['dns_name']).grid(
            row=3, column=1, sticky='w', pady=5)
    
    def crear_tab_tags(self, parent):
        """Crear pestaña de tags"""
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        if not self.fs_data['tags']:
            ttk.Label(frame, text="No hay tags configurados").pack()
            return
        
        # TreeView para tags
        columns = ["Key", "Value"]
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        
        tree.heading("Key", text="Key")
        tree.heading("Value", text="Value")
        tree.column("Key", width=200)
        tree.column("Value", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", expand=True, fill='both')
        scrollbar.pack(side="right", fill='y')
        
        # Insertar tags
        for tag in self.fs_data['tags']:
            tree.insert("", "end", values=(tag['Key'], tag['Value']))