from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated, Optional, List, Dict, Literal, Union
import pandas as pd 
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict 
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)  


class State(TypedDict):
    thread_id: str
    messages: Annotated[list, add_messages]
    message_type: str | None
    csv_path: str
    schema: Optional[dict]
    dataframe: Optional[pd.DataFrame]


class ChartSpec(BaseModel):
    chart_name: str
    chart_type: Literal["LINE", "BAR", "PIE"]
    x_axis: List[str]  
    y_axis: List[str]  
    data: List[Dict[str, Union[str, float, int]]]

class MultiChartResponse(BaseModel):
    charts: List[ChartSpec]


class TableSpec(BaseModel):
    header: List[str]
    rows: List[List[Union[str, float, int]]]