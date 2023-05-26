# Andean
## Versatile chatbot based on LangChain and connected to Google Drive

Andean is a versatile chatbot connected to Google Drive and leveraging Open Source Large Language Models such as [Flant T5](https://huggingface.co/docs/transformers/model_doc/t5), [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) and other [Llama-based](https://github.com/facebookresearch/llama) LLM for various text processing tasks. Andean is built on [LangChain](https://python.langchain.com/) framework and aims to be deployed in serverless architecture such as Cloud Run and Tensorflow Serving. 

To showcase the effectiveness of LangChain Framework, andean initial milestones are focussed on two exploratory initial use cases:

- Context Analysis: Automatically generate a structured Google Doc that presents an overview of the essential concepts and vocabulary associated with the documents uploaded in the Google Drive directory.
- Assistance for Technical Questionnaire filling: Answer any questions that appear alone in a paragraph also alone in a document section. The paragraph may contain multiple phrases, but must end by “?”.

**[https://github.com/Yvelo/andean](https://github.com/Yvelo/andean)**

## Architecture
### Proof of concept (current)
Currently, andean is designed for use by a select group of beta testers, eliminating the need for consumption tracking or billing functionality. 

![Proof of Concept architecture](/app/static/img/proof_of_concept_architecture.jpg "Proof of Concept architecture")
### Public (target)
In a potential and yet-to-be-realized situation, Andean could be scaled up collaboratively to support commercial operations, which would notably include the ability to bill for API usage.

![Target architecture](/app/static/img/target_architecture.jpg "Target architecture")

## Quick Start

1) To get started, clone this repository.

   `git clone https://github.com/Yvelo/andean.git`

2) Create a file api-keys.json in the root folder using api-keys.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to secure it.

2) Create a file google-api-credentials.json in the root folder using google-api-credentials.template.json as a template. Store it in your built environment (e.g. Google Storage Buckets) to secure it.

5) Customize ai_persona.json as per your preference.

3) Update cloubuild.yaml according to the characteristics of your continous integration platform.

4) Deploy your Llama Models as for instance [Alpaca](https://crfm.stanford.edu/2023/03/13/alpaca.html) in a GPU capable farm such as Tensorflow Serving or Banana.

6) To run andean locally you need acces to Redis. Set .env with REDIS_URL="redis://IP_REDIS_GATEWAY:6379/0" and as a Cloud Build environment variable.

## How to use

1) Enter a valid andean API KEY in the main prompt. The API KEY must exist in the file api-keys.json.

2) Select the chatbot from the top menu to interact with the available models.

3) Enter a valid a Google Drive or Google Doc link in the prompt and andean will propose possible actions (summarize, answer technical questionaire...)

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
