# pyKmux
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

A small and simple python script to automatically renew a kerberos ticket in a tmux session. The kinit password prompt and password are encrypted and individually stored as environment variables, whereas the encryption key is stored seperately in a file, at a path specified by the user. The passwords and path need to be specified whenever they are not available during runtime of the script, ie. whenever the file_path eg. is not stored as an environment variable anymore, the user needs to specify the path again. The same applies for the kinit password prompt or password. After sucessful ticket renewal, a new key will be generated, the password prompt and password encrypted using the new key and stored accordingly.

## Installation
* Clone the pyKmux repository
* Navigate to the project root (where `pykmux.py` lives)
* Execute `pip install -r requirements.txt` to install all required packages
* Execute `kinit` in your terminal and copy the entire password prompt (including the colon)

## How to use
* Create or attach to a tmux session: `tmux new` or `tmux a -t X`
* Open a new tmux pane: `Ctrl+B "`
* Activate the new pane: `Ctrl+B DOWN`
* Execute `pykmux.py` every 5 hours: `watch -n 18000 "python pykmux.py"`
* If prompted: Enter path to folder in which the encryption key is stored as well as password prompt (visible when typing) and password (not visible when typing)
* (Optional) Hide the pane
