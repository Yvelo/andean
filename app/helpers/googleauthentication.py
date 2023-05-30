import pickle
import os
import redis

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from urllib.parse import urlparse
from app.helpers.recall import AIPersonaRecall

def get_gdrive_services(api_key, 
                        required_service = ["drive-v3",
                                            "docs-v1",
                                            "sheets-v4", 
                                            "slides-v1"]):
    creds = None
    services={}

    parsed_url = urlparse(os.getenv("REDIS_URL", "redis://localhost:6379"))
    r = redis.Redis(host=parsed_url.hostname, port=6379, db=0) 

    if r.exists("google-api-token-"+api_key):
        creds = pickle.loads(r.get("google-api-token-"+api_key))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("google-api-credentials.json", SCOPES)
            creds = flow.run_local_server(port=8000)
        r.set("google-api-token-"+api_key, pickle.dumps(creds))
    
    for service in required_service:
        service_name, version = service.split("-")
        services[service] = build(service_name, version, credentials=creds)
    
    return services

def is_access_authorized(item_id, 
                         api_key, 
                         user_api_keys, 
                         permissions = None):
    services = get_gdrive_services(api_key, ["drive-v3"])
    authorized = False
    ai_persona = AIPersonaRecall(item_id="main", 
                                    api_key=api_key,
                                    recall_group=user_api_keys["recall_group"])
    ai_email = ai_persona.email

    if not permissions:
        file = services["drive-v3"].files().get(fileId=item_id, 
                                                fields="id, name, mimeType, permissions").execute()
        permissions = file.get("permissions", [])

    for perm in permissions:
        if perm['type'] == 'user' and perm['emailAddress'] == ai_email:
            authorized = True
            break

    return authorized

