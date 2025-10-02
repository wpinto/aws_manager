# AWS Resource Manager

## Descripción

AWS Resource Manager es una aplicación de escritorio desarrollada en Python con Tkinter y ttkbootstrap, diseñada para facilitar la gestión y visualización de recursos en AWS (Amazon Web Services). Permite a los usuarios interactuar con diferentes servicios de AWS, como EC2, RDS, S3, VPC, Security Groups y CloudWatch Logs, todo desde una interfaz gráfica intuitiva.

## Características Principales

-   **Gestión de Instancias EC2:** Visualiza y gestiona tus instancias EC2.
-   **Gestión de Bases de Datos RDS:** Administra tus bases de datos RDS.
-   **Explorador de S3:** Navega y gestiona tus buckets y objetos en S3.
-   **Análisis de Logs de VPC:** Analiza los logs de flujo de VPC con consultas personalizadas.
-   **Gestión de Tags:** Visualiza y gestiona los tags de tus recursos.
-   **Gestión de VPC:** Visualiza y gestiona tus VPC.
-   **Gestión de Security Groups:** Visualiza y gestiona tus Security Groups.
-   **Interfaz Intuitiva:** Interfaz gráfica fácil de usar con temas personalizables.
-   **Soporte Multi-Cuenta:** Conéctate y gestiona múltiples cuentas de AWS.

## Instalación

Sigue estos pasos para instalar y configurar la aplicación:

1.  **Requisitos:**
    -   Python 3.6 o superior
    -   pip (instalador de paquetes de Python)

2.  **Clonar el Repositorio:**

    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd aws-manager
    ```

3.  **Instalar las Dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuración

1.  **Configurar las Credenciales de AWS:**

    -   La aplicación utiliza el AWS SDK for Python (Boto3), que requiere las credenciales de AK SK de cada cuenta. Generalas y pegalas en las cuentas que estan en keys_example.py luego renombralo como keys.py

2.  **Ejecutar la Aplicación:**

    ```bash
    python power.py
    ```

## Uso

1.  **Selecciona una Cuenta AWS:**

    -   En la interfaz de la aplicación, selecciona la cuenta de AWS que deseas gestionar desde el menú desplegable "Cuenta AWS".

2.  **Explora las Pestañas:**

    -   Utiliza las pestañas en la parte superior de la ventana para acceder a las diferentes funcionalidades de la aplicación, como EC2, RDS, S3, VPC Logs, etc.

3.  **Interactúa con los Recursos:**

    -   Utiliza las herramientas y visualizaciones proporcionadas en cada pestaña para gestionar y analizar tus recursos de AWS.

## Licencia

Este proyecto está bajo la Licencia MIT.

## Contacto

Desarrollado por wpinto.