import os
import sqlite3
from flask import Flask, render_template, request, redirect
from telegram import Bot

# ===== إعداد البوت =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")   # حط معرف القناة زي @mychannel
bot = Bot(BOT_TOKEN)

# ===== إعداد Flask =====
app = Flask(__name__)

# ===== قاعدة البيانات =====
conn = sqlite3.connect("auctions.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS auctions
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              item TEXT,
              highest_bid REAL,
              highest_user TEXT)''')
conn.commit()

# إضافة مزاد تجريبي عند التشغيل أول مرة
c.execute("SELECT COUNT(*) FROM auctions")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO auctions (item, highest_bid, highest_user) VALUES (?, ?, ?)",
              ("🎁 هدية تجريبية", 5.0, "لا يوجد"))
    conn.commit()

# ===== الصفحة الرئيسية =====
@app.route("/")
def index():
    c.execute("SELECT item, highest_bid, highest_user FROM auctions ORDER BY id DESC LIMIT 1")
    auction = c.fetchone()
    return render_template("index.html", auction=auction)

# ===== إضافة مزايدة جديدة =====
@app.route("/bid", methods=["POST"])
def bid():
    user = request.form["user"]
    amount = float(request.form["amount"])

    # جلب المزاد الحالي
    c.execute("SELECT id, highest_bid FROM auctions ORDER BY id DESC LIMIT 1")
    auction = c.fetchone()

    if auction and amount > auction[1]:
        c.execute("UPDATE auctions SET highest_bid=?, highest_user=? WHERE id=?", (amount, user, auction[0]))
        conn.commit()

        # إرسال تحديث للقناة
        if CHANNEL_ID:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"🔥 مزايدة جديدة!\nالمستخدم: {user}\nالمبلغ: {amount} TON"
            )

    return redirect("/")

# ===== إضافة منتج جديد (من الأدمن) =====
@app.route("/add/<item>/<start_price>")
def add(item, start_price):
    c.execute("INSERT INTO auctions (item, highest_bid, highest_user) VALUES (?, ?, ?)",
              (item, float(start_price), "لا يوجد"))
    conn.commit()

    # نشر المزاد في القناة
    if CHANNEL_ID:
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"📢 بدأ المزاد الجديد!\nالمنتج: {item}\nالسعر الابتدائي: {start_price} TON\n\nشارك الآن عبر الرابط 👇\n{os.getenv('WEBAPP_URL')}"
        )

    return f"تم إضافة المزاد: {item}"

# ===== تشغيل السيرفر =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
