import llmfs.config as config
import llmfs.fs as fs
import llmfs.p9fs as p9fs
import llmfs.backend as backend
import llmfs.backends as backends
def llmfs_init(config_path: str):
    config.config_init(config_path)
    fs.root_init()
    p9fs.p9fs_init()
    # TODO: backends are registered here manually, should be dynamicly registered
    backend.backend_register("dummy", "llmfs.backends.dummy.backend_dummy")
    backend.backend_register("vllm", "llmfs.backends.vllm.backend_vllm")
    backend.backend_register("sglang", "llmfs.backends.sglang.backend_sglang")
    backend.llmserver_init()

def main(config_path: str):
    llmfs_init(config_path)
    while True:
        try:
            print(p9fs.p9fs.serve())
            #fs.serve()
        except KeyboardInterrupt:
            del p9fs.p9fs
            break
