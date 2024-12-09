#!/usr/bin/env python3

import os
import io
import sys
import typer
from gpt4all import GPT4All
import tkinter as tk
from tkinter import scrolledtext
from typing_extensions import Annotated
import threading
import time


CLI_START_MESSAGE = f"""
    
 ██████  ██████  ████████ ██   ██  █████  ██      ██      
██       ██   ██    ██    ██   ██ ██   ██ ██      ██      
██   ███ ██████     ██    ███████ ███████ ██      ██      
██    ██ ██         ██         ██ ██   ██ ██      ██      
 ██████  ██         ██         ██ ██   ██ ███████ ███████ 
                                                          
                                                    
"""

class ChatGUI:
    def __init__(self):
        self.model_path = None
        self.gpt4all_instance = None
        self.sysprompt = ""
        self.threads = 0
        self.context = 0
        self.prompt = None
        self.device = None
        self.output_window = None
        self.input_text = None
        self.esc_pressed = False
        self.root = None
        self.inference_thread = None
        self.chatsession = None
        self.temperature = 0

    def opt(self,
        model: Annotated[str, typer.Option("--model", "-m", help="Model to use for chatbot")] = None,
        n_threads: Annotated[int, typer.Option("--n-threads", "-t", help="Number of threads to use for chatbot")] = None,
        temperature: Annotated[float, typer.Option("--temperature", help="Temperature to use for chatbot")] = 0.65,
        device: Annotated[str, typer.Option("--device", "-d", help="Device to use for chatbot, e.g. gpu, amd, nvidia, intel. Defaults to CPU.")] = None,
        prompt: Annotated[str, typer.Option("--prompt", "-p", help="Prompt template for the chatbot. Placeholder for user input: {0} ")] = None,
        sysprompt: Annotated[str, typer.Option("--sysprompt", "-s", help="System prompt to use for chatbot")] = "",
        ctx: Annotated[int, typer.Option("--context-length", "-c", help="Context length"),] = 2048):
      
        if model is None:
            print("Specify model with --model or -m")
            quit()      
      
        self.sysprompt = sysprompt
        self.prompt = prompt
        self.context = ctx
        self.threads = n_threads
        self.device = device
        self.model_path = model
        self.temperature = temperature

        self.run()
    
    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title('LLAMA TK GUI')
        self.root.geometry("1024x768")

        self.input_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=5)
        self.input_text.pack(side='bottom', fill='both', expand=True)

        self.output_window = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.output_window.pack(side='top', fill='both', expand=True)

        generate_button = tk.Button(self.root, text="Generate", command=self.generate)
        stop_button = tk.Button(self.root, text="Stop", command=self.stop)
        exit_button = tk.Button(self.root, text="Exit", command=self.root.destroy)
        newchat_button = tk.Button(self.root, text="New Chat", command=self.newchat)

        generate_button.pack(side='left', padx=(20, 0))
        stop_button.pack(side='left', padx=(20, 0))
        exit_button.pack(side='right', padx=(0, 20))
        newchat_button.pack(side='right', padx=(0, 20))
        
        self.gpt4all_instance = GPT4All(self.model_path, device=self.device, allow_download=False, n_ctx=self.context)
        # if threads are passed, set them
        if self.threads is not None:
            self.gpt4all_instance.model.set_thread_count(self.threads)
    
        self.new_chat_session()
        
        self.root.mainloop()
        
    def new_chat_session(self):   
        if self.chatsession is not None:
            self.chatsession.__exit__(None, None, None)
            
        if self.prompt is None:
            self.chatsession = self.gpt4all_instance.chat_session(self.sysprompt)
        else:
            self.chatsession = self.gpt4all_instance.chat_session(self.sysprompt, self.prompt)
        
        self.chatsession.__enter__()
        self.output_window.delete('1.0', tk.END)
        self.output_window.insert(tk.END, CLI_START_MESSAGE)
        self.output_window.insert(tk.END, "\nModel: " + self.model_path)
        self.output_window.insert(tk.END, "\nUsing " + repr(self.gpt4all_instance.model.thread_count())  + " threads")
        self.output_window.insert(tk.END, "\nTemperature: " + repr(self.temperature))
        self.output_window.insert(tk.END, "\nContext length: " + repr(self.context))
        self.root.after(10, lambda: self.input_text.focus_set())
        assert self.gpt4all_instance.current_chat_session[0]['role'] == 'system'
        self.output_window.insert(tk.END, "\nSystem prompt: " + repr(self.gpt4all_instance.current_chat_session[0]['content']))
        self.output_window.insert(tk.END, "\nPrompt template: " + repr(self.gpt4all_instance._current_prompt_template))
        self.output_window.insert(tk.END, "\n\n")

    def inference(self, user_input):
        start_time = time.time()
        self.esc_pressed = False
        
        message = user_input
        # execute chat completion and ignore the full response since 
        # we are outputting it incrementally
        self.output_window.insert(tk.END, "\n<<<<<<<<<<<<< AI <<<<<<<<<<<<<\n\n")
        self.output_window.yview(tk.END) 
        response_generator = self.gpt4all_instance.generate(
            message,
            # preferential kwargs for chat ux
            max_tokens=20000,
            temp=self.temperature,
            top_k=40,
            top_p=0.4,
            min_p=0.0,
            repeat_penalty=1.18,
            repeat_last_n=64,
            n_batch=128,
            # required kwargs for cli ux (incremental response)
            streaming=True,
            callback=self.stop_on_token_callback,
        )
        
        token_count = 0

        for token in response_generator:
            self.output_window.insert(tk.END, token)
            self.output_window.yview(tk.END)
            self.root.update_idletasks()
            token_count += 1
            if token_count == 1:
                prompt_eval_time = time.time() - start_time 
                start_time = time.time()  
                
        end_time = time.time()

        self.output_window.insert(tk.END, f"\n\nPrompt evaluation: {prompt_eval_time:.2f} seconds")   
        if token_count > 1:
            tokens_per_second = (token_count -1) / (end_time - start_time)  
            self.output_window.insert(tk.END, f"\nTokens: {token_count}  Tokens/second: {tokens_per_second:.2f}")                
        self.output_window.insert(tk.END, "\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n")
        self.output_window.yview(tk.END)    
        #print(self.gpt4all_instance.current_chat_session)
        #print("\n")
        self.inference_thread = None

    def init_inference(self):
        # Copy and paste into output window
        self.output_window.insert(tk.END, "\n>>>>>>>>>>>> USER >>>>>>>>>>>>\n\n")
        self.output_window.insert(tk.END, self.input_text.get("1.0", "end-1c"))
        self.output_window.insert(tk.END, "\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")
        self.output_window.yview(tk.END) 
        message = self.input_text.get("1.0", "end-1c")
        self.input_text.delete("1.0", "end") 
        self.inference(message)


    def generate(self):
        if self.inference_thread is None:
            self.inference_thread = threading.Thread(target=self.init_inference)
            self.inference_thread.start()

    def stop(self):
        self.esc_pressed = True
    
    def exit(self):
        del self.gpt4all_instance
        quit()
    
    def newchat(self):
        if self.inference_thread is None:
            self.new_chat_session()
            
    # Callback function from GPT-4all
    def stop_on_token_callback(self, token_id, token_string):
        if self.esc_pressed:
            return False
        else:
            return True

    def on_closing(self):
        del self.gpt4all_instance
        self.root.destroy()

if __name__ == "__main__":
    gui = ChatGUI()
    typer.run(gui.opt)
