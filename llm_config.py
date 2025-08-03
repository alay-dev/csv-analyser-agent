from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the LLM
def get_llm(model="gemini-2.0-flash", temperature=0):
    """
    Initialize and return a ChatGoogleGenerativeAI instance.
    
    Args:
        model (str): The model name to use
        temperature (float): The temperature parameter for generation
        
    Returns:
        ChatGoogleGenerativeAI: The initialized LLM
    """
    return ChatGoogleGenerativeAI(model=model, temperature=temperature)

# Create a default LLM instance
llm = get_llm()
