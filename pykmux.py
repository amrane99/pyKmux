# -- Import necessary modules -- #
import os, sys, pexpect
from getpass import getpass
from cryptography.fernet import Fernet

def _generate_key():
    # -- Generate a new encryption key -- #
    return Fernet.generate_key()

def _encrypt(key, token):
    f = Fernet(key)
    return f.encrypt(token)

def _decrypt(key, token):
    f = Fernet(key)
    try:
        return f.decrypt(token)
    except (Fernet.InvalidToken, TypeError):  # Catch any InvalidToken exceptions if the correct key was not provided
        print("Invalid Key - Unsuccessfully decrypted or token not in bytes")
        print("Exit the script")
        sys.exit(1)

def _load(file_path):
    # -- Load the key -- #
    with open(file_path, 'rb') as key_file:
        key = key_file.read()

    return key, os.environ['KINIT_PWD_PROMPT'], os.environ['CONNECTION_PWD']

def _store(key, file_path, prompt, pwd):
    # -- Store them as os.environ -- #
    os.environ['KINIT_PWD_PROMPT'] = prompt
    os.environ['CONNECTION_PWD'] = pwd
    # -- Store key as file at file_path -- #
    with open(file_path, 'wb') as key_file:
        key_file.write(key)

def renew_ticket():
    # -- Extract key encryption key -- #
    if os.environ['KEYS_PATH'] is None:
        # -- Ask user for the path -- #
        print("Please enter the path where the file with the encryption key will be stored: ")
        file_path = input()
        # -- Store the path as variable -- #
        os.environ['KEYS_PATH'] = os.path.join(file_path, '.secret.key')
        print("The file with the encryption key can be found at: {}.".format(os.environ['KEYS_PATH']))
    else:
        file_path = os.environ['KEYS_PATH']

    # -- Extract kinit password prompt and password to connect -- #
    if os.environ['KINIT_PWD_PROMPT'] is None or os.environ['CONNECTION_PWD'] is None:
        # -- Generate a new encryption key -- #
        key = _generate_key()
        # -- Get the kinit password prompt from the user if it is not already done once and stored in os.environ -- #
        print("Please enter the password prompt from kinit: ")
        password_prompt_decrypted = input()
        # -- Get the password as well -- #
        password_decrypted = getpass()
        # -- If the password prompt and password are not stored in the os.environ, then encrypt and store -- #
        # -- them so we do not need to ask again -- #
        # -- Encode turns the string to bytes -- #
        password_prompt_encrypted = _encrypt(key, password_prompt_decrypted.encode())
        password_encrypted = _encrypt(key, password_decrypted.encode())
        # -- Store everything -- #
        _store(key, file_path, password_prompt_encrypted, password_encrypted)
    else:
        # -- Load key and prompt with password -- #
        key, password_prompt, password = _load(file_path)
        f = Fernet(key)
        # NOTE: Decode the bytes back to string or the passwords do not match
        # -- Get kinit password prompt and decrypt it -- #
        password_prompt_decrypted = _decrypt(key, password_prompt).decode()
        # -- Get password and decrypt it -- #
        password_decrypted = _decrypt(key, password).decode()
        

    # -- Now we can renew the kerberos ticket in a tmux session (the safe encrypted way) -- #
    child = pexpect.spawn('kinit')
    child.expect(password_prompt_decrypted)
    child.sendline(password_decrypted)
    child.send('\n')

    # -- Encrypt the password prompt and password with a new key and restore everything -- #
    # -- Generate a new encryption key -- #
    key = _generate_key()
    # -- Store everything -- #
    _store(key, file_path, _encrypt(key, password_prompt_decrypted.encode()), _encrypt(key, password_decrypted.encode()))


if __name__ == "__main__":
    renew_ticket()