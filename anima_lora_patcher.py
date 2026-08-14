from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import comfy.sd
import comfy.utils
import folder_paths

import anima_remap


class Anima2_9BLoraPatcher:
    RETURN_TYPES = ("MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("model", "clip", "report")
    FUNCTION = "patch"
    CATEGORY = "loaders"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_stack": ("LORA_STACK",),
                "fill_inserted": (["none", "copy"],),
            },
        }

    @staticmethod
    def _resolve_lora(name):
        if hasattr(folder_paths, "get_full_path_or_raise"):
            try:
                return folder_paths.get_full_path_or_raise("loras", name)
            except Exception:
                return None
        path = folder_paths.get_full_path("loras", name)
        if path:
            return path
        return folder_paths.get_annotated_filepath(name)

    def patch(self, model, clip, fill_inserted, lora_stack=None):
        manifest = anima_remap.load_manifest()

        entries = [tuple(e) for e in (lora_stack or [])]

        report = [
            "Anima2.9B LoRA Patcher",
            "fill_inserted={}".format(fill_inserted),
        ]
        warnings = []
        any_remap = False

        for entry in entries:
            name = str(entry[0])
            sm = float(entry[1]) if len(entry) > 1 else 1.0
            sc = float(entry[2]) if len(entry) > 2 else 1.0

            if sm == 0 and sc == 0:
                report.append("[skip] {} (strength 0)".format(name))
                continue

            path = self._resolve_lora(name)
            if path is None or not os.path.isfile(path):
                warnings.append("LoRA not found: {}".format(name))
                report.append("[missing] {}".format(name))
                continue

            try:
                lora = comfy.utils.load_torch_file(path, safe_load=True)
            except Exception as exc:
                warnings.append("failed to load {}: {}".format(name, exc))
                report.append("[error] {}: {}".format(name, exc))
                continue

            should_remap = anima_remap.detect_anima_28(lora.keys())

            if should_remap:
                lora, stats, unmapped = anima_remap.remap_lora_dict(lora, manifest, fill_inserted=fill_inserted)
                report.append(
                    "[28->40] {} (sm={:.2f}, sc={:.2f}): {} remapped, {} passthrough, {} copied".format(
                        name, sm, sc, stats["remapped"], stats["passthrough"], stats["inserted_copied"]
                    )
                )
                any_remap = True
                for key in unmapped[:10]:
                    warnings.append("  dropped key: {}".format(key))
                if len(unmapped) > 10:
                    warnings.append("  ... {} more dropped keys".format(len(unmapped) - 10))
            else:
                report.append("[pass] {} (sm={:.2f}, sc={:.2f})".format(name, sm, sc))

            try:
                model, clip = comfy.sd.load_lora_for_models(model, clip, lora, sm, sc)
            except Exception as exc:
                warnings.append("failed to apply {}: {}".format(name, exc))
                report.append("[error] apply {}: {}".format(name, exc))

        if any_remap:
            old_to_new, _, _ = anima_remap.build_block_maps(
                manifest["old_block_count"],
                manifest["new_block_count"],
                manifest["insertion_positions"],
                manifest.get("inserted_to_source"),
            )
            alignment = ", ".join("{}->{}".format(o, n) for o, n in sorted(old_to_new.items()))
            report.append("alignment: {}".format(alignment))

        report.extend(warnings)
        return (model, clip, "\n".join(report))
