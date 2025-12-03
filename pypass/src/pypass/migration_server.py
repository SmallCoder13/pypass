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

        user_data = json.loads(user_data)

        env_data = json_repair.from_file(os.path.join(data_path, ".env"))
        env_data["MAIN_KEY"] = main_key

        with open(os.path.join(data_path, current_user, ".passwords.json"), mode="w") as passwords_file:
            json.dump(user_data, passwords_file)

        with open(os.path.join(data_path, ".env"), mode="w") as env_file:
            json.dump(env_data, env_file)

        app_env = json_repair.from_file(os.path.join(data_path, ".env"))
        app_env["MIGRATION_SUCCESSFUL"] = "true"

        with open(os.path.join(data_path, ".env"), mode="w") as env_file:
            json.dump(app_env, env_file)

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