# INTRODUCCION

Chatbot con LLM-RAG desarrollado por Miguel Monllau Monfort.
El objetivo es tener la posibilidad de hacer preguntas sobre documentos técnicos muy densos .

Los usuarios pueden cargar documentos y deben estar en formatos PDF, DOCX, PPTX.

Se realiza la consulta de los datos mediante RAG, utilizando una base de datos vectorial par almacenar los embeddings

Se controla el correcto dialogo mediante prompting, y se usa tambien un sistema de guardarail implementado internamente que verifica si la pregunta es sobre la tematica del chatbot para evitar uso inadecuado

Se almacena el historial de preguntas y respuestas, asi como el feedback indicado por el usuario para fines de mejora.

La interactuacion , o frontend, es mediante entorno webapp.
Para desarrollo en local es con el protocolo http,
y en el entorno de produccion se utiliza el protocolo https, y  se instala un certificado digital.

Esta en desarrollo la version APIREST que permite la interaccion mediante WhatsApp

## FRONTEND

Se usa Streamlit para implementar el Frontend.

## BACKEND


- la database para almacenar los embedings.

- un http server para mostraer los documentos que se han incorporado al RAG (pdfs, docs, ...). 



## REQUISITOS PREVIOS

Necesitaremos una cuenta de OPENAI , y obtener la APIKEY.
Cuenta en Azure, AWS, o servicio cloud que permita levantar una VM en la que clonar el repositorio.


### LLMs

Se ha implementado en el Frontend un selector de LLM para utilizar en el RAG.
Por defecto se utiliza OpenAI, la implementacion de otros LLMs como Gemini, son facilmente incorporables.
Requerira añadir la seleccion en el Front, asi como añadir el codigo especifico en la funcion que realiza la respuesta LLM.
Tambien necesitaremos obtener el API_KEY para el nuevo LLM.

### IMPLEMENTAR EN PRODUCCION

Necesitaremos una VM en el cloud,  en el cual instalaremos una version Linux Ubuntu

Intalaremos Python, la version debe ser la 3.10 o posterior , porque como frontend instalaremos Streamlit.

En nuestro caso lo creamos en Azure.

El acceso a la VM lo realizamos mediante SSH , y para la autenticacion usamos la clave privada que nos descargamos en el momento de crear la VM

### Instalar entorno en VM

#### Python

Para instalar Python 3.10 en Ubuntu, puedes seguir estos pasos:

```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10
```

#### Entorno virtual

Las dependencias, las instalaremos dentro de un entorno virtual:

crear y activar un entorno virtual:

```
python3.10 -m venv /home/azureuser/.venv
source  /home/azureuser/.venv/bin/activate
```

#### CLONAR EL REPOSITORIO EN LA VM

Ejecutamos el comando para clonar el repositorio origen:

```
git clone {url-github-code}
```

Creamos un archivo que ejecutaremos definir las variables de entorno que usa la aplicación y para inicializar la aplicación:

```
nano start_app.sh
````

Este archivo debe contener algo similar a esto:

```
export DOCS_HOST={ip_addres_server}
export DOCS_USER={username}
export DOCS_PASSWORD={userpasswd}
export DOCS_NAME={name database}
export HTTP_HOST={ip_addres_server}
export OPENAI_API_KEY=s{api key}
source .venv/bin/activate
cd chatbot/
nohup python -m http.server 8900 &
nohup streamlit run app/main.py --server.port 8000 --server.headless true --theme.base light &
```

cambiar los permisos de ejecución:

```
chmod +x /home/azureuser/start_app.sh
```

Este archivo es el que se debe ejecutar para arrancar la aplicación.
Es aconsejable configurar la ejecucion automatica como archivo de sistema en el reinicio de la VM


### DATABASE. CREACION DE SERVIDOR POSTGRESQL Y DATABASE VECTORIAL

El chatbot utiliza una base de datos propia para el RAG.
Vamos a ver como poner en funcionamiento el servidor postgresql y la database:

Para crear una base de datos postgresql solo necesitas seguir las
 [instrucciones oficiales para la instalación de postgres]:

 https://www.postgresql.org/download/linux/ubuntu/

 Es importante que la versión de postgres sea la 15 para la base de datos de documentos.

```
sudo sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get -y install postgresql-15
```

Después de eso, el servicio postgresql debería estar ejecutándose. 
Para acceder a él desde Internet, deberá modificar algunos archivos de configuración y abrir el puerto 5432 en el firewall.

Modificaremos el archivo:

`/etc/postgresql/15/main/pg_hba.conf` 

debemos agregar una entrada adicional para permitir todas las IP externas:

```
host    all    all    0.0.0.0/0    md5
````

Otro archive que tendremos que modificar es 

/etc/postgresql/15/main/postgresql.conf

Debemos quitar la marca de comentario de la línea que contiene el parámetro :

`listen_addresses` y configúrelo en `*` en lugar de `localhost`


Ahora necesitaremos instalar la extensión que convierte la base de datos postgresql en una base de datos vectorial:

```
sudo apt install postgresql-15-pgvector
```

Continuaremos con la creación de las bases de datos que vamos a necesitar:

Accedemos al servidor postgresql:

```
sudo -u postgres psql
```

creamos la base de datos:

```
CREATE DATABASE {nombrebasededatos};
```

Accedemos a la base de datos:

```
\c nombrebasededatos
````

Creamos la extensión vectorial:

```
CREATE EXTENSION vector;
```

Creamos el user admin para la base de datos:

```
CREATE USER usuarioadmin WITH PASSWORD 'USER_PASSWORD';
ALTER USER usuarioadmin WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE facilito TO usuarioadmin;
````

Creamos tabla para los embeddings (usaremos 1536 dimensiones para los vectores):

```
CREATE TABLE IF NOT EXISTS docs (
    content TEXT,
    page INT,
    name VARCHAR(255),
    chunk INT,
    embedding vector(1536),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    hash VARCHAR(255) NOT NULL
);
ALTER TABLE docs ADD CONSTRAINT unique_name_page_chunk UNIQUE (name, page, chunk);
````

Creamos la tabla para el historial:

```
CREATE TABLE IF NOT EXISTS history (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    chat_id INT NOT NULL,
    feedback INT
);
````

Modificamos el password por defecto para el usuario postgres:

```
ALTER USER postgres PASSWORD 'new_password';
```

## Servidor de archivos en maquina VM

Para visualizar los archivos PDF simplemente deje funcionando un servidor http en el puerto 8900:

```
python -m http.server 8900
```


## PERSONALIZACION Chatbot

Para poder probrar , se pueden usar los documentos PDF del directorio  "docs_pdf".
Este directorio contiene pdfs descargados de Wikipedia, sobre el sistema solar.

Personalizacemos el prompt , indicando que es un asistente experto en astronbomia y el sistema solar,

y posteriormente se procedera a incorporar estos documentos como base de conocimiento.

Una vez incorporados , podremos empezar a realizar preguntas al chatbot-

### Tematica chatbot

En el prompt se indica la tematica del chatbot, este parametro se usa en la comprocacion interna antes de procesar cada pregunta.

### Aspecto Frontend 
La personalizacion en el aspecto se puede modificar editanto los archivos de Streamlit: config.yml, las imagenes en el directorio images.

### Paginas frontend

la pagina principal del frontend es main.py. 

Esta pagina contiene la logica y los elementos del chatbot

La pagina  pages\2_upload.py es para cargar nuevos documentos de conocimiento, ver los documentos que se han subido y eliminarlos si se desea, asi como abrir el documento para visualizarlo.




