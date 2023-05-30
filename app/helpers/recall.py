import os
import redis
import json
import pinecone
from urllib.parse import urlparse
from langchain.llms import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import AnalyzeDocumentChain

#from langchain.document_loaders import GoogleDriveLoader
from app.helpers.googledrive import GoogleDriveLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

SCOPES = ["https://www.googleapis.com/auth/drive"]

def split_docs(documents, chunk_size=1000, chunk_overlap=20):
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
  docs = text_splitter.split_documents(documents)
  return docs

class Recall:
    def __init__(self, item_id, api_key, recall_group):
        parsed_url = urlparse(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.redis = redis.Redis(host=parsed_url.hostname, port=6379, db=0) 
        self.item_id = item_id
        self.api_key = api_key
        self.recall_group = recall_group

        self.item_name = None
        self.item_type = None
        self.linked_recalls = None
        self.summary = None
        self.refresh_token = None

    def __getstate__(self):
        state = self.__dict__.copy()
 
        if 'non_pickleable_attribute' in state:
            del state['non_pickleable_attribute']

        return state

    def get(self):
        recall_id = self.recall_id()
        data = self.redis.get(recall_id)
        if data is None:
            self.set()
            data = self.redis.get(recall_id)
        data_object = json.loads(data)

        self.item_name = data_object.get('item_name', None)
        self.item_type = data_object.get('item_type', None)
        self.linked_recalls = data_object.get('linked_recalls', None)
        self.summary = data_object.get('summary', None)
        self.refresh_token = data_object.get('refresh_token', None)

        return data

    def set(self):
        data = {
            'item_id': self.item_id,
            'item_name': self.item_name,
            'item_type': self.item_type,
            'linked_recalls': self.linked_recalls,
            'summary': self.summary,
            'refresh_token': self.refresh_token
        }

        self.redis.set(self.recall_id(), json.dumps(data))

    def delete(self):
        self.redis.delete(self.recall_id())

    def recall_id(self):
        return self.recall_group + "-" + self.item_id

class AIPersonaRecall(Recall):
     def __init__(self, item_id, api_key, recall_group):
         self.first_name = None
         self.last_name = None
         self.email = None
         super().__init__(item_id, api_key, recall_group)
         self.load()

     def load(self):
         if (self.item_id and self.api_key and self.recall_group):
             self.get()
             if not self.summary:
                 with open("app/static/ai_persona.json") as f:
                     ai_persona_memory=json.load(f)
                 self.first_name = ai_persona_memory[self.item_id]["first_name"]
                 self.last_name = ai_persona_memory[self.item_id]["last_name"]
                 self.email = ai_persona_memory[self.item_id]["email"]
                 self.summary = ai_persona_memory[self.item_id]["personality"]
                 self.item_name = self.first_name 
                 
     def recall_id(self):
         return self.recall_group + "-ai_persona-" + self.item_id


class GoogleDriveRecall(Recall):
    def __init__(self, item_id, api_key, recall_group, services, user_api_keys, forced_reload = "lazy"):
        assert forced_reload in [ "old", "lazy", "eager"]
        self.services = services
        self.user_api_keys = user_api_keys
        super().__init__(item_id, api_key, recall_group)
        self.load(forced_reload)

    def load(self, forced_reload = "lazy"):
        if (self.item_id and self.api_key and self.recall_group):
            item = self.services["drive-v3"].files().get(fileId=self.item_id, fields='id, name, mimeType, modifiedTime, createdTime').execute()
            self.item_type = self.get_gdrive_item_type(item)
            item_current_refresh_token = str(item["createdTime"])+"-"+str(item["modifiedTime"])
            self.get()
            item_past_refresh_token = self.refresh_token
            has_changed = item_current_refresh_token != item_past_refresh_token
            
            if (((has_changed) or (forced_reload == "eager")) and (forced_reload != "old")):
                self.item_name = item["name"]

                self.refresh_token = item_current_refresh_token

                linked_recalls ={}
                all_docs =[]

                if self.item_type == "folder":
                    results = self.services["drive-v3"].files().list(pageSize=100, 
                                                                fields="nextPageToken, files(id, name, mimeType)",
                                                                q = "'{}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false".format(self.item_id)).execute()
                    files = results.get("files", [])

                    if files:
                        for file in files:
                            target_recall_id = self.recall_group + "-google_drive-" + file["id"]
                            linked_recalls[target_recall_id]={"target_item_id" : file["id"], 
                                                              "target_item_name" :  file["name"], 
                                                              "target_item_url" : self.get_gdrive_item_url(file), 
                                                              "link_type" : "file in folder"}

                            loader = GoogleDriveLoader(file_ids=[file["id"]], recursive=False, services= self.services)
                            docs = loader.load()
                            all_docs.extend(docs)
                            GoogleDriveRecall(item_id=file["id"], 
                                              api_key=self.api_key,
                                              recall_group=self.recall_group,
                                              services = self.services,
                                              user_api_keys = self.user_api_keys,
                                              forced_reload = forced_reload)

                else:
                    if has_changed or forced_reload=="eager":
                        loader = GoogleDriveLoader(file_ids=[self.item_id], recursive=False, services= self.services)
                        docs = loader.load()
                        all_docs.extend(docs)
                
                # Embeddings
                print("Embeding : " + self.item_type + " " + self.item_name)
                splitted_docs = split_docs(all_docs)
                embeddings = OpenAIEmbeddings()

                pinecone.init(api_key = self.user_api_keys["pinecone_api_key"],
                              environment = self.user_api_keys["pinecone_env"],
                              namespace = self.recall_id())
                index_name = self.user_api_keys["pinecone_index"]
                index = pinecone.Index(index_name=index_name)
                index.delete(delete_all = True,
                             namespace = self.recall_id())


                docsearch = Pinecone.from_existing_index(index_name, embeddings)
                if not docsearch or has_changed or forced_reload=="eager":
                    docsearch = Pinecone.from_documents(splitted_docs, embeddings, index_name=index_name)

                # Summarizings
                print("Summarizing : " + self.item_type + " " + self.item_name)
                combined_content = ""
                for doc in all_docs:
                    combined_content += doc.page_content

                llm = OpenAI(temperature=0)
                try:
                    summary_chain = load_summarize_chain(llm, chain_type="map_reduce")
                    summarize_document_chain = AnalyzeDocumentChain(combine_docs_chain=summary_chain)

                    summary = ""
                    if len(combined_content):
                        summary = summarize_document_chain.run(input_document=combined_content)
                except:
                    summary = "Error while preparing summary"

                self.summary = summary
                self.linked_recalls = linked_recalls
                self.set()

        return self

    def recall_id(self):
        return self.recall_group + "-" + self.item_type + "-" + self.item_id

    def get_gdrive_item_url(self=None, item=None):
        mime_type = self.item_type if item is None else item["mimeType"]
        mime_name = self.item_name if item is None else item["name"]
        mime_id = self.item_id if item is None else item["id"]
        item_link = ""

        if mime_type == "application/vnd.google-apps.folder":
            item_link = u'<a class="html-link" href="https://drive.google.com/drive/folders/{1}">{0}</a>'.format(mime_name, mime_id)
        elif mime_type == "application/vnd.google-apps.document":
            item_link = u'<a class="html-link" href="https://docs.google.com/document/d/{1}">{0}</a>'.format(mime_name, mime_id)
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            item_link = u'<a class="html-link" href="https://docs.google.com/spreadsheets/d/{1}">{0}</a>'.format(mime_name, mime_id)
        elif mime_type == "application/vnd.google-apps.presentation":
            item_link = u'<a class="html-link" href="https://docs.google.com/presentation/d/{1}">{0}</a>'.format(mime_name, mime_id)
        else:
            item_link = u'<a class="html-link" href="https://drive.google.com/file/d/{1}">{0}</a>'.format(mime_name,mime_id)
    
        return item_link


    def get_gdrive_item_type(self=None, item=None):
        mime_type = self.item_type if item is None else item["mimeType"]
        item_type = ""

        if mime_type == "application/vnd.google-apps.folder":
            item_type = "folder"
        elif mime_type == "application/vnd.google-apps.document":
            item_type = "document"
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            item_type = "spreadsheets"
        elif mime_type == "application/vnd.google-apps.presentation":
            item_type = "presentation"
        else:
            item_type = "file"

        return item_type
