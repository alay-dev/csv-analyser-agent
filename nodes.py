from shared import State, llm
import os
import pandas as pd
from pydantic import BaseModel, Field
from typing import  Literal, Optional, List
from langchain.output_parsers import PydanticOutputParser
from shared import ChartSpec, MultiChartResponse, TableSpec


class MessageClassifier(BaseModel):
    message_type: Literal["generate_graph", "analytical_response", "generate_dashboard"] = Field(
        ...,
        description="Classify if the message requires to generate graph or analytical response"
    )

def load_csv_node(state: State) -> State:
    print("📂 Loading CSV...")
    csv_path = "sample.csv"
    if not csv_path or not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV path not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    state["dataframe"] = df
    return state

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


def router(state: State):
    message_type = state.get("message_type", "analytical_response")
    if message_type == "generate_graph":
        return {"next": "generate_graph"}
    if message_type == "generate_dashboard":
        return {"next": "generate_dashboard"}

    return {"next": "analytical_response"}



def generate_graph_agent(state: State):
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

    return {
        "messages": [
            {
                "role": "assistant",
                "type": "CHART",
                "content": f"{result.model_dump_json(indent=2)}"
            }
        ]
    }

def generate_dashboard_entities(state: State):
    from typing import Literal, Optional, List, Dict, Union
    from pydantic import BaseModel
    from langchain.output_parsers import PydanticOutputParser

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
- Avoid dumping full raw tables unless valuable.

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


def analytical_response_agent(state: State):
    last_message = state["messages"][-1]
    schema = state["schema"]

    messages = [
        {"role": "system",
         "content": f"""You are a **Data Analyst Assistant** specialized in analyzing structured datasets like CSV files.

Your job is to help users understand their data through clear, insightful, and accurate responses based solely on the dataset schema and sample rows.

---

### Responsibilities:

Use the provided dataset to answer natural language questions about the data.  
All insights must be grounded in the actual schema or sample data — do not guess or fabricate values.

---

### You can respond to:

• Aggregated metrics  
→ Summarize totals, averages, maximums, minimums, medians, or counts.

• Breakdowns  
→ Describe how a metric changes over time, per category, or per group (e.g., per date, per campaign).

• Trends or comparisons  
→ Identify increases, decreases, patterns, or anomalies (e.g., "Spend is decreasing over the last 3 days").

• Ambiguous queries  
→ If the question is unclear, infer intent based on context or politely ask for clarification.

---

### Output Instructions:

- Use **plain text with line breaks and bullet points** for readability
- Use **emojis** to highlight or emphasize key metrics and trends (e.g., totals, peaks, drops)
- Do not format the response as a table
- Mention relevant column names when possible
- Do not fabricate values — use only what is in the schema or sample rows

---

Dataset context below.  
Use only the following schema and sample data to form your answers:

Schema:  
{schema}
"""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages, config={"thread_id": state["thread_id"]})
    return {"messages": [{"role": "assistant", "type": "TEXT", "content": reply.content}]}


def analyze_schema_node(state: State) -> State:
    df = state["dataframe"]
    schema = {
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "sample": df.head(5).to_dict(orient="records")
    }
    state["schema"] = schema
    return state

def load_and_analyze_csv(state: State) -> State:
    state = load_csv_node(state)
    state = analyze_schema_node(state)
    return state
