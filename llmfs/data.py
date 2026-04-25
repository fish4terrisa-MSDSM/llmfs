import json
import uuid
import time
from py9 import Modes

import llmfs.vfs as vfs
import llmfs.utils as utils
import llmfs.config as config
import llmfs.backend as backend


PLACEHOLDER_USER_NAME = "Unknown"

"""
The array of chatlogs.
all it's members are like this:
{
  "id": <uuid>,
  "index": <int: index>,    // This is not present in dict(data), but in the files
  "text": "<text>",
  "role": "<role>",
  "name": "<name>",         // Only for user chats, have no effects on other roles
  "processed": <int: processed>
}
All roles has a default prompt template, set in config toml. However, the 'null'
role is special, it doesnt use any template and the text is added to the context
without format.
"""
data = {}

def clear_data(_, _content=None):
    global data
    data.clear()
    return ''

def get_by_id(uuid: str):
    global data
    try:
        # TODO: Maybe... we make ever chatlog a dir instead of files contain json?
        tmp = data[uuid]
        tmp["index"] = list(data).index(uuid)
        return json.dumps(tmp)
    except KeyError:
        # Use None as a error for nonexisted chatlog
        return None

def get_by_index(index: str):
    global data
    if index.isnumeric():
        try:
            return get_by_id(list(data.keys())[int(index)])
        except IndexError:
            # Index out of range
            # TODO: Correct error handling
            return {}
    else:
        # TODO: Index isnt int. Should fail immediately.
        return {}

def get_response(_):
    global data
    # TODO: Should add a way to change these params temporarily
    ret = backend.llmserver_generate(apply_template(), response_mode=config.mode, structured_output=config.enforce_structure)
    tmp = {}
    tmp["id"] = str(uuid.uuid4())
    # TODO: add get_atime() and get_mtime() to FILE and DIR
    #tmp["atime"] = int(time.time())
    #tmp["mtime"] = int(time.time())
    tmp["text"] = ret
    tmp["role"] = "assistant"
    tmp["processed"] = 0
    data[tmp["id"]] = tmp
    return json.dumps(tmp)


def set_by_id(uuid: str, content: str):
    global data
    try:
        content = json.loads(content)
        tmp = data[uuid]
        if content.get("text", False):
            tmp["text"] = content["text"]
        if content.get("role", False):
            if (content["role"] in config.roles.keys()) or (content["role"] == "null"):
                tmp["role"] = content["role"]
            else:
                # TODO: The role isnt vaild, should return Rerror to report
                tmp["role"] = "user"
            if content["role"] == "user":
                if content.get("name", False):
                    tmp["name"] = content["name"]
                else:
                    if not tmp.get("name", False):
                        tmp["name"] = PLACEHOLDER_USER_NAME
        if data[uuid] != tmp:
            tmp["processed"] = 0
        data[uuid] = tmp
        if content.get("index", False):
            # TODO: Correct error handling, for now it silently ignores.
            if isinstance(content["index"], int) or (str(content["index"]).isnumeric()):
                data = utils.move_to_position(data, uuid, int(content["index"]))
    except json.JSONDecodeError:
        # When a non json is written, we treat it as a content change
        # FIXME: Questionable API
        try:
            tmp = data[uuid]
            tmp["text"] = content
            tmp["processed"] = 0
            data[uuid] = tmp
        except KeyError:
            # sliently drop it for now
            pass
            # DEBUG
            #raise Exception("No such uuid...")
    except KeyError:
        # sliently drop it for now
        pass
        # DEBUG
        #raise Exception("No such uuid...")

def set_by_index(index: str, content):
    global data
    if index.isnumeric():
        try:
            set_by_id(list(data.keys())[int(index)], content)
        except IndexError:
            # Index out of range
            # TODO: Correct error handling
            pass
    else:
        # TODO: Index isnt int. Should fail immediately.
        pass

def rm_by_id(uuid: str):
    global data
    data.pop(uuid, None)
    return 0

def rm_by_index(index: str):
    global data
    if index.isnumeric():
        try:
            rm_by_id(list(data.keys())[int(index)])
            return 0
        except IndexError:
            # Index out of range
            # TODO: Correct error handling
            return 1
    else:
        # TODO: Index isnt int. Should fail immediately.
        return 1

def walk_by_id(_):
    global data
    files = []
    for id_name in data.keys():
        files.append(vfs.FILE(id_name, Modes.DMREAD | Modes.DMWRITE, get_content=get_by_id, set_content=set_by_id, rm=rm_by_id))
    return files

def walk_by_name(name: str):
    global data
    files = []
    for id_name, value in data.items():
        # For now only users have names, no support for multi llms
        if value["role"] == "user":
            if value["name"] == name:
                files.append(vfs.FILE(id_name, Modes.DMREAD | Modes.DMWRITE, get_content=get_by_id, set_content=set_by_id, rm=rm_by_id))
    return files

def walk_by_role_role(role: str):
    global data
    items = []
    if role == "user":
        names = set([])
        for _, value in data.items():
            if value["role"] == "user":
                if value["name"] not in names:
                    names.add(value["name"])
        for name in names:
            items.append(vfs.DIR(name, Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=walk_by_name))
    else:
        for id_name, value in data.items():
            if value["role"] == role:
                items.append(vfs.FILE(id_name, Modes.DMREAD | Modes.DMWRITE, get_content=get_by_id, set_content=set_by_id, rm=rm_by_id))
    return items

def walk_by_index(_):
    global data
    files = []
    for index, (_, _) in enumerate(data.items()):
        files.append(vfs.FILE(str(index), Modes.DMREAD | Modes.DMWRITE, get_content=get_by_index, set_content=set_by_index, rm=rm_by_index))
    return files

def walk_by_role(_):
    global data
    dirs = []
    roles = set([])
    for _, value in data.items():
        roles.add(value["role"])
    for value in roles:
        dirs.append(vfs.DIR(value, Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=walk_by_role_role))
    return dirs

# TODO: /by-status is highly unfinished, the "processed" or not handle logic
# is damn freaking horrible, this function need a whole rework and the /by-status
# structure needs to be redesigned
def walk_by_status(status_filter):
    global data
    files = []
    for id_name, value in data.items():
        if value["processed"] == int(status_filter == "processed"):
            files.append(vfs.FILE(id_name, Modes.DMREAD | Modes.DMWRITE, get_content=get_by_id, set_content=set_by_id, rm=rm_by_id))
    return files

def append_to_data(_, content: str):
    global data
    try:
        # TODO: Settings in env
        content = json.loads(content)
    except json.JSONDecodeError:
        # Non json is treated as plain text.
        # TODO: VLM and STT support
        content = { "text": content.decode("utf-8", errors='replace') }
    tmp = {}
    tmp["id"] = str(uuid.uuid4())
    if not content.get("text", False):
        # TODO: Correct Rerror 
        raise Exception("No text Key!!!")
    tmp["text"] = content["text"]
    # Check if the role is valid, failback to user
    if content.get("role", False):
    # TODO: The role isnt vaild, should return Rerror to report
        if (content["role"] in config.roles.keys()) or (content["role"] == "null"):
            tmp["role"] = content["role"]
        else:
            tmp["role"] = "user"
        if content["role"] == "user":
            if content.get("name", False):
                tmp["name"] = content["name"]
            else:
                tmp["name"] = PLACEHOLDER_USER_NAME
    else:
        tmp["role"] = "user"
        tmp["name"] = PLACEHOLDER_USER_NAME
    tmp["processed"] = 0
    data[tmp["id"]] = tmp
    # TODO: Should we respect the index given to /ctl/new?
    # if so we should put the index move logic elsewhere
    if content.get("index", False):
        # TODO: Correct error handling, for now it silently ignores.
        if content["index"].isnumeric():
            data = move_to_position(data, tmp["id"], int(content["index"]))

# TODO: Use the template in config, Currently isnt finished!!!
def apply_template():
    global data
    tmp = ''
    # The items in dicts follow follow the order of it's creation time.
    for msg_id, target in data.items():
        if target["role"] == "null":
            tmp += target["text"]
        else:
        # TODO: Add failback template, handle non defined roles
            format_string = config.roles[target["role"]]["template"]
            tmp += format_string.format(name=target.get("name", PLACEHOLDER_USER_NAME), content=target["text"])
        # For now apply_template() is only used when passing the text to the llm
        # TODO: maybe, just maybe we could put it at somewhere more reasonable
        # so we could use apply_template() elsewhere
        target["processed"] = 1
        data[msg_id] = target
    # DEBUG
    print(tmp)
    # TODO: Maybe a generation_prompt arg to decide add a prompt or not?
    tmp += tmp + config.generation_prompt
    return tmp
