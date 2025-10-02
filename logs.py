import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
import json
import csv
from datetime import datetime, timedelta
import cliente as cliente



class LogsInsightsTab:
    def __init__(self, parent_frame, parent_app):
        self.parent_frame = parent_frame
        self.parent_app = parent_app
        self.logs_client = None
        self.ec2_client = None
        self.current_results = []
        self.parsed_results = []
        self.query_history = []
        
        # Mapeo de protocolos
        self.protocol_map = {
            '1': 'ICMP',
            '6': 'TCP', 
            '17': 'UDP',
            '41': 'IPv6',
            '47': 'GRE',
            '50': 'ESP',
            '51': 'AH',
            '58': 'ICMPv6'
        }
        
        # Mapeo de acciones
        self.action_map = {
            'ACCEPT': 'ACCEPT',
            'REJECT': 'REJECT'
        }
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        # Crear canvas y scrollbar para toda la interfaz
        self.canvas = tk.Canvas(self.parent_frame)
        self.scrollbar = ttk.Scrollbar(self.parent_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind para ajustar el ancho del frame al canvas
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Configurar grid
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configurar pesos para redimensionamiento
        self.parent_frame.grid_rowconfigure(0, weight=1)
        self.parent_frame.grid_columnconfigure(0, weight=1)
        
        # Bind para scroll con mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # Sección de configuración
        self.crear_seccion_configuracion(self.scrollable_frame)
        
        # Sección de query
        self.crear_seccion_query(self.scrollable_frame)
        
        # Sección de resultados
        self.crear_seccion_resultados(self.scrollable_frame)

    #scroll del mouse
    def _on_mousewheel(self, event):
        """Maneja el scroll con la rueda del mouse"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")   
    #Configurar el ancho del frame scrollable al ancho del canvas
    def _on_canvas_configure(self, event):
        """Ajusta el ancho del frame scrollable al ancho del canvas"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def crear_seccion_configuracion(self, parent):
        config_frame = ttk.LabelFrame(parent, text="🔧 Configuración", padding=10)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        # Row 1: Log Group y botón actualizar
        row1 = ttk.Frame(config_frame)
        row1.pack(fill='x', pady=5)
        
        ttk.Label(row1, text="Log Group:").pack(side='left')
        self.log_group_var = tk.StringVar()
        self.combo_log_groups = ttk.Combobox(row1, textvariable=self.log_group_var, 
                                           font=('Segoe UI', 10), width=120)
        self.combo_log_groups.pack(side='left', padx=(5, 10))
        
        ttk.Button(row1, text="🔄 Actualizar Log Groups", 
                  command=self.actualizar_log_groups,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        
        # Row 2: Rango de tiempo
        row2 = ttk.Frame(config_frame)
        row2.pack(fill='x', pady=5)
        
        ttk.Label(row2, text="Rango de tiempo:").pack(side='left')
        
        self.time_range_var = tk.StringVar(value="1h")
        time_ranges = [
            ("Última hora", "1h"),
            ("Últimas 6 horas", "6h"), 
            ("Último día", "1d"),
            ("Últimos 7 días", "7d"),
            ("Personalizado", "custom")
        ]
        
        for text, value in time_ranges:
            ttk.Radiobutton(row2, text=text, variable=self.time_range_var, 
                           value=value).pack(side='left', padx=5)
        
        # Row 3: Fechas personalizadas (inicialmente ocultas)
        self.custom_time_frame = ttk.Frame(config_frame)
        
        ttk.Label(self.custom_time_frame, text="Desde:").pack(side='left')
        self.start_time_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        ttk.Entry(self.custom_time_frame, textvariable=self.start_time_var, 
                 font=('Segoe UI', 10), width=16).pack(side='left', padx=2)
        
        ttk.Label(self.custom_time_frame, text="Hasta:").pack(side='left', padx=(10, 0))
        self.end_time_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d %H:%M"))
        ttk.Entry(self.custom_time_frame, textvariable=self.end_time_var, 
                 font=('Segoe UI', 10), width=16).pack(side='left', padx=2)
        
        # Bind para mostrar/ocultar fechas personalizadas
        self.time_range_var.trace('w', self.toggle_custom_time)
    
    def crear_seccion_query(self, parent):
        query_frame = ttk.LabelFrame(parent, text="📝 Query", padding=10)
        query_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Container principal para dividir en dos columnas
        main_container = ttk.Frame(query_frame)
        main_container.pack(fill='both', expand=True)
        
        # Configurar grid para dos columnas iguales
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # PARTE IZQUIERDA: Editor de Query
        self.crear_editor_query(main_container)
        
        # PARTE DERECHA: Asistente de Query
        self.crear_asistente_query(main_container)
    
    def crear_editor_query(self, parent):
        # Frame izquierdo para el editor
        editor_frame = ttk.LabelFrame(parent, text="✏️ Editor de Query", padding=10)
        editor_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Toolbar
        toolbar = ttk.Frame(editor_frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        ttk.Button(toolbar, text="🗑️ Limpiar", 
                  command=self.limpiar_query,
                  style="Large.TButton").pack(side='left', padx=2)
        
        # Botones de acción
        action_frame = ttk.Frame(toolbar)
        action_frame.pack(side='right')
        
        ttk.Button(action_frame, text="▶️ Ejecutar Query", 
                  command=self.ejecutar_query,
                  style="Large.success.TButton").pack(side='left', padx=2)
        
        ttk.Button(action_frame, text="💾 Exportar Resultados", 
                  command=self.exportar_resultados,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        
        # Editor de query
        query_editor_frame = ttk.Frame(editor_frame)
        query_editor_frame.pack(fill='both', expand=True)
        
        self.query_text = tk.Text(query_editor_frame, height=12, font=('Consolas', 11),
                                 wrap='none', bg='#2b2b2b', fg='white',
                                 insertbackground='white')
        
        # Scrollbars para el editor
        query_v_scroll = ttk.Scrollbar(query_editor_frame, orient="vertical", 
                                      command=self.query_text.yview)
        query_h_scroll = ttk.Scrollbar(query_editor_frame, orient="horizontal", 
                                      command=self.query_text.xview)
        
        self.query_text.configure(yscrollcommand=query_v_scroll.set,
                                 xscrollcommand=query_h_scroll.set)
        
        # Grid para editor y scrollbars
        self.query_text.grid(row=0, column=0, sticky="nsew")
        query_v_scroll.grid(row=0, column=1, sticky="ns")
        query_h_scroll.grid(row=1, column=0, sticky="ew")
        
        query_editor_frame.grid_rowconfigure(0, weight=1)
        query_editor_frame.grid_columnconfigure(0, weight=1)
        
        # Query de ejemplo modificada para incluir @timestamp y @message
        ejemplo_query = """fields @timestamp, @message
| filter  (  action="ACCEPT" and (srcAddr = '10.103.128.91' and dstAddr = '10.99.166.77' ) and (dstPort != '443' and dstPort != '135') )
| sort @timestamp desc
| limit 100"""
        
        self.query_text.insert('1.0', ejemplo_query)
    
# ... (el resto del archivo permanece igual hasta llegar a crear_asistente_query)

    def crear_asistente_query(self, parent):
        # Frame derecho para el asistente
        assistant_frame = ttk.LabelFrame(parent, text="🔧 Asistente de Query", padding=10)
        assistant_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Variables para los campos del asistente
        self.ip_origen_var = tk.StringVar()
        self.ip_destino_var = tk.StringVar()
        self.puerto_destino_var = tk.StringVar()
        self.puerto_distinto_var = tk.BooleanVar()
        self.accion_var = tk.StringVar(value="TODAS")

        # Frame principal con 2 columnas
        grid_frame = ttk.Frame(assistant_frame)
        grid_frame.pack(fill='both', expand=True)

        # IP Origen
        ip_origen_frame = ttk.LabelFrame(grid_frame, text="🌐 IP Origen", padding=10)
        ip_origen_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ttk.Entry(ip_origen_frame, textvariable=self.ip_origen_var, font=('Segoe UI', 10)).pack(fill='x', pady=2)
        ttk.Label(ip_origen_frame, text="Ejemplo: 10.103.128.91 o 10.1.1.1,10.2.2.2", font=('Segoe UI', 8), foreground='gray').pack(anchor='w')

        # IP Destino
        ip_destino_frame = ttk.LabelFrame(grid_frame, text="🎯 IP Destino", padding=10)
        ip_destino_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ttk.Entry(ip_destino_frame, textvariable=self.ip_destino_var, font=('Segoe UI', 10)).pack(fill='x', pady=2)
        ttk.Label(ip_destino_frame, text="Ejemplo: 10.99.166.77 o 10.3.3.3,10.4.4.4", font=('Segoe UI', 8), foreground='gray').pack(anchor='w')

        # Puerto Destino
        puerto_frame = ttk.LabelFrame(grid_frame, text="🔌 Puerto Destino", padding=10)
        puerto_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        ttk.Checkbutton(puerto_frame, text="Excluir puerto (!=)", variable=self.puerto_distinto_var).pack(anchor='w')
        ttk.Entry(puerto_frame, textvariable=self.puerto_destino_var, font=('Segoe UI', 10)).pack(fill='x', pady=2)
        ttk.Label(puerto_frame, text="Ejemplo: 443 o 443,135 (múltiples)", font=('Segoe UI', 8), foreground='gray').pack(anchor='w')

        # Acción
        accion_frame = ttk.LabelFrame(grid_frame, text="⚡ Acción", padding=10)
        accion_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        acciones = [("Todas", "TODAS"), ("Permitir (ACCEPT)", "ACCEPT"), ("Rechazar (REJECT)", "REJECT")]
        for text, value in acciones:
            ttk.Radiobutton(accion_frame, text=text, variable=self.accion_var, value=value).pack(anchor='w')

        # Límite de resultados
        limite_frame = ttk.LabelFrame(grid_frame, text="📊 Configuración", padding=10)
        limite_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.limite_var = tk.StringVar(value="100")
        ttk.Label(limite_frame, text="Límite de resultados:").pack(anchor='w')
        ttk.Combobox(limite_frame, textvariable=self.limite_var, values=["50", "100", "500", "1000"],
                     font=('Segoe UI', 10), width=10).pack(anchor='w', pady=2)

        # Botones
        buttons_frame = ttk.Frame(grid_frame)
        buttons_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        ttk.Button(buttons_frame, text="🔄 Generar Query", command=self.generar_query_desde_asistente,
                   style="Large.success.TButton").pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="🗑️ Limpiar Campos", command=self.limpiar_asistente,
                   style="Large.warning.TButton").pack(fill='x', pady=2)

        # Expandir columnas equitativamente
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)

    
    def generar_query_desde_asistente(self):
        """Genera la query basada en los campos del asistente"""
        try:
            # Construir filtros
            filtros = []
            
            # Filtro de acción
            if self.accion_var.get() != "TODAS":
                filtros.append(f'action="{self.accion_var.get()}"')
            
            # Filtros de IP
            ip_filtros = []

            # Procesar IPs de origen (múltiples IPs separadas por comas)
            if self.ip_origen_var.get().strip():
                ips_origen = [ip.strip() for ip in self.ip_origen_var.get().split(',')]
                if len(ips_origen) == 1:
                    ip_filtros.append(f"srcAddr = '{ips_origen[0]}'")
                else:
                    # Múltiples IPs origen con OR
                    ip_origen_conditions = [f"srcAddr = '{ip}'" for ip in ips_origen]
                    ip_filtros.append(f"({' or '.join(ip_origen_conditions)})")

            # Procesar IPs de destino (múltiples IPs separadas por comas)
            if self.ip_destino_var.get().strip():
                ips_destino = [ip.strip() for ip in self.ip_destino_var.get().split(',')]
                if len(ips_destino) == 1:
                    ip_filtros.append(f"dstAddr = '{ips_destino[0]}'")
                else:
                    # Múltiples IPs destino con OR
                    ip_destino_conditions = [f"dstAddr = '{ip}'" for ip in ips_destino]
                    ip_filtros.append(f"({' or '.join(ip_destino_conditions)})")

            if ip_filtros:
                filtros.append(f"({' and '.join(ip_filtros)})")
            
            # Filtro de puerto destino
            if self.puerto_destino_var.get().strip():
                puertos = [p.strip() for p in self.puerto_destino_var.get().split(',')]
                operador = "!=" if self.puerto_distinto_var.get() else "="
                
                if len(puertos) == 1:
                    filtros.append(f"dstPort {operador} '{puertos[0]}'")
                else:
                    # Múltiples puertos
                    puerto_conditions = [f"dstPort {operador} '{p}'" for p in puertos]
                    if operador == "!=":
                        # Para != usamos AND (no debe ser ninguno de estos puertos)
                        filtros.append(f"({' and '.join(puerto_conditions)})")
                    else:
                        # Para = usamos OR (puede ser cualquiera de estos puertos)
                        filtros.append(f"({' or '.join(puerto_conditions)})")
            
            # Construir query completa
            query_parts = ["fields @timestamp, @message"]
            
            if filtros:
                filter_clause = f"| filter {' and '.join(filtros)}"
                query_parts.append(filter_clause)
            
            query_parts.append("| sort @timestamp desc")
            query_parts.append(f"| limit {self.limite_var.get()}")
            
            query_completa = '\n'.join(query_parts)
            
            # Insertar en el editor
            self.query_text.delete('1.0', tk.END)
            self.query_text.insert('1.0', query_completa)
            
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la query: {str(e)}")
    
    def limpiar_asistente(self):
        """Limpia todos los campos del asistente"""
        self.ip_origen_var.set("")
        self.ip_destino_var.set("")
        self.puerto_destino_var.set("")
        self.puerto_distinto_var.set(False)
        self.accion_var.set("TODAS")
        self.limite_var.set("100")
    
    def crear_seccion_resultados(self, parent):
        results_frame = ttk.LabelFrame(parent, text="📊 Resultados", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Info header
        info_frame = ttk.Frame(results_frame)
        info_frame.pack(fill='x', pady=(0, 10))
        
        self.results_info = ttk.Label(info_frame, text="No hay resultados", 
                                     font=('Segoe UI', 10))
        self.results_info.pack(side='left')
        
        self.query_status = ttk.Label(info_frame, text="", 
                                     font=('Segoe UI', 10))
        self.query_status.pack(side='right')
        
        # Tabla de resultados
        self.results_frame = ttk.Frame(results_frame)
        self.results_frame.pack(fill='both', expand=True)
        
        # Crear tabla inicial vacía
        self.crear_tabla_resultados([])
    
    def toggle_custom_time(self, *args):
        if self.time_range_var.get() == "custom":
            self.custom_time_frame.pack(fill='x', pady=5)
        else:
            self.custom_time_frame.pack_forget()
    
    def actualizar_log_groups(self):
        if not self.parent_app.cuenta_actual:
            messagebox.showwarning("Sin conexión", "Primero selecciona una cuenta AWS")
            return
        
        def cargar_log_groups():
            try:
                self.parent_app.loading.show("Cargando Log Groups...")
                
                # Crear cliente de logs si no existe #Probar este cambio!!!!!!!!!!
                if not self.logs_client or getattr(self, 'cuenta_anterior', None) != self.parent_app.cuenta_actual:
                    self.logs_client = cliente.crear("logs", self.parent_app.cuenta_actual)
                    self.cuenta_anterior = self.parent_app.cuenta_actual
                
                # Obtener log groups (filtrar por AWSAccelerator-NetworkVpcStack)
                response = self.logs_client.describe_log_groups()
                log_groups = []
                
                for lg in response['logGroups']:
                    name = lg['logGroupName']
                    # Filtrar solo log groups que comienzan con "AWSAccelerator-NetworkVpcStack"
                    if name.startswith('AWSAccelerator-NetworkVpcStack'):
                        log_groups.append(name)
                
                self.parent_app.root.after(0, self.actualizar_combo_log_groups, log_groups)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error al cargar Log Groups: {str(e)}"))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=cargar_log_groups, daemon=True).start()
    
    def actualizar_combo_log_groups(self, log_groups):
        self.combo_log_groups['values'] = log_groups
        if log_groups:
            self.combo_log_groups.set(log_groups[0])
        self.parent_app.status_bar.set_status("Log Groups cargados", "success", 
                                            f"Encontrados: {len(log_groups)}")
    
    def limpiar_query(self):
        self.query_text.delete('1.0', tk.END)
    
    def parse_vpc_flow_log(self, message):
        """
        Parsea un mensaje de VPC Flow Log y extrae los campos individuales
        Formato esperado: version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes windowstart windowend action flowlogstatus
        """
        try:
            # Dividir el mensaje por espacios
            parts = message.strip().split()
            
            if len(parts) < 14:
                return None
            
            # Mapear los campos según la especificación de VPC Flow Logs
            parsed = {
                'Account ID': parts[1],
                'Interface ID': parts[2],
                'IP Origen': parts[3],
                'IP Destino': parts[4],
                'Puerto Origen': parts[5],
                'Puerto Destino': parts[6],
                'Protocolo': self.protocol_map.get(parts[7], f'Protocolo {parts[7]}'),
                'Paquetes': parts[8],
                'Bytes': parts[9],
                'Fecha y Hora': self.format_timestamp(parts[10]),
                'Acción': self.action_map.get(parts[12], parts[12])
            }
            
            return parsed
            
        except Exception as e:
            print(f"Error parseando mensaje: {e}")
            return None
    
    def format_timestamp(self, timestamp_str):
        """Convierte timestamp Unix a formato legible"""
        try:
            timestamp = int(timestamp_str)
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return timestamp_str
    
    def ejecutar_query(self):
        if not self.logs_client:
            messagebox.showwarning("Sin conexión", "Primero actualiza los Log Groups")
            return
        
        log_group = self.log_group_var.get()
        query = self.query_text.get('1.0', tk.END).strip()
        
        if not log_group or not query:
            messagebox.showwarning("Datos incompletos", "Selecciona un Log Group y escribe una query")
            return
        
        def ejecutar():
            try:
                self.parent_app.loading.show("Ejecutando query...")
                
                # Calcular rango de tiempo
                start_time, end_time = self.calcular_rango_tiempo()
                
                # Iniciar query
                response = self.logs_client.start_query(
                    logGroupName=log_group,
                    startTime=int(start_time.timestamp()),
                    endTime=int(end_time.timestamp()),
                    queryString=query
                )
                
                query_id = response['queryId']
                
                # Esperar resultados
                max_wait = 60  # máximo 60 segundos
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    
                    result = self.logs_client.get_query_results(queryId=query_id)
                    status = result['status']
                    
                    self.parent_app.root.after(0, self.actualizar_status_query, 
                                             f"Estado: {status} ({wait_time}s)")
                    
                    if status == 'Complete':
                        results = result['results']
                        self.parent_app.root.after(0, self.mostrar_resultados, results, query)
                        return
                    elif status == 'Failed':
                        raise Exception("La query falló")
                
                # Timeout
                raise Exception("Timeout: La query tardó más de 60 segundos")
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error ejecutando query: {str(e)}"))
                self.parent_app.root.after(0, self.actualizar_status_query, "Error")
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=ejecutar, daemon=True).start()
    
    def calcular_rango_tiempo(self):
        time_range = self.time_range_var.get()
        end_time = datetime.now()
        
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "1d":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "custom":
            try:
                start_time = datetime.strptime(self.start_time_var.get(), "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(self.end_time_var.get(), "%Y-%m-%d %H:%M")
            except ValueError:
                raise Exception("Formato de fecha inválido. Use: YYYY-MM-DD HH:MM")
        
        return start_time, end_time
    
    def actualizar_status_query(self, status):
        self.query_status.config(text=status)
    
    def mostrar_resultados(self, results, query):
        self.current_results = results
        
        # Parsear los resultados para extraer y formatear los campos del message
        self.parsed_results = []
        
        for row in results:
            parsed_row = {}

            message_raw = None
            
            # Extraer timestamp y message de los resultados
            for field in row:
                field_name = field.get('field', '')
                field_value = field.get('value', '')
                

                if field_name == '@message':
                    message_raw = field_value
            
            # Parsear el message si existe
            if message_raw:
                parsed_message = self.parse_vpc_flow_log(message_raw)
                if parsed_message:
                    parsed_row.update(parsed_message)
                else:
                    # Si no se puede parsear, mostrar el mensaje completo
                    parsed_row['Mensaje'] = message_raw
            
            if parsed_row:
                self.parsed_results.append(parsed_row)
        
        # Agregar a historial
        self.query_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'query': query,
            'results_count': len(self.parsed_results)
        })
        
        # Actualizar info
        self.results_info.config(text=f"{len(self.parsed_results)} resultados encontrados")
        self.query_status.config(text="Completado")
        
        # Crear tabla
        self.crear_tabla_resultados_parseados()
        
        self.parent_app.status_bar.set_status("Query completada", "success", 
                                            f"Resultados: {len(self.parsed_results)}")
    
    def crear_tabla_resultados_parseados(self):
        """Crea la tabla de resultados con los datos parseados"""
        # Limpiar frame anterior
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not self.parsed_results:
            ttk.Label(self.results_frame, text="No hay resultados para mostrar",
                     font=('Segoe UI', 12)).pack(pady=20)
            return
        
        columns = [
            'Fecha y Hora',
            'IP Origen',
            'IP Destino',
            'Puerto Origen',
            'Puerto Destino',
            'Protocolo',
            'Paquetes',
            'Bytes',
            'Acción',
            'Account ID',
            'Interface ID'
        ]

        # Crear frame contenedor con scrollbars
        tree_frame = ttk.Frame(self.results_frame)
        tree_frame.pack(fill='both', expand=True)
        
        # Crear Treeview
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                        selectmode="extended", height=15)
        
        # Scrollbars vertical y horizontal
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.bind('<Control-c>', self._copy_selection)

        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Configurar columnas con anchos apropiados
        column_widths = {
            'Fecha y Hora': 200,
            'IP Origen': 120,
            'IP Destino': 120,
            'Puerto Origen': 100,
            'Puerto Destino': 100,
            'Protocolo': 80,
            'Acción': 80,
            'Paquetes': 80,
            'Bytes': 80,
            'Account ID': 150,
            'Interface ID': 180,

        }
        
        for col in columns:
            tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            tree.column(col, width=width, anchor="w", minwidth=50)
        
        # Insertar datos
        for row in self.parsed_results:
            values = []
            for col in columns:
                values.append(row.get(col, ''))
            tree.insert("", "end", values=values)
        
        # Posicionar elementos usando grid para mejor control
        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        # Configurar pesos para redimensionamiento
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind para click derecho (menú contextual opcional)
        tree.bind('<Button-3>', self._show_context_menu)

        # Bind para doble click (seleccionar celda)
        tree.bind('<Double-1>', self._select_cell)

        self.results_tree = tree
    
    def crear_tabla_resultados(self, results):
        """Método legacy mantenido para compatibilidad"""
        self.crear_tabla_resultados_parseados()

    def _copy_selection(self, event):
        """Copia la celda seleccionada al clipboard"""
        try:
            tree = event.widget
            
            # Obtener la posición del mouse
            x = tree.winfo_pointerx() - tree.winfo_rootx()
            y = tree.winfo_pointery() - tree.winfo_rooty()
            
            # Identificar la celda bajo el cursor
            item = tree.identify_row(y)
            column = tree.identify_column(x)
            
            if not item or not column:
                # Si no hay celda específica, copiar la fila completa
                selected_items = tree.selection()
                if not selected_items:
                    return
                
                # Copiar todas las filas seleccionadas
                copy_content = []
                for selected_item in selected_items:
                    values = tree.item(selected_item)['values']
                    copy_content.append('\t'.join(str(v) for v in values))
                
                clipboard_text = '\n'.join(copy_content)
                self.parent_frame.clipboard_clear()
                self.parent_frame.clipboard_append(clipboard_text)
                
                self.parent_app.status_bar.set_status("Copiado al clipboard", "success", 
                                                    f"{len(selected_items)} filas copiadas")
                return
            
            # Obtener el valor de la celda específica
            column_index = int(column.replace('#', '')) - 1
            values = tree.item(item)['values']
            
            if 0 <= column_index < len(values):
                cell_value = str(values[column_index])
                
                # Copiar al clipboard
                self.parent_frame.clipboard_clear()
                self.parent_frame.clipboard_append(cell_value)
                
                # Obtener nombre de la columna para feedback
                column_name = tree.heading(column)['text']
                self.parent_app.status_bar.set_status("Celda copiada", "success", 
                                                    f"{column_name}: {cell_value[:50]}{'...' if len(cell_value) > 50 else ''}")
            
        except Exception as e:
            print(f"Error al copiar: {e}")

    def exportar_resultados(self):
        if not self.parsed_results:
            messagebox.showwarning("Sin datos", "No hay resultados para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.parsed_results, f, indent=2, ensure_ascii=False)
            else:
                # Exportar como CSV
                if self.parsed_results:
                    # Obtener todas las columnas
                    all_columns = set()
                    for row in self.parsed_results:
                        all_columns.update(row.keys())
                    
                    columns = list(all_columns)
                    if 'Fecha y Hora' in columns:
                        columns.remove('Fecha y Hora')
                        columns.insert(0, 'Fecha y Hora')
                    
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        
                        for row in self.parsed_results:
                            values = [row.get(col, '') for col in columns]
                            writer.writerow(values)
            
            messagebox.showinfo("Export completo", f"Datos exportados a {filename}")
            
        except Exception as e:
            messagebox.showerror("Error de exportación", f"Error al exportar: {str(e)}")

    def _select_cell(self, event):
        """Selecciona una celda específica al hacer doble click"""
        tree = event.widget
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        
        if item and column:
            # Seleccionar la fila
            tree.selection_set(item)
            tree.focus(item)

    def _show_context_menu(self, event):
        """Muestra menú contextual con opción de copiar"""
        try:
            tree = event.widget
            item = tree.identify_row(event.y)
            
            if item:
                # Crear menú contextual
                context_menu = tk.Menu(tree, tearoff=0)
                context_menu.add_command(label="Copiar celda (Ctrl+C)", 
                                    command=lambda: self._copy_selection(event))
                context_menu.add_separator()
                context_menu.add_command(label="Copiar fila completa", 
                                    command=lambda: self._copy_full_row(tree, item))
                
                # Mostrar menú
                context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error en menú contextual: {e}")

    def _copy_full_row(self, tree, item):
        """Copia una fila completa"""
        values = tree.item(item)['values']
        clipboard_text = '\t'.join(str(v) for v in values)
        
        self.parent_frame.clipboard_clear()
        self.parent_frame.clipboard_append(clipboard_text)
        
        self.parent_app.status_bar.set_status("Fila copiada", "success", "Fila completa copiada")