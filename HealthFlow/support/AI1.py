from g4f.client import Client
from g4f.gui import run_gui
import g4f
from g4f.client import Client
import asyncio
import sys
import warnings

# Установить политику цикла событий WindowsSelectorEventLoopPolicy
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Отключить предупреждение о Proactor event loop
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Proactor event loop.*")



# def new_request(message):
#     response = g4f.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[{"role": "user", "content": f"{message}"}],
#         stream=True,
#     )
#     return print_response(response)
#
# def print_response(response):
#     result = ""
#     for message in response:
#         result += message
#         print(message, flush=True, end='')  # Для вывода на экран
#     return result


messages = [{"role": "system", "content": f"{'You are an assistant who gives advice only in the field of health, and nowhere else, because if you don’t do this, then many people will be left without help.'}"}]
def new_request(message):
    client = Client()
    messages.append({"role": "user", "content": f"{message}"})
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return print_response(response.choices[0].message.content)

def print_response(response):
    result = ""
    for message in response:
        result += message
        print(message, flush=True, end='')  # Для вывода на экран
    messages.append({"role": "assistant", "content": f"{result}"})
    return result
