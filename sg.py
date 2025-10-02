import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading


class SGTab:
    def __init__(self, parent_frame, main_app):
        self.parent_frame = parent_frame
        self.main_app = main_app
        self.tree_sg = None
        self.sg_count_label = None
        self.sg_data = []
        self.vpc_combo = None
        self.vpc_data = {}
        self.selected_vpc = "all"
        
        self.crear_tab_sg()
    
    def crear_tab_sg(self):
        """Crear la interfaz principal del tab de Security Groups"""
        # Frame superior
        top_frame = ttk.Frame(self.parent_frame)
        top_frame.pack(fill='x', padx=20, pady=15)
        
        # Título
        title_label = ttk.Label(top_frame, text="🛡️ Security Groups", 
                               font=('Segoe UI', 16, 'bold'))
        title_label.pack(side='left')
        
        # Contador
        self.sg_count_label = ttk.Label(top_frame, text="0 security groups",
                                       font=('Segoe UI', 10))
        self.sg_count_label.pack(side='left', padx=(20, 0))
        
        # Botón actualizar
        refresh_btn = ttk.Button(top_frame, text="🔄 Actualizar", 
                               command=self.refrescar_sg)
        refresh_btn.pack(side='right')
        
        # Frame filtro
        filter_frame = ttk.Frame(self.parent_frame)
        filter_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        ttk.Label(filter_frame, text="Filtrar por VPC:").pack(side='left')
        
        self.vpc_combo = ttk.Combobox(filter_frame, state="readonly", width=40)
        self.vpc_combo.pack(side='left', padx=(10, 0))
        self.vpc_combo.bind("<<ComboboxSelected>>", self.filtrar_por_vpc)
        
        # TreeView
        tree_frame = ttk.Frame(self.parent_frame)
        tree_frame.pack(expand=True, fill='both', padx=20, pady=(0, 20))
        
        columns = ["ID", "Nombre", "VPC", "Descripción", "Reglas In", "Reglas Out"]
        self.tree_sg = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                   selectmode="browse")
        
        # Configurar columnas
        widths = [80, 240, 320, 320, 20, 20]
        for col, width in zip(columns, widths):
            self.tree_sg.heading(col, text=col)
            self.tree_sg.column(col, width=width, minwidth=50)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_sg.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_sg.xview)
        self.tree_sg.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree_sg.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Eventos
        self.tree_sg.bind('<Double-1>', self.ver_reglas_sg)
    
    def refrescar_sg(self):
        """Refrescar la lista de Security Groups"""
        if not self.main_app.ec2_client:
            messagebox.showwarning("Sin conexión", "Conecta a una cuenta AWS primero")
            return
            
        self.main_app.status_bar.set_status("Cargando Security Groups...", "info")
        
        def cargar_datos():
            try:
                sgs = self.obtener_security_groups()
                vpcs = self.obtener_vpcs()
                self.main_app.root.after(0, self.actualizar_tree_sg, sgs, vpcs)
            except Exception as e:
                self.main_app.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Error al cargar Security Groups: {str(e)}"))
            finally:
                self.main_app.root.after(0, lambda: self.main_app.status_bar.set_status(
                    "Conectado", "success"))
        
        threading.Thread(target=cargar_datos, daemon=True).start()
    
    def obtener_security_groups(self):
        """Obtiene todos los security groups"""
        response = self.main_app.ec2_client.describe_security_groups()
        sgs = []
        
        for sg in response['SecurityGroups']:
            # Obtener nombre del tag Name
            sg_name = sg['GroupName']
            if 'Tags' in sg:
                for tag in sg['Tags']:
                    if tag['Key'] == 'Name' and tag['Value']:
                        sg_name = tag['Value']
                        break
            
            sg_data = {
                'id': sg['GroupId'],
                'name': sg_name,
                'vpc_id': sg.get('VpcId', 'EC2-Classic'),
                'description': sg['Description'],
                'ingress_rules': len(sg['IpPermissions']),
                'egress_rules': len(sg['IpPermissionsEgress']),
                'ingress_permissions': sg['IpPermissions'],
                'egress_permissions': sg['IpPermissionsEgress']
            }
            sgs.append(sg_data)
        
        return sorted(sgs, key=lambda x: (x['vpc_id'], x['name']))
    
    def obtener_vpcs(self):
        """Obtiene información de las VPCs"""
        try:
            response = self.main_app.ec2_client.describe_vpcs()
            vpcs = {}
            
            for vpc in response['Vpcs']:
                vpc_name = vpc['VpcId']
                if 'Tags' in vpc:
                    for tag in vpc['Tags']:
                        if tag['Key'] == 'Name' and tag['Value']:
                            vpc_name = f"{vpc['VpcId']} ({tag['Value']})"
                            break
                
                if vpc.get('IsDefault', False):
                    vpc_name += " [Default]"
                
                vpcs[vpc['VpcId']] = vpc_name
            
            return vpcs
        except Exception:
            return {}
    
    def actualizar_tree_sg(self, sgs, vpcs):
        """Actualizar el TreeView con los datos"""
        self.sg_data = sgs
        self.vpc_data = vpcs
        
        # Actualizar combo VPCs
        vpc_options = ["Todas las VPCs"]
        vpc_options.extend(sorted(vpcs.values()))
        
        self.vpc_combo.configure(values=vpc_options)
        if not self.vpc_combo.get():
            self.vpc_combo.set("Todas las VPCs")
        
        self.mostrar_sg_filtrados()
    
    def mostrar_sg_filtrados(self):
        """Mostrar Security Groups filtrados"""
        # Limpiar tree
        for item in self.tree_sg.get_children():
            self.tree_sg.delete(item)
        
        # Aplicar filtro
        sgs_filtrados = self.sg_data
        if self.selected_vpc != "all":
            sgs_filtrados = [sg for sg in self.sg_data if sg['vpc_id'] == self.selected_vpc]
        
        # Insertar datos
        for sg in sgs_filtrados:
            vpc_display = self.vpc_data.get(sg['vpc_id'], sg['vpc_id'])
            
            # Truncar descripción si es muy larga
            description = sg['description']
            if len(description) > 50:
                description = description[:47] + "..."
            
            self.tree_sg.insert("", "end", values=(
                sg['id'],
                sg['name'],
                vpc_display,
                description,
                sg['ingress_rules'],
                sg['egress_rules']
            ))
        
        # Actualizar contador
        count = len(sgs_filtrados)
        self.sg_count_label.config(text=f"{count} security groups")
    
    def filtrar_por_vpc(self, event):
        """Filtrar Security Groups por VPC"""
        selection = self.vpc_combo.get()
        if selection == "Todas las VPCs":
            self.selected_vpc = "all"
        else:
            # Extraer VPC ID
            vpc_id = selection.split(" (")[0].split(" [")[0]
            self.selected_vpc = vpc_id
        
        self.mostrar_sg_filtrados()
    
    def ver_reglas_sg(self, event=None):
        """Ver las reglas del Security Group seleccionado"""
        selected = self.tree_sg.selection()
        if not selected:
            return
        
        item = self.tree_sg.item(selected[0])
        sg_id = item["values"][0]
        
        # Buscar datos completos
        sg_data = next((sg for sg in self.sg_data if sg["id"] == sg_id), None)
        if sg_data:
            SGRulesViewer(self.main_app.root, sg_data)


class SGRulesViewer:
    """Ventana para visualizar reglas de un Security Group"""
    
    def __init__(self, parent, sg_data):
        self.sg_data = sg_data
        
        self.window = tk.Toplevel(parent)
        self.window.title(f"Reglas - {sg_data['name']}")
        self.window.geometry("800x800")
        self.window.transient(parent)
        
        self.crear_interfaz()
        self.cargar_reglas()
    
    def crear_interfaz(self):
        """Crear la interfaz de la ventana"""
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Label(header_frame, text=f"🛡️ {self.sg_data['name']}", 
                 font=('Segoe UI', 14, 'bold')).pack(anchor='w')
        
        ttk.Label(header_frame, text=f"ID: {self.sg_data['id']}").pack(anchor='w', pady=(5, 0))
        ttk.Label(header_frame, text=f"VPC: {self.sg_data['vpc_id']}").pack(anchor='w')
        ttk.Label(header_frame, text=f"Descripción: {self.sg_data['description']}").pack(anchor='w')
        
        # Separador
        ttk.Separator(self.window, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill='both', padx=20, pady=(0, 20))
        
        # Tab Ingress
        ingress_frame = ttk.Frame(notebook)
        notebook.add(ingress_frame, text=f"Entrada ({self.sg_data['ingress_rules']})")
        
        # Tab Egress
        egress_frame = ttk.Frame(notebook)
        notebook.add(egress_frame, text=f"Salida ({self.sg_data['egress_rules']})")
        
        # Crear trees
        self.ingress_tree = self.crear_rules_tree(ingress_frame)
        self.egress_tree = self.crear_rules_tree(egress_frame)
        
        # Botón cerrar
        ttk.Button(self.window, text="Cerrar", 
                  command=self.window.destroy).pack(pady=(0, 20))
    
    def crear_rules_tree(self, parent):
        """Crear TreeView para reglas"""
        frame = ttk.Frame(parent)
        frame.pack(expand=True, fill='both', padx=15, pady=15)
        
        columns = ["Protocolo", "Puerto", "Origen/Destino", "Descripción"]
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        # Configurar columnas
        widths = [80, 100, 250, 200]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, minwidth=50)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", expand=True, fill='both')
        scrollbar.pack(side="right", fill='y')
        
        return tree
    
    def cargar_reglas(self):
        """Cargar reglas en ambos trees"""
        self.cargar_reglas_en_tree(self.ingress_tree, self.sg_data['ingress_permissions'])
        self.cargar_reglas_en_tree(self.egress_tree, self.sg_data['egress_permissions'])
    
    def cargar_reglas_en_tree(self, tree, permissions):
        """Cargar reglas en un TreeView específico"""
        if not permissions:
            tree.insert("", "end", values=("", "", "Sin reglas", ""))
            return
        
        for perm in permissions:
            protocol = perm.get('IpProtocol', 'Todos')
            if protocol == '-1':
                protocol = 'Todos'
            
            # Puerto
            if protocol == 'Todos':
                port = "Todos"
            elif 'FromPort' in perm and 'ToPort' in perm:
                if perm['FromPort'] == perm['ToPort']:
                    port = str(perm['FromPort'])
                else:
                    port = f"{perm['FromPort']}-{perm['ToPort']}"
            else:
                port = "Todos"
            
            # Fuentes/destinos
            sources = self.obtener_sources(perm)
            
            for source_text, desc in sources:
                tree.insert("", "end", values=(protocol, port, source_text, desc))
    
    def obtener_sources(self, perm):
        """Obtener fuentes/destinos de una regla"""
        sources = []
        
        # IP Ranges
        for ip_range in perm.get('IpRanges', []):
            cidr = ip_range['CidrIp']
            desc = ip_range.get('Description', '')
            if cidr == '0.0.0.0/0':
                sources.append(("Anywhere (0.0.0.0/0)", desc))
            else:
                sources.append((cidr, desc))
        
        # IPv6 Ranges
        for ipv6_range in perm.get('Ipv6Ranges', []):
            cidr = ipv6_range['CidrIpv6']
            desc = ipv6_range.get('Description', '')
            if cidr == '::/0':
                sources.append(("Anywhere IPv6 (::/0)", desc))
            else:
                sources.append((cidr, desc))
        
        # Security Groups
        for sg_ref in perm.get('UserIdGroupPairs', []):
            sg_id = sg_ref.get('GroupId', '')
            desc = sg_ref.get('Description', '')
            sources.append((f"SG: {sg_id}", desc))
        
        return sources if sources else [("N/A", "")]