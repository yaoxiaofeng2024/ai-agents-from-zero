# 21 - Agent 智能体 · 面试题版

> 只保留实战项目会碰到、真实面试会被问的知识点。其余一律不收。

---

## Q1：Agent 到底是什么？一句话怎么说？

**Agent = 模型 + 工具集 + 运行循环 + 状态。**

它不是某个模型，也不是某个工具，而是一种**围绕目标持续做决策并调用能力**的运行方式。

核心区别：普通 LLM 调用是"问一次答一次"；Agent 是"问一次，模型自己判断要不要调工具、调几次、什么时候停"。

---

## Q2：Agent 和 Tool 的关系是什么？面试怎么答？

| 对象 | 定位 | 一句话 |
|------|------|--------|
| **Tool** | 能力层 | 我能做什么 |
| **Agent** | 决策层 | 我什么时候、按什么顺序去用这些能力 |

**面试关键句：** Tool 是被动的能力封装，Agent 是主动的决策者。有 Tool 不等于有 Agent——"查北京天气"一步就能完成，不需要 Agent；但"找最热无线耳机、查库存、告诉你哪款能买"需要多步决策，这时 Agent 才有价值。

---

## Q3：什么时候用 Agent，什么时候用链/工作流？

**这是最高频的实战判断题。**

| 场景 | 用什么 |
|------|--------|
| 步骤固定、顺序可提前写死 | 链 / 工作流 |
| 下一步怎么做要模型根据中间结果动态决定 | Agent |

实战口诀：**路径确定用链，路径不确定用 Agent。**

常见误区：不是所有问题都需要 Agent。如果 A→B→C 的顺序是固定的，用 LCEL 或 LangGraph Workflow 更稳更快。

---

## Q4：ReAct 是什么？Agent 的循环机制怎么工作？

**ReAct就是“边想边做”的循环。**
每一轮，模型先输出**思考**（Thought），再输出**行动**（Action）去调工具，工具返回的结果作为**观察**（Observation）喂回来。
模型看到观察后，再进入下一轮思考：是继续调工具，还是直接给答案。
在代码里，这就是一个**Agent节点 → 条件边**的图：条件边不是写死的，而是**看模型输出里有没有工具调用** ——有就执行工具再回来，没有就结束。
整个过程，**走哪条路、走多少步，全由模型自己决定**。这就是Agent的循环机制，也是它和工作流最本质的区别。



---

## Q5：AgentExecutor 和 create_agent 有什么区别？

| 维度 | V0.3 classic | V1.x `create_agent` |
|------|-------------|-------------------|
| 入口 | `create_tool_calling_agent` + `AgentExecutor` | `create_agent` |
| 谁驱动循环 | AgentExecutor 显式驱动 | LangGraph graph runtime 驱动 |
| 代码量 | 多，手动拼 Prompt + Executor | 少，统一入口 |
| 学习价值 | 看清内部怎么转 | 新项目怎么写 |

**面试怎么答：** Agent 只负责"出主意"，V0.3 里 AgentExecutor 负责驱动循环、执行工具、回写结果；V1.x 把这些封装进 graph-based runtime，看起来一步创建，底层仍然在循环。

---

## Q6：agent_scratchpad 是什么？为什么必须有？

它是 Agent 的"草稿区"，用来承接：上一轮模型决定调什么工具、工具返回了什么、下一轮模型基于这些继续推理。

**没有 scratchpad，模型就不知道自己刚刚做过什么，多步循环无法成立。**

在 V0.3 中显式出现在 Prompt 里：`("placeholder", "{agent_scratchpad}")`；V1.x 被封装了，但底层机制一样。

---

## Q7：create_agent 的关键参数有哪些？实战怎么选？

| 参数 | 什么时候用 |
|------|-----------|
| `model` | 必传，选哪个模型做推理 |
| `tools` | 需要外部能力时传 |
| `system_prompt` | 需要约束角色/风格/规则时传 |
| `response_format` | 需要结构化输出（JSON/Pydantic）时传 |
| `checkpointer` | 需要多轮对话状态持久化时传 |
| `middleware` | 需要工具调用守护/人工审核/日志时传 |

**面试重点：** 前四个入门必知；`checkpointer` + `thread_id` 解决短期记忆；`middleware` 解决运行边界和安全控制。

---

## Q8：checkpointer 和 thread_id 解决什么问题？

- **checkpointer**：状态保存器，把 Agent 运行状态存下来
- **thread_id**：会话标识，区分不同对话线程
- **短期记忆**：同一 thread_id 下，多轮消息和状态能延续

```python
config = {"configurable": {"thread_id": "user-001"}}
```

**实战意义：** 没有 checkpointer，Agent 是无状态的，每次调用都是全新的；加上后，Agent 能"记住"之前的对话。

---

## Q9：response_format 解决什么问题？

Agent 不只能返回自然语言，还能返回结构化结果（JSON、TypedDict、Pydantic 对象）。

**这不是后处理把字符串转 JSON，而是在输出阶段就把"结果长什么样"约束清楚。**

实战价值：后端业务逻辑可以直接消费结构化字段，不用再解析自然语言。

---

## Q10：Agent 为什么必须设迭代上限、超时和失败处理？

**这是生产级 Agent 的必备常识。**

Agent 会根据中间结果继续决策，没有边界可能导致：
- 死循环调用工具，成本失控
- 执行危险动作无兜底
- 超时无响应，用户体验崩溃

工程上必须有：停止条件、错误兜底、日志追踪。

---

## Q11：middleware 是什么？为什么生产 Agent 必须要？

middleware 在模型调用、工具调用、状态更新等阶段插入控制逻辑，**给 Agent 加运行边界**。

常见用途：
- **工具调用守护**：高风险操作前检查权限
- **人类审核（Human-in-the-loop）**：删除、支付等动作不让 Agent 静默执行
- **动态提示词**：根据租户/权限调整 system prompt
- **日志监控**：记录关键决策和异常

**面试关键句：** 生产级 Agent 的重点不是工具越多越好，而是能力越强边界越要清楚。

---

## Q12：Tool、Function Calling、RAG、MCP、Agent 的关系？

| 概念 | 解决什么 | 一句话 |
|------|---------|--------|
| **Tool** | 系统有哪些可调用能力 | 能力层 |
| **Function Calling** | 模型怎么把"调工具"表达出来 | 调用机制 |
| **RAG** | 模型缺知识时怎么拿上下文 | 上下文增强 |
| **MCP** | 工具/资源怎么标准化接入 | 连接协议 |
| **Agent** | 什么时候用什么能力、按什么顺序做 | 决策与编排层 |

真实项目链路：用户提目标 → Agent 判断 → 缺知识走 RAG → 缺能力通过 Function Calling 调 Tool → Tool 可能来自 MCP → Agent 继续判断 → 直到完成。

---

## Q13：A2A（多智能体协作）的核心思想是什么？

**分工 + 协调。**

不是一个 Agent 解决所有问题，而是：
- 每个子 Agent 单一职责（机票 Agent、酒店 Agent、打车 Agent）
- 一个总协调逻辑负责调度
- 各自有边界，最后汇总结果

**面试怎么答：** LangChain 官方常见做法是把 subagent 包装成 tool 再交给主 Agent 调用。关键是"分工+协调"，不是 API 形式。

---

## Q14：Agent + MCP 的实战意义？

前面案例的工具都是本地 `@tool`，而 MCP 让工具来源可以被**标准化外置**。

链路：读取 `mcp.json` → `MultiServerMCPClient` 连接 MCP 服务 → 获取工具列表 → 交给 Agent 使用。

**实战意义：** 后端团队封装 MCP 服务，Agent 侧只负责接入，一个工具集可被多个 AI 应用复用。

---

## Q15：stream() 和 LangSmith 分别解决什么问题？

- **stream()**：代码层面实时看 Agent 中间进展（调了什么工具、卡在哪步）
- **LangSmith**：可视化层面追踪 Agent 运行过程（为什么选了这个工具、为什么多调了一轮、哪步耗时最长）

**面试怎么答：** `invoke()` 等最终结果，`stream()` 看过程；`stream()` 是代码级可观测，LangSmith 是平台级可观测。生产 Agent 两者都需要。

---

## 速记清单

1. Agent = 模型 + 工具 + 循环 + 状态，核心是**决策层**
2. Tool 是能力，Agent 是决策——有 Tool 不等于需要 Agent
3. 路径确定用链，路径不确定用 Agent
4. ReAct = Reason + Act，是工作机制不只是 Prompt 模板
5. agent_scratchpad 是多步循环的草稿区，没有它循环断
6. V0.3 手动拼 Executor，V1.x create_agent 封装 graph runtime
7. checkpointer + thread_id 解决短期记忆和会话隔离
8. response_format 约束输出结构，不是后处理
9. middleware 加运行边界，生产 Agent 必备
10. 迭代上限、超时、失败处理是工程底线
11. Tool/FC/RAG/MCP/Agent = 能力/机制/增强/协议/决策
12. A2A 核心是分工+协调
13. MCP 让工具来源标准化外置
14. stream() 看过程，LangSmith 做可观测
