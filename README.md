# 图书借阅管理系统 (JY) - Web版

这是一个基于 Python Flask 框架开发的图书借阅管理系统 Web 界面。它实现了对 SQL Server 数据库中 `book` 表的增删改查 (CRUD) 功能。

## 1. 设计思想

本项目采用了 **MVC (Model-View-Controller)** 的设计模式（在 Flask 中通常称为 MTV: Model-Template-View）：

*   **Model (模型)**: 数据层由 SQL Server 数据库承担。我们在 Python 代码中通过 `pyodbc` 库直接执行 SQL 语句与数据库交互，映射 `book` 表的数据结构。
*   **Template (模板/视图)**: 使用 Jinja2 模板引擎渲染 HTML 页面。前端采用 **Bootstrap 5** 框架，确保界面美观、响应式，并提供良好的用户体验（如模态框确认删除、表单验证）。
*   **View (视图/控制器)**: `app.py` 中的路由函数充当控制器，接收用户请求（GET/POST），处理业务逻辑（如连接数据库、执行 SQL），并返回渲染后的页面或重定向。

选择 Flask 的原因：
*   **轻量级**: 适合快速构建小型到中型的 Web 应用。
*   **灵活性**: 可以自由选择数据库连接方式（这里直接使用 ODBC，直观且高效）。
*   **易于部署**: 依赖少，运行简单。

## 2. 项目结构

```
code/
├── templates/              # 存放 HTML 模板文件
│   ├── base.html           # 基础模板，包含导航栏和页脚，被其他页面继承
│   ├── index.html          # 首页，显示图书列表
│   ├── add.html            # 添加图书表单页面
│   └── edit.html           # 编辑图书表单页面
├── app.py                  # 主程序入口，包含路由和数据库逻辑
├── requirements.txt        # Python 依赖包列表
└── README.md               # 项目说明文档
```

## 3. 文件说明

*   **`app.py`**: 核心代码文件。
    *   配置了数据库连接字符串（支持 Windows 身份验证和 SQL Server 身份验证）。
    *   定义了 `/` (列表), `/add` (添加), `/edit/<id>` (编辑), `/delete/<id>` (删除) 四个主要路由。
    *   实现了数据库连接函数 `get_db_connection()`，确保每次请求都获取新的连接并在结束后关闭。
*   **`templates/base.html`**: 定义了页面的通用结构，引入了 Bootstrap CSS/JS 资源，并处理了 Flash 消息（用于显示操作成功或失败的提示）。
*   **`templates/index.html`**: 使用表格展示所有图书信息，包含“编辑”和“删除”按钮。删除操作通过模态框（Modal）进行二次确认，防止误删。
*   **`templates/add.html`**: 包含添加图书的表单。对 `book_id` 进行了正则验证 (`pattern="b[0-9]{4}"`) 以符合数据库约束。
*   **`templates/edit.html`**: 包含编辑图书的表单。`book_id` 字段设为只读，因为主键不可修改。

## 4. 环境准备

在运行本程序前，请确保您的环境满足以下要求：

1.  **操作系统**: Windows 10/11 (x86_64)
2.  **Python**: 已安装 Python 3.x。
3.  **数据库**: Microsoft SQL Server 已运行，且存在 `JY` 数据库和 `book` 表。
4.  **ODBC 驱动**: 安装了 **ODBC Driver 17 for SQL Server** (通常随 SQL Server 或 SSMS 安装，如果没有请从微软官网下载)。

## 5. 编译与运行

请按照以下步骤在终端（PowerShell 或 CMD）中操作：

### 第一步：安装依赖

在 `code` 文件夹下打开终端，运行以下命令安装 Flask 和 pyodbc：

```powershell
pip install -r requirements.txt
```

### 第二步：检查数据库配置

打开 `app.py`，找到 `DB_CONFIG` 部分。默认配置使用 **Windows 身份验证** 连接本地数据库：

```python
DB_CONFIG = {
    'driver': 'ODBC Driver 17 for SQL Server',
    'server': 'localhost',
    'database': 'JY',
    'trusted_connection': 'yes'
}
```

如果您需要使用 SQL Server 账号 (`admin` / `owen0126`)，请注释掉上面的配置，并取消注释下方的 Option 2 配置。

### 第三步：运行程序

在终端中运行：

```powershell
python app.py
```

如果一切正常，您将看到类似以下的输出：
```
 * Running on http://127.0.0.1:5000
```

### 第四步：访问系统

打开浏览器，访问地址：[http://127.0.0.1:5000](http://127.0.0.1:5000)

## 6. 测试指南

您可以按照以下流程测试系统的各项功能：

1.  **查看列表 (Read)**:
    *   打开首页，应能看到数据库中现有的图书列表。
    *   如果表为空，会显示“暂无图书数据”。

2.  **添加图书 (Create)**:
    *   点击右上角的“添加新书”按钮。
    *   输入图书信息。尝试输入错误的 ID 格式（如 `a123`），浏览器应会提示格式错误。
    *   输入合法的 ID（如 `b9999`）和其他信息，点击“保存”。
    *   页面应跳转回首页，并显示“图书添加成功”的绿色提示条，列表中应出现新书。

3.  **编辑图书 (Update)**:
    *   在列表中找到刚才添加的书，点击蓝色的“编辑”图标。
    *   修改价格或借阅次数。注意 ID 栏是灰色的，无法修改。
    *   点击“更新图书”。
    *   回到首页，确认数据已更新。

4.  **删除图书 (Delete)**:
    *   点击红色的“删除”图标。
    *   会弹出一个确认框，询问是否确定删除。
    *   点击“确认删除”。
    *   该书应从列表中消失，并显示“图书删除成功”的提示。

## 7. 常见问题排查

*   **错误：`DataSourceName not found and no default driver specified`**:
    *   原因：缺少 ODBC 驱动。
    *   解决：请下载并安装 [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)。
*   **错误：`Login failed for user`**:
    *   原因：数据库认证失败。
    *   解决：检查 `app.py` 中的 `DB_CONFIG`。如果使用 Windows 身份验证，请确保当前 Windows 用户有权访问数据库。如果使用 SQL 账号，请确认账号密码正确。
*   **错误：`IntegrityError`**:
    *   原因：通常是因为尝试添加重复的 `book_id`，或者违反了数据库的其他约束（如字段长度）。
    *   解决：检查输入的数据是否符合要求。

## 参考资料

*   [Flask 官方文档](https://flask.palletsprojects.com/)
*   [pyodbc Wiki](https://github.com/mkleehammer/pyodbc/wiki)
*   [Bootstrap 5 文档](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
