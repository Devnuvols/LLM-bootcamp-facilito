# Import Guard and Validator
# 
#pip install guardrails --no-deps
#pip install codecov==2.1.13

# guardrails hub install hub://guardrails/unusual_prompt

from guardrails.hub import UnusualPrompt
from guardrails import Guard
import openai

# Supongamos que esta es tu función que llama al modelo LLM
def LLM_bot(history):
    return openai.chat.completions.create(
        prompt=history,
        temperature=0.3,
        max_tokens=100,
    )

# Inicializar el objeto Guard con el validador UnusualPrompt
guard = Guard().use(UnusualPrompt, on="prompt", on_fail="exception")

while True:
    # Pedir entrada de texto al usuario
    history = input("Por favor, ingresa el prompt a validar (o 'salir' para terminar): ")

    # Permitir salir del bucle
    if history.lower() == 'salir':
        break

    try:
        # Utilizar el guardián para validar el prompt antes de llamar a LLM_bot
        res = guard(LLM_bot, prompt=history)
        # Si pasa la validación, se ejecuta LLM_bot y se obtiene la respuesta
        print("Respuesta del LLM_bot:", res)
    except Exception as e:
        # Si falla la validación, se maneja la excepción
        print("Error:", e)