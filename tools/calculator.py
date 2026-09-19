# ==============================================================================
# 文件名: tools/calculator.py
# 职责: 安全数学计算（AST 解析，防 eval 注入）
# ==============================================================================
import ast

from .base import register_tool


def _safe_eval(node):
    """递归求值 AST 节点，只允许安全类型"""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("除数不能为零")
            return left / right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("取模运算除数不能为零")
            return left % right
        if isinstance(node.op, ast.Pow):
            if abs(right) > 10000:
                raise ValueError("幂运算指数过大")
            return left ** right
        raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return operand
        raise ValueError("不支持的一元运算符")
    raise ValueError(f"不支持的表达式: {type(node).__name__}")


@register_tool(
    name="calculate",
    description="进行数学计算，支持 + - * / ( ) % ^ 和基本函数。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 '2+3*4'"}
        },
        "required": ["expression"],
    },
)
def calculate(expression: str) -> str:
# def calculate(expression: str, **_kwargs) -> str:
    try:
        normalized = expression.replace("^", "**")
        allowed_chars = set("0123456789+-*/().% \t\n")
        if not all(c in allowed_chars for c in normalized):
            return "计算失败：表达式包含不允许的字符"

        tree = ast.parse(normalized, mode="eval")
        result = _safe_eval(tree.body)
        return f"计算结果：{expression} = {result}"
    except ZeroDivisionError as e:
        return f"计算失败: {e}"
    except ValueError as e:
        return f"计算失败: {e}"
    except SyntaxError as e:
        return f"计算失败: 表达式语法错误 - {e}"
    except Exception as e:
        return f"计算失败: {e}"