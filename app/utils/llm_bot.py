from typing import List, Dict, Any, Iterable
from openai import OpenAI
from unidecode import unidecode
import os
import re
from .database import get_conn

client = OpenAI()

def echo_bot(msg):
    return 'Echo: {}'.format(msg)

def chat_llm(history: List[Dict[str, str]],llm:str) -> Iterable[str]:
    """
    Uses the ChatCompletion API with the given messages.
    """
    print('llm:',llm)
    if llm.lower() == 'openai':
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=history,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
   
def llm_guard(prompt:str, tematica:str)->str:
    messages = [
        {"role": "system", "content": "Eres un asistente que ayuda a verificar la temática de los textos."},
        {"role": "user", "content": f"Clasifica el siguiente texto en la temática '{tematica}':\n\nTexto: \"{prompt}\"\n\n¿El texto corresponde a la temática '{tematica}'? Responde 'sí' o 'no' . Si la respuesta es no, proporciona una breve explicación."}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.2,
    )
    respuesta_completa = response.choices[0].message.content
    return respuesta_completa

   
def get_embedding(txt: str) -> List[float]:
    """
    Preprocess the query with chatgpt before embedding it.
    """

    text = txt.replace("\n", " ")
    hyde_prompt = """You will be given a sentence.
If the sentence is a question, convert it to a plausible answer.
If the sentence does not contain a question,
just repeat the sentence as is without adding anything to it.

Examples:
- what furniture there is in my room? --> In my room there is a bed,
a wardrobe and a desk with my computer
- where did you go today --> today I was at school
- I like ice cream --> I like ice cream
- how old is Jack --> Jack is 20 years old"""
    prompt = """
Sentence:
- {input} --> """ + text
    history = [
        {"role": "system", "content": hyde_prompt},
        {"role": "user", "content": prompt},
    ]
  
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=history,
        temperature=0.2
    )
    response = response.choices[0].message.content
    query = text + ' ' + response
    return_response = client.embeddings.create(input=[query], model='text-embedding-3-small').data[0].embedding
   
    return return_response

def get_context(prompt: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Retrieves the most similar document chunk with its metadata in a dictionary.
    """
    conn = get_conn()
    cursor = conn.cursor()
    try:
        query_emb = get_embedding(prompt)
   
        command = f"SELECT * FROM docs ORDER BY embedding <-> '{query_emb}' LIMIT 5;"
        cursor.execute(command)
        
        colnames = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        
        nearests = [{k: v for k, v in zip(colnames, result)} for result in results]
        nearests_txt = '\n\n'.join([row['content'] + ' La URL / enlace es: ' + to_url(row['name'], row['page']) for row in nearests])
                
    finally:
        cursor.close()
        conn.close()
    return nearests_txt

def normalize_str(a: str) -> str:
    """Removes all non-alphanumerical characters"""
    pattern = re.compile('[\W_]+')
    return unidecode(pattern.sub('', a))

def get_next_word(sentence: str, target_words: List[str]) -> str:
    """
    Finds the next word in the sentence after the target word.
    Assumes the target word appears only once in the sentence.
    """
    words = sentence.split()
    for i in range(len(words) - 1):
        if words[i] in target_words:
            return words[i + 1]
    return 'all'


def to_url(name: str, page: int) -> str:
    """Parses name and page into url from http server of pdfs."""
    name = name.replace(" ", "%20").replace('local_storage/pdf/', '')
    
    pdf_ip = os.environ.get('HTTP_HOST', 'localhost')
    access_url = f'https://' + pdf_ip + '/downloads/' + name + '#page=' + str(page)
    return access_url
