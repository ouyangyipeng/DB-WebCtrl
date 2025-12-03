from flask import Flask, render_template, request, redirect, url_for, flash
import pyodbc
from decimal import Decimal
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
