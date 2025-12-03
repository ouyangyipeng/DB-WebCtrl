# `app.py` 代码详解

本文档对 `app.py` 代码逐块进行详细讲解，帮助你理解每一部分的功能、设计考量、以及如何根据自己的环境调整。

**注意**：下面所有代码片段都基于仓库内的 `app.py` 当前实现。

---

## 目录

- 概览
- 导入与初始化
- 数据库配置（DB_CONFIG）
- `get_db_connection()` 函数详解
- 根路由 `/`（列表 / Read）
- 添加路由 `/add`（Create）
- 编辑路由 `/edit/<book_id>`（Update）
- 删除路由 `/delete/<book_id>`（Delete）
- `if __name__ == '__main__'` 入口
- 异常处理与常见问题
- 可选改进点与安全建议

---

## 概览

`app.py` 使用 Flask 构建一个小型的 Web 应用，直接通过 `pyodbc` 连接到本地 SQL Server（数据库名 `JY`），对 `book` 表实现增删改查（CRUD）。前端由 Jinja2 模板渲染（templates 文件夹），使用 Bootstrap 美化界面。

该文件总体结构清晰：先有配置与工具函数，再定义路由（处理 GET/POST），最后启动服务器。

---

## 导入与初始化

代码片段：
```python
from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages
```

讲解：
- `Flask, render_template, request, redirect, url_for, flash`：Flask 常用组件。
  - `render_template`：渲染模板文件（Jinja2）。
  - `request`：读取 HTTP 请求内的表单数据等。
  - `redirect` / `url_for`：重定向到其他路由。
  - `flash`：向模板传递一次性提示消息（成功/失败通知）。
- `pyodbc`：ODBC 驱动库，用于连接 SQL Server。
- `Decimal`：在本项目中未被大量使用，但通常用于金额精确处理。保留以备扩展。
- `app.secret_key`：用于签署会话 cookie 和 flash。上线部署时请替换为随机且保密的值。

---

## 数据库配置（DB_CONFIG）

代码片段：

```python
# Database Configuration
# Option 1: Windows Authentication (Recommended)
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost',
    'database': 'JY',
    'trusted_connection': 'yes'
}

# Option 2: SQL Server Authentication (Uncomment to use)
# DB_CONFIG = {
#     'driver': 'ODBC Driver 17 for SQL Server',
#     'server': 'localhost',
#     'database': 'JY',
#     'uid': 'admin',
#     'pwd': 'owen0126'
# }
```

讲解：
- `driver`：ODBC 驱动名称，常见值有 `ODBC Driver 17 for SQL Server`、`ODBC Driver 18 for SQL Server` 等。请根据系统上已安装的驱动修改。
- `server`：数据库服务器地址，本地通常为 `localhost` 或 `127.0.0.1`。
- `database`：要访问的数据库名，这里是 `JY`。
- `trusted_connection: 'yes'`：启用 Windows 身份验证（Integrated Security），推荐在本机上使用，这样无需保存 SQL 帐号密码。
- 如果需要使用 SQL Server 认证（用户名/密码），请注释掉 Windows 身份验证配置并使用 `uid` / `pwd`。

安全提示：不要在代码库中硬编码生产账号密码，优先使用环境变量或配置文件（并确保 .gitignore 忽略敏感文件）。

---

## get_db_connection() 函数详解

代码片段：

```python
def get_db_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
    )
    
    if 'trusted_connection' in DB_CONFIG:
        conn_str += f"Trusted_Connection={DB_CONFIG['trusted_connection']};"
    else:
        conn_str += f"UID={DB_CONFIG.get('uid')};PWD={DB_CONFIG.get('pwd')};"

    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        print(f"Database connection failed: {ex}")
        return None
```

讲解：
- 该函数负责组装 ODBC 连接字符串并建立连接：
  - 基础格式：`DRIVER={...};SERVER=...;DATABASE=...;`。
  - 如果使用 Windows 身份验证，添加 `Trusted_Connection=yes;`。
  - 否则使用 `UID`/`PWD` 指定用户名密码。注意这些值必须存在于 `DB_CONFIG` 中。
- 返回值：成功返回 `pyodbc.Connection` 对象，失败返回 `None` 并打印错误。路由里会根据返回值判断并向用户展示错误提示。

注意事项：
- ODBC 驱动名称需要与本机安装的驱动匹配，否则会抛错（`DataSourceName not found` 等）。
- 在高并发场景应考虑连接池（如使用 SQLAlchemy 或自行维护连接池），pyodbc 本身没有内置持久连接管理。

---

## 根路由 `/`（列表 / Read）

代码片段：

```python
@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash('无法连接到数据库，请检查配置。', 'danger')
        return render_template('index.html', books=[])

    cursor = conn.cursor()
    # Using dictionary cursor logic manually since pyodbc rows are tuples
    cursor.execute("SELECT * FROM book")
    columns = [column[0] for column in cursor.description]
    books = []
    for row in cursor.fetchall():
        books.append(dict(zip(columns, row)))
    
    conn.close()
    return render_template('index.html', books=books)
```

讲解：
- 功能：查询 `book` 表所有行并渲染 `index.html` 模板。
- 处理流程：
  1. 获取数据库连接；若失败，flash 错误并返回空列表页面。
  2. 使用 `cursor.execute("SELECT * FROM book")` 执行查询。
  3. `cursor.description` 提供列名元组（用于生成字典）。
  4. 将每一行转换为字典（列名->值），便于模板中使用 `book.book_name` 等字段名访问。
  5. 关闭连接并返回渲染结果。

注意与改进：
- 当前用 `SELECT *`。在生产环境建议明确列名，避免因表结构变动影响应用。
- 若数据量大应添加分页（LIMIT/OFFSET 或在 SQL Server 中使用 `OFFSET ... FETCH`）。

---

## 添加路由 `/add`（Create）

代码片段：

```python
@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        book_id = request.form['book_id']
        book_name = request.form['book_name']
        book_isbn = request.form['book_isbn']
        book_author = request.form['book_author']
        book_publisher = request.form['book_publisher']
        book_price = request.form['book_price']
        interviews_times = request.form['interviews_times']

        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'danger')
            return redirect(url_for('index'))

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO book (book_id, book_name, book_isbn, book_author, book_publisher, book_price, interviews_times) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (book_id, book_name, book_isbn, book_author, book_publisher, book_price, interviews_times)
            )
            conn.commit()
            flash('图书添加成功！', 'success')
            return redirect(url_for('index'))
        except pyodbc.IntegrityError:
            flash('添加失败：图书编号可能已存在或违反约束。', 'danger')
        except Exception as e:
            flash(f'添加失败：{str(e)}', 'danger')
        finally:
            conn.close()

    return render_template('add.html')
```

讲解：
- GET 请求：渲染 `add.html` 表单页面。
- POST 请求流程：读取表单字段 -> 获取 DB 连接 -> 使用参数化 SQL (`?` 占位符) 执行插入 -> 提交事务 -> flash 成功并重定向。
- 为什么使用参数化 SQL：防止 SQL 注入并让驱动正确处理类型转换。
- 错误处理：捕获 `pyodbc.IntegrityError` 用于主键冲突或违反约束的场景；其它异常显示错误信息。

输入校验：
- 前端表单使用 `pattern="b[0-9]{4}"` 强制 `book_id` 格式；后端也可以加上正则校验以防止绕过前端限制。
- `book_price` 与 `interviews_times` 应当转换为合适类型（例如 `Decimal` 或 `int`），当前代码将字符串直接传入 pyodbc，ODBC 驱动会尝试进行转换，但显式转换更安全。

示例改进（后端类型转换）：

```python
try:
    book_price = Decimal(book_price)
    interviews_times = int(interviews_times)
except ValueError:
    flash('价格或借阅次数格式错误', 'danger')
    return redirect(url_for('add'))
```

---

## 编辑路由 `/edit/<book_id>`（Update）

代码片段：

```python
@app.route('/edit/<book_id>', methods=('GET', 'POST'))
def edit(book_id):
    conn = get_db_connection()
    if not conn:
        flash('数据库连接失败', 'danger')
        return redirect(url_for('index'))

    cursor = conn.cursor()

    if request.method == 'POST':
        book_name = request.form['book_name']
        book_isbn = request.form['book_isbn']
        book_author = request.form['book_author']
        book_publisher = request.form['book_publisher']
        book_price = request.form['book_price']
        interviews_times = request.form['interviews_times']

        try:
            cursor.execute(
                "UPDATE book SET book_name = ?, book_isbn = ?, book_author = ?, book_publisher = ?, book_price = ?, interviews_times = ? WHERE book_id = ?",
                (book_name, book_isbn, book_author, book_publisher, book_price, interviews_times, book_id)
            )
            conn.commit()
            flash('图书更新成功！', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
        finally:
            conn.close()

    else:
        cursor.execute("SELECT * FROM book WHERE book_id = ?", (book_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [column[0] for column in cursor.description]
            book = dict(zip(columns, row))
            return render_template('edit.html', book=book)
        else:
            flash('未找到该图书', 'warning')
            return redirect(url_for('index'))
```

讲解：
- GET 请求：读取 `book_id` 对应的记录并渲染 `edit.html`，模板中显示原始字段供编辑。
- POST 请求：读取表单中变更字段，执行参数化 `UPDATE`，提交事务并重定向。
- 注意：主键 `book_id` 在模板中被设为只读/disabled，后端仍然使用路由参数作为更新条件。
- 小细节：用于读取单条记录后，使用 `cursor.description` 获取列名。但在目前实现中，`cursor.description` 在 `fetchone()` 后仍然可用；如果你的数据库驱动行为不同，建议在 `execute()` 之后立即读取 `cursor.description`。

---

## 删除路由 `/delete/<book_id>`（Delete）

代码片段：

```python
@app.route('/delete/<book_id>', methods=('POST',))
def delete(book_id):
    conn = get_db_connection()
    if not conn:
        flash('数据库连接失败', 'danger')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM book WHERE book_id = ?", (book_id,))
        conn.commit()
        flash('图书删除成功！', 'success')
    except Exception as e:
        flash(f'删除失败：{str(e)}', 'danger')
    finally:
        conn.close()

    return redirect(url_for('index'))
```

讲解：
- 接受 `POST` 请求执行删除。前端通过一个确认模态框提交删除表单以避免误删。
- 仍使用参数化 SQL 来避免注入风险。
- 可考虑在删除前检查是否存在依赖（例如借阅记录外键），根据需要先处理级联或拒绝删除。

---

## `if __name__ == '__main__'` 入口

代码片段：

```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

讲解：
- 入口使用 Flask 自带的开发服务器，`debug=True` 开启调试与自动重载，便于开发，但生产环境中不要启用。
- 默认监听端口 `5000`，可以根据需要修改为 `0.0.0.0` 以便外网访问（注意防火墙与安全性）。

---

## 异常处理与常见问题

1. pyodbc 安装失败
   - 原因：某些 pyodbc 版本没有为你的 Python 版本提供预编译 wheel，会尝试从源码编译，需要 Visual C++ Build Tools。
   - 解决：要么安装对应 Python 版本的 pyodbc wheel（pip 会优先使用 wheel），要么安装 Microsoft Visual C++ Build Tools。你在本机上成功安装到了 `pyodbc-5.3.0`。

2. 无法找到 ODBC 驱动
   - 错误示例：`DataSourceName not found and no default driver specified`。
   - 解决：在 Windows 上安装 `ODBC Driver 17 for SQL Server` 或更高版本，并把 `DB_CONFIG['driver']` 改为正确的驱动名称（可在 ODBC 管理器中查看）。

3. 登录失败（认证问题）
   - 如果使用 Windows 身份验证：确保当前 Windows 用户对数据库有访问权限。
   - 如果使用 SQL Server 认证：确保 `uid`/`pwd` 正确，且 SQL Server 配置允许 SQL 身份验证。

4. 字段/数据类型错误
   - 插入或更新时若字段类型不匹配，会抛出异常。建议后端做必要的类型转换（例如 `Decimal(book_price)` / `int(interviews_times)`）。

---

## 可选改进点与安全建议

- 使用环境变量管理配置：例如 `os.environ.get('DB_DRIVER')`、`os.environ.get('DB_PWD')`，避免在代码中明文存放敏感信息。
- 使用连接池或 ORM：如果项目扩展，建议用 SQLAlchemy（它支持连接池、ORM、迁移工具等）来简化数据库操作与提高性能。
- 输入校验与错误友好提示：后端补充验证逻辑并精准捕获常见错误（例如数据长度超限、格式错误等）。
- 权限与认证：当前应用无登录机制，任何人都能对数据库修改。若用于多人场景，请加入用户认证与权限控制。
- 部署建议：生产环境请使用 Gunicorn/uWSGI + 反向代理（例如 nginx），并关闭 `debug` 模式。

---

## 常用调试命令（PowerShell）

在 `code` 目录下：

```powershell
# 安装依赖
pip install -r requirements.txt

# 运行应用
python app.py

# 如果想在指定主机/端口并关闭 debug
python -c "from app import app; app.run(host='0.0.0.0', port=8080, debug=False)"
```

---

如果你希望我把文档也渲染为 HTML 页面（例如在项目中添加 `docs/`），或者需要对 `app.py` 做进一步重构（例如引入蓝图、改用 SQLAlchemy、加入登录系统），我可以继续实现。