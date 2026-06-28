import streamlit as st
import pandas as pd
import asyncio
import io
from aiogram import Bot

# ─── Конфигурация страницы ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Рассылка расписаний",
    page_icon="🏀",
    layout="centered",
)

# ─── Кастомные стили (Светлая тема) ─────────────────────────────────────────
st.markdown("""
<style>
/* Основной фон и шрифт */
.stApp { background: #f8fafc; color: #1e293b; }

/* Заголовок */
.main-title {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
}
.main-sub {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 32px;
}

/* Карточки-секции */
.section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);
}
.section-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #475569;
    margin-bottom: 14px;
}

/* Статус файла */
.file-ok {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    padding: 14px 18px;
    color: #166534;
    font-size: 14px;
    font-weight: 600;
    margin-top: 10px;
}
.file-none {
    background: #f8fafc;
    border: 1px dashed #cbd5e1;
    border-radius: 12px;
    padding: 16px;
    color: #64748b;
    font-size: 14px;
    margin-top: 10px;
    text-align: center;
}

/* Карточки итогов */
.result-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 20px;
}
.result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px 12px;
    text-align: center;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
}
.result-val {
    font-size: 34px;
    font-weight: 800;
    display: block;
    line-height: 1;
}
.result-lbl {
    font-size: 11px;
    color: #64748b;
    margin-top: 8px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}
.val-ok   { color: #10b981; }
.val-skip { color: #f59e0b; }
.val-err  { color: #ef4444; }

/* Лог */
.log-entry {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
    font-size: 13px;
    font-weight: 500;
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 8px;
    line-height: 1.5;
    border: 1px solid transparent;
}
.log-ok   { background: #f0fdf4; color: #166534; border-color: #dcfce7; }
.log-err  { background: #fef2f2; color: #991b1b; border-color: #fee2e2; }
.log-warn { background: #fffbec; color: #92400e; border-color: #fef3c7; }
.log-info { background: #f0f9ff; color: #075985; border-color: #e0f2fe; }

/* Адаптация дефолтных элементов ввода Streamlit под светлую тему */
div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border-radius: 10px !important;
}
button[kind="primary"] {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
}
button[kind="secondary"] {
    border-radius: 10px !important;
}

/* Скрыть стандартные элементы streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 3rem; max-width: 680px; }
</style>
""", unsafe_allow_html=True)


# ─── Утилиты ─────────────────────────────────────────────────────────────────

def escape_markdown(text: str) -> str:
    special = ['_','*','[',']','(',')','~','`','>','#','+','-','=','|','{','}','.','!']
    for c in special:
        text = text.replace(c, f'\\{c}')
    return text

def get_match_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:   return "матч"
    if count % 10 in [2,3,4] and count % 100 not in [12,13,14]: return "матча"
    return "матчей"

def get_operator_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:   return "оператор"
    if count % 10 in [2,3,4] and count % 100 not in [12,13,14]: return "оператора"
    return "операторов"

def build_messages(name: str, group: pd.DataFrame) -> list[str]:
    numbers = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    matches_count = len(group)
    current_msg = (
        f"🏀 *Привет, {escape_markdown(name)}\\!*\n"
        f"📊 Завтра у тебя *{matches_count}* {escape_markdown(get_match_word(matches_count))}\n\n"
    )
    messages = []

    for idx, (_, row) in enumerate(group.iterrows()):
        raw_dt = row['Дата начала']
        if pd.isna(raw_dt):
            time_val = "??:??"
        elif isinstance(raw_dt, pd.Timestamp):
            time_val = raw_dt.strftime('%H:%M')
        else:
            time_val = str(raw_dt).split(' ')[-1][:5]

        event_name  = escape_markdown(str(row['Название события']))
        competition = escape_markdown(str(row['Соревнование']))
        number_emoji = numbers[idx] if idx < 10 else f"{idx+1}\\."

        block = (
            f"{number_emoji} *{escape_markdown(time_val)}* — {event_name}\n"
            f"    🏆 {competition}\n\n"
        )

        if len(current_msg) + len(block) > 3900:
            messages.append(current_msg)
            current_msg = block
        else:
            current_msg += block

    footer = "\n🚀 *Удачи на смене\\!*"
    if len(current_msg) + len(footer) > 4000:
        messages.append(current_msg)
        messages.append(footer)
    else:
        messages.append(current_msg + footer)

    return messages


# ─── Асинхронная функция рассылки ────────────────────────────────────────────

async def send_schedules(token: str, admin_id: int, user_ids: dict,
                         df: pd.DataFrame, log_callback):
    bot = Bot(token=token)
    sent_count = error_count = skipped_count = total_matches = 0

    try:
        required_cols = ['Оператор', 'Дата начала', 'Название события', 'Соревнование']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            log_callback('err', f"Отсутствуют колонки: {missing}")
            return 0, 0, 0, 0

        grouped = df.groupby('Оператор')

        for operator_name, group in grouped:
            name_clean  = str(operator_name).strip()
            matches_count = len(group)
            total_matches += matches_count

            if name_clean not in user_ids:
                log_callback('warn', f"{name_clean} — не найден в списке ({matches_count} матчей)")
                skipped_count += 1
                continue

            target_id = user_ids[name_clean]
            messages  = build_messages(name_clean, group)
            op_ok     = True

            for part in messages:
                try:
                    await bot.send_message(chat_id=target_id, text=part, parse_mode="MarkdownV2")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    log_callback('warn', f"{name_clean}: ошибка форматирования, пробую plain...")
                    try:
                        clean = part.replace('*','').replace('\\','')
                        await bot.send_message(chat_id=target_id, text=clean)
                    except Exception as e2:
                        log_callback('err', f"{name_clean}: {e2}")
                        op_ok = False
                        error_count += 1

            if op_ok:
                sent_count += 1
                log_callback('ok', f"{name_clean} — отправлено ({matches_count} {get_match_word(matches_count)})")

        # Отчёт администратору
        summary  = f"📬 *Рассылка завершена\\!*\n\n"
        summary += f"✅ Отправлено: *{sent_count}* {escape_markdown(get_operator_word(sent_count))}\n"
        summary += f"📊 Всего матчей: *{total_matches}*\n"
        if skipped_count > 0:
            summary += f"⚠️ Пропущено: *{skipped_count}* {escape_markdown(get_operator_word(skipped_count))}\n"
        summary += "✨ Ошибок нет\\!\n" if error_count == 0 else f"❌ Ошибок: *{error_count}*\n"

        await bot.send_message(chat_id=admin_id, text=summary, parse_mode="MarkdownV2")
        log_callback('info', "Итоговый отчёт отправлен администратору")

    except Exception as e:
        log_callback('err', f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

    return sent_count, error_count, skipped_count, total_matches


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ─── Секреты ─────────────────────────────────────────────────────────────────
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    ADMIN_ID  = int(st.secrets["ADMIN_ID"])
except KeyError as e:
    st.error(f"❌ Не найден секрет: {e}. Добавь BOT_TOKEN and ADMIN_ID в Streamlit Secrets.")
    st.stop()

# ─── Состояние сессии ─────────────────────────────────────────────────────────
if 'operators' not in st.session_state:
    st.session_state.operators = [
        {'name': 'Tigran', 'id': '5980876264'},
        {'name': 'Taron',  'id': '1014173917'},
    ]
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'results' not in st.session_state:
    st.session_state.results = None


# ─── UI ───────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🚀 Панель рассылки расписаний операторов</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Загрузи файл — нажми кнопку — операторы получат расписание в Telegram</div>', unsafe_allow_html=True)

# ── Загрузка файла
st.markdown('<div class="section-card"><div class="section-label">Файл расписания (.xlsx)</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")

if uploaded_file:
    st.markdown(f'<div class="file-ok">✅ &nbsp;{uploaded_file.name}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="file-none">📂 &nbsp;Перетащи файл сюда или нажми «Browse files»</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Операторы
st.markdown('<div class="section-card"><div class="section-label">Операторы и их Telegram ID</div>', unsafe_allow_html=True)

ops = st.session_state.operators
to_delete = None

for i, op in enumerate(ops):
    c1, c2, c3 = st.columns([3, 3, 0.7])
    with c1:
        ops[i]['name'] = st.text_input(f"Имя_{i}", value=op['name'],
                                        placeholder="Имя (как в файле)",
                                        label_visibility="collapsed", key=f"op_name_{i}")
    with c2:
        ops[i]['id'] = st.text_input(f"ID_{i}", value=op['id'],
                                      placeholder="Telegram User ID",
                                      label_visibility="collapsed", key=f"op_id_{i}")
    with c3:
        if st.button("✕", key=f"del_{i}", help="Удалить"):
            to_delete = i

if to_delete is not None:
    st.session_state.operators.pop(to_delete)
    st.rerun()

if st.button("＋ Добавить оператора", use_container_width=True):
    st.session_state.operators.append({'name': '', 'id': ''})
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Кнопка запуска
can_send = bool(uploaded_file)

if st.button("⚡️ Запустить рассылку в Telegram",
             use_container_width=True,
             disabled=not can_send,
             type="primary"):

    st.session_state.logs = []
    st.session_state.results = None

    user_ids = {op['name'].strip(): op['id'].strip()
                for op in st.session_state.operators
                if op['name'].strip() and op['id'].strip()}

    df = pd.read_excel(io.BytesIO(uploaded_file.read()), engine='openpyxl')

    log_container = st.container()
    log_entries   = []

    def log_callback(kind, msg):
        icons = {'ok':'✅', 'err':'❌', 'warn':'⚠️', 'info':'ℹ️'}
        log_entries.append((kind, f"{icons.get(kind,'')} {msg}"))
        st.session_state.logs = log_entries[:]
        with log_container:
            css_class = {'ok':'log-ok','err':'log-err','warn':'log-warn','info':'log-info'}.get(kind,'log-info')
            st.markdown(
                f'<div class="log-entry {css_class}">{icons.get(kind,"")} {msg}</div>',
                unsafe_allow_html=True
            )

    with st.spinner("Отправляю сообщения..."):
        sent, errors, skipped, total = run_async(
            send_schedules(
                token        = BOT_TOKEN,
                admin_id     = ADMIN_ID,
                user_ids     = user_ids,
                df           = df,
                log_callback = log_callback,
            )
        )

    st.session_state.results = (sent, errors, skipped, total)

# ── Итоги
if st.session_state.results:
    sent, errors, skipped, total = st.session_state.results
    st.markdown("---")
    st.markdown("<h4 style='color: #0f172a;'>📊 Итоги рассылки</h4>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="result-grid">
        <div class="result-card">
            <span class="result-val val-ok">{sent}</span>
            <div class="result-lbl">Отправлено</div>
        </div>
        <div class="result-card">
            <span class="result-val val-skip">{skipped}</span>
            <div class="result-lbl">Пропущено</div>
        </div>
        <div class="result-card">
            <span class="result-val val-err">{errors}</span>
            <div class="result-lbl">Ошибок</div>
        </div>
    </div>
    <div class="result-card" style="margin-top:14px; background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:16px 20px; text-align:center;">
        <span style="color:#0284c7; font-size:15px; font-weight:700;">📊 Всего матчей в файле: {total}</span>
    </div>
    """, unsafe_allow_html=True)

    if errors == 0:
        st.success("✅ Рассылка завершена без ошибок!")
    else:
        st.warning(f"⚠️ Рассылка завершена с {errors} ошибками. Проверь лог выше.")
