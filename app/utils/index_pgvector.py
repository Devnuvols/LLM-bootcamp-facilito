from typing import List, Dict, Any, Tuple
import os
import json
from functools import reduce
import psycopg2
from .database import get_conn


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



def insert_or_update(vector: Dict[str, Any], hash:str):
    """
    Insert or update the given embedding with metadata in chroma collection.
    Identifier is a hash of its content and metadata.
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:

        temp_content = vector['content'].replace("\x00", "\uFFFD")
        
        upsert_query = """
            INSERT INTO docs (embedding, content, page, name, chunk, hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT unique_name_page_chunk
            DO UPDATE SET embedding = EXCLUDED.embedding, content = EXCLUDED.content, page = EXCLUDED.page, name = EXCLUDED.name, chunk = EXCLUDED.chunk, hash = EXCLUDED.hash;
        """
        cursor.execute(upsert_query, (
            vector['vector'], temp_content, vector['page'], vector['name'], vector['chunk'], hash
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





