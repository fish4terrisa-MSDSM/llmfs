import nest_asyncio

nest_asyncio.apply()

# launch the offline engine
import asyncio

import sglang as sgl
from sglang.utils import async_stream_and_merge, stream_and_merge

from ..backend import llmfs_llm_server

class backend_sglang(llmfs_llm_server):
    def __init__(self, model: str, tokenizer: str | None, extra_args: dict):
        # llm_extra_args is bonded to llmserver and shouldnt be changeable
        self.llm_extra_args = extra_args
        self.llm = sgl.Engine(model_path=model, tokenizer_path=tokenizer, **extra_args)

    def set_config(self, default_mode: str, structured_output: bool, modes_config: dict, eos_token: str, extra_args: dict):
        self.default_mode = default_mode
        self.modes_config = modes_config
        self.eos_token = eos_token
        self.sampling_params_extra_args = extra_args
        self.default_structured_output = structured_output
        if (self.modes_config[self.default_mode]["start"] == "") and (self.modes_config[self.default_mode]["end"] == ""):
            # Disable structured output when both start and end is empty
            self.default_structured_output = False
        if self.default_structured_output:
            self.structured_outputs_params = { "regex": fr"{self.modes_config[self.default_mode]["start"]}.*?{self.modes_config[self.default_mode]["end"]}" }
        else:
            self.structured_outputs_params = {}
        stop_tokens = [ self.eos_token ]
        for key, value in self.modes_config.items():
            # Add all end tokens to it
            if value["end"] == "":
                continue
            if value["stop"] > 0:
                stop_tokens.append(value["end"])
        self.stop_tokens = stop_tokens
        self.sampling_params = {**(self.structured_outputs_params), **(self.sampling_params_extra_args) }
        self.sampling_params["stop"] = self.stop_tokens
        self.sampling_params["no_stop_trim"] = True
        # We always include the stop str. However, when the eos_tokwn is at
        # the end of the result, we remove it. This is implemented in
        # .generate()
        # TODO: Find a more elegant way to do this
        self.sampling_params.update(self.structured_outputs_params)
        print(self.sampling_params)

    def generate(self, prompt, response_mode: str | None, structured_output: bool | True):
        if response_mode == None:
            response_mode = self.default_mode
        # If the config is the same as the configs used to generate self.sampling_params
        # TODO: Currently this is useless since the same backend config is passed
        # to both set_config() and generate() and we cannot even change the config
        # (even if we can change the server config, it still should call set_config()
        # first. We need a elegant way to generate a response with a temp config
        # only once.
        ret = None
        if (self.default_mode == response_mode) and (self.default_structured_output == structured_output):
            ret = self.llm.generate(prompt, self.sampling_params)
        else:
            use_structured_output = structured_output
            temp_structured_outputs_params = {}
            if (self.modes_config[response_mode]["start"] == "") and (self.modes_config[response_mode]["end"] == ""):
                use_structured_output = False
            if use_structured_output:
                temp_structured_outputs_params = { "regex": fr"{self.modes_config[response_mode]["start"]}.*?{self.modes_config[response_mode]["end"]}" }
            temp_sampling_params = {**(self.structured_outputs_params), **(self.sampling_params_extra_args) }
            temp_sampling_params["stop"] = self.stop_tokens
            temp_sampling_params["no_stop_trim"] = True
            temp_sampling_params.update(temp_structured_outputs_params)
            ret = self.llm.generate(prompt, temp_sampling_params)
        ret = ret[0].output['text']
        # remove the eos token from the output if it exists
        ret = ret.removesuffix(self.eos_token)
        return ret
