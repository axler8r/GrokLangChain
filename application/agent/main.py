from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()


def main() -> str:
    """Returns a greeting from the agent.

    Returns:
        str: Greeting message.
    """
    return "Hello from agent!"


@app.get("/", response_class=PlainTextResponse)
def read_root() -> str:
    """FastAPI endpoint that returns the agent greeting.

    Returns:
        str: Greeting message.
    """
    return main()


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("application.agent.main:app", host="0.0.0.0", port=8000, reload=True)
