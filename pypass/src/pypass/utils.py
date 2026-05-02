import os
import toga
import json
import json_repair
from pathlib import Path
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

            if encrypted_received_data == b"":
                break

            decrypted_received_data: str = cipher.decrypt(
            main_cipher.decrypt(encrypted_received_data)).decode()

        except InvalidToken:
            print("Couldn't decrypt received data")

        else:
            print("Data was successfully decrypted, breaking out of while loop")
            encrypted_received_data = b""
            break

    return decrypted_received_data

def get_main_key():
    env = json_repair.from_file(Path(toga.App.app.paths.data, ".env"))

    if env == "":
        env = {}

    if toga.platform.current_platform == "android":
        from java.security import KeyStore
        from javax.crypto import KeyGenerator
        from android.security.keystore import KeyProperties, KeyGenParameterSpec

        key_generator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            "AndroidKeyStore"
        )

        key_generator.init(
            KeyGenParameterSpec.Builder(
                "PYPASS_MAIN_KEY",
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT
            )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setUserAuthenticationRequired(False)
            .build()
        )

        key_store = KeyStore.getInstance("AndroidKeyStore")
        key_store.load(None)

        if key_store.containsAlias("PYPASS_MAIN_KEY"):
            key = key_store.getKey("PYPASS_MAIN_KEY", None)

        elif not key_store.containsAlias("PYPASS_MAIN_KEY") and env.get("MAIN_KEY") is not None:
            key = env["MAIN_KEY"]

        else:
            key = key_generator.generateKey()

        if env.get("MAIN_KEY") is not None:
            del env["MAIN_KEY"]

            with open(Path(toga.App.app.paths.data, ".env"), mode="w") as env_file:
                json.dump(env, env_file)

    else:
        import keyring

        if keyring.get_password("PYPASS","MAIN_KEY") is None and env.get("FIRST_RUN") == "true":

            key = Fernet.generate_key().decode()
            keyring.set_password("PYPASS", "MAIN_KEY", key)

        elif "MAIN_KEY" in env.keys() and env.get("FIRST_RUN") == "false":
            key = env["MAIN_KEY"]
            keyring.set_password("PYPASS", "MAIN_KEY", key)

            del env["MAIN_KEY"]
            with open(Path(toga.App.app.paths.data, ".env"), mode="w") as env_file:
                json.dump(env, env_file)

        else:
            key = keyring.get_password("PYPASS", "MAIN_KEY")

    print(f"Retrieved MAIN_KEY: {key}")

    return key

def decrypt_data(data_to_decrypt: str or bytes, key_to_use: str="main_key", iv=None):
    if key_to_use == "main_key":
        decryption_key = get_main_key()

    else:
        decryption_key = key_to_use

    if data_to_decrypt is str:
        data_to_decrypt = data_to_decrypt.encode()

    if toga.platform.current_platform == "android":
        from java.util import Base64
        from javax.crypto import Cipher
        from java.security import KeyStore
        from javax.crypto.spec import GCMParameterSpec

        key_store_instance = KeyStore.getInstance("AndroidKeyStore")
        key_store_instance.load(None)

        decryption_iv = Base64.getDecoder().decode(iv)

        decryption_cipher = Cipher.getInstance("AES/GCM/NoPadding")
        decryption_cipher.init(
            Cipher.DECRYPT_MODE,
            decryption_key,
            GCMParameterSpec(
                128,
                decryption_iv
            )
        )

        encrypted_decoded = Base64.getDecoder().decode(data_to_decrypt)
        decrypted_bytes_data = decryption_cipher.doFinal(encrypted_decoded)

        print(f"Decrypted data is: {bytes(decrypted_bytes_data).decode()}")

        return bytes(decrypted_bytes_data).decode()

    else:
        # Implement logic for desktop OS's
        return Fernet(decryption_key).decrypt(data_to_decrypt)

def encrypt_data(data_to_encrypt: str or bytes, key_to_use: str ="main_key"):
    if key_to_use == "main_key":
        encryption_key = get_main_key()

    else:
        encryption_key = key_to_use


    if isinstance(data_to_encrypt, str) == True:
        data_to_encrypt = data_to_encrypt.encode()

    print(f"Data to encrypt is: {data_to_encrypt}")
    print(f"Data to encrypt is of type: {type(data_to_encrypt)}")

    assert isinstance(data_to_encrypt, bytes)

    if toga.platform.current_platform == "android":
        from java.util import Base64
        from javax.crypto import Cipher

        cipher_instance = Cipher.getInstance("AES/GCM/NoPadding")
        cipher_instance.init(Cipher.ENCRYPT_MODE, encryption_key)
        cipher_iv = cipher_instance.getIV()
        encrypted_text = cipher_instance.doFinal(data_to_encrypt)
        encrypted_base64 = Base64.getEncoder().encodeToString(encrypted_text)
        iv_base64 = Base64.getEncoder().encodeToString(cipher_iv)

        return {
            "encrypted_data": encrypted_base64,
            "iv_used": iv_base64
        }

    else:
        print(f"Encryption key is: {encryption_key}")
        encrypted_data = Fernet(encryption_key).encrypt(data_to_encrypt)
        return {
            "encrypted_data": encrypted_data,
            "iv_used": None
        }
