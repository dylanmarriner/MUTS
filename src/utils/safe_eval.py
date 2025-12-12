"""
Safe mathematical expression evaluator
Replaces dangerous eval() usage with controlled AST parsing
"""
import ast
import operator
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Mapping of AST operators to Python operators
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

class SafeEvalVisitor(ast.NodeVisitor):
    """AST visitor that validates only allowed operations"""
    
    def __init__(self, allowed_names: set):
        self.allowed_names = allowed_names
        self.errors = []
    
    def visit_Expression(self, node: ast.Expression) -> None:
        self.generic_visit(node)
    
    def visit_BinOp(self, node: ast.BinOp) -> None:
        if type(node.op) not in OPERATORS:
            self.errors.append(f"Operator {type(node.op).__name__} not allowed")
        self.generic_visit(node)
    
    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if type(node.op) not in OPERATORS:
            self.errors.append(f"Unary operator {type(node.op).__name__} not allowed")
        self.generic_visit(node)
    
    def visit_Num(self, node: ast.Num) -> None:
        pass  # Numbers are always allowed
    
    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, (int, float)):
            pass  # Numbers are allowed
        else:
            self.errors.append(f"Constant type {type(node.value).__name__} not allowed")
    
    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in self.allowed_names:
            self.errors.append(f"Variable '{node.id}' not allowed")
    
    def generic_visit(self, node: ast.AST) -> None:
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)

def safe_eval_expression(expression: str, variables: Dict[str, Any], 
                        allowed_names: Optional[set] = None) -> Any:
    """
    Safely evaluate a mathematical expression
    
    Args:
        expression: String expression to evaluate
        variables: Dictionary of variable values
        allowed_names: Set of allowed variable names (defaults to variables.keys())
    
    Returns:
        Result of the expression
    
    Raises:
        SyntaxError: If expression has invalid syntax
        ValueError: If expression contains disallowed operations
        ZeroDivisionError: If division by zero occurs
    """
    if allowed_names is None:
        allowed_names = set(variables.keys())
    
    # Log the expression for auditability
    logger.debug(f"Evaluating expression: {expression} with variables: {list(variables.keys())}")
    
    try:
        # Parse the expression
        tree = ast.parse(expression, mode='eval')
        
        # Validate the AST
        validator = SafeEvalVisitor(allowed_names)
        validator.visit(tree)
        
        if validator.errors:
            raise ValueError(f"Expression contains disallowed operations: {', '.join(validator.errors)}")
        
        # Evaluate the expression
        return _eval_node(tree.body, variables)
        
    except SyntaxError as e:
        logger.error(f"Syntax error in expression '{expression}': {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error in expression '{expression}': {e}")
        raise
    except Exception as e:
        logger.error(f"Error evaluating expression '{expression}': {e}")
        raise ValueError(f"Failed to evaluate expression: {e}")

def _eval_node(node: ast.AST, variables: Dict[str, Any]) -> Any:
    """Recursively evaluate an AST node"""
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](left, right)
        else:
            raise ValueError(f"Operator {op_type.__name__} not allowed")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, variables)
        op_type = type(node.op)
        if op_type in OPERATORS:
            return OPERATORS[op_type](operand)
        else:
            raise ValueError(f"Unary operator {op_type.__name__} not allowed")
    elif isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        else:
            raise ValueError(f"Variable '{node.id}' not defined")
    else:
        raise ValueError(f"AST node type {type(node).__name__} not allowed")

# Convenience function for mpsrom.py usage
def evaluate_mpsrom_formula(formula: str, data: list) -> float:
    """
    Evaluate MPS ROM formula with A, B, C, D variables
    
    Args:
        formula: Mathematical expression string
        data: List of values [A] or [A, B] or [A, B, C, D]
    
    Returns:
        Evaluated result as float
    """
    # Map data to variables
    variables = {}
    if len(data) >= 1:
        variables['A'] = data[0]
    if len(data) >= 2:
        variables['B'] = data[1]
    if len(data) >= 3:
        variables['C'] = data[2]
    if len(data) >= 4:
        variables['D'] = data[3]
    
    # Only allow A, B, C, D variables
    allowed_names = {'A', 'B', 'C', 'D'}
    
    result = safe_eval_expression(formula, variables, allowed_names)
    
    # Ensure result is numeric
    if not isinstance(result, (int, float)):
        raise ValueError(f"Formula must evaluate to numeric result, got {type(result)}")
    
    return float(result)
