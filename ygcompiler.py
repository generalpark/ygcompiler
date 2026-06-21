import sys
from dataclasses import dataclass


# =========================
# Token
# =========================

@dataclass
class Token:
    type: str
    value: object
    line: int
    col: int


KEYWORDS = {
    "let": "LET",
    "print": "PRINT",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "func": "FUNC",
    "return": "RETURN",
    "true": "TRUE",
    "false": "FALSE",
}


# =========================
# Lexer
# =========================

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def current(self):
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def peek(self):
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def advance(self):
        ch = self.current()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def add(self, type_, value=None, line=None, col=None):
        self.tokens.append(Token(type_, value, line or self.line, col or self.col))

    def tokenize(self):
        while self.current() != "\0":
            ch = self.current()

            if ch in " \t\r\n":
                self.advance()
                continue

            if ch == "#":
                while self.current() not in ("\n", "\0"):
                    self.advance()
                continue

            if ch.isdigit():
                self.number()
                continue

            if ch.isalpha() or ch == "_":
                self.identifier()
                continue

            if ch == '"':
                self.string()
                continue

            self.operator_or_symbol()

        self.add("EOF", None)
        return self.tokens

    def number(self):
        start_line = self.line
        start_col = self.col
        text = ""

        while self.current().isdigit():
            text += self.advance()

        if self.current() == ".":
            text += self.advance()
            while self.current().isdigit():
                text += self.advance()

        self.add("NUMBER", float(text), start_line, start_col)

    def identifier(self):
        start_line = self.line
        start_col = self.col
        text = ""

        while self.current().isalnum() or self.current() == "_":
            text += self.advance()

        token_type = KEYWORDS.get(text, "IDENT")
        self.add(token_type, text, start_line, start_col)

    def string(self):
        start_line = self.line
        start_col = self.col
        self.advance()
        text = ""

        while self.current() != '"' and self.current() != "\0":
            if self.current() == "\\":
                self.advance()
                esc = self.advance()
                if esc == "n":
                    text += "\n"
                elif esc == "t":
                    text += "\t"
                elif esc == '"':
                    text += '"'
                else:
                    text += esc
            else:
                text += self.advance()

        if self.current() != '"':
            raise SyntaxError(f"line {start_line}:{start_col} 문자열이 닫히지 않았습니다.")

        self.advance()
        self.add("STRING", text, start_line, start_col)

    def operator_or_symbol(self):
        start_line = self.line
        start_col = self.col
        two = self.current() + self.peek()

        if two in ("==", "!=", "<=", ">=", "&&", "||"):
            self.advance()
            self.advance()
            self.add(two, two, start_line, start_col)
            return

        ch = self.advance()

        if ch in "+-*/%(){};,=!<>":
            self.add(ch, ch, start_line, start_col)
            return

        raise SyntaxError(f"line {start_line}:{start_col} 알 수 없는 문자: {ch}")


# =========================
# AST Nodes
# =========================

@dataclass
class Program:
    statements: list


@dataclass
class Block:
    statements: list


@dataclass
class LetStmt:
    name: str
    expr: object


@dataclass
class AssignStmt:
    name: str
    expr: object


@dataclass
class PrintStmt:
    expr: object


@dataclass
class IfStmt:
    condition: object
    then_block: Block
    else_block: object


@dataclass
class WhileStmt:
    condition: object
    body: Block


@dataclass
class FuncDef:
    name: str
    params: list
    body: Block


@dataclass
class ReturnStmt:
    expr: object


@dataclass
class ExprStmt:
    expr: object


@dataclass
class Literal:
    value: object


@dataclass
class Var:
    name: str


@dataclass
class Binary:
    left: object
    op: str
    right: object


@dataclass
class Unary:
    op: str
    expr: object


@dataclass
class Call:
    name: str
    args: list


# =========================
# Parser
# =========================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def peek(self):
        if self.pos + 1 >= len(self.tokens):
            return self.current()
        return self.tokens[self.pos + 1]

    def match(self, *types):
        if self.current().type in types:
            tok = self.current()
            self.pos += 1
            return tok
        return None

    def consume(self, type_, message):
        tok = self.current()
        if tok.type == type_:
            self.pos += 1
            return tok
        raise SyntaxError(f"line {tok.line}:{tok.col} {message}, 현재 토큰: {tok.type}")

    def parse(self):
        statements = []
        while self.current().type != "EOF":
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        if self.match("LET"):
            return self.let_statement()

        if self.match("PRINT"):
            return self.print_statement()

        if self.match("IF"):
            return self.if_statement()

        if self.match("WHILE"):
            return self.while_statement()

        if self.match("FUNC"):
            return self.func_def()

        if self.match("RETURN"):
            expr = self.expression()
            self.consume(";", "return문 끝에는 ;가 필요합니다")
            return ReturnStmt(expr)

        if self.current().type == "IDENT" and self.peek().type == "=":
            name = self.consume("IDENT", "변수 이름이 필요합니다").value
            self.consume("=", "= 이 필요합니다")
            expr = self.expression()
            self.consume(";", "대입문 끝에는 ;가 필요합니다")
            return AssignStmt(name, expr)

        expr = self.expression()
        self.consume(";", "문장 끝에는 ;가 필요합니다")
        return ExprStmt(expr)

    def let_statement(self):
        name = self.consume("IDENT", "let 뒤에는 변수 이름이 필요합니다").value
        self.consume("=", "변수 선언에는 = 이 필요합니다")
        expr = self.expression()
        self.consume(";", "let 문장 끝에는 ;가 필요합니다")
        return LetStmt(name, expr)

    def print_statement(self):
        self.consume("(", "print 뒤에는 ( 가 필요합니다")
        expr = self.expression()
        self.consume(")", "print 인자 뒤에는 ) 가 필요합니다")
        self.consume(";", "print 문장 끝에는 ;가 필요합니다")
        return PrintStmt(expr)

    def if_statement(self):
        condition = self.expression()
        then_block = self.block()
        else_block = None

        if self.match("ELSE"):
            else_block = self.block()

        return IfStmt(condition, then_block, else_block)

    def while_statement(self):
        condition = self.expression()
        body = self.block()
        return WhileStmt(condition, body)

    def func_def(self):
        name = self.consume("IDENT", "func 뒤에는 함수 이름이 필요합니다").value
        self.consume("(", "함수 이름 뒤에는 ( 가 필요합니다")

        params = []
        if self.current().type != ")":
            while True:
                params.append(self.consume("IDENT", "매개변수 이름이 필요합니다").value)
                if not self.match(","):
                    break

        self.consume(")", "매개변수 뒤에는 ) 가 필요합니다")
        body = self.block()
        return FuncDef(name, params, body)

    def block(self):
        self.consume("{", "블록 시작에는 { 가 필요합니다")
        statements = []

        while self.current().type != "}":
            if self.current().type == "EOF":
                raise SyntaxError("블록이 닫히지 않았습니다. } 가 필요합니다.")
            statements.append(self.statement())

        self.consume("}", "블록 끝에는 } 가 필요합니다")
        return Block(statements)

    def expression(self):
        return self.or_expr()

    def or_expr(self):
        expr = self.and_expr()
        while self.match("||"):
            op = "||"
            right = self.and_expr()
            expr = Binary(expr, op, right)
        return expr

    def and_expr(self):
        expr = self.equality()
        while self.match("&&"):
            op = "&&"
            right = self.equality()
            expr = Binary(expr, op, right)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.current().type in ("==", "!="):
            op = self.current().type
            self.pos += 1
            right = self.comparison()
            expr = Binary(expr, op, right)
        return expr

    def comparison(self):
        expr = self.term()
        while self.current().type in ("<", ">", "<=", ">="):
            op = self.current().type
            self.pos += 1
            right = self.term()
            expr = Binary(expr, op, right)
        return expr

    def term(self):
        expr = self.factor()
        while self.current().type in ("+", "-"):
            op = self.current().type
            self.pos += 1
            right = self.factor()
            expr = Binary(expr, op, right)
        return expr

    def factor(self):
        expr = self.unary()
        while self.current().type in ("*", "/", "%"):
            op = self.current().type
            self.pos += 1
            right = self.unary()
            expr = Binary(expr, op, right)
        return expr

    def unary(self):
        if self.current().type in ("!", "-"):
            op = self.current().type
            self.pos += 1
            expr = self.unary()
            return Unary(op, expr)
        return self.call()

    def call(self):
        expr = self.primary()

        while self.match("("):
            if not isinstance(expr, Var):
                tok = self.current()
                raise SyntaxError(f"line {tok.line}:{tok.col} 함수 호출 대상이 잘못되었습니다.")

            args = []
            if self.current().type != ")":
                while True:
                    args.append(self.expression())
                    if not self.match(","):
                        break

            self.consume(")", "함수 호출에는 ) 가 필요합니다")
            expr = Call(expr.name, args)

        return expr

    def primary(self):
        if tok := self.match("NUMBER"):
            return Literal(tok.value)

        if tok := self.match("STRING"):
            return Literal(tok.value)

        if self.match("TRUE"):
            return Literal(True)

        if self.match("FALSE"):
            return Literal(False)

        if tok := self.match("IDENT"):
            return Var(tok.value)

        if self.match("("):
            expr = self.expression()
            self.consume(")", "괄호가 닫히지 않았습니다")
            return expr

        tok = self.current()
        raise SyntaxError(f"line {tok.line}:{tok.col} 표현식이 필요합니다. 현재 토큰: {tok.type}")


# =========================
# Interpreter
# =========================

class Environment:
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        self.values[name] = value

    def get(self, name):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"정의되지 않은 변수 또는 함수입니다: {name}")

    def assign(self, name, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeError(f"대입할 수 없는 이름입니다: {name}")


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class UserFunction:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def call(self, interpreter, args):
        if len(args) != len(self.params):
            raise RuntimeError(
                f"함수 {self.name}의 인자 개수가 맞지 않습니다. "
                f"필요: {len(self.params)}, 입력: {len(args)}"
            )

        env = Environment(self.closure)

        for name, value in zip(self.params, args):
            env.define(name, value)

        try:
            interpreter.execute_block(self.body.statements, env)
        except ReturnSignal as r:
            return r.value

        return None


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.env = self.global_env

        self.global_env.define("len", lambda x: len(str(x)))
        self.global_env.define("str", lambda x: str(x))
        self.global_env.define("num", lambda x: float(x))

    def interpret(self, program):
        for stmt in program.statements:
            self.execute(stmt)

    def execute_block(self, statements, env):
        previous = self.env
        self.env = env

        try:
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.env = previous

    def execute(self, stmt):
        if isinstance(stmt, LetStmt):
            value = self.evaluate(stmt.expr)
            self.env.define(stmt.name, value)
            return

        if isinstance(stmt, AssignStmt):
            value = self.evaluate(stmt.expr)
            self.env.assign(stmt.name, value)
            return

        if isinstance(stmt, PrintStmt):
            value = self.evaluate(stmt.expr)
            print(self.stringify(value))
            return

        if isinstance(stmt, IfStmt):
            if self.truthy(self.evaluate(stmt.condition)):
                self.execute_block(stmt.then_block.statements, Environment(self.env))
            elif stmt.else_block:
                self.execute_block(stmt.else_block.statements, Environment(self.env))
            return

        if isinstance(stmt, WhileStmt):
            while self.truthy(self.evaluate(stmt.condition)):
                self.execute_block(stmt.body.statements, Environment(self.env))
            return

        if isinstance(stmt, FuncDef):
            function = UserFunction(stmt.name, stmt.params, stmt.body, self.env)
            self.env.define(stmt.name, function)
            return

        if isinstance(stmt, ReturnStmt):
            value = self.evaluate(stmt.expr)
            raise ReturnSignal(value)

        if isinstance(stmt, ExprStmt):
            self.evaluate(stmt.expr)
            return

        raise RuntimeError(f"알 수 없는 문장입니다: {stmt}")

    def evaluate(self, expr):
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Var):
            return self.env.get(expr.name)

        if isinstance(expr, Unary):
            value = self.evaluate(expr.expr)

            if expr.op == "-":
                return -self.to_number(value)

            if expr.op == "!":
                return not self.truthy(value)

            raise RuntimeError(f"알 수 없는 단항 연산자입니다: {expr.op}")

        if isinstance(expr, Binary):
            if expr.op == "&&":
                return self.truthy(self.evaluate(expr.left)) and self.truthy(self.evaluate(expr.right))

            if expr.op == "||":
                return self.truthy(self.evaluate(expr.left)) or self.truthy(self.evaluate(expr.right))

            left = self.evaluate(expr.left)
            right = self.evaluate(expr.right)

            if expr.op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    return self.stringify(left) + self.stringify(right)
                return self.to_number(left) + self.to_number(right)

            if expr.op == "-":
                return self.to_number(left) - self.to_number(right)

            if expr.op == "*":
                return self.to_number(left) * self.to_number(right)

            if expr.op == "/":
                if self.to_number(right) == 0:
                    raise RuntimeError("0으로 나눌 수 없습니다.")
                return self.to_number(left) / self.to_number(right)

            if expr.op == "%":
                return self.to_number(left) % self.to_number(right)

            if expr.op == "<":
                return self.to_number(left) < self.to_number(right)

            if expr.op == ">":
                return self.to_number(left) > self.to_number(right)

            if expr.op == "<=":
                return self.to_number(left) <= self.to_number(right)

            if expr.op == ">=":
                return self.to_number(left) >= self.to_number(right)

            if expr.op == "==":
                return left == right

            if expr.op == "!=":
                return left != right

            raise RuntimeError(f"알 수 없는 이항 연산자입니다: {expr.op}")

        if isinstance(expr, Call):
            callee = self.env.get(expr.name)
            args = [self.evaluate(arg) for arg in expr.args]

            if isinstance(callee, UserFunction):
                return callee.call(self, args)

            if callable(callee):
                return callee(*args)

            raise RuntimeError(f"{expr.name}은 호출할 수 없습니다.")

        raise RuntimeError(f"알 수 없는 표현식입니다: {expr}")

    def truthy(self, value):
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return True

    def to_number(self, value):
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        raise RuntimeError(f"숫자로 사용할 수 없는 값입니다: {value}")

    def stringify(self, value):
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
        return str(value)


# =========================
# Main
# =========================

def run(source):
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    program = parser.parse()

    interpreter = Interpreter()
    interpreter.interpret(program)


def main():
    if len(sys.argv) != 2:
        print("사용법: python3 ygcompiler.py <source.yg>", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()

        run(source)

    except SyntaxError as e:
        print(f"[Syntax Error] {e}", file=sys.stderr)
        sys.exit(1)

    except RuntimeError as e:
        print(f"[Runtime Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
