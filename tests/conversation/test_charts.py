import pytest
from app.conversation.charts import specification
from app.conversation.contracts import Context
from app.conversation.taxonomy import normalize


def test_chart_spec_reuses_observed_numbers_and_rejects_incompatible_types():
    rows=[normalize(dict(store_id='A',store_location='Bandra',sku_id='P',date='2026-09-28',category='shirt',
                         units_sold=3,unit_price_inr='100',source='fixture',fixture=True))]
    ctx=Context(period={'start':'2026-09-28','end':'2026-09-28','label':'Today'},chart_type='pie')
    spec=specification(rows,ctx)
    assert spec['datasets'][0]['values']==[300.0]
    assert '100.0%' in spec['interpretation']
    with pytest.raises(ValueError):specification(rows,ctx.model_copy(update={'group_by':'date','chart_type':'pie'}))
    for kind in ['bar','horizontal_bar','pie','doughnut']:assert specification(rows,ctx.model_copy(update={'chart_type':kind}))['type']==kind
