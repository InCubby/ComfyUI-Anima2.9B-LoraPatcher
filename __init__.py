import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anima_lora_patcher import Anima2_9BLoraPatcher

NODE_CLASS_MAPPINGS = {
    "Anima2.9BLoraPatcher": Anima2_9BLoraPatcher,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Anima2.9BLoraPatcher": "Anima2.9B LoRA Patcher",
}
