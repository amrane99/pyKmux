# -- Import necessary modules -- #
from getpass import getpass
import os, sys, pexpect, json
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

def _parse_file(path):
    own_env = dict()
    with open(path) as input:
        for line in input:
            if 'export ' in line and '=' in line:    # --> environmental variable
                (key, value) = line.replace('export ', '').split('=', 1)
                own_env[key] = value.replace('\n', '')  # to remove \n
    return own_env

def _load(key_path, own_env):
    # -- Load the key -- #
    with open(key_path, 'rb') as key_file:
        key = key_file.read()
    return key, own_env['KINIT_PWD_PROMPT'], own_env['CONNECTION_PWD']

def _store(key, key_path, prompt, pwd, own_env, cont_path):
    # -- Load the content of the file -- #
    with open(cont_path) as outfile:
        cont = outfile.read()
    # -- Loop through the file line by line and replace the line with the new variables (if applicable) -- #
    prefix = "export "
    vars = [prefix+'KINIT_PWD_PROMPT='+str(own_env.get('KINIT_PWD_PROMPT', " ")), # Use a blank space since that should never be the case
            prefix+'CONNECTION_PWD='+str(own_env.get('CONNECTION_PWD', " "))]
    new_vars = [prefix+'KINIT_PWD_PROMPT='+str(prompt),
                prefix+'CONNECTION_PWD='+str(pwd)]
    first = True
    for idx, var in enumerate(vars):
        if var in cont:
            # -- Replace the old variable (with content) with the new one -- #
            cont = cont.replace(var, str(new_vars[idx]))
        else:
            if len(cont) == 0:
                cont += str(new_vars[idx])
                first = False
                continue
            if first:
                cont += "\n"
                first = False
            cont += "\n" + str(new_vars[idx])
    # -- Make the environ variables permanent by writing the path again -- #
    with open(cont_path, 'w') as outfile:
        outfile.write(cont)
    # -- Store key as file at key_path -- #
    with open(key_path, 'wb') as key_file:
        key_file.write(key)

def renew_ticket():
    # -- Load the paths file and check if it is empty -- #
    init_information = dict()
    paths_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.paths')
    with open(paths_file, 'r') as file:
        try:
            init_information = json.load(file)
        except:
            # -- File is empty or corrupted -- #
            pass
    if init_information.get('path_to_file', None) is None:
        # -- Ask user for the content file path -- #
        yes = {'yes','y'}
        no = {'no','n'}
        if os.path.isfile(os.path.expanduser("~/.bashrc")): # bash exists
            while True:
                print("Do you want to use the bashrc file at {} for storing the encrypted prompt and password (y/n): ".format(os.path.expanduser("~/.bashrc")))
                use_bashrc = input().lower()
                if use_bashrc in yes:
                    path = os.path.expanduser("~/.bashrc")
                    no_bash = False
                    break
                if use_bashrc in no:
                    no_bash = True
                    break
        if no_bash:
            print("\nPlease enter the path to the file where the encrypted prompt and password should be stored: ")
            base = input()
            print("\nEnter the desired name of this file (please don't add an extension): ")
            name = input()
            # -- Add ending and leading dot -- #
            if name[0] != '.':
                name = '.' + name
            path = os.path.join(base, name)
            # -- Create the directory if it does not exist -- #
            os.makedirs(os.path.normpath(base), exist_ok=True)
            if not os.path.isfile(path):
                open(path, 'a').close()
            
        # -- Store the path accordingly -- #
        print("\nThe file with the relevant paths can be found at: {}.\n".format(paths_file))
        init_information['path_to_file'] = str(path)
        with open(paths_file, 'w') as outfile:
            json.dump(init_information, outfile, indent=4, sort_keys=True)
    
    # -- Extract key encryption key -- #
    if init_information.get('path_to_key', None) is None:
        # -- Ask user for the path -- #
        print("Please enter the path where the file with the encryption key will be stored.\n"+
              "Choose a different path than the path under which the encrypted prompt and password are stored: ")
        base = input()
        print() # Print empty line for better visibility
        # -- Store the path as variable -- #
        file_path = os.path.join(base, '.secret_key')
        init_information['path_to_key'] = str(file_path)
        with open(paths_file, 'w') as outfile:
            json.dump(init_information, outfile, indent=4, sort_keys=True)

    # -- Extract the path to the key file -- #
    key_path = init_information['path_to_key']
    cont_path = init_information['path_to_file']

    # -- First and foremost load the file by hand -- #
    own_env = _parse_file(cont_path)

    # -- Extract kinit password prompt and password to connect -- #
    if own_env.get('KINIT_PWD_PROMPT', None) is None or own_env.get('CONNECTION_PWD', None) is None:
        # -- Generate a new encryption key -- #
        key = _generate_key()
        # -- Get the kinit password prompt from the user if it is not already done once and stored in own_env -- #
        print("Please enter the password prompt from kinit:")
        password_prompt_decrypted = input()
        if password_prompt_decrypted[-1] != ':':
            password_prompt_decrypted += ':'
        print() # Print empty line for better visibility
        # -- Get the password as well -- #
        password_decrypted = getpass('Password to connect with: ')
        # -- If the password prompt and password are not stored in the own_env, then encrypt and store -- #
        # -- them so we do not need to ask again -- #
        # -- Encode turns the string to bytes -- #
        password_prompt_encrypted = _encrypt(key, password_prompt_decrypted.encode())
        password_encrypted = _encrypt(key, password_decrypted.encode())
        # -- Store everything -- #
        _store(key, key_path, password_prompt_encrypted.decode(), password_encrypted.decode(), own_env, cont_path)
        # -- Reload own_env -- #
        own_env = _parse_file(cont_path)
    else:
        # -- Load key and prompt with password -- #
        key, password_prompt, password = _load(key_path, own_env)
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
    _store(key, key_path, _encrypt(key, password_prompt_decrypted.encode()).decode(), _encrypt(key, password_decrypted.encode()).decode(), own_env, cont_path)


if __name__ == "__main__":
    renew_ticket()