from shared import State, llm, ChartSpec, TableSpec, AIMessage
from typing import Literal, Optional, List
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

def generate_dashboard_entities(state: State):
    last_message = state["messages"][-1]
    schema = state["schema"]

    class DashboardEntity(BaseModel):
        entity_type: Literal["TEXT", "CHART"]
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

Do not treat the data as sample data, dont mention sample word in any response.
The dashboard consists of multiple entities — each being a chart or a section header (text).
The dashboard has to be as detailed as possible, but also concise. Try to create as many components as needed to provide comprehensive information. A correct number of components will be around 20-25.
Determine the correct chart types based on the data that you want to show.

The dashboard can have **multiple headers (categories/sections)**.  
   - Example: `"Campaign Performance"`, `"Audience Insights"`, `"Revenue Trends"`.  
   - Each header should be a **TEXT entity**.  

**Time-based insights (if relevant):**  
   - Charts can naturally show **last 30 days, last 3 months, year-to-date (YTD), etc.**  
   - This is represented through the **X or Y axis labels (date, month, week, etc.)**, not as a separate field.  

---

⚙️ Layout Requirements (Pixel-based):

Each entity **must include pixel positioning**:
- `"x"`: horizontal position in pixels (e.g. 0, 600, 1200)
- `"y"`: vertical position in pixels (e.g. 0, 200, 800)
- `"width"`: pixel width of the component (e.g. 600-1200)
- `"height"`: pixel height of the component (e.g. 100-600)

Spacing Rule:
Add a minimum vertical gap of 40 pixels between entities (i.e., next_entity.y = previous_entity.y + previous_entity.height + 40).
Add a minimum horizontal gap of 40 pixels between entities (i.e., next_entity.x = previous_entity.x + previous_entity.width + 40).
Place components top to bottom, avoiding overlap and ensuring clear separation. 


Suggested sizes:
- TEXT:
  - width: 1000-1200
  - height: 60-100
- CHART:
  - width: 600-800
  - height: 300-500

Place components **top to bottom**, avoiding overlap by adjusting `y`.

---

🎯 Relevance Guidelines:

Only include **insightful** elements:
- Add TEXT sections for headers or summaries.
- Use CHARTS for time trends, category comparisons, or breakdowns.

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

    ai_message = AIMessage(
        content=f"{result.model_dump_json(indent=2)}", 
        additional_kwargs={"message_type": "DASHBOARD"}
    )
    return {"messages": [ai_message]}
