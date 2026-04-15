# Menejerlik sari bot tizimi

Bu loyiha Telegram bot + Web App + admin panel ko'rinishida tayyorlangan.

## Imkoniyatlar
- Foydalanuvchi kabineti
- Telegram orqali kirish
- ID va balans ko'rsatish
- Savollar bo'limi
- Testlar bo'limi
- Qo'llanmalar bo'limi
- Onlayn kurslar bo'limi
- Balans to'ldirish so'rovi
- Oddiy admin panel
- SQLite bazada saqlash

## O'rnatish

### 1. Python o'rnating
Python 3.10+ tavsiya qilinadi.

### 2. Kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

### 3. `.env` fayl yarating
`.env.example` nusxasini `.env` nomi bilan saqlang va to'ldiring:
- `BOT_TOKEN`
- `WEBAPP_URL`
- `ADMIN_PASSWORD`

### 4. Serverni ishga tushiring
```bash
python app.py
```

Server odatda bu manzilda ishlaydi:
`http://127.0.0.1:8000`

### 5. Botni ishga tushiring
Yangi terminal ochib:
```bash
python bot.py
```

## Muhim
Agar bot ichida Web App ochilsa, `WEBAPP_URL` internetdagi HTTPS domen bo'lishi kerak.
Masalan:
- Render
- Railway
- VPS + Nginx + SSL

## Admin kirish
Admin sahifa:
`/admin?password=12345`

Yoki `.env` dagi parol bilan.

## Fayllar
- `app.py` — FastAPI server
- `bot.py` — Telegram bot
- `templates/index.html` — foydalanuvchi kabineti
- `templates/admin.html` — admin panel
- `static/styles.css` — dizayn
- `menejerlik_sari.db` — avtomatik yaratiladi

## Test ishlash tartibi
1. `/start` bosing
2. `Menejerlik sari kabinetini ochish` tugmasini bosing
3. Menyulardan foydalaning
4. Admin orqali test, kurs va qo'llanma qo'shing


## Yangi qo'shilgan imkoniyatlar
- Admin login sahifasi: /admin-login
- Test natijalarini bazaga saqlash
- Foydalanuvchi uchun natijalar bo'limi
- To'lov so'rovini admin tomonidan tasdiqlash
- Tasdiqlanganda balans avtomatik qo'shiladi
