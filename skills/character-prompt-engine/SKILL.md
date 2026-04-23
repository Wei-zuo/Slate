---
name: character-prompt-engine
description: 美术设计 Agent 的内部能力。用于把角色、场景、道具、style pack 或参考图需求，转成写入 `ImageJob.prompt` 的结构化 prompt block，服务 Slate 的 `ArtGenerationPlan.asset_jobs`。Use when Codex needs prompt blocks for character / location / prop / style-pack generation inside the art-design stage.
---

# Character Prompt Engine

## 定位

本 skill 默认由 `video-agent-orchestration` 在**美术设计阶段**调用。

它的产出不是“给用户复制的一段 prompt”，而是要进入 `ArtGenerationPlan.asset_jobs[*].prompt`，供图片生产 Agent 消费。

## 支持的 `asset_type`

本 skill 负责：

- `character`
- `location`
- `prop`
- `style_pack`

本 skill **不处理**：

- `camera_pack`

`camera_pack` 由副导演在镜头层指定，不由美术设计 skill 生成。

## 输出契约

默认输出的是可直接写入 `ImageJob.prompt` / `ImageJob.negative_prompt` 的 prompt block。

要求：

- 能说明要画什么
- 能锁定身份 / 结构 / 材质 / 色板 / 道具
- 能服务跨图一致性
- 不能只剩“漂亮 / 高级 / 电影感”这类空词

## Routing

在写 prompt 之前，先判断属于哪类：

- `base design`
  - 第一次给角色 / 场景 / 道具 / style pack 建锚点
- `variation`
  - 保持身份稳定，只换服装、灯光、时代、背景或情绪
- `consistency pass`
  - 把同一主体跨多张图的脸型、轮廓、服化道结构锁死
- `model mode`
  - 按目标图像模型或 image-to-video seed 调整语言密度

如果输入稀薄，做保守默认，不要擅自发明未经批准的剧情信息。

## Prompt Priorities

写 prompt 时，优先级固定：

1. 角色 / 场景 / 道具是什么
2. 结构锚点是什么
3. 材质逻辑是什么
4. 主色 / 辅色 / accent 是什么
5. 识别道具是什么
6. 画面构图和镜头高度是什么
7. 光线和 mood 是什么
8. 背景纪律是什么
9. 一致性语言是什么

优先写**可见结构**，不要写抽象赞美词。

## Model Modes

- `Universal / SDXL / Flux`
  - 用自然语言 + 结构化视觉分组
- `Midjourney`
  - 关键词密度更高，但仍然先写结构锚点
- `2D / anime`
  - 强调清晰轮廓、可读剪影、受控形状、cel / hand-drawn 逻辑
- `live-action / key art`
  - 强调镜头、材质、摄影光线和真实 production feel
- `image-to-video seed`
  - 强调同一张脸、同一套发型、同一套服装架构、同一套 style logic

## style_pack 的特殊写法

`style_pack` 的 prompt 不是“画一张什么东西”，而是“定义整个项目的风格基准”。

模板：

- 媒介 / rendering logic
- 主色关系
- 线条 / 体块 / 材质逻辑
- 光影纪律
- 镜头总体气质
- 必须避免的风格漂移

style pack prompt 示例结构：

```text
2D hand-drawn Chinese folklore animation style pack, blue-gray stone palette with warm gold highlights, clear silhouette hierarchy, ink-wash edges with controlled cel shading, sturdy architectural geometry, restrained atmospheric perspective, mythic but grounded tone, avoid photoreal 3D, avoid glossy game textures, avoid cute chibi proportions
```

## Guardrails

- 不添加未经批准的剧情反转、关系和 lore
- 不复刻在世公众人物的精确脸
- 不直接照搬受版权保护的命名角色设计
- 不用 `beautiful`、`cool`、`premium` 这类空词替代结构描述
- 除非有明确要求，默认压制：多余人物、文字、水印、logo、坏手、坏脸、背景脏乱、风格漂移

## Iteration Rules

当上游说：

- `保持脸不变，换成雨夜版本`
- `只改服装，其他不变`
- `更像电影定妆照，不要像海报`
- `换成棚拍纯背景`
- `改成 2D 风格`
- `加一个更明确的道具识别点`

就直接重写 prompt，不解释修改过程，除非对方明确问原因。
