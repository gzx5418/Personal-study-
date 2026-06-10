"""从菜鸟教程抓取 Python3 教程内容，生成知识库和知识图谱。"""

import json
import os
import re
import time
import sys

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.runoob.com/python3/"

# 基础教程页面（按学习顺序排列）
BASIC_PAGES = [
    ("py_intro", "Python3 简介", "python3-intro.html", "第0章 准备", 1),
    ("py_install", "Python3 环境搭建", "python3-install.html", "第0章 准备", 1),
    ("py_basic_syntax", "Python3 基础语法", "python3-basic-syntax.html", "第1章 基础语法", 1),
    ("py_variable", "变量与赋值", "python3-basic-syntax.html", "第1章 基础语法", 1),
    ("py_datatype", "基本数据类型", "python3-data-type.html", "第1章 基础语法", 1),
    ("py_type_cast", "数据类型转换", "python3-type-conversion.html", "第1章 基础语法", 1),
    ("py_comment", "注释", "python3-comment.html", "第1章 基础语法", 1),
    ("py_operator", "运算符", "python3-basic-operators.html", "第1章 基础语法", 2),
    ("py_number", "数字", "python3-number.html", "第2章 数据类型", 1),
    ("py_string_basic", "字符串基础", "python3-string.html", "第2章 数据类型", 1),
    ("py_string_adv", "字符串进阶", "python3-string.html", "第2章 数据类型", 2),
    ("py_list", "列表", "python3-list.html", "第2章 数据类型", 2),
    ("py_tuple", "元组", "python3-tuple.html", "第2章 数据类型", 2),
    ("py_dict", "字典", "python3-dictionary.html", "第2章 数据类型", 2),
    ("py_set", "集合", "python3-set.html", "第2章 数据类型", 3),
    ("py_if", "条件控制 if", "python3-if-statement.html", "第3章 流程控制", 2),
    ("py_for", "for 循环", "python3-loop.html", "第3章 流程控制", 2),
    ("py_while", "while 循环", "python3-loop.html", "第3章 流程控制", 2),
    ("py_break_continue", "break 与 continue", "python3-loop.html", "第3章 流程控制", 3),
    ("py_comprehension", "推导式", "python3-data-structure.html", "第3章 流程控制", 3),
    ("py_func_def", "函数定义", "python3-function.html", "第4章 函数", 2),
    ("py_func_param", "函数参数", "python3-function.html", "第4章 函数", 3),
    ("py_lambda", "Lambda 表达式", "python3-function.html", "第4章 函数", 3),
    ("py_decorator", "装饰器", "python-decorators.html", "第4章 函数", 4),
    ("py_scope", "变量作用域", "python3-namespace-scope.html", "第4章 函数", 3),
    ("py_iterator", "迭代器", "python3-iterator-generator.html", "第5章 高级特性", 3),
    ("py_generator", "生成器", "python3-iterator-generator.html", "第5章 高级特性", 3),
    ("py_with", "with 语句", "python3-with-keyword.html", "第5章 高级特性", 3),
    ("py_module", "模块与导入", "python3-module.html", "第6章 模块与包", 2),
    ("py_package", "包", "python3-module.html", "第6章 模块与包", 3),
    ("py_io", "输入与输出", "python3-inputoutput.html", "第6章 模块与包", 2),
    ("py_file_read", "文件操作", "python3-file-methods.html", "第6章 模块与包", 3),
    ("py_try_except", "异常处理", "python3-errors-execptions.html", "第7章 面向对象", 3),
    ("py_class", "类与对象", "python3-class.html", "第7章 面向对象", 3),
    ("py_inherit", "继承", "python3-class.html", "第7章 面向对象", 3),
    ("py_encapsulation", "封装", "python3-class.html", "第7章 面向对象", 4),
    ("py_polymorphism", "多态", "python3-class.html", "第7章 面向对象", 4),
]

# 高级教程页面
ADVANCED_PAGES = [
    ("py_regex", "正则表达式", "python3-reg-expressions.html", "第8章 高级主题", 4),
    ("py_json", "JSON 处理", "python3-json.html", "第8章 高级主题", 3),
    ("py_datetime", "日期和时间", "python3-date-time.html", "第8章 高级主题", 3),
    ("py_multithreading", "多线程", "python3-multithreading.html", "第8章 高级主题", 4),
    ("py_socket", "网络编程", "python3-socket.html", "第8章 高级主题", 4),
]

# 知识依赖关系（from -> to）
EDGES = [
    # 基础
    ("py_intro", "py_install"),
    ("py_install", "py_basic_syntax"),
    ("py_basic_syntax", "py_variable"),
    ("py_variable", "py_datatype"),
    ("py_variable", "py_comment"),
    ("py_datatype", "py_type_cast"),
    ("py_datatype", "py_operator"),
    # 数据类型
    ("py_datatype", "py_number"),
    ("py_datatype", "py_string_basic"),
    ("py_string_basic", "py_string_adv"),
    ("py_datatype", "py_list"),
    ("py_list", "py_tuple"),
    ("py_list", "py_dict"),
    ("py_dict", "py_set"),
    # 流程控制
    ("py_variable", "py_if"),
    ("py_if", "py_for"),
    ("py_for", "py_while"),
    ("py_while", "py_break_continue"),
    ("py_list", "py_comprehension"),
    # 函数
    ("py_variable", "py_func_def"),
    ("py_func_def", "py_func_param"),
    ("py_func_def", "py_lambda"),
    ("py_func_def", "py_decorator"),
    ("py_func_def", "py_scope"),
    # 高级特性
    ("py_list", "py_iterator"),
    ("py_iterator", "py_generator"),
    ("py_try_except", "py_with"),
    # 模块
    ("py_func_def", "py_module"),
    ("py_module", "py_package"),
    ("py_variable", "py_io"),
    ("py_string_basic", "py_io"),
    ("py_io", "py_file_read"),
    # 面向对象
    ("py_func_def", "py_try_except"),
    ("py_func_def", "py_class"),
    ("py_class", "py_inherit"),
    ("py_inherit", "py_encapsulation"),
    ("py_inherit", "py_polymorphism"),
    # 高级
    ("py_string_basic", "py_regex"),
    ("py_dict", "py_json"),
    ("py_module", "py_datetime"),
    ("py_func_def", "py_multithreading"),
    ("py_module", "py_socket"),
]

ALL_PAGES = BASIC_PAGES + ADVANCED_PAGES


def fetch_page(url: str, client: httpx.Client) -> str | None:
    """抓取页面 HTML。"""
    try:
        resp = client.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  [WARN] 抓取失败 {url}: {e}")
        return None


def extract_content(html: str) -> str:
    """从菜鸟教程页面提取主要内容，转为 Markdown。"""
    soup = BeautifulSoup(html, "html.parser")

    # 菜鸟教程的内容在 #content 中
    content_div = soup.find("div", id="content")
    if not content_div:
        content_div = soup.find("div", class_="article-intro")
    if not content_div:
        content_div = soup.find("article")
    if not content_div:
        return ""

    # 移除不需要的元素
    for tag in content_div.find_all(["script", "style", "ins", "iframe"]):
        tag.decompose()
    # 移除广告和导航
    for tag in content_div.find_all(class_=re.compile(r"(ad|nav|sidebar|footer|header|breadcrumb)")):
        tag.decompose()

    # 转为 Markdown
    lines = []
    for element in content_div.children:
        _convert_element(element, lines)

    text = "\n".join(lines).strip()
    # 清理多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _convert_element(element, lines: list, depth: int = 0):
    """递归转换 HTML 元素为 Markdown。"""
    from bs4 import NavigableString, Tag

    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text:
            lines.append(text)
        return

    if not isinstance(element, Tag):
        return

    tag = element.name

    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(tag[1])
        text = element.get_text(strip=True)
        if text:
            lines.append(f"\n{'#' * level} {text}\n")

    elif tag == "p":
        text = element.get_text(strip=True)
        if text:
            lines.append(f"\n{text}\n")

    elif tag in ("pre",):
        code = element.find("code")
        lang = ""
        if code:
            classes = code.get("class", [])
            for c in classes:
                if c.startswith("language-") or c.startswith("lang-"):
                    lang = c.split("-", 1)[1]
                    break
            text = code.get_text()
        else:
            text = element.get_text()
        lines.append(f"\n```{lang}\n{text.strip()}\n```\n")

    elif tag == "code":
        # inline code
        text = element.get_text()
        if text:
            lines.append(f"`{text}`")

    elif tag in ("ul", "ol"):
        for i, li in enumerate(element.find_all("li", recursive=False)):
            prefix = f"{i+1}." if tag == "ol" else "-"
            text = li.get_text(strip=True)
            if text:
                lines.append(f"{prefix} {text}")

    elif tag == "table":
        rows = element.find_all("tr")
        for i, row in enumerate(rows):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if cells:
                lines.append("| " + " | ".join(cells) + " |")
                if i == 0:
                    lines.append("| " + " | ".join(["---"] * len(cells)) + " |")

    elif tag == "blockquote":
        text = element.get_text(strip=True)
        if text:
            lines.append(f"\n> {text}\n")

    elif tag in ("div", "section", "article", "span", "a", "strong", "em", "b", "i"):
        for child in element.children:
            _convert_element(child, lines, depth + 1)

    elif tag == "br":
        lines.append("\n")

    elif tag == "hr":
        lines.append("\n---\n")

    else:
        text = element.get_text(strip=True)
        if text:
            lines.append(text)


def build_knowledge_base(pages: list, client: httpx.Client) -> dict:
    """构建知识库 JSON。"""
    kb = {}
    total = len(pages)

    for i, (node_id, title, filename, chapter, difficulty) in enumerate(pages):
        url = BASE_URL + filename
        print(f"  [{i+1}/{total}] 抓取: {title} ({url})")

        html = fetch_page(url, client)
        if not html:
            content = f"## {title}\n\n内容暂未获取，请参考 [菜鸟教程]({url})"
        else:
            content = extract_content(html)
            if not content:
                content = f"## {title}\n\n内容提取失败，请参考 [菜鸟教程]({url})"

        kb[node_id] = {
            "title": title,
            "chapter": chapter,
            "difficulty": difficulty,
            "content": content,
            "source": url,
        }

        # 礼貌延迟
        time.sleep(0.5)

    return kb


def build_knowledge_graph(pages: list, edges: list) -> dict:
    """构建知识图谱 JSON。"""
    nodes = []
    for node_id, title, filename, chapter, difficulty in pages:
        nodes.append({
            "id": node_id,
            "name": title,
            "chapter": chapter,
            "difficulty": difficulty,
            "description": f"{title}相关知识点",
        })

    edge_list = [{"from": f, "to": t} for f, t in edges]

    return {
        "python_programming": {
            "course_name": "Python3 程序设计",
            "nodes": nodes,
            "edges": edge_list,
        }
    }


def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_bases")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("菜鸟教程 Python3 知识库抓取工具")
    print("=" * 60)

    client = httpx.Client(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
        verify=False,
    )

    # 1. 抓取内容
    print(f"\n[1/3] 抓取 {len(ALL_PAGES)} 个页面...")
    kb = build_knowledge_base(ALL_PAGES, client)

    # 2. 生成知识图谱
    print("\n[2/3] 生成知识图谱...")
    kg = build_knowledge_graph(ALL_PAGES, EDGES)

    # 3. 保存文件
    kb_path = os.path.join(output_dir, "python_programming.json")
    kg_path = os.path.join(output_dir, "knowledge_graph.json")

    print(f"\n[3/3] 保存文件...")
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
    print(f"  知识库: {kb_path} ({len(kb)} 个知识点)")

    with open(kg_path, "w", encoding="utf-8") as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)
    print(f"  知识图谱: {kg_path} ({len(kg['python_programming']['nodes'])} 节点, {len(kg['python_programming']['edges'])} 边)")

    client.close()
    print("\n完成！")


if __name__ == "__main__":
    main()
