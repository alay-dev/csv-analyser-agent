from uuid import uuid4
from nodes import router, generate_graph_agent, analytical_response_agent, load_and_analyze_csv, generate_dashboard_entities, classify_message
from shared import State
from langgraph.graph import StateGraph, START, END

def create_graph():
    # Compile the LangGraph
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
        {"generate_graph": "generate_graph", "analytical_response": "analytical_response", "generate_dashboard": "generate_dashboard"}
    )
    graph_builder.add_edge("generate_dashboard", END)
    graph_builder.add_edge("generate_graph", END)
    graph_builder.add_edge("analytical_response", END)
    return graph_builder.compile()

def initialize_state(csv_path="sample.csv"):
    # Create initial state
    thread_id = str(uuid4())
    
    global_state = State({
        "thread_id": thread_id,
        "csv_path": csv_path,
        "messages": [],
        "message_type": None
    })
    
    # Load and analyze CSV
    global_state = load_and_analyze_csv(global_state)
    
    return global_state
