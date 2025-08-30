from shared import State, llm
import pandas as pd
from pydantic import BaseModel, Field
from typing import  Literal


class MessageClassifier(BaseModel):
    message_type: Literal["generate_graph", "analytical_response", "generate_dashboard"] = Field(
        ...,
        description="Classify if the message requires to generate graph or analytical response"
    )


def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)
    
    # Get conversation history (excluding the last message which will be added separately)
    conversation_history = state["messages"][:-1] if len(state["messages"]) > 1 else []
    
    # Build conversation context from previous messages
    conversation_context = ""
    if conversation_history:
        conversation_context = "\n\n--- Previous Conversation ---\n"
        for msg in conversation_history:
            role = "User" if hasattr(msg, 'type') and msg.type == "human" else "Assistant"
            conversation_context += f"{role}: {msg.content}\n"
        conversation_context += "--- End Previous Conversation ---\n\n"

    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": f"""Classify the user message as either:
            - 'generate_dashboard': if it asks to generate a dashboard or a overall summary based on the given CSV data.
            - 'generate_graph': if it asks to generate graphs based on the given CSV data.
            - 'analytical_response': if it asks for an analytical response that doesn't require generating graphs.
            
            Consider the conversation context when making your classification. For example:
            - If the user has already asked for a dashboard, subsequent requests might be better classified as analytical responses
            - If the user is asking follow-up questions about previously generated graphs, consider the context
            - Look for patterns in the conversation to make more informed decisions
            
            {conversation_context}"""
        },
        {"role": "user", "content": last_message.content},
    ], config={"thread_id": state["thread_id"]})

    print(len(state["messages"]), "LENGTH")

    if result.message_type == "generate_dashboard":
        # If there are more than 2 messages already, switch to analytical response
        if len(state["messages"]) > 1:
            return {"message_type": "analytical_response"}

    print(result.message_type, "TYPE")
    return {"message_type": result.message_type}

