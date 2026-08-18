import json

import json_repair
import toga
import queue
import uvicorn
import asyncio
import threading
import traceback
from .utils import *
from pathlib import Path
from fastapi import FastAPI
from queue import Queue, ShutDown
from toga.app import App as BastionPass
from contextlib import asynccontextmanager
from toga.platform import current_platform
from httpx import post, ConnectError, ConnectTimeout

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

        message_listener = asyncio.create_task(self.message_listener())
        # asyncio.create_task(self.command_listener())

        yield

        self.shutdown_in_progress = True
        message_listener.cancel()

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
                        "message": "Adding receive data route"
                    }
                ) + "DONE"
            )

            self.fast_api.add_api_route(
                path="/receive_data/{offset_string}",
                endpoint=self.receive_data,
                methods=["POST"]
            )

            # self.app_queue.put_nowait("Finished adding first and second route DONE")
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": "Finished adding receive data route"
                    }
                ) + "DONE"
            )
        except Exception:
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

    def receive_data(self, data_offset: int = 0, offset_string: str = ""):

        if data_offset == 0 and offset_string != "":
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "input_required",
                        "message": "Please provide the offset number generated by the receiving device",
                        "function": "self.receive_data",
                        "param": "data_offset"
                    }
                ) + "DONE"
            )

            with open(Path(toga.App.app.paths.cache,".offset_data.txt"), mode="w") as offset_file:
                json.dump(offset_string, offset_file, indent=4)

        elif offset_string == "" and data_offset != 0:
            with open(Path(toga.App.app.paths.cache, ".offset_data.txt")) as offset_file:
                offset_string = offset_file.read()

            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "gui_message",
                        "message": f"Offset string is: {offset_string}"
                    }
                ) + "DONE"
            )

            offset_dictionary = json_repair.loads(offset_string)

            if offset_dictionary == "":
                return self.app_queue.put_nowait(
                    json.dumps(
                        {
                            "message_type": "error",
                            "message": f"Unable to deoffset received data. Received data is: {offset_dictionary}"
                        }
                    ) + "DONE"
                )

            for service in offset_dictionary:
                service = deoffset_string(
                    string_to_deoffset=service,
                    data_offset=data_offset
                )

                print(service)

            # data = deoffset_string(
            #     string_to_deoffset=offset_string,
            #     data_offset=data_offset
            # )

            # data = json.loads(data)

            offset_list = [
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
                "-"
                "!"
            ]

            # TODO: Can't continue without offset string!!!
            # data = [offset_list[offset_list.index(character)] for character in offset_data.split(" ") if character[-1] != "!"]

        else:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error",
                        "message": f"Unexpected values for data or data_offset. \nData is: {offset_string} \nData offset is: {data_offset}"
                    }
                ) + "DONE"
            )


    def send_data(self, offset_data: dict, receiving_address: str, receiving_port: int):
        self.app_queue.put_nowait(
            json.dumps(
                {
                    "message_type": "message",
                    "message": f"Send data called, attempting to send data to receiving device. \nReceiving address: {receiving_address} \n{receiving_port}"
                }
            )
        )

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

        except ConnectTimeout:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error",
                        "message": "ERROR: Connection timed out while sending data to receiving device."
                    }
                ) + "DONE"
            )

        except Exception:
            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "error_with_traceback",
                        "message": "An unhandled error occurred while sending data to receiving device.",
                        "traceback": traceback.format_exc()
                    }
                )
            )
            # self.app_queue.put_nowait("ERROR: Unable to connect to receiving device. Please make sure receiving device is ready to receive data and connected to the same network.")

    def search_for_command(self, message_to_search: dict):

        if message_to_search["command"] == "send":
            offset_string, offset_number = offset_user_data(
                load_user_data(
                    password_file_path=Path(message_to_search["path"])
                )
            )

            self.send_data(
                offset_data=offset_string,
                receiving_address=message_to_search["address"],
                receiving_port=message_to_search["port"]
            )

            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "gui_message",
                        "message": f"The data offset is: {offset_number}. Please enter it into the receiving device when requested."
                    }
                ) + "DONE"
            )

        elif message_to_search["command"] == "required_input":

            exec(f"{message_to_search['function']}({message_to_search['param']}={message_to_search['message']})")


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
        message_loop = asyncio.get_running_loop()
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
                try:
                    message += await message_loop.run_in_executor(None, self.server_queue.get)

                except queue.Empty:
                    await asyncio.sleep(0.001)
                    continue
                # message += await self.server_queue.get()
                # message = self.comms_pipe.get()

                if isinstance(message, bytes):
                    message = message.decode()
                else:
                    message = str(message)

                if message.endswith("DONE"):
                    message_as_dictionary = json_repair.loads(message.replace("DONE", ""))
                    self.search_for_command(message_to_search=message_as_dictionary)

                    message = ""
                #     self.is_command_complete = True
                #     message = ""
                #
                # elif not message.endswith("DONE") and self.is_command_complete is True:
                #     self.is_command_complete = False
                #     self.command += message

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