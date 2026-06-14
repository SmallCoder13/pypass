import httpx
from .utils import *
import multiprocessing
from pathlib import Path
from fastapi import FastAPI
from threading import Thread
from asyncio import new_event_loop
from uvicorn import Config, Server
from toga.platform import current_platform

class BackgroundServer:
    def __init__(self, port: int, data_path: Path, username: str, comms_pipe: multiprocessing.Pipe):
        httpx.post("http://127.0.0.1:8000/'Background_server_called'")

        self.comms_pipe: multiprocessing.Pipe = comms_pipe
        self.is_command_complete: bool = False
        self.server_loop = new_event_loop()
        self.data_path: Path = data_path
        self.username: str = username
        self.fast_api = FastAPI()
        self.command = {}
        self.port = port

        httpx.post("http://127.0.0.1:8000/'Initialized_all_variables,_setting_up_server'")

        self.event_listener_thread = Thread(target=self.message_listener)
        self.event_listener_thread.start()

        self.command_executor_thread = Thread(target=self.command_listener)
        self.command_executor_thread.start()

        self.add_endpoints()
        self.start_server()

    def add_endpoints(self):
        self.fast_api.add_api_route(
            path="/receive_data/{sending_address}/{data}",
            endpoint=self.receive_data,
            methods=["POST"]
        )

        self.fast_api.add_api_route(
            path="/send_data/{receiving_address}/{data}",
            endpoint=self.send_data,
            methods=["POST"]
        )

    def start_server(self):
        try:
            server_config = Config(app=self.fast_api, host="0.0.0.0", port=self.port)
            server_task = self.server_loop.create_task(Server(config=server_config).serve())

        except Exception as e:
            httpx.post(f"http://127.0.0.1:8000/Error_{e}")

    def receive_data(self, sending_address, data):
        pass

    def send_data(self, offset_data: dict, receiving_address: str, receiving_port: int):
        # data = self.gather_data()

        print(offset_data)

    def gather_data(self):
        try:
            data: dict = load_user_data(self.data_path)

            if "data" not in data.keys() or len(data["data"].keys()) == 0:
                return "No passwords found"

            else:
                data: dict = data["data"]

            decrypted_data = {}

            for service in list(data.keys()):
                for service_username in data[service].keys():
                    username_password = data[service][service_username]["password"]

                    if current_platform.lower() == "android":
                        username_iv = data[service][service_username]["iv"]
                        decrypted_key  = decrypt_data(data_to_decrypt=data[service][service_username]["key"], iv=username_iv)
                        decrypted_password = Fernet(decrypted_key).decrypt(username_password.encode())

                    else:
                        username_key = data[service][service_username]["key"]
                        decrypted_key = decrypt_data(data_to_decrypt=username_key)
                        print(f"Decrypted key is: {decrypted_key}")
                        decrypted_password = decrypt_data(data_to_decrypt=username_password.encode(), key_to_use=decrypted_key)

                    if service in decrypted_data.keys():
                        decrypted_data[service][service_username] = {
                            "password": decrypted_password,
                            "key": decrypted_key
                        }

                    else:
                        decrypted_data[service] = {
                            service_username: {
                                "password": decrypted_password,
                                "key": decrypted_key
                            }
                        }

        except Exception as e:
            httpx.post(f"http://127.0.0.1:8000/Error_{e}")

    def command_listener(self):
        try:
            httpx.post("http://127.0.0.1:8000/'Started_command_executor'")

            while True:
                if self.is_command_complete is True:
                    if self.command["COMMAND"] == "SEND":
                        offset_data = offset_user_data(
                            user_data=load_user_data(
                                password_file_path=self.command["PATH"]
                            )
                        )

                        self.send_data(
                            offset_data=offset_data,
                            receiving_port=self.command["PORT"],
                            receiving_address=self.command["ADDRESS"]
                        )

                else:
                    continue

        except Exception as e:
            httpx.post(f"http://127.0.0.1:8000/Error_{e}")

    def message_listener(self):
        try:
            httpx.post("http://127.0.0.1:8000/'Started_message_listener'")

            while True:
                if not self.comms_pipe.poll(timeout=5):
                    httpx.post("http://127.0.0.1:8000/'Poll timeout reached'")
                    continue

                message = self.comms_pipe.recv()

                httpx.post("http://127.0.0.1:8000/'Received_new_message'")

                if isinstance(message, bytes):
                    message = message.decode()
                else:
                    message = str(message)

                httpx.post(f"http://127.0.0.1:8000/{message.replace(' ', '_')}")

                if message == "DONE":
                    self.is_command_complete = True

                elif message != "DONE" and self.is_command_complete is True:
                    self.is_command_complete = False
                    self.command += message

                else:
                    self.command += message

        except Exception as e:
            httpx.post(f"http://127.0.0.1:8000/Error_{e}")