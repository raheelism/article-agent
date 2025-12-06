from typing import List, Literal, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from app.core.state import AgentState
from app.core.llm import get_planner_model
import json
import re

def create_initial_plan(state: AgentState) -> dict:
    """
    Generates the initial plan based on the user's topic.
    """
    print(f"--- PLANNING: {state['topic']} ---")
    
    llm = get_planner_model()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert Content Strategist.
        Your goal is to create a JSON execution plan for an article.
        
        The plan must involve TWO types of tasks:
        1. 'research': Investigating keywords, competitors, or specific subtopics.
        2. 'write': Drafting specific sections of the article.
        
        Rules:
        - Always start with broad research.
        - Break writing down into sections (Intro, Body Points, Conclusion).
        - Ensure logical flow.
        - The final result should meet the word count goal: {word_count}.
        
        Return ONLY valid JSON. No markdown formatting, no explanations.
        
        Format:
        [
            {{
                "id": 1,
                "type": "research",
                "description": "Research the main topic..."
            }},
            {{
                "id": 2,
                "type": "write",
                "description": "Write the Introduction..."
            }}
        ]
        """),
        ("user", "Topic: {topic}\nLanguage: {language}")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "topic": state["topic"], 
            "word_count": state["word_count"],
            "language": state["language"]
        })
        
        content = response.content
        # specific fix for markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        tasks_data = json.loads(content.strip())
        
        # Validate and format
        tasks_list = []
        for i, step in enumerate(tasks_data):
             step_dict = {
                 "id": i + 1,
                 "type": step.get("type", "research"),
                 "description": step.get("description", "Do work"),
                 "status": "pending",
                 "params": {}
             }
             tasks_list.append(step_dict)
             
        return {"plan": tasks_list}
        
    except Exception as e:
        print(f"Planning failed: {e}. Using fallback.")
        return {"plan": [
            {"id": 1, "type": "research", "description": f"Research key facts about {state['topic']}", "status": "pending", "params": {}},
            {"id": 2, "type": "write", "description": "Write the Introduction", "status": "pending", "params": {}},
            {"id": 3, "type": "write", "description": "Write the Main Body", "status": "pending", "params": {}},
            {"id": 4, "type": "write", "description": "Write the Conclusion", "status": "pending", "params": {}}
        ]}
