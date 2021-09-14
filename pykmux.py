# -- Import necessary modules -- #
import os, sys, pexpect
from getpass import getpass
import cryptography.fernet
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
    except (cryptography.fernet.InvalidToken, TypeError):  # Catch any InvalidToken exceptions if the correct key was not provided
        print("Invalid Key - Unsuccessfully decrypted or token not in bytes")
        print("Exit the script")
        sys.exit(1)

def _parse_bashrc():
    own_env = dict()
    with open(os.path.expanduser("~/.bashrc")) as input:
        for line in input:
            if 'export ' in line and '=' in line:    # --> environmental variable
                (key, value) = line.replace('export ', '').split('=', 1)
                own_env[key] = value.replace('\n', '')  # to remove \n
    return own_env

def _load(file_path, own_env):
    # -- Load the key -- #
    with open(file_path, 'rb') as key_file:
        key = key_file.read()
    # -- We can not use os.environ since the script might be executed in watch mode, and then the change -- #
    # -- in the bashrc file would not take effect until the bash is resetted which is not possible from -- #
    # -- the script -- #
    return key, own_env['KINIT_PWD_PROMPT'], own_env['CONNECTION_PWD']

def _store(key, file_path, prompt, pwd, own_env):
    # -- Load the content of the ~/.bashrc file -- #
    with open(os.path.expanduser("~/.bashrc")) as outfile:
        bashrc = outfile.read()
    # -- Loop through the file line by line and replace the line with the new variables (if applicable) -- #
    prefix = "export "
    vars = [prefix+'KINIT_PWD_PROMPT='+str(own_env.get('KINIT_PWD_PROMPT', " ")), # Use a blank space since that should never be the case
            prefix+'CONNECTION_PWD='+str(own_env.get('CONNECTION_PWD', " ")),
            prefix+'KEYS_PATH='+str(own_env.get('KEYS_PATH', " "))]
    new_vars = [prefix+'KINIT_PWD_PROMPT='+str(prompt),
                prefix+'CONNECTION_PWD='+str(pwd),
                prefix+'KEYS_PATH='+str(file_path)]
    for idx, var in enumerate(vars):
        if var in bashrc:
            # -- Replace the old variable with content with the new one -- #
            bashrc = bashrc.replace(var, str(new_vars[idx]))
        else:
            bashrc += "\n" + str(new_vars[idx])
    # -- Make the environ variables permanent by writing the .~/bashrc again -- #
    with open(os.path.expanduser("~/.bashrc"), 'w') as outfile:
        outfile.write(bashrc)
    # -- Store key as file at file_path -- #
    with open(file_path, 'wb') as key_file:
        key_file.write(key)

def renew_ticket():
    # -- First and foremost load the bashrc by hand since when changing the bashrc the terminal needs to be resetted -- #
    # -- which is not possible when using watch on <time> "<command>" -- #
    own_env = _parse_bashrc()
    # -- Extract key encryption key -- #
    if own_env.get('KEYS_PATH', None) is None:
        # -- Ask user for the path -- #
        print("Please enter the path where the file with the encryption key will be stored: ")
        base = input()
        # -- Store the path as variable -- #
        file_path = os.path.join(base, '.secret_key')
        own_env['KEYS_PATH'] = file_path
        print("The file with the encryption key can be found at: {}.\n".format(own_env['KEYS_PATH']))
    else:
        file_path = own_env['KEYS_PATH']

    # -- Extract kinit password prompt and password to connect -- #
    if own_env.get('KINIT_PWD_PROMPT', None) is None or own_env.get('CONNECTION_PWD', None) is None:
        # -- Generate a new encryption key -- #
        key = _generate_key()
        # -- Get the kinit password prompt from the user if it is not already done once and stored in own_env -- #
        print("Please enter the password prompt from kinit (including the colon at the end):")
        password_prompt_decrypted = input()
        print() # Print empty line for better visibility
        # -- Get the password as well -- #
        password_decrypted = getpass('Password to connect with: ')
        # -- If the password prompt and password are not stored in the own_env, then encrypt and store -- #
        # -- them so we do not need to ask again -- #
        # -- Encode turns the string to bytes -- #
        password_prompt_encrypted = _encrypt(key, password_prompt_decrypted.encode())
        password_encrypted = _encrypt(key, password_decrypted.encode())
        # -- Store everything -- #
        _store(key, file_path, password_prompt_encrypted.decode(), password_encrypted.decode(), own_env)
        # -- Reload own_env -- #
        own_env = _parse_bashrc()
    else:
        # -- Load key and prompt with password -- #
        key, password_prompt, password = _load(file_path, own_env)
        f = Fernet(key)
        # NOTE: Decode the bytes back to string or the passwords do not match
        # -- Get kinit password prompt and decrypt it -- #
        password_prompt_decrypted = _decrypt(key, password_prompt.encode()).decode()
        # -- Get password and decrypt it -- #
        password_decrypted = _decrypt(key, password.encode()).decode()

    # -- Now we can renew the kerberos ticket in a tmux session (the safe encrypted way) -- #
    child = pexpect.spawn('kinit')
    child.expect(password_prompt_decrypted)
    child.sendline(password_decrypted)
    child.send('\n')
    print("The ticket has been successfully renewed.")

    # -- Encrypt the password prompt and password with a new key and restore everything -- #
    # -- Generate a new encryption key -- #
    key = _generate_key()
    # -- Store everything -- #
    _store(key, file_path, _encrypt(key, password_prompt_decrypted.encode()).decode(), _encrypt(key, password_decrypted.encode()).decode(), own_env)


if __name__ == "__main__":
    renew_ticket()