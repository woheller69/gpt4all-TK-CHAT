#!/usr/bin/env python3
"""GPT4All TK GUI

The GPT4All TK GUI is a self-contained script based on the `gpt4all` and `typer` packages. It offers a
REPL to communicate with a language model similar to the chat GUI application, but more basic.
"""

import os
import importlib.metadata
import io
import sys
from collections import namedtuple
from typing_extensions import Annotated

import typer
from gpt4all import GPT4All
import tkinter as tk
from tkinter import scrolledtext
import threading
gpt4all_instance = None
prompt = None
sysprompt = None
output_window = None
input_text = None

VersionInfo = namedtuple('VersionInfo', ['major', 'minor', 'micro'])
VERSION_INFO = VersionInfo(1, 0, 0)
VERSION = '.'.join(map(str, VERSION_INFO))  # convert to string form, like: '1.2.3'

CLI_START_MESSAGE = f"""
    
 ██████  ██████  ████████ ██   ██  █████  ██      ██      
██       ██   ██    ██    ██   ██ ██   ██ ██      ██      
██   ███ ██████     ██    ███████ ███████ ██      ██      
██    ██ ██         ██         ██ ██   ██ ██      ██      
 ██████  ██         ██         ██ ██   ██ ███████ ███████ 
                                                          

Welcome to the GPT4All TK GUI Version {VERSION}
                                                    
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
    global gpt4all_instance
    global mPrompt
    global mSysprompt
    global output_window
    mPrompt = prompt
    mSysprompt = sysprompt
    
    if model is None:
        print("Specify model with --model or -m")
        quit()
        
    """The CLI read-eval-print loop."""
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

    output_window.insert(tk.END, CLI_START_MESSAGE)
    output_window.insert(tk.END, "\nModel: "+model)

    with gpt4all_instance.chat_session(sysprompt):
        assert gpt4all_instance.current_chat_session[0]['role'] == 'system'
        output_window.insert(tk.END, "\nSystem prompt: " + repr(gpt4all_instance.current_chat_session[0]['content']))
        output_window.insert(tk.END, "\nPrompt template: " + repr(gpt4all_instance._current_prompt_template))
        output_window.insert(tk.END, "\nPrompt insertion: " + prompt)
        output_window.insert(tk.END, "\n\n")
        
        root.mainloop()


def inference(gpt4all_instance, prompt, user_input):
    global output_window

    global esc_pressed
    esc_pressed = False
        
    message = prompt + user_input
    # execute chat completion and ignore the full response since 
    # we are outputting it incrementally
    output_window.insert(tk.END, "\n<<<<<<<<<<< AI <<<<<<<<<<<\n\n")
    output_window.yview(tk.END) 
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
        output_window.insert(tk.END, token)
        output_window.yview(tk.END)
        response.write(token)
        root.update_idletasks()
        
    output_window.insert(tk.END, "\n\n<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n")
    output_window.yview(tk.END)    
    response_message = {'role': 'assistant', 'content': response.getvalue()}
    response.close()
    gpt4all_instance.current_chat_session.append(response_message)

def inference_thread():
    global gpt4all_instance
    global mPrompt
    global input_text
    global output_window
    # Copy and paste into output window
    output_window.insert(tk.END, "\n>>>>>>>>>> USER >>>>>>>>>>\n\n")
    output_window.insert(tk.END, input_text.get("1.0", "end-1c"))
    output_window.insert(tk.END, "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")
    output_window.yview(tk.END) 
    message = input_text.get("1.0", "end-1c")
    input_text.delete("1.0", "end") 
    inference(gpt4all_instance, mPrompt, message)


def generate():
    newthread = threading.Thread(target=inference_thread)
    newthread.start()

def stop():
    global esc_pressed 
    esc_pressed = True
    
def exit():
    quit()
    
def newchat():
    python = sys.executable
    os.execl(python, python, *sys.argv)

    
            
# Callback function from GPT-4all
def stop_on_token_callback(token_id, token_string):
    global esc_pressed

    if esc_pressed:
        return False
    else:
        return True


def check_for_updates():
    app()

if __name__ == "__main__":
    # Setup Tkinter GUI
    root = tk.Tk()
    root.title('GPT4ALL TK GUI')
    root.geometry("1024x768")

    input_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=5)
    input_text.pack(side='bottom', fill='both', expand=True)

    output_window = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    output_window.pack(side='top', fill='both', expand=True)

    generate_button = tk.Button(root, text="Generate", command=generate)
    stop_button = tk.Button(root, text="Stop", command=stop)
    exit_button = tk.Button(root, text="Exit", command=exit)
    newchat_button = tk.Button(root, text="New Chat", command=newchat)

    generate_button.pack(side='left', padx=(20, 0))
    stop_button.pack(side='left', padx=(20, 0))
    exit_button.pack(side='right', padx=(0, 20))
    newchat_button.pack(side='right', padx=(0, 20))

    typer.run(repl)

