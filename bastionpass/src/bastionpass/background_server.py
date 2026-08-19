# import json
# import toga
# from toga.app import App as BastionPass
# from toga.platform import current_platform

import queue
import uvicorn
import asyncio
import threading
import traceback
import json_repair
from .utils import *
from pathlib import Path
from fastapi import FastAPI
from queue import Queue, ShutDown
from cryptography.fernet import Fernet
from contextlib import asynccontextmanager
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

            with open(Path(toga.App.app.paths.cache, ".offset_data.txt"), mode="w") as offset_file:
                json.dump(offset_string, offset_file, indent=4)

        elif offset_string == "" and data_offset != 0:
            offset_user_data = json_repair.loads(json_repair.from_file(Path(toga.App.app.paths.cache, ".offset_data.txt")))
            deoffset_user_data = {}

            if offset_user_data == "":
                return self.app_queue.put_nowait(
                    json.dumps(
                        {
                            "message_type": "error",
                            "message": "Unable to deoffset received data. Invalid data saved"
                        }
                    ) + "DONE"
                )

            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "message",
                        "message": f"offset user data is: {offset_user_data} \nData offset: {data_offset}"
                    }
                ) + "DONE"
            )

            for offset_service in offset_user_data.keys():
                service = deoffset_string(
                    string_to_deoffset=offset_service,
                    data_offset=data_offset
                )

                for offset_username in offset_user_data[offset_service].keys():
                    username = deoffset_string(
                        string_to_deoffset=offset_username,
                        data_offset=data_offset
                    )
                    password = deoffset_string(
                        string_to_deoffset=offset_user_data[offset_service][offset_username]["password"],
                        data_offset=data_offset
                    )
                    # key = deoffset_string(
                    #     string_to_deoffset=offset_user_data[offset_service][offset_username]["key"],
                    #     data_offset=data_offset
                    # )

                    key = Fernet.generate_key()

                    # if offset_user_data[offset_service][offset_username]["iv"] == "":
                    #     iv = ""
                    #
                    # else:
                    #     iv = deoffset_string(
                    #         string_to_deoffset=offset_user_data[offset_service][offset_username]["iv"],
                    #         data_offset=data_offset
                    #     )

                    self.app_queue.put_nowait(
                        json.dumps(
                            {
                                "message_type": "message",
                                "message": f"Key is: {key}"
                            }
                        ) + "DONE"
                    )

                    encrypted_password = encrypt_data(data_to_encrypt=password, key_to_use=key)["encrypted_data"]
                    encrypted_key, encryption_iv = encrypt_data(data_to_encrypt=key).values()

                    if isinstance(encrypted_password, bytes):
                        encrypted_password = encrypted_password.decode()

                    if isinstance(encrypted_key, bytes):
                        encrypted_key = encrypted_key.decode()

                    if isinstance(encryption_iv, bytes):
                        encryption_iv = encryption_iv.decode()

                    if service in deoffset_user_data.keys():
                        deoffset_user_data[service][username] = {
                            "password": encrypted_password,
                            "key": encrypted_key
                        }

                    else:
                        deoffset_user_data[service] = {
                            username: {
                                "password": encrypted_password,
                                "key": encrypted_key
                            }
                        }

                    if toga.platform.current_platform.lower() == "android":
                        deoffset_user_data[service][username]["iv"] = encryption_iv

            user_data = load_user_data(self.data_path)

            if "data" not in user_data.keys():
                user_data["data"] = {}

            for service in deoffset_user_data.keys():
                for username in deoffset_user_data[service].keys():
                    if service in user_data["data"].keys() and username in user_data["data"][service].keys():
                        user_data["data"][service][username] = {
                            "password": encrypted_password,
                            "key": encrypted_key
                        }

                    else:
                        user_data["data"][service] = deoffset_user_data[service]

            with open(self.data_path, mode="w") as data_file:
                json.dump(user_data, data_file, indent=4)

            self.app_queue.put_nowait(
                json.dumps(
                    {
                        "message_type": "gui_message",
                        "message": "Successfully migrated data!"
                    }
                ) + "DONE"
            )

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
        offset_user_data = {}

        if message_to_search["command"] == "send":
            user_data = load_user_data(password_file_path=Path(message_to_search["path"]))["data"]

            if user_data == "Password file path doesn't exist":
                self.app_queue.put_nowait(
                    json.dumps(
                        {
                            "message_type": "error",
                            "message": "Unable to offset user data. Password file path doesn't exist."
                        }
                    ) + "DONE"
                )

            elif user_data == "Invalid data saved":
                self.app_queue.put_nowait(
                    json.dumps(
                        {
                            "message_type": "error",
                            "message": "Unable to offset user data. Saved data isn't valid."
                        }
                    ) + "DONE"
                )

            for service in user_data.keys():
                offset_service, offset_number = offset_string(service)

                self.app_queue.put_nowait(
                    json.dumps(
                        {
                            "message_type": "message",
                            "message": f"Service data is: {user_data[service]}"
                        }
                    ) + "DONE"
                )

                for username in user_data[service].keys():
                    if toga.platform.current_platform.lower() == "android":
                        decrypted_key = decrypt_data(data_to_decrypt=user_data[service][username]["key"], iv=user_data[service][username]["iv"])

                    else:
                        decrypted_key = decrypt_data(data_to_decrypt=user_data[service][username]["key"])

                    offset_username = offset_string(username, offset_number)[0]
                    offset_password = offset_string(decrypt_data(data_to_decrypt=user_data[service][username]["password"], key_to_use=decrypted_key), offset_number)[0]
                    # offset_key = offset_string(decrypted_key, offset_number)[0]

                    # if "iv" in user_data[service][username].keys():
                    #     offset_iv = offset_string(user_data[service][username]["iv"], offset_number)[0]
                    #
                    # else:
                    #     offset_iv = ""

                    if offset_service not in offset_user_data.keys():
                        offset_user_data[offset_service] = {
                            offset_username: {
                                "password": offset_password,
                                # "key": offset_key,
                                # "iv": offset_iv
                            }
                        }

                    else:
                        offset_user_data[offset_service][offset_username] = {
                            "password": offset_password,
                            # "key": offset_key,
                            # "iv": offset_iv
                        }

            self.send_data(
                offset_data=offset_user_data,
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