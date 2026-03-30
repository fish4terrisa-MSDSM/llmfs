# This is basically a wrapper around a multi level dict just to make my life easier
import time
from py9 import (
    Modes,
    Stat,
    Qid,
)

# DIR, contain both static DIRs + FILEs and dynamic function for return a list of
# FILE and DIR
class FILE:
    def __init__(self, name: str, mode: Modes, get_content=None, set_content=None, rm=None, virtual=False):
        self.name = name
        self.mode = mode
        self.atime = self.mtime = int(time.time())
        self.virtual = virtual
        if get_content != None:
            self._get_content = get_content
        else:
            self._get_content = None
        if set_content != None:
            self._set_content = set_content
        else:
            self._set_content = None
        if rm != None:
            self._rm = rm
        else:
            self._rm = None
    
    def set_content(self, data: str | None):
        if self._set_content != None:
            self._set_content(self.name, data)
            self.atime = self.mtime = int(time.time())

    def get_content(self, offset, count):
        if self.virtual and (offset != 0):
            # So virtual files shouldnt allow offset, since another read call
            # will execute the function another time and ruin everything
            # TODO: A more elegant way to solve this
            return b''
        self.atime = int(time.time())
        if self._get_content != None:
            ret = self._get_content(self.name)
            # Ensure we use utf-8
            ret = ret.encode('utf-8')
            return ret[offset:offset+count]
        else:
            return b''

    # Virtual files always return 0 in length, meanwhile static files have fixed 
    # length
    def get_length(self):
        if self.virtual or (self._get_content == None):
            return 0
        else:
            return len(self._get_content(self.name))

    # .get() is used to get a file or dir in DIR, here we define it just so
    # we no longer need to concern if it has this method
    # TODO: maybe we should have a better name for all these functions and 
    # create a abstract class for FILE and DIR
    def get(self, _):
        return None

    def rm(self):
        if self._rm != None:
            return self._rm(self.name)
        else:
            # couldnt be removed if there's no _rm function
            return 1

    def get_stat(self, qid: Qid):
        _type = 77
        dev = 48
        # TODO: Add user namespace for chat log from different "user"(client)
        uid = 'user'
        gid = 'group'
        muid = 'user'
        return Stat(
            _type=_type,
            dev=dev,
            qid=qid,
            mode=self.mode,
            atime=self.atime,
            mtime=self.mtime,
            length=self.get_length(),
            name=self.name,
            uid=uid,
            gid=gid,
            muid=muid,
        )

# TODO: The dir remove part is a freaking mess
class DIR:
    # atime and mtime is set on init internally
    # on init the content should be empty
    # The root DIR's name doesnt matter, since it's only used to show subdirs
    # get_content return list of FILEs and DIRs
    # rm_content accept a str and delete all 
    # matched DIRs and FILEs(not recursively tho, we wont need it for now)
    def __init__(self, name: str, mode: Modes, get_content=None, rm_content=None):
        self.name = name
        self.mode = mode
        self.atime = self.mtime = int(time.time())
        self.content = []
        self._get_content=get_content
        self._rm_content=rm_content

    # This append a new static DIR or FILE in the list
    def append(self, target):
        self.atime = self.mtime = int(time.time())
        self.content.append(target)

    # This rm itself, for now it's only for internal usage so it's generally
    # fine to just delete it(in the context of dir, it's like `rm -r`)
    # By design 9p should be able to have two different files with the same name in
    # a dir I think? But we arent using this so whatever remove anything matched
    # TODO: Some dirs are immutable, add permission check
    # Return: 0(succeed), any other value(failed)
    def rm(self):
        errno = 0
        if self._get_content != None:
            dyn_content = self._get_content(self.name)
        else:
            dyn_content = []
        for target in self.content:
            ret = target.rm()
            if ret > 0:
                # For now, since it's unreasonable to leave a user a half
                # cleaned dir, lets delete everything possible, tho in this
                # case the dir itself isnt deleted
                errno = 1
                continue
            else:
                self.content.remove(target)
        for target in dyn_content:
            ret = target.rm()
            if ret > 0:
                errno = 1
        
        return errno


    def get(self, name: str):
        self.atime = int(time.time())
        # dynamic content comes first
        if self._get_content != None:
            dyn_content = self._get_content(self.name)
            for target in dyn_content:
                if target.name == name:
                    return target
        for target in self.content:
            if target.name == name:
                return target
        return None

    def get_content(self):
        self.atime = int(time.time())
        if self._get_content != None:
            return self.content + self._get_content(self.name)
        else:
            return self.content

    # DIRs dont have length
    def get_length(self):
        return 0

    # TODO: Put this function else where, maybe we need a FILELIKE abstract class
    def get_stat(self, qid: Qid):
        _type = 77
        dev = 48
        # TODO: Add user namespace for chat log from different "user"(client)
        uid = 'user'
        gid = 'group'
        muid = 'user'
        return Stat(
            _type=_type,
            dev=dev,
            qid=qid,
            mode=self.mode,
            atime=self.atime,
            mtime=self.mtime,
            length=self.get_length(),
            name=self.name,
            uid=uid,
            gid=gid,
            muid=muid,
        )
