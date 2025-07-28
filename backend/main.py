from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from groq import Groq
from notion_client import Client
import json

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
    

meeting_cache={}

def parse_meeting_summary(response_text:str):
    parsed_data={}
    
    def extract_field(label):
        match=re.search(r"\*\*{label}\*\*:(.+)",response_text)
        return match.group(1).strip() if match else ""
    def extract_section(start_label, end_label=None):
        start_pattern = rf"\*\*{re.escape(start_label)}\*\*"
        if end_label:
            end_pattern = rf"\*\*{re.escape(end_label)}\*\*"
            pattern = rf"{start_pattern}\n(.+?)\n{end_pattern}"
        else:
            pattern = rf"{start_pattern}\n(.+)"
        match = re.search(pattern, response_text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    parsed_data["title"] = extract_field("Meeting Title")
    parsed_data["facilitator"] = extract_field("Facilitator")
    parsed_data["attendees"] = extract_field("Attendees").split(",")
    parsed_data["agenda"] = extract_section("Agenda Topics & Discussion Summaries", "Decisions Made")
    parsed_data["decisions"] = extract_section("Decisions Made", "Action Items")
    parsed_data["action_items"] = extract_section("Action Items", "Next Steps")
    parsed_data["next_steps"] = extract_section("Next Steps")

    return parsed_data


def format_for_notion(meeting):
    def text_block(content):
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            }
        }

    def bulleted_list(text):
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

    def parse_bullets(section):
        items = [item.strip("- ").strip() for item in section.strip().split("\n") if item.strip()]
        return [bulleted_list(item) for item in items]

    blocks = [
        {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"type": "text", "text": {"content": meeting['title']}}]}},
        text_block(f"Facilitator: {meeting['facilitator']}"),
        text_block(f"Attendees: {', '.join([a.strip() for a in meeting['attendees']])}"),
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Agenda Topics"}}]}},
    ] + parse_bullets(meeting['agenda']) + [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Decisions Made"}}]}},
    ] + parse_bullets(meeting['decisions']) + [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Action Items"}}]}},
    ] + parse_bullets(meeting['action_items']) + [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Next Steps"}}]}},
    ] + parse_bullets(meeting['next_steps'])

    return blocks

def format_for_slack(meeting):
    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"📋 Meeting Summary: {meeting['title']}", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Facilitator:* {meeting['facilitator']}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Attendees:* {', '.join(meeting['attendees'])}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Agenda:*\n{meeting['agenda']}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Decisions:*\n{meeting['decisions']}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Action Items:*\n{meeting['action_items']}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Next Steps:*\n{meeting['next_steps']}"}},
    ]

@app.get("/health")
async def status_report():
    return {"status":"ok"}

print("GROQ_API_KEY:", os.getenv('GROQ_API_KEY'))  # Debug: Remove after confirming

# Setting up clients for integrating with notion , groq , slack apis
groq_client=Groq(api_key=os.getenv('GROQ_API_KEY'))
notion_client=Client(auth=os.getenv('NOTION_API_KEY'))
notion_page_id=os.getenv('NOTION_PAGE_ID')
slack_channel_id=os.getenv('SLACK_CHANNEL_ID')
slack_token=os.getenv('SLACK_TOKEN')

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
    chat_completion=groq_client.chat.completions.create(
        messages=[
            {
            "role":"user",
            "content":prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    
    print(chat_completion.choices[0].message.content)
    llm_response=chat_completion.choices[0].message.content
    parsed=parse_meeting_summary(llm_response)
    meeting_cache['meeting_summary']=parsed
    return {"summary":llm_response}
    
@app.post("/notion")
def sendToNotion():
    if 'meeting_summary' not in meeting_cache:
        raise HTTPException(status_code=400, detail="No meeting summary available. Please summarize first.")
    
    meeting = meeting_cache["meeting_summary"]
    notion_blocks = format_for_notion(meeting)

    response = notion_client.pages.create(
        parent={"type": "page_id", "page_id": notion_page_id},
        properties={
            "title": [
                {
                    "type": "text",
                    "text": {"content": meeting['title']}
                }
            ]
        },
        children=notion_blocks
    )

    print(f"Notion response is {response}")
    print(json.dumps(notion_blocks, indent=2))
    return {"notion_url": response["url"]}


@app.post("/slack")
def sendToSlack():
    meeting=meeting_cache["meeting_summary"]
    headers={
        "Authorization":f"Bearer {slack_token}",
        "Content-Type":"application/json"
    }
    data={
        "channel":slack_channel_id,
        "blocks":format_for_slack(meeting)
    }
    response=httpx.post("https://slack.com/api/chat.postMessage",headers=headers,json=data)
    if not response.json.get("ok"):
        print(f"Failed to get message to slack:{response.data}")
    else:
        print("Message sent to slack successfully")
    return {"message":"Posted to Slack"}

@app.post("/gmail")
def sendToGmail():
    pass







 