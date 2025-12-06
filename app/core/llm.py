import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

def get_model(model_id: str, temperature: float = 0.0):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    return ChatGroq(
        model=model_id,
        temperature=temperature,
        api_key=api_key
    )

def get_planner_model():
    # Using 120B for high-quality planning
    return get_model("openai/gpt-oss-120b", temperature=0.2)

def get_researcher_model():
    # Using 20B for fast summarization/selection. 
    # If quality is poor, switch to 120B.
    return get_model("openai/gpt-oss-20b", temperature=0.0)

def get_writer_model():
    # Using 120B for high-quality writing
    return get_model("openai/gpt-oss-120b", temperature=0.4)
