
from dataclasses import dataclass

@dataclass
class Config:
    llm_model_name: str = "gemini-2.5-flash-lite"    # options: "gemini-2.5-flash", "gemini-2.5-flash-lite", 
                                                # "gemini-2.0-flash", "gemini-2.0-flash-lite"