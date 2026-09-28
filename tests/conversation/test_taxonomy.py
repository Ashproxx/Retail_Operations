from app.conversation.taxonomy import classify, normalize, mentioned_category


def test_preserves_raw_and_reports_unknown():
    raw = {'category': 'formal shirt', 'style_name': 'Oxford', 'color': 'Blue'}
    result = normalize(raw)
    assert result['normalized_category'] == 'Shirts'
    assert result['apparel_family'] == 'Tops'
    assert result['raw'] == raw
    assert raw['category'] == 'formal shirt'
    assert classify('mystery garment')['taxonomy_status'] == 'unmapped'
    assert classify('mystery garment')['apparel_family'] is None


def test_aliases_require_observed_category_and_handle_tshirts():
    assert mentioned_category('How are shirts doing?', ['Shirts']) == 'Shirts'
    assert mentioned_category('How are shorts doing?', ['Shirts']) is None
    assert mentioned_category('show t-shirts', ['Shirts', 'T-shirts']) == 'T-shirts'
