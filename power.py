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


class AppAWS:
    def __init__(self, root):
        self.root = root
        
        # Lista de temas disponibles en ttkbootstrap
        self.temas_disponibles = [
            "cosmo", "superhero", "darkly"
        ]
        
        # Configurar el tema inicial
        self.tema_actual = "superhero"
        self.style = ttk.Style(self.tema_actual)
        self.configurar_estilos_interfaz()

        self.root.title("AWS Resource Manager")
        self.root.state('zoomed')
        self.root.minsize(1000, 800)
        
        self.cuentas = ["QA", "Dev", "UAT", "Prod", "SharedServices", "Networking", "aws_management", "Audit", "LogArchive", "Backup"]
        
        # Cache para información de cuentas obtenida dinámicamente
        self.info_cuentas_cache = {}
        
        self.ec2_client = None
        self.rds_client = None
        self.s3_client = None
        self.sts_client = None  # Cliente STS para obtener información de la cuenta
        self.iam_client = None  # Cliente IAM para obtener información adicional
        self.cuenta_actual = None
        self.loading = LoadingIndicator(root)
        
        # Referencias a las tabs
        self.ec2_tab = None
        self.rds_tab = None
        self.s3_tab = None
        self.vpc_tab = None
        self.sg_tab = None
  

        self.crear_header()
        self.crear_contenido_principal()
        self.crear_status_bar()
        
        self.status_bar.set_status("Desconectado", "danger", " by wpinto Selecciona una cuenta AWS")
    
    def configurar_estilos_interfaz(self):
        """Configura todos los estilos de la interfaz"""
        self.style.configure("Treeview", font=('Segoe UI', 12))
        self.style.configure("Treeview.Heading", font=('Segoe UI', 14, 'bold'))
        self.style.configure("Treeview", rowheight=30)
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 12, ''))
        self.configurar_estilos_botones()

    def cambiar_tema(self, event):
        """Cambia el tema de la aplicación"""
        nuevo_tema = self.combo_temas.get()
        if nuevo_tema != self.tema_actual:
            try:
                # Crear nuevo estilo con el tema seleccionado
                self.style = ttk.Style(nuevo_tema)
                self.tema_actual = nuevo_tema
                
                # Reconfigurar estilos
                self.configurar_estilos_interfaz()
                
                # Reconfigurar colores de los árboles si tienen datos
                if hasattr(self.ec2_tab, 'tree_ec2') and self.ec2_tab.tree_ec2.get_children():
                    self.configurar_colores_tree(self.ec2_tab.tree_ec2)
                if hasattr(self.rds_tab, 'tree_rds') and self.rds_tab.tree_rds.get_children():
                    self.configurar_colores_tree(self.rds_tab.tree_rds)
                    
            except Exception as e:
                messagebox.showerror("Error de tema", f"No se pudo aplicar el tema {nuevo_tema}: {str(e)}")
                # Restaurar tema anterior en el combobox
                self.combo_temas.set(self.tema_actual)

    def crear_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side='left')
        
        ttk.Label(title_frame, text="⚡ AWS Resource Manager", 
                 font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        
        # Frame para controles del lado derecho
        controls_frame = ttk.Frame(header_frame)
        controls_frame.pack(side='right')
        
        # Frame para tema
        tema_frame = ttk.Frame(controls_frame)
        tema_frame.pack(side='top', anchor='e', pady=(0, 5))
        
        ttk.Label(tema_frame, text="Tema:", 
                 font=('Segoe UI', 10)).pack(side='left', padx=(0, 5))
        
        self.combo_temas = ttk.Combobox(tema_frame, values=self.temas_disponibles, 
                                       state="readonly", font=('Segoe UI', 10), width=12)
        self.combo_temas.set(self.tema_actual)
        self.combo_temas.pack(side='left')
        self.combo_temas.bind("<<ComboboxSelected>>", self.cambiar_tema)
        
        # Frame para cuenta AWS
        cuenta_frame = ttk.Frame(controls_frame)
        cuenta_frame.pack(side='top', anchor='e')
        
        ttk.Label(cuenta_frame, text="Cuenta AWS:", 
                 font=('Segoe UI', 10)).pack(anchor='w')
        
        # Frame horizontal para combobox y botón de información
        combo_info_frame = ttk.Frame(cuenta_frame)
        combo_info_frame.pack(pady=5)
        
        self.combo_cuentas = ttk.Combobox(combo_info_frame, values=self.cuentas, state="readonly",
                                         font=('Segoe UI', 12), width=20)
        self.combo_cuentas.set("Seleccionar cuenta")
        self.combo_cuentas.pack(side='left')
        self.combo_cuentas.bind("<<ComboboxSelected>>", self.cambiar_cuenta)
        
        # Botón de información (inicialmente deshabilitado)
        self.btn_info = ttk.Button(combo_info_frame, text="ℹ", width=3, 
                                  command=self.mostrar_info_cuenta, state="disabled",
                                  style="info.TButton")
        self.btn_info.pack(side='left', padx=(5, 0))
    
    def crear_contenido_principal(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        self.tabs = ttk.Notebook(main_frame)
        self.tabs.pack(expand=True, fill='both')
        
        # Crear las tabs usando las clases separadas
        tab_ec2_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_ec2_frame, text=" EC2 ")
        self.ec2_tab = EC2Tab(tab_ec2_frame, self)
        
        tab_rds_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_rds_frame, text=" RDS ")
        self.rds_tab = RDSTab(tab_rds_frame, self)
        
        # Nueva pestaña para S3
        tab_s3_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_s3_frame, text=" S3 ")
        self.s3_tab = S3Tab(tab_s3_frame, self)
        
        # Nueva pestaña para Logs Insights
        tab_logs_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_logs_frame, text=" VPC Logs ")
        self.logs_insights_tab = LogsInsightsTab(tab_logs_frame, self)
        
        # Nueva pestaña para Tags
        tab_tags_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_tags_frame, text=" Tags ")
        self.tags_tab = TagsTab(tab_tags_frame, self)
    
        # Nueva pestaña para VPC
        tab_vpc_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_vpc_frame, text=" VPC ")
        self.vpc_tab = VPCTab(tab_vpc_frame, self)

        # Nueva pestaña para Security Groups
        tab_sg_frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_sg_frame, text=" Security Groups ")
        self.sg_tab = SGTab(tab_sg_frame, self)

    def mostrar_info_cuenta(self):
       
        if not self.cuenta_actual:
            messagebox.showerror("Error", "No hay cuenta seleccionada")
            return
        
        # Mostrar loading mientras se obtiene la información
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

        # Verificar si ya tenemos la info en cache
        if self.cuenta_actual in self.info_cuentas_cache:
            return self.info_cuentas_cache[self.cuenta_actual]
        
        info = {
            "nombre": self.cuenta_actual,
            "id": "No disponible",
            "arn": "No disponible"
        }
        
        try:
            # Crear cliente STS si no existe
            if not self.sts_client:
                self.sts_client = cliente.crear("sts", self.cuenta_actual)
            
            # Obtener información básica de la cuenta
            caller_identity = self.sts_client.get_caller_identity()
            info["id"] = caller_identity.get("Account", "No disponible")
            info["arn"] = caller_identity.get("Arn", "No disponible")
            
            # Intentar obtener información adicional con IAM
            try:
                if not self.iam_client:
                    self.iam_client = cliente.crear("iam", self.cuenta_actual)
                
                # Obtener alias de la cuenta si existe
                try:
                    aliases = self.iam_client.list_account_aliases()
                    if aliases["AccountAliases"]:
                        info["alias"] = aliases["AccountAliases"][0]
                except:
                    info["alias"] = "No disponible"
                
                # Intentar obtener información del usuario/rol actual        
            except Exception as e:
                # Si no se puede acceder a IAM, continuar con la info básica
                pass
        
        except Exception as e:
            # Si hay error obteniendo info básica, mantener valores por defecto
            print(f"Error obteniendo información de cuenta: {str(e)}")
        
        # Guardar en cache
        self.info_cuentas_cache[self.cuenta_actual] = info
        
        return info
    

    def mostrar_ventana_info(self, info_cuenta):
        """Muestra la ventana con la información de la cuenta (click en valor -> copia al portapapeles)"""

        # Crear ventana modal
        info_window = ttk.Toplevel(self.root)
        info_window.title("Información de la Cuenta")
        info_window.geometry("500x620")
        info_window.resizable(True, True)

        # Centrar la ventana
        info_window.transient(self.root)
        info_window.grab_set()

        # Calcular posición para centrar
        x = (info_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (info_window.winfo_screenheight() // 2) - (620 // 2)
        info_window.geometry(f"500x620+{x}+{y}")

        # Frame principal con padding
        main_frame = ttk.Frame(info_window, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Título
        title_label = ttk.Label(main_frame, text="AWS Resource Manager",
                            font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=(0, 10))

        # Frame para la información
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill='x', pady=5)

        # Label de feedback (inicialmente vacío)
        feedback_label = ttk.Label(main_frame, text="", font=('Segoe UI', 10, 'bold'), foreground="green")
        feedback_label.pack(pady=(5, 0))

        # Función para mostrar feedback
        def show_feedback(msg="Copiado al portapapeles"):
            feedback_label.config(text=msg)
            info_window.after(1200, lambda: feedback_label.config(text=""))

        # Información de la cuenta
        info_items = [
            ("Cuenta:", info_cuenta["nombre"]),
            ("ID de Cuenta:", info_cuenta["id"]),
            ("ARN:", info_cuenta["arn"])
        ]

        if "alias" in info_cuenta and info_cuenta["alias"] != "No disponible":
            info_items.insert(2, ("Alias:", info_cuenta["alias"]))

        for label_text, value_text in info_items:
            ttk.Label(info_frame, text=label_text, font=('Segoe UI', 12, 'bold')).pack(anchor='w')

            entry = ttk.Entry(info_frame, font=('Segoe UI', 11), width=60)
            entry.insert(0, value_text)
            entry.config(state='readonly')
            entry.pack(anchor='w', padx=(20, 0), fill='x')

            # Handler de click -> selecciona y copia
            def on_click(event, widget=entry, val=value_text):
                widget.focus_set()
                widget.selection_range(0, 'end')
                info_window.clipboard_clear()
                info_window.clipboard_append(val)
                show_feedback()
                return "break"

            entry.bind('<Button-1>', on_click)

            # Espacio entre items
            ttk.Label(info_frame, text="").pack(pady=(0, 5))

        # Footer con nombre
        wp_label = ttk.Label(main_frame, text="wpinto", font=('Segoe UI', 12, 'bold'))
        wp_label.pack(pady=(0, 0))

        # Botón para cerrar
        btn_cerrar = ttk.Button(main_frame, text="Cerrar", command=info_window.destroy,
                            style="primary.TButton")
        btn_cerrar.pack(pady=(10, 5))

        # Enfocar la ventana
        info_window.focus_set()


    
    def mostrar_error_info(self, error_msg):
        """Muestra error al obtener información de la cuenta"""
        messagebox.showerror("Error", f"No se pudo obtener la información de la cuenta:\n\n{error_msg}")

    def crear_status_bar(self):
        self.status_bar = StatusBar(self.root)
    
    def cambiar_cuenta(self, event):
        cuenta = self.combo_cuentas.get()
        
        # Actualizar status bar al iniciar conexión
        self.status_bar.set_status("Conectando...", "warning", f"Cuenta: {cuenta}")

        def conectar():
            try:
                self.loading.show(f"Conectando a cuenta {cuenta}...")
                time.sleep(1)
                
                self.ec2_client = cliente.crear("ec2", cuenta)
                self.rds_client = cliente.crear("rds", cuenta)
                self.s3_client = cliente.crear("s3", cuenta)
                self.sts_client = cliente.crear("sts", cuenta)
                self.iam_client = cliente.crear("iam", cuenta)
                self.cuenta_actual = cuenta
                
                self.root.after(0, self.actualizar_despues_conexion, cuenta)
            except Exception as e:
                self.root.after(0, self.mostrar_error_conexion, cuenta, str(e))
            finally:
                self.root.after(0, self.loading.hide)
        
        threading.Thread(target=conectar, daemon=True).start()
    
    def actualizar_despues_conexion(self, cuenta):
        self.status_bar.set_status("Conectado by wpinto", "success", f"Cuenta: {cuenta}")
        
        # Habilitar el botón de información
        self.btn_info.configure(state="normal")
        
        # Limpiar cliente de logs para forzar recreación
        if hasattr(self, 'logs_insights_tab') and hasattr(self.logs_insights_tab, 'logs_client'):
            self.logs_insights_tab.logs_client = None
        
        # Limpiar cliente S3 en la tab para forzar recreación
        if hasattr(self, 's3_tab'):
            self.s3_tab.s3_client = None
        
        # Limpiar cache de información de cuenta para forzar actualización
        if self.cuenta_actual in self.info_cuentas_cache:
            del self.info_cuentas_cache[self.cuenta_actual]
            
        # Refrescar datos en las tabs
        if self.ec2_tab:
            self.ec2_tab.refrescar_ec2()
        if self.rds_tab:
            self.rds_tab.refrescar_rds()
        # Limpiar datos de Security Groups para forzar recarga
        if hasattr(self, 'sg_tab'):
            self.sg_tab.sg_data = []
            self.sg_tab.vpc_data = {}
        # La tab S3 no se refresca automáticamente, el usuario debe hacer click en "Actualizar Buckets"
        # Limpiar cliente VPC en la tab para forzar recreación
        if hasattr(self, 'vpc_tab'):
            self.vpc_tab.ec2_client = None

    def mostrar_error_conexion(self, cuenta, error):
        self.status_bar.set_status("Error de conexión", "danger", f"Cuenta: {cuenta}")
        # Deshabilitar el botón de información en caso de error
        self.btn_info.configure(state="disabled")
        # Limpiar clientes en caso de error
        self.sts_client = None
        self.iam_client = None
        messagebox.showerror("Error de conexión", f"No se pudo conectar con la cuenta {cuenta}\n\nError: {error}")
    
    def obtener_color_estado(self, estado):
        """Función utilitaria para obtener colores según el estado"""
        if estado in ("running", "available"):
            return "success"
        elif estado in ("stopped", "stopping"):
            return "danger"
        elif estado in ("pending", "starting"):
            return "warning"
        return "normal"
    
    def configurar_colores_tree(self, tree):
        """Función utilitaria para configurar colores en los TreeView"""
        tree.tag_configure("success", foreground="#28a745")
        tree.tag_configure("danger", foreground="#dc3545")
        tree.tag_configure("warning", foreground="#ffc107")
        tree.tag_configure("normal", foreground="white")

    def configurar_estilos_botones(self):    
        # Estilo para botones normales
        self.style.configure("Large.TButton", 
                            font=('Segoe UI', 11, 'bold'),  # Fuente más grande
                            padding=(10, 8))                # Padding interno (horizontal, vertical)
        
        # Estilos para botones con colores específicos
        self.style.configure("Large.primary.TButton", 
                            font=('Segoe UI', 11, 'bold'),
                            padding=(10, 8))
        
        self.style.configure("Large.success.TButton", 
                            font=('Segoe UI', 11, 'bold'),
                            padding=(10, 8))
        
        self.style.configure("Large.danger.TButton", 
                            font=('Segoe UI', 11, 'bold'),
                            padding=(10, 8))
        
        self.style.configure("Large.warning.TButton", 
                            font=('Segoe UI', 11, 'bold'),
                            padding=(10, 8))

def main():
    root = ttk.Window()
    app = AppAWS(root)
    root.mainloop()

if __name__ == "__main__":
    main()