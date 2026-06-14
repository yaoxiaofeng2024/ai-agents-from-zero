# 第十三章（通俗版）：SQL 生成前的"精筛"和"补全"

---

## 一、为什么合并后还要过滤？

上一章把三路召回结果整理成了 `table_infos` 和 `metric_infos`。但"整理好"不等于"足够精确"。

以"统计华北地区的销售总额"为例，合并后可能拿到：

| 召回结果 | 是否需要 |
|---------|---------|
| fact_order（订单事实表） | 需要 |
| dim_region（地区维度表） | 需要 |
| dim_date（日期维度表） | 不需要 |
| GMV（成交总额） | 需要 |
| AOV（客单价） | 不需要 |

**召回阶段宁可多保留候选，避免漏掉关键信息。过滤阶段负责把多余的删掉，减少噪声。**

> 打个比方：召回是"宁可多拿几本书"，过滤是"只留下真正用得上的那几本"。

---

## 二、三个节点的分工

| 节点 | 做什么 | 一句话 |
|------|--------|--------|
| `filter_table` | 从候选表中选出必要表和字段 | "查哪些表、用哪些字段" |
| `filter_metric` | 从候选指标中选出必要指标 | "算什么指标" |
| `add_extra_context` | 补充当前日期、数据库信息 | "补上模型不能凭空知道的信息" |

```text
过滤：删掉不需要的（filter_table、filter_metric）
补全：加上必须有的（add_extra_context）
```

---

## 三、为什么上下文要转成 YAML？

Python 里的 `table_infos` 是列表和字典，不能直接丢给大模型。要转成文本。

项目选 YAML 而不是 JSON：

| | JSON | YAML |
|--|------|------|
| 层级表达 | 靠花括号和方括号 | 靠缩进 |
| 中文显示 | 需要额外处理 | `allow_unicode=True` 直接显示 |
| 字段顺序 | 可能被字母排序打乱 | `sort_keys=False` 保留原始顺序 |

转成 YAML 后，模型看到的上下文长这样：

```yaml
- name: fact_order
  role: fact
  columns:
    - name: order_amount
      type: decimal
      role: measure
      description: 订单金额
```

**对人和模型都更友好。**

---

## 四、filter_table：让模型做选择题

### 核心思路

**不让模型重写完整表结构，只让它选"保留哪些表、哪些字段"。**

原因：完整 `table_infos` 层级很深，让模型原样重写容易出错。只返回选择结果，程序自己裁剪，更稳。

### 模型输出格式

```json
{
  "fact_order": ["order_amount", "region_id"],
  "dim_region": ["region_id", "region_name"]
}
```

含义：保留这两张表，每张表只保留列出的字段。

### 程序怎么裁剪？

```python
filtered_table_infos = []
for table_info in table_infos:
    if table_info["name"] in result:  # 表被选中
        table_info["columns"] = [
            col for col in table_info["columns"]
            if col["name"] in result[table_info["name"]]  # 字段被选中
        ]
        filtered_table_infos.append(table_info)
```

**模型负责判断，程序负责执行。**

---

## 五、filter_metric：同样的模式，更简单

指标没有"表→字段"的嵌套层级，所以更简单。

模型输出：

```json
["GMV"]
```

程序过滤：

```python
filtered_metric_infos = [
    m for m in metric_infos if m["name"] in result
]
```

**允许返回空数组**——如果当前问题不需要任何指标（比如"在职实习生有哪些？"），模型不应该硬选一个。

---

## 六、add_extra_context：补上模型不能凭空知道的信息

| 补什么 | 为什么 |
|--------|--------|
| 当前日期、星期、季度 | 用户说"今年""本季度"，模型需要知道"今天"是哪天 |
| 数据库方言和版本 | 不同数据库 SQL 语法不同，MySQL 8 和 MySQL 5 也有差异 |

这些信息不是从元数据知识库来的，而是从运行时环境获取的：

```python
# 当前日期
date_info = {
    "date": "2026-04-27",
    "weekday": "Monday",
    "quarter": "Q2"
}

# 数据库信息
db_info = {
    "dialect": "mysql",
    "version": "8.0.44"
}
```

---

## 七、整条链路回顾

```text
召回（宁可多）→ 合并（整理结构）→ 过滤（删掉不需要的）→ 补全（加上必须有的）→ 生成 SQL
```

**这一步不是让模型"知道更多"，而是让模型"少被无关信息打扰"。**

---

## 八、本章要点速记

| 要点 | 一句话 |
|------|--------|
| 过滤的目的 | 减少噪声，让 SQL 生成更准确 |
| filter_table | 模型选表和字段，程序负责裁剪 |
| filter_metric | 模型选指标，允许空数组 |
| add_extra_context | 补日期和数据库信息 |
| YAML | 比 JSON 更适合放进提示词 |
| 选择题模式 | 不让模型重写结构，只让它选保留什么 |
