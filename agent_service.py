import os
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

from todo_service import add_task, delete_task, get_tasks, update_task

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL = "gemini-2.5-flash"

TASK_TYPES = ["task", "event", "reminder"]
TASK_STATUSES = ["pending", "in_progress", "completed"]

DATE_DESCRIPTION = "Date in YYYY-MM-DD format"

GET_TASKS_DECL = types.FunctionDeclaration(
    name="get_tasks",
    description="Fetch tasks from the system, optionally filtered by any combination of the given fields.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "Exact task code to look up"},
            "title": {"type": "string", "description": "Substring to search for in the task title"},
            "type": {"type": "string", "enum": TASK_TYPES},
            "status": {"type": "string", "enum": TASK_STATUSES},
            "start_date_from": {"type": "string", "description": f"{DATE_DESCRIPTION}. Lower bound (inclusive) for start_date"},
            "start_date_to": {"type": "string", "description": f"{DATE_DESCRIPTION}. Upper bound (inclusive) for start_date"},
            "end_date_from": {"type": "string", "description": f"{DATE_DESCRIPTION}. Lower bound (inclusive) for end_date"},
            "end_date_to": {"type": "string", "description": f"{DATE_DESCRIPTION}. Upper bound (inclusive) for end_date"},
        },
    },
)

ADD_TASK_DECL = types.FunctionDeclaration(
    name="add_task",
    description="Create a new task in the system.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short task title"},
            "description": {"type": "string", "description": "Detailed task description"},
            "type": {"type": "string", "enum": TASK_TYPES},
            "start_date": {"type": "string", "description": DATE_DESCRIPTION},
            "end_date": {"type": "string", "description": DATE_DESCRIPTION},
            "status": {"type": "string", "enum": TASK_STATUSES},
        },
        "required": ["title"],
    },
)

UPDATE_TASK_DECL = types.FunctionDeclaration(
    name="update_task",
    description="Update one or more fields of an existing task, identified by its code.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "Code of the task to update"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "type": {"type": "string", "enum": TASK_TYPES},
            "start_date": {"type": "string", "description": DATE_DESCRIPTION},
            "end_date": {"type": "string", "description": DATE_DESCRIPTION},
            "status": {"type": "string", "enum": TASK_STATUSES},
        },
        "required": ["code"],
    },
)

DELETE_TASK_DECL = types.FunctionDeclaration(
    name="delete_task",
    description="Delete a task from the system by its code.",
    parameters_json_schema={
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "Code of the task to delete"},
        },
        "required": ["code"],
    },
)

TOOLS = [
    types.Tool(
        function_declarations=[
            GET_TASKS_DECL,
            ADD_TASK_DECL,
            UPDATE_TASK_DECL,
            DELETE_TASK_DECL,
        ]
    )
]

AVAILABLE_FUNCTIONS = {
    "get_tasks": get_tasks,
    "add_task": add_task,
    "update_task": update_task,
    "delete_task": delete_task,
}


def _system_prompt() -> str:
    return (
        "You are a helpful task-management assistant. "
        f"Today's date is {date.today().isoformat()}. "
        "Use the provided functions to answer the user's request about their tasks: "
        "fetching, adding, updating or deleting them. "
        "The user usually refers to tasks by title or description, not by code. "
        "If you need a task's code in order to update or delete it, first call get_tasks "
        "to look it up (e.g. by title), then call update_task/delete_task with the code you found. "
        "Resolve relative dates (e.g. 'tomorrow', 'next week') to absolute YYYY-MM-DD dates "
        "yourself before calling a function. "
        "IMPORTANT: always reply in the exact same language the user's message was written in "
        "(e.g. if the user wrote in Hebrew, your entire reply must be in Hebrew)."
    )


def agent(query: str, max_turns: int = 5) -> str:
    config = types.GenerateContentConfig(
        system_instruction=_system_prompt(),
        tools=TOOLS,
    )

    contents = [types.Content(role="user", parts=[types.Part(text=query)])]

    for _ in range(max_turns):
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config,
        )

        if not response.function_calls:
            return response.text or "מצטערת, לא הצלחתי לנסח תשובה. אפשר לנסות שוב?"

        contents.append(response.candidates[0].content)

        for function_call in response.function_calls:
            function_to_call = AVAILABLE_FUNCTIONS[function_call.name]
            function_result = function_to_call(**function_call.args)

            function_response_part = types.Part.from_function_response(
                name=function_call.name,
                response={"result": function_result},
            )
            contents.append(types.Content(role="tool", parts=[function_response_part]))

    return "מצטערת, לא הצלחתי להשלים את הבקשה. אפשר לנסח אותה מחדש?"
