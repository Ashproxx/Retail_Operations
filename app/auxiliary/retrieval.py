"""Development retrieval measurement with an explicit lightweight lexical baseline."""
import math
from sklearn.feature_extraction.text import TfidfVectorizer


class LexicalEmbedder:
    identity = 'auxiliary-tfidf-unigram-bigram-v1'

    def __init__(self, documents):
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), norm='l2').fit(documents)

    def encode(self, texts):
        return self.vectorizer.transform(texts).toarray().tolist()


def retrieval_metrics(positives, negatives):
    if not positives or not negatives:
        raise ValueError('Positive and negative cases are both required')
    ranks=[]
    for row in positives:
        ranked=list(dict.fromkeys(row['ranked']))
        ranks.append(ranked.index(row['expected'])+1 if row['expected'] in ranked else None)
    negative_abstentions=sum(r['status']=='insufficient_evidence' for r in negatives)
    all_abstentions=negative_abstentions+sum(r['status']=='insufficient_evidence' for r in positives)
    return {'positive_queries':len(positives), 'negative_queries':len(negatives),
        'recall_at_1':sum(r==1 for r in ranks)/len(ranks),
        'recall_at_3':sum(r is not None and r<=3 for r in ranks)/len(ranks),
        'mrr_at_3':sum(1/r for r in ranks if r is not None and r<=3)/len(ranks),
        'ndcg_at_3':sum(1/math.log2(r+1) for r in ranks if r is not None and r<=3)/len(ranks),
        'abstention_precision':negative_abstentions/all_abstentions if all_abstentions else None,
        'negative_abstention_rate':negative_abstentions/len(negatives),
        'positive_evidence_rate':sum(r['status']=='evidence_found' for r in positives)/len(positives)}
