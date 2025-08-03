from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

from nodes import classify_message, router, generate_graph_agent, analytical_response_agent, load_and_analyze_csv, generate_dashboard_entities
from shared import State

from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Optional CORS middleware if calling from browser or frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load and analyze CSV once
csv_path = "ad_metrics_sample.csv"
thread_id = str(uuid4())

global_state = State({
    "thread_id": thread_id,
    "csv_path": csv_path,
    "messages": [],
    "message_type": None
})
global_state = load_and_analyze_csv(global_state)

# Compile the LangGraph once
graph_builder = StateGraph(State)
graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("generate_dashboard", generate_dashboard_entities)
graph_builder.add_node("generate_graph", generate_graph_agent)
graph_builder.add_node("analytical_response", analytical_response_agent)
graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {"generate_graph": "generate_graph", "analytical_response": "analytical_response" , "generate_dashboard": "generate_dashboard"}
)
graph_builder.add_edge("generate_dashboard", END)
graph_builder.add_edge("generate_graph", END)
graph_builder.add_edge("analytical_response", END)
graph = graph_builder.compile()


class QueryRequest(BaseModel):
    query: str


@app.post("/query")
def query_chatbot(request: QueryRequest):
    query = request.query

    global global_state
    global_state["messages"].append({"role": "user", "content": query})
    global_state = graph.invoke(global_state)

    if global_state.get("messages"):
        last_msg = global_state["messages"][-1]
        return {"response": last_msg.content, "type": last_msg.additional_kwargs.get("type", "TEXT")}

    return {"response": "Sorry, I couldn't process your query."}
