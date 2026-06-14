import os
import toga
import json
import uvicorn
import json_repair
from fastapi import FastAPI

fastapi_server = FastAPI()

class MigrationServer:
    @staticmethod
    @fastapi_server.get("/")
    def home_page():
        return "This is the home page"

    @staticmethod
    @fastapi_server.post("/{current_user}/{user_data}/{main_key}")
    def receive_user_data(current_user: str, user_data: str, main_key: str):

        data_path = toga.App.app.paths.data

        user_data = json_repair.loads(user_data)

        print(user_data)

        if toga.platform.current_platform.lower() == "android":
            for offset_service in user_data:
                for offset_username in user_data[offset_service]:
                    offset_password = user_data[offset_service][offset_username]["password"]
                    offset_key = user_data[offset_service][offset_username]["key"]

                    password_list = offset_password.split(" ")
                    key_list = offset_key.split(" ")

                    for character in password_list:
                        print(character)

        # with open(os.path.join(data_path, current_user, ".passwords.json"), mode="w") as passwords_file:
        #     json.dump(user_data, passwords_file)

        # toga.App.app.migration_successful = True

        return {
            "success": True,
            "messages": None
        }

    @staticmethod
    @fastapi_server.post("/shutdown")
    def shutdown_server():
        toga.App.app.server_task.cancel()
        print("Shutting down...")
        return "Shutting down..."

    @staticmethod
    def set_up_server(event_loop: str, port: str):

        server_config = uvicorn.Config(fastapi_server, host="0.0.0.0", port=int(port), loop=event_loop)
        server = uvicorn.Server(config=server_config)

        return server