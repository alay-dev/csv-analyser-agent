from shared import State
import os
import pandas as pd

def load_csv(state: State) -> State:
    print("📂 Loading CSV...")
    csv_path = state.get("csv_path")
    if not csv_path or not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV path not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    state["dataframe"] = df
    return state

def analyze_schema(state: State) -> State:
    df = state["dataframe"]
    schema = {
        "columns": list(df.columns),
        "dtypes": df.dtypes.apply(lambda x: str(x)).to_dict(),
        "sample": df.head(5).to_dict(orient="records")
    }
    state["schema"] = schema
    return state


def load_and_analyze_csv(state: State) -> State:
    state = load_csv(state)
    state = analyze_schema(state)
    return state