import sys
from .llmfs import main

if __name__ == "__main__":
    # This block allows my_module.py to be run directly as a script as well
    sys.exit(main(str(sys.argv[1])))
