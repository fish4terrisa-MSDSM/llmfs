# It's not the exact same like 9p I think, but I'll say it's close enough :)
from pathlib import PurePosixPath
# Import py9
from py9 import (
    Py9Server,
    Errors,
    Fid,
    Qid,
    Stat,
    Types,
    Modes,
)

import llmfs.vfs as vfs
import llmfs.fs as fs
import llmfs.config as config

p9fs = None

# path should always be the absolute path, like '/ctl/gen', '/'
# things like 'ctl/gen' would work but not recommanded
def get_filelike(path: str):
    # sanitize path, if the path is '/' then we'll just return root so it's fine
    path = path.strip('/')
    _path = list(PurePosixPath(path).parts)
    tmp_filelike = fs.root
    for target_name in _path:
        tmp = tmp_filelike.get(target_name)
        if tmp != None:
            tmp_filelike = tmp
        else:
            #raise Exception("IMPOSSIBLE")
            return None
            break
    return tmp_filelike

class FileServer(Py9Server):
    def __init__(
            self,
            ip: str,
            port: int,
    ) -> None:
        super().__init__(ip, port)

        self.path_num = -1
        self.paths: dict[str, int] = {}

    def open_file(self, fid: Fid):
        # All things are stored in memory... So if doesnt make a difference opened
        # or not
        fid.fs_fid = fid.path


    def close_file(self, fid: Fid):
        # Again doesnt matter like at all
        if fid.fs_fid:
            fid.fs_fid = False

    def read_file(self, fid: Fid, offset: int, count: int) -> bytes:
        # Why? It doesnt matter... Tho I'll keep it
        if not fid.fs_fid:
            raise Exception("No file opened")
        if isinstance(fid.fs_fid, str):
            path = fid.fs_fid
            tmp = get_filelike(path)
            if tmp == None:
                return b''
            if isinstance(tmp, vfs.DIR):
                ret = b''
                fss = []
                for target in tmp.get_content():
                    qid: Qid = self.get_qid(path)
                    fss.append(target.get_stat(qid))
                for fs in fss:
                    ret += fs.to_bytes()
                return ret[offset:offset+count]
            # it's a vfs.FILE
            else:
                assert isinstance(tmp, vfs.FILE)
                # TODO: This should only apply to 
                if (offset != 0):
                    return b''
                return tmp.get_content(offset, count)

    def write_file(self, fid: Fid, offset: int, count: int, content: str) -> int:
        if not fid.fs_fid:
            raise Exception("No file opened")
        if isinstance(fid.fs_fid, str):
            path = fid.fs_fid
            tmp = get_filelike(path)
            # TODO: Maybe verify this is a file?
            # We cannot create directories for now, but we may add this
            tmp.set_content(content)
            # TODO: Should return the actual count
            return count

    def check_file_type(self, path: str) -> Types:
        tmp = get_filelike(path)
        if tmp == None:
            print("check_file_t: " + path + " NONE!")
            return None
        if isinstance(tmp, vfs.DIR):
            return Types.QTDIR
        else:
            return Types.QTFILE

    def get_path_num(self) -> int:
        self.path_num += 1
        if self.path_num > 256 ** 8 - 1:
            self.path_num = 0

        return self.path_num

    def get_qid(self, path: str) -> Qid:
        if path in self.paths:
            return self.qids[self.paths[path]]
        path_num = self.get_path_num()
        file_type = self.check_file_type(path)
        qid = Qid(
            _type=file_type,
            version=0,
            path=path_num,
        )
        self.paths[path] = path_num
        self.qids[self.paths[path]] = qid
        return qid

    def handle_Tauth(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']
        client.socket.sendall(
            client._encode_Rerror(
                Errors.Enoauth,
                data['tag'],
            )
        )

    def handle_Tattach(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']
        fid = data['fid']

        if fid in client.fids:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Edupfid,
                    data['tag'],
                )
            )
            return

        qid = self.get_qid('/')
        client.fids[fid] = Fid(
            fid=fid,
            path='/',
            qid=qid,
        )
        client.socket.sendall(
            client._encode_Rattach(
                qid,
                data['tag'],
            )
        )

    def handle_Tflush(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']
        client.socket.sendall(
            client._encode_Rerror(
                Errors.Eperm,
                data['tag'],
            )
        )

    def handle_Twalk(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        if data['fid'] not in client.fids:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Eunknownfid,
                    data['tag'],
                )
            )
            return

        if data['newfid'] in client.fids and data['fid'] != data['newfid']:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Edupfid,
                    data['tag'],
                )
            )
            return

        fid = client.fids[data['fid']]
        nfid = Fid(
            fid=data['newfid'],
            path=fid.path,
        )

        walk_nodir = True
        failed = False
        new_path = fid.path
        qids: [Qid] = []

        if not data['wnames']:
            nfid.path = fid.path
            nfid.qid = self.get_qid(fid.path)
            client.fids[data['newfid']] = nfid

            client.socket.sendall(
                client._encode_Rwalk(
                    qids,
                    data['tag'],
                )
            )
            return

        for p in map(lambda x: x.decode(), data['wnames']):
            if not isinstance(get_filelike(new_path), vfs.DIR):
                failed = True
                break
            walk_nodir = False
            if '/' in p:
                client.socket.sendall(
                    client._encode_Rerror(
                        Errors.Ebotch,
                        data['tag'],
                    )
                )
            if p == '..':
                if new_path != '/':
                    new_path = '/'.join(new_path.split('/')[0:-1])
            else:
                p_path = new_path + '/' + p
                if get_filelike(p_path) != None:
                    new_path = p_path
                else:
                    failed = True
                    break
            qids.append(self.get_qid(new_path))

        if failed and walk_nodir:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Ewalknodir,
                    data['tag'],
                )
            )
            return

        if not failed:
            nfid.path = new_path
            nfid.qid = self.get_qid(new_path)
            client.fids[data['newfid']] = nfid

        client.socket.sendall(
            client._encode_Rwalk(
                qids,
                data['tag'],
            )
        )

    def handle_Topen(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = data['fid']
        try:
            mode = Modes(data['mode'])
        except ValueError:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Enowrite,
                    data['tag'],
                )
            )
            return

        if data['fid'] not in client.fids:
            client.socket.sendall(
                client._encode_Rerror(
                    Errors.Eunknownfid,
                    data['tag'],
                )
            )
            return

        # TODO: What's this???????????
        #if ((mode != Modes.OREAD) or (mode != Modes.OWRITE) or (mode != Modes.DMDIR)):
        #    client.socket.sendall(
        #        client._encode_Rerror(
        #            Errors.Enowrite,
        #            data['tag'],
        #        )
        #    )
        #    return

        fid_c: Fid = client.fids[fid]
        qid = fid_c.qid
        self.open_file(fid_c)

        client.socket.sendall(
            client._encode_Ropen(
                qid,
                self.msize,
                data['tag'],
            )
        )

    # No create dirs for now
    def handle_Tcreate(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']
        client.socket.sendall(
            client._encode_Rerror(
                Errors.Enocreate,
                data['tag'],
            )
        )

    def handle_Tread(self, d: dict):
        global log, settings, gen_settings
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = data['fid']
        offset = data['offset']
        count = data['count']

        fid_c: Fid = client.fids[fid]
        readed = self.read_file(fid_c, offset, count)

        client.socket.sendall(
            client._encode_Rread(
                readed,
                data['tag'],
            )
        )

    def handle_Twrite(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = data['fid']
        offset = data['offset']
        count = data['count']
        content = data['data']

        fid_c: Fid = client.fids[fid]
        count = self.write_file(fid_c, offset, count, content)

        client.socket.sendall(
            client._encode_Rwrite(
                count,
                data['tag'],
            )
        )

    def handle_Tclunk(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = data['fid']
        try:
            fid_c: Fid = client.fids[fid]
            self.close_file(fid_c)
            del client.fids[fid]
        except KeyError:
            pass

        client.socket.sendall(
            client._encode_Rclunk(
                data['tag'],
            )
        )

    # TODO: Add delete_file
    def handle_Tremove(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = client.fids[data['fid']]
        path = fid.path

        ret = False
        if path != None:
            tmp = get_filelike(path)
            if tmp != None:
                # TODO: Dir removal is not done yet
                if isinstance(tmp, vfs.FILE):
                    ret = tmp.rm()

        if not ret:
            del client.fids[data['fid']]


        client.socket.sendall(
            client._encode_Rremove(
                data['tag'],
            )
        )

    def handle_Tstat(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = client.fids[data['fid']]
        path = fid.path
        qid = fid.qid
        target = get_filelike(path)
        stat = target.get_stat(qid)

        client.socket.sendall(
            client._encode_Rstat(
                [stat],
                data['tag'],
            )
        )

    # TODO: Twstat NOT TESTED
    def handle_Twstat(self, d: dict):
        client: Py9Server.Client = self.clients[d['client_id']]
        data: dict = d['data']

        fid = client.fids[data['fid']]
        stat = Stat.from_bytes(data['stat'])
        qid = stat.qid
        target = get_filelike(fid.path)

        if target != None:
            target.atime = stat.atime
            target.mtime = stat.mtime
            client.socket.sendall(
                client._encode_Rwstat(
                    data['tag'],
                )
            )
        else:
            client._encode_Rerror(
                Errors.Enowstat,
                data['tag']
            )

# Init the p9 server, initialize the paths
def p9fs_init():
    global p9fs
    p9fs = FileServer(
        ip=config.listenip,
        port=int(config.port),
    )
