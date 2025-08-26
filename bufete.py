import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyodbc
import tempfile
import os
import webbrowser
import threading
import datetime

# 🎨 Estilos centralizados
ESTILOS = {
    "color_primario": "#2C3E50",              # Fondo del menú
    "color_secundario": "#34495E",            # Botones del menú
    "color_contenido": "#ECF0F1",             # Fondo del contenido
    "color_boton": "#34495E",
    "color_boton_filtro": "#1ABC9C",
    "color_boton_buscar": "#2980B9",
    "color_accento": "#5DADE2",  # Puedes cambiar el color si deseas
    

    "fondo_general": "#ECF0F1",
    "acordeon_caso_bg": "#DDEEEF",
    "acordeon_expediente_bg": "#FDF2E9",
    "acordeon_notificacion_bg": "#FBE9E7",
    "acordeon_pago_bg": "#FDEDEC",
    

    "fuente_titulo": ("Arial", 14, "bold"),
    "fuente_normal": ("Arial", 10),
    "fuente_boton": ("Arial", 9, "bold"),
    "fuente_negrita": ("Arial", 10, "bold"),
    "fuente_subtitulo": ("Arial", 12, "bold"),
    "fuente_italic": ("Arial", 10, "italic"),
    "fuente_filtro_bold": ("Arial", 10, "bold"),

}

# Conexión a SQL Server
def conectar_db():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};" 
        "SERVER=FABRI\SQLEXPRESS;" 
        "DATABASE=BufeteDB;"
        "Trusted_Connection=yes;"
    )

def validar_datos_generales(frame, campos, campos_opcionales=[]):
    validado = True
    for widget in frame.winfo_children():
        if isinstance(widget, tk.Entry):
            widget.configure(bg="white")  # Restaurar color por defecto

    for i, (campo, var) in enumerate(campos.items()):
        if campo not in campos_opcionales and not var.get().strip():
            validado = False
            # Buscar el Entry correspondiente
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Entry) and widget.cget("textvariable") == str(var):
                    widget.configure(bg="#FADBD8")  # Fondo rojo claro
                    break

    return validado



def validar_datos_cliente(campos, frame=None):
    campos_validos = True
    for clave, var in campos.items():
        if not var.get().strip():
            campos_validos = False
            if frame and hasattr(frame, "entradas_campos"):
                for v, entrada in frame.entradas_campos:
                    if v == var:
                        entrada.config(highlightthickness=2, highlightbackground="red")
        else:
            if frame and hasattr(frame, "entradas_campos"):
                for v, entrada in frame.entradas_campos:
                    if v == var:
                        entrada.config(highlightthickness=0)
    return campos_validos



# 📂 Abrir PDF desde SQL según el tipo de tabla
def abrir_pdf_desde_sql(numero, tabla):
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        campo_pdf = ""
        if tabla == "CASO":
            campo_pdf = "PDF_CASO"
            query = "SELECT PDF_CASO FROM CASO WHERE NUMERO_CASO = ?"
        elif tabla == "EXPEDIENTE":
            campo_pdf = "PDF_EXPEDIENTE"
            query = "SELECT PDF_EXPEDIENTE FROM EXPEDIENTE WHERE NUMERO_EXPEDIENTE = ?"
        elif tabla == "NOTIFICACION":
            campo_pdf = "DOCUMENTO_PDF"
            query = "SELECT DOCUMENTO_PDF FROM NOTIFICACION WHERE ID_NOTIFICACION = ?"
        else:
            return

        cursor.execute(query, (numero,))
        fila = cursor.fetchone()
        if fila and fila[0]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(fila[0])
                webbrowser.open_new(tmp.name)
        else:
            messagebox.showinfo("Sin archivo", "No se encontró un PDF para este registro.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()

# 🔁 Actualiza los datos de un Treeview
def actualizar_tabla(treeview, datos):
    for fila in treeview.get_children():
        treeview.delete(fila)
    for fila in datos:
        treeview.insert('', 'end', values=fila)

# --- CREAR CAMPOS DE FORMULARIO DE MANERA REUTILIZABLE ---
def crear_campos_formulario(frame, lista_campos, fila_inicial=0):
    entradas = []  # Guardaremos las entradas para resaltar

    for i, (etiqueta, variable) in enumerate(lista_campos):
        tk.Label(frame, text=etiqueta, bg=ESTILOS["color_contenido"]).grid(
            row=fila_inicial + i, column=0, sticky="e", padx=5, pady=3
        )
        entrada = tk.Entry(frame, textvariable=variable, width=40)
        entrada.grid(row=fila_inicial + i, column=1, padx=5, pady=3)
        entradas.append((variable, entrada))

    # Guardamos las entradas en el frame para acceder luego
    frame.entradas_campos = entradas




# 🏠 Pantalla de inicio
def pantalla_inicio(frame):
    frame.configure(bg=ESTILOS["color_contenido"])
    
    tk.Label(frame, text="Bienvenido al BUFETE DE ABOGADOS ROJAS Y ASOCIADOS", 
             font=ESTILOS["fuente_titulo"], bg=ESTILOS["color_contenido"]).pack(pady=20)

    # Botón para ver notificaciones de hoy
    tk.Button(
        frame, 
        text="🔔 Ver notificaciones de hoy", 
        font=ESTILOS["fuente_negrita"],
        bg=ESTILOS["color_accento"], 
        fg="white", 
        command=lambda: mostrar_notificaciones_hoy(frame)
    ).pack(pady=10)

    # Contenedor donde se mostrarán las notificaciones si se hace clic
    frame.notif_hoy_container = tk.Frame(frame, bg=ESTILOS["color_contenido"])
    frame.notif_hoy_container.pack(fill="both", expand=True, padx=20)


# --- MOSTRAR NOTIFICACIONES DE HOY ---
def mostrar_notificaciones_hoy(parent_frame):
    from datetime import date
    hoy = date.today()

    # Limpiar el contenedor primero
    for widget in parent_frame.winfo_children():
        widget.destroy()

    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ID_NOTIFICACION, TIPO_EXPEDIENTE, FECHA_AUDIENCIA, HORA_AUDIENCIA, LINK_REUNION, DOCUMENTO_PDF
            FROM NOTIFICACION
            WHERE FECHA_AUDIENCIA = ?
        """, hoy)
        notifs = cursor.fetchall()

        if not notifs:
            tk.Label(parent_frame, text="No hay notificaciones para hoy.", 
                     font=ESTILOS["fuente_normal"], bg=ESTILOS["color_contenido"]).pack(pady=5)
            return

        for notif in notifs:
            id_notif, tipo, fecha, hora, link, pdf = notif

            frame_notif = tk.Frame(parent_frame, bg=ESTILOS["acordeon_notificacion_bg"], bd=1, relief="ridge")
            frame_notif.pack(fill="x", pady=4, padx=10)

            encabezado = f"🔔 {tipo} - {fecha.strftime('%d/%m/%Y')} {hora.strftime('%H:%M')}"
            tk.Label(frame_notif, text=encabezado, font=ESTILOS["fuente_negrita"], 
                     bg=ESTILOS["acordeon_notificacion_bg"]).pack(anchor="w", padx=10, pady=2)

            def expandir(info=(id_notif, tipo, fecha, hora, link, pdf)):
                detalles = tk.Toplevel()
                detalles.title(f"Notificación {info[0]}")
                tk.Label(detalles, text=f"Tipo de expediente: {info[1]}").pack(anchor="w")
                tk.Label(detalles, text=f"Fecha: {info[2]}").pack(anchor="w")
                tk.Label(detalles, text=f"Hora: {info[3]}").pack(anchor="w")
                tk.Label(detalles, text=f"Link: {info[4]}").pack(anchor="w")
                if info[5]:
                    tk.Button(detalles, text="Abrir PDF", 
                              command=lambda: abrir_pdf_desde_sql(info[0], "NOTIFICACION")).pack(pady=5)

            tk.Button(frame_notif, text="Ver más", command=expandir).pack(anchor="e", padx=10)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar las notificaciones: {e}")
    finally:
        conn.close()

# --- FORMULARIO DE CLIENTE ---
def formulario_cliente(frame):
    frame.configure(bg=ESTILOS["color_contenido"])

    campos = {
        "DNI": tk.StringVar(),
        "Nombre": tk.StringVar(),
        "Apellido Paterno": tk.StringVar(),
        "Apellido Materno": tk.StringVar(),
        "Dirección 1": tk.StringVar(),
        "Dirección 2": tk.StringVar(),
        "Teléfono 1": tk.StringVar(),
        "Teléfono 2": tk.StringVar(),
        "Correo": tk.StringVar(),
        "Fecha de Nacimiento (YYYY-MM-DD)": tk.StringVar(),
        "Estado Civil (S/C/V)": tk.StringVar()
    }

    crear_campos_formulario(frame, list(campos.items()))

    def guardar_cliente():
        if not validar_datos_generales(frame, campos):
            messagebox.showwarning("Campos obligatorios", "Por favor completa los campos resaltados.")
            return
        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CLIENTE 
                (DNI, NOMBRE, APELLIDO_PATERNO, APELLIDO_MATERNO, 
                DIRECCION1, DIRECCION2, TELEFONO1, TELEFONO2, 
                CORREO, FECHA_NACIMIENTO, ESTADO_CIVIL)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(var.get().strip() for var in campos.values()))
            conn.commit()
            messagebox.showinfo("Éxito", "Cliente agregado correctamente")
            for var in campos.values():
                    var.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()



    tk.Button(frame, text="Guardar Cliente", command=guardar_cliente, bg=ESTILOS["color_secundario"], fg="white").grid(row=len(campos), column=0, columnspan=2, pady=10)

# --- FORMULARIO DE CASO ---
def formulario_caso(frame):
    from tkinter import filedialog

    campos = {
        "Número de Caso": tk.StringVar(),
        "DNI del Cliente": tk.StringVar(),
        "Materia": tk.StringVar(),
        "Delitos": tk.StringVar(),
        "Especialista Legal": tk.StringVar(),
        "Fiscal": tk.StringVar(),
        "Agraviado": tk.StringVar(),
        "Imputado": tk.StringVar(),
        "Fecha de Registro (YYYY-MM-DD)": tk.StringVar(),
    }
    estado = tk.StringVar(value="denuncia")
    nombre_pdf = tk.StringVar()
    pdf_binario = None

    def seleccionar_pdf():
        nonlocal pdf_binario
        ruta = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if ruta:
            with open(ruta, "rb") as archivo:
                pdf_binario = archivo.read()
            nombre_pdf.set(f"📎 {ruta.split('/')[-1]}")

    crear_campos_formulario(frame, list(campos.items()))

    ttk.Label(frame, text="Estado del Caso", background=ESTILOS["color_contenido"]).grid(row=len(campos), column=0, sticky="e", padx=5, pady=3)
    estado_combo = ttk.Combobox(frame, textvariable=estado, values=["denuncia", "investigacion", "decision"], state="readonly")
    estado_combo.grid(row=len(campos), column=1, padx=5, pady=3)

    ttk.Button(frame, text="Seleccionar PDF del caso", command=seleccionar_pdf).grid(row=len(campos)+1, column=0, columnspan=2, pady=5)
    ttk.Label(frame, textvariable=nombre_pdf, background=ESTILOS["color_contenido"], foreground="green").grid(row=len(campos)+2, column=0, columnspan=2)

    def guardar_caso():
        if not validar_datos_generales(frame, campos, campos_opcionales=["Delitos", "Especialista Legal"]):
            return

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO CASO (
                    NUMERO_CASO, DNI_CLIENTE, MATERIA, DELITOS,
                    NOMBRE_ESPECIALISTA, FISCAL, AGRAVIADO, IMPUTADO,
                    PDF_CASO, ESTADO_CASO, FECHA_REGISTRO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campos["Número de Caso"].get(), campos["DNI del Cliente"].get(), campos["Materia"].get(),
                campos["Delitos"].get(), campos["Especialista Legal"].get(), campos["Fiscal"].get(),
                campos["Agraviado"].get(), campos["Imputado"].get(), pdf_binario,
                estado.get(), campos["Fecha de Registro (YYYY-MM-DD)"].get()
            ))
            conn.commit()
            messagebox.showinfo("Éxito", "Caso registrado correctamente.")
            for var in campos.values():
                var.set("")
            estado.set("denuncia")
            nombre_pdf.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()


    ttk.Button(frame, text="Guardar Caso", command=guardar_caso).grid(row=len(campos)+3, column=0, columnspan=2, pady=10)

# --- FORMULARIO DE EXPEDIENTE ---
def formulario_expediente(frame):
    from tkinter import filedialog

    campos = {
        "Número de Expediente": tk.StringVar(),
        "DNI del Cliente": tk.StringVar(),
        "Materia": tk.StringVar(),
        "Delitos": tk.StringVar(),
        "Especialista Legal": tk.StringVar(),
        "Juez": tk.StringVar(),
        "Demandante": tk.StringVar(),
        "Demandado": tk.StringVar(),
        "Fecha de Registro (YYYY-MM-DD)": tk.StringVar(),
    }
    estado = tk.StringVar(value="control de acusacion")
    nombre_pdf = tk.StringVar()
    pdf_binario = None 

    def seleccionar_pdf():
        nonlocal pdf_binario
        ruta = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if ruta:
            with open(ruta, "rb") as archivo:
                pdf_binario = archivo.read()
            nombre_pdf.set(f"📎 {ruta.split('/')[-1]}")

    crear_campos_formulario(frame, list(campos.items()))

    ttk.Label(frame, text="Estado del Expediente", background=ESTILOS["color_contenido"]).grid(row=len(campos), column=0, sticky="e", padx=5, pady=3)
    estado_combo = ttk.Combobox(frame, textvariable=estado, values=["control de acusacion", "juzgamiento", "sentencia"], state="readonly")
    estado_combo.grid(row=len(campos), column=1, padx=5, pady=3)

    ttk.Button(frame, text="Seleccionar PDF del expediente", command=seleccionar_pdf).grid(row=len(campos)+1, column=0, columnspan=2, pady=5)
    ttk.Label(frame, textvariable=nombre_pdf, background=ESTILOS["color_contenido"], foreground="green").grid(row=len(campos)+2, column=0, columnspan=2)

    def guardar_expediente():
        if not validar_datos_generales(frame, campos, campos_opcionales=["Delitos", "Especialista Legal"]):
            return

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO EXPEDIENTE (
                    NUMERO_EXPEDIENTE, DNI_CLIENTE, MATERIA, DELITOS,
                    NOMBRE_ESPECIALISTA, JUEZ, DEMANDANTE, DEMANDADO,
                    PDF_EXPEDIENTE, ESTADO_EXPEDIENTE, FECHA_REGISTRO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campos["Número de Expediente"].get(), campos["DNI del Cliente"].get(), campos["Materia"].get(),
                campos["Delitos"].get(), campos["Especialista Legal"].get(), campos["Juez"].get(),
                campos["Demandante"].get(), campos["Demandado"].get(), pdf_binario,
                estado.get(), campos["Fecha de Registro (YYYY-MM-DD)"].get()
            ))
            conn.commit()
            messagebox.showinfo("Éxito", "Expediente registrado correctamente.")
            for var in campos.values():
                var.set("")
            estado.set("control de acusacion")
            nombre_pdf.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    ttk.Button(frame, text="Guardar Expediente", command=guardar_expediente).grid(row=len(campos)+3, column=0, columnspan=2, pady=10)

# --- FORMULARIO DE NOTIFICACIÓN ---
def formulario_notificacion(frame):
    from tkinter import filedialog
    import datetime

    dni = tk.StringVar()
    tipo = tk.StringVar()
    fecha = tk.StringVar()
    hora = tk.StringVar()
    link = tk.StringVar()
    nombre_pdf = tk.StringVar()
    pdf_binario = None

    campos = {
        "DNI del Cliente": dni,
        "Fecha de Audiencia (YYYY-MM-DD)": fecha,
        "Hora de Audiencia (HH:MM)": hora,
        "Link de la Reunión": link,
    }

    # Botón y etiqueta para PDF
    def seleccionar_pdf():
        nonlocal pdf_binario
        ruta = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if ruta:
            with open(ruta, "rb") as archivo:
                pdf_binario = archivo.read()
            nombre_pdf.set(f"Archivo cargado: {ruta.split('/')[-1]}")

    crear_campos_formulario(frame, list(campos.items()))

    # Tipo de expediente
    tk.Label(frame, text="Tipo de expediente", bg=ESTILOS["color_contenido"]).grid(row=len(campos), column=0, sticky="e", padx=5, pady=3)
    tipo_combo = ttk.Combobox(frame, textvariable=tipo, values=["caso", "expediente"], state="readonly")
    tipo_combo.grid(row=len(campos), column=1, padx=5, pady=3)
    tipo_combo.current(0)

    # Botón y etiqueta PDF
    tk.Button(frame, text="Seleccionar PDF de la notificación", command=seleccionar_pdf).grid(row=len(campos)+1, columnspan=2, pady=5)
    tk.Label(frame, textvariable=nombre_pdf, bg=ESTILOS["color_contenido"], fg="green").grid(row=len(campos)+2, columnspan=2)

    def guardar_notificacion():
        if not validar_datos_generales(frame, campos):
            messagebox.showwarning("Campos obligatorios", "Por favor completa los campos resaltados.")
            return
        if pdf_binario is None:
            messagebox.showwarning("Falta PDF", "Por favor selecciona un archivo PDF.")
            return

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO NOTIFICACION (
                    DNI_CLIENTE, TIPO_EXPEDIENTE, FECHA_AUDIENCIA, 
                    HORA_AUDIENCIA, LINK_REUNION, DOCUMENTO_PDF
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dni.get(), tipo.get(), fecha.get(), hora.get(), link.get(), pdf_binario
            ))
            conn.commit()
            messagebox.showinfo("Éxito", "Notificación registrada correctamente.")
            for var in campos.values():
                var.set("")
            tipo.set("caso")
            nombre_pdf.set("")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    tk.Button(frame, text="Guardar Notificación", command=guardar_notificacion, bg=ESTILOS["color_secundario"], fg="white").grid(row=len(campos)+4, columnspan=2, pady=10)

# --- FORMULARIO DE PAGO ---
def formulario_pago(frame):
    from tkinter import ttk

    dni = tk.StringVar()
    tipo = tk.StringVar()
    referencia = tk.StringVar()
    monto = tk.StringVar()
    fecha = tk.StringVar()
    estado = tk.StringVar()

    campos = {
        "DNI del Cliente": dni,
        "Número de Caso o Expediente": referencia,
        "Monto (S/.)": monto,
        "Fecha de Pago (YYYY-MM-DD)": fecha
    }

    crear_campos_formulario(frame, list(campos.items()))

    # Tipo de expediente
    tk.Label(frame, text="Tipo de expediente", bg=ESTILOS["color_contenido"]).grid(row=len(campos), column=0, sticky="e", padx=5, pady=3)
    tipo_combo = ttk.Combobox(frame, textvariable=tipo, values=["caso", "expediente"], state="readonly")
    tipo_combo.grid(row=len(campos), column=1, padx=5, pady=3)
    tipo_combo.current(0)

    # Estado del pago
    tk.Label(frame, text="Estado del Pago", bg=ESTILOS["color_contenido"]).grid(row=len(campos)+1, column=0, sticky="e", padx=5, pady=3)
    estado_combo = ttk.Combobox(frame, textvariable=estado, values=["Pagado", "Pendiente"], state="readonly")
    estado_combo.grid(row=len(campos)+1, column=1, padx=5, pady=3)
    estado_combo.current(0)

    def guardar_pago():
        campos = {
            "DNI del Cliente": dni,
            "Número de Caso o Expediente": referencia,
            "Monto (S/.)": monto,
            "Fecha de Pago (YYYY-MM-DD)": fecha
        }

        if not validar_datos_generales(frame, campos):
            messagebox.showwarning("Campos obligatorios", "Por favor completa los campos obligatorios.")
            return

        try:
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO PAGO (
                    DNI_CLIENTE, TIPO_EXPEDIENTE, NUMERO_REFERENCIA,
                    MONTO, FECHA_PAGO, ESTADO_PAGO
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dni.get(),
                tipo.get(),
                referencia.get(),
                float(monto.get()),
                fecha.get(),
                estado.get()
            ))
            conn.commit()
            messagebox.showinfo("Éxito", "Pago registrado correctamente.")
            for var in campos.values():
                var.set("")
            tipo.set("caso")
            estado.set("Pagado")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    tk.Button(frame, text="Registrar Pago", command=guardar_pago).grid(row=len(campos)+2, columnspan=2, pady=10)

# --- MOSTRAR DETALLE DE UNA NOTIFICACIÓN ---
def mostrar_detalle_notificacion(id_notificacion):
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM NOTIFICACION WHERE ID_NOTIFICACION = ?", (id_notificacion,))
        notif = cursor.fetchone()

        if notif:
            # Mostrar detalles en ventana flotante
            detalle = tk.Toplevel()
            detalle.title("Detalle de Notificación")
            detalle.configure(bg=ESTILOS["color_contenido"])

            tk.Label(detalle, text=f"DNI Cliente: {notif.DNI_CLIENTE}", bg=ESTILOS["color_contenido"], font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalle, text=f"Fecha de Audiencia: {notif.FECHA_AUDIENCIA}", bg=ESTILOS["color_contenido"], font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalle, text=f"Hora: {notif.HORA_AUDIENCIA}", bg=ESTILOS["color_contenido"], font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalle, text=f"Link: {notif.LINK_REUNION}", bg=ESTILOS["color_contenido"], font=ESTILOS["fuente_normal"]).pack(anchor="w")

            if notif.DOCUMENTO_PDF:
                def abrir():
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(notif.DOCUMENTO_PDF)
                        webbrowser.open_new(tmp.name)
                tk.Button(detalle, text="Abrir PDF", command=abrir, bg=ESTILOS["color_secundario"], fg="white").pack(pady=5)

            # Marcar como alertado
            cursor.execute("UPDATE NOTIFICACION SET ALERTADO = 1 WHERE ID_NOTIFICACION = ?", (id_notificacion,))
            conn.commit()

        else:
            messagebox.showinfo("No encontrado", "No se encontró la notificación.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()


def mostrar_login():
    login = tk.Tk()
    login.title("Login - Bufete de Abogados")
    login.geometry("300x180")

    tk.Label(login, text="Usuario:", font="fuente_normal").pack(pady=5)
    usuario_var = tk.StringVar()
    tk.Entry(login, textvariable=usuario_var).pack()

    tk.Label(login, text="Contraseña:", font="fuente_normal").pack(pady=5)
    clave_var = tk.StringVar()
    tk.Entry(login, textvariable=clave_var, show="*").pack()

    def validar_login():
        usuario = usuario_var.get().strip()
        clave = clave_var.get().strip()
        if not usuario or not clave:
            messagebox.showwarning("Campos vacíos", "Por favor completa todos los campos.")
            return

        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USUARIO WHERE USERNAME = ? AND PASSWORD_HASH = ?", (usuario, clave))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            messagebox.showinfo("Acceso permitido", f"Bienvenido, {usuario}")
            login.destroy()
            mostrar_ventana_principal()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")

    tk.Button(login, text="Ingresar", command=validar_login).pack(pady=15)
    login.mainloop()

# --- VERIFICAR ALERTAS AUTOMÁTICAS DE NOTIFICACIONES ---
import threading
import datetime

def verificar_alertas_pendientes():
    try:
        conn = conectar_db()
        cursor = conn.cursor()

        ahora = datetime.datetime.now()
        cursor.execute("""
            SELECT ID_NOTIFICACION, FECHA_AUDIENCIA, HORA_AUDIENCIA 
            FROM NOTIFICACION 
            WHERE ALERTADO = 0
        """)
        for row in cursor.fetchall():
            id_notif, fecha, hora = row
            if isinstance(fecha, datetime.date) and isinstance(hora, datetime.time):
                dt_audiencia = datetime.datetime.combine(fecha, hora)
                diferencia = (dt_audiencia - ahora).total_seconds()
                if 0 <= diferencia <= 1800:  # 30 minutos o menos
                    mostrar_detalle_notificacion(id_notif)

        conn.close()
    except Exception as e:
        print("Error al verificar alertas:", e)

    # Se vuelve a ejecutar cada 60 segundos
    threading.Timer(60, verificar_alertas_pendientes).start()

# 📂 Mostrar CASOS en forma de acordeón
def mostrar_casos_como_acordeon(parent, lista_casos):
    for widget in parent.winfo_children():
        widget.destroy()

    for caso in lista_casos:
        frame_caso = tk.Frame(parent, bg=ESTILOS["acordeon_caso_bg"], bd=1, relief="raised")
        frame_caso.pack(fill="x", pady=4, padx=10)

        encabezado = f"📂 {caso['numero']} - {caso['materia']} [{caso['estado']}]"
        lbl = tk.Label(frame_caso, text=encabezado, font=ESTILOS["fuente_negrita"], bg=ESTILOS["acordeon_caso_bg"])
        lbl.pack(anchor="w", padx=10, pady=2)

        def expandir(info=caso):
            detalles = tk.Toplevel()
            detalles.title(f"Detalle del caso {info['numero']}")

            # Variables editables
            fiscal = tk.StringVar(value=info['fiscal'])
            agraviado = tk.StringVar(value=info['agraviado'])
            imputado = tk.StringVar(value=info['imputado'])
            fecha = tk.StringVar(value=info['fecha'])

            # Widgets
            entries = []

            def agregar_campo(label_text, var):
                frame = tk.Frame(detalles)
                frame.pack(anchor="w", fill="x", padx=10, pady=2)
                tk.Label(frame, text=label_text, width=12).pack(side="left")
                ent = tk.Entry(frame, textvariable=var, state="disabled", width=50)
                ent.pack(side="left", fill="x", expand=True)
                entries.append(ent)

            agregar_campo("Fiscal:", fiscal)
            agregar_campo("Agraviado:", agraviado)
            agregar_campo("Imputado:", imputado)
            agregar_campo("Fecha:", fecha)

            if info['pdf']:
                tk.Button(detalles, text="Abrir PDF", command=lambda: abrir_pdf_desde_sql(info['numero'], "CASO")).pack(pady=5)

            # 🔒 Editar
            def habilitar_edicion():
                for ent in entries:
                    ent.config(state="normal")
                btn_editar.pack_forget()
                btn_guardar.pack(pady=5)

            def guardar_cambios():
                try:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE CASO SET 
                        FISCAL = ?, AGRAVIADO = ?, IMPUTADO = ?, FECHA_REGISTRO = ?
                        WHERE NUMERO_CASO = ?
                    """, (fiscal.get(), agraviado.get(), imputado.get(), fecha.get(), info['numero']))
                    conn.commit()
                    messagebox.showinfo("Éxito", "Datos del caso actualizados.")
                    detalles.destroy()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    conn.close()

            btn_editar = tk.Button(detalles, text="Editar", command=habilitar_edicion)
            btn_editar.pack(pady=5)

            btn_guardar = tk.Button(detalles, text="Guardar Cambios", command=guardar_cambios)
            btn_guardar.pack_forget()

            # Pagos vinculados
            try:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MONTO, FECHA_PAGO, ESTADO_PAGO 
                    FROM PAGO 
                    WHERE NUMERO_REFERENCIA = ? AND TIPO_EXPEDIENTE = 'caso'
                """, (info['numero'],))
                pagos = cursor.fetchall()
                if pagos:
                    tk.Label(detalles, text="Pagos vinculados:", font=ESTILOS["fuente_negrita"]).pack(anchor="w", pady=(10, 0))
                    for pago in pagos:
                        texto_pago = f"Monto: S/. {pago[0]}, Fecha: {pago[1]}, Estado: {pago[2]}"
                        tk.Label(detalles, text=texto_pago).pack(anchor="w")
                else:
                    tk.Label(detalles, text="Sin pagos vinculados a este caso.").pack(anchor="w", pady=(10, 0))
                conn.close()
            except Exception as e:
                tk.Label(detalles, text=f"Error al obtener pagos: {e}", fg="red").pack(anchor="w")

        tk.Button(frame_caso, text="Ver más", command=expandir).pack(anchor="e", padx=10)


# 📁 Mostrar EXPEDIENTES en forma de acordeón
def mostrar_expedientes_como_acordeon(parent, lista_expedientes):
    for widget in parent.winfo_children():
        widget.destroy()

    for exp in lista_expedientes:
        frame_exp = tk.Frame(parent, bg=ESTILOS["acordeon_expediente_bg"], bd=1, relief="raised")
        frame_exp.pack(fill="x", pady=4, padx=10)

        encabezado = f"📁 {exp['numero']} - {exp['materia']} [{exp['estado']}]"
        lbl = tk.Label(frame_exp, text=encabezado, font=ESTILOS["fuente_negrita"], bg=ESTILOS["acordeon_expediente_bg"])
        lbl.pack(anchor="w", padx=10, pady=2)

        def expandir(info=exp):
            detalles = tk.Toplevel()
            detalles.title(f"Detalle del expediente {info['numero']}")

            tk.Label(detalles, text=f"Especialista: {info['especialista']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Juez: {info['juez']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Demandante: {info['demandante']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Demandado: {info['demandado']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Fecha: {info['fecha']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")

            if info['pdf']:
                tk.Button(detalles, text="Abrir PDF", font=ESTILOS["fuente_normal"],
                          command=lambda: abrir_pdf_desde_sql(info['numero'], "EXPEDIENTE")).pack(pady=5)

            try:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MONTO, FECHA_PAGO, ESTADO_PAGO 
                    FROM PAGO 
                    WHERE NUMERO_REFERENCIA = ? AND TIPO_EXPEDIENTE = 'expediente'
                """, (info['numero'],))
                pagos = cursor.fetchall()
                if pagos:
                    tk.Label(detalles, text="Pagos vinculados:", font=ESTILOS["fuente_negrita"]).pack(anchor="w", pady=(10, 0))
                    for pago in pagos:
                        texto_pago = f"Monto: S/. {pago[0]}, Fecha: {pago[1]}, Estado: {pago[2]}"
                        tk.Label(detalles, text=texto_pago, font=ESTILOS["fuente_normal"]).pack(anchor="w")
                else:
                    tk.Label(detalles, text="Sin pagos vinculados a este expediente.", font=ESTILOS["fuente_normal"]).pack(anchor="w", pady=(10, 0))
                conn.close()
            except Exception as e:
                tk.Label(detalles, text=f"Error al obtener pagos: {e}", fg="red", font=ESTILOS["fuente_normal"]).pack(anchor="w")

        tk.Button(frame_exp, text="Ver más", command=expandir, font=ESTILOS["fuente_normal"]).pack(anchor="e", padx=10)


# 🔔 Mostrar NOTIFICACIONES en forma de acordeón
def mostrar_notificaciones_como_acordeon(parent, lista_notif):
    for widget in parent.winfo_children():
        widget.destroy()

    for notif in lista_notif:
        frame_notif = tk.Frame(parent, bg=ESTILOS["acordeon_notificacion_bg"], bd=1, relief="ridge")
        frame_notif.pack(fill="x", pady=4, padx=10)

        encabezado = f"🔔 {notif['tipo']} [{notif['fecha']} {notif['hora']}]"
        lbl = tk.Label(frame_notif, text=encabezado, font=ESTILOS["fuente_negrita"], bg=ESTILOS["acordeon_notificacion_bg"])
        lbl.pack(anchor="w", padx=10, pady=2)

        def expandir(info=notif):
            detalles = tk.Toplevel()
            detalles.title(f"Notificación {info['numero']}")
            tk.Label(detalles, text=f"Tipo de expediente: {info['tipo']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Fecha: {info['fecha']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Hora: {info['hora']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Link: {info['link']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            if info['pdf']:
                tk.Button(detalles, text="Abrir PDF", font=ESTILOS["fuente_normal"],
                          command=lambda: abrir_pdf_desde_sql(info['numero'], "NOTIFICACION")).pack(pady=5)

        tk.Button(frame_notif, text="Ver más", command=expandir, font=ESTILOS["fuente_normal"]).pack(anchor="e", padx=10)



# 💰 Mostrar PAGOS en forma de acordeón
def mostrar_pagos_como_acordeon(parent, lista_pagos):
    for widget in parent.winfo_children():
        widget.destroy()

    for pago in lista_pagos:
        frame_pago = tk.Frame(parent, bg=ESTILOS["acordeon_pago_bg"], bd=1, relief="raised")
        frame_pago.pack(fill="x", pady=4, padx=10)

        encabezado = f"💰 {pago['tipo']} - {pago['referencia']} [{pago['estado']}]"
        lbl = tk.Label(frame_pago, text=encabezado, font=ESTILOS["fuente_negrita"], bg=ESTILOS["acordeon_pago_bg"])
        lbl.pack(anchor="w", padx=10, pady=2)

        def expandir(info=pago):
            detalles = tk.Toplevel()
            detalles.title(f"Detalle del pago {info['referencia']}")
            tk.Label(detalles, text=f"Tipo: {info['tipo']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Número de Referencia: {info['referencia']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Monto: S/. {info['monto']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Fecha: {info['fecha']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")
            tk.Label(detalles, text=f"Estado: {info['estado']}", font=ESTILOS["fuente_normal"]).pack(anchor="w")

        tk.Button(frame_pago, text="Ver más", command=expandir, font=ESTILOS["fuente_normal"]).pack(anchor="e", padx=10)



# --- CREAR TABLA CON TÍTULO ---
def crear_acordeon_casos(frame, lista_casos):
    for caso in lista_casos:
        contenedor = tk.Frame(frame, bd=1, relief="groove", bg="#F9F9F9")
        contenedor.pack(fill="x", padx=5, pady=3)

        encabezado = tk.Frame(contenedor, bg="#D6EAF8")
        encabezado.pack(fill="x")
        tk.Label(encabezado, text=f"{caso['numero']} - {caso['materia']} ({caso['estado']})", font=("Arial", 10, "bold"), bg="#D6EAF8").pack(side="left", padx=5, pady=5)

        cuerpo = tk.Frame(contenedor, bg="#F2F4F4")
        tk.Label(cuerpo, text=f"Fiscal: {caso['fiscal']}", bg="#F2F4F4").pack(anchor="w")
        tk.Label(cuerpo, text=f"Agraviado: {caso['agraviado']}", bg="#F2F4F4").pack(anchor="w")
        tk.Label(cuerpo, text=f"Imputado: {caso['imputado']}", bg="#F2F4F4").pack(anchor="w")
        tk.Label(cuerpo, text=f"Fecha: {caso['fecha']}", bg="#F2F4F4").pack(anchor="w")
        if caso['pdf']:
            tk.Button(cuerpo, text="Ver PDF").pack(anchor="w", pady=3)

        def toggle():
            if cuerpo.winfo_viewable():
                cuerpo.pack_forget()
            else:
                cuerpo.pack(fill="x", padx=10, pady=5)

        tk.Button(encabezado, text="➤", width=3, command=toggle).pack(side="right", padx=5)

# --- FORMULARIO DE BÚSQUEDA POR DNI ---
def formulario_buscar_dni(frame):
    frame.configure(bg=ESTILOS["fondo_general"])

    tk.Label(frame, text="Buscar Cliente por DNI", font=ESTILOS["fuente_titulo"], bg=ESTILOS["fondo_general"]).pack(pady=10)

    dni_var = tk.StringVar()
    datos_cliente = tk.StringVar()

    tk.Entry(frame, textvariable=dni_var, width=30, font=ESTILOS["fuente_normal"]).pack()
    tk.Button(frame, text="Buscar", command=lambda: buscar_dni(dni_var.get(), frame, datos_cliente),
              bg=ESTILOS["color_boton_buscar"], fg="white", font=ESTILOS["fuente_boton"]).pack(pady=5)
    tk.Label(frame, textvariable=datos_cliente, font=ESTILOS["fuente_italic"], bg=ESTILOS["fondo_general"]).pack(pady=5)

    acordeon_container = tk.Frame(frame, bg=ESTILOS["fondo_general"])
    acordeon_container.pack(fill="both", expand=True)

    # ----- CASOS -----
    tk.Label(acordeon_container, text="Casos", font=ESTILOS["fuente_subtitulo"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10)

    tk.Label(acordeon_container, text="🔍 Filtrar en Casos:", font=ESTILOS["fuente_filtro_bold"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10, pady=(10, 0))

    frame_filtro_casos = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame_filtro_casos.pack(fill="x", padx=20, pady=(0, 5))

    filtro_materia_caso = tk.StringVar()
    filtro_estado_caso = tk.StringVar()

    tk.Label(frame_filtro_casos, text="Materia:", bg=ESTILOS["fondo_general"]).grid(row=0, column=0, sticky="e", padx=2)
    tk.Entry(frame_filtro_casos, textvariable=filtro_materia_caso, width=20).grid(row=0, column=1, padx=2)

    tk.Label(frame_filtro_casos, text="Estado:", bg=ESTILOS["fondo_general"]).grid(row=0, column=2, sticky="e", padx=2)
    tk.Entry(frame_filtro_casos, textvariable=filtro_estado_caso, width=20).grid(row=0, column=3, padx=2)

    tk.Button(frame_filtro_casos, text="Filtrar Casos", command=lambda: aplicar_filtro_casos(),
              bg=ESTILOS["color_boton_filtro"], fg="white", font=ESTILOS["fuente_boton"]).grid(row=0, column=4, padx=10)

    frame.acordeon_casos = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame.acordeon_casos.pack(fill="x", padx=10)

    def aplicar_filtro_casos():
        materia = filtro_materia_caso.get().strip().lower()
        estado = filtro_estado_caso.get().strip().lower()
        filtrados = [
            c for c in getattr(frame, "todos_los_casos", [])
            if (not materia or materia in c["materia"].lower()) and (not estado or estado in c["estado"].lower())
        ]
        mostrar_casos_como_acordeon(frame.acordeon_casos, filtrados)


        # ----- EXPEDIENTES -----
    tk.Label(acordeon_container, text="Expedientes", font=ESTILOS["fuente_subtitulo"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10, pady=(10, 0))

    tk.Label(acordeon_container, text="🧠 Filtrar en Expedientes:", font=ESTILOS["fuente_filtro_bold"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10, pady=(5, 0))

    frame_filtro_exp = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame_filtro_exp.pack(fill="x", padx=20, pady=(0, 5))

    filtro_materia_exp = tk.StringVar()
    filtro_estado_exp = tk.StringVar()

    tk.Label(frame_filtro_exp, text="Materia:", bg=ESTILOS["fondo_general"]).grid(row=0, column=0, sticky="e", padx=2)
    tk.Entry(frame_filtro_exp, textvariable=filtro_materia_exp, width=20).grid(row=0, column=1, padx=2)

    tk.Label(frame_filtro_exp, text="Estado:", bg=ESTILOS["fondo_general"]).grid(row=0, column=2, sticky="e", padx=2)
    tk.Entry(frame_filtro_exp, textvariable=filtro_estado_exp, width=20).grid(row=0, column=3, padx=2)

    tk.Button(frame_filtro_exp, text="Filtrar Expedientes", command=lambda: aplicar_filtro_expedientes(),
              bg=ESTILOS["color_boton_filtro"], fg="white", font=ESTILOS["fuente_boton"]).grid(row=0, column=4, padx=10)

    frame.acordeon_expedientes = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame.acordeon_expedientes.pack(fill="x", padx=10)

    def aplicar_filtro_expedientes():
        materia = filtro_materia_exp.get().strip().lower()
        estado = filtro_estado_exp.get().strip().lower()
        filtrados = [
            e for e in getattr(frame, "todos_los_expedientes", [])
            if (not materia or materia in e["materia"].lower()) and (not estado or estado in e["estado"].lower())
        ]
        mostrar_expedientes_como_acordeon(frame.acordeon_expedientes, filtrados)

    # ----- NOTIFICACIONES -----
    tk.Label(acordeon_container, text="Notificaciones", font=ESTILOS["fuente_subtitulo"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10, pady=(10, 0))
    frame.acordeon_notificaciones = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame.acordeon_notificaciones.pack(fill="x", padx=10)

    # ----- PAGOS -----
    tk.Label(acordeon_container, text="Pagos", font=ESTILOS["fuente_subtitulo"], bg=ESTILOS["fondo_general"]).pack(anchor="w", padx=10, pady=(10, 0))
    frame.acordeon_pagos = tk.Frame(acordeon_container, bg=ESTILOS["fondo_general"])
    frame.acordeon_pagos.pack(fill="x", padx=10)

    # Referencias para actualización desde buscar_dni
    frame.tablas = {
        "expedientes": frame.acordeon_expedientes,
        "notificaciones": frame.acordeon_notificaciones,
        "pagos": frame.acordeon_pagos
    }


# --- FUNCIÓN DE BÚSQUEDA DE CLIENTE POR DNI ---
def buscar_dni(dni, frame, datos_cliente):
    dni = dni.strip()
    if not dni:
        messagebox.showwarning("Error", "Por favor, ingresa un DNI.")
        return

    if not hasattr(frame, "tablas"):
        messagebox.showerror("Error", "Este formulario no soporta búsqueda de registros.")
        return

    try:
        conn = conectar_db()
        cursor = conn.cursor()

        # Buscar cliente
        cursor.execute("SELECT * FROM CLIENTE WHERE DNI = ?", dni)
        cliente = cursor.fetchone()
        if not cliente:
            messagebox.showinfo("Sin resultados", "No se encontró cliente con ese DNI.")
            return

        datos_cliente.set(f"{cliente.NOMBRE} {cliente.APELLIDO_PATERNO} {cliente.APELLIDO_MATERNO} - {cliente.DIRECCION1}")

        # Buscar casos
        cursor.execute("""
            SELECT NUMERO_CASO, MATERIA, ESTADO_CASO, FISCAL, AGRAVIADO, IMPUTADO, FECHA_REGISTRO, PDF_CASO 
            FROM CASO WHERE DNI_CLIENTE = ?
        """, dni)
        casos_sql = cursor.fetchall()
        casos = [{
            "numero": c[0],
            "materia": c[1],
            "estado": c[2],
            "fiscal": c[3],
            "agraviado": c[4],
            "imputado": c[5],
            "fecha": str(c[6]),
            "pdf": bool(c[7])
        } for c in casos_sql]
        frame.todos_los_casos = casos
        mostrar_casos_como_acordeon(frame.acordeon_casos, casos)

        # Buscar expedientes
        cursor.execute("""
            SELECT NUMERO_EXPEDIENTE, MATERIA, ESTADO_EXPEDIENTE, NOMBRE_ESPECIALISTA, JUEZ, DEMANDANTE, DEMANDADO, FECHA_REGISTRO, PDF_EXPEDIENTE 
            FROM EXPEDIENTE WHERE DNI_CLIENTE = ?
        """, dni)
        expedientes_sql = cursor.fetchall()
        expedientes = [{
            "numero": e[0],
            "materia": e[1],
            "estado": e[2],
            "especialista": e[3],
            "juez": e[4],
            "demandante": e[5], 
            "demandado": e[6],
            "fecha": str(e[7]),
            "pdf": bool(e[8])
        } for e in expedientes_sql]
        frame.todos_los_expedientes = expedientes
        mostrar_expedientes_como_acordeon(frame.acordeon_expedientes, expedientes)

        # Buscar notificaciones
        cursor.execute("""
            SELECT ID_NOTIFICACION, TIPO_EXPEDIENTE, FECHA_AUDIENCIA, HORA_AUDIENCIA, LINK_REUNION, DOCUMENTO_PDF 
            FROM NOTIFICACION WHERE DNI_CLIENTE = ?
        """, dni)
        notificaciones_sql = cursor.fetchall()
        notifs = [{
            "numero": n[0],
            "tipo": n[1],
            "fecha": str(n[2]),
            "hora": str(n[3]),
            "link": n[4],
            "pdf": bool(n[5])
        } for n in notificaciones_sql]
        mostrar_notificaciones_como_acordeon(frame.acordeon_notificaciones, notifs)

        # Buscar pagos
        cursor.execute("""
            SELECT TIPO_EXPEDIENTE, NUMERO_REFERENCIA, MONTO, FECHA_PAGO, ESTADO_PAGO 
            FROM PAGO WHERE DNI_CLIENTE = ?
        """, dni)
        pagos_sql = cursor.fetchall()
        pagos = [{
            "tipo": p[0],
            "referencia": p[1],
            "monto": float(p[2]),
            "fecha": str(p[3]),
            "estado": p[4]
        } for p in pagos_sql]
        mostrar_pagos_como_acordeon(frame.acordeon_pagos, pagos)

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        conn.close()






# 🧭 Ventana principal del sistema
def mostrar_ventana_principal():
    root = tk.Tk()
    root.title("Sistema de Gestión - Bufete de Abogados")
    root.geometry("1000x600")

    menu_frame = tk.Frame(root, bg=ESTILOS["color_primario"], width=200)
    menu_frame.pack(side="left", fill="y")

    contenido_frame = tk.Frame(root, bg=ESTILOS["fondo_general"])
    contenido_frame.pack(side="right", fill="both", expand=True)

    def mostrar_en_contenido(funcion):
        for widget in contenido_frame.winfo_children():
            widget.destroy()
        funcion(contenido_frame)

    botones_menu = [
        ("Inicio", pantalla_inicio),
        ("Buscar por DNI", formulario_buscar_dni),
        ("Registrar Cliente", formulario_cliente),
        ("Registrar Notificación", formulario_notificacion),
        ("Registrar Caso", formulario_caso),
        ("Registrar Expediente", formulario_expediente),
        ("Registrar Pago", formulario_pago),
    ]

    for texto, funcion in botones_menu:
        tk.Button(menu_frame, text=texto, command=lambda f=funcion: mostrar_en_contenido(f),
                  bg=ESTILOS["color_boton"], fg="white", relief="flat", height=2,
                  font=ESTILOS["fuente_boton"]).pack(fill="x", padx=10, pady=5)

    mostrar_en_contenido(pantalla_inicio)
    verificar_alertas_pendientes()  # 👈 Esto activa las alertas automáticas
    root.mainloop()

if __name__ == "__main__":
    mostrar_login()
