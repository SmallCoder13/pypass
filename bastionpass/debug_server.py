from fastapi import FastAPI
import asyncio
import uvicorn

app = FastAPI()

@app.post("/{message}")
def print_message(message):
    print(message)

if __name__ == "__main__":
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config=config)

    server_thread = asyncio.new_event_loop()
    server_thread.create_task(server.serve())
    server_thread.run_forever()
