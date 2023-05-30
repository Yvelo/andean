from googleapiclient.errors import HttpError

from app.helpers.googleauthentication import get_gdrive_services
from app.helpers.embedding import query_embedding

def answer_document_questionnaire(document_id, api_key, user_api_keys, recall):
    try:
        # Retrieve the documents contents
        services = get_gdrive_services(api_key, ["docs-v1"])
        document = services["docs-v1"].documents().get(documentId=document_id).execute()
        
        requests = []
        length_shift = 0
        answer = ""
        insert_location = 0

        for index, element in enumerate(document['body']['content']):
            if 'paragraph' in element:
                paragraphs = element.get('paragraph').get('elements')
                if len(paragraphs) == 1:
                    text_run = paragraphs[0].get('textRun')
                    if text_run and text_run.get('content').strip().endswith('?'):
                        question = text_run.get('content') 
                        embedding_answer, link_name, link_url = query_embedding(question = question,
                                                                                user_api_keys = user_api_keys,
                                                                                recall = recall)


                        chat_answer = embedding_answer +'<BR><a href="' + link_url + '">' + link_name + '</a>'
                        document_answer = embedding_answer + '\n' 
                        document_answer = '\n' + document_answer.lstrip('\n')
                        insert_location = element['endIndex'] + length_shift-1
                        requests.append({
                            'insertText': {
                                'location': {
                                    'index': insert_location
                                },
                                'text': document_answer
                            }
                        })
                        length_shift += len(document_answer)
                        insert_location = element['endIndex'] + length_shift -1 
                        requests.append({
                            'insertText': {
                                'location': {
                                    'index': insert_location
                                },
                                'text': link_name
                            },
                        })
                        length_shift += len(link_name)
                        requests.append({
                            'updateTextStyle': {
                                'range': {
                                    'startIndex': insert_location,
                                    'endIndex': len(link_name) + insert_location,
                                },
                                'textStyle': {
                                    'link': {
                                        'url': link_url
                                    }
                                },
                                'fields': 'link'
                            }
                        })
                            
 
                        answer += "<b>" + question + "</b><BR>" + chat_answer + "<BR><BR>"

        if answer=="":
            answer = "There are no section in this document with only one paragraph ending with a question mark."
        
        if insert_location:
            services["docs-v1"].documents().batchUpdate(documentId=document_id, 
                                                        body={'requests': requests}).execute()
        
        return answer
    except HttpError as error:
        return f'An error occurred: {error}'

