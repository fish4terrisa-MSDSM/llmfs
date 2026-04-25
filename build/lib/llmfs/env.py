import json
from py9 import Modes

import llmfs.config as config
import llmfs.vfs as vfs

"""
/env is used to expose writeable configs to the client. The design is still in it's early stage, so there're many situations where json is used instead of using filesystem to expose the data.
An alternative design could be /config, where the toml is dumped whenever it's read and the user write a toml into it to reload the config. No matter what design we choose in the end the logic of handling the config is needed anyway.
"""

def get_backend(_):
    return config.backend

def get_model_path(_):
    return config.model_path

def get_tokenizer_path(_):
    return config.tokenizer_path

def get_backend_extra_args(_):
    return json.dumps(config.backend_extra_args)

def get_current_mode(_):
    return config.mode

def get_enforce_structure(_):
    return str(config.enforce_structure)

def get_current_modes(_):
    return json.dumps(config.modes)

def get_generation_prompt(_):
    return config.generation_prompt

def get_eos_token(_):
    return config.eos_token

def get_roles(_):
    return json.dumps(config.roles)

# TODO: Make the readwrite function, finish the config reload logic, and convert
# those stupid jsons into filesystem-based database instead
def walk_env(_):
    files = []
    files.append(vfs.FILE("backend", Modes.DMREAD, get_content=get_backend))
    files.append(vfs.FILE("model_path", Modes.DMREAD, get_content=get_model_path))
    files.append(vfs.FILE("tokenizer_path", Modes.DMREAD, get_content=get_tokenizer_path))
    files.append(vfs.FILE("backend_extra_args", Modes.DMREAD, get_content=get_backend_extra_args))
    files.append(vfs.FILE("mode", Modes.DMREAD, get_content=get_current_mode))
    files.append(vfs.FILE("enforce_structure", Modes.DMREAD, get_content=get_enforce_structure))
    files.append(vfs.FILE("modes", Modes.DMREAD, get_content=get_current_modes))
    files.append(vfs.FILE("generation_prompt", Modes.DMREAD, get_content=get_generation_prompt))
    files.append(vfs.FILE("eos_token", Modes.DMREAD, get_content=get_eos_token))
    files.append(vfs.FILE("roles", Modes.DMREAD, get_content=get_roles))
    return files

