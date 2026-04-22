# ToonPrompt

Version: `0.2.0`

Open-source Codex skills for screenplay development, character prompt design, and producer-led video agent orchestration.

This repository now includes:

- `screenplay-development` for story development
- `character-prompt-engine` for prompt-only character design and key art generation
- `video-agent-orchestration` for turning a brief or existing script into a producer-led video production packet

## 中文简介

`ToonPrompt` 目前开源了三个可直接放进 Codex 的技能：

- `screenplay-development`：把灵感、梗概和草稿打磨成更可拍、更可卖的剧本
- `character-prompt-engine`：把角色设定、服化道、镜头与气质需求压缩成可直接出图的人设/定妆照提示词
- `video-agent-orchestration`：把 brief、现成剧本或改编任务，组织成制片驱动的视频 agent 流程，并整理出可交给生产层的 production packet

其中，`screenplay-development` 不是单纯的“剧本生成器”，而是一个更接近编剧室开发流程的工作流：

- 先把灵感打磨成可卖、可讲、可继续开发的“一句话故事”
- 再用 `Save the Cat / 救猫咪` 做结构压力测试
- 然后才往角色、beat、scene list、treatment、screenplay 逐层展开

这个 skill 适合处理四类输入：

- `spark`：一个词、一种情绪、一张画面、一个设定
- `premise`：一句话故事、logline、简短梗概
- `draft`：大纲、分场、对白页、初稿
- `industrialize`：希望把故事做得更可拍、更可卖、更适合系列化

`character-prompt-engine` 则更像一个“角色设计师 + 提示词编译器”：

- 默认只输出提示词本身，不写说明文档
- 适合角色定妆照、人设图、服装变化版、同角色多镜头一致性出图
- 强调脸型、发型、轮廓、服装结构、材质、色彩和道具锚点的稳定性

`video-agent-orchestration` 则负责把前两个 skill 串成真实的视频生产链：

- 制片先冻结 brief
- 编剧阶段调用 `screenplay-development`
- 美术阶段调用 `character-prompt-engine`
- 副导演产出 `storyboard.md` 和 `ad_feedback.md`
- 制片整合成 `schedule.md`、`production_todo.md`、`production_packet.md`

## 当前收录

- `skills/screenplay-development/`
  - 以一句话故事为前置闸门
  - 内置 `Save the Cat` 节拍和 logline 工作法
  - 支持短片、长片、剧集、微短剧的开发
  - 可用于前期立项、剧本医生、商业化重构
- `skills/character-prompt-engine/`
  - 面向角色设定、人设图、定妆照和视觉变体
  - 默认输出可直接复制到图像模型的 prompt
  - 支持 2D、写实、海报感、棚拍纯背景等常见模式
  - 适合和剧作 skill 串联使用，先做故事，再锁角色视觉
- `skills/video-agent-orchestration/`
  - 面向制片驱动的视频 agent 工作流
  - 产出 `brief`、`story package`、`art package`、`storyboard`、`AD feedback`、`schedule`、`production todo`、`production packet`
  - 适合改编已有剧本、民间传说、IP 设定和短片策划
  - 默认把 `screenplay-development` 和 `character-prompt-engine` 融入编剧与美术阶段

## 安装方式

将本仓库里的 skill 目录复制到本地 Codex skills 目录，例如：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/screenplay-development "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/character-prompt-engine "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/video-agent-orchestration "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装后，直接在 Codex 中调用：

```text
Use $screenplay-development 把这个灵感先打磨成 3 条一句话故事，等我选中再继续扩写。
```

```text
Use $character-prompt-engine 把这个角色设定整理成一条可直接出图的人设提示词，只输出提示词本身。
```

```text
Use $video-agent-orchestration 把这个剧本改编成 2D 动画前期生产包，并在编剧阶段调用 $screenplay-development、在美术阶段调用 $character-prompt-engine。
```

## OpenClaw 拉取

仓库拉取链接：

```text
https://github.com/Wei-zuo/ToonPrompt.git
```

如果你使用 OpenClaw，可以把这两个 skill 拉到共享 skills 目录：

```bash
git clone https://github.com/Wei-zuo/ToonPrompt.git
mkdir -p ~/.openclaw/skills
cp -R ToonPrompt/skills/character-prompt-engine ~/.openclaw/skills/
cp -R ToonPrompt/skills/screenplay-development ~/.openclaw/skills/
cp -R ToonPrompt/skills/video-agent-orchestration ~/.openclaw/skills/
```

如果你只想装到当前 workspace：

```bash
git clone https://github.com/Wei-zuo/ToonPrompt.git
mkdir -p ./skills
cp -R ToonPrompt/skills/character-prompt-engine ./skills/
cp -R ToonPrompt/skills/screenplay-development ./skills/
cp -R ToonPrompt/skills/video-agent-orchestration ./skills/
```

重开一个新的 OpenClaw session 后，skill 就会被加载。

## 目录结构

```text
skills/
  character-prompt-engine/
    SKILL.md
    agents/
      openai.yaml
  screenplay-development/
    SKILL.md
    agents/
      openai.yaml
    references/
      commercial-evaluation.md
      development-frameworks.md
      logline-and-save-the-cat.md
  video-agent-orchestration/
    SKILL.md
    agents/
      openai.yaml
    references/
      handoff-rules.md
      pipeline-files.md
examples/
  zhaozhouqiao-2d-adaptation/
    README.md
    art-tests/
      luban-test.png
      zhangguolao-test.png
      chaiwangye-test.png
      bridge-test.png
```

## 示例案例

仓库现在附带一个完整案例：

- `examples/zhaozhouqiao-2d-adaptation/`

这个案例展示了如何把《赵州桥·八仙试桥》从已有剧本改编成 `2D 国风动画` 的前期生产包，并附上 4 张测试美术图，方便对照 `art_package.md` 和后续 production packet。

## License

MIT
