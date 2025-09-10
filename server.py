from fastmcp import FastMCP
from meilisearch import Client, errors
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Create a server instance
mcp = FastMCP(name="MyAssistantServer")


@mcp.tool
def search_supply_demands(
    query: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0,
    attributes_to_retrieve: Optional[List[str]] = None,
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    查询MeiliSearch中的supply_demands索引

    Args:
        query: 搜索关键词
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如createdAt, updatedAt, expiresAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"）
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        attributes_to_retrieve: 指定要返回的字段列表，可选
        sort: 排序规则列表，可选

    Returns:
        搜索结果字典

    示例:
        # 基本关键词搜索
        search_supply_demands("瓦楞纸箱")

        # 带筛选条件的搜索
        search_supply_demands(
            "瓦楞纸箱", 
            filter_conditions={
                "category": "瓦楞纸箱",
                "areaName": "天元区"
            }
        )

        # 带排序和字段筛选的搜索
        search_supply_demands(
            "纸箱",
            filter_conditions={
                "category": ["瓦楞纸箱", "包装盒"],
            },
            sort=["createdAt:desc"],
            attributes_to_retrieve=["id", "title", "productName", "quantity", "price", "areaName", "companyName", "contactName", "contactPhone", "createdAt"],
            limit=10
        )

        # 搜索特定价格范围的产品
        search_supply_demands(
            "瓦楞纸箱",
            filter_conditions={
                "category": "瓦楞纸箱",
            },
            sort=["createdAt:desc"],
            limit=5
        )
        
        # 按公司名称搜索
        search_supply_demands(
            "测试有限公司",
            filter_conditions={
                "companyName": "测试有限公司"
            },
            sort=["createdAt:desc"]
        )
        
        # 按地区搜索
        search_supply_demands(
            "",
            filter_conditions={
                "areaName": "天元区"
            },
            sort=["createdAt:desc"]
        )
        
        # 按时间范围搜索
        search_supply_demands(
            "",
            filter_conditions={
                "createdAt": {"gte": "2025-09-09T00:00:00.000Z", "lte": "2025-09-09T23:59:59.999Z"}
            },
            sort=["createdAt:desc"]
        )
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 固定查询supply_demands索引
        INDEX_NAME = "supply_demands"

        # 创建MeiliSearch客户端
        client = Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)

        # 获取索引
        index = client.index(INDEX_NAME)

        # 构建搜索参数
        search_params: dict[str, Any] = {
            'hitsPerPage': limit,
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
        results = index.search(query, search_params)

        # 安全地获取结果字段
        return {
            "success": True,
            "hits": results.get("hits", []),
            "estimated_total_hits": results.get("estimatedTotalHits") or results.get("nbHits", 0),
            "limit": results.get("hitsPerPage") or results.get("limit", limit),
            "offset": results.get("offset", offset),
            "processing_time_ms": results.get("processingTimeMs", 0)
        }

    except errors.MeilisearchApiError as e:
        return {
            "success": False,
            "error": f"MeiliSearch API错误: {str(e)}",
            "error_code": getattr(e, 'code', 'unknown')
        }
    except errors.MeilisearchCommunicationError as e:
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

    # 定义时间字段列表
    time_fields = ["createdAt", "updatedAt", "expiresAt"]

    for key, value in filter_conditions.items():
        if value is None:
            continue

        if isinstance(value, list):
            # 处理数组值的情况 (IN查询)
            if len(value) > 0:
                # 转义特殊字符并构建表达式
                escaped_values = [_escape_filter_value(v, key in time_fields) for v in value]
                values_str = ", ".join(escaped_values)
                filter_expressions.append(f"{key} IN [{values_str}]")
        elif isinstance(value, dict):
            # 处理范围查询和其他复杂条件
            for op, val in value.items():
                if op == "gt":
                    filter_expressions.append(
                        f"{key} > {_escape_filter_value(val, key in time_fields)}")
                elif op == "gte":
                    filter_expressions.append(
                        f"{key} >= {_escape_filter_value(val, key in time_fields)}")
                elif op == "lt":
                    filter_expressions.append(
                        f"{key} < {_escape_filter_value(val, key in time_fields)}")
                elif op == "lte":
                    filter_expressions.append(
                        f"{key} <= {_escape_filter_value(val, key in time_fields)}")
                elif op == "ne":
                    filter_expressions.append(
                        f"{key} != {_escape_filter_value(val, key in time_fields)}")
        else:
            # 处理单个值的情况
            filter_expressions.append(f"{key} = {_escape_filter_value(value, key in time_fields)}")

    return filter_expressions


def _escape_filter_value(value: Any, is_time_field: bool = False) -> str:
    """
    转义筛选值中的特殊字符

    Args:
        value: 要转义的值
        is_time_field: 是否为时间字段，如果是则需要特殊处理

    Returns:
        转义后的字符串
    """
    # 如果是时间字段且值是日期时间对象，则转换为ISO格式字符串
    if is_time_field and hasattr(value, 'isoformat'):
        value = value.isoformat().replace('+00:00', 'Z')
    elif is_time_field and isinstance(value, (int, float)):
        # 如果是时间戳，转换为日期时间对象再转为ISO格式
        import datetime
        try:
            # 假设是秒级时间戳
            dt = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
            value = dt.isoformat().replace('+00:00', 'Z')
        except (ValueError, OSError):
            # 如果转换失败，保持原值
            pass

    if isinstance(value, str):
        # 转义单引号并用单引号包围字符串
        escaped = value.replace("'", "\\'")
        return f"'{escaped}'"
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


if __name__ == "__main__":
    # 从环境变量获取服务器配置
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8800"))

    # 使用HTTP连接方式运行服务器
    mcp.run(transport="http", host=host, port=port)