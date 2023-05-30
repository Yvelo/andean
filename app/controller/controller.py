import os
import logging
import banana_dev as banana
import pinecone
from dotenv import load_dotenv
from flask import Flask, request, render_template, send_file
from flaskext.markdown import Markdown
from langchain import PromptTemplate, LLMChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.memory.chat_message_histories import RedisChatMessageHistory
from langchain.chat_models import ChatOpenAI

#from langchain.llms import Banana
from app.helpers.bananadev import Banana
from app.helpers.authentication import is_authenticated, get_session_id
from app.helpers.recall import Recall, AIPersonaRecall
from app.helpers.embedding import query_embedding
from app.controller.actions_controller import (list_actions, memorize_drive_content, 
                                               memorize_folder_content, list_folder_content, 
                                               summarize_folder_content, summarize_files, 
                                               memorize_file_content, summarize_file_content,
                                               treat_as_questionnaire)

load_dotenv()

app_path = os.getcwd() + "/app"
templates_path = app_path + "/templates"
static_path = app_path + "/static"
app = Flask(__name__, template_folder=templates_path, static_folder=static_path)
Markdown(app)

@app.route("/")
def root():
    readme = open(os.getcwd() +"/README.md" ,"r")
    mkd_text =readme.read()
    return render_template("home.html", mkd_text=mkd_text)

@app.route("/app/static/img/<string:image_name>.jpg")
def display_static_image(image_name):
    img_path = static_path+ f"/img/{image_name}.jpg" 
    return send_file(img_path, as_attachment=False) 

@app.route("/banana_alpaca_13b")
def banana_alpaca_13b():
    return render_template("ask_chat.html", type_of_template="banana_alpaca_13b")

@app.route("/banana_stable_diffusion")
def banana_stable_diffusion():
    return render_template("ask_chat.html", type_of_template="banana_stable_diffusion")

@app.route("/banana_flant_t5")
def banana_flant_t5():
    return render_template("ask_chat.html", type_of_template="banana_flant_t5")

@app.route("/open_ai_gpt35")
def open_ai_gpt35():
    return render_template("ask_chat.html", type_of_template="open_ai_gpt35")

@app.route("/submit_chat", methods=["GET", "POST"])
def submit_chat():
    cookie_api_key = request.cookies.get("API-Key")
    type_of_template = request.form.get("type-of-template")
    question = request.form.get("question")
    api_key = request.form.get("API-Key")
    submit_button_id = request.form.get("submit-button-id")
    item_id = request.form.get("item-id")
    item_type = request.form.get("item-type")
    item_name = request.form.get("item-name")
    forced_reload = request.form.get("forced-reload")

    try:
        session_id=request.form.get("session-id")
    except:
        session_id=None
    if (not (session_id) and (cookie_api_key)):
        session_id=get_session_id(cookie_api_key)

    image_base64=None
    actions={}
    response=""
    output=""

    available_models, user_api_keys=is_authenticated(api_key)

    
    if (submit_button_id=="memorize-drive-content"):
        output = memorize_drive_content(session_id=session_id, 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys,
                                        forced_reload=forced_reload)

    elif (submit_button_id=="memorize-folder-content"):
        output = memorize_folder_content(folder_id=item_id, 
                                        session_id=session_id, 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys,
                                        forced_reload=forced_reload)

    elif (submit_button_id=="list-drive-content"):
        output = list_folder_content(folder_id=item_id, 
                                    session_id=session_id, 
                                    api_key=api_key, 
                                    user_api_keys=user_api_keys)

    elif (submit_button_id=="summarize-drive-content"):
        output = summarize_folder_content(folder_id=item_id, 
                                         session_id=session_id, 
                                         api_key=api_key, 
                                         user_api_keys=user_api_keys,
                                         forced_reload=forced_reload)

    elif (submit_button_id=="summarize-files"):
        output = summarize_files(folder_id=item_id, 
                                 session_id=session_id, 
                                 api_key=api_key, 
                                 user_api_keys=user_api_keys,
                                 forced_reload=forced_reload)

    elif (submit_button_id=="summarize-file"):
        output = summarize_file_content(file_id=item_id, 
                                        session_id=session_id, 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys,
                                        forced_reload=forced_reload)

    elif (submit_button_id=="memorize-file"):
        output = memorize_file_content(file_id=item_id, 
                                       session_id=session_id, 
                                       api_key=api_key, 
                                       user_api_keys=user_api_keys,
                                       forced_reload=forced_reload)

    elif (submit_button_id=="treat-as-questionnaire"):
        output = treat_as_questionnaire(file_id=item_id, 
                                        session_id=session_id, 
                                        api_key=api_key, 
                                        user_api_keys=user_api_keys,
                                        forced_reload=forced_reload)

    elif (submit_button_id=="main-chat" or submit_button_id == "question"):
        if available_models:
            if (type_of_template in available_models):
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                message_history = RedisChatMessageHistory(url=redis_url, ttl=604800, session_id=session_id)
                conversation_memory = ConversationBufferWindowMemory(memory_key="history", chat_memory=message_history, k=50)

                if len(conversation_memory.chat_memory.messages)==0:
                    ai_persona = AIPersonaRecall(item_id="main", 
                                api_key=api_key,
                                recall_group=user_api_keys["recall_group"])
                    conversation_memory.save_context({"input": "I am a Human named "+user_api_keys["first_name"] + " " + user_api_keys["last_name"]}, 
                                     {"output": "I am an AI Chatbot named " + ai_persona.first_name + " " + ai_persona.last_name + 
                                     ". My email is " +ai_persona.email + "." + 
                                     ai_persona.summary})

                if (type_of_template=="banana_stable_diffusion"):
                    model_inputs = {
                        "prompt": question,
                        "height": 768,
                        "width": 768,
                        "steps": 20,
                        "guidance_scale": 9,
                        "seed": None
                        }
                    out = banana.run(os.environ.get("BANANA_API_KEY"), available_models["banana_stable_diffusion"], model_inputs)
                    text_answer= "Generated image" + out["id"]
                    image_base64 = str(out["modelOutputs"][0]["image_base64"])

                elif (type_of_template=="banana_alpaca_13b"):
                    print(user_api_keys["firstName"]+": \n"+question+"\n"+type_of_template+":")
                    llm = Banana(model_key=available_models["banana_alpaca_13b"])
                    prompt= PromptTemplate(
                        input_variables=["question","history"],
                        template="###Context: {history} ###Instruction: {question} ###Response:",
                     )
                    llm_chain = LLMChain(prompt=prompt, llm=llm, memory=conversation_memory)
                    text_answer=llm_chain.run(question=question)
                    print("")

                elif (type_of_template=="banana_flant_t5"):
                    print(user_api_keys["firstName"]+": \n"+question+"\n"+type_of_template+":")
                    llm = Banana(model_key=available_models["banana_flant_t5"])
                    prompt= PromptTemplate(
                        input_variables=["question"],
                        template="{question}",
                     )
                    model_kwargs = {
                        "question": question, 
                        "context": str(conversation_memory.load_memory_variables({}))
                     }
                    llm_chain = LLMChain(prompt=prompt, llm=llm, memory=conversation_memory)
                    llm.model_kwargs=model_kwargs
                    text_answer=llm_chain.run(question=question)
                    print("")

                elif (type_of_template=="open_ai_gpt35"):
                    print(user_api_keys["first_name"]+": \n"+question+"\n"+type_of_template+":")
                    text_answer, actions, item_id, item_name, item_type = list_actions(question = question, 
                                                                                       type_of_template = type_of_template, 
                                                                                       api_key = api_key, 
                                                                                       item_id = item_id, 
                                                                                       item_name = item_name, 
                                                                                       item_type = item_type,
                                                                                       user_api_keys = user_api_keys)
                    if not text_answer:

                        if item_id != "None":
                            recall = Recall(item_id=item_id,
                                            api_key=api_key,
                                            recall_group=user_api_keys["recall_group"])

                            embedding_answer, link_name, link_url = query_embedding(question = question,
                                                                                    user_api_keys = user_api_keys,
                                                                                    recall = recall)

                            answer = embedding_answer +'<BR><a href="' + link_url + '">' + link_name + '</a>'

                        else:
                            llm = ChatOpenAI(model_name="gpt-3.5-turbo", streaming=True, callbacks=[StreamingStdOutCallbackHandler()], temperature=0)
                            conversation = ConversationChain(llm=llm, memory=conversation_memory)
                            answer=conversation(question)["response"]
                        text_answer = answer
                        print("")
            else:
                text_answer= f"Please set your API and/or Model Key for {type_of_template}"

            response = {"question": question, "answer": text_answer, "img": image_base64, "actions":actions }

        else:
            available_models, user_api_keys=is_authenticated(question)
            if user_api_keys:
                response = {"question": question, "answer": "Valid API-Key supplied!", "img": None, "actions":{}}
                logging.info("Valid API-Key supplied")
            else:
                response = {"question": question, "answer": "Missing or wrong API-Key. Please submit a valid Andea API key in the prompt.", "img": None, "actions":{}}
                logging.info("Missing or wrong API-Key")

        output = render_template("answer_chat.html", response=response, session_id=session_id, item_id=item_id, item_type=item_type, item_name=item_name)

    return output
