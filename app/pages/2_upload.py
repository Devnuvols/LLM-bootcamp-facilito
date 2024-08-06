import streamlit as st
import os
import time
import yaml
from yaml.loader import SafeLoader
import hashlib

from st_pages import show_pages, Page, hide_pages
from utils.embeddings import process_file, save
from utils.index_pgvector import insert_or_update, check_hash
from utils.database import get_conn, delete_docs
import pandas as pd
from sqlalchemy import create_engine



# Leer el archivo de configuración yaml
with open('./app/config.yml', 'r') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Configurar la página
st.set_page_config(
    layout='wide',
    page_title=config['upload']['tab_title'],
    page_icon=config['upload']['page_icon'],
)

# Mostrar las páginas
show_pages(
    [
        Page("app/main.py", "Chatbot", "🤖"),
        Page("app/pages/2_upload.py", "Documentos", "📄"),

    ]
)
# comprobar si el directorio local_storage existe, si no, crearlo
if 'init_local_storage' not in st.session_state:
            st.session_state.init_local_storage = True
            os.makedirs('local_storage/pdf/', exist_ok=True)
            os.makedirs('local_storage/json/', exist_ok=True)

if uploaded_file := st.file_uploader('SUBIR LOS DOCUMENTOS AQUI....', type=['pdf','docx', 'pptx']):
    # Mostrar la barra de progreso
    progress_text = "Uploading file..."
    my_bar = st.progress(0, text=progress_text)
    

    # Guardar el archivo cargado  
    with open(os.path.join('local_storage/pdf', uploaded_file.name), "wb") as f:
        f.write(uploaded_file.read())
    with open(os.path.join('local_storage/pdf', uploaded_file.name), "rb") as f:
        hash = hashlib.sha256(f.read()).hexdigest()
        print(hash, flush=True)
    my_bar.progress(100, text=progress_text)
    my_bar.progress(0, text='Checking duplicates')
    is_duplicate = check_hash(hash)
    my_bar.progress(100, text='Checking duplicates')
    if is_duplicate:
        st.error('The file is already uploaded.')
        my_bar.empty()
    else:
        # Indexar el contenido en la base de datos
        my_bar.progress(0, text='Indexing document.')
        file_path = os.path.join('local_storage/pdf', uploaded_file.name)
        print(f"mmmmmmm-------el archivo:{file_path}", flush=True)

        vectors = process_file(file_path, 'openai')
        
        print("--------MMMMM------------")
        save(vectors, os.path.join('local_storage/json', os.path.splitext(uploaded_file.name)[0] + '.json'))
        my_bar.progress(0, text='Indexing vectors in the database.')
        for k, vector in enumerate(vectors):
            insert_or_update(vector, hash)
            my_bar.progress(k / len(vectors), text='Indexing vectors in the database.')
            time.sleep(0.1)
            my_bar.empty()

        # Informar al usuario que el proceso ha finalizado
        st.success(f"The file '{uploaded_file.name}' has been saved successfully.")
        # Vaciar el cargador de archivos
        uploaded_file = None

# La eliminación de documentos
if st.button('Delete'):
    if 'new_df' in st.session_state:
        remove_indices = list(st.session_state['new_df']['edited_rows'].keys())
        remove_indices = list(filter(
            lambda x: 'Mark for deletion' in st.session_state['new_df']['edited_rows'][x] and st.session_state['new_df']['edited_rows'][x]['Mark for deletion'],
            remove_indices))
        tmp_df = st.session_state['curr_df']
        hashes = list(tmp_df.iloc[remove_indices]['hash'])
        delete_docs(hashes)

# Consultar y mostrar datos de la base de datos
conn = get_conn()
try:
    query = """
    SELECT name, MAX(timestamp) as timestamp, hash
    FROM docs
    GROUP BY name, hash;
    """
    engine = create_engine('postgresql+psycopg2://', creator=lambda: conn)
    df = pd.read_sql_query(query, engine)
except Exception as e:
    st.error(f"Error al ejecutar la consulta: {e}")
    df = pd.DataFrame()  # Definir un DataFrame vacío en caso de error
finally:
    conn.close()

if not df.empty:
    df.fillna('-', inplace=True)

    pdf_ip = os.environ.get('HTTP_HOST', 'localhost')
    df['name'] = df['name'].apply(lambda x: x.replace('local_storage/pdf/', ''))
    df['url'] = df['name'].apply(lambda x: f'http://{pdf_ip}/downloads/' + x)

    
    if 'Mark for deletion' not in df.columns:
            df['Mark for deletion'] = False
    
    st.session_state['curr_df'] = df.copy()
    
    if 'filter_name' in st.session_state and st.session_state['filter_name'] is not None:
        df = df[df['name'].str.contains(st.session_state['filter_name'])]

    st.session_state['curr_df'] = df.copy()

    column_mapping = {
        'Name': 'name',
        'Timestamp': 'timestamp',
        'Url': 'url',
        'Mark for deletion': 'Mark for deletion'
    }

    cols_display = ['Mark for deletion', 'Name', 'Timestamp', 'Url']
    cols_db = [column_mapping[col] for col in cols_display if col in column_mapping]

    changed_w = st.data_editor(
        df[cols_db].rename(columns=column_mapping),
        hide_index=True, 
        key='new_df',
        column_config={
            'name': st.column_config.Column(label="Name", disabled=True),
            'timestamp': st.column_config.DatetimeColumn(label="Timestamp", disabled=True),
            'url': st.column_config.LinkColumn(label="Url", disabled=True)
        }
    )
    
    changed = changed_w.copy()
    changed['hash'] = df['hash'].values

    if not changed_w.equals(df[cols_db].rename(columns=column_mapping)):
        changed = changed_w.rename(columns={k: v for k, v in column_mapping.items()})
else:
    st.write("No hay datos disponibles para mostrar.")
    changed_w = pd.DataFrame()  # Definir un DataFrame vacío para changed_w si no hay datos

# Aquí puedes agregar cualquier lógica adicional necesaria para cuando no hay datos disponibles