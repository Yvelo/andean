from flask import render_template
from urllib.parse import urlparse

from app.helpers.googleauthentication import is_access_authorized, get_gdrive_services
from app.helpers.googledocument import answer_document_questionnaire
from app.helpers.recall import GoogleDriveRecall

SCOPES = ["https://www.googleapis.com/auth/drive"]

def list_actions(question, 
                 type_of_template, 
                 item_id,
                 item_name,
                 item_type,
                 api_key, 
                 user_api_keys):
    services = get_gdrive_services(api_key, ["drive-v3"])
    answer = None
    actions = {}
    if (question.startswith("https://drive.google.com/drive/folders")):
        item_id = question.split("/")[5]
        item_type = "folder"
        if is_access_authorized(item_id = item_id, 
                                api_key=api_key, 
                                user_api_keys=user_api_keys):
            folder = services["drive-v3"].files().get(fileId=item_id).execute()
            item_name = folder["name"]
            answer = "I am now focussed on the folder <a href='{}'>{}</a> and capable to answer questions on its content or perform one of the following actions:".format(question, folder["name"])

            actions["memorize-drive-content"]={"item_id": item_id, 
                                               "item_type": item_type, 
                                               "item_name": item_name, 
                                               "action_name": "Refresh full drive recalls (slow)"}
            actions["memorize-folder-content"]={"item_id": item_id, 
                                               "item_type": item_type, 
                                               "item_name": item_name, 
                                               "action_name": "Refresh folder recalls"}
            actions["list-drive-content"]={"item_id": item_id, 
                                           "item_type": item_type, 
                                           "item_name": item_name, 
                                           "action_name": 
                                           "List folder content"}
            actions["summarize-drive-content"]={"item_id": item_id, 
                                                "item_type": item_type, 
                                                "item_name": item_name, 
                                                "action_name": "Summarize folder"}
            actions["summarize-files"]={"item_id": item_id, 
                                        "item_type": item_type, 
                                        "item_name": item_name, 
                                        "action_name": "Summarize each file in folder"}
        else:
            answer = "Sorry, I am not authorized to access this Google Drive folder."
    if (question.startswith("https://drive.google.com/file/d/") or question.startswith("https://docs.google.com/")):
        item_id = question.split("/")[5]
        item_type = question.split("/")[3]
        if is_access_authorized(item_id = item_id, 
                                api_key=api_key, 
                                user_api_keys=user_api_keys):

            file = services["drive-v3"].files().get(fileId=item_id).execute()
            item_name = file["name"]
            answer = "I am now focussed on the document <a href='{}'>{}</a> and capable to answer questions on its content or perform one of the following actions:".format(question, file["name"])

            actions["memorize-file"]={"item_id": item_id, 
                                      "item_type": item_type, 
                                      "item_name": item_name, 
                                      "action_name": "Memorize file"}
            actions["summarize-file"]={"item_id": item_id, 
                                       "item_type": item_type, 
                                       "item_name": item_name, 
                                       "action_name": "Summarize file"}
            if item_type == "document":
                actions["treat-as-questionnaire"]={"item_id": item_id, 
                                           "item_type": item_type, 
                                           "item_name": item_name, 
                                           "action_name": "Treat as questionnaire"}
        else:
            answer = "Sorry, I am not authorized to access this Google Drive file."

    return answer, actions, item_id, item_name, item_type

def memorize_drive_content(session_id, 
                           api_key,
                           user_api_keys, 
                           forced_reload):
    services = get_gdrive_services(api_key)
    page_token = None
    list_folders = "Drive content:"

    while True:
        results = services["drive-v3"].files().list(pageSize=100, 
                                                    fields="nextPageToken, files(id, name, mimeType, permissions)",
                                                    q = "mimeType='application/vnd.google-apps.folder' and trashed = false",
                                                    pageToken=page_token
                                                    ).execute()

        folders = results.get("files", [])
    
        if not folders:
             list_folders += "Drive is empty."

        else:
            list_folders += "<ul>"
            for folder in folders:
                print("Processing folder " + folder["name"])
                if is_access_authorized(item_id = folder["id"], 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys,
                                        permissions = folder.get("permissions", [])):
                    print(" - " + folder["name"] + " authorized")
                    list_folders += "<li>" + GoogleDriveRecall.get_gdrive_item_url(item = folder) + "</li>"
                    GoogleDriveRecall(item_id=folder.get("id"), 
                                    api_key=api_key,
                                    recall_group=user_api_keys["recall_group"], 
                                    services = services, 
                                    user_api_keys = user_api_keys,
                                    forced_reload = forced_reload)

            list_folders += "</ul>"
            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break

        response = {"question": "", "answer": list_folders, "img": None, "actions":{}}
        output = render_template("answer_chat.html", 
                                 response=response, 
                                 session_id=session_id, 
                                 item_id=None, 
                                 item_name=None, 
                                 item_type=None)
    return output

def memorize_folder_content(folder_id, 
                            session_id, 
                            api_key, 
                            user_api_keys, 
                            forced_reload):
    services = get_gdrive_services(api_key)
    recall = GoogleDriveRecall(item_id=folder_id, 
                               api_key=api_key,
                               recall_group=user_api_keys["recall_group"], 
                               services = services, 
                               user_api_keys = user_api_keys,
                               forced_reload = forced_reload)

    if is_access_authorized(item_id = folder_id, 
                            api_key=api_key, 
                            user_api_keys=user_api_keys):
        results = services["drive-v3"].files().list(pageSize = 100, 
                                                    fields = "nextPageToken, files(id, name, mimeType, permissions)",
                                                    q = "'{}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false".format(folder_id)
                                                    ).execute()
    
        files = results.get("files", [])
        for file in files:
            if is_access_authorized(item_id = file["id"], 
                                    api_key = api_key, 
                                    user_api_keys = user_api_keys, 
                                    permissions = file.get("permissions", [])):
                GoogleDriveRecall(item_id = file["id"], 
                                   api_key = api_key,
                                   recall_group = user_api_keys["recall_group"], 
                                   services = services,
                                   user_api_keys = user_api_keys,
                                   forced_reload = "lazy")                

        folder_link=recall.get_gdrive_item_url()
        answer = "Recalls on folder " + folder_link + " and its direct dependencies have been refreshed from Google Drive."
    else:
        answer = "Sorry, I am not authorized to access this Google Drive folder."

    response = {"question": "", "answer": answer, "img": None, "actions":{}}
    output = render_template("answer_chat.html", 
                             response=response, 
                             session_id=session_id, 
                             item_id=folder_id, 
                             item_name=recall.item_name, 
                             item_type="folder")
    return output

def list_folder_content(folder_id, 
                        session_id, 
                        api_key, 
                        user_api_keys):
    services = get_gdrive_services(api_key, ["drive-v3"])
    if is_access_authorized(item_id = folder_id, 
                            api_key=api_key, 
                            user_api_keys=user_api_keys):
        results = services["drive-v3"].files().list(pageSize=100, 
                                                    fields="nextPageToken, files(id, name, mimeType, permissions)",
                                                    q = "'{}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false".format(folder_id)
                                                    ).execute()
    
        files = results.get("files", [])

        folder = services["drive-v3"].files().get(fileId=folder_id).execute()
        folder_link = GoogleDriveRecall.get_gdrive_item_url(item = folder)
        list_files = "Folder " + folder_link + " content:"
    
        if not files:
             list_files += "Drive " + folder_id + " is empty."
        else:
            list_files += "<ul>"
            for file in files:
                if is_access_authorized(item_id = file["id"], 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys, 
                                        permissions = file.get("permissions", [])):
                    list_files += "<li>" + GoogleDriveRecall.get_gdrive_item_url(item = file) + "</li>"
            list_files += "</ul>"
        response = {"question": "", "answer": list_files, "img": None, "actions":{}}
        output = render_template("answer_chat.html", 
                                    response=response, 
                                    session_id=session_id, 
                                    item_id=folder_id, 
                                    item_name=file["name"], 
                                    item_type="folder")

    else:
        list_files = "Sorry, I am not authorized to access this Google Drive folder."
        response = {"question": "", "answer": list_files, "img": None, "actions":{}}
        output = render_template("answer_chat.html", 
                                    response=response, 
                                    session_id=session_id)
    
    return output

def summarize_folder_content(folder_id,
                            session_id, 
                            api_key, 
                            user_api_keys, 
                            forced_reload):
    services = get_gdrive_services(api_key)
    if is_access_authorized(item_id = folder_id,
                            api_key=api_key,
                            user_api_keys=user_api_keys):
        recall = GoogleDriveRecall(item_id=folder_id, 
                                   api_key=api_key,
                                   recall_group=user_api_keys["recall_group"], 
                                   services = services,
                                   user_api_keys = user_api_keys,
                                   forced_reload = forced_reload)
        answer = recall.summary
    else:
        answer = "Sorry, I am not authorized to access this Google Drive folder."

    response = {"question": "", "answer": answer, "img": None, "actions":{}}
    output = render_template("answer_chat.html", 
                             response=response, 
                             session_id=session_id, 
                             item_id=folder_id, 
                             item_name=recall.item_name, 
                             item_type="folder")

    return output


def summarize_files(folder_id, 
                    session_id, 
                    api_key, 
                    user_api_keys,
                    forced_reload):
    services = get_gdrive_services(api_key)
    if is_access_authorized(item_id = folder_id,
                            api_key=api_key,
                            user_api_keys=user_api_keys):
        results = services["drive-v3"].files().list(pageSize=100, 
                                                    fields="nextPageToken, files(id, name, mimeType, permissions)",
                                                    q = "'{}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false".format(folder_id)).execute()
        files = results.get("files", [])

        folder = services["drive-v3"].files().get(fileId=folder_id).execute()
        folder_link = GoogleDriveRecall.get_gdrive_item_url(item = folder)
        files_summary = "Folder " + folder_link+":"

        if not files:
             files_summary+=" is empty."
        else:
            files_summary+="<ul>"
            for file in files:
                if is_access_authorized(item_id = file["id"],
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys, 
                                        permissions = file.get("permissions", [])):
                    recall = GoogleDriveRecall(item_id=file["id"], 
                                               api_key=api_key,
                                               recall_group=user_api_keys["recall_group"],
                                               services = services,
                                               user_api_keys = user_api_keys,
                                               forced_reload = forced_reload)

                    files_summary += GoogleDriveRecall.get_gdrive_item_url(item = file)
                    files_summary += "<ul><li>"+recall.summary+"</li></ul>"
                    files_summary += "</li>"

            files_summary+="</ul>"
    else:
        files_summary = "Sorry, I am not authorized to access this Google Drive folder."

    response = {"question": "", "answer": files_summary, "img": None, "actions":{}}
    output=render_template("answer_chat.html", 
                           response=response, 
                           session_id=session_id, 
                           item_id=folder_id, 
                           item_name=folder["name"], 
                           item_type="folder")
    
    return output

def memorize_file_content(file_id, 
                          session_id, 
                          api_key, 
                          user_api_keys,
                          forced_reload):
    services = get_gdrive_services(api_key)
    if is_access_authorized(item_id = file_id,
                            api_key=api_key,
                            user_api_keys=user_api_keys):
        recall = GoogleDriveRecall(item_id=file_id, 
                                   api_key=api_key,
                                   recall_group=user_api_keys["recall_group"], 
                                   services = services, 
                                   user_api_keys = user_api_keys,
                                   forced_reload = forced_reload)

        file_link=recall.get_gdrive_item_url()
        answer = "Recall on file " + file_link + " has been refreshed from Google Drive."
    else:
        answer = "Sorry, I am not authorized to access this Google Drive folder."

    response = {"question": "", "answer": answer, "img": None, "actions":{}}
    output = render_template("answer_chat.html", 
                             response = response, 
                             session_id = session_id, 
                             item_id = file_id, 
                             item_name = recall.item_name, 
                             item_type = "file")
    return output

def summarize_file_content(file_id, 
                           session_id, 
                           api_key, 
                           user_api_keys,
                           forced_reload):
    services = get_gdrive_services(api_key)
    if is_access_authorized(item_id = file_id,
                            api_key=api_key,
                            user_api_keys=user_api_keys):
        recall = GoogleDriveRecall(item_id = file_id, 
                                   api_key = api_key,
                                   recall_group = user_api_keys["recall_group"], 
                                   services = services,
                                   user_api_keys = user_api_keys,
                                   forced_reload = forced_reload)
        answer = recall.summary
    else:
        answer = "Sorry, I am not authorized to access this Google Drive file."

    response = {"question": "", "answer": answer, "img": None, "actions":{}}

    output = render_template("answer_chat.html", 
                             response = response, 
                             session_id = session_id, 
                             item_id =  file_id, 
                             item_name = recall.item_name, 
                             item_type = "file")

    return output

def treat_as_questionnaire(file_id, 
                           session_id, 
                           api_key, 
                           user_api_keys,
                           forced_reload):
    services = get_gdrive_services(api_key)
    if is_access_authorized(item_id = file_id,
                            api_key=api_key,
                            user_api_keys=user_api_keys):
        recall = GoogleDriveRecall(item_id = file_id, 
                                   api_key = api_key,
                                   recall_group = user_api_keys["recall_group"], 
                                   services = services,
                                   user_api_keys = user_api_keys,
                                   forced_reload = "old")

        if recall.item_type == "document":
            file_metadata = services["drive-v3"].files().get(fileId=file_id, fields='parents').execute()
            parent_folder_id = file_metadata['parents'][0]
            parent_recall = GoogleDriveRecall(item_id = parent_folder_id, 
                                       api_key = api_key,
                                       recall_group = user_api_keys["recall_group"], 
                                       services = services,
                                       user_api_keys = user_api_keys,
                                       forced_reload = "old")

            answer = answer_document_questionnaire(document_id = file_id, 
                                                   api_key = api_key, 
                                                   user_api_keys = user_api_keys,
                                                   recall = parent_recall)
        else:
            answer =  "Questionnaire answering is only activated for Google Docs files."
    else:
        answer = "Sorry, I am not authorized to access this Google Drive file."

    response = {"question": "", "answer": answer, "img": None, "actions":{}}

    output = render_template("answer_chat.html", 
                             response = response, 
                             session_id = session_id, 
                             item_id =  file_id, 
                             item_name = recall.item_name, 
                             item_type = "file")

    return output
