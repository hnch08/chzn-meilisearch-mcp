from fastmcp import FastMCP
import meilisearch
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Create a server instance
mcp = FastMCP(name="MyAssistantServer")


@mcp.tool
def search_meilisearch(
    query: str,
    index_name: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0,
    attributes_to_retrieve: Optional[List[str]] = None,
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    查询MeiliSearch索引

    Args:
        query: 搜索关键词
        index_name: 索引名称
        filter_conditions: 筛选条件字典，可选
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        attributes_to_retrieve: 指定要返回的字段列表，可选
        sort: 排序规则列表，可选

    Returns:
        搜索结果字典

    示例:
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
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 创建MeiliSearch客户端
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)

        # 获取索引
        index = client.index(index_name)

        # 构建搜索参数
        search_params = {
            'q': query,
            'limit': limit,
            'offset': offset
        }

        # 添加可选参数
        if attributes_to_retrieve:
            search_params['attributesToRetrieve'] = attributes_to_retrieve

        if sort:
            search_params['sort'] = sort

        # 处理筛选条件
        if filter_conditions:
            filter_expressions = _build_filter_expressions(filter_conditions)
            if filter_expressions:
                search_params['filter'] = filter_expressions

        # 执行搜索
        results = index.search(**search_params)

        return {
            "success": True,
            "hits": results["hits"],
            "estimated_total_hits": results["estimatedTotalHits"],
            "limit": results["limit"],
            "offset": results["offset"],
            "processing_time_ms": results["processingTimeMs"]
        }

    except meilisearch.errors.MeiliSearchApiError as e:
        return {
            "success": False,
            "error": f"MeiliSearch API错误: {str(e)}",
            "error_code": e.code
        }
    except meilisearch.errors.MeiliSearchCommunicationError as e:
        return {
            "success": False,
            "error": f"MeiliSearch连接错误: {str(e)}",
            "error_type": "communication_error"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}",
            "error_type": "unknown_error"
        }


def _build_filter_expressions(filter_conditions: Dict[str, Any]) -> List[str]:
    """
    构建MeiliSearch筛选表达式

    Args:
        filter_conditions: 筛选条件字典

    Returns:
        筛选表达式列表
    """
    filter_expressions = []

    for key, value in filter_conditions.items():
        if value is None:
            continue

        if isinstance(value, list):
            # 处理数组值的情况 (IN查询)
            if len(value) > 0:
                # 转义特殊字符并构建表达式
                escaped_values = [_escape_filter_value(v) for v in value]
                values_str = ", ".join(escaped_values)
                filter_expressions.append(f"{key} IN [{values_str}]")
        elif isinstance(value, dict):
            # 处理范围查询和其他复杂条件
            for op, val in value.items():
                if op == "gt":
                    filter_expressions.append(
                        f"{key} > {_escape_filter_value(val)}")
                elif op == "gte":
                    filter_expressions.append(
                        f"{key} >= {_escape_filter_value(val)}")
                elif op == "lt":
                    filter_expressions.append(
                        f"{key} < {_escape_filter_value(val)}")
                elif op == "lte":
                    filter_expressions.append(
                        f"{key} <= {_escape_filter_value(val)}")
                elif op == "ne":
                    filter_expressions.append(
                        f"{key} != {_escape_filter_value(val)}")
        else:
            # 处理单个值的情况
            filter_expressions.append(f"{key} = {_escape_filter_value(value)}")

    return filter_expressions


def _escape_filter_value(value: Any) -> str:
    """
    转义筛选值中的特殊字符

    Args:
        value: 要转义的值

    Returns:
        转义后的字符串
    """
    if isinstance(value, str):
        # 转义单引号并用单引号包围字符串
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


@mcp.tool
def get_index_stats(index_name: str) -> Dict[str, Any]:
    """
    获取MeiliSearch索引统计信息

    Args:
        index_name: 索引名称

    Returns:
        索引统计信息
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)
        index = client.index(index_name)
        stats = index.get_stats()

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取索引统计信息失败: {str(e)}"
        }


@mcp.tool
def get_all_indexes() -> Dict[str, Any]:
    """
    获取所有MeiliSearch索引列表

    Returns:
        索引列表
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)
        indexes = client.get_indexes()

        # 提取索引名称
        index_names = [index.uid for index in indexes['results']
                       ] if 'results' in indexes else []

        return {
            "success": True,
            "indexes": index_names
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取索引列表失败: {str(e)}"
        }


if __name__ == "__main__":
    # 从环境变量获取服务器配置
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8800"))

    # 使用HTTP连接方式运行服务器
    mcp.run(transport="http", host=host, port=port)
