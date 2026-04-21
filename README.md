# ToonPrompt

Open-source Codex skills for story, prompt, and media development workflows.

This repository currently includes `screenplay-development`, a screenwriting skill that turns sparks, one-sentence stories, premises, and rough drafts into sharper, more producible scripts.

## 中文简介

`ToonPrompt` 目前开源的是一个可直接放进 Codex 的剧作 skill：`screenplay-development`。

它不是单纯的“剧本生成器”，而是一个更接近编剧室开发流程的工作流：

- 先把灵感打磨成可卖、可讲、可继续开发的“一句话故事”
- 再用 `Save the Cat / 救猫咪` 做结构压力测试
- 然后才往角色、beat、scene list、treatment、screenplay 逐层展开

这个 skill 适合处理四类输入：

- `spark`：一个词、一种情绪、一张画面、一个设定
- `premise`：一句话故事、logline、简短梗概
- `draft`：大纲、分场、对白页、初稿
- `industrialize`：希望把故事做得更可拍、更可卖、更适合系列化

## 当前收录

- `skills/screenplay-development/`
  - 以一句话故事为前置闸门
  - 内置 `Save the Cat` 节拍和 logline 工作法
  - 支持短片、长片、剧集、微短剧的开发
  - 可用于前期立项、剧本医生、商业化重构

## 安装方式

将本仓库里的 skill 目录复制到本地 Codex skills 目录，例如：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/screenplay-development "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装后，直接在 Codex 中调用：

```text
Use $screenplay-development 把这个灵感先打磨成 3 条一句话故事，等我选中再继续扩写。
```

## 目录结构

```text
skills/
  screenplay-development/
    SKILL.md
    agents/
      openai.yaml
    references/
      commercial-evaluation.md
      development-frameworks.md
      logline-and-save-the-cat.md
```

## License

MIT
