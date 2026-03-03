"""
All items for Elo rating system testing.
Includes mundane emojis, salient emojis, unicode symbols, and words.
"""

# Mundane emojis
MUNDANE_EMOJIS = [
    {'emoji': '🗄️', 'name': 'file cabinet', 'code': 0x1F5C4},
    {'emoji': '🚌', 'name': 'bus', 'code': 0x1F68C},
    {'emoji': '🪨', 'name': 'rock', 'code': 0x1FAA8},
    {'emoji': '🥔', 'name': 'potato', 'code': 0x1F954},
    {'emoji': '🪑', 'name': 'chair', 'code': 0x1FA91},
    {'emoji': '📏', 'name': 'ruler', 'code': 0x1F4CF},
    {'emoji': '🥄', 'name': 'spoon', 'code': 0x1F944},
    {'emoji': '📂', 'name': 'open file folder', 'code': 0x1F4C2},
    {'emoji': '🛒', 'name': 'shopping cart', 'code': 0x1F6D2},
    {'emoji': '🍞', 'name': 'bread', 'code': 0x1F35E}
]

# Salient emojis
SALIENT_EMOJIS = [
    {'emoji': '💀', 'name': 'skull', 'code': 0x1F480},
    {'emoji': '🗡️', 'name': 'dagger', 'code': 0x1F5E1},
    {'emoji': '💣', 'name': 'bomb', 'code': 0x1F4A3},
    {'emoji': '🔫', 'name': 'pistol', 'code': 0x1F52B},
    {'emoji': '🦂', 'name': 'scorpion', 'code': 0x1F982},
    {'emoji': '☠️', 'name': 'skull and crossbones', 'code': 0x2620},
    {'emoji': '⚰️', 'name': 'coffin', 'code': 0x26B0},
    {'emoji': '🔪', 'name': 'kitchen knife', 'code': 0x1F52A},
    {'emoji': '🐍', 'name': 'snake', 'code': 0x1F40D},
    {'emoji': '🕷️', 'name': 'spider', 'code': 0x1F577},
    {'emoji': '☣️', 'name': 'biohazard', 'code': 0x2623},
    {'emoji': '☢️', 'name': 'radioactive', 'code': 0x2622},
    {'emoji': '🦟', 'name': 'mosquito', 'code': 0x1F99F}
]

# Additional symbols from the second list
ADDITIONAL_SYMBOLS = []

# Words
WORDS = []

def get_all_items():
    """
    Returns a list of all items as strings for use in the Elo system.
    """
    items = []
    
    # Add mundane emojis
    for item in MUNDANE_EMOJIS:
        items.append(item['emoji'])
    
    # Add salient emojis
    for item in SALIENT_EMOJIS:
        items.append(item['emoji'])
    
    # Add additional symbols
    for item in ADDITIONAL_SYMBOLS:
        items.append(item['symbol'])
    
    # Add words
    for item in WORDS:
        items.append(item['word'])
    
    return items

def get_item_info(item):
    """
    Returns information about an item (name, type, etc.) if available.
    """
    # Check mundane emojis
    for emoji_info in MUNDANE_EMOJIS:
        if emoji_info['emoji'] == item:
            return {'name': emoji_info['name'], 'type': 'mundane_emoji'}
    
    # Check salient emojis
    for emoji_info in SALIENT_EMOJIS:
        if emoji_info['emoji'] == item:
            return {'name': emoji_info['name'], 'type': 'salient_emoji'}
    
    # Check additional symbols
    for symbol_info in ADDITIONAL_SYMBOLS:
        if symbol_info['symbol'] == item:
            return {'name': symbol_info['name'], 'type': symbol_info['type']}
    
    # Check words
    for word_info in WORDS:
        if word_info['word'] == item:
            return {'type': word_info['type']}
    
    return None

if __name__ == "__main__":
    # Test the functions
    all_items = get_all_items()
    print(f"Total items: {len(all_items)}")
    print(f"First 10 items: {all_items[:10]}")
    print(f"Last 10 items: {all_items[-10:]}")
    
    # Test item info
    test_items = ['🔥', 'beige', '∃', '📏']
    for item in test_items:
        info = get_item_info(item)
        print(f"{item}: {info}")