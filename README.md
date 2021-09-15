# pyKmux
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

A small and simple python script to automatically renew a kerberos ticket in a tmux session. The kinit password prompt and password are encrypted and individually stored in a file, whereas the encryption key is stored seperately in a different file, both at paths specified by the user. The passwords and path need to be specified whenever they are not available during runtime of the script, ie. whenever the `.paths` file eg. does not exist (anymore), the user needs to specify the paths again. The same applies for missing kinit password prompt or password. Every key will be used only once, ie. after a successful ticket renewal, a new key will be generated, the password prompt and password encrypted using the new key and stored accordingly.

## Installation
* Clone the pyKmux repository
* Navigate to the project root (where `pykmux.py` lives)
* Execute `pip install -r requirements.txt` to install all required packages
* Execute `kinit` in your terminal and copy the entire password prompt

## Initialization/First use:
* Open the terminal (or tmux session) and execute `python pykmux.py` once.
* Follow the instructions by answering the prompts:
    * Where to store the encrypted prompt and password (visible when typing)
    * Where to store the encryption key (visible when typing)
    * The `kinit` password prompt (visible when typing)
    * The password to connect with, the one that is necessary to renew the ticket (not visible when typing)

Note: Perform this initialization step before the `watch -n <time> <"command">` command shown below since the user interaction for the initialization does not work when using the `watch` command. The initialization step is important to set everything correctly for an automated renewal of a kerberos ticket afterwards. The initialization step always applies when relevant/some information is removed/deleted. Once the initialization is done, the script can be automatically executed given a specified time as follows.

## How to execute the script with `watch -n <time> <"command">`
* Create a tmux session: `tmux new -s <session_name>`
* Execute `python pykmux.py` every 5 hours: `watch -n 18000 "python pykmux.py"`
