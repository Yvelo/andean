# Andean
## Versatile Google Suite chatbot based on LangChain 

Andean is a demonstration model for a chatbot that employs Open Source Large Language Models like [Flant T5](https://huggingface.co/docs/transformers/model_doc/t5), [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) and other [Llama-based](https://github.com/facebookresearch/llama) LLMs to perform a range of text processing tasks within the Google Suite. Constructed on the [Python version](https://python.langchain.com/) of the [LangChain](https://github.com/hwchase17/langchain) framework, Andean is designed for serverless deployment architectures like Cloud Run, with the intention to undergo stress testing. 

To showcase the effectiveness of LangChain, andean POC version is focussed on two exploratory use cases:

- Context Analysis: Possibility to answer questions associated with documents uploaded in a Google Drive directory.
- Prefill a Technical Questionnaire in Google Doc from the content of a Google Drive directory.

Andean mainly aims to compare at scale, the main llms (OpenAI, PaLm, Llama...) on text processing and personal assistance tasks. 

![Screen shoot](/app/static/img/screen_shot_1.jpg "Screen shot 1")

## Architecture
### Deployement
At present, Andean is targeting a designated group of beta testers, thereby obviating the requirement for tracking API usage or incorporating billing features.

![Proof of Concept architecture](/app/static/img/proof_of_concept_architecture.jpg "Proof of Concept architecture")

### Long term memory
Long-term memories, termed "Recalls", store not only a summary of the document or folder they represent, but also a link to an embedding of the content within. Similar to human memory, Recalls can reference other Recalls and may need to be updated (if the underlying document has changed) or deleted (to free up space in Pinecone and Redis). Recalls are refreshed mannualy or as needed.

The Recall class is specialized into two types: GoogleDriveRecall and AIPersonaRecall (which stores information that the AI agent knows about itself). To conserve processing resources, Recalls are shared among all users within a specific recall group. Please note that Andean needs account set in AI Persona to have access to the Google Drive ressource.

Due to Google Memorystore's lack of support for Redis Modules it is not possible to use its vector store capabilities, we have elected to use Pinecone instead.

![Long term memory](/app/static/img/long_term_memory.jpg "Long term memory")


## Quick Start

**[https://github.com/Yvelo/andean](https://github.com/Yvelo/andean)**

1) To get started, clone this repository.

   `git clone https://github.com/Yvelo/andean.git`

2) Create a file api-keys.json in the root folder using api-keys.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to insert them in the Docker images. For each user/entry in api-keys.json set OPENAI_API_KEY, BANANADEV_API_KEY and the BANANADEV_MODEL_KEYs to be obtained from [OpenAI](https://platform.openai.com/docs/introduction) and [Banana.dev](https://app.banana.dev/).

3) Create a file google-api-credentials.json in the root folder using google-api-credentials.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to secure it. How to obtain [Google Api Credentials](https://developers.google.com/workspace/guides/create-credentials).

4) Customize /app/static/ai_persona.json as per your preference and ai_persona.template.json .

5) Update cloubuild.yaml according to the characteristics of your continous integration platform.

6) Deploy your Llama Models as for instance [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) in a GPU capable farm such as Tensorflow Serving or Banana.dev.

7) To run andean locally you need acces to Redis. Set .env with REDIS_URL="redis://IP_REDIS_GATEWAY:6379/0" and as a Cloud Build environment variable.

## How to use

1) Enter a valid andean API KEY in the main prompt. The API KEY must exist in the file api-keys.json.

2) Select the chatbot from the top menu to interact with the available models.

3) Enter a valid a url (Google Drive, Google Doc, Youtube or any web page) in the prompt and andean will memorize it and propose possible actions (summarize, answer technical questionaire...). Pressing "Shift" while clicking on the action will force andean to rebuild the Recall from Google Drive.

4) Any Google Document can be completed by andean. The document should contain somewhere [andean-GOOGLE_DRIVE_FOLDER_ID] for andean to identify and answer any section containing a unique paragraph ending by a question mark. 

## Most probable functional evolutions of this scallable POC:

1) Google Calendar: Suggest a list of links relevant for the next calendar event.

2) Youtube: Summarize and extract meta informations from Youtube links or from liked videos.

3) LangChain Agents: Add the possibility to run agents (now andean only runs chains)

4) Batch mode: Possibility to schedule excecution of chains and agents to for instance regularely refresh all Recalls.

5) Connect LangChain Hub: Select and run chains from https://github.com/hwchase17/langchain-hub

6) Google Mail: Prepare draft answers based on the email received directly or forwarded, past conversations from the same sender and relevant long term memories from Redis.

7) Multi AI Persona: Test interactions (Three of Thougts, Reflexion, Collaborative Agents...) involving multiple specialized AI persona.

## Main limitations of this POC:

The code of this repository is not hardened for large scale production and is only shared for information, education and testing.

1) Basic synchronization with Google Drive, more advanced approach could be based on [Google Start Page Token](https://developers.google.com/drive/api/guides/manage-changes).

2) The current security model cannot scale-up. Each andean groups must be associated to a dedicated service account with appropriate [Googel IAM](https://cloud.google.com/iam/docs/manage-access-service-accounts) set-up.

3) Limited Error management.

4) No Unit test. Pytest could be challenged by none determistic testing from LLM feedbacks.

5) AI answers are not streamed as if Server Sent Events would be used.

6) Flask in single threaded and should be replaced by the multi threaded gunicorn.

## Notes and useful links

* Many thanks to Patrick Grenning for [AI Question Answer](https://github.com/pgrennin/ai_question_answer_web_template) which I have used as startup material for Andean.

* [Redis Memory Store and Cloud Run](https://medium.com/google-cloud/using-memorystore-with-cloud-run-82e3d61df016)

* [Configure Serverless VPC Access](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)

* [Serverless GPU deployment](https://fullstackdeeplearning.com/cloud-gpus/)

### Main tools used in this project are:

- Python 3.9
- langchain
- flask
- openai
- pinecone-client
- banana-dev
- redis
- google-api-python-client

### More screen shots

![Screen shoot](/app/static/img/screen_shot_2.jpg "Screen shot 2")

![Screen shoot](/app/static/img/screen_shot_3.jpg "Screen shot 3")

![Screen shoot](/app/static/img/screen_shot_4.jpg "Screen shot 4")