import json
import os
import time
import hashlib

def is_authenticated(api_key):
    available_models={}
    with open(os.path.join(os.getcwd(), 'api-keys.json'), 'r') as f:
        api_key_dict = json.load(f)

    if api_key in api_key_dict:
        user_api_keys = api_key_dict[api_key]

        os.environ.update({'OPENAI_API_KEY': user_api_keys["openai_api_key"]})
        os.environ.update({"BANANA_API_KEY": user_api_keys["banana_api_key"]})

        available_models["ANDEAN_API_KEY"]=api_key

        if ("openai_api_key" in user_api_keys):
            available_models["open_ai_gpt35"]="open_ai_gpt35"

        if ("alpaca_13b_model_key" in user_api_keys):
            available_models["banana_alpaca_13b"]=user_api_keys["alpaca_13b_model_key"]

        if ("stable_diffusion_model_key" in user_api_keys):
            available_models["banana_stable_diffusion"]=user_api_keys["stable_diffusion_model_key"]

        if ("flant_t5_model_key" in user_api_keys):
            available_models["banana_flant_t5"]=user_api_keys["flant_t5_model_key"]

        return available_models, user_api_keys
    else:
        return available_models, None

def get_value_after_prefix(string, prefix=""):
    if string.startswith(prefix):
        return string[len(prefix):]
    else:
        return None

def get_session_id(api_key):
    hash_object = hashlib.md5(api_key.encode())
    return hash_object.hexdigest() + "-" + str(int(time.time()))