import pytest
from app.auxiliary.routing import evaluate


def case(**changes):
    return dict(id='1',group='g',split='train',text='Show inventory',draft_label='INVENTORY',
                reviewer=None,reviewed_label=None)|changes


def test_draft_results_cannot_claim_human_review():
    result=evaluate([case(),case(id='2',group='other',text='hello',draft_label='UNKNOWN')])
    assert result['human_reviewed'] is False
    assert result['summaries']['all']['accuracy']==1
    assert result['summaries']['all']['abstentions']==1
    with pytest.raises(ValueError,match='200'):evaluate([case()],reviewed=True)


def test_group_leakage_and_duplicate_queries_are_rejected():
    with pytest.raises(ValueError,match='crosses'):
        evaluate([case(),case(id='2',text='Show inventory please',split='test')])
    with pytest.raises(ValueError,match='Unique'):evaluate([case(),case(id='2')])


def test_large_draft_still_requires_actual_review_fields():
    rows=[case(id=str(i),group=str(i),text=f'Show inventory for product {i}') for i in range(200)]
    with pytest.raises(ValueError,match='Human reviewer'):evaluate(rows,reviewed=True)
