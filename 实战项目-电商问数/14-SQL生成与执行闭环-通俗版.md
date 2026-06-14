# 第十四章（通俗版）：SQL 生成与执行——从"理解问题"到"查出结果"

---

## 一、这一章要做什么？

前面所有节点都在为 SQL 生成做准备。这一章要完成最后四个节点：

```text
generate_sql  → 生成 SQL
validate_sql  → 校验 SQL（用 EXPLAIN）
correct_sql   → 校正 SQL（根据错误信息修正）
run_sql       → 执行 SQL
```

**跑通这条链路后，问数智能体才真正从"理解问题"走到"查出结果"。**

---

## 二、SQL 生成前已经有什么？

| 上下文 | 告诉模型什么 |
|--------|------------|
| `query` | 用户到底问了什么 |
| `table_infos` | 有哪些表、字段、类型、描述、示例值 |
| `metric_infos` | 业务指标怎么算、依赖哪些字段 |
| `date_info` | 当前日期、星期、季度 |
| `db_info` | 数据库方言和版本 |

**模型不是凭空写 SQL，而是在整理好的约束范围内生成。**

---

## 三、generate_sql：生成候选 SQL

### 提示词的核心约束

- 只能使用上下文中提供的表和字段
- 只输出一条纯 SQL，不要解释、不要 Markdown 代码块
- 如果有指标，要按指标口径计算

### 为什么不能输出 Markdown 代码块？

大模型写代码时习惯性输出：

````markdown
```sql
select ...
```
````

但项目拿到 SQL 后要直接交给数据库执行。如果 SQL 里混了 ` ```sql `，数据库会报语法错误。

### 代码要点

```python
# 用 StrOutputParser（不是 JsonOutputParser），因为只需要一条 SQL 字符串
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

result = await chain.ainvoke({
    "table_infos": yaml.dump(table_infos, ...),
    "metric_infos": yaml.dump(metric_infos, ...),
    "date_info": yaml.dump(date_info, ...),
    "db_info": yaml.dump(db_info, ...),
    "query": query,
})

return {"sql": result}
```

---

## 四、validate_sql：用 EXPLAIN 校验

### 为什么不能直接执行？

大模型可能写错：表名拼错、字段名不存在、JOIN 条件不完整、SQL 方言不对……

**更稳的做法：先用 EXPLAIN 让数据库解析 SQL，确认没有语法和字段问题。**

```sql
EXPLAIN SELECT ...  -- 数据库只解析，不真正执行
```

- 解析成功 → SQL 没问题
- 解析失败 → 数据库会返回具体错误，比如 `Unknown column 'd.region_name1'`

### 代码要点

```python
try:
    await dw_mysql_repository.validate(sql)  # 内部执行 EXPLAIN
    return {"error": None}                   # 校验通过
except Exception as e:
    return {"error": str(e)}                 # 校验失败，记录错误
```

**注意：校验失败时不抛异常，而是把错误信息写入 State，交给条件边判断。**

---

## 五、条件分支：校验通过→执行，校验失败→校正

```text
generate_sql
  → validate_sql
      → error 为空 → run_sql → END
      → error 不为空 → correct_sql → run_sql → END
```

代码：

```python
graph_builder.add_conditional_edges(
    source="validate_sql",
    path=lambda state: "run_sql" if state["error"] is None else "correct_sql",
)
```

> 当前是简化版：校验一次 → 如果失败则校正一次 → 执行。生产级系统通常会加多轮重试和次数限制。

---

## 六、correct_sql：根据错误修正 SQL

### 和 generate_sql 的区别

| | generate_sql | correct_sql |
|--|-------------|-------------|
| 输入 | query + 上下文 | query + 上下文 + **错误 SQL + 错误信息** |
| 目标 | 从零生成 SQL | 在尽量保持业务语义不变的前提下修复错误 |

### 提示词的核心约束

- 必须基于错误信息修正，不能随意改
- 不得改变原始业务语义
- 不得新增/删除统计指标、维度、过滤条件
- 仍然只输出纯 SQL

### 为什么不只传错误信息？

错误信息只告诉模型"哪里错了"，但不知道"用户原来想查什么、有哪些表字段可用、指标口径是什么"。只传错误信息，模型可能修好了语法，却改丢了业务含义。

---

## 七、run_sql：执行最终 SQL

```python
async def run_sql(state, runtime):
    sql = state["sql"]  # 可能是 generate_sql 直接生成的，也可能是 correct_sql 修正后的
    result = await dw_mysql_repository.run(sql)
    logger.info(f"SQL执行结果：{result}")
```

这是工作流的最后一个节点。执行完成后，查询结果通过日志确认（后续 API 阶段会通过 SSE 返回前端）。

---

## 八、整条闭环回顾

```text
用户问题
  → 抽关键词 → 三路召回 → 合并 → 过滤 → 补全
  → 生成 SQL
  → EXPLAIN 校验
      → 通过 → 执行 → 结果
      → 失败 → 根据错误修正 → 执行 → 结果
```

**核心思想：不是一次生成就盲目执行，而是先校验；校验失败就把错误信息带回模型，让它基于真实错误修正。**

---

## 九、本章要点速记

| 要点 | 一句话 |
|------|--------|
| generate_sql | 在约束范围内生成纯 SQL，不要 Markdown 代码块 |
| validate_sql | 用 EXPLAIN 校验，不直接执行 |
| 条件分支 | 校验通过→执行，失败→校正 |
| correct_sql | 基于错误信息最小修复，不改业务语义 |
| run_sql | 执行最终 SQL，返回查询结果 |
| 闭环 | 生成 → 校验 → 校正 → 执行，不是盲写盲跑 |
