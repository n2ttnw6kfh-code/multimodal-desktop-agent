# ==============================================================================
# 文件名: tools/stock.py
# 职责: 查询股票/指数/汇率的实时价格（数据源：Yahoo Finance）
# ==============================================================================
from .base import register_tool


@register_tool(
    name="get_stock_price",
    description=(
        "查询股票、指数或外汇的实时价格与涨跌幅。"
        "支持 A 股（如 600519.SS）、美股（如 AAPL）、港股（如 0700.HK）、"
        "指数（如 ^GSPC）和汇率（如 USDCNY=X）。"
        "当用户询问股价、汇率、指数行情时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 'AAPL'、'600519.SS'、'USDCNY=X'",
            }
        },
        "required": ["symbol"],
    },
)
def get_stock_price(symbol: str) -> str:
    try:
        import yfinance as yf
    except ImportError:
        return "缺少依赖：请先执行 pip install yfinance"

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info  # 比 .info 快很多

        price = info.get("last_price")
        prev_close = info.get("previous_close")
        currency = info.get("currency", "")

        if price is None:
            return f"未找到 {symbol} 的行情数据，请检查代码是否正确。"

        change = (price - prev_close) if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0
        arrow = "📈" if change >= 0 else "📉"

        return (
            f"【{symbol} 实时行情】\n"
            f"最新价：{price:.4f} {currency}\n"
            f"昨收：  {prev_close:.4f} {currency}\n"
            f"涨跌：  {arrow} {change:+.4f}（{change_pct:+.2f}%）"
        )
    except Exception as e:
        return f"行情查询失败: {e}"