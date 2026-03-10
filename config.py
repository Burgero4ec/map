# config.py - Конфигурация и данные для карты
import pandas as pd
import os

# Путь к CSV файлу
CSV_FILE = os.path.join(os.path.dirname(__file__), 'countries_2026.csv')


def load_countries_from_csv():
    """Загрузка стран из CSV файла"""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            return df
        except Exception as e:
            print(f"⚠️ Ошибка чтения CSV: {e}")
            return None
    else:
        print(f"⚠️ Файл {CSV_FILE} не найден!")
        return None


def iso_a2_to_flag(iso_a2):
    """
    Конвертация ISO Alpha-2 кода в эмодзи флага
    Например: 'RU' → '🇷🇺', 'US' → '🇺🇸'
    """
    # Проверка на NaN (float) и пустые значения
    if iso_a2 is None or (isinstance(iso_a2, float) and pd.isna(iso_a2)):
        return '🏳️'

    # Преобразуем в строку
    iso_a2 = str(iso_a2).strip().upper()

    if len(iso_a2) != 2:
        return '🏳️'

    try:
        # Unicode региональные индикаторы
        flag = chr(ord(iso_a2[0]) + 127397) + chr(ord(iso_a2[1]) + 127397)
        return flag
    except:
        return '🏳️'


def get_flag_emojis():
    """Генерация словаря флагов из CSV"""
    df = load_countries_from_csv()
    if df is not None:
        flag_dict = {}
        for _, row in df.iterrows():
            iso_a3 = row.get('iso_alpha3', '')
            iso_a2 = row.get('iso_alpha2', '')
            if iso_a3:
                flag_dict[iso_a3] = iso_a2_to_flag(iso_a2)
        return flag_dict
    return {}


def get_extra_countries():
    """Загрузка дополнительных стран из CSV"""
    df = load_countries_from_csv()
    if df is not None:
        return df[['country_en', 'iso_alpha3']].rename(
            columns={'country_en': 'country', 'iso_alpha3': 'iso_a3'}
        ).to_dict('records')
    return []


def get_all_countries_dict():
    """Получить словарь всех стран {название: ISO}"""
    df = load_countries_from_csv()
    if df is not None:
        return dict(zip(df['country_en'], df['iso_alpha3']))
    return {}


# Для обратной совместимости
FLAG_EMOJIS = get_flag_emojis()
EXTRA_COUNTRIES = get_extra_countries()
ALL_COUNTRIES = get_all_countries_dict()

# Информация для отладки
if __name__ == "__main__":
    print(f"📊 Всего стран в CSV: {len(EXTRA_COUNTRIES)}")
    print(f"🚩 Всего флагов: {len(FLAG_EMOJIS)}")
    print(f"📁 Путь к CSV: {CSV_FILE}")
    print(f"✅ Файл существует: {os.path.exists(CSV_FILE)}")
    if EXTRA_COUNTRIES:
        print(f"🔍 Первые 5 стран: {[c['country'] for c in EXTRA_COUNTRIES[:5]]}")
        print(f"🏳️ Примеры флагов:")
        for c in EXTRA_COUNTRIES[:5]:
            flag = FLAG_EMOJIS.get(c['iso_a3'], '🏳️')
            print(f"   {c['iso_a3']} → {flag}")