from shared import State, llm, AIMessage

def analytical_response_agent(state: State):
    last_message = state["messages"][-1]
    schema = state["schema"]
    
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
- Reference previous conversation context when relevant to provide continuity

---

Dataset context below.  
Use only the following schema and data to form your answers:

Schema:  
{schema}

{conversation_context}"""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages, config={"thread_id": state["thread_id"]})
    ai_message = AIMessage(content=reply.content, additional_kwargs={"message_type": "TEXT"})
    return {"messages": [ai_message]}
