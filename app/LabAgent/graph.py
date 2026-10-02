from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, BaseMessage, SystemMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from model.load import get_model
from prompts import SYSTEM_PROMPT
from tools import TOOLS

MAX_TOOL_TURNS = 3


# graph state
class DeskState(TypedDict):

    messages: Annotated[list[AnyMessage], add_messages]
    tool_turns: int


# nodes
_tool_node = ToolNode(TOOLS)


def _assistant_node(state: DeskState) -> dict:

    turns = state.get("tool_turns", 0)
    model = get_model()

    # tools are only offered to the model while under the tool use limit
    if turns < MAX_TOOL_TURNS:
        runnable = model.bind_tools(TOOLS)
    else:
        runnable = model

    conversation = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]

    reply: BaseMessage = runnable.invoke(conversation)
    return {"messages": [reply]}


def _tools(state: DeskState) -> dict:

    result = _tool_node.invoke(state)
    return {
        "messages": result["messages"],
        "tool_turns": state.get("tool_turns", 0) + 1,
    }


def _route_after_assistant(state: DeskState) -> str:

    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_graph(checkpointer=None):

    graph = StateGraph(DeskState)
    graph.add_node("assistant", _assistant_node)
    graph.add_node("tools", _tools)

    graph.add_edge(START, "assistant")

    graph.add_conditional_edges(
        "assistant",
        _route_after_assistant,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge("tools", "assistant")

    return graph.compile(checkpointer=checkpointer, name="maintenance-desk")