# 第十五章（通俗版）：API 接口基础——让能力可以被调用

---

## 一、为什么需要 API？

到第 14 章为止，问数智能体只能在命令行里跑。真正交付给前端或其他系统时，需要把它封装成 HTTP API。

**目标：前端发一个 POST 请求，后端流式返回执行进度和最终结果。**

---

## 二、先搭一个最小 FastAPI 接口

### FastAPI 是什么？

一个 Python Web 框架，负责把 Python 函数暴露成 HTTP 接口。

最小示例：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

| 代码 | 含义 |
|------|------|
| `app = FastAPI()` | 创建应用 |
| `@app.get("/health")` | 声明一个 GET 接口 |
| `return {"status": "ok"}` | 返回字典，自动转成 JSON |

### 项目里的文件分工

| 文件 | 职责 |
|------|------|
| `main.py` | 创建 FastAPI 应用，挂载路由 |
| `query_router.py` | 定义 `/api/query` 接口 |
| `query_schema.py` | 定义请求体结构 |

### 请求体定义

```python
class QuerySchema(BaseModel):
    query: str  # 用户输入的自然语言问题
```

前端发送 `{"query": "统计华北地区的销售总额"}`，后端通过 `query.query` 取出。

---

## 三、为什么查询接口要用流式响应？

普通接口：**等所有逻辑执行完，一次性返回。** 用户只能看到页面一直转圈。

流式接口：**边执行边返回。** 用户能实时看到每一步在做什么。

```text
普通接口：等 10 秒 → 一次性返回结果
流式接口：每秒返回一步 → "抽取关键词" → "召回字段" → "生成SQL" → "结果"
```

> 打个比方：普通接口像"等快递到了才能拆"，流式接口像"边打包边告诉你进度"。

---

## 四、SSE 协议：前后端约定的流式格式

### SSE vs WebSocket

| 方案 | 特点 | 适合场景 |
|------|------|---------|
| WebSocket | 双向通信 | 聊天、在线协作 |
| SSE | 服务端单向推送 | 任务进度、日志流 |

本项目前端只提交一次问题，后续主要是接收服务端推送，所以 SSE 更合适。

### SSE 消息格式

最简格式：

```text
data: 这里是内容

```

注意：一条消息后面要有**两个换行符**（`\n\n`）。

Python 里写：

```python
yield "data: step:0\n\n"
```

发 JSON：

```python
yield f'data: {json.dumps({"type": "progress", "step": "抽取关键词"})}\n\n'
```

### 两层协议

```text
外层：SSE 传输格式 → data: ...\n\n
内层：项目业务协议 → {"type": "progress", "step": "抽取关键词"}
```

**SSE 是传输格式，JSON 是业务内容，别混在一起。**

---

## 五、FastAPI 三件套

| 能力 | 解决什么问题 | 项目里怎么用 |
|------|------------|------------|
| **lifespan** | 应用启动/关闭时管理资源 | 初始化 Qdrant、ES、MySQL 客户端 |
| **middleware** | 每个请求前后统一执行逻辑 | 生成 request_id |
| **Depends** | 路由函数依赖的对象怎么创建 | 组装 QueryService |

### lifespan：应用级资源

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 前：应用启动时，初始化客户端
    init_clients()
    yield  # 应用运行中
    # yield 后：应用关闭前，释放连接
    await close_clients()
```

### middleware：请求级统一逻辑

```python
@app.middleware("http")
async def add_request_id(request, call_next):
    # call_next 前：生成 request_id
    response = await call_next(request)
    # call_next 后：补充响应头等
    return response
```

### Depends：声明"我需要什么"

```python
@query_router.post("/api/query")
async def query_handler(
    query: QuerySchema,
    query_service: Annotated[QueryService, Depends(get_query_service)],
):
    ...
```

路由只声明"我需要 QueryService"，怎么创建交给 `get_query_service()`。

---

## 六、子依赖和带 yield 的依赖

### 子依赖

依赖可以嵌套：

```text
get_query_service
  → get_meta_mysql_repository
      → get_meta_session
  → get_embedding_client
  → ...
```

FastAPI 自动解析依赖树，同一请求内共用子依赖会缓存。

### 带 yield 的依赖

数据库 Session 是请求级资源，用 `yield` 管理：

```python
async def get_meta_session():
    async with session_factory() as session:
        yield session  # 请求期间使用
    # 请求结束后自动关闭
```

| | lifespan | 带 yield 的依赖 |
|--|---------|----------------|
| 生命周期 | 整个应用 | 单次请求 |
| 典型资源 | 客户端、连接池 | 数据库 Session |

---

## 七、本章要点速记

| 要点 | 一句话 |
|------|--------|
| 流式响应 | 边执行边返回，不让用户干等 |
| SSE | 服务端单向推送，格式是 `data: ...\n\n` |
| 两层协议 | SSE 管传输，JSON 管业务 |
| lifespan | 应用级资源的初始化和释放 |
| middleware | 所有请求都经过的统一逻辑 |
| Depends | 路由只声明需要什么，创建交给依赖函数 |
| 带 yield 的依赖 | 管理请求级资源（如 Session） |
