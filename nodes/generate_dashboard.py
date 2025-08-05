from shared import State, llm, ChartSpec, TableSpec
from typing import Literal, Optional, List
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

def generate_dashboard_entities(state: State):
    last_message = state["messages"][-1]
    schema = state["schema"]

    class DashboardEntity(BaseModel):
        entity_type: Literal["TEXT", "CHART", "TABLE"]
        x: int  # in pixels
        y: int  # in pixels
        width: int  # in pixels
        height: int  # in pixels
        text: Optional[str] = None
        chart: Optional[ChartSpec] = None
        table: Optional[TableSpec] = None

    class DashboardEntitiesResponse(BaseModel):
        items: List[DashboardEntity]

    output_parser = PydanticOutputParser(pydantic_object=DashboardEntitiesResponse)

    messages = [
        {
            "role": "system",
            "content": f"""
You are a dashboard generation assistant.

Based on the user's request and the dataset schema below, generate a relevant, well-structured dashboard layout.

The dashboard consists of multiple entities — each being a chart, table, or a section header (text).

---

⚙️ Layout Requirements (Pixel-based):

Each entity **must include pixel positioning**:
- `"x"`: horizontal position in pixels (e.g. 0, 600, 1200)
- `"y"`: vertical position in pixels (e.g. 0, 200, 800)
- `"width"`: pixel width of the component (e.g. 600-1200)
- `"height"`: pixel height of the component (e.g. 100-600)

Spacing Rule:
Add a minimum vertical gap of 40 pixels between entities (i.e., next_entity.y = previous_entity.y + previous_entity.height + 40).
Add a minimum vertical gap of 40 pixels between entities (i.e., next_entity.x = previous_entity.x + previous_entity.width + 40).
Place components top to bottom, avoiding overlap and ensuring clear separation.

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

Place components **top to bottom**, avoiding overlap by adjusting `y`.

---

🎯 Relevance Guidelines:

Only include **insightful** elements:
- Add TEXT sections for headers or summaries.
- Use CHARTS for time trends, category comparisons, or breakdowns.
- Use TABLES for top-k summaries or aggregated breakdowns.

---

📦 Entity object schema:
{output_parser.get_format_instructions()}

---

📊 Dataset Schema:
{schema}
"""
        },
        {
            "role": "user",
            "content": last_message.content
        }
    ]

    response = llm.invoke(messages, config={"thread_id": state["thread_id"]})
    result = output_parser.parse(response.content)

    return {
        "messages": [
            {
                "role": "assistant",
                "type": "DASHBOARD",
                "content": f"{result.model_dump_json(indent=2)}"
            }
        ]
    }
