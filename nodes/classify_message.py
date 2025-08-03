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


    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": """Classify the user message as either:
            - 'generate_dashboard': if it asks to generate a dashboard or a overall summary based on the given CSV data.
            - 'generate_graph': if it asks to generate graphs based on the given CSV data.
            - 'analytical_response': if it asks for an analytical response that doesn't require generating graphs.
            """
        },
        {"role": "user", "content": last_message.content},
    ], config={"thread_id": state["thread_id"]})

    print(result.message_type, "TYPE")
    return {"message_type": result.message_type}

