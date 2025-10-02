import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

class StatusBar:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='x', side='bottom', padx=5, pady=5)
        
        connection_frame = ttk.Frame(self.frame)
        connection_frame.pack(side='left')
        
        self.connection_dot = ttk.Label(connection_frame, text="●", font=('Arial', 12), bootstyle="danger")
        self.connection_dot.pack(side='left')
        
        self.status_text = ttk.Label(connection_frame, text="Desconectado by wpinto")
        self.status_text.pack(side='left', padx=(5, 0))
        
        self.account_label = ttk.Label(self.frame, text="")
        self.account_label.pack(side='right')
    
    def set_status(self, status, color=None, account=""):
        """
        Actualiza el estado de la barra de estado.
        
        Args:
            status (str): Texto del estado
            color (str, optional): Color del punto. Puede ser un color tkinter tradicional 
                                  o un estilo de bootstrap
            account (str): Información de la cuenta
        """
        # Mapeo de colores tradicionales a estilos de bootstrap
        color_map = {
            # Colores tkinter tradicionales
            'red': 'danger',
            'green': 'success', 
            'orange': 'warning',
            'blue': 'info',
            'yellow': 'warning',
            # Códigos hex comunes
            '#ff0000': 'danger',
            '#00ff00': 'success',
            '#0000ff': 'info',
            '#ffa500': 'warning',
            # Estilos de bootstrap (por si ya los usan)
            'danger': 'danger',
            'success': 'success',
            'warning': 'warning',
            'info': 'info',
            'primary': 'primary',
            'secondary': 'secondary'
        }
        
        # Actualizar el texto del status
        self.status_text.configure(text=status)
        
        # Actualizar el color del punto si se proporciona
        if color:
            bootstrap_style = color_map.get(color.lower() if isinstance(color, str) else color, 'secondary')
            self.connection_dot.configure(bootstyle=bootstrap_style)
        
        # Actualizar la información de la cuenta
        if account:
            self.account_label.configure(text=account)
           
 
class LoadingIndicator:
    def __init__(self, parent):
        self.parent = parent
        self.loading_window = None
        self.is_loading = False
        
    def show(self, message="Cargando..."):
        if self.is_loading:
            return
        self.is_loading = True
        
        self.loading_window = ttk_bs.Toplevel(self.parent)
        self.loading_window.title("Procesando")
        self.loading_window.geometry("300x120")
        self.loading_window.resizable(False, False)
        self.loading_window.transient(self.parent)
        self.loading_window.grab_set()
        
        # Centrar ventana
        self.loading_window.geometry("+{}+{}".format(
            self.parent.winfo_rootx() + 50, self.parent.winfo_rooty() + 50))
        
        ttk_bs.Label(self.loading_window, text=message, font=('Arial', 10)).pack(pady=20)
        
        self.progress = ttk_bs.Progressbar(
            self.loading_window, 
            mode='indeterminate',
            bootstyle="info-striped"
        )
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start(10)
        
    def hide(self):
        if not self.is_loading:
            return
        self.is_loading = False
        if self.loading_window:
            self.progress.stop()
            self.loading_window.destroy()
            self.loading_window = None

class DetailWindow:
    def __init__(self, parent, title, data, resource_type):
        self.window = ttk_bs.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("720x650")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        self.parent = parent
        
        # Variables para el redimensionamiento de tags
        self.tags_frame_container = None
        self.current_tags_dict = {}
        
        # Centrar ventana respecto del padre
        self.window.geometry("+{}+{}".format(
            parent.winfo_rootx() + 100, parent.winfo_rooty() + 50))

        # Vincular evento de redimensionamiento
        self.window.bind('<Configure>', self._on_window_resize)
        
        self.create_content(data, resource_type)

    def _on_window_resize(self, event):
        """Maneja el redimensionamiento de la ventana para reajustar los tags"""
        # Solo procesar si es la ventana principal la que cambió de tamaño
        if event.widget == self.window and self.tags_frame_container:
            # Usar after para evitar llamadas excesivas durante el redimensionamiento
            if hasattr(self, '_resize_job'):
                self.window.after_cancel(self._resize_job)
            self._resize_job = self.window.after(100, self._rebuild_tags_layout)

    def _rebuild_tags_layout(self):
        """Reconstruye el layout de los tags basado en el ancho actual de la ventana"""
        if self.tags_frame_container and self.current_tags_dict:
            # Limpiar el contenido actual
            for widget in self.tags_frame_container.winfo_children():
                widget.destroy()
            
            # Recrear los tags con el nuevo layout
            self._create_tags_grid(self.tags_frame_container, self.current_tags_dict)

    def _create_context_menu(self, widget, value):
        """Crea un menú contextual para copiar el valor"""
        context_menu = tk.Menu(self.window, tearoff=0)
        context_menu.add_command(
            label="📋 Copiar", 
            command=lambda: self._copy_to_clipboard(value)
        )
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            except:
                pass
            finally:
                context_menu.grab_release()
        
        # Vincular botón derecho del mouse
        widget.bind("<Button-3>", show_context_menu)  # Windows/Linux
        widget.bind("<Button-2>", show_context_menu)  # Mac (middle click como alternativa)
        
        # También agregar Ctrl+C para copiar
        widget.bind("<Control-c>", lambda e: self._copy_to_clipboard(value))

    def _copy_to_clipboard(self, value):

        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(str(value))
            self.window.update() 
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo copiar al portapapeles: {str(e)}")

    def create_content(self, data, resource_type):
        # Frame del header
        header_frame = ttk_bs.Frame(self.window)
        header_frame.pack(fill='x', padx=10, pady=10)

        icon = "🖥️" if resource_type == "ec2" else "💾" 
        header_label = ttk_bs.Label(
            header_frame, 
            text=f"{icon} {data.get('name', data.get('id'))}",
            font=('Arial', 14, 'bold')
        )
        header_label.pack()

        # Frame principal con scroll
        main_frame = ttk_bs.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Canvas y scrollbar para el contenido scrolleable
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk_bs.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk_bs.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Crear el contenido según el tipo de recurso
        if resource_type == "ec2":
            self.create_ec2_details(scrollable_frame, data)
        else:
            self.create_rds_details(scrollable_frame, data)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel para scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def create_section(self, parent, title, items):
        # Frame principal de la sección
        section_frame = ttk_bs.LabelFrame(parent, text=title, padding=15)
        section_frame.pack(fill='x', pady=(0, 15))

        # Grid para los elementos
        for i, (key, value) in enumerate(items):
            # Label para la clave
            key_label = ttk_bs.Label(section_frame, text=f"{key}:", font=('Arial', 9, 'bold'))
            key_label.grid(row=i, column=0, sticky='w', pady=2, padx=(0, 10))

            # Entry para el valor (readonly)
            value_entry = ttk_bs.Entry(section_frame, font=('Arial', 9), width=50)
            value_entry.insert(0, str(value))
            value_entry.configure(state='readonly')
            value_entry.grid(row=i, column=1, sticky='ew', pady=2)
            
            # Configurar expansión de columna
            section_frame.grid_columnconfigure(1, weight=1)

            # Agregar menú contextual para copiar
            self._create_context_menu(value_entry, value)

            # Seleccionar texto al hacer clic
            value_entry.bind("<Button-1>", lambda event, e=value_entry: e.after(1, lambda: e.select_range(0, 'end')))

    def create_tags_section(self, parent, tags_data):
        """
        Crea una sección específica para mostrar los tags de manera más visual.
        Los tags se ajustarán automáticamente al ancho de la ventana.
        """
        # Frame principal de la sección de tags
        tags_frame = ttk_bs.LabelFrame(parent, text="🏷️ Tags", padding=15)
        tags_frame.pack(fill='both', expand=True, pady=(0, 15))

        # Verificar si hay tags
        if not tags_data or (isinstance(tags_data, (list, dict)) and len(tags_data) == 0):
            no_tags_label = ttk_bs.Label(
                tags_frame, 
                text="No hay tags configurados para este recurso",
                font=('Arial', 9, 'italic'),
                foreground='gray'
            )
            no_tags_label.pack(pady=10)
            return

        # Procesar los tags según su formato
        tags_dict = {}
        
        if isinstance(tags_data, dict):
            tags_dict = tags_data
        elif isinstance(tags_data, list):
            # Si es una lista de diccionarios con Key/Value
            if tags_data and isinstance(tags_data[0], dict):
                for tag in tags_data:
                    if 'Key' in tag and 'Value' in tag:
                        tags_dict[tag['Key']] = tag['Value']
                    elif 'key' in tag and 'value' in tag:
                        tags_dict[tag['key']] = tag['value']
            else:
                # Si es una lista de strings, mostrar como items numerados
                for i, tag in enumerate(tags_data):
                    tags_dict[f"Tag {i+1}"] = str(tag)
        elif isinstance(tags_data, str):
            # Si es un string, intentar parsearlo o mostrarlo tal como está
            tags_dict["Tags"] = tags_data

        # Guardar referencia para redimensionamiento
        self.current_tags_dict = tags_dict

        # Crear frame contenedor que se expandirá
        self.tags_frame_container = ttk_bs.Frame(tags_frame)
        self.tags_frame_container.pack(fill='both', expand=True)
        
        # Crear los tags inicialmente
        self._create_tags_grid(self.tags_frame_container, tags_dict)

    def _create_tags_grid(self, parent, tags_dict):
        """
        Crea la grilla de tags en el widget padre especificado.
        Calcula dinámicamente el número de columnas basado en el ancho disponible.
        """
        if not tags_dict:
            return
            
        # Calcular el número de columnas basado en el ancho de la ventana
        window_width = self.window.winfo_width()
        if window_width <= 1:  # Si aún no se ha renderizado, usar valor por defecto
            window_width = 720
        
        # Estimar ancho por tag (considerando padding, margins, etc.)
        tag_width = 280  # Ancho aproximado por tag
        available_width = window_width - 100  # Restar padding y scrollbar
        cols = max(1, min(3, available_width // tag_width))  # Entre 1 y 3 columnas
        
        row = 0
        col = 0
        
        for key, value in tags_dict.items():
            # Frame para cada tag individual con un estilo más visual
            tag_frame = ttk_bs.Frame(parent, relief='solid', borderwidth=1, padding=5)
            tag_frame.grid(row=row, column=col, sticky='ew', padx=3, pady=3)
            
            # Label para la clave del tag (más prominente)
            key_label = ttk_bs.Label(
                tag_frame, 
                text=str(key), 
                font=('Arial', 9, 'bold'),
                bootstyle="primary"
            )
            key_label.pack(anchor='w', padx=3, pady=(2, 0))
            
            # Entry para el valor del tag (readonly y más ancho)
            value_entry = ttk_bs.Entry(
                tag_frame, 
                font=('Arial', 8), 
                bootstyle="secondary"
            )
            value_entry.insert(0, str(value) if value else "")
            value_entry.configure(state='readonly')
            value_entry.pack(fill='x', padx=3, pady=(0, 2))
            
            # Agregar menú contextual para copiar
            tag_value = f"{key}: {value}" if value else str(key)
            self._create_context_menu(value_entry, tag_value)
            self._create_context_menu(key_label, tag_value)
            
            # Seleccionar texto al hacer clic
            value_entry.bind("<Button-1>", lambda event, e=value_entry: e.after(1, lambda: e.select_range(0, 'end')))
            
            # Actualizar posición en la grilla
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        # Configurar que las columnas se expandan uniformemente
        for i in range(cols):
            parent.grid_columnconfigure(i, weight=1)

    def create_ec2_details(self, parent, data):
        basic_info = [
            ("ID de Instancia", data.get('id', 'N/A')),
            ("Nombre", data.get('name', 'N/A')),
            ("Estado", data.get('state', 'N/A')),
            ("Tipo de Instancia", data.get('type', 'N/A')),
            ("Plataforma", data.get('platform', 'N/A')),
            ("Arquitectura", data.get('architecture', 'N/A')),
            ("Hipervisor", data.get('hypervisor', 'N/A'))
        ]
        self.create_section(parent, "📋 Información Básica", basic_info)

        network_info = [
            ("IP Privada", data.get('private_ip', 'N/A')),
            ("IP Pública", data.get('public_ip', 'N/A')),
            ("VPC ID", data.get('vpc_id', 'N/A')),
            ("Subnet ID", data.get('subnet_id', 'N/A')),
            ("Grupos de Seguridad", data.get('security_groups', 'N/A')),
            ("Zona de Disponibilidad", data.get('availability_zone', 'N/A'))
        ]
        self.create_section(parent, "🌐 Red y Conectividad", network_info)

        additional_info = [
            ("Fecha de Lanzamiento", data.get('launch_time', 'N/A')),
            ("Clave SSH", data.get('key_name', 'N/A')),
            ("Razón del Estado", data.get('state_reason', 'N/A'))
        ]
        self.create_section(parent, "⚙️ Configuración Adicional", additional_info)

        # Agregar sección de tags para EC2
        tags_data = data.get('tags', {})
        self.create_tags_section(parent, tags_data)

    def create_rds_details(self, parent, data):
        basic_info = [
            ("Identificador", data.get('id', 'N/A')),
            ("Nombre de BD", data.get('name', 'N/A')),
            ("Estado", data.get('state', 'N/A')),
            ("Motor", data.get('engine', 'N/A')),
            ("Clase de Instancia", data.get('class', 'N/A')),
            ("Fecha de Creación", data.get('creation_time', 'N/A'))
        ]
        self.create_section(parent, "📋 Información Básica", basic_info)

        storage_info = [
            ("Tipo de Almacenamiento", data.get('storage_type', 'N/A')),
            ("Almacenamiento Asignado (GB)", data.get('allocated_storage', 'N/A')),
            ("Almacenamiento Máximo (GB)", data.get('max_allocated_storage', 'N/A')),
            ("Retención de Backup (días)", data.get('backup_retention', 'N/A'))
        ]
        self.create_section(parent, "💾 Almacenamiento y Backup", storage_info)

        network_info = [
            ("Endpoint", data.get('endpoint', 'N/A')),
            ("Puerto", data.get('port', 'N/A')),
            ("Multi-AZ", data.get('multi_az', 'N/A')),
            ("Acceso Público", data.get('publicly_accessible', 'N/A')),
            ("Zona de Disponibilidad", data.get('availability_zone', 'N/A')),
            ("Grupos de Seguridad VPC", data.get('vpc_security_groups', 'N/A'))
        ]
        self.create_section(parent, "🌐 Red y Disponibilidad", network_info)

        # Agregar sección de tags para RDS
        tags_data = data.get('tags', {})
        self.create_tags_section(parent, tags_data)