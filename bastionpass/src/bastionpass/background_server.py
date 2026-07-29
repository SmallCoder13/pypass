import asyncio
import uvicorn
import threading
from .utils import *
from pathlib import Path
from fastapi import FastAPI
from toga.app import App as BastionPass
from toga.platform import current_platform
from contextlib import asynccontextmanager

def create_app(app_object):
    @asynccontextmanager
    async def app_lifespan(app):
        # asyncio.create_task(
        #     asyncio.to_thread(
        #         app_object.app_queue.put,
        #         "'Lifespan thingy called'"
        #     )
        # )
        asyncio.create_task(app_object.message_listener())
        asyncio.create_task(app_object.command_listener())

        yield

        app_object.shutdown_in_progress = True
    return FastAPI(lifespan=app_lifespan)

class BackgroundServer:
    def __init__(self, port: int, data_path: Path, username: str, server_queue: asyncio.Queue, app_queue: asyncio.Queue):
        try:

            self.server_queue: asyncio.Queue = server_queue
            self.app_queue: asyncio.Queue = app_queue
            self.shutdown_in_progress: bool = False
            self.is_command_complete: bool = False
            self.data_path: Path = data_path
            self.fast_api = create_app(self)
            self.username: str = username
            self.command = {}
            self.port = port

            self.app_queue.put_nowait("Adding endpoints")
            self.add_endpoints()

            self.app_queue.put_nowait("Starting server")
            server_started = self.start_server()

            if not server_started:
                raise Exception("Server didn't successfully start")

        except Exception as e:
            self.app_queue.put_nowait(f"Error {e}")

    def add_endpoints(self):
        try:
            self.app_queue.put_nowait("Adding first and second route")

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

        except Exception as e:
            self.app_queue.put_nowait(f"Error: {e}")

        return None

    def start_server(self):
        """
        Attempts to start background server. If server startup is successful, this function returns True. If an exception is thrown during startup, this function will return False
        """
        try:
            threading.Thread(
                target=uvicorn.run,
                kwargs={
                    "app": self.fast_api,
                    "host": "0.0.0.0",
                    "port": self.port
                },
                daemon=True
            ).start()

            return True

        except Exception as e:
            self.app_queue.put_nowait(f"Error {e}")
            return False

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
            self.app_queue.put_nowait(f"Error {e}")

    async def command_listener(self):
        while not self.shutdown_in_progress:
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
                await asyncio.sleep(0.01)
                continue

    async def message_listener(self):
        try:
            await self.app_queue.put("Started message listener")
            message = ""

            while not self.shutdown_in_progress:
                message += await self.server_queue.get()
                # message = self.comms_pipe.get()

                await self.app_queue.put("Received new message")

                if isinstance(message, bytes):
                    message = message.decode()
                else:
                    message = str(message)

                await self.app_queue.put(message.replace(' ', '_'))

                if message[-4:] == "DONE":
                    self.is_command_complete = True
                    message = ""

                elif message[-4:] != "DONE" and self.is_command_complete is True:
                    self.is_command_complete = False
                    self.command.update(json_repair.loads(message))
                    # self.command += message

                elif message == "SHUTDOWN":
                    self.shutdown_in_progress = True
                    # self.event_listener_thread.join()
                    # self.command_executor_thread.join()
                    # self.server_loop.stop()

                else:
                    self.command.update(json_repair.loads(message))
                    # self.command += message

        except Exception as e:
            await self.app_queue.put(f"Error {e}")