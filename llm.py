import os, json
from openai import OpenAI
schema = json.load(open('schemas/assessment.schema.json','r'))
client=None
key=os.getenv('OPENAI_API_KEY','')
if key:
    try: client=OpenAI(api_key=key)
    except Exception: client=None
def extract_with_llm(transcript:str):
    if not client: return None
    try:
        resp = client.chat.completions.create(
            model=os.getenv('LLM_MODEL','gpt-4o-mini'),
            temperature=0,
            response_format={'type':'json_schema','json_schema':{'name':'assessment','schema':schema}},
            messages=[{'role':'system','content':'Return only JSON for the schema.'},{'role':'user','content':transcript}],
        )
        import json as _json
        return _json.loads(resp.choices[0].message.content)
    except Exception:
        return None
