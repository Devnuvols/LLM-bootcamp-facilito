
from openai import OpenAI

# Configura tu clave de API de OpenAI
client = OpenAI()

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

    
prompts = [
    "El nuevo avance en inteligencia artificial está revolucionando la tecnología.",
    "hola",
    "gracias",
    "El descubrimiento de agua en Marte abre nuevas posibilidades para la exploración espacial.",
    "Los telescopios espaciales han mejorado nuestra comprensión del universo.",
    "La inteligencia artificial se utiliza en la investigación astronómica para analizar datos.",
    "La nueva misión a Júpiter tiene como objetivo estudiar sus lunas y su atmósfera.",
    "El uso de la inteligencia artificial en la medicina está avanzando rápidamente.",
    "La astrobiología estudia la posibilidad de vida en otros planetas.",
    "El desarrollo de nuevos algoritmos de aprendizaje automático está transformando la tecnología.",
    "Los satélites son fundamentales para la comunicación y la observación de la Tierra.",
    "La exploración del sistema solar ha revelado muchos misterios sobre nuestros vecinos planetarios."
]

tematica = "el sistema solar y planetas, astronomía en general"

for i, prompt in enumerate(prompts):
    resultado = llm_guard(prompt, tematica)
    print("---------")
    print(f"Prompt {i+1}: {prompt}\n")
    if resultado == "sí":
        print(f"Resultado: SI\n")
    else:
        print(f"Resultado: {resultado}\n")
   
