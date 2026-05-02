from cryptography.fernet import Fernet
from pypass.app import PyPass
from pypass.utils import *
from pathlib import Path
import shutil
import pytest
import toga
import json
import os


os.environ["TOGA_BACKEND"] = "toga_dummy"
pytest_plugins = ("pytest_asyncio",)

pypass_object = PyPass(app_id="id", formal_name="name")
pypass_object.app.paths.data.mkdir(parents=True, exist_ok=True)

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
    toga.App.app.main_loop()

    if toga.platform.current_platform == "android":
        from org.beeware.android import MainActivity

        setattr(toga.App.app._impl, "native", MainActivity.singletonThis)

    assert copy_to_clipboard("Test text") == "Successfully copied to clipboard"

@pytest.mark.asyncio
async def test_receive_all():
    import time
    import socket
    import asyncio
    import netifaces
    from pypass_server import start_server, stop_server

    test_main_key = Fernet.generate_key()
    interface = netifaces.interfaces()[0]
    server_result = start_server(server_interface=interface, server_port=9000)

    print(server_result)
    print(f"Address being returned: {netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["addr"]}")

    await asyncio.sleep(1)

    data_subfolders = os.listdir("./data")
    del data_subfolders[data_subfolders.index("data.json")]

    print(data_subfolders)
    assert len(data_subfolders) == 0

    assert server_result["server_running"] == True
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((netifaces.ifaddresses(interface)[netifaces.AF_INET][0]["addr"], 9000))

    await asyncio.to_thread(server.sendall, b"test_user")
    server.sendall(test_main_key)
    server_key = Fernet(test_main_key).decrypt(server.recv(1024))

    for_server = {
        "test": {
            "test": {
                "password": "test",
                "key": server_key.decode()
            }
        }
    }

    encrypted_for_server_string: bytes = Fernet(server_key).encrypt(
        Fernet(test_main_key).encrypt(
            json.dumps(for_server).encode()
        )
    )

    await asyncio.to_thread(server.sendall, encrypted_for_server_string)
    await asyncio.to_thread(server.sendall, Fernet(server_key).encrypt(Fernet(test_main_key).encrypt(b"REPLACE")))

    server_response = await asyncio.to_thread(server.recv, 1024)

    assert server_response == b"Successfully updated data"


    server.sendall(
        Fernet(server_key).encrypt(Fernet(test_main_key).encrypt(b"DOWNLOAD_DATA"))
    )

    downloaded_data = await asyncio.to_thread(
        receive_all,
        server_key=server_key,
        server_connection=server,
        main_cipher=Fernet(test_main_key)
    )

    print(f"Data from server: {downloaded_data}")

    assert json.loads(downloaded_data) == for_server

    try:
        time.sleep(2)
        await asyncio.to_thread(
            server.sendall,
            Fernet(server_key).encrypt(Fernet(test_main_key).encrypt(b"DONE"))
        )
        await asyncio.to_thread(stop_server)
        await asyncio.to_thread(server.close)

    except ConnectionResetError:
        pass

    shutil.rmtree("./data")

def test_get_main_key():
    Path(toga.App.app.paths.data, ".env").write_text("{}")

    decryption_key = get_main_key()
    print(f"Decryption key is of type: {type(decryption_key)}")

    if toga.platform.current_platform == "android":
        from java import jclass
        assert isinstance(decryption_key, jclass("android.security.keystore2.AndroidKeyStoreSecretKey")) == True

    else:
        encrypted_text = Fernet(decryption_key).encrypt(b"Some text")
        assert Fernet(decryption_key).decrypt(encrypted_text).decode() == "Some text"

def test_encrypt_and_decrypt_data():
    encrypted_data = encrypt_data(data_to_encrypt="Test Text")
    assert decrypt_data(data_to_decrypt=encrypted_data["encrypted_data"], iv=encrypted_data["iv_used"]) == b"Test Text"