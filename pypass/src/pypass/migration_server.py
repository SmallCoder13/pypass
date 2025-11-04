import os
import json
import json_repair
import uvicorn
from fastapi import FastAPI

fastapi_server = FastAPI()

class MigrationServer:
    @staticmethod
    @fastapi_server.get("/")
    def home_page():
        return "This is the home page"

    @fastapi_server.post("/{current_user}/{user_data}/{main_key}/{data_path}")
    def receive_user_data(current_user: str, user_data: str, main_key: str, data_path: str):
        data_path = data_path.replace("-", "/")

        user_data = json.loads(user_data)

        env_data = json_repair.from_file(os.path.join(data_path, ".env"))
        env_data["MAIN_KEY"] = main_key


        with open(os.path.join(data_path, current_user, ".passwords.json"), mode="w") as passwords_file:
            json.dump(user_data, passwords_file)

        with open(os.path.join(data_path, ".env"), mode="w") as env_file:
            json.dump(env_data, env_file)

        os.environ['MIGRATION_SUCCESSFUL'] = "true"

        return {
            "success": True,
            "messages": None
        }

    def __init__(self):
        # fastapi_server.add_api_route("/{current_user}/{user_data}/{main_key}/{data_path}", self.receive_user_data, methods=["POST"])
        uvicorn.run(fastapi_server, host="0.0.0.0", port=9001)

MigrationServer()