# ygcompiler

ygcompiler is a simple programming language implemented with a hand-written Lexer, Recursive Descent Parser, AST, and Interpreter in Python.

## Features

- Variable declaration with let
- Variable assignment
- Arithmetic operations
- Comparison operations
- Logical operations
- if / else statements
- while loops
- print statement
- String values
- Function definition
- Function call
- Return statement
- Recursive function
- Comments using #

## Example

let x = 0;

while x < 5 {
    print(x);
    x = x + 1;
}

if x == 5 {
    print("loop finished");
} else {
    print("error");
}

func add(a, b) {
    return a + b;
}

print(add(10, 20));

func fact(n) {
    if n <= 1 {
        return 1;
    } else {
        return n * fact(n - 1);
    }
}

print(fact(5));

let name = "ygcompiler";
print("language name: " + name);

## How to Run

python3 ygcompiler.py sample.yg

## Output

0
1
2
3
4
loop finished
30
120
language name: ygcompiler

## Files

- ygcompiler.py: source code of the hand-written lexer, parser, AST, and interpreter
- sample.yg: sample program written in ygcompiler language
- output.txt: execution result
- README.md: project description
