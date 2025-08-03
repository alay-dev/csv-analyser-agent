from shared import State

def router(state: State):
    message_type = state.get("message_type", "analytical_response")
    if message_type == "generate_graph":
        return {"next": "generate_graph"}
    if message_type == "generate_dashboard":
        return {"next": "generate_dashboard"}

    return {"next": "analytical_response"}
