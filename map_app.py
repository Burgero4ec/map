import streamlit as st
import plotly.express as px
import pandas as pd
import logging

# --- ИМПОРТ ДАННЫХ ИЗ CONFIG ---
from config import FLAG_EMOJIS, EXTRA_COUNTRIES, iso_a2_to_flag


# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
def setup_logging():
    log_file = "app_logs.log"
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logger = logging.getLogger("MapAppLogger")
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    return logger


logger = setup_logging()

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(layout="wide", page_title="Карта Захвата Территорий (2026)")


# --- ЗАГРУЗКА ДАННЫХ КАРТЫ ---
@st.cache_data
def load_world_map_2026():
    logger.info("Загрузка данных из countries_2026.csv...")
    try:
        df = pd.read_csv('countries_2026.csv', encoding='utf-8')
        # Переименовываем колонки для совместимости
        df = df.rename(columns={
            'country_en': 'country',
            'country_ru': 'country_ru',
            'iso_alpha3': 'iso_a3',
            'iso_alpha2': 'iso_a2'
        })
        logger.info(f"Загружено стран: {len(df)}")
        return df
    except FileNotFoundError:
        logger.error("Файл countries_2026.csv не найден.")
        st.error("❌ Файл countries_2026.csv отсутствует. Поместите его в папку с приложением.")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        st.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()


df_countries = load_world_map_2026()

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ---
if 'occupied_countries' not in st.session_state:
    st.session_state.occupied_countries = []
    logger.info("Сессия инициирована. Список занятых стран пуст.")


# --- ФУНКЦИИ ---
def toggle_country(country_name, country_ru, iso_a3, iso_a2=None):
    current_list = st.session_state.occupied_countries
    exists = any(c['name'] == country_name for c in current_list)

    if exists:
        st.session_state.occupied_countries = [c for c in current_list if c['name'] != country_name]
        logger.info(f"Страна УБРАНА: {country_ru} ({country_name}, {iso_a3})")
        return False
    else:
        st.session_state.occupied_countries.append({
            'name': country_name,
            'country_ru': country_ru,
            'iso': iso_a3,
            'iso_a2': iso_a2
        })
        logger.info(f"Страна ЗАХВАЧЕНА: {country_ru} ({country_name}, {iso_a3})")
        return True


def get_flag_for_country(iso_a3, iso_a2=None):
    """Получить флаг для страны"""
    # Сначала пробуем из готового словаря
    if iso_a3 in FLAG_EMOJIS:
        return FLAG_EMOJIS[iso_a3]
    # Если есть 2-буквенный код - генерируем флаг
    if iso_a2:
        return iso_a2_to_flag(iso_a2)
    return '🏳️'


def generate_map():
    if df_countries.empty:
        return None

    df_map = df_countries.copy()
    occupied_names = [c['name'] for c in st.session_state.occupied_countries]
    df_map['occupied'] = df_map['country'].apply(lambda x: 1 if x in occupied_names else 0)

    color_map = {0: '#e0e0e0', 1: '#ff4b4b'}

    fig = px.choropleth(
        df_map,
        locations="iso_a3",
        locationmode="ISO-3",
        color="occupied",
        color_discrete_map=color_map,
        projection="natural earth",
        hover_name="country",
        hover_data={'occupied': False},
        title="🗺️ Карта захвата территорий (2026)"
    )

    fig.update_geos(
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="white",
        showlakes=True,
        lakecolor="white"
    )

    fig.update_layout(
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        coloraxis_showscale=False
    )

    return fig


# --- ОБРАБОТКА КЛИКА ---
def handle_click(map_data):
    if map_data is not None and 'points' in map_data:
        point = map_data['points'][0]
        iso_code = point['location']
        row = df_countries[df_countries['iso_a3'] == iso_code]
        if not row.empty:
            row = row.iloc[0]
            country_name = row['country']
            country_ru = row.get('country_ru', country_name)
            iso_a2 = row.get('iso_a2')
            toggle_country(country_name, country_ru, iso_code, iso_a2)
            st.rerun()


# --- ИНТЕРФЕЙС ---
st.sidebar.header("🎮 Управление")

if df_countries.empty:
    st.error("❌ Не удалось загрузить данные карты. Проверьте наличие файла countries_2026.csv.")
    st.stop()

# Информация о данных
with st.sidebar.expander("📊 Информация"):
    st.write(f"📁 Стран в CSV: {len(df_countries)}")
    st.write(f"🚩 Занято: {len(st.session_state.occupied_countries)}")
    st.write(f"🏳️ Флагов в базе: {len(FLAG_EMOJIS)}")

# 1. Поиск (на русском и английском)
search_query = st.sidebar.text_input(
    "🔍 Поиск страны",
    placeholder="Например: Россия или Russia"
)

if search_query:
    # Поиск по обоим полям: country (англ) и country_ru (рус)
    matches_en = df_countries[df_countries['country'].str.contains(search_query, case=False, na=False)]
    matches_ru = df_countries[df_countries['country_ru'].str.contains(search_query, case=False, na=False)]

    # Объединяем результаты
    matches = pd.concat([matches_en, matches_ru]).drop_duplicates()

    if not matches.empty:
        row = matches.iloc[0]
        country_name = row['country']
        country_ru = row.get('country_ru', country_name)
        country_iso3 = row['iso_a3']
        country_iso2 = row.get('iso_a2')

        # Отображаем русское название если есть
        display_name = country_ru if country_ru and pd.notna(country_ru) else country_name
        flag = get_flag_for_country(country_iso3, country_iso2)
        st.sidebar.success(f"✅ Найдено: {flag} {display_name}")

        is_occupied = any(c['name'] == country_name for c in st.session_state.occupied_countries)
        btn_label = "❌ Убрать территорию" if is_occupied else "✅ Захватить территорию"

        if st.sidebar.button(btn_label, key="search_action"):
            toggle_country(country_name, country_ru, country_iso3, country_iso2)
            st.rerun()
    else:
        st.sidebar.warning("Страна не найдена")
        logger.warning(f"Страна НЕ НАЙДЕНА в поиске: {search_query}")

st.sidebar.divider()

# 2. Список занятых
st.sidebar.subheader(f"🚩 Занято стран: {len(st.session_state.occupied_countries)}")
if st.session_state.occupied_countries:
    for c in st.session_state.occupied_countries:
        flag = get_flag_for_country(c['iso'], c.get('iso_a2'))
        display_name = c.get('country_ru', c['name'])
        st.sidebar.write(f"{flag} {display_name}")

    if st.sidebar.button("🗑️ Очистить всё"):
        count = len(st.session_state.occupied_countries)
        st.session_state.occupied_countries = []
        logger.info(f"ВСЕ СТРАНЫ ОЧИЩЕНЫ. Всего удалено: {count}")
        st.rerun()
else:
    st.sidebar.info("Список пуст")

st.sidebar.divider()

# 3. Экспорт карты
st.sidebar.markdown("### 📥 Экспорт")
if st.sidebar.button("📸 Скачать PNG"):
    fig = generate_map()
    if fig:
        try:
            img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
            st.sidebar.download_button(
                label="⬇️ Скачать файл",
                data=img_bytes,
                file_name="conquered_map_2026.png",
                mime="image/png"
            )
            logger.info("Карта экспортирована в PNG")
        except Exception as e:
            st.sidebar.error(f"Ошибка: {e}")
            logger.error(f"Ошибка экспорта PNG: {e}")

# --- ОСНОВНАЯ ОБЛАСТЬ ---
st.title("🌍 Интерактивная Карта Захвата (2026)")
st.markdown("""
**Инструкция:**
1. Используйте поиск слева для нахождения страны (**можно на русском!**)
2. Или **кликните по стране на карте**, чтобы захватить её
3. Занятые страны подсвечиваются **красным цветом**
4. Скачайте итоговую карту в формате PNG
""")

fig = generate_map()

if fig:
    st.plotly_chart(fig, width="stretch", on_click=handle_click)
    st.info("💡 **Совет:** Кликните по любой стране на карте, чтобы захватить её!")

    if st.session_state.occupied_countries:
        st.subheader("🚩 Ваши владения:")
        cols = st.columns(min(5, len(st.session_state.occupied_countries)))
        for i, c in enumerate(st.session_state.occupied_countries):
            with cols[i % 5]:
                flag = get_flag_for_country(c['iso'], c.get('iso_a2'))
                display_name = c.get('country_ru', c['name'])
                st.metric(label=flag, value=display_name)
else:
    st.warning("Карта не может быть отображена из-за ошибки загрузки данных.")

logger.info(f"Приложение запущено. Занято стран: {len(st.session_state.occupied_countries)}")