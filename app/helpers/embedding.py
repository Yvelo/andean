import pinecone
from googleapiclient.errors import HttpError
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain import PromptTemplate
from langchain.llms.openai import OpenAI

template = """
Based on the following information:

{embedding_extract}



{question}
"""

prompt = PromptTemplate(
    input_variables=["embedding_extract", "question"],
    template=template,
)


def query_embedding(question, user_api_keys, recall):
    try:
        reformated_answer = "Sorry but I cannot answer this question." 
        document_link_name = None 
        document_link_url = None

        embeddings = OpenAIEmbeddings()
        pinecone.init(api_key = user_api_keys["pinecone_api_key"],
                        environment = user_api_keys["pinecone_env"],
                        namespace = recall.recall_id())
        index_name = user_api_keys["pinecone_index"]

        docsearch = Pinecone.from_existing_index(index_name = index_name, 
                                                    embedding = embeddings)
                                                    #text_key = "text",
                                                    #namespace = recall.recall_id())
        docs = docsearch.similarity_search(question)

        if docs != []:
            embedding_extract = docs[0].page_content
            reformated_question = prompt.format(question = question,
                            embedding_extract = embedding_extract)
            llm = OpenAI()
            reformated_answer = llm(reformated_question)
            document_link_name = docs[0].metadata["title"]
            document_link_url = docs[0].metadata["source"]
                            
        
        return reformated_answer, document_link_name, document_link_url
    except HttpError as error:
        return f'An error occurred: {error}'


