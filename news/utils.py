from django.utils.text import slugify as django_slugify


def slugify(text):
    """
    Custom slugify function that handles cyrillic characters by transliterating them to latin
    """
    if not text:
        return ""
        
    # Transliteration mapping
    cyrillic_mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ye', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya',
        'э': 'e', 'ы': 'y', 'ъ': '', 'ё': 'yo',
    }

    # Convert text to lowercase
    text = text.lower()

    # Replace Cyrillic characters with their Latin equivalents
    for cyrillic, latin in cyrillic_mapping.items():
        text = text.replace(cyrillic, latin)

    # Use Django's slugify for the rest of the processing
    return django_slugify(text)
