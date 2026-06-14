# 第六章（通俗版）：MySQL、Embedding 和日志——三个基础能力

---

## 一、这一章解决什么问题？

上一章接入了 Qdrant 和 ES，但还有两个问题没闭环：

1. **Qdrant 里的向量从哪来？** → 需要 Embedding 服务
2. **结构化数据和运行日志怎么管？** → 需要 MySQL 和日志系统

```text
文本 → Embedding 服务 → 向量 → Qdrant 检索
结构化数据 → MySQL
运行过程 → 日志（Loguru + request_id）
```

---

## 二、Embedding：把文字变成数字

### 2.1 什么是 Embedding？

**一句话：把一段文字变成一组数字（向量），意思相近的文字，数字也相近。**

比如：
- "销售额" → `[0.12, -0.08, 0.44, ...]`
- "订单金额" → `[0.11, -0.07, 0.43, ...]`（和上面很接近！）
- "客户姓名" → `[0.85, 0.32, -0.19, ...]`（和上面差很远）

这样 Qdrant 就能通过比较数字的接近程度，找到语义相似的字段。

### 2.2 项目怎么做的？

项目不是在代码里直接加载模型，而是用 **TEI（Text Embeddings Inference）** 把模型部署成一个 HTTP 服务：

```text
BAAI/bge-large-zh-v1.5（模型）
  → TEI（部署服务）
  → EmbeddingClientManager（项目封装）
  → 字段召回 / 指标召回
```

**好处：代码只管"调用服务"，不用管"加载模型"。**

### 2.3 客户端封装

`EmbeddingClientManager` 做的事很简单：

| 方法 | 做什么 |
|------|--------|
| `_get_url()` | 根据 host + port 拼出服务地址 |
| `init()` | 创建 HuggingFaceEndpointEmbeddings 客户端 |
| 没有 close() | 因为是无状态 HTTP 调用，不需要显式关闭 |

---

## 三、MySQL：两套数据库，两种职责

### 3.1 为什么是两套 MySQL？

| 配置项 | 连到哪里 | 做什么 |
|--------|---------|--------|
| `db_meta` | 元数据库 | "系统知道库里有什么" |
| `db_dw` | 数仓模拟库 | "系统最终去查什么" |

> 一个管"知识"，一个管"数据"。

### 3.2 SQLAlchemy 三件套

项目用 SQLAlchemy 访问 MySQL，先搞懂三个概念：

| 概念 | 通俗理解 | 类比 |
|------|---------|------|
| **ORM** | 把数据库表映射成 Python 类 | 翻译官：你操作对象，它帮你生成 SQL |
| **Engine** | 数据库连接的总入口 | 连接池：管理一组可复用的连接 |
| **Session** | 一次数据库操作的工作窗口 | 工作台：这次查询/写入都在这里完成 |

### 3.3 客户端封装

`MySQLClientManager` 的核心：

```python
class MySQLClientManager:
    def init(self):
        # 创建 Engine（连接池）
        self.engine = create_async_engine(url, pool_size=10)
        # 创建 Session 工厂
        self.session_factory = async_sessionmaker(self.engine)
```

项目创建了两个实例：

```python
meta_mysql_client_manager = MySQLClientManager(app_config.db_meta)  # 元数据库
dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)      # 数仓库
```

### 3.4 异步驱动

项目用 `asyncmy` 作为 MySQL 的异步驱动。SQLAlchemy 负责抽象层，asyncmy 负责底层通信。

连接地址格式：`mysql+asyncmy://user:password@host:port/database`

---

## 四、日志：让你知道系统跑到哪了

项目用 **Loguru** 做日志管理，配置写在 `app_config.yaml` 里：

```yaml
logging:
  file:
    enable: true
    level: INFO
    path: logs
    rotation: "10 MB"      # 日志文件超过 10MB 就轮转
    retention: "7 days"     # 只保留最近 7 天的日志
  console:
    enable: true
    level: INFO
```

### 日志能帮你做什么？

- **调试**：看每一步执行了什么
- **排障**：出错时追查是哪一步出了问题
- **观察**：了解系统运行状态

---

## 五、三类能力的协作关系

```text
Embedding：文本 → 向量（给 Qdrant 用）
MySQL：存结构化数据（元数据 + 数仓）
日志：记录运行过程（调试 + 排障）
```

**只有这三部分都接起来，后面的知识库构建、混合召回、SQL 生成才会形成闭环。**

---

## 六、本章要点速记

| 要点 | 一句话 |
|------|--------|
| Embedding | 把文字变成数字，意思相近的数字也相近 |
| TEI | 把 Embedding 模型部署成 HTTP 服务 |
| 两套 MySQL | 元数据库管"知识"，数仓库管"数据" |
| SQLAlchemy | ORM 翻译官 + Engine 连接池 + Session 工作台 |
| Loguru | 日志管理，支持文件轮转和保留策略 |
| 异步 | 项目全面使用异步（asyncmy、AsyncQdrantClient 等） |
