# GPT4All Command-Line Interface (CLI)

GPT4All on the command-line.

## Quickstart

The CLI is based on the `gpt4all` Python bindings and the `typer` and `pynput` package.

The following shows one way to get started with the CLI, the documentation has more information.
Typically, you will want to replace `python` with `python3` on _Unix-like_ systems. 
Also, it's assumed you have all the necessary Python components already installed.
`pynput` does not work with Wayland on Ubuntu. You need to switch to Xorg.

The CLI is a self-contained Python script named `app.py`. As long as
its package dependencies are present, you can download and run it from wherever you like.

```shell
# pip-install the necessary packages;
python -m pip install --upgrade gpt4all typer pynput
# run the CLI
python app.py repl
```
By default, it will automatically download the `groovy` model to `.cache/gpt4all/` in your user
directory, if necessary.

If you have already saved a model beforehand, specify its path with the `-m`/`--model` argument and an optional prompt with `-p`/`--prompt`, 
for example:
```shell
python app.py repl --model /home/user/my-gpt4all-models/gpt4all-13b-snoozy-q4_0.gguf --prompt "I am in the jungle"
```
A system prompt can also be set with `-s`/`--sysprompt`

Inference can be interrupted using the `Space` key.


# GPT4All TK GUI

In addition there is a version with simple TK GUI. It uses `tkinter` and does not need `pynput`

```shell
python appGUI.py repl --model /home/user/my-gpt4all-models/gpt4all-13b-snoozy-q4_0.gguf --prompt "I am in the jungle"
```


