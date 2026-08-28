## MVP

### 1. Autenticación y Gestión de Sesiones

Backend: Implementar el estándar OAuth2 con JWT (JSON Web Tokens) nativo de FastAPI.

Flujo: El usuario envía credenciales al endpoint /token. FastAPI valida contra PostgreSQL, genera un token JWT y el frontend lo guarda. Todas las peticiones subsecuentes llevan este token en el header para que cada dataset y modelo quede asociado al user_id.

### 2. Ingesta de Datos (Upload)

Acción: El usuario arrastra un CSV.

Backend: FastAPI recibe el archivo con UploadFile. Lo guarda en un directorio local (ej. /datasets/user_123/raw_data.csv).

Análisis inicial: FastAPI lee el archivo con Pandas, extrae los nombres de las columnas, tipos de datos (numérico, categórico) y cantidad de valores nulos.

Respuesta: Devuelve un JSON al frontend con este perfil de datos para construir la interfaz.

### 3. Tratamiento Interactivo (Limpieza con Clicks)

Interfaz: El frontend muestra una tabla con las columnas y botones de acción.

Acción: El usuario hace clicks: "Eliminar columna 'ID'", "Rellenar nulos de 'Edad' con la media", "Definir 'Precio' como variable objetivo".

Backend: Al confirmar, el frontend envía un JSON de configuración al endpoint /api/clean. FastAPI toma ese JSON, aplica las transformaciones a través de un pipeline de Pandas/Scikit-learn, y guarda un nuevo archivo: clean_data.csv.

### 4. Entrenamiento Asíncrono

Acción: El usuario elige el modelo (ej. Random Forest o FFN en PyTorch) y ajusta hiperparámetros básicos.

Backend: Se crea un registro en la tabla Jobs con estado Pending. FastAPI usa BackgroundTasks para iniciar el entrenamiento sin dejar al usuario esperando.

Proceso: El worker lee clean_data.csv, entrena, calcula métricas (Accuracy, F1), guarda el archivo del modelo (.joblib o .pt en /models/user_123/) y actualiza la base de datos a estado Success.

### 5. Despliegue (El "Deploy")

Acción: El usuario ve que el modelo terminó y hace click en "Desplegar".

Backend (MVP): La forma más viable es el Enrutamiento Dinámico. En lugar de levantar contenedores Docker complejos al inicio, tu misma API de FastAPI tiene un endpoint /api/predict/{model_id}. Cuando recibe una petición, busca el modelo en disco, lo carga en memoria, hace la inferencia con los datos enviados en el body, y devuelve la predicción. (Más adelante puedes evolucionarlo a generación de contenedores Docker individuales).