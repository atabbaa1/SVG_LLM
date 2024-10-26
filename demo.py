import getpass
import os

os.environ["ANTHROPIC_API_KEY"] = "Your Key Here"
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

_set_env(ANTHROPIC_API_KEY)


##############################################################################################################################################
########################################## THE FOLLOWING FUNCTIONALITY IMPLEMENTS A BASIC CHATBOT ############################################
##############################################################################################################################################
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# Adding memory requires a "checkpointer" and a "thread_id"
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import ToolNode, tools_condition

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

# Every 'node' we define will receive the current State as input and return a value that updates that state
# 'messages' will appended to the current list, rather than directly overwritten due to the `add_messages` function in the Annotated syntax
graph_builder = StateGraph(State)



llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# To add tools to the llm
# tool = some tool
# tools = [tool]
# llm = llm.bind_tools(tools=[tools])

def chatbot_node(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot_node)


# tool_node = ToolNode(tools=[tool])
# graph_builder.add_node("tools", tool_node)

# Conditional edges route control flow from one node to the next
# The imported tools_condition function .........
# graph_builder.add_conditional_edges(
#     "chatbot",
#     tools_condition,
# )
# # Any time a tool is called, we return to the chatbot to decide the next step
# graph_builder.add_edge("tools", "chatbot")
# graph_builder.add_edge(START, "chatbot")


# The following is an "in-memory" checkpointer, which will not save memory between sessions.
# LATER, change this to SqliteSaver or PostgressSaver and connect to our own database
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# You can visualize the graph using the get_graph() method and a draw method like draw_ascii() or draw_png()
from IPython.display import Image, display


try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass




# Below is the code to actually run the chatbot
config = {"configurable": {"thread_id": "basic_test"}}
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break