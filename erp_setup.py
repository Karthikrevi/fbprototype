from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'erp_secret_key'

# ---- DATABASE SETUP ----

def create_tables():
    conn = sqlite3.connect('erp.db')
    c = conn.cursor()

    # Vendors
    c.execute('''
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        password TEXT NOT NULL
    )
    ''')

    # Products
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_email TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_url TEXT,
        quantity INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

# ---- VENDOR AUTH ----

@app.route('/erp')
def erp_home():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))
    return redirect(url_for("manage_products"))

@app.route('/erp/login', methods=["GET", "POST"])
def erp_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("SELECT * FROM vendors WHERE email=? AND password=?", (email, password))
        vendor = c.fetchone()
        conn.close()

        if vendor:
            session["vendor"] = email
            return redirect(url_for("erp_home"))
        else:
            return "Invalid credentials"

    return '''
        <h2>Vendor Login</h2>
        <form method="POST">
            Email: <input type="email" name="email"><br>
            Password: <input type="password" name="password"><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/erp/register', methods=["GET", "POST"])
def vendor_register():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect('erp.db')
            c = conn.cursor()
            c.execute("INSERT INTO vendors (email, name, password) VALUES (?, ?, ?)", (email, name, password))
            conn.commit()
            conn.close()
            return redirect(url_for("erp_login"))
        except sqlite3.IntegrityError:
            return "Vendor already exists with that email."

    return '''
        <h2>Vendor Registration</h2>
        <form method="POST">
            Name: <input name="name"><br>
            Email: <input type="email" name="email"><br>
            Password: <input type="password" name="password"><br>
            <button type="submit">Register</button>
        </form>
    '''


@app.route('/erp/logout')
def erp_logout():
    session.pop("vendor", None)
    return redirect(url_for("erp_login"))

# ---- PRODUCT MANAGEMENT ----

@app.route('/erp/products')
def manage_products():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    conn = sqlite3.connect('erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE vendor_email=?", (session["vendor"],))
    products = c.fetchall()
    conn.close()

    return render_template("erp_products.html", products=products)

@app.route('/erp/products/add', methods=["GET", "POST"])
def add_product():
    if "vendor" not in session:
        return redirect(url_for("erp_login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        image_url = request.form["image_url"]
        quantity = int(request.form["quantity"])

        conn = sqlite3.connect('erp.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (vendor_email, name, description, price, image_url, quantity) VALUES (?, ?, ?, ?, ?, ?)",
                  (session["vendor"], name, description, price, image_url, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for("manage_products"))

    return '''
        <h2>Add Product</h2>
        <form method="POST">
            Name: <input name="name"><br>
            Description: <input name="description"><br>
            Price: <input name="price" type="number" step="0.01"><br>
            Image URL: <input name="image_url"><br>
            Quantity: <input name="quantity" type="number"><br>
            <button type="submit">Add Product</button>
        </form>
    '''

# ---- INITIALIZATION ----

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)
