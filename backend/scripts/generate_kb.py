# -*- coding: utf-8 -*-
"""Generate python_programming.json knowledge base content for all 51 nodes."""
import json

TOPICS = {
    "py_variable": {
        "title": "变量与赋值",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 变量与赋值\n\n"
            "变量是存储数据值的容器。Python 中变量无需声明类型，赋值时自动确定。\n\n"
            "### 基本概念\n"
            "- 变量名由字母、数字、下划线组成，不能以数字开头\n"
            "- Python 是动态类型语言，变量类型在运行时确定\n"
            "- 使用 = 进行赋值操作\n\n"
            "### 语法要点\n"
            "```python\n"
            "x = 10          # 整数变量\n"
            'name = "Python" # 字符串变量\n'
            "pi = 3.14       # 浮点数变量\n"
            "is_valid = True # 布尔变量\n"
            "\n"
            "# 多重赋值\n"
            "a, b, c = 1, 2, 3\n"
            "x = y = z = 0\n"
            "```\n\n"
            "### 命名规则\n"
            "- 区分大小写（Age 和 age 是不同变量）\n"
            "- 不能使用 Python 关键字（if、for、class 等）\n"
            "- 推荐使用下划线命名法：student_name\n\n"
            "### 常见错误\n"
            "- 使用未定义的变量会报 NameError\n"
            "- 变量名拼写错误是最常见的 bug 来源之一"
        )
    },
    "py_datatype": {
        "title": "数据类型",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 数据类型\n\n"
            "Python 中的基本数据类型包括数字、字符串和布尔值。\n\n"
            "### 数字类型\n"
            "- **int**（整数）：如 10, -5, 0\n"
            "- **float**（浮点数）：如 3.14, -2.5, 1.0e10\n"
            "- **complex**（复数）：如 3+4j\n\n"
            "### 类型转换\n"
            "```python\n"
            "int('123')    # 字符串转整数 -> 123\n"
            "float('3.14') # 字符串转浮点 -> 3.14\n"
            "str(123)      # 整数转字符串 -> '123'\n"
            "bool(0)       # 0转为False\n"
            "bool('hello') # 非空字符串转为True\n"
            "```\n\n"
            "### type() 函数\n"
            "```python\n"
            "type(10)       # <class 'int'>\n"
            "type(3.14)     # <class 'float'>\n"
            "type('hello')  # <class 'str'>\n"
            "type(True)     # <class 'bool'>\n"
            "```\n\n"
            "### 布尔类型\n"
            "- True 或 False（注意首字母大写）\n"
            "- 布尔值可以参与整数运算：True == 1, False == 0"
        )
    },
    "py_operator": {
        "title": "运算符",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 运算符\n\n"
            "运算符用于对变量和值执行操作。\n\n"
            "### 算术运算符\n"
            "- + 加法、- 减法、* 乘法、/ 除法\n"
            "- % 取模（求余数）、** 幂运算、// 整除\n\n"
            "```python\n"
            "10 / 3   # 3.3333...\n"
            "10 // 3  # 3（整除）\n"
            "10 % 3   # 1（取模）\n"
            "2 ** 3   # 8（幂运算）\n"
            "```\n\n"
            "### 比较运算符\n"
            "- == 等于、!= 不等于\n"
            "- > 大于、< 小于、>= 大于等于、<= 小于等于\n\n"
            "### 逻辑运算符\n"
            "- and 与、or 或、not 非\n"
            "- 短路求值：and 遇到 False 停止，or 遇到 True 停止\n\n"
            "### 赋值运算符\n"
            "- = 基本赋值、+= 加法赋值、-= 减法赋值\n"
            "- *=、/=、//=、%=、**= 等"
        )
    },
    "py_io": {
        "title": "输入与输出",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 输入与输出\n\n"
            "Python 使用 input() 接收用户输入，print() 输出内容。\n\n"
            "### input() 函数\n"
            "- 接收用户输入，返回字符串类型\n"
            "- 可传入提示文字参数\n\n"
            "```python\n"
            'name = input("请输入姓名: ")\n'
            'age = int(input("请输入年龄: "))  # 需要手动转换类型\n'
            "```\n\n"
            "### print() 函数\n"
            "```python\n"
            'print("Hello", "World")          # Hello World\n'
            'print("Hello", "World", sep="-") # Hello-World\n'
            'print("Hello", end=" ")          # 不换行\n'
            'print("World")                   # Hello World\n'
            "```\n\n"
            "### f-string 格式化（推荐）\n"
            "```python\n"
            'name = "张三"\n'
            "age = 20\n"
            'print(f"我叫{name}，今年{age}岁")\n'
            "print(f\"pi = {3.14159:.2f}\")  # 保留2位小数\n"
            "```"
        )
    },
    "py_comment": {
        "title": "注释与代码规范",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 注释与代码规范\n\n"
            "注释用于解释代码，Python 解释器会忽略注释内容。\n\n"
            "### 单行注释\n"
            "```python\n"
            "# 这是一个单行注释\n"
            "x = 10  # 行尾注释\n"
            "```\n\n"
            "### 多行注释\n"
            "```python\n"
            "# 第一行注释\n"
            "# 第二行注释\n"
            "```\n\n"
            "### PEP 8 代码规范\n"
            "- 使用4个空格缩进（不要用Tab）\n"
            "- 每行不超过79个字符\n"
            "- 运算符两侧加空格：x = 10 而非 x=10\n"
            "- 函数之间空两行\n\n"
            "### 常见错误\n"
            "- 缩进不一致会导致 IndentationError\n"
            "- 混用 Tab 和空格会导致难以排查的错误"
        )
    },
    "py_string_basic": {
        "title": "字符串基础",
        "chapter": "第1章 Python基础入门",
        "content": (
            "## 字符串基础\n\n"
            "字符串是 Python 中最常用的数据类型之一，用引号创建。\n\n"
            "### 创建字符串\n"
            "```python\n"
            "s1 = 'hello'\n"
            's2 = "world"\n'
            "```\n\n"
            "### 索引与切片\n"
            "```python\n"
            's = "Python"\n'
            "s[0]    # 'P'（正向索引从0开始）\n"
            "s[-1]   # 'n'（反向索引从-1开始）\n"
            "s[0:3]  # 'Pyt'（切片，左闭右开）\n"
            "s[:3]   # 'Pyt'\n"
            "s[3:]   # 'hon'\n"
            "```\n\n"
            "### 常用方法\n"
            "```python\n"
            's = "Hello World"\n'
            "s.lower()       # 'hello world'\n"
            "s.upper()       # 'HELLO WORLD'\n"
            "s.strip()       # 去除首尾空格\n"
            's.replace("o", "0")  # 替换\n'
            's.split(" ")   # [\'Hello\', \'World\']\n'
            "len(s)          # 11\n"
            "'Hello' in s    # True\n"
            "```"
        )
    },
    "py_if": {
        "title": "条件判断if",
        "chapter": "第2章 流程控制",
        "content": (
            "## 条件判断 if\n\n"
            "条件判断是程序根据条件执行不同代码分支的机制。\n\n"
            "### 基本语法\n"
            "```python\n"
            "age = 18\n"
            "if age >= 18:\n"
            '    print("成年")\n'
            "elif age >= 12:\n"
            '    print("青少年")\n'
            "else:\n"
            '    print("儿童")\n'
            "```\n\n"
            "### 三元表达式\n"
            "```python\n"
            'status = "成年" if age >= 18 else "未成年"\n'
            "```\n\n"
            "### 嵌套条件\n"
            "```python\n"
            "if score >= 60:\n"
            "    if score >= 90:\n"
            '        print("优秀")\n'
            "    else:\n"
            '        print("及格")\n'
            "else:\n"
            '    print("不及格")\n'
            "```\n\n"
            "### 常见错误\n"
            "- 忘记写冒号\n"
            "- 缩进不一致\n"
            "- 使用 = 而非 == 进行比较"
        )
    },
    "py_for": {
        "title": "for循环",
        "chapter": "第2章 流程控制",
        "content": (
            "## for 循环\n\n"
            "for 循环用于遍历序列（列表、字符串、range 等）。\n\n"
            "### 基本语法\n"
            "```python\n"
            "for i in range(5):\n"
            "    print(i)  # 输出 0 1 2 3 4\n"
            "\n"
            'for fruit in ["苹果", "香蕉", "橘子"]:\n'
            "    print(fruit)\n"
            "```\n\n"
            "### range() 函数\n"
            "```python\n"
            "range(5)       # 0, 1, 2, 3, 4\n"
            "range(2, 8)   # 2, 3, 4, 5, 6, 7\n"
            "range(0, 10, 2)  # 0, 2, 4, 6, 8\n"
            "```\n\n"
            "### enumerate() 带索引遍历\n"
            "```python\n"
            'fruits = ["苹果", "香蕉"]\n'
            "for i, fruit in enumerate(fruits):\n"
            '    print(f"{i}: {fruit}")\n'
            "```\n\n"
            "### 遍历字典\n"
            "```python\n"
            'd = {"name": "张三", "age": 20}\n'
            "for key, value in d.items():\n"
            '    print(f"{key}: {value}")\n'
            "```"
        )
    },
    "py_while": {
        "title": "while循环",
        "chapter": "第2章 流程控制",
        "content": (
            "## while 循环\n\n"
            "while 循环在条件为真时重复执行代码块。\n\n"
            "### 基本语法\n"
            "```python\n"
            "count = 0\n"
            "while count < 5:\n"
            "    print(count)\n"
            "    count += 1\n"
            "```\n\n"
            "### 循环条件\n"
            "- 条件表达式在每次循环开始前求值\n"
            "- 条件为 False 时循环结束\n\n"
            "### 死循环\n"
            "```python\n"
            "while True:\n"
            "    user_input = input('输入q退出: ')\n"
            "    if user_input == 'q':\n"
            "        break\n"
            "```\n\n"
            "### 常见错误\n"
            "- 忘记更新循环变量导致死循环\n"
            "- 条件永远为 True"
        )
    },
    "py_break_continue": {
        "title": "break与continue",
        "chapter": "第2章 流程控制",
        "content": (
            "## break 与 continue\n\n"
            "break 和 continue 用于控制循环流程。\n\n"
            "### break 跳出循环\n"
            "```python\n"
            "for i in range(10):\n"
            "    if i == 5:\n"
            "        break  # 跳出整个循环\n"
            "    print(i)   # 输出 0 1 2 3 4\n"
            "```\n\n"
            "### continue 跳过当前迭代\n"
            "```python\n"
            "for i in range(10):\n"
            "    if i % 2 == 0:\n"
            "        continue  # 跳过偶数\n"
            "    print(i)      # 输出 1 3 5 7 9\n"
            "```\n\n"
            "### 循环的 else 子句\n"
            "```python\n"
            "for i in range(5):\n"
            "    if i == 10:\n"
            "        break\n"
            "else:\n"
            '    print("循环正常结束")  # 没有被 break 时执行\n'
            "```"
        )
    },
    "py_nested_loop": {
        "title": "嵌套循环",
        "chapter": "第2章 流程控制",
        "content": (
            "## 嵌套循环\n\n"
            "嵌套循环是在一个循环内部再放置一个循环。\n\n"
            "### 基本用法\n"
            "```python\n"
            "# 打印九九乘法表\n"
            "for i in range(1, 10):\n"
            "    for j in range(1, i + 1):\n"
            '        print(f"{j}x{i}={i*j}", end=" ")\n'
            "    print()\n"
            "```\n\n"
            "### 矩阵操作\n"
            "```python\n"
            "matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]\n"
            "for row in matrix:\n"
            "    for elem in row:\n"
            '        print(elem, end=" ")\n'
            "    print()\n"
            "```\n\n"
            "### 循环优化\n"
            "- 尽量减少内层循环的计算量\n"
            "- 使用列表推导替代简单嵌套循环"
        )
    },
    "py_func_def": {
        "title": "函数定义与调用",
        "chapter": "第3章 函数编程",
        "content": (
            "## 函数定义与调用\n\n"
            "函数是可重用的代码块，通过 def 关键字定义。\n\n"
            "### 定义函数\n"
            "```python\n"
            "def greet(name):\n"
            "    # 向用户打招呼\n"
            '    return f"你好，{name}！"\n'
            "\n"
            'result = greet("张三")\n'
            "print(result)  # 你好，张三！\n"
            "```\n\n"
            "### 返回值\n"
            "- return 语句返回结果并结束函数\n"
            "- 没有 return 则返回 None\n"
            "- 可以返回多个值（实际是元组）\n\n"
            "```python\n"
            "def min_max(lst):\n"
            "    return min(lst), max(lst)\n"
            "\n"
            "lo, hi = min_max([3, 1, 4, 1, 5])\n"
            "```\n\n"
            "### 文档字符串\n"
            "- 在函数体第一行用字符串描述函数功能\n"
            "- 可通过 help(func) 查看"
        )
    },
    "py_func_param": {
        "title": "函数参数",
        "chapter": "第3章 函数编程",
        "content": (
            "## 函数参数\n\n"
            "Python 函数支持多种灵活的参数传递方式。\n\n"
            "### 位置参数与关键字参数\n"
            "```python\n"
            "def info(name, age):\n"
            '    print(f"{name}, {age}岁")\n'
            "\n"
            'info("张三", 20)       # 位置参数\n'
            'info(age=20, name="张三") # 关键字参数\n'
            "```\n\n"
            "### 默认参数\n"
            "```python\n"
            "def power(base, exp=2):\n"
            "    return base ** exp\n"
            "\n"
            "power(3)    # 9（使用默认 exp=2）\n"
            "power(3, 3) # 27\n"
            "```\n\n"
            "### *args 和 **kwargs\n"
            "```python\n"
            "def total(*args, **kwargs):\n"
            "    print(args)   # 元组\n"
            "    print(kwargs) # 字典\n"
            "\n"
            "total(1, 2, 3, name='张三', age=20)\n"
            "# (1, 2, 3)\n"
            "# {'name': '张三', 'age': 20}\n"
            "```"
        )
    },
    "py_scope": {
        "title": "作用域与闭包",
        "chapter": "第3章 函数编程",
        "content": (
            "## 作用域与闭包\n\n"
            "作用域决定了变量的可见范围和生命周期。\n\n"
            "### LEGB 规则\n"
            "查找顺序：Local -> Enclosing -> Global -> Built-in\n\n"
            "```python\n"
            'x = "global"\n'
            "\n"
            "def outer():\n"
            '    x = "enclosing"\n'
            "    def inner():\n"
            '        x = "local"\n'
            '        print(x)  # "local"\n'
            "    inner()\n"
            "```\n\n"
            "### global 和 nonlocal\n"
            "```python\n"
            "count = 0\n"
            "def increment():\n"
            "    global count\n"
            "    count += 1\n"
            "\n"
            "def make_counter():\n"
            "    n = 0\n"
            "    def counter():\n"
            "        nonlocal n\n"
            "        n += 1\n"
            "        return n\n"
            "    return counter\n"
            "```\n\n"
            "### 闭包\n"
            "- 内部函数引用外部函数的变量\n"
            "- 外部函数已经返回，变量仍然存在"
        )
    },
    "py_recursive": {
        "title": "递归",
        "chapter": "第3章 函数编程",
        "content": (
            "## 递归\n\n"
            "递归是函数调用自身的编程技巧。\n\n"
            "### 基本要素\n"
            "- **基准条件**：终止递归的条件\n"
            "- **递归步骤**：问题分解为更小的子问题\n\n"
            "### 经典示例\n"
            "```python\n"
            "# 阶乘\n"
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n"
            "\n"
            "# 斐波那契\n"
            "def fib(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    return fib(n-1) + fib(n-2)\n"
            "```\n\n"
            "### 递归深度\n"
            "- Python 默认最大递归深度为 1000\n"
            "- 超过会报 RecursionError\n"
            "- 可通过 sys.setrecursionlimit() 调整"
        )
    },
    "py_lambda": {
        "title": "Lambda与高阶函数",
        "chapter": "第3章 函数编程",
        "content": (
            "## Lambda 与高阶函数\n\n"
            "Lambda 是匿名函数，高阶函数以函数为参数。\n\n"
            "### lambda 表达式\n"
            "```python\n"
            "square = lambda x: x ** 2\n"
            "add = lambda a, b: a + b\n"
            "\n"
            "square(5)    # 25\n"
            "add(3, 4)    # 7\n"
            "```\n\n"
            "### 常用高阶函数\n"
            "```python\n"
            "# map: 对每个元素应用函数\n"
            "list(map(lambda x: x**2, [1,2,3]))  # [1, 4, 9]\n"
            "\n"
            "# filter: 过滤元素\n"
            "list(filter(lambda x: x > 3, [1,2,3,4,5]))  # [4, 5]\n"
            "\n"
            "# sorted: 自定义排序\n"
            "sorted([('a',3),('b',1),('c',2)], key=lambda x: x[1])\n"
            "# [('b', 1), ('c', 2), ('a', 3)]\n"
            "\n"
            "# reduce: 累积计算\n"
            "from functools import reduce\n"
            "reduce(lambda a, b: a + b, [1,2,3,4])  # 10\n"
            "```"
        )
    },
    "py_decorator": {
        "title": "装饰器",
        "chapter": "第3章 函数编程",
        "content": (
            "## 装饰器\n\n"
            "装饰器是修改函数行为的高级技巧，本质是高阶函数。\n\n"
            "### 基本原理\n"
            "```python\n"
            "def timer(func):\n"
            "    import time\n"
            "    def wrapper(*args, **kwargs):\n"
            "        start = time.time()\n"
            "        result = func(*args, **kwargs)\n"
            "        print(f'{func.__name__} 耗时: {time.time()-start:.4f}s')\n"
            "        return result\n"
            "    return wrapper\n"
            "\n"
            "@timer\n"
            "def slow_func():\n"
            "    import time\n"
            "    time.sleep(1)\n"
            "\n"
            "slow_func()  # slow_func 耗时: 1.00xxs\n"
            "```\n\n"
            "### 带参数的装饰器\n"
            "```python\n"
            "def repeat(n):\n"
            "    def decorator(func):\n"
            "        def wrapper(*args):\n"
            "            for _ in range(n):\n"
            "                result = func(*args)\n"
            "            return result\n"
            "        return wrapper\n"
            "    return decorator\n"
            "\n"
            "@repeat(3)\n"
            "def say_hi():\n"
            '    print("Hi!")\n'
            "```"
        )
    },
    "py_list": {
        "title": "列表",
        "chapter": "第4章 数据结构",
        "content": (
            "## 列表\n\n"
            "列表是 Python 中最灵活的数据结构，可存储有序的可变元素集合。\n\n"
            "### 创建列表\n"
            "```python\n"
            "nums = [1, 2, 3, 4, 5]\n"
            'mixed = [1, "hello", True, 3.14]\n'
            "nested = [[1, 2], [3, 4]]\n"
            "```\n\n"
            "### 增删改查\n"
            "```python\n"
            'fruits = ["苹果", "香蕉"]\n'
            'fruits.append("橘子")      # 末尾添加\n'
            'fruits.insert(0, "西瓜")   # 指定位置插入\n'
            'fruits.remove("香蕉")      # 按值删除\n'
            "last = fruits.pop()        # 弹出末尾元素\n"
            'fruits[0] = "草莓"         # 修改元素\n'
            "```\n\n"
            "### 常用方法\n"
            "```python\n"
            "len([1,2,3])     # 3\n"
            "[1,2] + [3,4]    # [1,2,3,4]\n"
            "[1] * 3          # [1,1,1]\n"
            "3 in [1,2,3]     # True\n"
            "sorted([3,1,2])  # [1,2,3]\n"
            "```"
        )
    },
    "py_tuple": {
        "title": "元组",
        "chapter": "第4章 数据结构",
        "content": (
            "## 元组\n\n"
            "元组是不可变的有序序列，一旦创建不能修改。\n\n"
            "### 创建元组\n"
            "```python\n"
            "t = (1, 2, 3)\n"
            "single = (1,)   # 单元素元组必须加逗号\n"
            "empty = ()\n"
            "```\n\n"
            "### 不可变性\n"
            "- 元组创建后不能增删改元素\n"
            "- 适合存储不应改变的数据（如坐标、配置）\n\n"
            "### 解包\n"
            "```python\n"
            "point = (3, 4)\n"
            "x, y = point\n"
            "print(x, y)  # 3 4\n"
            "\n"
            "a, *rest = (1, 2, 3, 4)\n"
            "print(a, rest)  # 1 [2, 3, 4]\n"
            "```\n\n"
            "### 具名元组\n"
            "```python\n"
            "from collections import namedtuple\n"
            "Point = namedtuple('Point', ['x', 'y'])\n"
            "p = Point(3, 4)\n"
            "print(p.x, p.y)  # 3 4\n"
            "```"
        )
    },
    "py_dict": {
        "title": "字典",
        "chapter": "第4章 数据结构",
        "content": (
            "## 字典\n\n"
            "字典是键值对的无序可变集合，通过键快速查找值。\n\n"
            "### 创建字典\n"
            "```python\n"
            'student = {"name": "张三", "age": 20, "score": 95}\n'
            "empty = {}\n"
            "from_dict = dict(name='李四', age=21)\n"
            "```\n\n"
            "### 键值操作\n"
            "```python\n"
            'student["name"]           # "张三"\n'
            'student.get("grade", "无") # "无"（默认值）\n'
            'student["gender"] = "男"   # 添加/修改\n'
            'del student["score"]       # 删除\n'
            "```\n\n"
            "### 遍历\n"
            "```python\n"
            "for key in student:\n"
            "    print(key, student[key])\n"
            "\n"
            "for key, value in student.items():\n"
            '    print(f"{key}: {value}")\n'
            "```\n\n"
            "### 字典推导\n"
            "```python\n"
            "squares = {x: x**2 for x in range(5)}\n"
            "# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}\n"
            "```"
        )
    },
    "py_set": {
        "title": "集合",
        "chapter": "第4章 数据结构",
        "content": (
            "## 集合\n\n"
            "集合是无序且元素唯一的数据结构，支持数学集合运算。\n\n"
            "### 创建集合\n"
            "```python\n"
            "s = {1, 2, 3, 3}  # {1, 2, 3}（自动去重）\n"
            "s = set([1, 2, 2, 3])  # {1, 2, 3}\n"
            "```\n\n"
            "### 集合运算\n"
            "```python\n"
            "a = {1, 2, 3, 4}\n"
            "b = {3, 4, 5, 6}\n"
            "a & b   # {3, 4}  交集\n"
            "a | b   # {1,2,3,4,5,6} 并集\n"
            "a - b   # {1, 2}  差集\n"
            "a ^ b   # {1,2,5,6} 对称差集\n"
            "```\n\n"
            "### 常用操作\n"
            "```python\n"
            "s.add(5)        # 添加元素\n"
            "s.remove(1)     # 删除（不存在报错）\n"
            "s.discard(1)    # 删除（不存在不报错）\n"
            "```"
        )
    },
    "py_slice": {
        "title": "切片操作",
        "chapter": "第4章 数据结构",
        "content": (
            "## 切片操作\n\n"
            "切片用于从序列中提取子序列。\n\n"
            "### 基本语法\n"
            "```python\n"
            "lst = [0, 1, 2, 3, 4, 5]\n"
            "lst[1:4]    # [1, 2, 3]\n"
            "lst[:3]     # [0, 1, 2]\n"
            "lst[3:]     # [3, 4, 5]\n"
            "lst[:]      # 复制整个列表\n"
            "```\n\n"
            "### 步长\n"
            "```python\n"
            "lst[::2]    # [0, 2, 4]（每隔一个取）\n"
            "lst[::-1]   # [5, 4, 3, 2, 1, 0]（反转）\n"
            "lst[1::2]   # [1, 3, 5]\n"
            "```\n\n"
            "### 负索引\n"
            "```python\n"
            "lst[-1]     # 5（最后一个）\n"
            "lst[-3:]    # [3, 4, 5]\n"
            "lst[-3:-1]  # [3, 4]\n"
            "```\n\n"
            "### 切片赋值\n"
            "```python\n"
            "lst[1:3] = [10, 20, 30]  # 替换指定范围\n"
            "```"
        )
    },
    "py_comprehension": {
        "title": "推导式",
        "chapter": "第4章 数据结构",
        "content": (
            "## 推导式\n\n"
            "推导式是 Python 中简洁创建序列的方式。\n\n"
            "### 列表推导\n"
            "```python\n"
            "squares = [x**2 for x in range(10)]\n"
            "evens = [x for x in range(20) if x % 2 == 0]\n"
            "```\n\n"
            "### 字典推导\n"
            "```python\n"
            'word_len = {w: len(w) for w in ["hello", "world"]}\n'
            "# {'hello': 5, 'world': 5}\n"
            "```\n\n"
            "### 集合推导\n"
            "```python\n"
            'unique_lens = {len(w) for w in ["hi", "hey", "hello"]}\n'
            "# {2, 3, 5}\n"
            "```\n\n"
            "### 嵌套推导\n"
            "```python\n"
            "matrix = [[1,2],[3,4],[5,6]]\n"
            "flat = [x for row in matrix for x in row]\n"
            "# [1, 2, 3, 4, 5, 6]\n"
            "```"
        )
    },
    "py_string_adv": {
        "title": "字符串进阶",
        "chapter": "第4章 数据结构",
        "content": (
            "## 字符串进阶\n\n"
            "字符串高级操作包括格式化、编码处理等。\n\n"
            "### 格式化方法\n"
            "```python\n"
            "# format 方法\n"
            '"{} + {} = {}".format(1, 2, 3)\n'
            '"{name}今年{age}岁".format(name="张三", age=20)\n'
            "\n"
            "# f-string（推荐）\n"
            'name = "张三"\n'
            'f"{name:=^10}"  # 居中填充\n'
            'f"{3.14159:.2f}" # 3.14\n'
            "```\n\n"
            "### 常用方法\n"
            "```python\n"
            's = "Hello, World!"\n'
            's.startswith("Hello")  # True\n'
            's.endswith("!")        # True\n'
            's.find("World")        # 7\n'
            "s.count('l')          # 3\n"
            "s.zfill(15)           # 左侧补零\n"
            "```\n\n"
            "### 编码\n"
            "```python\n"
            's = "你好"\n'
            "s.encode('utf-8')      # 编码为字节\n"
            "b = s.encode('utf-8')\n"
            "b.decode('utf-8')      # 解码为字符串\n"
            "```"
        )
    },
    "py_file_read": {
        "title": "文件读写",
        "chapter": "第5章 文件与异常",
        "content": (
            "## 文件读写\n\n"
            "文件操作是 Python 与外部数据交互的基本方式。\n\n"
            "### 读取文件\n"
            "```python\n"
            '# 读取整个文件\n'
            'with open("data.txt", "r", encoding="utf-8") as f:\n'
            "    content = f.read()\n"
            "\n"
            "# 逐行读取\n"
            'with open("data.txt", "r", encoding="utf-8") as f:\n'
            "    for line in f:\n"
            "        print(line.strip())\n"
            "```\n\n"
            "### 写入文件\n"
            "```python\n"
            "# 覆盖写入\n"
            'with open("output.txt", "w", encoding="utf-8") as f:\n'
            '    f.write("Hello World\\n")\n'
            "\n"
            "# 追加写入\n"
            'with open("output.txt", "a", encoding="utf-8") as f:\n'
            '    f.write("追加内容\\n")\n'
            "```\n\n"
            "### 文件模式\n"
            "- 'r' 只读、'w' 写入（覆盖）、'a' 追加\n"
            "- 'rb' 二进制读、'wb' 二进制写"
        )
    },
    "py_with": {
        "title": "with上下文管理",
        "chapter": "第5章 文件与异常",
        "content": (
            "## with 上下文管理\n\n"
            "with 语句确保资源在使用后正确释放。\n\n"
            "### 基本用法\n"
            "```python\n"
            'with open("data.txt", "r") as f:\n'
            "    content = f.read()\n"
            "# 文件自动关闭，即使发生异常\n"
            "```\n\n"
            "### 等价于\n"
            "```python\n"
            'f = open("data.txt", "r")\n'
            "try:\n"
            "    content = f.read()\n"
            "finally:\n"
            "    f.close()\n"
            "```\n\n"
            "### 多个上下文\n"
            "```python\n"
            'with open("input.txt") as fin, open("output.txt", "w") as fout:\n'
            "    fout.write(fin.read())\n"
            "```"
        )
    },
    "py_try_except": {
        "title": "异常处理",
        "chapter": "第5章 文件与异常",
        "content": (
            "## 异常处理\n\n"
            "异常处理让程序在出错时优雅地恢复或报告。\n\n"
            "### 基本语法\n"
            "```python\n"
            "try:\n"
            "    result = 10 / 0\n"
            "except ZeroDivisionError:\n"
            '    print("不能除以零")\n'
            "except (TypeError, ValueError) as e:\n"
            '    print(f"类型或值错误: {e}")\n'
            "else:\n"
            '    print("没有异常时执行")\n'
            "finally:\n"
            '    print("始终执行")\n'
            "```\n\n"
            "### 常见异常类型\n"
            "- ValueError：值不正确\n"
            "- TypeError：类型不匹配\n"
            "- KeyError：字典键不存在\n"
            "- IndexError：索引越界\n"
            "- FileNotFoundError：文件不存在\n"
            "- ZeroDivisionError：除以零"
        )
    },
    "py_custom_exception": {
        "title": "自定义异常",
        "chapter": "第5章 文件与异常",
        "content": (
            "## 自定义异常\n\n"
            "自定义异常用于表达业务特定的错误情况。\n\n"
            "### 定义异常类\n"
            "```python\n"
            "class AppError(Exception):\n"
            "    # 应用基础异常\n"
            "    pass\n"
            "\n"
            "class ValidationError(AppError):\n"
            "    def __init__(self, field, message):\n"
            "        self.field = field\n"
            "        self.message = message\n"
            '        super().__init__(f"{field}: {message}")\n'
            "\n"
            "# 使用\n"
            "try:\n"
            '    raise ValidationError("age", "年龄必须大于0")\n'
            "except ValidationError as e:\n"
            "    print(e)\n"
            "```\n\n"
            "### raise from 链式异常\n"
            "```python\n"
            "try:\n"
            '    int("abc")\n'
            "except ValueError as e:\n"
            '    raise ValidationError("value", "无效数值") from e\n'
            "```"
        )
    },
    "py_class": {
        "title": "类与对象",
        "chapter": "第6章 面向对象",
        "content": (
            "## 类与对象\n\n"
            "类是面向对象编程的核心，用于创建自定义数据类型。\n\n"
            "### 定义类\n"
            "```python\n"
            "class Student:\n"
            "    def __init__(self, name, age):\n"
            "        self.name = name  # 实例属性\n"
            "        self.age = age\n"
            "\n"
            "    def introduce(self):  # 实例方法\n"
            '        return f"我是{self.name}，今年{self.age}岁"\n'
            "\n"
            's = Student("张三", 20)\n'
            "print(s.introduce())\n"
            "```\n\n"
            "### self 关键字\n"
            "- 指向当前实例对象\n"
            "- 在方法中通过 self 访问属性和其他方法\n"
            "- 类似其他语言的 this"
        )
    },
    "py_inherit": {
        "title": "继承",
        "chapter": "第6章 面向对象",
        "content": (
            "## 继承\n\n"
            "继承允许子类复用父类的属性和方法。\n\n"
            "### 基本继承\n"
            "```python\n"
            "class Animal:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n"
            "\n"
            "    def speak(self):\n"
            '        return "..."\n'
            "\n"
            "class Dog(Animal):\n"
            "    def speak(self):  # 方法重写\n"
            '        return "汪汪！"\n'
            "\n"
            "class Cat(Animal):\n"
            "    def speak(self):\n"
            '        return "喵喵！"\n'
            "```\n\n"
            "### super() 调用父类\n"
            "```python\n"
            "class Student(Person):\n"
            "    def __init__(self, name, age, school):\n"
            "        super().__init__(name, age)\n"
            "        self.school = school\n"
            "```"
        )
    },
    "py_encapsulation": {
        "title": "封装",
        "chapter": "第6章 面向对象",
        "content": (
            "## 封装\n\n"
            "封装隐藏对象内部实现细节，只暴露必要的接口。\n\n"
            "### 私有属性\n"
            "```python\n"
            "class BankAccount:\n"
            "    def __init__(self, owner, balance=0):\n"
            "        self.owner = owner\n"
            "        self.__balance = balance  # 私有属性\n"
            "\n"
            "    @property\n"
            "    def balance(self):\n"
            "        return self.__balance\n"
            "\n"
            "    @balance.setter\n"
            "    def balance(self, amount):\n"
            "        if amount < 0:\n"
            '            raise ValueError("余额不能为负")\n'
            "        self.__balance = amount\n"
            "```\n\n"
            "### 命名约定\n"
            "- _var：受保护（约定，不强制）\n"
            "- __var：私有（名称修饰）"
        )
    },
    "py_polymorphism": {
        "title": "多态",
        "chapter": "第6章 面向对象",
        "content": (
            "## 多态\n\n"
            "多态允许不同类型的对象对同一消息做出不同响应。\n\n"
            "### 鸭子类型\n"
            "```python\n"
            "class Dog:\n"
            '    def speak(self): return "汪汪"\n'
            "\n"
            "class Cat:\n"
            '    def speak(self): return "喵喵"\n'
            "\n"
            "def make_sound(animal):\n"
            "    print(animal.speak())  # 不关心具体类型\n"
            "\n"
            'make_sound(Dog())  # 汪汪\n'
            'make_sound(Cat())  # 喵喵\n'
            "```\n\n"
            "### 抽象基类\n"
            "```python\n"
            "from abc import ABC, abstractmethod\n"
            "\n"
            "class Shape(ABC):\n"
            "    @abstractmethod\n"
            "    def area(self):\n"
            "        pass\n"
            "\n"
            "class Circle(Shape):\n"
            "    def __init__(self, r):\n"
            "        self.r = r\n"
            "    def area(self):\n"
            "        return 3.14 * self.r ** 2\n"
            "```"
        )
    },
    "py_magic_method": {
        "title": "魔术方法",
        "chapter": "第6章 面向对象",
        "content": (
            "## 魔术方法\n\n"
            "魔术方法让自定义类支持 Python 内置操作。\n\n"
            "### 常用魔术方法\n"
            "```python\n"
            "class Vector:\n"
            "    def __init__(self, x, y):\n"
            "        self.x = x\n"
            "        self.y = y\n"
            "\n"
            "    def __str__(self):\n"
            '        return f"Vector({self.x}, {self.y})"\n'
            "\n"
            "    def __add__(self, other):\n"
            "        return Vector(self.x + other.x, self.y + other.y)\n"
            "\n"
            "    def __len__(self):\n"
            "        return 2\n"
            "\n"
            "    def __eq__(self, other):\n"
            "        return self.x == other.x and self.y == other.y\n"
            "```\n\n"
            "### 运算符重载\n"
            "- __add__ -> +, __sub__ -> -, __mul__ -> *\n"
            "- __getitem__ -> [], __contains__ -> in"
        )
    },
    "py_classmethod": {
        "title": "类方法与静态方法",
        "chapter": "第6章 面向对象",
        "content": (
            "## 类方法与静态方法\n\n"
            "类方法和静态方法不需要实例化即可调用。\n\n"
            "### 类方法\n"
            "```python\n"
            "class Date:\n"
            "    def __init__(self, year, month, day):\n"
            "        self.year = year\n"
            "        self.month = month\n"
            "        self.day = day\n"
            "\n"
            "    @classmethod\n"
            "    def from_string(cls, date_str):\n"
            '        y, m, d = date_str.split("-")\n'
            "        return cls(int(y), int(m), int(d))\n"
            "\n"
            'd = Date.from_string("2026-01-15")\n'
            "```\n\n"
            "### 静态方法\n"
            "```python\n"
            "class Math:\n"
            "    @staticmethod\n"
            "    def add(a, b):\n"
            "        return a + b\n"
            "```"
        )
    },
    "py_import": {
        "title": "模块导入",
        "chapter": "第7章 模块与包",
        "content": (
            "## 模块导入\n\n"
            "模块是组织 Python 代码的基本单位。\n\n"
            "### 导入方式\n"
            "```python\n"
            "import math\n"
            "math.sqrt(16)  # 4.0\n"
            "\n"
            "from math import sqrt\n"
            "sqrt(16)  # 4.0\n"
            "\n"
            "from math import sqrt as s\n"
            "s(16)  # 4.0\n"
            "```\n\n"
            "### __name__ 检测\n"
            "```python\n"
            "# mymodule.py\n"
            "def main():\n"
            '    print("运行主程序")\n'
            "\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
            "```"
        )
    },
    "py_package": {
        "title": "包与虚拟环境",
        "chapter": "第7章 模块与包",
        "content": (
            "## 包与虚拟环境\n\n"
            "包是模块的集合，虚拟环境隔离项目依赖。\n\n"
            "### 包结构\n"
            "```\n"
            "mypackage/\n"
            "    __init__.py\n"
            "    module1.py\n"
            "    module2.py\n"
            "    subpackage/\n"
            "        __init__.py\n"
            "        module3.py\n"
            "```\n\n"
            "### 虚拟环境\n"
            "```bash\n"
            "python -m venv myenv\n"
            "myenv\\Scripts\\activate   # Windows\n"
            "source myenv/bin/activate  # Linux/Mac\n"
            "pip install package_name\n"
            "pip freeze > requirements.txt\n"
            "```"
        )
    },
    "py_pip": {
        "title": "第三方库管理",
        "chapter": "第7章 模块与包",
        "content": (
            "## 第三方库管理\n\n"
            "pip 是 Python 的包管理工具。\n\n"
            "### 基本操作\n"
            "```bash\n"
            "pip install requests       # 安装\n"
            "pip uninstall requests     # 卸载\n"
            "pip list                   # 列出已安装\n"
            "pip show requests          # 查看详情\n"
            "pip install -r requirements.txt  # 批量安装\n"
            "```\n\n"
            "### requirements.txt\n"
            "```\n"
            "requests==2.31.0\n"
            "flask>=3.0\n"
            "numpy\n"
            "```\n\n"
            "### 常用第三方库\n"
            "- requests：HTTP 请求\n"
            "- flask/fastapi：Web 框架\n"
            "- numpy/pandas：数据处理\n"
            "- matplotlib：数据可视化"
        )
    },
    "py_generator": {
        "title": "生成器",
        "chapter": "第8章 高级特性",
        "content": (
            "## 生成器\n\n"
            "生成器是惰性求值的迭代器，按需产生值。\n\n"
            "### yield 关键字\n"
            "```python\n"
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        yield a\n"
            "        a, b = b, a + b\n"
            "\n"
            "for num in fibonacci(10):\n"
            '    print(num, end=" ")  # 0 1 1 2 3 5 8 13 21 34\n'
            "```\n\n"
            "### 生成器表达式\n"
            "```python\n"
            "squares = (x**2 for x in range(1000000))\n"
            "# 不会一次性占用内存\n"
            "next(squares)  # 0\n"
            "next(squares)  # 1\n"
            "```\n\n"
            "### 优势\n"
            "- 惰性计算，节省内存\n"
            "- 适合处理大量数据"
        )
    },
    "py_iterator": {
        "title": "迭代器",
        "chapter": "第8章 高级特性",
        "content": (
            "## 迭代器\n\n"
            "迭代器是实现迭代器协议的对象。\n\n"
            "### 迭代器协议\n"
            "```python\n"
            "class CountDown:\n"
            "    def __init__(self, n):\n"
            "        self.n = n\n"
            "\n"
            "    def __iter__(self):\n"
            "        return self\n"
            "\n"
            "    def __next__(self):\n"
            "        if self.n <= 0:\n"
            "            raise StopIteration\n"
            "        self.n -= 1\n"
            "        return self.n + 1\n"
            "\n"
            "for i in CountDown(5):\n"
            "    print(i)  # 5 4 3 2 1\n"
            "```\n\n"
            "### iter() 和 next()\n"
            "```python\n"
            "it = iter([1, 2, 3])\n"
            "next(it)  # 1\n"
            "next(it)  # 2\n"
            "next(it)  # 3\n"
            "next(it)  # StopIteration\n"
            "```"
        )
    },
    "py_contextmanager": {
        "title": "上下文管理器",
        "chapter": "第8章 高级特性",
        "content": (
            "## 上下文管理器\n\n"
            "上下文管理器用于管理资源的获取和释放。\n\n"
            "### 使用 contextlib\n"
            "```python\n"
            "from contextlib import contextmanager\n"
            "\n"
            "@contextmanager\n"
            "def timer(label):\n"
            "    import time\n"
            "    start = time.time()\n"
            "    yield\n"
            "    print(f'{label}: {time.time()-start:.4f}s')\n"
            "\n"
            'with timer("操作"):\n'
            "    sum(range(1000000))\n"
            "```\n\n"
            "### 自定义上下文管理器\n"
            "```python\n"
            "class DatabaseConnection:\n"
            "    def __enter__(self):\n"
            "        self.conn = create_connection()\n"
            "        return self.conn\n"
            "    def __exit__(self, exc_type, exc_val, exc_tb):\n"
            "        self.conn.close()\n"
            "```"
        )
    },
    "py_regex": {
        "title": "正则表达式",
        "chapter": "第8章 高级特性",
        "content": (
            "## 正则表达式\n\n"
            "正则表达式用于文本模式匹配和替换。\n\n"
            "### 基本使用\n"
            "```python\n"
            "import re\n"
            "\n"
            "# 搜索\n"
            "re.search(r'\\d+', 'abc123def')  # 匹配 '123'\n"
            "\n"
            "# 查找所有\n"
            "re.findall(r'\\d+', 'a1b22c333')  # ['1', '22', '333']\n"
            "\n"
            "# 替换\n"
            "re.sub(r'\\d+', 'X', 'a1b22c333')  # 'aXbXcX'\n"
            "\n"
            "# 分割\n"
            "re.split(r'[,;]', 'a,b;c,d')  # ['a', 'b', 'c', 'd']\n"
            "```\n\n"
            "### 常用模式\n"
            "- \\d 数字、\\w 字母数字下划线、\\s 空白\n"
            "- . 任意字符、* 零次或多次、+ 一次或多次\n"
            "- ^ 开头、$ 结尾、[] 字符集"
        )
    },
    "py_itertools": {
        "title": "itertools工具库",
        "chapter": "第8章 高级特性",
        "content": (
            "## itertools 工具库\n\n"
            "itertools 提供高效的迭代器工具函数。\n\n"
            "### 常用函数\n"
            "```python\n"
            "from itertools import chain, product, permutations, combinations, groupby\n"
            "\n"
            "# chain: 连接多个迭代器\n"
            "list(chain([1,2], [3,4]))  # [1, 2, 3, 4]\n"
            "\n"
            "# product: 笛卡尔积\n"
            "list(product('AB', '12'))  # [('A','1'),('A','2'),('B','1'),('B','2')]\n"
            "\n"
            "# permutations: 排列\n"
            "list(permutations('ABC', 2))  # [('A','B'),('A','C'),...]\n"
            "\n"
            "# combinations: 组合\n"
            "list(combinations('ABC', 2))  # [('A','B'),('A','C'),('B','C')]\n"
            "\n"
            "# groupby: 分组\n"
            "data = sorted([('A',1),('B',2),('A',3)], key=lambda x: x[0])\n"
            "for key, group in groupby(data, key=lambda x: x[0]):\n"
            "    print(key, list(group))\n"
            "```"
        )
    },
    "py_numpy": {
        "title": "NumPy基础",
        "chapter": "第9章 数据科学",
        "content": (
            "## NumPy 基础\n\n"
            "NumPy 是 Python 科学计算的基础库。\n\n"
            "### 创建数组\n"
            "```python\n"
            "import numpy as np\n"
            "\n"
            "a = np.array([1, 2, 3, 4])\n"
            "b = np.zeros((3, 4))   # 3x4 零矩阵\n"
            "c = np.ones((2, 3))    # 2x3 全1矩阵\n"
            "d = np.arange(0, 10, 2)  # [0, 2, 4, 6, 8]\n"
            "```\n\n"
            "### 数组运算\n"
            "```python\n"
            "a = np.array([1, 2, 3])\n"
            "a * 2        # [2, 4, 6]\n"
            "a + 10       # [11, 12, 13]\n"
            "a.sum()      # 6\n"
            "a.mean()     # 2.0\n"
            "a.reshape(3, 1)\n"
            "```\n\n"
            "### 广播机制\n"
            "```python\n"
            "a = np.array([[1], [2], [3]])  # 3x1\n"
            "b = np.array([10, 20, 30])     # 1x3\n"
            "a + b  # 3x3 矩阵\n"
            "```"
        )
    },
    "py_pandas": {
        "title": "Pandas基础",
        "chapter": "第9章 数据科学",
        "content": (
            "## Pandas 基础\n\n"
            "Pandas 是数据分析的核心库。\n\n"
            "### 创建 DataFrame\n"
            "```python\n"
            "import pandas as pd\n"
            "\n"
            "df = pd.DataFrame({\n"
            '    "name": ["张三", "李四", "王五"],\n'
            '    "age": [20, 21, 19],\n'
            '    "score": [85, 92, 78]\n'
            "})\n"
            "```\n\n"
            "### 数据选取\n"
            "```python\n"
            'df["name"]            # 选取列\n'
            'df[df["age"] > 19]    # 条件筛选\n'
            "df.iloc[0]            # 按位置选取\n"
            'df.loc[0, "name"]     # 按标签选取\n'
            "```\n\n"
            "### 聚合操作\n"
            "```python\n"
            'df["score"].mean()    # 平均分\n'
            'df.groupby("age")["score"].mean()  # 分组聚合\n'
            'df.sort_values("score", ascending=False)  # 排序\n'
            "```"
        )
    },
    "py_data_clean": {
        "title": "数据清洗",
        "chapter": "第9章 数据科学",
        "content": (
            "## 数据清洗\n\n"
            "数据清洗是数据分析的必要步骤。\n\n"
            "### 缺失值处理\n"
            "```python\n"
            "import pandas as pd\n"
            "\n"
            'df = pd.DataFrame({"A": [1, None, 3], "B": [4, 5, None]})\n'
            "\n"
            "df.isnull()           # 检测缺失值\n"
            "df.dropna()           # 删除含缺失值的行\n"
            "df.fillna(0)          # 用0填充\n"
            'df["A"].fillna(df["A"].mean())  # 用均值填充\n'
            "```\n\n"
            "### 重复值处理\n"
            "```python\n"
            "df.duplicated()       # 检测重复行\n"
            "df.drop_duplicates()  # 删除重复行\n"
            "```\n\n"
            "### 类型转换\n"
            "```python\n"
            'df["age"] = df["age"].astype(int)\n'
            "pd.to_datetime('2026-01-15')\n"
            "```"
        )
    },
    "py_visual": {
        "title": "数据可视化",
        "chapter": "第9章 数据科学",
        "content": (
            "## 数据可视化\n\n"
            "matplotlib 是 Python 最基础的可视化库。\n\n"
            "### 折线图\n"
            "```python\n"
            "import matplotlib.pyplot as plt\n"
            "\n"
            "x = [1, 2, 3, 4, 5]\n"
            "y = [2, 4, 6, 8, 10]\n"
            'plt.plot(x, y, label="趋势")\n'
            'plt.xlabel("X轴")\n'
            'plt.ylabel("Y轴")\n'
            'plt.title("折线图示例")\n'
            "plt.legend()\n"
            'plt.savefig("chart.png")\n'
            "```\n\n"
            "### 柱状图\n"
            "```python\n"
            'names = ["张三", "李四", "王五"]\n'
            "scores = [85, 92, 78]\n"
            "plt.bar(names, scores)\n"
            'plt.title("成绩对比")\n'
            "```\n\n"
            "### 散点图\n"
            "```python\n"
            "plt.scatter(x, y, c='red', s=50)\n"
            "```"
        )
    },
    "py_csv_json": {
        "title": "CSV与JSON处理",
        "chapter": "第9章 数据科学",
        "content": (
            "## CSV 与 JSON 处理\n\n"
            "CSV 和 JSON 是常见的数据交换格式。\n\n"
            "### CSV 处理\n"
            "```python\n"
            "import csv\n"
            "\n"
            "# 读取 CSV\n"
            'with open("data.csv", "r", encoding="utf-8") as f:\n'
            "    reader = csv.DictReader(f)\n"
            "    for row in reader:\n"
            '        print(row["name"], row["score"])\n'
            "\n"
            "# 写入 CSV\n"
            'with open("output.csv", "w", newline="", encoding="utf-8") as f:\n'
            '    writer = csv.DictWriter(f, fieldnames=["name", "score"])\n'
            "    writer.writeheader()\n"
            '    writer.writerow({"name": "张三", "score": 95})\n'
            "```\n\n"
            "### JSON 处理\n"
            "```python\n"
            "import json\n"
            "\n"
            'data = {"name": "张三", "scores": [85, 92, 78]}\n'
            "json_str = json.dumps(data, ensure_ascii=False)\n"
            "parsed = json.loads(json_str)\n"
            "```"
        )
    },
    "py_project": {
        "title": "项目结构",
        "chapter": "第10章 综合实战",
        "content": (
            "## 项目结构\n\n"
            "良好的项目结构是可维护代码的基础。\n\n"
            "### 推荐结构\n"
            "```\n"
            "myproject/\n"
            "    README.md\n"
            "    requirements.txt\n"
            "    config.py\n"
            "    main.py\n"
            "    mypackage/\n"
            "        __init__.py\n"
            "        models.py\n"
            "        services.py\n"
            "        utils.py\n"
            "    tests/\n"
            "        test_models.py\n"
            "```\n\n"
            "### __main__ 入口\n"
            "```python\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
            "```\n\n"
            "### 日志记录\n"
            "```python\n"
            "import logging\n"
            "logging.basicConfig(level=logging.INFO)\n"
            "logger = logging.getLogger(__name__)\n"
            'logger.info("程序启动")\n'
            "```"
        )
    },
    "py_debug": {
        "title": "调试技巧",
        "chapter": "第10章 综合实战",
        "content": (
            "## 调试技巧\n\n"
            "调试是定位和修复程序错误的过程。\n\n"
            "### print 调试\n"
            "```python\n"
            "def calculate(a, b):\n"
            '    print(f"a={a}, b={b}")  # 调试输出\n'
            "    result = a / b\n"
            '    print(f"result={result}")\n'
            "    return result\n"
            "```\n\n"
            "### pdb 调试器\n"
            "```python\n"
            "import pdb\n"
            "def buggy_func(x):\n"
            "    pdb.set_trace()  # 设置断点\n"
            "    y = x * 2\n"
            "    return y / 0\n"
            "```\n\n"
            "### logging 模块\n"
            "```python\n"
            "import logging\n"
            "logging.basicConfig(level=logging.DEBUG)\n"
            'logging.debug("调试信息")\n'
            'logging.info("普通信息")\n'
            'logging.warning("警告")\n'
            'logging.error("错误")\n'
            "```"
        )
    },
    "py_test": {
        "title": "单元测试",
        "chapter": "第10章 综合实战",
        "content": (
            "## 单元测试\n\n"
            "单元测试确保代码按预期工作。\n\n"
            "### unittest\n"
            "```python\n"
            "import unittest\n"
            "\n"
            "class TestMath(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(1 + 1, 2)\n"
            "        self.assertTrue(3 > 2)\n"
            "\n"
            "    def test_divide(self):\n"
            "        with self.assertRaises(ZeroDivisionError):\n"
            "            1 / 0\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    unittest.main()\n"
            "```\n\n"
            "### pytest（推荐）\n"
            "```python\n"
            "def test_add():\n"
            "    assert 1 + 1 == 2\n"
            "\n"
            "def test_list():\n"
            "    assert len([1, 2, 3]) == 3\n"
            "```\n\n"
            "### 运行测试\n"
            "```bash\n"
            "pytest tests/ -v       # 详细输出\n"
            "pytest --cov=. tests/  # 覆盖率报告\n"
            "```"
        )
    },
    "py_api": {
        "title": "API基础",
        "chapter": "第10章 综合实战",
        "content": (
            "## API 基础\n\n"
            "API 交互是现代应用开发的基本技能。\n\n"
            "### requests 库\n"
            "```python\n"
            "import requests\n"
            "\n"
            "# GET 请求\n"
            'resp = requests.get("https://api.example.com/users")\n'
            "data = resp.json()\n"
            "\n"
            "# POST 请求\n"
            "resp = requests.post(\n"
            '    "https://api.example.com/users",\n'
            '    json={"name": "张三", "age": 20}\n'
            ")\n"
            "\n"
            "# 处理响应\n"
            "print(resp.status_code)  # 200\n"
            'print(resp.headers["Content-Type"])\n'
            "```\n\n"
            "### 错误处理\n"
            "```python\n"
            "try:\n"
            "    resp = requests.get(url, timeout=5)\n"
            "    resp.raise_for_status()\n"
            "except requests.RequestException as e:\n"
            '    print(f"请求失败: {e}")\n'
            "```"
        )
    },
}


def main():
    # Load graph to get node metadata
    with open("data/knowledge_bases/knowledge_graph.json", "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes = graph["python_programming"]["nodes"]
    result = {}

    missing = []
    for node in nodes:
        nid = node["id"]
        if nid in TOPICS:
            result[nid] = {
                "title": TOPICS[nid]["title"],
                "chapter": TOPICS[nid]["chapter"],
                "content": TOPICS[nid]["content"],
            }
        else:
            missing.append(nid)
            result[nid] = {
                "title": node["name"],
                "chapter": node["chapter"],
                "content": f"## {node['name']}\n\n{node['description']}",
            }

    with open("data/knowledge_bases/python_programming.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(result)} topic entries")
    if missing:
        print(f"WARNING: Missing detailed content for: {missing}")
    else:
        print("All 51 nodes have detailed content!")

    # Verify content lengths
    short = [nid for nid, t in result.items() if len(t["content"]) < 200]
    if short:
        print(f"Short entries (<200 chars): {short}")


if __name__ == "__main__":
    main()
