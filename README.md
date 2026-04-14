# llmfs: LLM in 9p filesystem

This is a 9p file server written in python, serve LLM service.
Currently it's experimental and is not ready for production environment.

## fs structure

Currently chatlogs' content is json format of the text and their attributes.
May change to plain text later.

```
llmfs
├── by-id
│   └── <chatlogs, uuid as filename>
├── by-index
│   └── <chatlogs, by their inserted order, index as filename>
├── by-role
│   ├── <roles>
│   │   └── <chatlogs of this role, uuid as filename>
│   └── user
│       └── <names>
│           └── <chatlogs made by this user, uuid as filename>
├── by-status   # Not functional yet
│   └── <status> 
│       └── <value>
│           └── <chatlogs matched with uuid as filename>
├── ctl
│   ├── gen # Reading from it generates response. Writing to it does nothing.
│   ├── clear # Read/Write it clear the chatlog
│   └── new # Writing to it adds new chatlog. Reading from it does nothing.
└── env
    └── <configs, key as filename>  # RO, config reloading isnt implemented yet
```

## Dependencies

 - [py9](https://git.sr.ht/~emru/py9)
 - vllm (Optional: Only if you want to use the vllm backend)
 - sglang (Optional: Only if you want to use the sglang backend)

## Backends

 - vllm
 - sglang (with little tested, sglang refuse to work on my orin nano, and somehow sglang uses more memory than vllm and it causes OOM)
 - dummy (for testing)

We may add TensorRT-LLM and simple transformer failback backends later(for TensorRT-LLM, it'll wait until JetPack 7.2 release). We also support backend registration from 3rdparty modules, check [backend.py](./llmfs/backend.py) and [backends/](./llmfs/backends/) for details.

## Clients

 - 9pfuse (In some cases, e.g. all our aarch64 machines, 9pfuse will refuse to connect for whatever reason)
 - v9fs
 - 9p (from plan9port)

Not tested in a real Plan9 machine yet(a power loss unfortuately killed my 9front installation on a rpi3 with gefs.) Maybe I'll test it in a plan9 QEMU machine later.

## AI Policy
We do not accept any kind of AI contribution, even if it's only used for commit description or docs.
All code and docs in this repo is written by human beings, if there're mistakes it's because the author is ESL.
We support "AI is the content", we do not support "AI generated content".

## TODO
 - We need a TODO list. (check the TODOs in source files for now)

## Questions / Contribution

 - If you have any questions or requests open an [issue](https://github.com/fish4terrisa-MSDSM/llmfs/issues)
 - Welcome for contribitions (Check our AI Policy first)

## License
AGPLv3 only, as described in [LICENSE.md](./LICENSE.md)
