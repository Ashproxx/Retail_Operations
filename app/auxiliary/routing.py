"""Review-gated router diagnostics; heuristic confidence is not probability."""
from collections import Counter
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from app.orchestration.router.classifier import classify, make_plan
from app.orchestration.router.contracts import Intent, RouteSettings


def evaluate(cases, reviewed=False):
    labels=[intent.value for intent in Intent]
    ids=set();texts=set();groups={};rows=[]
    if not cases or reviewed and len(cases)<200:
        raise ValueError('Reviewed acceptance requires at least 200 cases')
    for case in cases:
        if not case['id'] or case['id'] in ids or not case['text'].strip() or case['text'] in texts:
            raise ValueError('Unique IDs and nonempty distinct queries required')
        ids.add(case['id']);texts.add(case['text'])
        if not case['group'] or case['split'] not in {'train','validation','test'}:
            raise ValueError('Valid group and partition required')
        if case['group'] in groups and groups[case['group']]!=case['split']:
            raise ValueError('Paraphrase group crosses partitions')
        groups[case['group']]=case['split']
        if reviewed and (not case.get('reviewer') or not case.get('reviewed_label')):
            raise ValueError('Human reviewer and reviewed label required for every case')
        expected=case.get('reviewed_label') if reviewed else case['draft_label']
        if expected not in labels:raise ValueError('Invalid intent label')
        plan=make_plan(classify(case['text'],RouteSettings()))
        rows.append({'id':case['id'],'group':case['group'],'split':case['split'],
            'expected':expected,'predicted':plan.intent.value,'score':plan.confidence,
            'abstained':plan.requires_human,'reason':plan.reason})
    summaries={}
    for split in ['all','train','validation','test']:
        subset=[r for r in rows if split=='all' or r['split']==split]
        if not subset:continue
        truth=[r['expected'] for r in subset];pred=[r['predicted'] for r in subset]
        summaries[split]={'cases':len(subset),'groups':len({r['group'] for r in subset}),
            'accuracy':float(accuracy_score(truth,pred)),
            'macro_f1_all_ten':float(f1_score(truth,pred,labels=labels,average='macro',zero_division=0)),
            'label_counts':dict(Counter(truth)),
            'confusion_matrix':confusion_matrix(truth,pred,labels=labels).tolist(),
            'abstentions':sum(r['abstained'] for r in subset)}
    bins=[]
    for score in sorted({r['score'] for r in rows}):
        subset=[r for r in rows if r['score']==score]
        bins.append({'heuristic_score':score,'cases':len(subset),
            'decision_accuracy':float(np.mean([r['expected']==r['predicted'] for r in subset])),
            'abstentions':sum(r['abstained'] for r in subset)})
    return {'human_reviewed':reviewed, 'labels':labels,'summaries':summaries,
            'heuristic_score_bins_not_calibration':bins,'rows':rows}
