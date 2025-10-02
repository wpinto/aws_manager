import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import threading
import time
from widgets import DetailWindow

class VPCTab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.tree_vpc = None
        self.tree_subnets = None
        self.vpc_count_label = None
        self.subnet_count_label = None
        self.vpc_context_menu = None
        self.subnet_context_menu = None
        self.vpc_data = []
        self.subnet_data = []
        self.ec2_client = None
        
        self.crear_tab_vpc()
    
    def crear_tab_vpc(self):
        # Frame principal con división vertical
        main_paned = ttk.PanedWindow(self.parent_frame, orient="vertical")
        main_paned.pack(expand=True, fill='both', padx=10, pady=10)
        
        # ===================
        # SECCIÓN VPC (Arriba)
        # ===================
        vpc_frame = ttk.Frame(main_paned)
        main_paned.add(vpc_frame, weight=1)
        
        # Header VPC
        vpc_top_frame = ttk.Frame(vpc_frame)
        vpc_top_frame.pack(fill='x', pady=(0, 10))
        
        vpc_info_frame = ttk.Frame(vpc_top_frame)
        vpc_info_frame.pack(side='left')
        
        ttk.Label(vpc_info_frame, text="Virtual Private Clouds (VPC)", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        
        self.vpc_count_label = ttk.Label(vpc_info_frame, text="0 VPCs encontradas",
                                        font=('Segoe UI', 10))
        self.vpc_count_label.pack(anchor='w')
        
        vpc_btn_frame = ttk.Frame(vpc_top_frame)
        vpc_btn_frame.pack(side='right')
        
        ttk.Button(vpc_btn_frame, text="🔄 Actualizar VPCs", command=self.refrescar_vpc,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        
        # TreeView VPC
        vpc_tree_frame = ttk.Frame(vpc_frame)
        vpc_tree_frame.pack(expand=True, fill='both')
        
        vpc_columns = ["VPC ID", "Nombre", "CIDR", "Estado", "Tenancy", "DNS Hostnames", "DNS Resolution"]
        self.tree_vpc = ttk.Treeview(vpc_tree_frame, columns=vpc_columns, show="headings", 
                                    selectmode="extended", height=8)
        
        # Scrollbar VPC
        scrollbar_vpc = ttk.Scrollbar(vpc_tree_frame, orient="vertical", command=self.tree_vpc.yview)
        self.tree_vpc.configure(yscrollcommand=scrollbar_vpc.set)
        
        # Configurar columnas VPC
        vpc_column_widths = [200, 200, 150, 100, 100, 120, 120]
        for i, col in enumerate(vpc_columns):
            self.tree_vpc.heading(col, text=col)
            self.tree_vpc.column(col, width=vpc_column_widths[i], anchor="center")
        
        self.tree_vpc.pack(side="left", expand=True, fill='both')
        scrollbar_vpc.pack(side="right", fill='y')
        
        # ===================
        # SECCIÓN SUBNETS (Abajo)
        # ===================
        subnet_frame = ttk.Frame(main_paned)
        main_paned.add(subnet_frame, weight=1)
        
        # Header Subnets
        subnet_top_frame = ttk.Frame(subnet_frame)
        subnet_top_frame.pack(fill='x', pady=(10, 10))
        
        subnet_info_frame = ttk.Frame(subnet_top_frame)
        subnet_info_frame.pack(side='left')
        
        ttk.Label(subnet_info_frame, text="Subnets", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        
        self.subnet_count_label = ttk.Label(subnet_info_frame, text="0 subnets encontradas",
                                           font=('Segoe UI', 10))
        self.subnet_count_label.pack(anchor='w')
        
        subnet_btn_frame = ttk.Frame(subnet_top_frame)
        subnet_btn_frame.pack(side='right')
        
        ttk.Button(subnet_btn_frame, text="🔄 Actualizar Subnets", command=self.refrescar_subnets,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        
        # TreeView Subnets
        subnet_tree_frame = ttk.Frame(subnet_frame)
        subnet_tree_frame.pack(expand=True, fill='both')
        
        subnet_columns = ["Subnet ID", "Nombre", "VPC ID", "CIDR", "Zona Disponibilidad", "Estado", "IPs Disponibles", "Tipo"]
        self.tree_subnets = ttk.Treeview(subnet_tree_frame, columns=subnet_columns, show="headings", 
                                        selectmode="extended", height=8)
        
        # Scrollbar Subnets
        scrollbar_subnets = ttk.Scrollbar(subnet_tree_frame, orient="vertical", command=self.tree_subnets.yview)
        self.tree_subnets.configure(yscrollcommand=scrollbar_subnets.set)
        
        # Configurar columnas Subnets
        subnet_column_widths = [200, 200, 180, 120, 150, 100, 120, 100]
        for i, col in enumerate(subnet_columns):
            self.tree_subnets.heading(col, text=col)
            self.tree_subnets.column(col, width=subnet_column_widths[i], anchor="center")
        
        self.tree_subnets.pack(side="left", expand=True, fill='both')
        scrollbar_subnets.pack(side="right", fill='y')
        
        # ===================
        # EVENTOS Y MENÚS CONTEXTUALES
        # ===================
        
        # Eventos VPC
        self.tree_vpc.bind('<Double-1>', self.on_vpc_double_click)
        self.tree_vpc.bind('<Button-3>', self.show_vpc_context_menu)
        self.tree_vpc.bind('<<TreeviewSelect>>', self.on_vpc_select)
        
        # Eventos Subnets
        self.tree_subnets.bind('<Double-1>', self.on_subnet_double_click)
        self.tree_subnets.bind('<Button-3>', self.show_subnet_context_menu)
        
        # Menú contextual VPC
        self.vpc_context_menu = tk.Menu(self.main_app.root, tearoff=0)
        self.vpc_context_menu.add_command(label="📋 Ver Detalles", command=self.ver_detalles_vpc)
        self.vpc_context_menu.add_command(label="📄 Copiar VPC ID", command=self.copiar_vpc_id)
        self.vpc_context_menu.add_command(label="📄 Copiar CIDR", command=self.copiar_vpc_cidr)
        self.vpc_context_menu.add_command(label="📄 Copiar Nombre", command=self.copiar_vpc_nombre)
        
        # Menú contextual Subnet
        self.subnet_context_menu = tk.Menu(self.main_app.root, tearoff=0)
        self.subnet_context_menu.add_command(label="📋 Ver Detalles", command=self.ver_detalles_subnet)
        self.subnet_context_menu.add_command(label="📄 Copiar Subnet ID", command=self.copiar_subnet_id)
        self.subnet_context_menu.add_command(label="📄 Copiar CIDR", command=self.copiar_subnet_cidr)
        self.subnet_context_menu.add_command(label="📄 Copiar Nombre", command=self.copiar_subnet_nombre)
    
    def get_ec2_client(self):
        """Obtiene el cliente EC2 de la aplicación principal"""
        if not self.ec2_client and self.main_app.ec2_client:
            self.ec2_client = self.main_app.ec2_client
        return self.ec2_client
    
    def obtener_vpcs(self):
        """Obtiene todas las VPCs"""
        try:
            client = self.get_ec2_client()
            if not client:
                return []
            
            response = client.describe_vpcs()
            vpcs = []
            
            for vpc in response['Vpcs']:
                # Obtener nombre del tag Name
                name = "Sin nombre"
                if 'Tags' in vpc:
                    for tag in vpc['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                
                vpc_data = {
                    'id': vpc['VpcId'],
                    'name': name,
                    'cidr': vpc['CidrBlock'],
                    'state': vpc['State'],
                    'tenancy': vpc['InstanceTenancy'],
                    'dns_hostnames': 'Sí' if vpc.get('DnsHostnames', False) else 'No',
                    'dns_resolution': 'Sí' if vpc.get('DnsResolution', False) else 'No',
                    'is_default': vpc.get('IsDefault', False),
                    'tags': vpc.get('Tags', [])
                }
                vpcs.append(vpc_data)
            
            return vpcs
        except Exception as e:
            print(f"Error obteniendo VPCs: {e}")
            return []
    
    def obtener_subnets(self, vpc_id=None):
        """Obtiene todas las subnets o las de una VPC específica"""
        try:
            client = self.get_ec2_client()
            if not client:
                return []
            
            if vpc_id:
                response = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
            else:
                response = client.describe_subnets()
            
            subnets = []
            
            for subnet in response['Subnets']:
                # Obtener nombre del tag Name
                name = "Sin nombre"
                if 'Tags' in subnet:
                    for tag in subnet['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                
                # Determinar tipo de subnet (público/privado)
                subnet_type = "Privada"
                if subnet.get('MapPublicIpOnLaunch', False):
                    subnet_type = "Pública"
                
                subnet_data = {
                    'id': subnet['SubnetId'],
                    'name': name,
                    'vpc_id': subnet['VpcId'],
                    'cidr': subnet['CidrBlock'],
                    'availability_zone': subnet['AvailabilityZone'],
                    'state': subnet['State'],
                    'available_ips': subnet['AvailableIpAddressCount'],
                    'type': subnet_type,
                    'map_public_ip': subnet.get('MapPublicIpOnLaunch', False),
                    'tags': subnet.get('Tags', [])
                }
                subnets.append(subnet_data)
            
            return subnets
        except Exception as e:
            print(f"Error obteniendo subnets: {e}")
            return []
    
    def refrescar_vpc(self):
        """Actualiza la lista de VPCs"""
        if not self.get_ec2_client():
            messagebox.showwarning("Sin conexión", "Primero selecciona una cuenta AWS")
            return
        
        self.main_app.status_bar.set_status("Cargando VPCs...", "info", f"Cuenta: {self.main_app.cuenta_actual}")
        
        def cargar_datos():
            try:
                vpcs = self.obtener_vpcs()
                self.main_app.root.after(0, self.actualizar_tree_vpc, vpcs)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error al cargar VPCs: {str(e)}"))
            finally:
                self.main_app.root.after(0, lambda: self.main_app.status_bar.set_status("Conectado", "success", f"Cuenta: {self.main_app.cuenta_actual}"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
    
    def refrescar_subnets(self):
        """Actualiza la lista de subnets"""
        if not self.get_ec2_client():
            messagebox.showwarning("Sin conexión", "Primero selecciona una cuenta AWS")
            return
        
        self.main_app.status_bar.set_status("Cargando Subnets...", "info", f"Cuenta: {self.main_app.cuenta_actual}")
        
        def cargar_datos():
            try:
                subnets = self.obtener_subnets()
                self.main_app.root.after(0, self.actualizar_tree_subnets, subnets)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error al cargar Subnets: {str(e)}"))
            finally:
                self.main_app.root.after(0, lambda: self.main_app.status_bar.set_status("Conectado", "success", f"Cuenta: {self.main_app.cuenta_actual}"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
    
    def actualizar_tree_vpc(self, vpcs):
        """Actualiza el TreeView de VPCs"""
        # Limpiar TreeView
        for item in self.tree_vpc.get_children():
            self.tree_vpc.delete(item)
        
        self.vpc_data = vpcs
        
        for vpc in vpcs:
            color_tag = self.main_app.obtener_color_estado(vpc["state"])
            self.tree_vpc.insert("", "end", values=(
                vpc["id"], 
                vpc["name"], 
                vpc["cidr"], 
                vpc["state"], 
                vpc["tenancy"],
                vpc["dns_hostnames"],
                vpc["dns_resolution"]
            ), tags=(color_tag,))
        
        self.main_app.configurar_colores_tree(self.tree_vpc)
        self.vpc_count_label.config(text=f"{len(vpcs)} VPCs encontradas")
    
    def actualizar_tree_subnets(self, subnets):
        """Actualiza el TreeView de Subnets"""
        # Limpiar TreeView
        for item in self.tree_subnets.get_children():
            self.tree_subnets.delete(item)
        
        self.subnet_data = subnets
        
        for subnet in subnets:
            color_tag = self.main_app.obtener_color_estado(subnet["state"])
            # Color especial para subnets públicas
            if subnet["type"] == "Pública":
                color_tag = "warning"
            
            self.tree_subnets.insert("", "end", values=(
                subnet["id"], 
                subnet["name"], 
                subnet["vpc_id"], 
                subnet["cidr"], 
                subnet["availability_zone"],
                subnet["state"],
                subnet["available_ips"],
                subnet["type"]
            ), tags=(color_tag,))
        
        self.main_app.configurar_colores_tree(self.tree_subnets)
        self.subnet_count_label.config(text=f"{len(subnets)} subnets encontradas")
    
    def on_vpc_select(self, event):
        """Evento cuando se selecciona una VPC - muestra sus subnets"""
        selected = self.tree_vpc.selection()
        if not selected:
            return
        
        item = self.tree_vpc.item(selected[0])
        vpc_id = item["values"][0]
        
        # Cargar subnets de la VPC seleccionada
        def cargar_subnets_vpc():
            try:
                subnets = self.obtener_subnets(vpc_id)
                self.main_app.root.after(0, self.actualizar_tree_subnets, subnets)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror("Error", f"Error al cargar subnets: {str(e)}"))
        
        threading.Thread(target=cargar_subnets_vpc, daemon=True).start()
    
    # ===================
    # EVENTOS DE DOBLE CLIC
    # ===================
    
    def on_vpc_double_click(self, event):
        self.ver_detalles_vpc()
    
    def on_subnet_double_click(self, event):
        self.ver_detalles_subnet()
    
    # ===================
    # MENÚS CONTEXTUALES VPC
    # ===================
    
    def show_vpc_context_menu(self, event):
        item = self.tree_vpc.identify_row(event.y)
        if item:
            self.tree_vpc.selection_set(item)
            self.vpc_context_menu.post(event.x_root, event.y_root)
    
    def ver_detalles_vpc(self):
        selected = self.tree_vpc.selection()
        if not selected:
            return
        
        item = self.tree_vpc.item(selected[0])
        vpc_id = item["values"][0]
        
        # Buscar datos completos
        data = next((vpc for vpc in self.vpc_data if vpc["id"] == vpc_id), None)
        if data:
            DetailWindow(self.main_app.root, f"Detalles de VPC - {data['name']}", data, "vpc")
    
    def copiar_vpc_id(self):
        selected = self.tree_vpc.selection()
        if not selected:
            return
        
        item = self.tree_vpc.item(selected[0])
        vpc_id = item["values"][0]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(vpc_id)
    
    def copiar_vpc_cidr(self):
        selected = self.tree_vpc.selection()
        if not selected:
            return
        
        item = self.tree_vpc.item(selected[0])
        cidr = item["values"][2]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(cidr)
    
    def copiar_vpc_nombre(self):
        selected = self.tree_vpc.selection()
        if not selected:
            return
        
        item = self.tree_vpc.item(selected[0])
        nombre = item["values"][1]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(nombre)
    
    # ===================
    # MENÚS CONTEXTUALES SUBNET
    # ===================
    
    def show_subnet_context_menu(self, event):
        item = self.tree_subnets.identify_row(event.y)
        if item:
            self.tree_subnets.selection_set(item)
            self.subnet_context_menu.post(event.x_root, event.y_root)
    
    def ver_detalles_subnet(self):
        selected = self.tree_subnets.selection()
        if not selected:
            return
        
        item = self.tree_subnets.item(selected[0])
        subnet_id = item["values"][0]
        
        # Buscar datos completos
        data = next((subnet for subnet in self.subnet_data if subnet["id"] == subnet_id), None)
        if data:
            DetailWindow(self.main_app.root, f"Detalles de Subnet - {data['name']}", data, "subnet")
    
    def copiar_subnet_id(self):
        selected = self.tree_subnets.selection()
        if not selected:
            return
        
        item = self.tree_subnets.item(selected[0])
        subnet_id = item["values"][0]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(subnet_id)
    
    def copiar_subnet_cidr(self):
        selected = self.tree_subnets.selection()
        if not selected:
            return
        
        item = self.tree_subnets.item(selected[0])
        cidr = item["values"][3]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(cidr)
    
    def copiar_subnet_nombre(self):
        selected = self.tree_subnets.selection()
        if not selected:
            return
        
        item = self.tree_subnets.item(selected[0])
        nombre = item["values"][1]
        
        self.main_app.root.clipboard_clear()
        self.main_app.root.clipboard_append(nombre)