from .utils import *
from pathlib import Path
from json_repair import json_repair
from toga.platform import current_platform

class SendData:
    def __init__(self, data_path: Path, username: str):
        self.data_path = data_path
        self.username = username

    def gather_data(self):
        data = json_repair.from_file(self.data_path)["data"]

        decrypted_data = {}

        for service, service_username in (data.keys(), data.values()):
            for username_password, username_iv in (data[service][service_username]["password"], data[service][service_username]["key"]):
                decrypted_password = decrypt_data(data_to_decrypt=username_password, iv=username_iv)

                if service in decrypted_data.keys():
                    decrypted_data[service][service_username] = {
                        "password": decrypted_password,
                        "key": username_iv
                    }

                else:
                    decrypted_data[service] = {
                        service_username: {
                            "password": decrypted_password,
                            "key": username_iv
                        }
                    }

        print(decrypted_data)
        return decrypted_data