import streamlit as st
import pandas as pd
import asyncio
import io
import datetime
from aiogram import Bot

# ─── Словарь автоботов ────────────────────────────────────────────────────────
AUTOBOT_MAP = {
    'Taron': 'autobot45', 'Erik': 'autobot46', 'Tiko Ap.': 'autobot47',
    'Lyov': 'autobot48', 'Levon': 'autobot61', 'Grigor': 'autobot69',
    'Hovo': 'autobot71', 'Hayk': 'autobot72', 'Hakob': 'autobot88',
    'Manvel': 'autobot113', 'Hrant': 'autobot114', 'Davo': 'autobot133',
    'Azat': 'autobot135', 'Artur': 'autobot149', 'Karen': 'autobot150',
    'Edo': 'autobot151', 'Vahe-2': 'autobot152', 'Tiko H.': 'autobot173',
    'Ando': 'autobot174', 'Arkadi': 'autobot177', 'Artur2': 'autobot178',
    'Hovo2': 'autobot179', 'Aren': 'autobot190', 'Jor': 'autobot191',
    'Davit': 'autobot192', 'Abul': 'autobot198', 'Mariam': 'autobot222',
    'Garegin': 'autobot237', 'Hayk-2': 'autobot238', 'Vahe-3': 'autobot239',
    'Vahe-4': 'autobot240', 'Vrej-2': 'autobot241', 'Jor-2': 'autobot242',
    'Lilit': 'autobot243', 'Seroj': 'autobot244', 'Davo-2': 'autobot247',
    'Gor': 'autobot293', 'Liparit': 'autobot294', 'Razmik': 'autobot295',
    'Gevorg': 'autobot296', 'Hamlet': 'autobot323', 'Arshak': 'autobot324',
}

# ─── Конфигурация страницы ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Рассылка расписаний",
    page_icon="🏀",
    layout="centered",
)

# ─── Кастомные стили (Светлая тема) ─────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: #f8fafc; color: #1e293b; }
.main-title { font-size: 28px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; margin-bottom: 6px; }
.main-sub { font-size: 14px; color: #64748b; margin-bottom: 32px; }
.section-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px;
    padding: 24px 28px; margin-bottom: 20px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}
.section-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #475569; margin-bottom: 14px; }
.file-ok { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 14px 18px; color: #166534; font-size: 14px; font-weight: 600; margin-top: 10px; }
.file-none { background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px; padding: 16px; color: #64748b; font-size: 14px; margin-top: 10px; text-align: center; }
.result-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
.result-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px 12px; text-align: center; }
.result-val { font-size: 34px; font-weight: 800; display: block; line-height: 1; }
.result-lbl { font-size: 11px; color: #64748b; margin-top: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.7px; }
.val-ok { color: #10b981; } .val-skip { color: #f59e0b; } .val-err { color: #ef4444; }
.log-entry { font-family: -apple-system, sans-serif; font-size: 13px; font-weight: 500; padding: 10px 14px; border-radius: 10px; margin-bottom: 8px; border: 1px solid transparent; }
.log-ok { background: #f0fdf4; color: #166534; border-color: #dcfce7; }
.log-err { background: #fef2f2; color: #991b1b; border-color: #fee2e2; }
.log-warn { background: #fffbec; color: #92400e; border-color: #fef3c7; }
.log-info { background: #f0f9ff; color: #075985; border-color: #e0f2fe; }

div[data-baseweb="input"], div[data-baseweb="textarea"] { background-color: #ffffff !important; border-radius: 10px !important; }
button[kind="primary"] {
    background-color: #2563eb !important; border-color: #2563eb !important; color: white !important;
    border-radius: 12px !important; font-weight: 600 !important; padding: 0.5rem 1rem !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
}
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

def format_duration(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}:{mins:02d}:00"


# ─── ЯДРО АВТОМАТИЧЕСКОГО РАСЧЕТА ───────────────────────────────────────────

def calculate_sheet_logic(df: pd.DataFrame) -> pd.DataFrame:
    df['Оператор'] = df['Оператор'].astype(str).str.strip()

    def parse_start_time(val):
        val_str = str(val).strip()
        if '-' in val_str:
            val_str = val_str.split('-')[0].strip()
        try:
            return pd.to_datetime(val_str)
        except:
            try:
                t = datetime.time.fromisoformat(val_str[:5])
                return datetime.datetime.combine(datetime.date.today(), t)
            except:
                return pd.NaT

    df['Parsed_Start'] = df['Дата начала'].apply(parse_start_time)
    calculated_rows = []
    grouped = df.groupby('Оператор')

    for name, group in grouped:
        if name == 'nan' or not name:
            continue

        group_sorted = group.sort_values('Parsed_Start')
        min_dt = group_sorted['Parsed_Start'].min()
        max_dt = group_sorted['Parsed_Start'].max()
        match_count = len(group_sorted)

        last_competition = str(group_sorted.iloc[-1]['Соревнование']).upper()

        if "NBA" in last_competition or "НБА" in last_competition:
            match_duration_mins = 150  # 2 часа 30 минут
        else:
            match_duration_mins = 120  # 2 часа

        if pd.notna(min_dt) and pd.notna(max_dt):
            time_diff_mins = int((max_dt - min_dt).total_seconds() / 60)
            total_minutes = time_diff_mins + match_duration_mins
        else:
            total_minutes = 0

        calculated_rows.append({
            'Имя': name,
            'Первый_Матч': min_dt.strftime('%d.%m.%Y %H:%M:%S') if pd.notna(min_dt) else "??:??",
            'Последний_Матч': max_dt.strftime('%d.%m.%Y %H:%M:%S') if pd.notna(max_dt) else "??:??",
            'Количество': match_count,
            'Отработано_Формат': format_duration(total_minutes),
            'Отработано_Минуты': total_minutes,
            'Автобот': AUTOBOT_MAP.get(name, '—'),
        })

    return pd.DataFrame(calculated_rows)


def build_messages(name: str, group: pd.DataFrame, calc_info: dict, header_template: str, footer_template: str) -> list[str]:
    numbers = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    matches_count = calc_info['Количество']
    match_word = get_match_word(matches_count)

    header_filled = header_template.replace("{Имя}", name)\
                                   .replace("{Количество}", str(matches_count))\
                                   .replace("{Слово_Матч}", match_word)\
                                   .replace("{Часы_Минуты}", calc_info['Отработано_Формат'])\
                                   .replace("{Минуты}", str(calc_info['Отработано_Минуты']))

    current_msg = escape_markdown(header_filled) + "\n\n"
    messages = []

    for idx, (_, row) in enumerate(group.sort_values('Parsed_Start').iterrows()):
        raw_dt = row['Дата начала']
        if pd.isna(raw_dt): time_val = "??:??"
        elif isinstance(raw_dt, pd.Timestamp): time_val = raw_dt.strftime('%H:%M')
        else: time_val = str(raw_dt).split(' ')[-1][:5]

        event_name  = escape_markdown(str(row['Название события']))
        competition = escape_markdown(str(row['Соревнование']))
        number_emoji = numbers[idx] if idx < 10 else f"{idx+1}\\."

        block = f"{number_emoji} *{escape_markdown(time_val)}* — {event_name}\n    🏆 {competition}\n\n"

        if len(current_msg) + len(block) > 3900:
            messages.append(current_msg)
            current_msg = block
        else:
            current_msg += block

    footer_escaped = "\n" + escape_markdown(footer_template)
    if len(current_msg) + len(footer_escaped) > 4000:
        messages.append(current_msg)
        messages.append(footer_escaped)
    else:
        messages.append(current_msg + footer_escaped)

    return messages


# ─── Асинхронная функция рассылки ────────────────────────────────────────────

async def send_schedules(token: str, admin_id: int, user_ids: dict,
                         df: pd.DataFrame, calc_df: pd.DataFrame, header_template: str, footer_template: str, log_callback):
    bot = Bot(token=token)
    sent_count = error_count = skipped_count = total_matches = 0

    try:
        grouped = df.groupby('Оператор')

        for operator_name, group in grouped:
            name_clean = str(operator_name).strip()
            if name_clean == 'nan' or not name_clean: continue

            if name_clean not in user_ids:
                log_callback('warn', f"{name_clean} — не найден в списке Telegram ID")
                skipped_count += 1
                continue

            op_calc = calc_df[calc_df['Имя'] == name_clean].iloc[0].to_dict()
            total_matches += op_calc['Количество']

            target_id = user_ids[name_clean]
            messages  = build_messages(name_clean, group, op_calc, header_template, footer_template)
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
                log_callback('ok', f"{name_clean} — отправлено (Отработано: {op_calc['Отработано_Формат']})")

        summary  = f"📬 *Рассылка завершена\\!*\n\n"
        summary += f"✅ Отправлено: *{sent_count}* {escape_markdown(get_operator_word(sent_count))}\n"
        summary += f"📊 Всего матчей обработано: *{total_matches}*\n"
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
    st.error(f"❌ Не найден секрет: {e}. Добавь BOT_TOKEN и ADMIN_ID в Streamlit Secrets.")
    st.stop()

# ─── Состояние сессии ─────────────────────────────────────────────────────────
if 'operators' not in st.session_state:
    st.session_state.operators = [
        {'name': 'Tigran', 'id': '5980876264'},
        {'name': 'Taron',  'id': '1014173917'},
        {'name': 'Lilit',  'id': '5980876264'},
        {'name': 'Artur2', 'id': '1122334455'}
    ]
if 'logs' not in st.session_state: st.session_state.logs = []
if 'results' not in st.session_state: st.session_state.results = None

if 'header_template' not in st.session_state:
    st.session_state.header_template = "🏀 Привет, {Имя}!\n⏱ Твое время смены: {Часы_Минуты} ({Минуты} мин)\n📊 Завтра у тебя {Количество} {Слово_Матч}:"
if 'footer_template' not in st.session_state:
    st.session_state.footer_template = "🚀 Удачи на смене!"


# ─── UI INTERFACE ─────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🚀 Расчет и Рассылка Графика Трейдинга</div>', unsafe_allow_html=True)
st.markdown('<div class="main-sub">Закинь файл с матчами — система сама рассчитает часы, минуты и разошлет уведомления</div>', unsafe_allow_html=True)

# ── БЛОК 1: Настройка шаблона
st.markdown('<div class="section-card"><div class="section-label">⚙️ Настройка шаблона сообщения</div>', unsafe_allow_html=True)
st.caption("Доступны авто-переменные: `{Имя}`, `{Количество}`, `{Слово_Матч}`, `{Часы_Минуты}` (ЧЧ:ММ:СС), `{Минуты}` (числом)")

st.session_state.header_template = st.text_area("Верхняя часть сообщения", value=st.session_state.header_template, height=90)
st.session_state.footer_template = st.text_input("Нижняя часть сообщения (Напутствие)", value=st.session_state.footer_template)
st.markdown('</div>', unsafe_allow_html=True)

# ── БЛОК 2: Загрузка файла и Расчёт
st.markdown('<div class="section-card"><div class="section-label">Загрузка файла с расписанием</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")

calc_df_global = None
df_source_global = None

if uploaded_file:
    st.markdown(f'<div class="file-ok">✅ &nbsp;{uploaded_file.name} загружен</div>', unsafe_allow_html=True)
    df_source_global = pd.read_excel(io.BytesIO(uploaded_file.read()), engine='openpyxl')

    required_cols = ['Оператор', 'Дата начала', 'Название события', 'Соревнование']
    if all(c in df_source_global.columns for c in required_cols):
        calc_df_global = calculate_sheet_logic(df_source_global)

        # Сортировка по времени первого матча
        calc_df_global['_sort'] = pd.to_datetime(
            calc_df_global['Первый_Матч'], format='%d.%m.%Y %H:%M:%S', errors='coerce'
        )
        calc_df_global = calc_df_global.sort_values('_sort').drop(columns='_sort').reset_index(drop=True)

        st.markdown("<br><div class='section-label'>📊 Автоматический расчет таблицы:</div>", unsafe_allow_html=True)

        def style_hours(row):
            minutes = row['Отработано_Минуты']
            hours = minutes / 60
            if hours >= 8:
                bg_color = 'background-color: #d1fae5; color: #065f46;'
            elif 6 <= hours < 8:
                bg_color = 'background-color: #fef3c7; color: #92400e;'
            else:
                bg_color = 'background-color: #fee2e2; color: #991b1b;'
            return [bg_color] * len(row)

        styled_calc_df = calc_df_global.style.apply(style_hours, axis=1)

        st.dataframe(
            styled_calc_df,
            column_config={
                "Имя": "Оператор",
                "Первый_Матч": "Приход",
                "Последний_Матч": "Уход (посл. матч)",
                "Количество": "Матчи",
                "Отработано_Формат": "Часы:Мин",
                "Отработано_Минуты": "Всего Минут",
                "Автобот": "Автобот",
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.error(f"Ошибка! В файле отсутствуют нужные колонки: {required_cols}")
else:
    st.markdown('<div class="file-none">📂 &nbsp;Перетащи сюда .xlsx файл, выгруженный из системы</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── БЛОК 3: Операторы
st.markdown('<div class="section-card"><div class="section-label">База операторов (Telegram ID)</div>', unsafe_allow_html=True)

ops = st.session_state.operators
to_delete = None

for i, op in enumerate(ops):
    c1, c2, c3 = st.columns([3, 3, 0.7])
    with c1: ops[i]['name'] = st.text_input(f"Имя_{i}", value=op['name'], placeholder="Имя", label_visibility="collapsed", key=f"op_name_{i}")
    with c2: ops[i]['id'] = st.text_input(f"ID_{i}", value=op['id'], placeholder="Telegram ID", label_visibility="collapsed", key=f"op_id_{i}")
    with c3:
        if st.button("✕", key=f"del_{i}"): to_delete = i

if to_delete is not None:
    st.session_state.operators.pop(to_delete)
    st.rerun()

if st.button("＋ Добавить нового оператора", use_container_width=True):
    st.session_state.operators.append({'name': '', 'id': ''})
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ── БЛОК 4: Запуск рассылки
can_send = calc_df_global is not None

if st.button("⚡️ Утвердить расчет и запустить рассылку", use_container_width=True, disabled=not can_send, type="primary"):
    st.session_state.logs = []
    st.session_state.results = None

    user_ids = {op['name'].strip(): op['id'].strip() for op in st.session_state.operators if op['name'].strip() and op['id'].strip()}

    log_container = st.container()
    log_entries   = []

    def log_callback(kind, msg):
        icons = {'ok':'✅', 'err':'❌', 'warn':'⚠️', 'info':'ℹ️'}
        log_entries.append((kind, f"{icons.get(kind,'')} {msg}"))
        st.session_state.logs = log_entries[:]
        with log_container:
            css_class = {'ok':'log-ok','err':'log-err','warn':'log-warn','info':'log-info'}.get(kind,'log-info')
            st.markdown(f'<div class="log-entry {css_class}">{icons.get(kind,"")} {msg}</div>', unsafe_allow_html=True)

    with st.spinner("Запуск асинхронной отправки по операторам..."):
        sent, errors, skipped, total = run_async(
            send_schedules(
                token=BOT_TOKEN, admin_id=ADMIN_ID, user_ids=user_ids,
                df=df_source_global, calc_df=calc_df_global,
                header_template=st.session_state.header_template,
                footer_template=st.session_state.footer_template,
                log_callback=log_callback
            )
        )

    st.session_state.results = (sent, errors, skipped, total)

# ── Итоги рассылки
if st.session_state.results:
    sent, errors, skipped, total = st.session_state.results
    st.markdown("---")
    st.markdown(f"""
    <div class="result-grid">
        <div class="result-card"><span class="result-val val-ok">{sent}</span><div class="result-lbl">Успешно</div></div>
        <div class="result-card"><span class="result-val val-skip">{skipped}</span><div class="result-lbl">Пропущено</div></div>
        <div class="result-card"><span class="result-val val-err">{errors}</span><div class="result-lbl">Ошибки</div></div>
    </div>
    """, unsafe_allow_html=True)
    if errors == 0: st.success("🎉 Все уведомления доставлены успешно!")
