# pyKmux
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)

A small and simple python script to automatically renew a kerberos ticket in a tmux session. The kinit password prompt and password are encrypted and individually stored as environment variables, whereas the encryption key is stored seperately in a file, at a path specified by the user. The passwords and path need to be specified whenever they are not available during runtime of the script, ie. whenever the file_path eg. is not stored as an environment variable anymore, the user needs to specify the path again. The same applies for the kinit password prompt or password. After sucessful ticket renewal, a new key will be generated, the password prompt and password encrypted using the new key and stored accordingly.

## Installation
* Clone the pyKmux repository
* Navigate to the project root (where `pykmux.py` lives)
* Execute `pip install -r requirements.txt` to install all required packages
* Execute `kinit` in your terminal and copy the entire password prompt (including the colon)

## Initialization/First use:
* Open the terminal (or tmux session) and execute `python pykmux.py` once.
* Specify the path where the encryption key should be stored (visible when typing)
* Add the password prompt extracted as described above using `kinit` (visible when typing)
* Specify the password to connect with, the one that is necessary to renew the ticket (not visible when typing).

Note: Do this initialization step whenever the `watch -n <time> <"command">` as shown below does not work. This is due to the expected input from the user for the program. For the first time, this command needs to be executed once for initialization purposes so set everything correctly. This always applies when the information is removed from the `~/.bashrc` file (manually). Once the initialization is done, the script can be automatically executed given a specified time as follows.

## How to execute the script with `watch -n <time> <"command">`
* Create or attach to a tmux session: `tmux new` or `tmux a -t X`
* Open a new tmux pane: `Ctrl+B "`
* Activate the new pane: `Ctrl+B DOWN`
* Execute `python pykmux.py` every 5 hours: `watch -n 18000 "python pykmux.py"`
* (Optional) Hide the pane
