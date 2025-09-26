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
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    查询MeiliSearch中的supply_demands索引

    Args:
        query: 搜索关键词
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如createdAt, updatedAt, expiresAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"）
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
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
        hits = results.get("hits", [])
        return {
            "success": True,
            "data": hits,
            "count": len(hits),
            "message": f"找到{len(hits)}条供需信息"
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


@mcp.tool
def search_policies(
    query: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0,
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    查询MeiliSearch中的policies索引

    Args:
        query: 搜索关键词
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如publishDate, effectDate, expireDate, createdAt, updatedAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"）
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        sort: 排序规则列表，可选

    Returns:
        搜索结果字典

    政策索引字段说明:
        - id: 唯一标识符
        - title: 标题
        - content: 内容
        - category: 分类
        - status: 状态
        - statusText: 状态文本
        - publishDate: 发布日期
        - effectDate: 生效日期
        - expireDate: 失效日期
        - author: 作者
        - tags: 标签
        - priority: 优先级
        - viewCount: 查看次数
        - version: 版本
        - createdAt: 创建时间
        - updatedAt: 更新时间
        - areaNames: 地区名称列表
        - areaIds: 地区ID列表

    示例:
        # 基本关键词搜索
        search_policies("税收优惠政策")

        # 按分类筛选
        search_policies(
            "", 
            filter_conditions={
                "category": "税收政策"
            }
        )

        # 按时间范围搜索
        search_policies(
            "",
            filter_conditions={
                "publishDate": {"gte": "2025-01-01T00:00:00.000Z", "lte": "2025-12-31T23:59:59.999Z"}
            },
            sort=["publishDate:desc"]
        )

        # 按地区搜索
        search_policies(
            "",
            filter_conditions={
                "areaNames": "湖南省"
            }
        )

        # 复合条件搜索
        search_policies(
            "小微企业",
            filter_conditions={
                "category": ["税收政策", "财政政策"],
                "status": "active"
            },
            sort=["publishDate:desc"],
            limit=10
        )
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 固定查询policies索引
        INDEX_NAME = "policies"

        # 创建MeiliSearch客户端
        client = Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)

        # 获取索引
        index = client.index(INDEX_NAME)

        # 构建搜索参数
        search_params: dict[str, Any] = {
            'hitsPerPage': limit,
            'offset': offset
        }

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
        hits = results.get("hits", [])
        return {
            "success": True,
            "data": hits,
            "count": len(hits),
            "message": f"找到{len(hits)}条政策信息"
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


@mcp.tool
def search_companies(
    query: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0,
    sort: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    查询MeiliSearch中的companies索引

    Args:
        query: 搜索关键词
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如establishDate, createdAt, updatedAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"）
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        sort: 排序规则列表，可选

    Returns:
        搜索结果字典

    企业索引字段说明:
        - id: 唯一标识符
        - name: 公司名称
        - description: 公司描述
        - industry: 行业
        - companyType: 公司类型
        - employeeCount: 员工数量
        - registeredAddress: 注册地址
        - contactName: 联系人姓名
        - contactPhone: 联系电话
        - email: 邮箱
        - website: 网站
        - establishDate: 成立日期
        - registeredCapital: 注册资本(单位是万元)
        - legalPerson: 法人代表
        - legalPersonPhone: 法人电话
        - isActive: 是否激活
        - areaName: 地区名称
        - areaCode: 地区代码
        - areaDescription: 地区描述
        - areaId: 地区ID
        - createdAt: 创建时间
        - updatedAt: 更新时间

    示例:
        # 基本关键词搜索
        search_companies("科技有限公司")

        # 按行业筛选
        search_companies(
            "", 
            filter_conditions={
                "industry": "信息技术"
            }
        )

        # 按地区搜索
        search_companies(
            "",
            filter_conditions={
                "areaName": "北京市"
            }
        )

        # 按成立时间范围搜索
        search_companies(
            "",
            filter_conditions={
                "establishDate": {"gte": "2020-01-01T00:00:00.000Z", "lte": "2025-12-31T23:59:59.999Z"}
            },
            sort=["establishDate:desc"]
        )

        # 复合条件搜索
        search_companies(
            "软件",
            filter_conditions={
                "industry": ["信息技术", "软件开发"],
                "isActive": True
            },
            sort=["createdAt:desc"],
            limit=10
        )
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 固定查询companies索引
        INDEX_NAME = "companies"

        # 创建MeiliSearch客户端
        client = Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)

        # 获取索引
        index = client.index(INDEX_NAME)

        # 构建搜索参数
        search_params: dict[str, Any] = {
            'hitsPerPage': limit,
            'offset': offset
        }

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
        hits = results.get("hits", [])
        return {
            "success": True,
            "data": hits,
            "count": len(hits),
            "message": f"找到{len(hits)}条企业信息"
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
                escaped_values = [_escape_filter_value(
                    v, key in time_fields) for v in value]
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
            filter_expressions.append(
                f"{key} = {_escape_filter_value(value, key in time_fields)}")
    print(filter_expressions)
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
            dt = datetime.datetime.fromtimestamp(
                value, tz=datetime.timezone.utc)
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


@mcp.tool
def get_area_names() -> Dict[str, Any]:
    """
    获取所有索引中的地区名称(areaName)，包括companies和supply_demands
    
    Returns:
        包含所有地区名称列表的字典
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 创建MeiliSearch客户端
        client = Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)
        
        # 定义要查询的索引列表
        index_names = ["companies", "supply_demands"]
        all_area_names = set()  # 使用集合避免重复
        
        # 遍历每个索引获取areaName
        for index_name in index_names:
            try:
                # 获取索引
                index = client.index(index_name)
                
                # 执行搜索并获取facet分布
                search_params = {
                    'facets': ['areaName'],
                    'hitsPerPage': 0  # 我们只需要facet信息，不需要实际的文档
                }
                
                results = index.search("", search_params)
                
                # 从facetDistribution中提取地区名称
                facet_distribution = results.get("facetDistribution", {})
                area_names = list(facet_distribution.get("areaName", {}).keys())
                all_area_names.update(area_names)
                
            except errors.MeilisearchApiError as e:
                # 如果某个索引出现问题，记录错误但继续处理其他索引
                print(f"获取索引 {index_name} 的地区名称时出错: {str(e)}")
                continue
            except errors.MeilisearchCommunicationError as e:
                # 如果连接某个索引出现问题，记录错误但继续处理其他索引
                print(f"连接索引 {index_name} 时出错: {str(e)}")
                continue
        
        # 转换为排序后的列表
        area_names_list = sorted(list(all_area_names))
        
        return {
            "success": True,
            "data": area_names_list,
            "count": len(area_names_list),
            "message": f"找到{len(area_names_list)}个不重复的地区名称"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"未知错误: {str(e)}",
            "error_type": "unknown_error"
        }


if __name__ == "__main__":
    # 从环境变量获取服务器配置
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8800"))

    # 使用HTTP连接方式运行服务器
    mcp.run(transport="http", host=host, port=port)
