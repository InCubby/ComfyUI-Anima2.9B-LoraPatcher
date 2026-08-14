# ComfyUI-Anima2.9B-LoraPatcher

English | [中文](README.zh-CN.md)

A ComfyUI custom node that hot-patches LoRA weights trained on the original
**28-block Anima** model so they align with the official **40-block
[Anima-2.9B](https://huggingface.co/Gazingstars123/Anima-2.9B)**.

Works on a whole `lora_stack` (e.g. output from LoRA Manager): each entry
is detected, remapped in memory, and applied with the standard
`comfy.sd.load_lora_for_models` pipeline. No file is written to disk.

## Credits

This node is a direct port of the layer-conversion logic from
**[storyAura/Anima2.9B-Lora-weight-conversion](https://github.com/storyAura/Anima2.9B-Lora-weight-conversion)**.
The 28→40 insertion layout (`expand_manifest.json`) and the key-remapping
algorithm come from that project — many thanks to **storyAura** for the
original tool and its documentation.

Related projects:

- [Gazingstars123/Anima-2.9B](https://huggingface.co/Gazingstars123/Anima-2.9B) — official 40-block model
- [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) — original 28-block base
- [gazingstars123/ComfyUI-Anima-2.9B](https://github.com/gazingstars123/ComfyUI-Anima-2.9B) — ComfyUI depth patch
- [LLaMA Pro: Progressive LLaMA with Block Expansion](https://arxiv.org/abs/2401.02415)

## Installation

Copy or symlink this folder into `ComfyUI/custom_nodes/`:

```
git clone https://github.com/InCubby/ComfyUI-Anima2.9B-LoraPatcher.git
```

then restart ComfyUI. The node appears under **loaders** as
`Anima2.9B LoRA Patcher`.

No extra dependencies: uses `safetensors` / `torch` that ship with ComfyUI.

## Usage

Node: **Anima2.9BLoraPatcher** (category: loaders)

Inputs:

| Input           | Type       | Description |
|-----------------|------------|-------------|
| `model`         | MODEL      | Anima-2.9B model (40 blocks) |
| `clip`          | CLIP       | Text encoder, passed through |
| `lora_stack`    | LORA_STACK | Every entry is processed in order |
| `fill_inserted` | none/copy   | none (recommended): inserted blocks get no LoRA patch; copy: duplicate the neighbor-source LoRA onto inserted blocks |

Outputs: `MODEL`, `CLIP`, and a `report` string listing what happened to
each entry plus the 28→40 alignment table.

Typical workflow with LoRA Manager: connect `model`, `clip` and the
manager's `lora_stack` to this node instead of a vanilla `LoraLoader`.
28-block Anima LoRAs in the stack are remapped automatically; other LoRAs
pass through untouched.

## How it works

- 28 original blocks keep their order and shift into the non-inserted slots
  of the 40-block layout (insertion positions `2, 5, 8, 11, 14, 17, 21, 24, 27, 30, 33, 36`),
  e.g. old block `2` → new block `3`, old block `27` → new block `39`.
- Inserted blocks are left without patches by default (`fill_inserted=none`),
  matching the "muted init" idea of Anima-2.9B's expansion recipe.
- Detection is heuristic: any LoRA whose `blocks.<idx>` keys have a max
  index ≤ 27 is treated as a 28-block Anima LoRA and remapped; everything
  else passes through untouched.

## Notes

- Only LoRA layer indices are remapped; Anima-2.9B base weights are untouched.
- Loading Anima-2.9B in ComfyUI still requires
  [ComfyUI-Anima-2.9B](https://github.com/gazingstars123/ComfyUI-Anima-2.9B)
  so the model is recognized with 40 blocks.

## License

The remapping algorithm and manifest are derived from
[storyAura/Anima2.9B-Lora-weight-conversion](https://github.com/storyAura/Anima2.9B-Lora-weight-conversion).
Please respect that project's terms; no separate license is declared here.
