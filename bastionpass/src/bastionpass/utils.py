import os
import toga
import json
import random
import json_repair
from pathlib import Path
from cryptography.fernet import Fernet

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip
    
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
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
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
        "-",
        "!",
        " "
    ]

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

    os.mkdir(user_data_path)

    with open(Path(user_data_path, ".passwords.json"), mode="w") as data_file:
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

        if (keyring.get_password("PYPASS","MAIN_KEY") is None and env.get("FIRST_RUN") == "true") or (keyring.get_password("PYPASS","MAIN_KEY") is None and env.get("FIRST_RUN") is None):

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

    return key


def decrypt_data(data_to_decrypt: bytes, key_to_use: str="main_key", iv=None) -> str:
    if key_to_use == "main_key":
        decryption_key = get_main_key()

    else:
        decryption_key = key_to_use

    if toga.platform.current_platform.lower() == "android" and key_to_use == "main_key":
        from java.util import Base64
        from javax.crypto import Cipher
        from javax.crypto.spec import GCMParameterSpec
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

    assert isinstance(data_to_encrypt, bytes)

    if toga.platform.current_platform == "android" and key_to_use == "main_key":
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
        encrypted_data = Fernet(encryption_key).encrypt(data_to_encrypt)
        return {
            "encrypted_data": encrypted_data,
            "iv_used": None
        }

def offset_string(string_to_offset: str, data_offset: int = 0):
    if data_offset == 0:
        data_offset = random.randint(1, len(offset_data))

    string_offset = ""

    for character in string_to_offset:
        try:
            string_offset += str(offset_data.index(character) + data_offset)

            if character.isupper():
                string_offset += "U"

        except ValueError:
            string_offset += str(character + "!")

        finally:
            string_offset += " "

    return (string_offset, data_offset)

def deoffset_string(string_to_deoffset: str, data_offset: int):
    deoffset_data = ""

    for character_data in string_to_deoffset.split(" "):
        if character_data == "":
            continue

        print(f"Character data is: {character_data}")

        if character_data[-1] == "!":
            deoffset_data += str(character_data[:-1]).replace("[", "").replace("]", "").replace("'", "").replace(",", "")

        elif character_data[-1] == "U":
            deoffset_data += offset_data[int(str(character_data[:-1]).replace("[", "").replace("]", "").replace("'", "").replace(",", "")) - data_offset].upper()

        else:
            deoffset_data += offset_data[int(character_data) - data_offset]

    return deoffset_data

def import_from_file(path: Path, file_pattern: list):
    """
    Import passwords from a given file
    Parameters:
        path: Path - The file path of the file to import passwords from
        file_pattern: list - The pattern to look for, e.g.:
            [
                "ignore"
                "service"
                "username"
                "password"
                "ignore"
            ]
    """
    if path is None or not path.exists():
        return "Path nonexistent"

    with open(path) as import_file:
        file_data = import_file.read().split("\n")

    pattern_header: str = ""
    pattern_footer: str = ""

    for pattern_item in file_pattern:
        if "header" in pattern_item:
            pattern_header: str = str(pattern_item.split(" ")[1:]).replace("[", "").replace("]", "").replace(",", "").replace("'", "")
            break

    for pattern_item in file_pattern:
        if "footer" in pattern_item:
            pattern_footer = str(pattern_item.split(" ")[1:]).replace("[", "").replace("]", "").replace(",", "").replace("'", "")
            break

    ready_to_continue: bool = False

    service: str = ""
    username: str = ""
    password: str = ""

    imported_data: dict = {}
    position_in_pattern: int = 0

    for line in file_data:
        print(f"Ready to continue value: {ready_to_continue}")
        print(f"Header value: {pattern_header}")
        print(f"Footer value: {pattern_footer}")
        print(f"Line value: {line}")

        print(f"Header isn't empty string: {pattern_header != ''}")
        print(f"Line is equal in header: {str(line) == str(pattern_header)}")
        print(f"Header isn't an empty string and line equals header: {pattern_header != "" and line == pattern_header}")

        if pattern_header != "" and line == pattern_header:
            # Header has been supplied and header has been reached in file
            ready_to_continue = True
            continue

        elif pattern_header == "":
            # No header has been supplied, rely on ignore to determine what lines to ignore
            ready_to_continue = True

        elif pattern_header != "" and line != pattern_header:
            # Header has been supplied, but not reached yet
            continue

        else:
            continue

        if ready_to_continue:
            line_role = file_pattern[position_in_pattern]

            print("Line role: " + line_role)
            print("Line is: " + line)

            if position_in_pattern + 1 == len(file_pattern):
                position_in_pattern = 0

            else:
                position_in_pattern += 1

            if line_role == "ignore":
                print(f"Imported data so far is: {imported_data}")

                service = ""
                username = ""
                password = ""
                continue
            else:
                if line_role == "service":
                    service = line
                elif line_role == "username":
                    username = line
                elif line_role == "password":
                    password = line

                    # Footer has not been supplied or footer has been supplied and reached
                    if pattern_footer == "" or (pattern_footer != "" and line == pattern_footer):
                        if service not in imported_data.keys():
                            imported_data[service] = {
                                username: password
                            }

                        else:
                            imported_data[service][username] = password

                    else:
                        ready_to_continue = False
                        continue

    return imported_data

def create_backup_phrase(phrase: str, wordlist: dict) -> list:
    backup_phrase = []
    index = 1

    for character in phrase:
        if character.isnumeric() is True or character == "-" or character == "=" or character == "_":
            string_to_append = character

        elif character.isupper():
            string_to_append = wordlist[character.upper()] + "!"

        else:
            string_to_append = wordlist[character.upper()]

        if not phrase.index(character) % 3 == 0:
            string_to_append += "    "

        backup_phrase.append(string_to_append)

        index += 1

    return backup_phrase
