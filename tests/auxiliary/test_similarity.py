import pytest
from app.auxiliary.similarity import compare_rankings


def rows():
    return [(f'SKU{i:02}', 100+i*10, (100+i*10)*(20+i**2), 20+i, 2+i%4) for i in range(10)]


def test_ranking_determinism_review_blanks_and_self_exclusion():
    data=rows(); result=compare_rankings(data)
    assert result == compare_rankings(list(reversed(data)))
    assert result['eligible_products'] == 10
    assert -1 <= result['mean_full_ranking_spearman'] <= 1
    assert 0 <= result['mean_top5_overlap_fraction'] <= 1
    assert all(r['query_sku'] != r['candidate_sku'] and r['reviewer'] is None
               and r['relevant'] is None for r in result['review_queue'])


def test_reject_invalid_and_record_exclusions():
    with pytest.raises(ValueError, match='Unique'):
        compare_rankings(rows()+[rows()[0]])
    with pytest.raises(ValueError, match='positive'):
        compare_rankings(rows()+[('bad',0,3,4,5)])
    assert compare_rankings(rows()+[('short',10,20,2,2)])['excluded_short_history'] == 1
    assert compare_rankings([(str(i),10,100,20,2) for i in range(8)])['status'] == 'UNVERIFIED'
