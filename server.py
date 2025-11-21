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
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如createdAt, updatedAt, expiresAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"），系统会自动转换为时间戳进行筛选
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        sort: 排序规则列表，可选

    Returns:
        搜索结果字典

    供需索引字段说明:
        - id: 唯一标识符
        - title: 标题
        - description: 描述
        - category: 分类
        - type: 类型（1表示供应，2表示需求，4表示招标）
        - companyName: 公司名称
        - areaName: 地区名称
        - price: 价格
        - unit: 单位
        - quantity: 数量
        - contactName: 联系人姓名
        - contactPhone: 联系电话
        - email: 邮箱
        - status: 状态
        - createdAt: 创建时间
        - updatedAt: 更新时间
        - expiresAt: 过期时间/投标截止时间

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
                "areaName": "石峰区"
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

        # 处理排序字段
        if sort:
            processed_sort = _process_sort_fields(sort)
            search_params['sort'] = processed_sort

        # 处理筛选条件
        # 合并用户提供的筛选条件和默认的未过期条件
        combined_filter_conditions = filter_conditions or {}

        # 添加默认的未过期条件：expiresAtTimestamp大于当前时间戳，或者expiresAtTimestamp不存在（永不过期）
        import time
        current_timestamp = int(time.time() * 1000)  # 当前时间戳（毫秒）

        # 如果用户没有提供expiresAt相关的筛选条件，则添加默认的未过期条件
        if "expiresAt" not in combined_filter_conditions and "expiresAtTimestamp" not in combined_filter_conditions:
            # 构建默认筛选条件表达式
            # 条件1: expiresAtTimestamp大于当前时间戳（未过期）
            # 条件2: expiresAtTimestamp不存在（未设置过期时间）
            # 使用OR连接这两个条件
            default_filter_expression = f"(expiresAtTimestamp > {current_timestamp} OR expiresAtTimestamp IS NULL)"

            if combined_filter_conditions:
                # 先处理用户提供的筛选条件
                user_filter_expressions = _build_filter_expressions(
                    combined_filter_conditions)
                if user_filter_expressions:
                    # 将用户筛选条件和默认筛选条件组合
                    # 用户条件之间用AND连接，与默认条件用AND连接
                    user_filter_str = " AND ".join(user_filter_expressions)
                    search_params['filter'] = f"{user_filter_str} AND {default_filter_expression}"
            else:
                # 没有用户筛选条件，只使用默认筛选条件
                search_params['filter'] = default_filter_expression
        else:
            # 用户提供了expiresAt相关的筛选条件，使用用户提供的条件
            if combined_filter_conditions:
                filter_expressions = _build_filter_expressions(
                    combined_filter_conditions)
                if filter_expressions:
                    search_params['filter'] = " AND ".join(filter_expressions)

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
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如publishDate, effectDate, expireDate, createdAt, updatedAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"），系统会自动转换为时间戳进行筛选
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        sort: 排序规则列表，可选。注意：如果排序字段为时间字段，系统会自动转换为对应的timestamp字段进行排序

    Returns:
        搜索结果字典

    政策索引字段说明:
        - id: 唯一标识符
        - title: 标题
        - content: 内容
        - category: 分类
        - status: 状态
        - statusText: 状态文本
        - effectDate: 生效日期
        - expireDate: 失效日期
        - author: 作者/发布部门
        - updatedAt: 更新时间

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
                "effectDate": {"gte": "2025-01-01T00:00:00.000Z", "lte": "2025-12-31T23:59:59.999Z"}
            },
            sort=["effectDate:desc"]
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

        # 处理排序字段
        if sort:
            processed_sort = _process_sort_fields(sort)
            search_params['sort'] = processed_sort

        # 处理筛选条件
        if filter_conditions:
            # # 特殊处理：如果筛选条件中包含areaNames，则额外添加appliesToAllAreas=1的条件
            # if "areaNames" in filter_conditions:
            #     # 构建基础筛选条件（除了areaNames）
            #     base_conditions = {k: v for k, v in filter_conditions.items() if k != "areaNames"}
            #     base_expressions = _build_filter_expressions(base_conditions)

            #     # 构建areaNames筛选条件
            #     area_conditions = {"areaNames": filter_conditions["areaNames"]}
            #     area_expressions = _build_filter_expressions(area_conditions)

            #     # 构建appliesToAllAreas=1的条件
            #     all_areas_expressions = _build_filter_expressions({"appliesToAllAreas": 1})

            #     # 组合所有条件
            #     all_filters = []
            #     if base_expressions:
            #         # 基础条件用AND连接
            #         all_filters.extend(base_expressions)

            #     # areaNames条件和appliesToAllAreas条件组成OR关系
            #     if area_expressions and all_areas_expressions:
            #         area_filter = area_expressions[0]
            #         all_areas_filter = all_areas_expressions[0]
            #         combined_area_filter = f"({area_filter}) OR ({all_areas_filter})"
            #         all_filters.append(combined_area_filter)

            #     # 将所有筛选条件组合成一个字符串
            #     if all_filters:
            #         search_params['filter'] = " AND ".join(all_filters)
            # else:
            # 正常处理筛选条件
            filter_expressions = _build_filter_expressions(filter_conditions)
            if filter_expressions:
                # 将筛选条件组合成一个字符串
                search_params['filter'] = " AND ".join(filter_expressions)

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
        filter_conditions: 筛选条件字典，可选。注意：如果筛选条件中包含时间字段（如establishDate, createdAt, updatedAt），时间值应使用ISO 8601格式字符串（例如："2025-09-09T07:43:16.910Z"），系统会自动转换为时间戳进行筛选
        limit: 返回结果数量限制，默认20
        offset: 偏移量，默认0
        sort: 排序规则列表，可选。注意：如果排序字段为时间字段，系统会自动转换为对应的timestamp字段进行排序

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
                "areaName": "荷塘区"
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

        # 处理排序字段
        if sort:
            processed_sort = _process_sort_fields(sort)
            search_params['sort'] = processed_sort

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

    # 定义时间字段列表和对应的timestamp字段映射
    time_fields = ["createdAt", "updatedAt", "expiresAt",
                   "publishDate", "effectDate", "expireDate", "establishDate"]
    time_field_mapping = {
        "createdAt": "createdAtTimestamp",
        "updatedAt": "updatedAtTimestamp",
        "expiresAt": "expiresAtTimestamp",
        "publishDate": "publishDateTimestamp",
        "effectDate": "effectDateTimestamp",
        "expireDate": "expireDateTimestamp",
        "establishDate": "establishDateTimestamp"
    }

    for key, value in filter_conditions.items():
        if value is None:
            continue

        # 确定是否为时间字段
        is_time_field = key in time_fields

        # 如果是时间字段，使用对应的timestamp字段名
        field_name = time_field_mapping.get(key, key) if is_time_field else key

        if isinstance(value, list):
            # 处理数组值的情况 (IN查询)
            if len(value) > 0:
                # 转义特殊字符并构建表达式
                escaped_values = [_escape_filter_value(
                    v, is_time_field) for v in value]
                values_str = ", ".join(escaped_values)
                filter_expressions.append(f"{field_name} IN [{values_str}]")
        elif isinstance(value, dict):
            # 处理范围查询和其他复杂条件
            for op, val in value.items():
                if op == "gt":
                    filter_expressions.append(
                        f"{field_name} > {_escape_filter_value(val, is_time_field)}")
                elif op == "gte":
                    filter_expressions.append(
                        f"{field_name} >= {_escape_filter_value(val, is_time_field)}")
                elif op == "lt":
                    filter_expressions.append(
                        f"{field_name} < {_escape_filter_value(val, is_time_field)}")
                elif op == "lte":
                    filter_expressions.append(
                        f"{field_name} <= {_escape_filter_value(val, is_time_field)}")
                elif op == "ne":
                    filter_expressions.append(
                        f"{field_name} != {_escape_filter_value(val, is_time_field)}")
        else:
            # 处理单个值的情况
            filter_expressions.append(
                f"{field_name} = {_escape_filter_value(value, is_time_field)}")
    print(filter_expressions)
    return filter_expressions


def _process_sort_fields(sort: Optional[List[str]]) -> Optional[List[str]]:
    """
    处理排序字段，将时间字段转换为对应的timestamp字段

    Args:
        sort: 排序规则列表，如 ["createdAt:desc", "updatedAt:asc"]

    Returns:
        处理后的排序规则列表
    """
    if not sort:
        return sort

    # 定义时间字段列表和对应的timestamp字段映射
    time_field_mapping = {
        "createdAt": "createdAtTimestamp",
        "updatedAt": "updatedAtTimestamp",
        "expiresAt": "expiresAtTimestamp",
        "publishDate": "publishDateTimestamp",
        "effectDate": "effectDateTimestamp",
        "expireDate": "expireDateTimestamp",
        "establishDate": "establishDateTimestamp"
    }

    processed_sort = []
    for sort_field in sort:
        # 分离字段名和排序方向
        if ":" in sort_field:
            field_name, direction = sort_field.split(":", 1)
            # 如果是时间字段，使用对应的timestamp字段名
            if field_name in time_field_mapping:
                processed_sort.append(
                    f"{time_field_mapping[field_name]}:{direction}")
            else:
                processed_sort.append(sort_field)
        else:
            # 只有字段名，没有排序方向
            if sort_field in time_field_mapping:
                processed_sort.append(time_field_mapping[sort_field])
            else:
                processed_sort.append(sort_field)

    return processed_sort


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
    elif is_time_field and isinstance(value, str):
        # 如果是时间字段且值是ISO格式字符串，则转换为时间戳
        try:
            import datetime
            # 解析ISO格式的时间字符串
            if value.endswith('Z'):
                dt = datetime.datetime.fromisoformat(
                    value[:-1]).replace(tzinfo=datetime.timezone.utc)
            else:
                dt = datetime.datetime.fromisoformat(value)
            # 转换为时间戳（毫秒）
            timestamp = int(dt.timestamp() * 1000)
            value = timestamp
        except (ValueError, TypeError):
            # 如果解析失败，保持原值
            pass
    elif is_time_field and isinstance(value, (int, float)):
        # 如果是时间戳，保持原值
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
    获取所有索引中的地区名称(areaName)，包括companies、supply_demands和policies索引中的areaNames数组字段

    Returns:
        包含所有地区名称列表的字典
    """
    try:
        # 从环境变量获取MeiliSearch配置
        MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        MEILISEARCH_MASTER_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "")

        # 创建MeiliSearch客户端
        client = Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)

        all_area_names = set()  # 使用集合避免重复

        # 定义要查询的索引列表
        index_names = ["companies", "supply_demands"]

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
                area_names = list(
                    facet_distribution.get("areaName", {}).keys())
                all_area_names.update(area_names)

            except errors.MeilisearchApiError as e:
                # 如果某个索引出现问题，记录错误但继续处理其他索引
                print(f"获取索引 {index_name} 的地区名称时出错: {str(e)}")
                continue
            except errors.MeilisearchCommunicationError as e:
                # 如果连接某个索引出现问题，记录错误但继续处理其他索引
                print(f"连接索引 {index_name} 时出错: {str(e)}")
                continue

        # 单独处理policies索引，获取areaNames数组字段
        try:
            policies_index = client.index("policies")

            # 搜索所有文档，获取areaNames字段
            search_params = {
                'attributesToRetrieve': ['areaNames'],
                'hitsPerPage': 1000  # 根据实际数据量调整
            }

            results = policies_index.search("", search_params)

            # 从结果中提取所有areaNames数组中的地区名称
            for hit in results.get('hits', []):
                area_names_array = hit.get('areaNames', [])
                if isinstance(area_names_array, list):
                    all_area_names.update(area_names_array)

        except errors.MeilisearchApiError as e:
            print(f"获取policies索引中的areaNames时出错: {str(e)}")
        except errors.MeilisearchCommunicationError as e:
            print(f"连接policies索引时出错: {str(e)}")

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
