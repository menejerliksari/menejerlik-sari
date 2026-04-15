import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import uvicorn

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "menejerlik_sari.db"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "12345")

app = FastAPI(title="Menejerlik sari Web App")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT UNIQUE,
        full_name TEXT NOT NULL,
        balance INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS faqs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT NOT NULL,
        test_id INTEGER NOT NULL,
        selected_option TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT NOT NULL,
        amount INTEGER NOT NULL,
        note TEXT,
        status TEXT DEFAULT 'kutilmoqda',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    user = cur.execute("SELECT * FROM users WHERE telegram_id = ?", ("8562088626",)).fetchone()
    if not user:
        cur.execute(
            "INSERT INTO users (telegram_id, full_name, balance) VALUES (?, ?, ?)",
            ("8562088626", "F. Mamadaliyev", 0),
        )

    if cur.execute("SELECT COUNT(*) AS c FROM faqs").fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO faqs (question, answer) VALUES (?, ?)",
            [
                ("Menejerlik sari nima?", "Bu test, kurs va qo'llanmalarni boshqaruvchi tizim."),
                ("Balans qanday to'ldiriladi?", "Balansni to'ldirish bo'limida summa yozib so'rov yuborasiz."),
                ("Test natijasi qayerda ko'rinadi?", "Test topshirilgandan keyin natija va tarix saqlanadi."),
            ],
        )

    if cur.execute("SELECT COUNT(*) AS c FROM tests").fetchone()["c"] == 0:
        cur.execute(
            """INSERT INTO tests
            (title, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "Marketing",
                "Marketingning asosiy maqsadi nima?",
                "Faqat reklama qilish",
                "Mijoz ehtiyojini aniqlash va qondirish",
                "Faqat mahsulot ishlab chiqarish",
                "Soliq to'lash",
                "B",
            ),
        )

    if cur.execute("SELECT COUNT(*) AS c FROM materials").fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO materials (title, content) VALUES (?, ?)",
            ("Rahbar uchun qo'llanma", "Bu yerga PDF linki yoki matnli qo'llanma joylanadi."),
        )

    if cur.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO courses (title, description) VALUES (?, ?)",
            ("Menejerlik kursi", "Rahbarlik, boshqaruv va test tayyorgarligi bo'yicha kurs."),
        )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, telegram_id: str = "8562088626"):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
    if not user:
        conn.execute(
            "INSERT INTO users (telegram_id, full_name, balance) VALUES (?, ?, ?)",
            (telegram_id, f"User {telegram_id}", 0),
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()

    faqs = conn.execute("SELECT * FROM faqs ORDER BY id DESC").fetchall()
    tests = conn.execute("SELECT * FROM tests ORDER BY id DESC").fetchall()
    materials = conn.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    payments = conn.execute(
        "SELECT * FROM payments WHERE telegram_id = ? ORDER BY id DESC LIMIT 10", (telegram_id,)
    ).fetchall()
    results = conn.execute("""
        SELECT tr.*, t.title, t.question
        FROM test_results tr
        JOIN tests t ON t.id = tr.test_id
        WHERE tr.telegram_id = ?
        ORDER BY tr.id DESC
        LIMIT 10
    """, (telegram_id,)).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "faqs": faqs,
            "tests": tests,
            "materials": materials,
            "courses": courses,
            "payments": payments,
            "results": results,
        },
    )


@app.post("/submit-test")
async def submit_test(
    telegram_id: str = Form(...),
    test_id: int = Form(...),
    answer: str = Form(...),
):
    conn = get_conn()
    test = conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()

    if not test:
        conn.close()
        raise HTTPException(status_code=404, detail="Test topilmadi")

    is_correct = answer.upper() == test["correct_option"].upper()
    conn.execute(
        "INSERT INTO test_results (telegram_id, test_id, selected_option, is_correct) VALUES (?, ?, ?, ?)",
        (telegram_id, test_id, answer.upper(), 1 if is_correct else 0),
    )
    conn.commit()
    conn.close()

    return JSONResponse(
        {
            "success": True,
            "correct": is_correct,
            "correct_option": test["correct_option"],
            "message": "To'g'ri javob!" if is_correct else "Noto'g'ri javob.",
        }
    )


@app.post("/payment-request")
async def payment_request(
    telegram_id: str = Form(...),
    amount: int = Form(...),
    note: str = Form(""),
):
    conn = get_conn()
    conn.execute(
        "INSERT INTO payments (telegram_id, amount, note, status) VALUES (?, ?, ?, ?)",
        (telegram_id, amount, note, "kutilmoqda"),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/?telegram_id={telegram_id}", status_code=303)


@app.get("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request, error: str = ""):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": error})


@app.post("/admin-login")
async def admin_login_post(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return RedirectResponse(url="/admin-login?error=Parol%20noto%27g%27ri", status_code=303)
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, password: str = ""):
    if password != ADMIN_PASSWORD:
        return RedirectResponse(url="/admin-login", status_code=303)

    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    tests = conn.execute("SELECT * FROM tests ORDER BY id DESC").fetchall()
    materials = conn.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()
    courses = conn.execute("SELECT * FROM courses ORDER BY id DESC").fetchall()
    payments = conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()
    results = conn.execute("""
        SELECT tr.*, t.title, t.question
        FROM test_results tr
        JOIN tests t ON t.id = tr.test_id
        ORDER BY tr.id DESC
    """).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "password": password,
            "users": users,
            "tests": tests,
            "materials": materials,
            "courses": courses,
            "payments": payments,
            "results": results,
        },
    )


@app.post("/admin/add-test")
async def add_test(
    password: str = Form(...),
    title: str = Form(...),
    question: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")
    conn = get_conn()
    conn.execute(
        """INSERT INTO tests (title, question, option_a, option_b, option_c, option_d, correct_option)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, question, option_a, option_b, option_c, option_d, correct_option.upper()),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/admin/add-material")
async def add_material(
    password: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")
    conn = get_conn()
    conn.execute("INSERT INTO materials (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/admin/add-course")
async def add_course(
    password: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")
    conn = get_conn()
    conn.execute("INSERT INTO courses (title, description) VALUES (?, ?)", (title, description))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/admin/add-balance")
async def add_balance(
    password: str = Form(...),
    telegram_id: str = Form(...),
    amount: int = Form(...),
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")
    conn = get_conn()
    conn.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (amount, telegram_id))
    conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


@app.post("/admin/approve-payment")
async def approve_payment(
    password: str = Form(...),
    payment_id: int = Form(...),
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri")

    conn = get_conn()
    payment = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    if payment and payment["status"] == "kutilmoqda":
        conn.execute("UPDATE payments SET status = 'tasdiqlandi' WHERE id = ?", (payment_id,))
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (payment["amount"], payment["telegram_id"]),
        )
        conn.commit()
    conn.close()
    return RedirectResponse(url=f"/admin?password={password}", status_code=303)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
