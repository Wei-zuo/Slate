# Slate Runtime

这层不是给人手动切 skill 用的，而是给程序执行的。

目标：

- 把 `制片 -> 编剧 -> 美术设计 -> 副导演 -> 生产` 变成真实状态图
- 把每阶段输出约束成 Pydantic 模型
- 把审核打回变成可计算的回退路由

建议入口：

- 先看 `../docs/agent-runtime-architecture.md`
- 再看 `video_agents/graph.py`

## 目录

- `video_agents/schemas.py`：结构化输出模型
- `video_agents/state.py`：状态、阶段、revision 预算
- `video_agents/services.py`：节点服务接口
- `video_agents/graph.py`：LangGraph 编排图
- `video_agents/export_schemas.py`：导出 JSON Schema
