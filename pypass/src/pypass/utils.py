import os
import toga
import json
import json_repair
from cryptography.fernet import Fernet, InvalidToken

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip

def recover_key(backup_phrase: list) -> str:
    recovered_key = ""

    for word in backup_phrase:
        # word = word.replace(" ", "").replace('"', "")

        if word == '':
            del backup_phrase[backup_phrase.index(word)]

        elif word.isnumeric() is True or word == "-" or word == "=":
            recovered_key += word

        else:
            if word[-1] == "!":
                recovered_key += word[0].title()

            else:
                recovered_key += word[0]

    return recovered_key


def add_to_screen(widgets_to_add: dict[str, toga.Widget], box_to_add_to: toga.Box, clear_screen: bool = False) -> str:
    if clear_screen:
        box_to_add_to.clear()

    for widget_title in widgets_to_add.keys():
        widget_object = widgets_to_add[widget_title]

        box_to_add_to.add(widget_object)

    return "Added widgets to screen"


def load_env(env_path, env_object: os._Environ) -> str:
    if not os.path.exists(env_path):
        return "Env path doesn't exist"

    with open(env_path, mode="r") as env_file:
        env_data = json_repair.load(env_file)

    if not hasattr(env_data, "keys"):
        return "Invalid data type saved"

    for key in env_data.keys():
        env_object[key] = env_data[key]

    return "Loaded environment"


def check_password(entered_password: str, saved_password: str, password_cipher: Fernet) -> str:

    if password_cipher.decrypt(saved_password).decode() == entered_password:
        return "Correct password entered"

    else:
        return "Incorrect password entered"


def load_user_data(password_file_path: str) -> str | dict:
    if not os.path.exists(password_file_path):
        return "Password file path doesn't exist"

    user_data = json_repair.from_file(password_file_path)

    if user_data == "":
        return "Invalid data saved"

    return user_data


def create_new_user(user_data_path: str, user: str, password: str, main_cipher: Fernet) -> str:
    encryption_key = Fernet.generate_key()
    cipher = Fernet(encryption_key)

    if os.path.exists(user_data_path):
        return "User already exists"

    user_data = {
        user: cipher.encrypt(password.encode()).decode(),
        "key": main_cipher.encrypt(encryption_key).decode()
    }

    os.mkdir(user_data_path)

    with open(os.path.join(user_data_path, ".passwords.json"), mode="w") as data_file:
        json.dump(user_data, data_file, indent=4)

    return "Successfully created new user"


def copy_to_clipboard(data_to_copy: str):
    if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
        cb = Clipboard.get_clipboard()

        cb.set_text(data_to_copy)

        return "Successfully copied to clipboard"

    elif toga.platform.current_platform.lower() == "linux" or toga.platform.current_platform.lower() == "freebsd" or toga.platform.current_platform.lower() == "macos":
        pyperclip.copy(data_to_copy)

        return "Successfully copied to clipboard"

    else:
        return "Can't copy to clipboard. Unsupported OS"

def receive_all(server_key: bytes, server_connection, main_cipher: Fernet) -> str:
    cipher = Fernet(server_key)

    encrypted_received_data: bytes = b""

    while True:
        print("Receiving new data")
        new_received_data = server_connection.recv(1024)

        print(
            f"\n ------------------------------ \n    Total received data: {encrypted_received_data} \n ------------------------------ ")
        print(
            f"\n ------------------------------ \n    New data received: {new_received_data} \n ------------------------------ ")

        if new_received_data.decode() == "DONE":
            decrypted_received_data: str = cipher.decrypt(
                main_cipher.decrypt(encrypted_received_data)).decode()

            break

        try:
            print("Trying to decrypt total received data")

            encrypted_received_data += new_received_data
            decrypted_received_data: str = cipher.decrypt(
            main_cipher.decrypt(encrypted_received_data)).decode()

        except InvalidToken:
            print("Couldn't decrypt received data")

        else:
            print("Data was successfully decrypted, breaking out of while loop")
            encrypted_received_data = b""
            break

    return decrypted_received_data
