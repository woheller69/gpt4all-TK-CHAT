# GPT4All TK CHAT GUI

## Quickstart

The TK GUI is based on the `gpt4all` Python bindings and the `typer` and `tkinter` package.

The following shows one way to get started with the GUI.
Typically, you will want to replace `python` with `python3` on _Unix-like_ systems. 
Also, it's assumed you have all the necessary Python components already installed.

The GUI is a self-contained Python script named `appGUI.py`. As long as
its package dependencies are present, you can download and run it from wherever you like.

```shell
# pip-install the necessary packages;
python -m pip install --upgrade gpt4all typer tkinter
```
Specify the path to the model with the `-m`/`--model` argument and an optional prompt with `-p`/`--prompt`. 
A system prompt can also be set with `-s`/`--sysprompt`.
Context length defaults to 2048, it can be set with `-c`/`--context-length`

```shell
python appGUI.py --model /home/user/my-gpt4all-models/gpt4all-13b-snoozy-q4_0.gguf --prompt "I am in the jungle"
```
Input your request in the bottom window and click "Generate".

<img src="01.png" width="250"/> 


# GPT4All Command-Line Interface (CLI)

In addition there is a simple CLI version. It uses `pynput`. 
Important: `pynput` does not work with Wayland on Ubuntu. You need to switch to Xorg

Example:
```shell
pip install pynput
python app.py --model /home/user/my-gpt4all-models/gpt4all-13b-snoozy-q4_0.gguf --prompt "I am in the jungle"
```

Inference can be interrupted using the `Space` key.




