import os
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def answer(state: AgentState, config: RunnableConfig) -> dict:
    model = ChatOpenAI(
        model=os.getenv("LITELLM_MODEL", "corporate-default"),
        base_url=os.environ["LITELLM_BASE_URL"],
        api_key=os.environ["LITELLM_API_KEY"],
        temperature=0,
    )

    response = model.invoke(state["messages"], config=config)
    return {"messages": [response]}


builder = StateGraph(AgentState)
builder.add_node("answer", answer)
builder.add_edge(START, "answer")
builder.add_edge("answer", END)

graph = builder.compile()

# LangGraph Server gestiona los callbacks de la ejecución.
# Añadimos Langfuse al grafo compilado, sin modificar el gestor recibido
# por el nodo.
if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
    from langfuse.langchain import CallbackHandler

    graph = graph.with_config({"callbacks": [CallbackHandler()]})