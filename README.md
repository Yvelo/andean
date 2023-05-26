# Andean
## Versatile Google Suite chatbot based on LangChain 

Andean is a chatbot that leverages Open Source Large Language Models such as [Flant T5](https://huggingface.co/docs/transformers/model_doc/t5), [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) and other [Llama-based](https://github.com/facebookresearch/llama) LLM for various text processing tasks on Google Suite. Andean is built on [LangChain](https://github.com/hwchase17/langchain) framework ([Python version](https://python.langchain.com/))  and aims to be deployed in serverless architecture such as Cloud Run and Tensorflow Serving. 

To showcase the effectiveness of LangChain Framework, andean initial milestones are focussed on two exploratory use cases:

- Context Analysis: Automatically generate a structured Google Doc that presents an overview of the essential concepts and vocabulary associated with the documents uploaded in the Google Drive directory.
- Assistance for Technical Questionnaire filling: Answer any questions that appear alone in a paragraph also alone in a document section. The paragraph may contain multiple phrases, but must end by “?”.

![Screen shoot](/app/static/img/screen_shot_1.jpg "Screen shot")

## Architecture
### Current
Currently, andean is designed for use by a select group of beta testers, eliminating the need for API consumption tracking or billing functionality. 

![Proof of Concept architecture](/app/static/img/proof_of_concept_architecture.jpg "Proof of Concept architecture")
### Target
In a potential and yet-to-be-realized situation, andean could be scaled up collaboratively to support commercial operations, which would notably include the ability to bill for API usage.

![Target architecture](/app/static/img/target_architecture.jpg "Target architecture")

## Quick Start

**[https://github.com/Yvelo/andean](https://github.com/Yvelo/andean)**

1) To get started, clone this repository.

   `git clone https://github.com/Yvelo/andean.git`

2) Create a file api-keys.json in the root folder using api-keys.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to insert them in the Docker images. For each user/entry in api-keys.json set OPENAI_API_KEY, BANANADEV_API_KEY and the BANANADEV_MODEL_KEYs.

3) Create a file google-api-credentials.json in the root folder using google-api-credentials.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to secure it.

4) Customize ai_persona.json as per your preference.

5) Update cloubuild.yaml according to the characteristics of your continous integration platform.

6) Deploy your Llama Models as for instance [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) in a GPU capable farm such as Tensorflow Serving or Banana.

7) To run andean locally you need acces to Redis. Set .env with REDIS_URL="redis://IP_REDIS_GATEWAY:6379/0" and as a Cloud Build environment variable.

## How to use

1) Enter a valid andean API KEY in the main prompt. The API KEY must exist in the file api-keys.json.

2) Select the chatbot from the top menu to interact with the available models.

3) Enter a valid a Google Drive or Google Doc link in the prompt and andean will propose possible actions (summarize, answer technical questionaire...).

4) Andean long term memory (Redis). Any Google Drive file, document or folder can be memorized. Andean memory can be refreshed on demand item by item or for all. 

## Future

Most probable functional evolutions:

1) Google Calendar: Suggest a list of links relevant for the next calendar event.

2) LangChain Agents: Add the possibility to run agents (now andean only runs chains)

3) Batch mode: Possibility to schedule chains and agents runs.

4) Connect LangChain Hub: Select and run chains from https://github.com/hwchase17/langchain-hub

5) Google Mail: Prepare draft answers based on the email received, past conversations from the same sender and relevant long term memories from Redis.

6) Streaming: Stream AI answers using server events.

## Notes

* Many thanks to Patrick Grenning for [AI Question Answer](https://github.com/pgrennin/ai_question_answer_web_template) which I have used as startup material for Andean.


### Main tools used in this project are:

- Python 3.9
- langchain
- flask
- openai
- banana-dev
- redis
- google-api-python-client
