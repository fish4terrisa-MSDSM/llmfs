from ..backend import llmfs_llm_server

class backend_dummy(llmfs_llm_server):
    def __init__(self, model: str, tokenizer: str | None, extra_args: dict):
        print("Dummy Backend Init Start :D\n")
        print(f"The model path: {model}\n")
        self.model_path = model
        if tokenizer != None:
            self.tokenizer_path = tokenizer
            print(f"The tokenizer path: {tokenizer}\n")
        else:
            print("The tokenizer path is empty, so the model path is used instead!\n")
        self.llm_extra_args = extra_args
        print(f"All extra args passed to LLM(): {extra_args}\n")
        print("Dummy Backend Init Finished!!! YAYYYYYYY!!!!!!\n")

    def set_config(self, default_mode: str, structured_output: bool, modes_config: dict, eos_token: str, extra_args: dict):
        print("Dummy Backend setting configs XD\n")
        self.default_mode = default_mode
        print(f"The default mode: {default_mode}")
        self.structured_output = structured_output
        print(f"Use the structured output: {structured_output}\n")
        self.modes_config = modes_config
        print(f"The config of the modes: {modes_config}\n")
        self.eos_token = eos_token
        print(f"The eos token: {eos_token}\n")
        self.sampling_params_extra_args = extra_args
        print(f"All extra args passed to SamplingParams(): {extra_args}\n")
        print("Dummy Backend configs set!\n")

    def generate(self, prompt, response_mode: str | None, structured_output: bool | True):
        print("Dummy Backend generating!\n")
        print(f"Text: {prompt}\n")
        if response_mode != None:
            print(f"Mode: {response_mode}\n")
            if self.default_mode == response_mode:
                print("The Mode requested is equal with the default one, so no need to regenerate.\n")
        else:
            print(f"Mode is empty somehow, use the default {self.default_mode}\n")
        response = "Nyan~\n"
        print(f"Response: {response}\n")
        return response


