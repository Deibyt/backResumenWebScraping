Puesta en Marcha del Proyecto Django
====================================

Este documento proporciona una guía paso a paso para configurar y ejecutar el proyecto Django localmente.

Requisitos previos
------------------
Asegúrese de tener instalado Python 3.10.11 antes de comenzar.

Pasos para la configuración
--------------------------

1. Creación y activación del entorno virtual
   Se debe crear un entorno virtual para manejar las dependencias de forma aislada. Utilice los siguientes comandos para crear y activar el entorno:

   .. code-block:: bash

      # Crear el entorno virtual
      python3 -m venv venv

      # Activar el entorno virtual en Windows
      .\\venv\\Scripts\\activate

      # Activar el entorno virtual en Unix o MacOS
      source venv/bin/activate

2. Instalación de dependencias
   Una vez activado el entorno virtual, instale las dependencias necesarias que se encuentran en el archivo ``requirements.txt``:

   .. code-block:: bash

      pip install -r requirements.txt

3. Acceso a la carpeta del proyecto
   Cambie al directorio del proyecto donde se encuentran los archivos de Django:

   .. code-block:: bash

      cd car_reviews

4. Ejecución del proyecto
   Finalmente, ejecute el servidor de desarrollo de Django con el siguiente comando:

   .. code-block:: bash

      python manage.py runserver

Siguiendo estos pasos, el proyecto Django debería estar corriendo localmente y accesible a través del navegador en ``http://127.0.0.1:8000``.
