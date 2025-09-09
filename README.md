# MeiliSearch MCP Server

这是一个用于查询MeiliSearch的MCP服务器实现，支持关键词搜索和多种筛选条件。

## 功能特性

- 关键词搜索
- 多种筛选条件支持：
  - 等值筛选
  - 范围筛选 (gt, gte, lt, lte, ne)
  - IN筛选 (数组值)
- 排序功能
- 字段筛选
- 分页支持
- 错误处理
- 索引统计信息查询
- 索引列表查询

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

## 数据字段说明

根据你提供的数据，索引中的文档包含以下字段：

- `id`: 唯一标识符
- `title`: 标题
- `description`: 描述信息
- `type`: 类型
- `category`: 分类
- `productName`: 产品名称
- `quantity`: 数量
- `unit`: 单位
- `price`: 价格
- `currency`: 货币单位
- `contactName`: 联系人姓名
- `contactPhone`: 联系电话
- `createdAt`: 创建时间
- `updatedAt`: 更新时间
- `expiresAt`: 过期时间
- `companyName`: 公司名称
- `areaName`: 地区名称

## 可用工具函数

### 1. search_meilisearch

执行MeiliSearch查询。

**参数：**
- `query` (str): 搜索关键词
- `index_name` (str): 索引名称
- `filter_conditions` (dict, 可选): 筛选条件
- `limit` (int, 默认20): 返回结果数量限制
- `offset` (int, 默认0): 偏移量
- `attributes_to_retrieve` (list, 可选): 指定要返回的字段列表
- `sort` (list, 可选): 排序规则列表

**示例用法：**

```python
# 基本关键词搜索
search_meilisearch("瓦楞纸箱", "products")

# 带筛选条件的搜索
search_meilisearch(
    "瓦楞纸箱", 
    "products", 
    filter_conditions={
        "category": "瓦楞纸箱",
        "quantity": {"gte": 1000},
        "areaName": "天元区"
    }
)

# 带排序和字段筛选的搜索
search_meilisearch(
    "纸箱",
    "products",
    filter_conditions={
        "category": ["瓦楞纸箱", "包装盒"],
        "quantity": {"gte": 500}
    },
    sort=["createdAt:desc"],
    attributes_to_retrieve=["title", "productName", "quantity", "price", "areaName", "companyName", "contactName", "contactPhone"],
    limit=10
)

# 搜索特定价格范围的产品
search_meilisearch(
    "瓦楞纸箱",
    "products",
    filter_conditions={
        "category": "瓦楞纸箱",
        "price": {"gte": 10, "lte": 100}
    },
    sort=["price:asc"],
    limit=5
)
```

### 2. get_index_stats

获取指定索引的统计信息。

**参数：**
- `index_name` (str): 索引名称

**示例用法：**
```python
get_index_stats("products")
```

### 3. get_all_indexes

获取所有索引的列表。

**示例用法：**
```python
get_all_indexes()
```

## 筛选条件语法

筛选条件通过 `filter_conditions` 参数传递，支持以下格式：

1. **等值筛选**：
   ```python
   {"category": "瓦楞纸箱"}
   ```

2. **范围筛选**：
   ```python
   {"quantity": {"gte": 1000}}  # 大于等于1000
   {"price": {"lt": 100}}       # 小于100
   {"quantity": {"gt": 500, "lt": 2000}}  # 大于500且小于2000
   ```

3. **IN筛选**（数组值）：
   ```python
   {"category": ["瓦楞纸箱", "包装盒"]}
   ```

4. **不等筛选**：
   ```python
   {"category": {"ne": "废弃物品"}}
   ```

## 排序语法

排序通过 `sort` 参数传递，支持以下格式：

```python
["createdAt:desc"]     # 按创建时间降序排列
["price:asc"]          # 按价格升序排列
["quantity:desc", "price:asc"]  # 多字段排序
```

## 配置

所有配置都通过环境变量进行管理，可以在 `.env` 文件中修改：

- `MEILISEARCH_URL`: MeiliSearch服务器地址
- `MEILISEARCH_MASTER_KEY`: MeiliSearch主密钥
- `SERVER_HOST`: 服务器监听主机地址
- `SERVER_PORT`: 服务器监听端口