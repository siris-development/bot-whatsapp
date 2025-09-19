# 📱 WhatsApp Appointment Bot

This project is a WhatsApp bot designed to automate the appointment scheduling process. It uses a graph-based architecture to manage conversation flows, integrates with multiple AI model providers, and connects to an external server (MCP) for business logic.

## 📋 Table of Contents

  - [🚀 Getting Started](https://www.google.com/search?q=%23-getting-started)
      - [Prerequisites](https://www.google.com/search?q=%23prerequisites)
      - [Installation](https://www.google.com/search?q=%23installation)
  - [⚙️ Usage](https://www.google.com/search?q=%23%EF%B8%8F-usage)
      - [Running with Docker](https://www.google.com/search?q=%23running-with-docker)
      - [Running Locally](https://www.google.com/search?q=%23running-locally)
  - [🧪 Testing](https://www.google.com/search?q=%23-testing)
      - [Testing Prerequisites](https://www.google.com/search?q=%23testing-prerequisites)
      - [Expected Graph Flow](https://www.google.com/search?q=%23expected-graph-flow)
      - [Test Cases](https://www.google.com/search?q=%23test-cases)
      - [Debugging Tips](https://www.google.com/search?q=%23debugging-tips)
  - [🔌 API Endpoint](https://www.google.com/search?q=%23-api-endpoint)

-----

## 🚀 Getting Started

Follow these instructions to get the project set up and running on your local machine.

### Prerequisites

Make sure you have the following software installed:

  * **Python** (e.g., 3.11.6)
  * **Docker** (for containerized execution)
  * **Redis** (for state management)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```
2.  **Create a virtual environment:**
      * We recommend using `venv` for managing Python packages.
        ```bash
        # Create the environment
        python3 -m venv bot-whatsapp-env

        # Activate the environment
        # On macOS/Linux:
        source bot-whatsapp-env/bin/activate
        # On Windows (PowerShell):
        .\bot-whatsapp-env\Scripts\Activate.ps1
        ```
      * *(Optional)* If you use `pyenv` to manage Python versions, you can use `pyenv-virtualenv`.
        ```bash
        # Install the desired Python version
        pyenv install 3.11.6
        # Create and activate the virtual environment
        pyenv virtualenv 3.11.6 bot-whatsapp-env
        pyenv activate bot-whatsapp-env
        ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
      * Create a `.env` file based on the `.env.example` template.
      * Set up your API keys for the desired model providers (OpenAI, Anthropic, etc.) and other required configurations.

-----

## ⚙️ Usage

### Running with Docker

1.  **Pull the latest image from Docker Hub:**
    ```bash
    docker pull siris837/bot-whatsapp:latest
    ```
2.  **Run the container:**
      * This command starts the container and maps port 80 to the host.
    <!-- end list -->
    ```bash
    docker run -d \
      --name bot-whatsapp \
      -p 80:80 \
      siris837/bot-whatsapp:latest
    ```
      * **Note:** For a production setup, you may need to pass environment variables using an `--env-file` flag.

The bot will be available at `http://localhost:80`.

### Running Locally

Once you have completed the installation steps, you can run the application with `uvicorn`. This command will start a local server that automatically reloads on code changes.

```bash
uvicorn app.api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

-----

## 🧪 Testing

This section outlines how to test the graph, its tools, and different components.

### Testing Prerequisites

Before running tests, ensure the following are ready:

1.  **Redis Server**: The Redis server must be running and accessible.
2.  **Environment Variables**: Your API keys for the model providers are correctly set in your environment.
3.  **MCP Server**: The MCP (Master Control Program) server is running and its endpoints are accessible.

### Expected Graph Flow

The conversation logic follows a defined path through the graph:

1.  **Start** → `determine_entry_point` (Checks if a user is already selected).
2.  **No user selected** → `llm_user_selection` (Prompts the AI to identify the user from the message).
3.  **User identified** → `user_approved` or `user_rejected` (Checks if the user has permission to schedule).
4.  **User approved** → `agent_node` (The main agent takes over to handle the scheduling task).
5.  **Agent processing** → `tools` (Executes tools like `get_sedes` or `get_citas_disponibles`) or `END` (Finishes the conversation).
6.  **Tools executed** → The flow returns to the `agent_node` with the tool's output.

### Test Cases

Here are various Python snippets to test different parts of the graph.

```python
# The state object passed to the graph on the first interaction
initial_state = {
    "nit": "900410267",
    "to": "3106400794",
    "users": [
        {
            "idUsuario": 25,
            "numDocUsr": "25000000",
            "nombreCompleto": "JOJOA JOJOA AVELINO AVELINO",
            "msgStatus": "Hola, JOJOA JOJOA AVELINO AVELINO, Lo sentimos, usted no es base propia de la IPS...",
            "puedeAgendar": "NO"
        },
        {
            "idUsuario": 29,
            "numDocUsr": "29000000",
            "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
            "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento...",
            "puedeAgendar": "SI"
        }
    ],
    "msgInit": "Buenos días",
    "phoneNumberId": "672067049329170",
    "idResolucion": 2,
    "modelProvider": "openai"
}
```
These tests validate the logic for identifying and selecting a user from the conversation.

**Test Case A: Valid User Selection**
The `llm_user_selection` node should identify the correct user and populate the `selectedUser` object in the state.

```python
# Input state for the selection node
state_before_selection = {
    **initial_state,
    "messages": ["Quiero agendar una cita para Taimbud"]
}

# Expected state *after* the selection node runs successfully
state_after_selection = {
    **initial_state,
    "messages": ["Quiero agendar una cita para Taimbud"],
    "selectedUser": {
        "idUsuario": 29,
        "numDocUsr": "29000000",
        "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
        "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento...",
        "puedeAgendar": "SI"
    }
}
```

**Test Case B: User Without Permission**
The graph should select the user but route them to the `user_rejected` path because `puedeAgendar` is "NO".

```python
state_with_permissionless_user = {
    **initial_state,
    "messages": ["Necesito una cita para Jojoa"],
    "selectedUser": { # This would be populated by the selection node
        "idUsuario": 25,
        "numDocUsr": "25000000",
        "nombreCompleto": "JOJOA JOJOA AVELINO AVELINO",
        "msgStatus": "Hola, JOJOA JOJOA AVELINO AVELINO, Lo sentimos, usted no es base propia de la IPS...",
        "puedeAgendar": "NO"
    }
}
```

**Test Case C: Invalid or Unclear User Selection**
If the user's input is ambiguous or doesn't match anyone, the graph should ask for clarification.

```python
state_with_invalid_user = {
    **initial_state,
    "messages": ["Quiero una cita para una persona que no está en la lista"]
}
# The graph should respond by asking to clarify which user should be selected.
```
**Test the complete graph flow:**

```python
from app.graph import invoke_graph

# Example of a state where a user is already selected and can schedule
test_state = {
    "nit": "900410267",
    "to": "3106400794",
    "users": [
        {
            "idUsuario": 29,
            "numDocUsr": "29000000",
            "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
            "msgStatus": "Hola...",
            "puedeAgendar": "SI"
        }
    ],
    "selectedUser": { # User is pre-selected
        "idUsuario": 29,
        "numDocUsr": "29000000",
        "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
        "msgStatus": "Hola...",
        "puedeAgendar": "SI"
    },
    "msgInit": "Buenos días",
    "phoneNumberId": "672067049329170",
    "idResolucion": 2,
    "modelProvider": "openai",
    "messages": ["Quiero una cita de medicina general en la sede principal para mañana"]
}

result = invoke_graph(test_state)
print("Graph result:", result)
```

**Test individual tools:**
You can also test the tools that connect to the MCP server directly.

```python
# Import tool functions
from tools.get_sedes import get_sedes
from tools.get_especialidades import get_especialidades
from tools.get_citas_disponibles import get_citas_disponibles

# Test get_sedes
sedes = get_sedes.invoke({"nit": 900410267})
print("Sedes:", sedes)

# Test get_citas_disponibles
citas = get_citas_disponibles.invoke({
    "nit": 900410267,
    "idSede": 1,
    "idEspecialidad": 2,
    "fecha": "2025-09-19"
})
print("Citas disponibles:", citas)
```
**Test with different model providers:**
Simply change the `modelProvider` key in the state object.

```python
# Test with Anthropic
test_state_anthropic = {
    **initial_state,
    "modelProvider": "anthropic",
    "messages": ["Quiero agendar una cita"]
}

# Test with Ollama
test_state_ollama = {
    **initial_state,
    "modelProvider": "ollama",
    "messages": ["Quiero agendar una cita"]
}
```

**Test error handling:**
The graph should handle invalid or incomplete state objects gracefully.

```python
# Test with missing required fields (e.g., 'users')
error_state = {
    "nit": "900410267",
    "to": "3106400794"
}

# Test with an invalid NIT that tools might reject
invalid_nit_state = {
    **initial_state,
    "nit": "INVALID_NIT"
}
```

### Debugging Tips

If you encounter issues, check the following:

1.  **Redis Connection**: Ensure the Redis server is running and the connection details are correct.
2.  **MCP Server**: Use `curl` or a client like Postman to test the MCP server endpoints directly and verify they are responding correctly.
3.  **Model Provider Keys**: Double-check that your API keys are valid and have not expired.
4.  **State Validation**: Ensure the state objects passed to the graph match the required Pydantic or TypedDict schema.
5.  **Tool Responses**: Check that the data format returned by each tool is exactly what the agent expects.

-----

## 🔌 API Endpoint

You can test the full flow by sending a POST request to the `/webhook` endpoint.

```bash
curl -X POST "https://gateway.siriscloud.com.co/api/mcp-server?nit=900410267" \
  -H "Content-Type: application/json" \
  -d '{
    "nit": "900410267",
    "to": "3106400794",
    "users": [
        {
            "idUsuario": 29,
            "numDocUsr": "29000000",
            "nombreCompleto": "TAIMBUD TAIMBUD ABELINA ABELINA",
            "msgStatus": "Hola, TAIMBUD TAIMBUD ABELINA ABELINA, Bienvenido a la plataforma de agendamiento de citas.",
            "puedeAgendar": "SI"
        }
    ],
    "msgInit": "Buenos días",
    "phoneNumberId": "672067049329170",
    "idResolucion": 2,
    "modelProvider": "openai"
  }'
```