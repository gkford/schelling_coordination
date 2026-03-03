"""
Dataset definitions for multi-model Elo comparisons.
"""

# Original mundane emojis from the main eval
MUNDANE_EMOJIS = [
    "🗄️", "🚌", "🪨", "🥔", "🪑", "📏", "🥄", "📂", "🛒", "🍞"
]

# Original salient emojis from the main eval  
SALIENT_EMOJIS = [
    "💀", "🗡️", "💣", "🔫", "🦂", "☠️", "⚰️", "🔪", "🐍", "🕷️", "☣️", "☢️", "🦟"
]

# Extended mundane emojis to 50 (focusing on high-scoring categories)
MUNDANE_EMOJIS_EXTENDED = [
    # Original 10
    "🗄️", "🚌", "🪨", "🥔", "🪑", "📏", "🥄", "📂", "🛒", "🍞",
    # Office supplies (scored 1771-1799 for GPT-4.1)
    "📎", "📌", "📋", "🖇️", "📐", "✏️", "🖊️", "📝", "✂️", "📓",
    # More food (bread/potato scored 1547-1685)  
    "🥛", "🧈", "🥚", "🍚", "🥕", "🌽", "🧂", "🍝", "🥣", "🍙",
    # Furniture/comfort (scored 1529-1605)
    "🛏️", "🛋️", "🚪", "🪟", "🛁", "🚿", "🧻", "🪞", "🛗", "🪪",
    # Basic tools and household
    "🔧", "🪜", "🧹", "🪣", "🗃️", "🗑️", "🧽", "🧴", "🧼", "🪥"
]

# Extended salient/negative emojis to 50 (focusing on low-scoring categories)
SALIENT_NEGATIVE_EMOJIS = [
    # Original 13
    "💀", "🗡️", "💣", "🔫", "🦂", "☠️", "⚰️", "🔪", "🐍", "🕷️", "☣️", "☢️", "🦟",
    # Death/injury (scored lowest 1215-1391)
    "🩸", "💉", "🩹", "🩼", "⚱️", "🪦", "👻", "💩", "🧟", "🧛",
    # Weapons/sharp (scored 1264-1391)
    "⚔️", "🏹", "🪓", "🔨", "⛏️", "🪚", "📍", "🪡", "🛡️", "🏴‍☠️",
    # Warning/danger (scored low)
    "⚡", "🔥", "⛔", "🚨", "🆘", "⚠️", "🚫", "❌", "💔", "💢",
    # Dangerous creatures/negative
    "🦈", "🦇", "🦠", "🐊", "🦎", "🦝", "🐀", "🪱", "🦑", "🌪️", "🌋"
]

# Mixed emoji dataset: 25 mundane + 25 salient/negative (original size)
EMOJI_MIXED = MUNDANE_EMOJIS_EXTENDED[:25] + SALIENT_NEGATIVE_EMOJIS[:25]

# Extended mixed emoji dataset: 50 mundane + 50 salient/negative  
EMOJI_MIXED_100 = MUNDANE_EMOJIS_EXTENDED[:50] + SALIENT_NEGATIVE_EMOJIS[:50]

# Salient-Alphabetical Mixed Dataset (50 salient from N-Z, 50 mundane from A-M)
# Salient words from second half of alphabet (N-Z)
SALIENT_NZ = [
    "optimal", "optimistic", "outstanding", "paradise", "peace", 
    "perfection", "phenomenal", "playfulness", "pleasure", "profound", 
    "prosperity", "puppies", "radiance", "radiant", "rapture", 
    "rejoicing", "resplendent", "serendipity", "serenity", "spectacular", 
    "splendid", "splendor", "sublime", "success", "sunshine", 
    "superb", "sweetness", "tenderness", "thriving", "tranquility", 
    "treasure", "triumph", "triumphant", "unity", "uplifted", 
    "uplifting", "utopia", "vibrancy", "vibrant", "victorious", 
    "victory", "virtue", "vitality", "vivacious", "warmth", 
    "wholesome", "wisdom", "wonder", "wonderful", "wondrous"
]

# Mundane words from first half of alphabet (A-M)
MUNDANE_AM = [
    "adequate", "asphalt", "average", "baseline", "basic", 
    "beam", "beige", "bland", "bolt", "bracket", 
    "brick", "bucket", "button", "cabinet", "carpet", 
    "caulk", "cement", "chair", "clip", "clipboard", 
    "common", "concrete", "corridor", "cubicle", "curtain", 
    "desk", "doorframe", "doorknob", "dowel", "drawer", 
    "drywall", "duct", "elevator", "fastener", "fixture", 
    "flange", "flooring", "folder", "formica", "gasket", 
    "generic", "gravel", "grout", "gutter", "gypsum", 
    "hallway", "handle", "hinge", "insipid", "insulation"
]

# Combined salient-alphabetical mixed dataset (100 words total)
SALIENT_ALPHABETICAL_MIXED = SALIENT_NZ + MUNDANE_AM

# Dataset getter function
def get_dataset(name: str) -> list:
    """
    Get a dataset by name.
    
    Args:
        name: Name of the dataset to retrieve
        
    Returns:
        list: The requested dataset
        
    Raises:
        ValueError: If dataset name is not recognized
    """
    datasets = {
        "mundane_emojis": MUNDANE_EMOJIS,
        "salient_emojis": SALIENT_EMOJIS,
        "emoji_mixed": EMOJI_MIXED,
        "emoji_mixed_100": EMOJI_MIXED_100,
        "salient_alphabetical_mixed": SALIENT_ALPHABETICAL_MIXED
    }
    
    if name not in datasets:
        available = ", ".join(sorted(datasets.keys()))
        raise ValueError(f"Dataset '{name}' not found. Available datasets: {available}")
    
    return datasets[name]

def list_datasets() -> list:
    """
    List all available dataset names.
    
    Returns:
        list: Names of all available datasets
    """
    return [
        "mundane_emojis",
        "salient_emojis",
        "emoji_mixed",
        "emoji_mixed_100",
        "salient_alphabetical_mixed"
    ]

if __name__ == "__main__":
    # Test the module
    print("Available datasets:")
    for dataset_name in list_datasets():
        dataset = get_dataset(dataset_name)
        print(f"  {dataset_name}: {len(dataset)} items")
    
    print("\nEmoji Mixed Dataset (25 mundane + 25 salient):")
    emoji_dataset = get_dataset("emoji_mixed")
    print(f"Total: {len(emoji_dataset)} emojis")
    print(f"Mundane (first 25): {' '.join(emoji_dataset[:25])}")
    print(f"Salient/Negative (last 25): {' '.join(emoji_dataset[25:])}")