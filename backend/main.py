from fastapi import FastAPI,HTTPException
import httpx
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from groq import Groq

load_dotenv()
app=FastAPI()

class TranscriptRequest(BaseModel):
    transcript:str
    
    
@app.get("/health")
async def status_report():
    return {"status":"ok"}

client=Groq(api_key=os.getenv('GROQ_API_KEY'))

@app.post("/summarize")
async def summarize_report(req:TranscriptRequest):
    # transcript=req.transcript
    # summary="this is the dummy summary of "+transcript[:50]
    # return {"summary" :summary}   
    prompt="Respond to this "+req.transcript
    chat_completion=client.chat.completions.create(
        messages=[
            {
            "role":"user",
            "content":prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return {" Here is the response ":chat_completion.choices[0].message.content}
    
    
    









 