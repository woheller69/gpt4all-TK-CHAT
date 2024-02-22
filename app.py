#!/usr/bin/env python3
"""GPT4All CLI

The GPT4All CLI is a self-contained script based on the `gpt4all` and `typer` packages. It offers a
REPL to communicate with a language model similar to the chat GUI application, but more basic.
"""

import importlib.metadata
import io
import sys
from collections import namedtuple
from typing_extensions import Annotated

import typer
from gpt4all import GPT4All
from pynput import keyboard

MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello there."},
    {"role": "assistant", "content": "Hi, how can I help you?"},
]

SPECIAL_COMMANDS = {
    "/reset": lambda messages: messages.clear(),
    "/exit": lambda _: sys.exit(),
    "/clear": lambda _: print("\n" * 100),
    "/help": lambda _: print("Special commands: /reset, /exit, /help and /clear. Press SPACE to stop inference.\n"),
}

VersionInfo = namedtuple('VersionInfo', ['major', 'minor', 'micro'])
VERSION_INFO = VersionInfo(1, 0, 2)
VERSION = '.'.join(map(str, VERSION_INFO))  # convert to string form, like: '1.2.3'

CLI_START_MESSAGE = f"""
    
 ██████  ██████  ████████ ██   ██  █████  ██      ██      
██       ██   ██    ██    ██   ██ ██   ██ ██      ██      
██   ███ ██████     ██    ███████ ███████ ██      ██      
██    ██ ██         ██         ██ ██   ██ ██      ██      
 ██████  ██         ██         ██ ██   ██ ███████ ███████ 
                                                          

Welcome to the GPT4All CLI! Version {VERSION}
Type /help for special commands.
                                                    
"""

# create typer app
app = typer.Typer()

def repl(
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Model to use for chatbot"),
    ] = None,
    n_threads: Annotated[
        int,
        typer.Option("--n-threads", "-t", help="Number of threads to use for chatbot"),
    ] = None,
    device: Annotated[
        str,
        typer.Option("--device", "-d", help="Device to use for chatbot, e.g. gpu, amd, nvidia, intel. Defaults to CPU."),
    ] = None,
    prompt: Annotated[
        str,
        typer.Option("--prompt", "-p", help="Text to inserted into the prompt template for the chatbot"),
    ] = "",
    sysprompt: Annotated[
        str,
        typer.Option("--sysprompt", "-s", help="System prompt to use for chatbot"),
    ] = "",
):
    """The CLI read-eval-print loop."""
    
    if model is None:
        print("Specify model with --model or -m")
        quit()
        
    gpt4all_instance = GPT4All(model, device=device, allow_download=False)

    # if threads are passed, set them
    if n_threads is not None:
        num_threads = gpt4all_instance.model.thread_count()
        print(f"\nAdjusted: {num_threads} →", end="")

        # set number of threads
        gpt4all_instance.model.set_thread_count(n_threads)

        num_threads = gpt4all_instance.model.thread_count()
        print(f" {num_threads} threads", end="", flush=True)
    else:
        print(f"\nUsing {gpt4all_instance.model.thread_count()} threads", end="")

    print(CLI_START_MESSAGE)
    print(f"Model {model}")

    _new_loop(gpt4all_instance, prompt, sysprompt)


def _new_loop(gpt4all_instance, prompt, sysprompt):

    with gpt4all_instance.chat_session(sysprompt):
        assert gpt4all_instance.current_chat_session[0]['role'] == 'system'
        print("System prompt template:", repr(gpt4all_instance.current_chat_session[0]['content']))
        print("Prompt template:", repr(gpt4all_instance._current_prompt_template))
        print("Prompt insertion:", prompt)
        
        listener = keyboard.Listener(
            on_press=on_press_esc)
        listener.start()
        while True:
            user_input = input(" ⇢  ")
            global esc_pressed
            esc_pressed = False
            # Check if special command and take action
            for command in SPECIAL_COMMANDS:
                if user_input.endswith(command):
                    SPECIAL_COMMANDS[command](MESSAGES)
                    break
            else:
                # If regular message, append to messages
                message = prompt + user_input
                MESSAGES.append({"role": "user", "content": message})
                # execute chat completion and ignore the full response since 
                # we are outputting it incrementally
                response_generator = gpt4all_instance.generate(
                    message,
                    # preferential kwargs for chat ux
                    max_tokens=20000,
                    temp=0.7,
                    top_k=40,
                    top_p=0.4,
                    repeat_penalty=1.18,
                    repeat_last_n=64,
                    n_batch=128,
                    # required kwargs for cli ux (incremental response)
                    streaming=True,
                    callback=stop_on_token_callback,
                )
                response = io.StringIO()
                for token in response_generator:
                    print(token, end='', flush=True)
                    response.write(token)

                # record assistant's response to messages
                response_message = {'role': 'assistant', 'content': response.getvalue()}
                response.close()
                gpt4all_instance.current_chat_session.append(response_message)
                MESSAGES.append(response_message)
                print() # newline before next prompt

        
def on_press_esc(key):
    global esc_pressed	
    if key == keyboard.Key.space:
        esc_pressed = True
     
            
# Callback function from GPT-4all
def stop_on_token_callback(token_id, token_string):
    global esc_pressed

    if esc_pressed:
        return False
    else:
        return True

if __name__ == "__main__":
    typer.run(repl)
