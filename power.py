import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
import cliente as cliente
from widgets import LoadingIndicator, StatusBar
from logs import LogsInsightsTab
from tags import TagsTab
from ec2 import EC2Tab
from rds import RDSTab
from s3 import S3Tab
from vpc import VPCTab
from sg import SGTab
from fsx import FSxTab


class AppAWS:
    def __init__(self, root):
        self.root = root
        
        # Configurar el tema inicial
        self.tema_actual = "superhero"
        self.style = ttk.Style(self.tema_actual)
        self.configurar_estilos_interfaz()

        self.root.title("AWS Resource Manager")
        self.root.state('zoomed')
        self.root.minsize(1200, 700)  # Aumentado el mínimo para mejor visualización
        
        self.cuentas = ["Prod", "QA", "UAT", "SharedServices", "Networking", 
                       "Management", "Audit", "LogArchive", "Backup", "DataPRD", "DataQA"]
        
        # Cache para información de cuentas obtenida dinámicamente
        self.info_cuentas_cache = {}
        
        # Inicialización de clientes
        self._inicializar_clientes()
        
        self.cuenta_actual = None
        self.loading = LoadingIndicator(root)
        
        # Referencias a las tabs
        self._inicializar_tabs()

        # Crear interfaz con mejor estructura
        self.crear_interfaz()
        
        self.status_bar.set_status("Desconectado", "danger", "Selecciona una cuenta AWS")
        
        # Bind para detectar cambios de tamaño
        self.root.bind('<Configure>', self._on_window_resize)
    
    def _inicializar_clientes(self):
        """Inicializa todos los clientes AWS"""
        self.ec2_client = None
        self.rds_client = None
        self.s3_client = None
        self.fsx_client = None
        self.sts_client = None
        self.iam_client = None
    
    def _inicializar_tabs(self):
        """Inicializa referencias a tabs"""
        self.ec2_tab = None
        self.rds_tab = None
        self.s3_tab = None
        self.vpc_tab = None
        self.sg_tab = None
        self.fsx_tab = None
        self.logs_insights_tab = None
        self.tags_tab = None
    
    def crear_interfaz(self):
        """Crea toda la interfaz de forma organizada"""
        # Frame principal con peso para expandirse
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(expand=True, fill='both')
        
        # Configurar grid weights para expansión correcta
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Header (fijo)
        self.crear_header()
        
        # Contenido principal (expandible)
        self.crear_contenido_principal()
        
        # Status bar (fijo en la parte inferior)
        self.crear_status_bar()
    
    def _on_window_resize(self, event):
        """Maneja el evento de cambio de tamaño de ventana"""
        if event.widget == self.root:
            # Forzar actualización del layout
            self.root.update_idletasks()
    
    def configurar_estilos_interfaz(self):
        """Configura todos los estilos de la interfaz"""
        self.style.configure("Treeview", font=('Segoe UI', 12))
        self.style.configure("Treeview.Heading", font=('Segoe UI', 14, 'bold'))
        self.style.configure("Treeview", rowheight=30)
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 12))
        self.configurar_estilos_botones()

    def crear_header(self):
        """Crea el header con título y controles"""
        header_frame = ttk.Frame(self.main_container)
        header_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        
        # Configurar columnas del header
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)
        
        # Título a la izquierda
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky='w')
        
        ttk.Label(title_frame, text="⚡ AWS Resource Manager", 
                 font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        
        # Controles a la derecha
        self._crear_controles_cuenta(header_frame)
    
    def _crear_controles_cuenta(self, parent):
        """Crea los controles de selección de cuenta"""
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=0, column=1, sticky='e')
        
        ttk.Label(controls_frame, text="Cuenta AWS:", 
                 font=('Segoe UI', 10)).pack(anchor='w')
        
        # Frame para combobox y botón
        combo_frame = ttk.Frame(controls_frame)
        combo_frame.pack(pady=5)
        
        self.combo_cuentas = ttk.Combobox(
            combo_frame, 
            values=self.cuentas, 
            state="readonly",
            font=('Segoe UI', 12), 
            width=20
        )
        self.combo_cuentas.set("Seleccionar cuenta")
        self.combo_cuentas.pack(side='left', padx=(0, 5))
        self.combo_cuentas.bind("<<ComboboxSelected>>", self.cambiar_cuenta)
        
        # Botón de información
        self.btn_info = ttk.Button(
            combo_frame, 
            text="ℹ", 
            width=3, 
            command=self.mostrar_info_cuenta, 
            state="disabled",
            style="info.TButton"
        )
        self.btn_info.pack(side='left')
    
    def crear_contenido_principal(self):
        """Crea el área de contenido principal con las tabs"""
        # Frame para contenido que se expande
        content_frame = ttk.Frame(self.main_container)
        content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        
        # Configurar expansión
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Notebook con las tabs
        self.tabs = ttk.Notebook(content_frame)
        self.tabs.grid(row=0, column=0, sticky='nsew')
        
        # Crear todas las tabs
        self._crear_todas_las_tabs()
    
    def _crear_todas_las_tabs(self):
        """Crea todas las tabs del notebook"""
        tabs_config = [
            ("EC2", EC2Tab, 'ec2_tab'),
            ("RDS", RDSTab, 'rds_tab'),
            ("S3", S3Tab, 's3_tab'),
            ("VPC Logs", LogsInsightsTab, 'logs_insights_tab'),
            ("Tags", TagsTab, 'tags_tab'),
            ("VPC", VPCTab, 'vpc_tab'),
            ("Security Groups", SGTab, 'sg_tab'),
            ("FSx", FSxTab, 'fsx_tab')
        ]
        
        for tab_name, tab_class, attr_name in tabs_config:
            frame = ttk.Frame(self.tabs)
            self.tabs.add(frame, text=f" {tab_name} ")
            setattr(self, attr_name, tab_class(frame, self))

    def crear_status_bar(self):
        """Crea la barra de estado fija en la parte inferior"""
        # Frame para status bar que NO se expande
        status_frame = ttk.Frame(self.main_container)
        status_frame.grid(row=2, column=0, sticky='ew', padx=0, pady=0)
        
        self.status_bar = StatusBar(status_frame)
    
    def cambiar_cuenta(self, event):
        """Maneja el cambio de cuenta AWS"""
        cuenta = self.combo_cuentas.get()
        
        if not cuenta or cuenta == "Seleccionar cuenta":
            return
        
        self.status_bar.set_status("Conectando...", "warning", f"Cuenta: {cuenta}")

        def conectar():
            try:
                self.loading.show(f"Conectando a cuenta {cuenta}...")
                time.sleep(0.5)  # Reducido el delay
                
                # Crear clientes
                self._crear_clientes_aws(cuenta)
                
                self.cuenta_actual = cuenta
                self.root.after(0, self.actualizar_despues_conexion, cuenta)
                
            except Exception as e:
                self.root.after(0, self.mostrar_error_conexion, cuenta, str(e))
            finally:
                self.root.after(0, self.loading.hide)
        
        threading.Thread(target=conectar, daemon=True).start()
    
    def _crear_clientes_aws(self, cuenta):
        """Crea todos los clientes AWS necesarios"""
        self.ec2_client = cliente.crear("ec2", cuenta)
        self.rds_client = cliente.crear("rds", cuenta)
        self.s3_client = cliente.crear("s3", cuenta)
        self.fsx_client = cliente.crear("fsx", cuenta)
        self.sts_client = cliente.crear("sts", cuenta)
        self.iam_client = cliente.crear("iam", cuenta)
    
    def actualizar_despues_conexion(self, cuenta):
        """Actualiza la interfaz después de conectarse exitosamente"""
        self.status_bar.set_status("Conectado", "success", f"Cuenta: {cuenta}")
        
        # Habilitar botón de información
        self.btn_info.configure(state="normal")
        
        # Limpiar caches y clientes
        self._limpiar_caches_tabs()
        
        # Refrescar tabs activas
        self._refrescar_tabs_activas()
    
    def _limpiar_caches_tabs(self):
        """Limpia los caches de todas las tabs"""
        # Limpiar cache de información de cuenta
        if self.cuenta_actual in self.info_cuentas_cache:
            del self.info_cuentas_cache[self.cuenta_actual]
        
        # Limpiar clientes en tabs específicas
        tabs_con_clientes = [
            ('logs_insights_tab', 'logs_client'),
            ('s3_tab', 's3_client'),
            ('fsx_tab', 'fsx_client'),
            ('vpc_tab', 'ec2_client')
        ]
        
        for tab_name, client_name in tabs_con_clientes:
            if hasattr(self, tab_name):
                tab = getattr(self, tab_name)
                if hasattr(tab, client_name):
                    setattr(tab, client_name, None)
        
        # Limpiar datos de Security Groups
        if hasattr(self, 'sg_tab'):
            self.sg_tab.sg_data = []
            self.sg_tab.vpc_data = {}
    
    def _refrescar_tabs_activas(self):
        """Refresca las tabs que requieren actualización automática"""
        if self.ec2_tab:
            self.ec2_tab.refrescar_ec2()
        if self.rds_tab:
            self.rds_tab.refrescar_rds()

    def mostrar_error_conexion(self, cuenta, error):
        """Muestra error al conectar con cuenta"""
        self.status_bar.set_status("Error de conexión", "danger", f"Cuenta: {cuenta}")
        self.btn_info.configure(state="disabled")
        self._inicializar_clientes()
        messagebox.showerror(
            "Error de conexión", 
            f"No se pudo conectar con la cuenta {cuenta}\n\nError: {error}"
        )
    
    def mostrar_info_cuenta(self):
        """Muestra la información de la cuenta actual"""
        if not self.cuenta_actual:
            messagebox.showerror("Error", "No hay cuenta seleccionada")
            return
        
        self.loading.show("Obteniendo información de la cuenta...")
        
        def obtener_info():
            try:
                info_cuenta = self.obtener_info_cuenta_dinamica()
                self.root.after(0, self.mostrar_ventana_info, info_cuenta)
            except Exception as e:
                self.root.after(0, self.mostrar_error_info, str(e))
            finally:
                self.root.after(0, self.loading.hide)
        
        threading.Thread(target=obtener_info, daemon=True).start()
    
    def obtener_info_cuenta_dinamica(self):
        """Obtiene información dinámica de la cuenta AWS"""
        # Verificar cache
        if self.cuenta_actual in self.info_cuentas_cache:
            return self.info_cuentas_cache[self.cuenta_actual]
        
        info = {
            "nombre": self.cuenta_actual,
            "id": "No disponible",
            "arn": "No disponible"
        }
        
        try:
            if not self.sts_client:
                self.sts_client = cliente.crear("sts", self.cuenta_actual)
            
            caller_identity = self.sts_client.get_caller_identity()
            info["id"] = caller_identity.get("Account", "No disponible")
            info["arn"] = caller_identity.get("Arn", "No disponible")
            
            # Obtener información adicional con IAM
            try:
                if not self.iam_client:
                    self.iam_client = cliente.crear("iam", self.cuenta_actual)
                
                aliases = self.iam_client.list_account_aliases()
                if aliases.get("AccountAliases"):
                    info["alias"] = aliases["AccountAliases"][0]
            except:
                pass
        
        except Exception as e:
            print(f"Error obteniendo información de cuenta: {str(e)}")
        
        # Guardar en cache
        self.info_cuentas_cache[self.cuenta_actual] = info
        return info

    def mostrar_ventana_info(self, info_cuenta):
        """Muestra ventana con información de la cuenta"""
        info_window = ttk.Toplevel(self.root)
        info_window.title("Información de la Cuenta")
        info_window.geometry("550x400")
        info_window.resizable(False, False)
        info_window.transient(self.root)
        info_window.grab_set()

        # Centrar ventana
        self._centrar_ventana(info_window, 550, 500)

        # Frame principal
        main_frame = ttk.Frame(info_window, padding=20)
        main_frame.pack(fill='both', expand=True)

        '''# Título
        ttk.Label(
            main_frame, 
            text="AWS Resource Manager",
            font=('Segoe UI', 16, 'bold')
        ).pack(pady=(0, 20))'''

        # Frame para información
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill='x', pady=5)

        # Label de feedback
        feedback_label = ttk.Label(
            main_frame, 
            text="", 
            font=('Segoe UI', 10, 'bold'), 
            foreground="green"
        )
        feedback_label.pack(pady=(10, 0))

        def show_feedback(msg="✓ Copiado al portapapeles"):
            feedback_label.config(text=msg)
            info_window.after(1500, lambda: feedback_label.config(text=""))

        # Información de la cuenta
        info_items = [
            ("Cuenta:", info_cuenta["nombre"]),
            ("ID de Cuenta:", info_cuenta["id"]),
            ("ARN:", info_cuenta["arn"])
        ]

        if info_cuenta.get("alias", "No disponible") != "No disponible":
            info_items.insert(2, ("Alias:", info_cuenta["alias"]))

        for label_text, value_text in info_items:
            # Label
            ttk.Label(
                info_frame, 
                text=label_text, 
                font=('Segoe UI', 11, 'bold')
            ).pack(anchor='w', pady=(5, 2))

            # Entry copiable
            entry = ttk.Entry(info_frame, font=('Segoe UI', 10), width=60)
            entry.insert(0, value_text)
            entry.config(state='readonly')
            entry.pack(anchor='w', padx=(10, 0), fill='x')

            # Click para copiar
            def on_click(event, val=value_text):
                info_window.clipboard_clear()
                info_window.clipboard_append(val)
                show_feedback()
                return "break"

            entry.bind('<Button-1>', on_click)

        # Footer
        ttk.Label(
            main_frame, 
            text="by wpinto", 
            font=('Segoe UI', 10, 'italic')
        ).pack(side='bottom', pady=(20, 0))

        # Botón cerrar
        ttk.Button(
            main_frame, 
            text="Cerrar", 
            command=info_window.destroy,
            style="primary.TButton"
        ).pack(side='bottom', pady=(10, 0))
    
    def _centrar_ventana(self, ventana, ancho, alto):
        """Centra una ventana en la pantalla"""
        x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
        y = (ventana.winfo_screenheight() // 2) - (alto // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    
    def mostrar_error_info(self, error_msg):
        """Muestra error al obtener información"""
        messagebox.showerror(
            "Error", 
            f"No se pudo obtener la información de la cuenta:\n\n{error_msg}"
        )
    
    def obtener_color_estado(self, estado):
        """Obtiene color según el estado"""
        estados_map = {
            ("running", "available"): "success",
            ("stopped", "stopping"): "danger",
            ("pending", "starting"): "warning"
        }
        
        for estados, color in estados_map.items():
            if estado in estados:
                return color
        return "normal"
    
    def configurar_colores_tree(self, tree):
        """Configura colores en TreeView"""
        colores = {
            "success": "#28a745",
            "danger": "#dc3545",
            "warning": "#ffc107",
            "normal": "white"
        }
        
        for tag, color in colores.items():
            tree.tag_configure(tag, foreground=color)

    def configurar_estilos_botones(self):
        """Configura estilos para botones"""
        estilos_base = {
            "font": ('Segoe UI', 11, 'bold'),
            "padding": (10, 8)
        }
        
        botones = ["TButton", "primary.TButton", "success.TButton", 
                   "danger.TButton", "warning.TButton"]
        
        for boton in botones:
            self.style.configure(f"Large.{boton}", **estilos_base)


def main():
    root = ttk.Window()
    app = AppAWS(root)
    root.mainloop()


if __name__ == "__main__":
    main()