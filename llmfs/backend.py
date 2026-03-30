from abc import ABC, abstractmethod

import llmfs.config as config

llmserver = None

available_backend = {}

# TODO: Async? Also currently shutdown llmserver and load a new one is not tested,
# and non of the actual backends support it so it's actually not possible to 
# let the changes in backend, backend_extra_args["llm"] and {model, tokenizer}_path
# take affect, when reloading is pretty much untested.
class llmfs_llm_server(ABC):
    # These kwargs should be forward to LLM(). This is initializing the LLM
    # loading model
    @abstractmethod
    def __init__(self, model: str, tokenizer: str | None, extra_args: dict):
        pass

    # This read a dict of config, and set those configs inside this object
    # The extra args should be stored in the class
    # TODO: Allow multiple modes get used at the same time
    @abstractmethod
    def set_config(self, default_mode: str, structured_output: bool, modes_config: dict, eos_token: str, extra_args: dict):
        pass

    # "mode" is for oneshot with a mode different from the config
    @abstractmethod
    def generate(self, text: str, response_mode: str | None, structured_output: bool | True):
        pass

# For internal and external backend registering
def backend_register(name: str, server: llmfs_llm_server):
    available_backend[name] = server

def llmserver_mode_reload():
    global llmserver
    llmserver.set_config(default_mode=config.mode, structured_output=config.enforce_structure, modes_config=config.modes, eos_token=config.eos_token, extra_args=config.backend_extra_args[config.backend]["samplingparams"])

# Init llmserver, use the backend in config.
def llmserver_init():
    global llmserver
    if available_backend.get(config.backend, False):
        tmp = available_backend[config.backend]
        llmserver = tmp(config.model_path, config.tokenizer_path, config.backend_extra_args[config.backend]["llm"])
        llmserver_mode_reload()
    else:
        raise ValueError("The backend isnt specified")

# This is for generate used in module
def llmserver_generate(text: str, response_mode: str | None, structured_output: bool | True):
    global llmserver
    return llmserver.generate(text, response_mode, structured_output)
