import re
from typing import List, Optional, Dict, Any
from loguru import logger

def clean_text(text: str) -> str:
    """Очистка текста от лишних символов и пробелов"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем управляющие символы
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

def normalize_whitespace(text: str) -> str:
    """Нормализация пробелов в тексте"""
    if not text:
        return ""
    
    # Заменяем множественные пробелы на одинарные
    text = re.sub(r' +', ' ', text)
    
    # Заменяем множественные переносы строк на двойные
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Удаляем пробелы в начале и конце строк
    lines = [line.strip() for line in text.split('\n')]
    
    return '\n'.join(lines).strip()

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезка текста до указанной длины с добавлением суффикса"""
    if not text or len(text) <= max_length:
        return text
    
    # Учитываем длину суффикса
    actual_length = max_length - len(suffix)
    if actual_length <= 0:
        return suffix[:max_length]
    
    return text[:actual_length] + suffix

def extract_mentions(text: str) -> List[str]:
    """Извлечение упоминаний пользователей (@username) из текста"""
    if not text:
        return []
    
    mentions = re.findall(r'@([a-zA-Z0-9_]+)', text)
    return list(set(mentions))  # Убираем дубликаты

def extract_hashtags(text: str) -> List[str]:
    """Извлечение хештегов (#hashtag) из текста"""
    if not text:
        return []
    
    hashtags = re.findall(r'#([a-zA-Zа-яА-Я0-9_]+)', text)
    return list(set(hashtags))  # Убираем дубликаты

def extract_urls(text: str) -> List[str]:
    """Извлечение URL из текста"""
    if not text:
        return []
    
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls

def remove_html_tags(text: str) -> str:
    """Удаление HTML тегов из текста"""
    if not text:
        return ""
    
    # Удаляем HTML теги
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Декодируем HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, char in html_entities.items():
        clean = clean.replace(entity, char)
    
    return clean

def escape_html(text: str) -> str:
    """Экранирование HTML символов в тексте"""
    if not text:
        return ""
    
    html_escape_table = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    return ''.join(html_escape_table.get(c, c) for c in text)

def escape_markdown(text: str) -> str:
    """Экранирование Markdown символов в тексте"""
    if not text:
        return ""
    
    markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_list_items(items: List[str], bullet: str = "•") -> str:
    """Форматирование списка элементов с маркерами"""
    if not items:
        return ""
    
    formatted_items = []
    for item in items:
        if item.strip():
            formatted_items.append(f"{bullet} {item.strip()}")
    
    return '\n'.join(formatted_items)

def split_long_message(text: str, max_length: int = 4000) -> List[str]:
    """Разделение длинного сообщения на части"""
    if not text or len(text) <= max_length:
        return [text] if text else []
    
    parts = []
    current_part = ""
    
    # Разделяем по абзацам
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # Если абзац помещается в текущую часть
        if len(current_part) + len(paragraph) + 2 <= max_length:
            if current_part:
                current_part += '\n\n' + paragraph
            else:
                current_part = paragraph
        else:
            # Сохраняем текущую часть если она не пустая
            if current_part:
                parts.append(current_part)
                current_part = ""
            
            # Если абзац слишком длинный, разделяем по предложениям
            if len(paragraph) > max_length:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 1 <= max_length:
                        if current_part:
                            current_part += ' ' + sentence
                        else:
                            current_part = sentence
                    else:
                        if current_part:
                            parts.append(current_part)
                        
                        # Если предложение все еще слишком длинное
                        if len(sentence) > max_length:
                            # Разделяем по словам
                            words = sentence.split()
                            current_part = ""
                            
                            for word in words:
                                if len(current_part) + len(word) + 1 <= max_length:
                                    if current_part:
                                        current_part += ' ' + word
                                    else:
                                        current_part = word
                                else:
                                    if current_part:
                                        parts.append(current_part)
                                    current_part = word
                        else:
                            current_part = sentence
            else:
                current_part = paragraph
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part)
    
    return parts

def count_words(text: str) -> int:
    """Подсчет количества слов в тексте"""
    if not text:
        return 0
    
    # Удаляем лишние пробелы и разделяем по словам
    words = text.strip().split()
    return len(words)

def count_sentences(text: str) -> int:
    """Подсчет количества предложений в тексте"""
    if not text:
        return 0
    
    # Ищем окончания предложений
    sentences = re.split(r'[.!?]+', text)
    # Убираем пустые элементы
    sentences = [s.strip() for s in sentences if s.strip()]
    return len(sentences)

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Извлечение ключевых слов из текста"""
    if not text:
        return []
    
    # Приводим к нижнему регистру и удаляем знаки препинания
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Разделяем на слова
    words = clean_text.split()
    
    # Фильтруем по длине и убираем стоп-слова
    stop_words = {
        'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об', 'при', 'за', 'над', 'под',
        'что', 'как', 'где', 'когда', 'почему', 'который', 'которая', 'которое', 'которые',
        'это', 'то', 'та', 'те', 'тот', 'эта', 'этот', 'эти',
        'я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они',
        'мой', 'твой', 'его', 'её', 'наш', 'ваш', 'их',
        'не', 'ни', 'да', 'нет', 'или', 'но', 'а', 'же', 'ли', 'бы',
        'был', 'была', 'было', 'были', 'есть', 'будет', 'будут'
    }
    
    keywords = []
    for word in words:
        if len(word) >= min_length and word not in stop_words:
            keywords.append(word)
    
    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords

def highlight_keywords(text: str, keywords: List[str], 
                      start_tag: str = "<b>", end_tag: str = "</b>") -> str:
    """Выделение ключевых слов в тексте"""
    if not text or not keywords:
        return text
    
    result = text
    
    # Сортируем ключевые слова по длине (сначала длинные)
    sorted_keywords = sorted(keywords, key=len, reverse=True)
    
    for keyword in sorted_keywords:
        # Создаем паттерн для поиска слова целиком
        pattern = r'\b' + re.escape(keyword) + r'\b'
        replacement = f"{start_tag}{keyword}{end_tag}"
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

def generate_summary(text: str, max_sentences: int = 3) -> str:
    """Генерация краткого резюме текста"""
    if not text:
        return ""
    
    # Разделяем на предложения
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    # Берем первые и последние предложения
    if max_sentences == 1:
        return sentences[0] + "."
    elif max_sentences == 2:
        return sentences[0] + ". " + sentences[-1] + "."
    else:
        # Берем первое, среднее и последнее
        middle_idx = len(sentences) // 2
        selected = [sentences[0], sentences[middle_idx], sentences[-1]]
        return ". ".join(selected) + "."

def validate_text_length(text: str, min_length: int = 0, max_length: int = 10000) -> Dict[str, Any]:
    """Валидация длины текста"""
    if not text:
        text = ""
    
    length = len(text)
    word_count = count_words(text)
    
    result = {
        'valid': min_length <= length <= max_length,
        'length': length,
        'word_count': word_count,
        'min_length': min_length,
        'max_length': max_length,
        'errors': []
    }
    
    if length < min_length:
        result['errors'].append(f"Текст слишком короткий (минимум {min_length} символов)")
    
    if length > max_length:
        result['errors'].append(f"Текст слишком длинный (максимум {max_length} символов)")
    
    return result

def format_user_input(text: str) -> str:
    """Форматирование пользовательского ввода"""
    if not text:
        return ""
    
    # Очищаем и нормализуем
    text = clean_text(text)
    text = normalize_whitespace(text)
    
    # Удаляем лишние символы
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()

def create_progress_bar(current: int, total: int, length: int = 20, 
                       fill: str = "█", empty: str = "░") -> str:
    """Создание текстового прогресс-бара"""
    if total <= 0:
        return empty * length
    
    progress = min(current / total, 1.0)
    filled_length = int(length * progress)
    
    bar = fill * filled_length + empty * (length - filled_length)
    percentage = int(progress * 100)
    
    return f"{bar} {percentage}%"

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def transliterate_russian(text: str) -> str:
    """Транслитерация русского текста в латиницу"""
    if not text:
        return ""
    
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    result = ""
    for char in text:
        result += translit_dict.get(char, char)
    
    return result