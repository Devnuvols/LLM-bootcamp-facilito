
from typing import List, Dict, Any, Tuple
from functools import reduce
import json
import os
import psycopg2
from psycopg2._psycopg import connection

def get_conn() -> connection:
    """
    Connection to documents database.
    """
    return psycopg2.connect(
        host=os.environ.get('DOCS_HOST', ''),
        database=os.environ.get('DOCS_NAME', ''),
        user=os.environ.get('DOCS_USER',''),
        password=os.environ.get('DOCS_PASSWORD', '')
    )

def insert_QA(query: str, answer: str):
    """Inserts query into table history"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        sqlquery = """
            INSERT INTO history (query, answer)
            VALUES (%s, %s)
        """
        cursor.execute(sqlquery, (query, answer))
        conn.commit()
    except Exception as e:
        conn.rollback()  # En caso de error, realiza un rollback
        print(f"Error al insertar en la base de datos: {e}")
    finally:
        cursor.close()
        conn.close()


def update_QA_feedback(feedback: str, n: int):
    """Adds feedback to message in history database"""
    
    conn = get_conn()
    cursor = conn.cursor()
    try:
        sqlquery = """
            SELECT id
            FROM history
            ORDER BY timestamp ASC
            LIMIT 1 OFFSET %s;
        """
        cursor.execute(sqlquery, (int(n/2)-1,))
        msg_id = cursor.fetchone()[0]
        # Then update the message
        sqlquery = """
            UPDATE history
            SET feedback = %s
            WHERE id = %s;
        """
        mapping = {'👍': 1, '👎': -1}
        cursor.execute(sqlquery, (mapping[feedback], msg_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def read_vectors(emb_path: str) -> Tuple[List[Dict[str, Any]], int]:
    """
    Reads embeddings and metadata in the format saved by pdf2emb.py.
    If a file is provided just read the file.
    If a folder is provided it recursively reads all json files in it.
    """
    vectors = []
    if os.path.isdir(emb_path):
        for root, dir, files in os.walk(emb_path):
            for file in files:
                if os.path.splitext(file)[1].lower() == '.json':
                    with open(os.path.join(root, file), 'r') as f:
                        new_vectors = json.load(f)
                        vectors.extend(new_vectors)
    else:
        assert os.path.splitext(emb_path)[1].lower() == '.json', 'Embeddings must be json.'
        with open(os.path.join(root, file), 'r') as f:
            new_vectors = json.load(f)
            vectors.extend(new_vectors)
    assert len(vectors) > 0, 'No valid embeddings found.'
    return vectors



def insert_or_update(vector: Dict[str, Any], metadata: Dict[str, Any]):
    """
    Insert or update the given embedding with metadata in chroma collection.
    Identifier is a hash of its content and metadata.
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:

        temp_content = vector['content'].replace("\x00", "\uFFFD")
        
        upsert_query = """
            INSERT INTO docs (embedding, content, page, name, chunk""" + reduce(lambda x,y: x+y,[', ' + x for x in metadata.keys()]) + """)
            VALUES (%s, %s, %s, %s, %s""" + reduce(lambda x,y: x+y,[', %s' for x in metadata.keys()]) + """)
            ON CONFLICT ON CONSTRAINT unique_name_page_chunk
            DO UPDATE SET embedding = EXCLUDED.embedding, content = EXCLUDED.content, page = EXCLUDED.page, name = EXCLUDED.name, chunk = EXCLUDED.chunk"""\
                + reduce(lambda x,y: x+y,[', ' + x + ' = EXCLUDED.' + x for x in metadata.keys()]) + """;
        """
        cursor.execute(upsert_query, (
            vector['vector'], vector['content'].replace("\x00", "\uFFFD"), vector['page'], vector['name'], vector['chunk'],
            *metadata.values()
        ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def check_hash(hash: str) -> bool:
    conn = get_conn()
    cursor = conn.cursor()
    try:
        select_query = "SELECT 1 FROM docs WHERE hash = %s"
        cursor.execute(select_query, (hash,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()

def delete_docs(hashes: List[str]):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM docs WHERE hash = ANY(%s);"
        cursor.execute(query, (hashes,))
        conn.commit()
    except psycopg2.DatabaseError as error:
        print(f"Error: {error}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()





