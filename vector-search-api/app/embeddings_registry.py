PRESETS = {
    "bge-m3":         {"backend": "fastembed", "name": "./models/bge-m3", "normalize": True, "e5_mode": "auto"},
    "mE5-small":      {"backend": "fastembed", "name": "./models/mE5-small", "normalize": True, "e5_mode": "query"},
    "mE5-base":       {"backend": "st", "name": "./models/mE5-base", "normalize": True, "e5_mode": "query"},
    "mE5-large":      {"backend": "st", "name": "./models/mE5-large", "normalize": True, "e5_mode": "query"},
    "paraphrase-ml":  {"backend": "st", "name": "./models/paraphrase-ml", "normalize": True, "e5_mode": "auto"},
    "ko-sbert":       {"backend": "st", "name": "./models/ko-sbert", "normalize": True, "e5_mode": "auto"},
    "ko-sroberta":    {"backend": "st", "name": "./models/ko-sroberta", "normalize": True, "e5_mode": "auto"},
    "ko-simcse":      {"backend": "st", "name": "./models/ko-simcse", "normalize": True, "e5_mode": "auto"},
    "ko-sentence":    {"backend": "st", "name": "./models/ko-sentence", "normalize": True, "e5_mode": "auto"},
    "nomic-embed":    {"backend": "st", "name": "./models/nomic-embed", "normalize": True, "e5_mode": "auto"},
}