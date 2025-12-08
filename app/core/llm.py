import os
import httpx
import ssl
import urllib3
import certifi
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Disable SSL warnings and verification if in corporate environment
_disable_ssl = os.getenv("DISABLE_SSL_VERIFY", "").lower() == "true"

if _disable_ssl:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ssl._create_default_https_context = ssl._create_unverified_context
    # Also set environment variables for all HTTP libraries
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    os.environ['SSL_CERT_FILE'] = ''

def get_http_client():
    """Get HTTP client with SSL bypass for corporate networks."""
    verify = not _disable_ssl
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    
    if proxy:
        return httpx.Client(proxy=proxy, verify=verify, timeout=60.0)
    return httpx.Client(verify=verify, timeout=60.0)

def get_model(model_id: str, temperature: float = 0.0):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Create custom http client with SSL bypass
    http_client = get_http_client()
    
    return ChatGroq(
        model=model_id,
        temperature=temperature,
        api_key=api_key,
        timeout=60,
        max_retries=3,
        http_client=http_client
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

def get_qwen_model():
    # Critic 1: Structure & SEO
    return get_model("qwen/qwen3-32b", temperature=0.1)

def get_kimi_model():
    # Critic 2: Content Quality & Engagement
    return get_model("moonshotai/kimi-k2-instruct", temperature=0.2)

def get_llama_model():
    # Critic 3: Fact-Checking & Logic
    return get_model("meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.1)

def get_optimizer_model():
    # Optimizer: Rewrites based on critiques
    return get_model("openai/gpt-oss-120b", temperature=0.2)
