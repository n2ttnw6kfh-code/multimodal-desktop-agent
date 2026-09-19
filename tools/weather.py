# ==============================================================================
# 文件名: tools/weather.py
# ==============================================================================
import requests

from .base import register_tool


@register_tool(
    name="get_weather",
    description="查询指定城市的实时天气和未来三天预报。",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称，如'北京'、'上海'"}
        },
        "required": ["city"],
    },
)
def get_weather(city: str) -> str:
# def get_weather(city: str, **_kwargs) -> str:
    try:
        url = f"https://wttr.in/{city}?format=j1&lang=zh"
        resp = requests.get(url, timeout=10)
        data = resp.json()

        current = data["current_condition"][0]
        desc = (
            current["lang_zh"][0]["value"]
            if "lang_zh" in current
            else current["weatherDesc"][0]["value"]
        )
        temp = current["temp_C"]
        feels = current["FeelsLikeC"]
        humidity = current["humidity"]
        wind = current["windspeedKmph"]

        forecast_lines = []
        for day in data.get("weather", [])[:3]:
            forecast_lines.append(
                f"  {day['date']}: {day['mintempC']}~{day['maxtempC']}°C"
            )

        return (
            f"【{city} 实时天气】\n"
            f"当前：{desc}，{temp}°C（体感 {feels}°C）\n"
            f"湿度：{humidity}%  风速：{wind} km/h\n"
            f"未来三天：\n" + "\n".join(forecast_lines)
        )
    except Exception as e:
        return f"天气查询失败: {e}"