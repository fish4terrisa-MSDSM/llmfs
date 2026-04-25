import tomllib

# Config settings
# "readonly" decides if the configs are editable
# 0(rw), !=0(ro)
readonly = 0
# Backend settings, for now by default it's "vllm"
# One backend at a time
backend = "vllm"
model_path = "/usr/src/llm/olmo-instruct"
# If tokenizer_path is None then the tokenizer is stored in the same path of the
# model
tokenizer_path = None

# This is a list of backend extra args
# it's passed to the backend part directly
# TODO: These are forced readonly for now(since wrong args would cause the server to
# crash. Should add checks for these args and remove those potential harmful ones
backend_extra_args = { 
    'vllm': {
        'llm': {
            'max_num_seqs': 1,
            'max_num_batched_tokens': 256,
            'max_model_len': 256,
            'dtype': 'auto',
            'trust_remote_code': True,
            'calculate_kv_scales': True,
            'enforce_eager': True,
            'gpu_memory_utilization': 0.76,
            'swap_space': 2,
            'kv_cache_dtype': 'fp8'
        },
        'samplingparams': {
            'temperature': 0.6,
            'top_p': 0.95,
            'n': 1,
            'max_tokens': 2048
        } 
    } 
}

# Server settings
listenip = "127.0.0.1"
port = 26980

# Mode settings
mode = "unknown"
enforce_structure = True
modes = { "unknown": { "start": "", "end": "", "stop": 0 } }

# generation prompt settings
generation_prompt = "<|im_start|>assistant\n"
eos_token = "<|im_end|>"

# role settings
# Required roles: "system", "environment", "assistant", "user"
# Forbidden role: "null" (used for plain text)
roles = {
    'system': {
        'template': '<|im_start|>system\n{content}<|im_end|>\n'
    },
    'environment': {
        'template': '<|im_start|>environment\n{content}<|im_end|>\n'
    }, 
    'assistant': {
        'template': '<|im_start|>assistant\n{content}<|im_end|>\n'
    }, 
    'user': {
        # Optional: use the var "name" for the speaker's name
        'template': '<|im_start|>user\n{content}<|im_end|>\n'
    }
}

# Let them fail when tomllib cannot decode the toml
def load_config(file: str | None):
    if file != None:
        with open(file, 'rb') as f:
            config = tomllib.load(f)
            return config
    else:
        # Global config
        try:
            with open('/etc/llmfs.toml', 'r') as f:
                config = tomllib.load(f)
                return config
        except FileNotFoundError:
            pass
        # llmfs.toml in current directory
        try:
            with open('llmfs.toml', 'r') as f:
                config = tomllib.load(f)
                return config
        except FileNotFoundError:
            pass

    # Even though we have default configs, it's not for actual usage but examples
    raise FileNotFoundError("Config TOML file NOT FOUND!")

def config_init(file: str | None):
    global readonly, backend, model_path, tokenizer_path, backend_extra_args, listenip, port, mode, enforce_structure, modes, generation_prompt, eos_token, roles
    config = load_config(file)
    if config.get("readonly", False):
        if type(config["readonly"]) is int:
            readonly = config["readonly"]
        else:
            raise TypeError("'readonly' field accepts int only. 0(rw), 1(ro)")
    # TODO: Some of them should fail if they dont exist to avoid attacks based on
    # the example settings
    if config.get("backend", False):
        backend_extra_args = config["backend"]
        backend = backend_extra_args.pop("backend", backend)
        model_path = backend_extra_args.pop("model_path", model_path)
        tokenizer_path = backend_extra_args.pop("tokenizer_path", tokenizer_path)
    if config.get("server", False):
        if config["server"].get("listenip", False):
            listenip = config["server"]["listenip"]
        if config["server"].get("port", False):
            port = config["server"]["port"]
    if config.get("prompt", False):
        if config["prompt"].get("generation", False):
            generation_prompt = config["prompt"]["generation"]
        if config["prompt"].get("eos", False):
            eos_token = config["prompt"]["eos"]
    if config.get("mode", False):
        modes = config["mode"]
        if modes.get("enforce_structure", False):
            enforce_structure = modes.pop("enforce_structure", enforce_structure)
        mode = modes.pop("default", mode)
    if config.get("role", False):
        roles = config["role"]





