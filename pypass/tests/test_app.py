from cryptography.fernet import Fernet
from pypass.app import PyPass
from pypass.utils import *
from pathlib import Path
import argparse
import toga
import json
import os

os.environ["TOGA_BACKEND"] = "toga_dummy"

parser = argparse.ArgumentParser()
parser.add_argument("--api-key", type=str, help="Github API key")
args_passed = parser.parse_args()

pypass_object = PyPass(app_id="id" ,formal_name="name")
pypass_object.app.paths.data.mkdir(parents=True, exist_ok=True)

PYPASS_SERVER_CODE_BRANCH = "dev-branch"
PYPASS_SERVER_CODE_FOLDER = "pypass-server"
PYPASS_SERVER_CODE_PATH = "coryellcottage/pypass"

def test_recover_key():
    print("Testing recover_key...")

    assert recover_key("afraid!/ boat/ 1/ !/ -/".replace(" ", "").split("/")) == "Ab1!-"

def test_add_to_screen():
    print("Testing add_to_screen...")

    add_to_screen(
        {
            "test_button": toga.Button(text="test"),
            "test_label": toga.Label(text="test", style=toga.style.Pack(margin_top=10))
        },
        toga.Box()
    )

    add_to_screen(
        {
            "self.test_entry": toga.TextInput(),
            "test_label": toga.Label(text="test", style=toga.style.Pack(margin_top=10))
        },
        toga.Box(),
        clear_screen=True
    )

def test_load_env():
    print("Testing load_env...")

    Path(pypass_object.app.paths.data, ".env").write_text("")

    assert load_env(env_path=Path(pypass_object.app.paths.data, ".env"),
                    env_object=os.environ) == "Invalid data type saved"

    assert load_env(env_path=Path("env_file"),
                    env_object=os.environ) == "Env path doesn't exist"

    with open(Path(pypass_object.app.paths.data, ".env"), mode="w") as env_file:
        json.dump(
            obj={
                "MAIN_KEY": Fernet.generate_key().decode()
            },
            fp=env_file
        )

    assert load_env(
        env_path=Path(pypass_object.app.paths.data, ".env"),
        env_object=os.environ
    ) == "Loaded environment"

    Path(pypass_object.app.paths.data, ".env").unlink(missing_ok=True)

def test_check_password():
    print("Testing check_password...")

    password = "password"
    cipher = Fernet(Fernet.generate_key())

    assert check_password(entered_password="password", saved_password=cipher.encrypt(password.encode()).decode(), password_cipher=cipher) == "Correct password entered"
    assert check_password(entered_password="password1", saved_password=cipher.encrypt(password.encode()).decode(), password_cipher=cipher) == "Incorrect password entered"

def test_load_user_data():
    print("Testing load_user_data")

    data_path = PyPass(formal_name="name", app_id="id").paths.data

    test_main_key = Fernet.generate_key()
    test_user_key = Fernet.generate_key()
    test_data = {
        "user": Fernet(test_main_key).encrypt(b"test").decode(),
        "key": Fernet(test_main_key).encrypt(test_user_key).decode(),
        "data": {
            "service": {
                "username": {
                    "password": Fernet(test_user_key).encrypt(b"test_password").decode(),
                    "key": Fernet(test_user_key).encrypt(Fernet.generate_key()).decode()
                }
            }
        },
        "servers": {}
    }

    assert load_user_data(Path(data_path, "passwords_file")) == "Password file path doesn't exist"

    Path(data_path ,"passwords_file").write_text("")
    assert load_user_data(Path(data_path ,"passwords_file")) == "Invalid data saved"

    with open(Path(data_path, "passwords_file"), mode="w") as passwords_file:
        json.dump(
            obj=test_data,
            fp=passwords_file
        )

    print(f"Data type from load_user_data: {type(load_user_data(Path(data_path, 'passwords_file')))}")

    assert load_user_data(Path(data_path, "passwords_file")) == test_data

    Path(data_path, "passwords_file").unlink(missing_ok=True)

def test_create_user():
    data_path = pypass_object.app.paths.data
    test_user = "user"
    test_password = "password"
    test_cipher = Fernet(Fernet.generate_key())

    assert create_new_user(user_data_path=Path(data_path, test_user), user=test_user, password=test_password, main_cipher=test_cipher) == "Successfully created new user"
    assert create_new_user(user_data_path=Path(data_path, test_user), user=test_user, password=test_password, main_cipher=test_cipher) == "User already exists"

    Path(data_path, test_user, ".passwords.json").unlink(missing_ok=True)
    Path(data_path, test_user).rmdir()

def test_copy_to_clipboard():
    assert copy_to_clipboard("Test text") == "Successfully copied to clipboard"

def test_server():
    import requests

    API_KEY = args_passed.api_key

    print(API_KEY)

    response = requests.get(f"https://api.github.com/repos/{PYPASS_SERVER_CODE_PATH}/contents/{PYPASS_SERVER_CODE_FOLDER}?ref={PYPASS_SERVER_CODE_BRANCH}", headers={"Authorization": f"Bearer {API_KEY}"})
    response.raise_for_status()

    api_data = response.json()

    for file in api_data:
        response = requests.get(file["download_url"])
        response.raise_for_status()

        file_text = response.text
        file_path = file["path"].split("/")
        del file_path[-1]

        try:
            for folder in file_path:
                Path(folder).mkdir(exist_ok=True)

        except FileExistsError:
            pass

        with open(file["path"], mode="w") as new_file:
            new_file.write(file_text)

    assert Path("pypass-server").exists() and Path("pypass-server", "main.py").exists() and Path("pypass-server", "requirements.txt").exists()

    Path("pypass-server", "requirements.txt").unlink(missing_ok=True)
    Path("pypass-server", "main.py").unlink(missing_ok=True)
    Path("pypass-server").rmdir()
