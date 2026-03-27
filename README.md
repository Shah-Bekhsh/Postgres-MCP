## Get Started

#### Virtual Environment
This project was created using uv as package manager. It is recommended to use uv as well (its actually quite easy, see [here](https://docs.astral.sh/uv/)).

Once you have cloned the repository, run the following command to install the dependencies in your virtual environment,

```uv sync```

and then the following command to activate your virtual environment.

```source .venv/bin/activate```

#### Database
Ensure you have Postgres installed and running on your machine.
You can also have a remote installation of a Postgres Database as well, however, I will leave the configuration for that up to you (the fields required in the .env should be the same)

Make sure you have the following DB related values configured in your .env file:

* DB_HOST
* DB_PORT
* DB_NAME
* DB_USER
* DB_PASSWORD

#### Chat Agent
In this project we have used Ollama to run the Qwen2.5:7b locally. To configure Ollama, make sure you have the following fields set in your .env file:

* OLLAMA_HOST // host FQDN or IP followed by :PORT
* OLLAMA_MODEL // qwen2.5:7b in our case

#### Running The Project
Once you have the .env file configured, navigate to the project root.

* Running MCP Server in a sandbox environment using MCP Inspector:

In project root, run the following command:

```mcp dev src/pg_mcp/server.py```

* Running the application by creating an MCP Client:

MAKE SURE YOU HAVE OLLAMA RUNNING. Then run the following:

```python src/pg_mcp/client.py```

This should put you in an interactive loop with the chat LLM. To exit the conversation, type ```exit```