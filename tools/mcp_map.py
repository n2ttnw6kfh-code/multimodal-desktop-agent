# ==============================================================================
# 文件名: tools/mcp_map.py
# 职责: 高德地图 MCP 工具（通过魔搭托管）
# 说明:
#   - MCP 是异步的，工具是同步的 → 用独立线程桥接
#   - 坐标格式统一为 "经度,纬度"
# ==============================================================================
import asyncio
import threading

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from .base import register_tool


# ⚠️ 从魔搭复制的完整 URL
MCP_URL = "https://mcp.api-inference.modelscope.net/2c587b24185649/mcp"


# ==============================================================================
# 底层：MCP 调用桥接
# ==============================================================================
def _run_mcp_tool(tool_name: str, arguments: dict, timeout: int = 30) -> str:
    """在独立线程里跑 MCP 调用，避免和 Qt 事件循环冲突。"""
    result_holder = {"value": None, "error": None}

    def _worker():
        try:
            async def _call():
                async with streamable_http_client(MCP_URL) as streams:
                    r, w = streams[0], streams[1]
                    async with ClientSession(r, w) as session:
                        await session.initialize()
                        res = await session.call_tool(tool_name, arguments)
                        # 提取文本内容
                        parts = []
                        for item in res.content:
                            text = getattr(item, "text", None)
                            if text:
                                parts.append(text)
                        return "\n".join(parts)
            result_holder["value"] = asyncio.run(_call())
        except Exception as e:
            result_holder["error"] = str(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return f"MCP 调用超时（>{timeout}s）"
    if result_holder["error"]:
        return f"MCP 调用失败: {result_holder['error']}"
    return result_holder["value"] or "（MCP 返回为空）"


# ==============================================================================
# 工具 1：关键词搜索地点
# ==============================================================================
@register_tool(
    name="map_search_places",
    description=(
        "根据关键词搜索城市内的地点信息，如餐厅、酒店、景点、加油站、商场。"
        "当用户询问某个城市有什么地方时使用。返回结果包含地点名称、地址、POI ID。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "keywords": {"type": "string", "description": "搜索关键词，如'餐厅'、'酒店'"},
            "city": {"type": "string", "description": "查询城市，如'北京'、'上海'"},
            "types": {"type": "string", "description": "POI 类型（可选），如'加油站'"},
        },
        "required": ["keywords"],
    },
)
def map_search_places(keywords: str, city: str = "", types: str = "") -> str:
    print(f"[高德] 搜索地点: {keywords} @ {city}")
    args = {"keywords": keywords}
    if city:
        args["city"] = city
    if types:
        args["types"] = types
    return _run_mcp_tool("maps_text_search", args)


# ==============================================================================
# 工具 2：周边搜索
# ==============================================================================
@register_tool(
    name="map_search_nearby",
    description=(
        "在指定坐标周围搜索地点。需要先知道中心点坐标（可通过 map_geocode 获取）。"
        "当用户询问'某个地方附近有什么'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "中心点坐标，格式'经度,纬度'"},
            "keywords": {"type": "string", "description": "搜索关键词（可选）"},
            "radius": {"type": "string", "description": "搜索半径（米，默认 1000）"},
        },
        "required": ["location"],
    },
)
def map_search_nearby(location: str, keywords: str = "", radius: str = "1000") -> str:
    print(f"[高德] 周边搜索: {keywords} @ {location}, 半径 {radius}m")
    args = {"location": location, "radius": radius}
    if keywords:
        args["keywords"] = keywords
    return _run_mcp_tool("maps_around_search", args)


# ==============================================================================
# 工具 3：地理编码（地址 → 经纬度）
# ==============================================================================
@register_tool(
    name="map_geocode",
    description=(
        "把地址或地名转换成经纬度坐标。"
        "当需要查询某个具体地址的坐标，或为路线规划获取起点/终点坐标时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "address": {"type": "string", "description": "详细地址或地标名称，如'天安门'"},
            "city": {"type": "string", "description": "指定城市（可选），如'北京'"},
        },
        "required": ["address"],
    },
)
def map_geocode(address: str, city: str = "") -> str:
    print(f"[高德] 地理编码: {address} @ {city}")
    args = {"address": address}
    if city:
        args["city"] = city
    return _run_mcp_tool("maps_geo", args)


# ==============================================================================
# 工具 4：逆地理编码（经纬度 → 地址）
# ==============================================================================
@register_tool(
    name="map_regeocode",
    description="把经纬度坐标转换为行政区划地址信息。",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "经纬度坐标，格式'经度,纬度'"},
        },
        "required": ["location"],
    },
)
def map_regeocode(location: str) -> str:
    return _run_mcp_tool("maps_regeocode", {"location": location})


# ==============================================================================
# 工具 5：驾车路线
# ==============================================================================
@register_tool(
    name="map_directions",
    description=(
        "规划驾车路线。当用户询问开车怎么去、驾车路线、驾车距离、驾车耗时等问题时使用。"
        "起点和终点坐标格式为'经度,纬度'，可先用 map_geocode 把地名转成坐标。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "起点坐标，格式'经度,纬度'"},
            "destination": {"type": "string", "description": "终点坐标，格式'经度,纬度'"},
        },
        "required": ["origin", "destination"],
    },
)
def map_directions(origin: str, destination: str) -> str:
    print(f"[高德] 驾车路线: {origin} → {destination}")
    return _run_mcp_tool("maps_direction_driving", {
        "origin": origin,
        "destination": destination,
    })


# ==============================================================================
# 工具 6：步行路线
# ==============================================================================
@register_tool(
    name="map_walking_route",
    description="规划步行路线。100km 以内的步行方案。",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "起点坐标，格式'经度,纬度'"},
            "destination": {"type": "string", "description": "终点坐标，格式'经度,纬度'"},
        },
        "required": ["origin", "destination"],
    },
)
def map_walking_route(origin: str, destination: str) -> str:
    return _run_mcp_tool("maps_direction_walking", {
        "origin": origin,
        "destination": destination,
    })


# ==============================================================================
# 工具 7：骑行路线
# ==============================================================================
@register_tool(
    name="map_bicycling_route",
    description="规划骑行路线。最大支持 500km 的骑行方案。",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "起点坐标，格式'经度,纬度'"},
            "destination": {"type": "string", "description": "终点坐标，格式'经度,纬度'"},
        },
        "required": ["origin", "destination"],
    },
)
def map_bicycling_route(origin: str, destination: str) -> str:
    return _run_mcp_tool("maps_bicycling", {
        "origin": origin,
        "destination": destination,
    })


# ==============================================================================
# 工具 8：公交路线
# ==============================================================================
@register_tool(
    name="map_transit_route",
    description="规划公共交通路线（火车、公交、地铁）。跨城场景必须传起点和终点城市。",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "起点坐标，格式'经度,纬度'"},
            "destination": {"type": "string", "description": "终点坐标，格式'经度,纬度'"},
            "city": {"type": "string", "description": "起点城市，如'北京'"},
            "cityd": {"type": "string", "description": "终点城市，如'上海'"},
        },
        "required": ["origin", "destination", "city", "cityd"],
    },
)
def map_transit_route(origin: str, destination: str, city: str, cityd: str) -> str:
    return _run_mcp_tool("maps_direction_transit_integrated", {
        "origin": origin,
        "destination": destination,
        "city": city,
        "cityd": cityd,
    })


# ==============================================================================
# 工具 9：距离测量
# ==============================================================================
@register_tool(
    name="map_distance",
    description="测量两个坐标之间的距离。支持驾车距离、步行距离、直线距离。",
    parameters={
        "type": "object",
        "properties": {
            "origins": {"type": "string", "description": "起点坐标，格式'经度,纬度'，多个坐标用竖线分隔"},
            "destination": {"type": "string", "description": "终点坐标，格式'经度,纬度'"},
            "type": {"type": "string", "description": "测量类型：1=驾车，0=直线，3=步行（默认 1）", "default": "1"},
        },
        "required": ["origins", "destination"],
    },
)
def map_distance(origins: str, destination: str, type: str = "1") -> str:
    return _run_mcp_tool("maps_distance", {
        "origins": origins,
        "destination": destination,
        "type": type,
    })


# ==============================================================================
# 工具 10：天气查询
# ==============================================================================
@register_tool(
    name="map_weather",
    description="根据城市名称或 adcode 查询指定城市的天气。",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称或 adcode，如'北京'"},
        },
        "required": ["city"],
    },
)
def map_weather(city: str) -> str:
    print(f"[高德] 天气查询: {city}")
    return _run_mcp_tool("maps_weather", {"city": city})


# ==============================================================================
# 工具 11：IP 定位
# ==============================================================================
@register_tool(
    name="map_ip_location",
    description="根据 IP 地址定位其所在位置。",
    parameters={
        "type": "object",
        "properties": {
            "ip": {"type": "string", "description": "IP 地址"},
        },
        "required": ["ip"],
    },
)
def map_ip_location(ip: str) -> str:
    return _run_mcp_tool("maps_ip_location", {"ip": ip})


# ==============================================================================
# 工具 12：POI 详情
# ==============================================================================
@register_tool(
    name="map_poi_detail",
    description="查询搜索获取到的 POI ID 的详细信息。",
    parameters={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "POI ID（从搜索结果获取）"},
        },
        "required": ["id"],
    },
)
def map_poi_detail(id: str) -> str:
    return _run_mcp_tool("maps_search_detail", {"id": id})