import os
import datetime
from dotenv import load_dotenv
import logging


# LLM
from langchain_openai import AzureChatOpenAI


# Prompting
from langchain_core.prompts import ChatPromptTemplate

# LangGraph core
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Your tools
from tools import (
    get_next_appointment,
    list_appointments,
    book_appointment,
    cancel_appointment,
)

logger = logging.getLogger("appointment_app")

# 🔐 Load environment variables

load_dotenv()

# 🤖 Initialize LLM 



llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0
)


# 🛠 Define tool groups

# Read-only tools
caller_tools1 = [
    get_next_appointment,
    list_appointments
]

# Action tools (mutating state)
caller_tools2 = [
    book_appointment,
    cancel_appointment
]

# All tools
all_tools = caller_tools1 + caller_tools2

# Convert tools into LangGraph nodes
tool_node1 = ToolNode(caller_tools1)
tool_node2 = ToolNode(caller_tools2)


# 🧠 Prompt for the agent

caller_prompt = """You are a personal assistant specializing in:

- Booking appointments
- Cancelling appointments
- Listing appointments
- Finding next available slots

-------------------------
CORE RULES
-------------------------

- Only handle appointment-related queries.

- Required fields for booking:
  client_name, date (year, month, day), time (hour, minute)

- Only proceed to booking when ALL required fields are available.

- If any required information is missing:
  Ask ONLY for the missing fields.

-------------------------
CANCELLATION RULES
-------------------------

- If multiple appointments exist:
  Show them as a numbered list.
  Ask the user to reply with the number (1, 2, 3).

- If the user provides a number:
  Use it directly to cancel.

- If a specific date and time is provided:
 Ask for confirmation with that sepcific appointment and cancel after confirmation.

-------------------------
CONTEXT HANDLING
-------------------------

- Maintain conversation context across turns.
- Reuse previously provided name, date, and time.
- Do NOT ask again for information already given.
- Extract structured details from user messages.

-------------------------
CONFIRMATION RULE
-------------------------

- Ask for confirmation ONLY for booking and cancellation.
- Ask confirmation only once when all booking details are available.
- If user confirms (yes, confirm, ok), proceed immediately.
- Do NOT ask for confirmation repeatedly.

-------------------------

Current time: {current_time}
"""

# Chat template (system + user messages)
caller_chat_template = ChatPromptTemplate.from_messages([
    ("system", caller_prompt),
    ("placeholder", "{messages}"),
])

# Bind tools to LLM
caller_model = caller_chat_template | llm.bind_tools(all_tools)


# 🧩 Agent Node (LLM reasoning step)

def chatbot(state: MessagesState):
    """
    This node:
    - Adds current time to context
    - Invokes LLM with tools
    - Returns updated messages
    """
    try:
        state["current_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        response = caller_model.invoke(state)
        logger.info("LLM responded")
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Agent error: {str(e)}", exc_info=True)
        raise



# 🔀 Router (decides next step)

def router(state: MessagesState):
    """
    Routes execution based on tool call:
    - Read-only → action1
    - Mutating → action2 (skipping human approval for API)
    """

    try:
        messages = state["messages"]
        tool_calls = messages[-1].tool_calls

        if tool_calls:
            tool_name = tool_calls[0]["name"]

            if tool_name in ["get_next_appointment", "list_appointments"]:
                return "action1"
            elif tool_name in ["book_appointment", "cancel_appointment"]:
                return "action2"

        return "end"
    except Exception as e:
        logger.error(f"Router error: {str(e)}", exc_info=True)
        return "end"



# 🏗 Build LangGraph workflow

workflow = StateGraph(MessagesState)

# Add nodes
workflow.add_node("agent", chatbot)
workflow.add_node("action1", tool_node1)
workflow.add_node("action2", tool_node2)


# Conditional edges from agent
workflow.add_conditional_edges(
    "agent",
    router,
    {
        "action1": "action1",
        "action2": "action2",
        "end": END,
    },
)

# Loop back after tool execution
workflow.add_edge("action1", "agent")
workflow.add_edge("action2", "agent")

# Entry point
workflow.set_entry_point("agent")


# 💾 Memory (for conversation state)

memory = MemorySaver()

# Compile graph
caller_app = workflow.compile(checkpointer=memory)