# MeiliSearch MCP Server

这是一个用于查询MeiliSearch的MCP服务器实现。

## 安装依赖

```bash
pip install -e .
```

## 环境变量配置

项目使用 `.env` 文件来配置环境变量。请根据需要修改 `.env` 文件中的配置：

```env
# MeiliSearch配置
MEILISEARCH_URL=http://localhost:7700
MEILISEARCH_MASTER_KEY=your_master_key_here

# 服务器配置
SERVER_HOST=127.0.0.1
SERVER_PORT=8800
```

## 启动服务器

### 使用HTTP连接方式（推荐）

直接运行Python文件（使用代码中配置的HTTP方式）：
```bash
python server.py
```

或者使用FastMCP CLI并指定传输方式：
```bash
fastmcp run server.py --transport http --port 8800
```

服务器将根据环境变量配置在指定的主机和端口上运行。

### 使用SSE连接方式

```bash
fastmcp run server.py --transport sse --port 8800
```

### 使用STDIO方式

```bash
fastmcp run server.py
```

## 配置

所有配置都通过环境变量进行管理，可以在 `.env` 文件中修改：

- `MEILISEARCH_URL`: MeiliSearch服务器地址
- `MEILISEARCH_MASTER_KEY`: MeiliSearch主密钥
- `SERVER_HOST`: 服务器监听主机地址
- `SERVER_PORT`: 服务器监听端口