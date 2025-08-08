from shared import State, llm, MultiChartResponse, AIMessage
from langchain.output_parsers import PydanticOutputParser

def generate_chart_agent(state: State):
    last_message = state["messages"][-1]
    schema = state["schema"]

    output_parser = PydanticOutputParser(pydantic_object=MultiChartResponse)

    messages = [
        {
            "role": "system",
            "content": f"""
You are a data visualization assistant. Based on the user's request and the dataset schema below,
generate a list of the most useful charts.

Each chart must:
- Be a separate object in a list.
- Use one of these chart types only: "LINE", "BAR", or "PIE"
- Have one x_axis and one y_axis
- Include inline data from the schema (based on sample rows)
- `"width"`: pixel width of the component (e.g. 600-1200)
- `"height"`: pixel height of the component (e.g. 100-600)


Suggested sizes:
- TEXT:
  - width: 1000-1200
  - height: 60-100
- CHART:
  - width: 600-800
  - height: 300-500
- TABLE:
  - width: 800-1000
  - height: 400-600

Your response must follow this Pydantic schema:
{output_parser.get_format_instructions()}


Schema:
{schema}
"""
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ]

    response = llm.invoke(messages, config={"thread_id": state["thread_id"]})

    # Parse structured response
    result = output_parser.parse(response.content)

    ai_message = AIMessage(
        content=f"{result.model_dump_json(indent=2)}", 
        additional_kwargs={"type": "CHART"}
    )
    return {"messages": [ai_message]}
