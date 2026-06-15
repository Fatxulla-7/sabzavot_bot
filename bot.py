import logging
import os
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import database as db

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8687459331:AAFrUqytKphv7eT6P7bDe70CW2ltv4whMqU"   # <-- O'z tokeningizni kiriting
ADMIN_IDS = [7461041638]              # <-- O'z Telegram ID'ingizni kiriting

bot = TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== HOLATLAR =====================
# Ro'yxatdan o'tish
STATE_REG_NAME       = "reg_name"
STATE_REG_SURNAME    = "reg_surname"
STATE_REG_PHONE      = "reg_phone"
STATE_REG_ADDRESS    = "reg_address"

# Admin holatlari
STATE_ADMIN_ADD_NAME  = "admin_add_name"
STATE_ADMIN_ADD_PRICE = "admin_add_price"
STATE_ADMIN_ADD_PHOTO = "admin_add_photo"
STATE_ADMIN_EDIT_SEL  = "admin_edit_select"
STATE_ADMIN_EDIT_NAME = "admin_edit_name"
STATE_ADMIN_EDIT_PRICE= "admin_edit_price"
STATE_ADMIN_EDIT_PHOTO= "admin_edit_photo"

# User holatlari saqlanishi (chat_id -> state)
user_states = {}
# Vaqtinchalik ma'lumotlar (chat_id -> dict)
user_data   = {}

# ===================== YORDAMCHI FUNKSIYALAR =====================

def is_admin(chat_id):
    return int(chat_id) in ADMIN_IDS

def get_state(chat_id):
    return user_states.get(str(chat_id))

def set_state(chat_id, state):
    user_states[str(chat_id)] = state

def clear_state(chat_id):
    user_states.pop(str(chat_id), None)
    user_data.pop(str(chat_id), None)

def set_data(chat_id, key, value):
    cid = str(chat_id)
    if cid not in user_data:
        user_data[cid] = {}
    user_data[cid][key] = value

def get_data(chat_id, key=None):
    cid = str(chat_id)
    if key:
        return user_data.get(cid, {}).get(key)
    return user_data.get(cid, {})

# ===================== KLAVIATURALAR =====================

def main_menu_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🛒 Sabzavotlar menyusi"))
    kb.add(KeyboardButton("📦 Mening buyurtmalarim"))
    kb.add(KeyboardButton("👤 Mening ma'lumotlarim"))
    return kb

def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Sabzavot qo'shish"))
    kb.add(KeyboardButton("✏️ Sabzavotlarni tahrirlash"))
    kb.add(KeyboardButton("📋 Barcha buyurtmalar"))
    kb.add(KeyboardButton("🔙 Asosiy menyu"))
    return kb

def phone_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    return kb

def cancel_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Bekor qilish"))
    return kb

def payment_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💵 Naqd pul", callback_data="pay_cash"),
        InlineKeyboardButton("💳 Karta", callback_data="pay_card")
    )
    return kb

def product_quantity_keyboard(product_id, quantity):
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("➖", callback_data=f"qty_minus_{product_id}"),
        InlineKeyboardButton(f"🥦 {quantity} kg", callback_data=f"qty_show_{product_id}"),
        InlineKeyboardButton("➕", callback_data=f"qty_plus_{product_id}")
    )
    kb.add(InlineKeyboardButton("🛒 Sotib olish", callback_data=f"buy_{product_id}"))
    return kb

def edit_product_field_keyboard(product_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data=f"edit_name_{product_id}"))
    kb.add(InlineKeyboardButton("💰 Narxini o'zgartirish", callback_data=f"edit_price_{product_id}"))
    kb.add(InlineKeyboardButton("🖼 Rasmini o'zgartirish", callback_data=f"edit_photo_{product_id}"))
    kb.add(InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_prod_{product_id}"))
    kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="edit_back"))
    return kb

# ===================== /start =====================

@bot.message_handler(commands=["start"])
def start_handler(msg):
    chat_id = msg.chat.id
    user = db.get_user(chat_id)
    first_name = msg.from_user.first_name or "Foydalanuvchi"

    if user:
        bot.send_message(
            chat_id,
            f"👋 Xush kelibsiz, <b>{user['first_name']} {user['last_name']}</b>!\n"
            f"🌿 <b>Sabzovot Savdo Botimizga</b> qaytib keldingiz!\n\n"
            f"Quyidagi menyudan foydalaning:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    else:
        clear_state(chat_id)
        set_state(chat_id, STATE_REG_NAME)
        bot.send_message(
            chat_id,
            f"👋 Salom, <b>{first_name}</b>!\n\n"
            f"🌿 <b>Sabzovot Savdo Botimizga</b> xush kelibsiz!\n\n"
            f"Davom etish uchun avval ro'yxatdan o'tishingiz kerak.\n\n"
            f"📝 <b>Ismingizni kiriting:</b>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )

# ===================== ADMIN PANEL =====================

@bot.message_handler(commands=["admin"])
def admin_command(msg):
    chat_id = msg.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "⛔ Sizda admin huquqi yo'q!")
        return
    clear_state(chat_id)
    bot.send_message(
        chat_id,
        "🔐 <b>Admin paneliga xush kelibsiz!</b>\n\nQuyidagi amallardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "➕ Sabzavot qo'shish")
def admin_add_start(msg):
    chat_id = msg.chat.id
    if not is_admin(chat_id):
        return
    set_state(chat_id, STATE_ADMIN_ADD_NAME)
    bot.send_message(chat_id, "🥦 <b>Sabzavot nomini kiriting:</b>", parse_mode="HTML", reply_markup=cancel_keyboard())

@bot.message_handler(func=lambda m: m.text == "✏️ Sabzavotlarni tahrirlash")
def admin_edit_list(msg):
    chat_id = msg.chat.id
    if not is_admin(chat_id):
        return
    products = db.get_all_products()
    if not products:
        bot.send_message(chat_id, "❌ Hozircha sabzavotlar yo'q.")
        return
    kb = InlineKeyboardMarkup()
    for p in products:
        kb.add(InlineKeyboardButton(f"🥦 {p['name']} — {p['price']:,} so'm/kg", callback_data=f"admin_edit_{p['id']}"))
    bot.send_message(chat_id, "✏️ <b>Tahrirlash uchun sabzavotni tanlang:</b>", parse_mode="HTML", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📋 Barcha buyurtmalar")
def admin_all_orders(msg):
    chat_id = msg.chat.id
    if not is_admin(chat_id):
        return
    orders = db.get_all_orders()
    if not orders:
        bot.send_message(chat_id, "📭 Hozircha buyurtmalar yo'q.")
        return
    text = "📋 <b>Barcha buyurtmalar:</b>\n\n"
    for o in orders:
        text += (
            f"🔖 Buyurtma #{o['id']}\n"
            f"👤 {o['first_name']} {o['last_name']}\n"
            f"📞 {o['phone']}\n"
            f"📍 {o['address']}\n"
            f"🥦 {o['product_name']} — {o['quantity']} kg\n"
            f"💰 {o['total_price']:,} so'm\n"
            f"💳 To'lov: {o['payment_method']}\n"
            f"📅 {o['created_at']}\n"
            f"{'─'*30}\n"
        )
    bot.send_message(chat_id, text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu")
def back_to_main(msg):
    chat_id = msg.chat.id
    clear_state(chat_id)
    user = db.get_user(chat_id)
    if user:
        bot.send_message(
            chat_id,
            "🏠 Asosiy menyu:",
            reply_markup=main_menu_keyboard()
        )

# ===================== RO'YXATDAN O'TISH =====================

@bot.message_handler(func=lambda m: m.text == "❌ Bekor qilish")
def cancel_handler(msg):
    chat_id = msg.chat.id
    clear_state(chat_id)
    user = db.get_user(chat_id)
    if user:
        bot.send_message(chat_id, "✅ Bekor qilindi.", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(
            chat_id,
            "❌ Bekor qilindi. /start bosing.",
            reply_markup=types.ReplyKeyboardRemove()
        )

@bot.message_handler(content_types=["text"])
def text_handler(msg):
    chat_id = msg.chat.id
    state = get_state(chat_id)
    text = msg.text.strip()

    # ── ASOSIY MENYU TUGMALARI ──
    if text == "🛒 Sabzavotlar menyusi":
        show_products(msg)
        return
    if text == "📦 Mening buyurtmalarim":
        show_my_orders(msg)
        return
    if text == "👤 Mening ma'lumotlarim":
        show_my_info(msg)
        return

    # ── RO'YXATDAN O'TISH ──
    if state == STATE_REG_NAME:
        if len(text) < 2:
            bot.send_message(chat_id, "⚠️ Ism juda qisqa. Qaytadan kiriting:")
            return
        set_data(chat_id, "first_name", text)
        set_state(chat_id, STATE_REG_SURNAME)
        bot.send_message(chat_id, f"✅ Ism: <b>{text}</b>\n\n📝 <b>Familiyangizni kiriting:</b>", parse_mode="HTML")
        return

    if state == STATE_REG_SURNAME:
        if len(text) < 2:
            bot.send_message(chat_id, "⚠️ Familiya juda qisqa. Qaytadan kiriting:")
            return
        set_data(chat_id, "last_name", text)
        set_state(chat_id, STATE_REG_PHONE)
        bot.send_message(
            chat_id,
            f"✅ Familiya: <b>{text}</b>\n\n📱 <b>Telefon raqamingizni yuboring:</b>\n"
            f"<i>(Tugmani bosing yoki +998XXXXXXXXX formatida kiriting)</i>",
            parse_mode="HTML",
            reply_markup=phone_keyboard()
        )
        return

    if state == STATE_REG_PHONE:
        # Matn orqali telefon kiritilsa
        phone = text.replace(" ", "").replace("-", "")
        if not (phone.startswith("+998") and len(phone) == 13 and phone[1:].isdigit()):
            bot.send_message(chat_id, "⚠️ Noto'g'ri format. +998XXXXXXXXX ko'rinishida kiriting:")
            return
        set_data(chat_id, "phone", phone)
        set_state(chat_id, STATE_REG_ADDRESS)
        bot.send_message(
            chat_id,
            f"✅ Telefon: <b>{phone}</b>\n\n📍 <b>Manzilingizni kiriting:</b>\n"
            f"<i>(Masalan: Toshkent, Chilonzor tumani, Bog'ishamol ko'chasi 5-uy)</i>",
            parse_mode="HTML",
            reply_markup=cancel_keyboard()
        )
        return

    if state == STATE_REG_ADDRESS:
        if len(text) < 5:
            bot.send_message(chat_id, "⚠️ Manzil juda qisqa. To'liq manzil kiriting:")
            return
        set_data(chat_id, "address", text)
        # Saqlash
        d = get_data(chat_id)
        db.save_user(chat_id, d["first_name"], d["last_name"], d["phone"], d["address"])
        clear_state(chat_id)
        bot.send_message(
            chat_id,
            f"🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
            f"👤 Ism: <b>{d['first_name']} {d['last_name']}</b>\n"
            f"📞 Tel: <b>{d['phone']}</b>\n"
            f"📍 Manzil: <b>{d['address']}</b>\n\n"
            f"🌿 <b>Bizning sabzavotlarimiz bilan tanishing!</b>\n"
            f"Quyidagi menyudan foydalaning 👇",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        return

    # ── ADMIN HOLATLARI ──
    if state == STATE_ADMIN_ADD_NAME:
        if not is_admin(chat_id):
            return
        set_data(chat_id, "prod_name", text)
        set_state(chat_id, STATE_ADMIN_ADD_PRICE)
        bot.send_message(chat_id, f"✅ Nom: <b>{text}</b>\n\n💰 <b>Narxini kiriting (so'm/kg):</b>", parse_mode="HTML")
        return

    if state == STATE_ADMIN_ADD_PRICE:
        if not is_admin(chat_id):
            return
        if not text.isdigit():
            bot.send_message(chat_id, "⚠️ Narx faqat raqam bo'lishi kerak:")
            return
        set_data(chat_id, "prod_price", int(text))
        set_state(chat_id, STATE_ADMIN_ADD_PHOTO)
        bot.send_message(chat_id, f"✅ Narx: <b>{int(text):,} so'm/kg</b>\n\n🖼 <b>Rasmini yuboring:</b>", parse_mode="HTML")
        return

    if state == STATE_ADMIN_EDIT_NAME:
        if not is_admin(chat_id):
            return
        prod_id = get_data(chat_id, "edit_prod_id")
        db.update_product_name(prod_id, text)
        clear_state(chat_id)
        bot.send_message(chat_id, f"✅ Nom <b>{text}</b> ga o'zgartirildi!", parse_mode="HTML", reply_markup=admin_keyboard())
        return

    if state == STATE_ADMIN_EDIT_PRICE:
        if not is_admin(chat_id):
            return
        if not text.isdigit():
            bot.send_message(chat_id, "⚠️ Narx faqat raqam bo'lishi kerak:")
            return
        prod_id = get_data(chat_id, "edit_prod_id")
        db.update_product_price(prod_id, int(text))
        clear_state(chat_id)
        bot.send_message(chat_id, f"✅ Narx <b>{int(text):,} so'm/kg</b> ga o'zgartirildi!", parse_mode="HTML", reply_markup=admin_keyboard())
        return


@bot.message_handler(content_types=["contact"])
def contact_handler(msg):
    chat_id = msg.chat.id
    state = get_state(chat_id)
    if state != STATE_REG_PHONE:
        return
    phone = msg.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    set_data(chat_id, "phone", phone)
    set_state(chat_id, STATE_REG_ADDRESS)
    bot.send_message(
        chat_id,
        f"✅ Telefon: <b>{phone}</b>\n\n📍 <b>Manzilingizni kiriting:</b>\n"
        f"<i>(Masalan: Toshkent, Chilonzor tumani, Bog'ishamol ko'chasi 5-uy)</i>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@bot.message_handler(content_types=["photo"])
def photo_handler(msg):
    chat_id = msg.chat.id
    state = get_state(chat_id)

    if state == STATE_ADMIN_ADD_PHOTO:
        if not is_admin(chat_id):
            return
        photo_id = msg.photo[-1].file_id
        d = get_data(chat_id)
        db.add_product(d["prod_name"], d["prod_price"], photo_id)
        clear_state(chat_id)
        bot.send_message(
            chat_id,
            f"✅ <b>{d['prod_name']}</b> muvaffaqiyatli qo'shildi!\n"
            f"💰 Narx: <b>{d['prod_price']:,} so'm/kg</b>",
            parse_mode="HTML",
            reply_markup=admin_keyboard()
        )
        return

    if state == STATE_ADMIN_EDIT_PHOTO:
        if not is_admin(chat_id):
            return
        photo_id = msg.photo[-1].file_id
        prod_id = get_data(chat_id, "edit_prod_id")
        db.update_product_photo(prod_id, photo_id)
        clear_state(chat_id)
        bot.send_message(chat_id, "✅ Rasm muvaffaqiyatli yangilandi!", reply_markup=admin_keyboard())
        return

# ===================== SABZAVOTLAR MENYUSI =====================

def show_products(msg):
    chat_id = msg.chat.id
    user = db.get_user(chat_id)
    if not user:
        bot.send_message(chat_id, "⚠️ Avval ro'yxatdan o'ting. /start")
        return

    products = db.get_all_products()
    if not products:
        bot.send_message(chat_id, "😔 Hozircha sabzavotlar mavjud emas.\nTez orada qo'shiladi!")
        return

    bot.send_message(chat_id, "🌿 <b>Bizning sabzavotlarimiz:</b>", parse_mode="HTML")

    for p in products:
        caption = (
            f"🥦 <b>{p['name']}</b>\n"
            f"💰 Narx: <b>{p['price']:,} so'm/kg</b>\n\n"
            f"Miqdorni tanlang va <b>Sotib olish</b> tugmasini bosing:"
        )
        qty = 1
        kb = product_quantity_keyboard(p['id'], qty)
        try:
            bot.send_photo(chat_id, p['photo_id'], caption=caption, parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            logger.error(f"Rasm yuborishda xato: {e}")
            bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=kb)

# ===================== CALLBACK HANDLER =====================

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    # ── MIQDOR BOSHQARUVI ──
    if data.startswith("qty_plus_") or data.startswith("qty_minus_"):
        action, product_id = data.rsplit("_", 1)
        product_id = int(product_id)
        product = db.get_product(product_id)
        if not product:
            bot.answer_callback_query(call.id, "Sabzavot topilmadi!")
            return

        # Joriy miqdorni caption dan o'qish
        caption = call.message.caption or ""
        current_qty = 1
        for line in caption.split("\n"):
            if "kg" in line and "so'm" not in line:
                try:
                    current_qty = int(line.split()[0])
                except:
                    pass

        # Inline keyboard dan miqdorni o'qish
        try:
            mid_btn_text = call.message.reply_markup.keyboard[0][1].text
            current_qty = int(mid_btn_text.split()[1])
        except:
            current_qty = 1

        if "plus" in action:
            new_qty = current_qty + 1
        else:
            new_qty = max(1, current_qty - 1)

        total = new_qty * product["price"]
        new_caption = (
            f"🥦 <b>{product['name']}</b>\n"
            f"💰 Narx: <b>{product['price']:,} so'm/kg</b>\n"
            f"📦 Miqdor: <b>{new_qty} kg</b>\n"
            f"💵 Jami: <b>{total:,} so'm</b>\n\n"
            f"Miqdorni o'zgartirish uchun <b>+ / -</b> tugmalarini bosing:"
        )
        kb = product_quantity_keyboard(product_id, new_qty)
        try:
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=call.message.message_id,
                caption=new_caption,
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Caption edit xato: {e}")
        bot.answer_callback_query(call.id)
        return

    # ── SOTIB OLISH ──
    if data.startswith("buy_"):
        product_id = int(data.split("_")[1])
        product = db.get_product(product_id)
        if not product:
            bot.answer_callback_query(call.id, "Sabzavot topilmadi!")
            return

        try:
            mid_btn_text = call.message.reply_markup.keyboard[0][1].text
            qty = int(mid_btn_text.split()[1])
        except:
            qty = 1

        total = qty * product["price"]
        set_data(chat_id, "order_product_id", product_id)
        set_data(chat_id, "order_qty", qty)
        set_data(chat_id, "order_total", total)

        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            f"🛒 <b>Buyurtmangiz:</b>\n\n"
            f"🥦 {product['name']}\n"
            f"📦 {qty} kg × {product['price']:,} so'm\n"
            f"💵 Jami: <b>{total:,} so'm</b>\n\n"
            f"💳 <b>To'lov usulini tanlang:</b>",
            parse_mode="HTML",
            reply_markup=payment_keyboard()
        )
        return

    # ── TO'LOV USULI ──
    if data in ("pay_cash", "pay_card"):
        payment = "💵 Naqd pul" if data == "pay_cash" else "💳 Karta"
        user = db.get_user(chat_id)
        if not user:
            bot.answer_callback_query(call.id, "Avval ro'yxatdan o'ting!")
            return

        product_id = get_data(chat_id, "order_product_id")
        qty = get_data(chat_id, "order_qty")
        total = get_data(chat_id, "order_total")
        product = db.get_product(product_id)

        if not all([product_id, qty, total, product]):
            bot.answer_callback_query(call.id, "Xato! Qaytadan urinib ko'ring.")
            return

        # Buyurtmani saqlash
        order_id = db.save_order(
            user_id=chat_id,
            product_id=product_id,
            quantity=qty,
            total_price=total,
            payment_method=payment
        )

        bot.answer_callback_query(call.id, "✅ Buyurtma qabul qilindi!")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=(
                f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
                f"🔖 Buyurtma #{order_id}\n"
                f"🥦 {product['name']} — {qty} kg\n"
                f"💰 Jami: <b>{total:,} so'm</b>\n"
                f"💳 To'lov: <b>{payment}</b>\n\n"
                f"📞 Tez orada siz bilan bog'lanamiz!"
            ),
            parse_mode="HTML"
        )

        # Adminga xabar
        admin_text = (
            f"🔔 <b>YANGI BUYURTMA #{order_id}</b>\n\n"
            f"👤 Mijoz: <b>{user['first_name']} {user['last_name']}</b>\n"
            f"📞 Tel: <b>{user['phone']}</b>\n"
            f"📍 Manzil: <b>{user['address']}</b>\n"
            f"🥦 Mahsulot: <b>{product['name']}</b>\n"
            f"📦 Miqdor: <b>{qty} kg</b>\n"
            f"💰 Jami: <b>{total:,} so'm</b>\n"
            f"💳 To'lov: <b>{payment}</b>"
        )
        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, admin_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Admin ga xabar yuborishda xato: {e}")

        clear_state(chat_id)
        return

    # ── ADMIN TAHRIRLASH ──
    if data.startswith("admin_edit_"):
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "⛔ Ruxsat yo'q!")
            return
        product_id = int(data.split("_")[-1])
        product = db.get_product(product_id)
        if not product:
            bot.answer_callback_query(call.id, "Topilmadi!")
            return
        set_data(chat_id, "edit_prod_id", product_id)
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            f"✏️ <b>{product['name']}</b>\n💰 {product['price']:,} so'm/kg\n\nNimani o'zgartirmoqchisiz?",
            parse_mode="HTML",
            reply_markup=edit_product_field_keyboard(product_id)
        )
        return

    if data.startswith("edit_name_"):
        if not is_admin(chat_id):
            return
        prod_id = int(data.split("_")[-1])
        set_data(chat_id, "edit_prod_id", prod_id)
        set_state(chat_id, STATE_ADMIN_EDIT_NAME)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "✏️ <b>Yangi nomni kiriting:</b>", parse_mode="HTML")
        return

    if data.startswith("edit_price_"):
        if not is_admin(chat_id):
            return
        prod_id = int(data.split("_")[-1])
        set_data(chat_id, "edit_prod_id", prod_id)
        set_state(chat_id, STATE_ADMIN_EDIT_PRICE)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "💰 <b>Yangi narxni kiriting (so'm/kg):</b>", parse_mode="HTML")
        return

    if data.startswith("edit_photo_"):
        if not is_admin(chat_id):
            return
        prod_id = int(data.split("_")[-1])
        set_data(chat_id, "edit_prod_id", prod_id)
        set_state(chat_id, STATE_ADMIN_EDIT_PHOTO)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🖼 <b>Yangi rasmni yuboring:</b>", parse_mode="HTML")
        return

    if data.startswith("delete_prod_"):
        if not is_admin(chat_id):
            return
        prod_id = int(data.split("_")[-1])
        db.delete_product(prod_id)
        bot.answer_callback_query(call.id, "🗑 O'chirildi!")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="✅ Sabzavot o'chirildi."
        )
        return

    if data == "edit_back":
        bot.answer_callback_query(call.id)
        admin_edit_list_callback(call.message)
        return

def admin_edit_list_callback(msg):
    chat_id = msg.chat.id
    products = db.get_all_products()
    if not products:
        bot.send_message(chat_id, "❌ Hozircha sabzavotlar yo'q.")
        return
    kb = InlineKeyboardMarkup()
    for p in products:
        kb.add(InlineKeyboardButton(f"🥦 {p['name']} — {p['price']:,} so'm/kg", callback_data=f"admin_edit_{p['id']}"))
    bot.send_message(chat_id, "✏️ <b>Tahrirlash uchun sabzavotni tanlang:</b>", parse_mode="HTML", reply_markup=kb)

# ===================== FOYDALANUVCHI MA'LUMOTLARI =====================

def show_my_info(msg):
    chat_id = msg.chat.id
    user = db.get_user(chat_id)
    if not user:
        bot.send_message(chat_id, "⚠️ Avval ro'yxatdan o'ting. /start")
        return
    bot.send_message(
        chat_id,
        f"👤 <b>Mening ma'lumotlarim:</b>\n\n"
        f"📛 Ism: <b>{user['first_name']}</b>\n"
        f"📛 Familiya: <b>{user['last_name']}</b>\n"
        f"📞 Tel: <b>{user['phone']}</b>\n"
        f"📍 Manzil: <b>{user['address']}</b>\n"
        f"📅 Ro'yxatdan o'tgan: <b>{user['created_at']}</b>",
        parse_mode="HTML"
    )

def show_my_orders(msg):
    chat_id = msg.chat.id
    orders = db.get_user_orders(chat_id)
    if not orders:
        bot.send_message(chat_id, "📭 Siz hali buyurtma bermagansiz.")
        return
    text = "📦 <b>Mening buyurtmalarim:</b>\n\n"
    for o in orders:
        text += (
            f"🔖 #{o['id']} | {o['created_at'][:10]}\n"
            f"🥦 {o['product_name']} — {o['quantity']} kg\n"
            f"💰 {o['total_price']:,} so'm | {o['payment_method']}\n"
            f"{'─'*25}\n"
        )
    bot.send_message(chat_id, text, parse_mode="HTML")

# ===================== ISHGA TUSHIRISH =====================

if __name__ == "__main__":
    db.init_db()
    logger.info("✅ Bot ishga tushdi!")
    print("🤖 Sabzavot Savdo Boti ishga tushdi!")
    bot.infinity_polling(timeout=30, long_polling_timeout=15)