import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import threading
import time
import os
from datetime import datetime
import cliente as cliente
from botocore.exceptions import ClientError


class S3Tab:
    def __init__(self, parent_frame, parent_app):
        self.parent_frame = parent_frame
        self.parent_app = parent_app
        self.s3_client = None
        self.current_bucket = None
        self.current_prefix = ""
        self.buckets_list = []
        self.objects_list = []
        self.crear_interfaz()
    
    def crear_interfaz(self):
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.crear_seccion_controles(main_container)
        ttk.Separator(main_container, orient='horizontal').pack(fill='x', pady=10)
        self.crear_seccion_navegacion(main_container)
    
    def crear_seccion_controles(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="🪣 Control de Buckets", padding=10)
        controls_frame.pack(fill='x', pady=(0, 10))
        
        row1 = ttk.Frame(controls_frame)
        row1.pack(fill='x', pady=5)
        
        # Selección de bucket
        bucket_frame = ttk.Frame(row1)
        bucket_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(bucket_frame, text="Bucket:").pack(side='left')
        self.bucket_var = tk.StringVar()
        self.combo_buckets = ttk.Combobox(bucket_frame, textvariable=self.bucket_var, 
                                         font=('Segoe UI', 10), width=40, state="readonly")
        self.combo_buckets.pack(side='left', padx=(5, 10), fill='x', expand=True)
        self.combo_buckets.bind("<<ComboboxSelected>>", self.cambiar_bucket)
        
        # Botones principales
        buttons_frame = ttk.Frame(row1)
        buttons_frame.pack(side='right')
        
        ttk.Button(buttons_frame, text="Actualizar", 
                  command=self.actualizar_buckets,
                  style="Large.primary.TButton").pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="Crear Bucket", 
                  command=self.crear_bucket,
                  style="Large.success.TButton").pack(side='left', padx=2)
        
        ttk.Button(buttons_frame, text="Eliminar Bucket", 
                  command=self.eliminar_bucket,
                  style="Large.danger.TButton").pack(side='left', padx=2)
    
    def crear_seccion_navegacion(self, parent):
        nav_frame = ttk.LabelFrame(parent, text="📁 Explorador de Archivos", padding=10)
        nav_frame.pack(fill='both', expand=True)
        
        # Barra de navegación
        nav_bar = ttk.Frame(nav_frame)
        nav_bar.pack(fill='x', pady=(0, 10))
        
        path_frame = ttk.Frame(nav_bar)
        path_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(path_frame, text="Ruta:").pack(side='left')
        self.path_var = tk.StringVar(value="/")
        self.path_label = ttk.Label(path_frame, textvariable=self.path_var, 
                                   font=('Segoe UI', 10, 'bold'), foreground='blue')
        self.path_label.pack(side='left', padx=(5, 0))
        
        nav_buttons = ttk.Frame(nav_bar)
        nav_buttons.pack(side='right')
        
        ttk.Button(nav_buttons, text="Raíz", command=self.ir_a_raiz, style="Large.primary.TButton").pack(fill='x', side='left', padx=2)
        ttk.Button(nav_buttons, text="Subir", command=self.subir_nivel, style="Large.primary.TButton").pack(fill='x', side='left', padx=2)
        ttk.Button(nav_buttons, text="Refrescar", command=self.refrescar_contenido, style="Large.primary.TButton").pack(fill='x', side='left', padx=2)
        
        # Frame principal con dos paneles
        content_frame = ttk.Frame(nav_frame)
        content_frame.pack(fill='both', expand=True, pady=10)
        
        # Panel de archivos
        files_frame = ttk.Frame(content_frame)
        files_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        columns = ('Nombre', 'Tipo', 'Tamaño', 'Fecha Modificación')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", 
                                      selectmode="extended", height=20)
        
        column_widths = {'Nombre': 400, 'Tipo': 80, 'Tamaño': 120, 'Fecha Modificación': 180}
        
        for col in columns:
            self.files_tree.heading(col, text=col)
            width = column_widths.get(col, 100)
            self.files_tree.column(col, width=width, anchor="w", minwidth=50)
        
        v_scroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        h_scroll = ttk.Scrollbar(files_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        files_frame.grid_rowconfigure(0, weight=1)
        files_frame.grid_columnconfigure(0, weight=1)
        
        self.files_tree.bind('<Double-1>', self.on_item_double_click)
        self.files_tree.bind('<Button-3>', self.show_context_menu)
        
        # Panel de acciones
        actions_frame = ttk.LabelFrame(content_frame, text="Acciones", padding=10)
        actions_frame.pack(side='right', fill='y')
        
        ttk.Button(actions_frame, text="Crear Carpeta", command=self.crear_carpeta,
                  style="Large.success.TButton").pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="Subir Archivo", command=self.subir_archivo,
                  style="Large.primary.TButton").pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="Descargar", command=self.descargar_archivo,
                  style="Large.success.TButton").pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="Eliminar", command=self.eliminar_archivo,
                  style="Large.danger.TButton").pack(fill='x', pady=2)
        
        ttk.Button(actions_frame, text="Copiar URL", command=self.copiar_url,
                  style="Large.TButton").pack(fill='x', pady=2)
        
        # Panel de información
        info_frame = ttk.LabelFrame(actions_frame, text="Información", padding=10)
        info_frame.pack(fill='x', expand=True, pady=(10, 0))
        
        self.info_text = tk.Text(info_frame, height=8, width=30, wrap=tk.WORD,
                                font=('Segoe UI', 9), bg='#f5f5f5')
        self.info_text.pack(fill='both', expand=True)
    
    def actualizar_buckets(self):
        if not self.parent_app.cuenta_actual:
            messagebox.showwarning("Sin conexión", "Selecciona una cuenta AWS primero")
            return
        
        def cargar_buckets():
            try:
                self.parent_app.loading.show("Cargando buckets...")
                
                if not self.s3_client:
                    self.s3_client = cliente.crear("s3", self.parent_app.cuenta_actual)
                
                response = self.s3_client.list_buckets()
                self.buckets_list = [bucket['Name'] for bucket in response['Buckets']]
                
                self.parent_app.root.after(0, self.actualizar_combo_buckets)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=cargar_buckets, daemon=True).start()
    
    def show_context_menu(self, event):
        try:
            item = self.files_tree.identify_row(event.y)
            if item:
                self.files_tree.selection_set(item)
                values = self.files_tree.item(item)['values']
                is_folder = values[1] == "Carpeta"
                
                context_menu = tk.Menu(self.parent_frame, tearoff=0)
                
                if is_folder:
                    context_menu.add_command(label="Abrir", command=lambda: self.on_item_double_click(event))
                    context_menu.add_command(label="Eliminar", command=self.eliminar_archivo)
                else:
                    context_menu.add_command(label="Descargar", command=self.descargar_archivo)
                    context_menu.add_command(label="Copiar URL", command=self.copiar_url)
                    context_menu.add_command(label="Eliminar", command=self.eliminar_archivo)
                
                context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error en menú contextual: {e}")

    
    def actualizar_combo_buckets(self):
        self.combo_buckets['values'] = self.buckets_list
        if self.buckets_list:
            self.combo_buckets.set(self.buckets_list[0])
            self.current_bucket = self.buckets_list[0]
            #self.refrescar_contenido()
    
    def cambiar_bucket(self, event):
        self.current_bucket = self.bucket_var.get()
        self.current_prefix = ""
        self.path_var.set("/")
        self.refrescar_contenido()
    
    def refrescar_contenido(self):
        if not self.current_bucket:
            return
        
        def cargar_objetos():
            try:
                self.parent_app.loading.show("Cargando contenido...")
                
                # Verificar que el cliente S3 esté disponible
                if not self.s3_client:
                    self.s3_client = cliente.crear("s3", self.parent_app.cuenta_actual)
                
                paginator = self.s3_client.get_paginator('list_objects_v2')
                
                # Configurar parámetros para la paginación
                params = {
                    'Bucket': self.current_bucket,
                    'Prefix': self.current_prefix,
                    'Delimiter': '/'
                }
                
                # Usar MaxItems para limitar la primera carga y evitar timeouts
                page_iterator = paginator.paginate(**params, PaginationConfig={'MaxItems': 1000})
                
                objects = []
                folders = []
                
                try:
                    for page in page_iterator:
                        # Procesar carpetas (CommonPrefixes)
                        if 'CommonPrefixes' in page:
                            for prefix in page['CommonPrefixes']:
                                folder_name = prefix['Prefix'][len(self.current_prefix):].rstrip('/')
                                if folder_name:  # Evitar nombres vacíos
                                    folders.append({
                                        'name': folder_name,
                                        'type': 'folder',
                                        'key': prefix['Prefix']
                                    })
                        
                        # Procesar archivos (Contents)
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                # Saltar el objeto si es igual al prefijo actual (carpeta actual)
                                if obj['Key'] == self.current_prefix:
                                    continue
                                
                                file_name = obj['Key'][len(self.current_prefix):]
                                # Solo incluir archivos en el nivel actual (sin subdirectorios)
                                if file_name and '/' not in file_name:
                                    objects.append({
                                        'name': file_name,
                                        'type': 'file',
                                        'size': obj['Size'],
                                        'modified': obj['LastModified'],
                                        'key': obj['Key']
                                    })
                    
                    # Combinar carpetas y archivos
                    self.objects_list = folders + objects
                    
                    # Actualizar la interfaz en el hilo principal
                    self.parent_app.root.after(0, self.actualizar_tabla_archivos)
                    
                except Exception as e:
                    # Si hay error en la iteración, aún podemos mostrar una lista vacía
                    print(f"Error iterando objetos: {e}")
                    self.objects_list = []
                    self.parent_app.root.after(0, self.actualizar_tabla_archivos)
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'NoSuchBucket':
                    error_msg = f"El bucket '{self.current_bucket}' no existe o no tienes permisos para acceder a él"
                elif error_code == 'AccessDenied':
                    error_msg = f"Acceso denegado al bucket '{self.current_bucket}'"
                else:
                    error_msg = f"Error AWS: {e.response['Error']['Message']}"
                
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error de AWS", error_msg))
                
            except Exception as e:
                error_msg = f"Error cargando contenido: {str(e)}"
                print(error_msg)  # Para debugging
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", error_msg))
                
            finally:
                # Asegurar que siempre se oculte el loading
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        # Ejecutar en hilo separado
        threading.Thread(target=cargar_objetos, daemon=True).start()
    
    def actualizar_tabla_archivos(self):
        # Limpiar tabla existente
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Agregar objetos a la tabla
        for obj in self.objects_list:
            if obj['type'] == 'folder':
                values = (f"📁 {obj['name']}", "Carpeta", "-", "-")
                self.files_tree.insert("", "end", values=values)
            else:
                size_str = self.format_file_size(obj['size'])
                date_str = obj['modified'].strftime("%Y-%m-%d %H:%M:%S")
                values = (f"📄 {obj['name']}", "Archivo", size_str, date_str)
                self.files_tree.insert("", "end", values=values)
        
        # Actualizar panel de información
        self.actualizar_info_panel()
    
    def format_file_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def actualizar_info_panel(self):
        self.info_text.delete('1.0', tk.END)
        
        if not self.current_bucket:
            self.info_text.insert(tk.END, "No hay bucket seleccionado")
            return
        
        total_files = len([obj for obj in self.objects_list if obj['type'] == 'file'])
        total_folders = len([obj for obj in self.objects_list if obj['type'] == 'folder'])
        total_size = sum(obj.get('size', 0) for obj in self.objects_list if obj['type'] == 'file')
        
        info = f"Bucket: {self.current_bucket}\n"
        info += f"Ruta: /{self.current_prefix}\n\n"
        info += f"Carpetas: {total_folders}\n"
        info += f"Archivos: {total_files}\n"
        info += f"Tamaño: {self.format_file_size(total_size)}"
        
        self.info_text.insert(tk.END, info)
    
    def on_item_double_click(self, event):
        selection = self.files_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.files_tree.item(item)['values']
        name = values[0]
        
        if values[1] == "Carpeta":
            folder_name = name.replace("📁 ", "")
            self.current_prefix += f"{folder_name}/"
            self.path_var.set(f"/{self.current_prefix}")
            self.refrescar_contenido()
    
    def ir_a_raiz(self):
        self.current_prefix = ""
        self.path_var.set("/")
        self.refrescar_contenido()
    
    def subir_nivel(self):
        if not self.current_prefix:
            return
        
        parts = self.current_prefix.rstrip('/').split('/')
        if len(parts) > 1:
            self.current_prefix = '/'.join(parts[:-1]) + '/'
        else:
            self.current_prefix = ""
        
        self.path_var.set(f"/{self.current_prefix}")
        self.refrescar_contenido()
    
    def crear_bucket(self):
        bucket_name = simpledialog.askstring("Crear Bucket", "Nombre del bucket:")
        if not bucket_name:
            return
        
        def crear():
            try:
                self.parent_app.loading.show(f"Creando bucket...")
                self.s3_client.create_bucket(Bucket=bucket_name)
                self.parent_app.root.after(0, self.actualizar_buckets)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=crear, daemon=True).start()
    
    def crear_carpeta(self):
        if not self.current_bucket:
            messagebox.showwarning("Sin bucket", "Selecciona un bucket primero")
            return
        
        folder_name = simpledialog.askstring("Crear Carpeta", "Nombre de la carpeta:")
        if not folder_name:
            return
        
        if not folder_name.endswith('/'):
            folder_name += '/'
        
        key = self.current_prefix + folder_name
        
        def crear():
            try:
                self.parent_app.loading.show("Creando carpeta...")
                self.s3_client.put_object(Bucket=self.current_bucket, Key=key)
                self.parent_app.root.after(0, self.refrescar_contenido)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=crear, daemon=True).start()
    
    def subir_archivo(self):
        if not self.current_bucket:
            messagebox.showwarning("Sin bucket", "Selecciona un bucket primero")
            return
        
        file_path = filedialog.askopenfilename(title="Seleccionar archivo")
        if not file_path:
            return
        
        file_name = os.path.basename(file_path)
        key = self.current_prefix + file_name
        file_size = os.path.getsize(file_path)
        
        # Crear ventana de progreso personalizada
        progress_window = self.crear_ventana_progreso(f"Subiendo {file_name}", file_size)
        
        def subir():
            try:
                start_time = time.time()
                uploaded_bytes = 0
                
                def callback(bytes_transferred):
                    nonlocal uploaded_bytes
                    uploaded_bytes += bytes_transferred
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    if elapsed > 0:
                        speed = uploaded_bytes / elapsed
                        percentage = (uploaded_bytes / file_size) * 100
                        
                        self.parent_app.root.after(0, lambda: self.actualizar_progreso(
                            progress_window, percentage, speed, uploaded_bytes, file_size))
                
                # Usar transfer_config para archivos grandes y callback para progreso
                from boto3.s3.transfer import TransferConfig
                config = TransferConfig(
                    multipart_threshold=1024 * 25,  # 25MB
                    max_concurrency=10,
                    multipart_chunksize=1024 * 25,
                    use_threads=True
                )
                
                self.s3_client.upload_file(
                    file_path, 
                    self.current_bucket, 
                    key,
                    Config=config,
                    Callback=callback
                )
                
                self.parent_app.root.after(0, self.refrescar_contenido)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, lambda: progress_window.destroy())
        
        threading.Thread(target=subir, daemon=True).start()
    
    def descargar_archivo(self):
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Selecciona un archivo primero")
            return
        
        item = selection[0]
        values = self.files_tree.item(item)['values']
        
        if values[1] == "Carpeta":
            messagebox.showwarning("Selección inválida", "No se pueden descargar carpetas")
            return
        
        file_name = values[0].replace("📄 ", "")
        
        file_obj = None
        for obj in self.objects_list:
            if obj['type'] == 'file' and obj['name'] == file_name:
                file_obj = obj
                break
        
        if not file_obj:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        save_path = filedialog.asksaveasfilename(
            title="Guardar archivo como",
            initialfile=file_name,
            filetypes=[("Todos los archivos", "*.*")]
        )
        
        if not save_path:
            return
        
        # Crear ventana de progreso personalizada
        file_size = file_obj['size']
        progress_window = self.crear_ventana_progreso(f"Descargando {file_name}", file_size)
        
        def descargar():
            try:
                start_time = time.time()
                downloaded_bytes = 0
                
                def callback(bytes_transferred):
                    nonlocal downloaded_bytes
                    downloaded_bytes += bytes_transferred
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    if elapsed > 0:
                        speed = downloaded_bytes / elapsed
                        percentage = (downloaded_bytes / file_size) * 100
                        
                        self.parent_app.root.after(0, lambda: self.actualizar_progreso(
                            progress_window, percentage, speed, downloaded_bytes, file_size))
                
                from boto3.s3.transfer import TransferConfig
                config = TransferConfig(
                    multipart_threshold=1024 * 25,  # 25MB
                    max_concurrency=10,
                    multipart_chunksize=1024 * 25,
                    use_threads=True
                )
                
                self.s3_client.download_file(
                    self.current_bucket, 
                    file_obj['key'], 
                    save_path,
                    Config=config,
                    Callback=callback
                )
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, lambda: progress_window.destroy())
        
        threading.Thread(target=descargar, daemon=True).start()
    
    def crear_ventana_progreso(self, titulo, total_size):
        """Crear ventana de progreso personalizada"""
        progress_window = tk.Toplevel(self.parent_app.root)
        progress_window.title(titulo)
        progress_window.geometry("420x180")
        progress_window.resizable(False, False)
        
        # Centrar la ventana
        progress_window.transient(self.parent_app.root)
        progress_window.grab_set()
        
        # Labels de información
        ttk.Label(progress_window, text=titulo, font=('Segoe UI', 10, 'bold')).pack(pady=10)
        
        # Barra de progreso
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window, 
            variable=progress_var, 
            maximum=100,
            length=350
        )
        progress_bar.pack(pady=5)
        
        # Label de porcentaje
        percentage_label = ttk.Label(progress_window, text="0%")
        percentage_label.pack(pady=2)
        
        # Label de velocidad y tamaño
        speed_label = ttk.Label(progress_window, text="Iniciando...")
        speed_label.pack(pady=2)
        
        # Botón cancelar (opcional, se puede implementar posteriormente)
        ttk.Button(progress_window, text="Cancelar", 
                  command=progress_window.destroy).pack(pady=5)
        
        # Almacenar referencias en la ventana para actualizaciones
        progress_window.progress_var = progress_var
        progress_window.percentage_label = percentage_label
        progress_window.speed_label = speed_label
        
        return progress_window
    
    def actualizar_progreso(self, progress_window, percentage, speed, transferred_bytes, total_size):
        """Actualizar la ventana de progreso"""
        try:
            if progress_window.winfo_exists():
                progress_window.progress_var.set(percentage)
                progress_window.percentage_label.config(text=f"{percentage:.1f}%")
                
                speed_str = self.format_file_size(speed) + "/s"
                transferred_str = self.format_file_size(transferred_bytes)
                total_str = self.format_file_size(total_size)
                
                progress_window.speed_label.config(
                    text=f"{transferred_str} / {total_str} - {speed_str}"
                )
        except tk.TclError:
            # La ventana fue cerrada
            pass
    
    def eliminar_archivo(self):
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Selecciona elementos para eliminar")
            return
        

        def eliminar():
            try:
                self.parent_app.loading.show("Eliminando...")
                
                objects_to_delete = []
                
                for item in selection:
                    values = self.files_tree.item(item)['values']
                    name = values[0].replace("📁 ", "").replace("📄 ", "")
                    
                    if values[1] == "Carpeta":
                        prefix = self.current_prefix + name + '/'
                        paginator = self.s3_client.get_paginator('list_objects_v2')
                        page_iterator = paginator.paginate(Bucket=self.current_bucket, Prefix=prefix)
                        
                        for page in page_iterator:
                            if 'Contents' in page:
                                for obj in page['Contents']:
                                    objects_to_delete.append({'Key': obj['Key']})
                    else:
                        for obj in self.objects_list:
                            if obj['type'] == 'file' and obj['name'] == name:
                                objects_to_delete.append({'Key': obj['key']})
                                break
                
                if objects_to_delete:
                    # Eliminar en lotes de 1000 (límite de AWS)
                    for i in range(0, len(objects_to_delete), 1000):
                        batch = objects_to_delete[i:i + 1000]
                        self.s3_client.delete_objects(
                            Bucket=self.current_bucket,
                            Delete={'Objects': batch}
                        )
                
                self.parent_app.root.after(0, self.refrescar_contenido)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=eliminar, daemon=True).start()
    
    
    def copiar_url(self):
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Selecciona un archivo primero")
            return
        
        item = selection[0]
        values = self.files_tree.item(item)['values']
        
        if values[1] == "Carpeta":
            messagebox.showwarning("Selección inválida", "No se puede obtener URL de carpetas")
            return
        
        file_name = values[0].replace("📄 ", "")
        
        file_obj = None
        for obj in self.objects_list:
            if obj['type'] == 'file' and obj['name'] == file_name:
                file_obj = obj
                break
        
        if not file_obj:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.current_bucket, 'Key': file_obj['key']},
                ExpiresIn=3600
            )
            
            self.parent_frame.clipboard_clear()
            self.parent_frame.clipboard_append(url)
            
            messagebox.showinfo("URL Copiada", f"URL copiada al clipboard (válida por 1 hora)")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_context_menu(self, event):
        try:
            item = self.files_tree.identify_row(event.y)
            if item:
                self.files_tree.selection_set(item)
                values = self.files_tree.item(item)['values']
                is_folder = values[1] == "Carpeta"
                
                context_menu = tk.Menu(self.parent_frame, tearoff=0)
                
                if is_folder:
                    context_menu.add_command(label="Abrir", command=lambda: self.on_item_double_click(event))
                    context_menu.add_command(label="Eliminar", command=self.eliminar_archivo)
                else:
                    context_menu.add_command(label="Descargar", command=self.descargar_archivo)
                    context_menu.add_command(label="Copiar URL", command=self.copiar_url)
                    context_menu.add_command(label="Eliminar", command=self.eliminar_archivo)
                
                context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error en menú contextual: {e}")

    def eliminar_bucket(self):
        if not self.current_bucket:
            messagebox.showwarning("Sin selección", "Selecciona un bucket primero")
            return
            
        def eliminar():
            try:
                self.parent_app.loading.show(f"Eliminando bucket {self.current_bucket}...")
                
                # Verificar que el bucket esté vacío
                response = self.s3_client.list_objects_v2(Bucket=self.current_bucket)
                if 'Contents' in response:
                    raise Exception("El bucket no está vacío. Elimina todos los objetos primero.")
                
                self.s3_client.delete_bucket(Bucket=self.current_bucket)
                
                self.current_bucket = None
                self.combo_buckets.set("")
                self.parent_app.root.after(0, self.actualizar_buckets)
                
            except Exception as e:
                self.parent_app.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Error al eliminar bucket: {str(e)}"))
            finally:
                self.parent_app.root.after(0, self.parent_app.loading.hide)
        
        threading.Thread(target=eliminar, daemon=True).start()