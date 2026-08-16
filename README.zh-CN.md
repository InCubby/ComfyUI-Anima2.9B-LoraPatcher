# ComfyUI-Anima2.9B-LoraPatcher

[English](README.md) | 中文

一个 ComfyUI 自定义节点，可将基于原始 **28 块 Anima** 模型训练的 LoRA 权重
热修补对齐到官方 **40 块 [Anima-2.9B](https://huggingface.co/Gazingstars123/Anima-2.9B)** 模型。

作用于整个 `lora_stack`（例如 LoRA Manager 的输出）：逐条检测、在内存中重映射，
并沿用标准 `comfy.sd.load_lora_for_models` 流程应用。不写入任何磁盘文件。

## 致谢

本节点是 [storyAura/Anima2.9B-Lora-weight-conversion](https://github.com/storyAura/Anima2.9B-Lora-weight-conversion)
层转换逻辑的直接移植。28→40 的插入布局（`expand_manifest.json`）与键重映射算法
均来自该项目——非常感谢 **storyAura** 提供的原始工具与文档。

相关项目：

- [Gazingstars123/Anima-2.9B](https://huggingface.co/Gazingstars123/Anima-2.9B) — 官方 40 块模型
- [circlestone-labs/Anima](https://huggingface.co/circlestone-labs/Anima) — 原始 28 块基础模型
- [gazingstars123/ComfyUI-Anima-2.9B](https://github.com/gazingstars123/ComfyUI-Anima-2.9B) — ComfyUI 深度补丁
- [LLaMA Pro: Progressive LLaMA with Block Expansion](https://arxiv.org/abs/2401.02415)

## 安装

将本文件夹复制或软链接到 `ComfyUI/custom_nodes/`：

```
git clone https://github.com/InCubby/ComfyUI-Anima2.9B-LoraPatcher.git
```

然后重启 ComfyUI。节点位于 **loaders** 分类下，名为
`Anima2.9B LoRA Patcher`。

无需额外依赖：使用 ComfyUI 自带的 `safetensors` / `torch`。

## 用法

节点：**Anima2.9BLoraPatcher**（分类：loaders）

输入：

| 输入            | 类型       | 说明 |
|-----------------|------------|------|
| `model`         | MODEL      | Anima-2.9B 模型（40 块） |
| `clip`          | CLIP       | 文本编码器，原样传递 |
| `lora_stack`    | LORA_STACK | 按顺序处理栈中的每一条目 |
| `enable_remap`  | BOOLEAN   | 开启（默认）：检测并重映射 28 块 Anima LoRA；关闭：按栈原样加载，不修补 |
| `fill_inserted` | none/copy   | none（推荐）：插入块不应用 LoRA 补丁；copy：将相邻源块上的 LoRA 复制到插入块 |

输出：`MODEL`、`CLIP`，以及一个 `report` 字符串，列出每个条目的处理结果
和 28→40 对齐表。

配合 LoRA Manager 的典型工作流：将 `model`、`clip` 和 Manager 的 `lora_stack`
连接到本节点，以替代原生 `LoraLoader`。栈中的 28 块 Anima LoRA 会被自动重映射；
其他 LoRA 原样透传。

## 工作原理

- 28 个原始块保持顺序，移入 40 块布局中的非插入槽位（插入位置
  `2, 5, 8, 11, 14, 17, 21, 24, 27, 30, 33, 36`），例如旧块 `2` → 新块 `3`，
  旧块 `27` → 新块 `39`。
- 默认情况下插入块不应用补丁（`fill_inserted=none`），与 Anima-2.9B
  扩展配方的「静默初始化」思路一致。
- 检测采用启发式：`blocks.<idx>` 键的最大索引 ≤ 27 的 LoRA 即视为
  28 块 Anima LoRA 并重映射；其余一律原样透传。

## 注意事项

- 仅重映射 LoRA 的层索引；Anima-2.9B 基础权重不受影响。
- 在 ComfyUI 中加载 Anima-2.9B 仍需要
  [ComfyUI-Anima-2.9B](https://github.com/gazingstars123/ComfyUI-Anima-2.9B)
  才能将模型识别为 40 块。

## 许可

重映射算法与清单派生自
[storyAura/Anima2.9B-Lora-weight-conversion](https://github.com/storyAura/Anima2.9B-Lora-weight-conversion)。
请遵守该项目的条款；本仓库未单独声明许可。
