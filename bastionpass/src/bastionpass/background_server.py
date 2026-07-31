import json

import uvicorn
import asyncio
import threading
import traceback
from .utils import *
from pathlib import Path
from fastapi import FastAPI
from httpx import post, ConnectError
from toga.app import App as BastionPass
from contextlib import asynccontextmanager
from toga.platform import current_platform
from queue import Queue, ShutDown

class BackgroundServer:
    @asynccontextmanager
    async def app_lifespan(self, app):
        self.app_queue.put_nowait(
            json.dumps(
                {
                    "message_type": "message",
                    "message": "FastAPI app started"
                }
            ) + "DONE"
        )
        # self.app_queue.put_nowait("FastAPI app started DONE")
        # asyncio.create_task(
        #     asyncio.to_thread(
        #         app_object.app_queue.put_nowait,
        #         "Lifespan thingy called DONE"
        #     )
        # )

        asyncio.create_task(self.message_listener())
        # asyncio.create_task(self.command_listener())

        yield

        self.shutdown_in_progress = True

    def __init__(self, port: int, data_path: Path, username: str, server_queue: Queue, app_queue: Queue):
        try:

            self.server_queue: asyncio.Queue = server_queue
            self.app_queue: asyncio.Queue = app_queue
            self.shutdown_in_progress: bool = False
            self.data_path: Path = data_path
            self.fast_api = FastAPI(lifespan=self.app_lifespan)
            self.username: str = username
            self.port = port

            # self.app_queue.put_nowait("Adding endpoints DONE")
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": "Adding endpoints"
                    }
                ) + "DONE"
            )
            self.add_endpoints()

            # self.app_queue.put_nowait("Starting server DONE")
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": "Starting server"
                    }
                ) + "DONE"
            )
            server_started = self.start_server()

            if not server_started:
                raise Exception("Server didn't successfully start DONE")

        except Exception as e:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error_with_traceback",
                        "message": "An error occurred while initializing background server.",
                        "traceback": traceback.format_exc()
                    }
                )
            )
            # self.app_queue.put_nowait(f"Error {e}")

    def add_endpoints(self):
        try:
            # self.app_queue.put_nowait("Adding first and second route DONE")
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": "Adding first and second route"
                    }
                ) + "DONE"
            )

            self.fast_api.add_api_route(
                path="/receive_data/{data}",
                endpoint=self.receive_data,
                methods=["POST"]
            )

            self.fast_api.add_api_route(
                path="/send_data/{receiving_address}/{data}",
                endpoint=self.send_data,
                methods=["POST"]
            )

            # self.app_queue.put_nowait("Finished adding first and second route DONE")
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": "Finished adding first and second route"
                    }
                ) + "DONE"
            )

        except Exception as e:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error_with_traceback",
                        "message": "An error occurred while adding server endpoints.",
                        "traceback": traceback.format_exc()
                    }
                ) + "DONE"
            )
            # self.app_queue.put_nowait(f"Error: {e}")

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
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error_with_traceback",
                        "message": "An error occurred while starting the server.",
                        "traceback": traceback.format_exc()
                    }
                )
            )
            # self.app_queue.put_nowait(f"Error {e}")
            return False

    def receive_data(self, data):
        pass

    def send_data(self, offset_data: dict, receiving_address: str, receiving_port: int):
        try:
            post(f"http://{receiving_address}:{receiving_port}/receive_data/{offset_data}")

        except ConnectError:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error",
                        "message": "ERROR: Unable to connect to receiving device. Please make sure receiving device is ready to receive data and connected to the same network."
                    }
                ) + "DONE"
            )
            # self.app_queue.put_nowait("ERROR: Unable to connect to receiving device. Please make sure receiving device is ready to receive data and connected to the same network.")

    def search_for_command(self, message_to_search: dict):

        if message_to_search["command"] == "send":
            self.send_data(
                offset_data=offset_user_data(
                    load_user_data(
                        password_file_path=Path(message_to_search["path"])
                    )
                ),
                receiving_address=message_to_search["address"],
                receiving_port=message_to_search["port"]
            )
        # self.app_queue.put_nowait("Started command listener DONE")
        # while not self.shutdown_in_progress:
        #     if self.is_command_complete is True:
        #         if self.command["COMMAND"] == "SEND":
        #             offset_data = offset_user_data(
        #                 user_data=load_user_data(
        #                     password_file_path=self.command["PATH"]
        #                 )
        #             )
        # 
        #             self.send_data(
        #                 offset_data=offset_data,
        #                 receiving_port=self.command["PORT"],
        #                 receiving_address=self.command["ADDRESS"]
        #             )
        # 
        #     else:
        #         await asyncio.sleep(0.01)
        #         continue

    async def message_listener(self):
        try:
            self.app_queue.put_nowait(
                json.dumps(
                    {"message_type": "message",
                     "message": "Started message listener"
                     }
                ) + "DONE"
            )
            # self.app_queue.put_nowait("Started message listener DONE")
            message = ""

            while not self.shutdown_in_progress:
                message += self.server_queue.get()
                # message = self.comms_pipe.get()

                if isinstance(message, bytes):
                    message = message.decode()
                else:
                    message = str(message)

                if message.endswith("DONE"):
                    message_as_dictionary = json_repair.loads(message.replace("DONE", ""))
                    self.search_for_command(message_to_search=message_as_dictionary)
                    # self.is_command_complete = True
                #     message = ""
                # 
                # elif not message.endswith("DONE") and self.is_command_complete is True:
                #     self.is_command_complete = False
                    # self.command += message

                elif message == "SHUTDOWN":
                    self.shutdown_in_progress = True
                    # self.event_listener_thread.join()
                    # self.command_executor_thread.join()
                    # self.server_loop.stop()

        except ShutDown:
            self.shutdown_in_progress = True

        except Exception as e:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error_with_traceback",
                        "message": "An error occurred while listening for messages.",
                        "traceback": traceback.format_exc()
                    }
                ) + "DONE"
            )
            # self.app_queue.put_nowait(f"An error occurred while listening for messages. Error {traceback.format_exc()}")