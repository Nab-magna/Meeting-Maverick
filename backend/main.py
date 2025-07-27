from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from groq import Groq

load_dotenv()
app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=['*'],
    allow_methods=['*']
)

class TranscriptRequest(BaseModel):
    transcript:str
    
    
@app.get("/health")
async def status_report():
    return {"status":"ok"}

print("GROQ_API_KEY:", os.getenv('GROQ_API_KEY'))  # Debug: Remove after confirming

client=Groq(api_key=os.getenv('GROQ_API_KEY'))

@app.post("/summarize")
async def summarize_report(req:TranscriptRequest):
    # transcript=req.transcript
    # summary="this is the dummy summary of "+transcript[:50]
    # return {"summary" :summary}
    base_prompt=''
    with open('./prompt.txt','r',encoding='utf-8') as f:
           base_prompt=f.read()
    # print(base_prompt)
    prompt=base_prompt+" "+req.transcript
    chat_completion=client.chat.completions.create(
        messages=[
            {
            "role":"user",
            "content":prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print(chat_completion.choices[0].message.content)
    return {"summary":chat_completion.choices[0].message.content}
    
    
    









 