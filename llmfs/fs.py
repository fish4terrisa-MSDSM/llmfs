from py9 import Modes

import llmfs.vfs as vfs
import llmfs.data as data
import llmfs.env as env

root = None
"""
/
|
|
|===ctl/===gen
|      |
|      |===new
|
|===env/===<files, parameter as name, content is the value>
|
|
|===by-id/===<files contain the json, with id as the filename>
|          
|
|===by-index/===<files contain the json, with the index as the filename>
|
|
|===by-role/===<dirs name with role name, except user>/===<id>
|          |
|          |
|          |===user/===<speaker>/===<id>
|
|
|===by-status/===<dirs like (un)processed>/===<id>      # /by-status is incompleted
"""
# This initialize the root
# TODO: Currently non dirs are actually writeable(deleteable), this need to be fixed
# And it potentially might affect the user's ability to delete files
def root_init():
    global root
    # for now all dirs are READ+EXEC
    root = vfs.DIR("/", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC)
    ctl = vfs.DIR("ctl", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC)
    ctl.append(vfs.FILE("gen", Modes.DMREAD, get_content=data.get_response, virtual=True))
    # TODO: maybe /ctl/new only need write permission
    ctl.append(vfs.FILE("new", Modes.DMREAD | Modes.DMWRITE, set_content=data.append_to_data, virtual=True))
    ctl.append(vfs.FILE("clear", Modes.DMREAD | Modes.DMWRITE, get_content=data.clear_data, set_content=data.clear_data, virtual=True))
    root.append(ctl)
    root.append(vfs.DIR("env", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=env.walk_env))
    root.append(vfs.DIR("by-id", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=data.walk_by_id))
    root.append(vfs.DIR("by-index", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=data.walk_by_index))
    root.append(vfs.DIR("by-role", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=data.walk_by_role))
    # TODO: rework and finish /by-status Rahhhhhhhhhhh!!!
    status = vfs.DIR("by-status", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC)
    status.append(vfs.DIR("processed", Modes.DMDIR | Modes.DMREAD | Modes.DMEXEC, get_content=data.walk_by_status))
    root.append(status)
