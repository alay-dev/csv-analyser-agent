from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from graph_builder import create_graph, initialize_state
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

# Initialize state and create graph
global_state = initialize_state("sample.csv")
graph = create_graph()

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
