"""Explicit apparel taxonomy. Never replace the supplied raw source fields."""
import json
import re
import unicodedata
from pathlib import Path

CONFIG = Path(__file__).parent / 'config' / 'apparel_taxonomy.json'


def key(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())


def taxonomy(path=CONFIG):
    rules = json.loads(Path(path).read_text())['rules']
    return rules


def classify(category, path=CONFIG):
    raw = key(category)
    matches = [r for r in taxonomy(path) if raw in [key(r['category']), *map(key, r['aliases'])]]
    if len(matches) != 1:
        return {'department': None, 'apparel_family': None, 'normalized_category': None,
                'taxonomy_status': 'unmapped' if not matches else 'ambiguous'}
    return {'department': 'Apparel', 'apparel_family': matches[0]['family'],
            'normalized_category': matches[0]['category'], 'taxonomy_status': 'mapped'}


def mentioned_category(message, available):
    """Resolve aliases only to categories actually present in the authorized view."""
    matches = []
    for rule in taxonomy():
        if rule['category'] not in available:
            continue
        for alias in [rule['category'], *rule['aliases']]:
            if re.search(r'(?<!\w)' + re.escape(key(alias)) + r'(?!\w)', key(message)):
                matches.append((len(alias), rule['category']))
    if not matches:
        return None
    longest = max(x[0] for x in matches)
    found = {x[1] for x in matches if x[0] == longest}
    return next(iter(found)) if len(found) == 1 else None


def normalize(raw):
    result = dict(raw)
    result.update(classify(raw.get('category')))
    result['raw'] = dict(raw.get('raw', raw))
    result['normalized_location'] = key(raw.get('store_location'))
    # These are display labels, not invented original product names.
    parts = [raw.get('gender'), raw.get('color'), raw.get('style_name') or raw.get('category'), raw.get('size')]
    result['product_label'] = ' · '.join(str(x) for x in parts if x) or 'Unnamed product'
    return result
