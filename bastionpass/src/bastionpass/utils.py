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


def add_to_screen(widgets_to_add: tuple, box_to_add_to: toga.Box, clear_screen: bool = False) -> str:
    if clear_screen:
        box_to_add_to.clear()

    [box_to_add_to.add(widget) for widget in widgets_to_add]

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


def check_password(entered_password: str, saved_password: str, password_cipher: Fernet=None) -> str:
    if password_cipher.decrypt(saved_password).decode() == entered_password:
        return "Correct password entered"

    else:
        return "Incorrect password entered"


def load_user_data(password_file_path: Path) -> str | dict:
    if not password_file_path.exists():
        return "Password file path doesn't exist"

    user_data = json_repair.from_file(password_file_path)

    if user_data == "":
        return "Invalid data saved"

    return user_data


def create_new_user(user_data_path: str, user: str, password: str, main_cipher: Fernet or str) -> str:
    encryption_key = Fernet.generate_key()
    cipher = Fernet(encryption_key)

    if Path(user_data_path).exists():
        return "User already exists"

    if isinstance(main_cipher, Fernet):
        user_data = {
            user: cipher.encrypt(password.encode()).decode(),
            "key": main_cipher.encrypt(encryption_key).decode()
        }

    elif isinstance(main_cipher, str):
        data = encrypt_data(data_to_encrypt=encryption_key)

        user_data = {
            user: cipher.encrypt(password.encode()).decode(),
            "key": data["encrypted_data"],
            "iv": data["iv_used"]

        }

    else:
        return "Couldn't encrypt password"

    print(f"User_data: \n{user_data}")

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

def get_main_key():
    if Path(toga.App.app.paths.data, ".env").exists():
        env = json_repair.from_file(Path(toga.App.app.paths.data, ".env"))

    else:
        env = {}

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


def decrypt_data(data_to_decrypt: bytes, key_to_use: str="main_key", iv=None) -> str:
    if key_to_use == "main_key":
        decryption_key = get_main_key()

    else:
        decryption_key = key_to_use

    if toga.platform.current_platform.lower() == "android":
        from java.util import Base64
        from javax.crypto import Cipher
        from javax.crypto.spec import GCMParameterSpec

        print(type(iv))
        print(iv)
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
        decrypted_data = Fernet(decryption_key).decrypt(data_to_decrypt)

        if isinstance(decrypted_data, bytes):
            decrypted_data = decrypted_data.decode()

        return decrypted_data

def encrypt_data(data_to_encrypt: str or bytes, key_to_use: str ="main_key") -> dict:
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

def offset_user_data(user_data: dict):
    offset_data = [
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "0",
        "_",
        "!"
    ]
    offset_user_data = {}

    decrypted_data = {}
    data_offset = str(random.randint(1, len(offset_data)))

    for service in user_data["data"]:
        for username in user_data["data"][service]:
            encryption_iv = user_data["data"][service][username]["iv"]
            decrypted_key = decrypt_data(user_data["data"][service][username]["key"], iv=encryption_iv)
            decrypted_password = Fernet(decrypted_key).decrypt(
                user_data["data"][service][username]["password"]).decode()

            if service in decrypted_data.keys():
                decrypted_data[service][username] = {
                    "password": decrypted_password,
                    "key": decrypted_key,
                    "iv": encryption_iv
                }

            else:
                decrypted_data[service] = {
                    username: {
                        "password": decrypted_password,
                        "key": decrypted_key,
                        "iv": encryption_iv
                    }
                }

    for service in decrypted_data:
        offset_service = ""
        offset_username = ""
        offset_password = ""
        offset_key = ""

        for character in str(service):
            offset_service += str(offset_data.index(character.lower()))

            if character.isupper():
                offset_service += "U"

            offset_service += " "

        print("Offset service")

        for username in decrypted_data[service]:
            for character in str(username):
                offset_username += str(offset_data.index(character.lower()))

                if character.isupper():
                    offset_username += "U"

                offset_username += " "

            print("Offset username")

            for character in str(decrypted_data[service][username]["password"]):
                print(f"Password is: {decrypted_data[service][username]["password"]}")
                print(f"Data offset is: {data_offset}")
                print(f"Character is: {character}")

                offset_password += str(offset_data.index(character.lower()))

                if character.isupper():
                    offset_password += "U"

                offset_password += " "
                print(offset_password)

            print("Offset password")

            for character in decrypted_data[service][username]["key"]:
                character = str(character)
                try:
                    offset_key += str(offset_data.index(character.lower()))

                    if character.isupper():
                        offset_key += "U"

                except ValueError:
                    offset_key += str(character) + "!"

                else:
                    offset_key += " "

            print("Offset key")

            if offset_service in offset_user_data.keys():
                offset_user_data[offset_service][offset_username] = {
                    "password": offset_password,
                    "key": offset_key,
                    "iv": encryption_iv
                }