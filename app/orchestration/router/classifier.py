"""Conservative English retail rules. No model, network or business-data access."""
import re
from app.orchestration.router.contracts import Intent, RouteSettings, RoutingPlan, Task

# Strong domain expressions score .82; generic standalone keywords score .45.
RULES = {
    Intent.INVENTORY: (r'\b(?:inventory|stockouts?|stockout risk|low stock|stock levels?|reorder points?|restock\w*|replenish\w*|overstock\w*|run out|units left|below.*reorder)\b', r'\bstock\b'),
    Intent.DEMAND: (r'\b(?:forecast\w*|predict demand|demand|sales trend\w*)\b', r'\btrend\w*\b'),
    Intent.PRICING: (r'\b(?:pric(?:e|es|ing)|discount\w*|promotion\w*|coupon\w*|price match\w*)\b', r'\bcost\w*\b'),
    Intent.ORDER: (r'\b(?:order status|track.*order|where.*order|shipping|shipments?|fulfill\w*|delivery|sla)\b', r'\border\w*\b'),
    Intent.SUPPLY_CHAIN: (r'\b(?:supplier\w*|vendor\w*|logistics|supply chain|lead times?|disruption\w*|negotiat\w*)\b', r'\bsupply\b'),
    Intent.CUSTOMER_SUPPORT: (r'\b(?:complaint\w*|customer service|customer support|faq|frustrat\w*|unhappy|angry|support ticket)\b', r'\b(?:help|policy)\b'),
    Intent.RETURNS: (r'\b(?:refund\w*|returns?|return eligibility|defective|wrong item)\b', r'\breimburse\w*\b'),
    Intent.ANALYTICS: (r'\b(?:analytics|reports?|reporting|total sales|units sold|sales by|top.*sku|top.*product|slow.moving|compare.*stores?|store comparison|sales drop|sales fell|sales summary|kpi|turnover)\b', r'\bsales\b'),
}
ORDER = [Intent.ANALYTICS, Intent.INVENTORY, Intent.DEMAND, Intent.SUPPLY_CHAIN,
         Intent.ORDER, Intent.PRICING, Intent.RETURNS, Intent.CUSTOMER_SUPPORT]
AGENTS = dict(zip(ORDER, ['analytics-reporting','inventory','demand-forecasting','supply-chain',
                         'order-fulfillment','pricing-promotions','returns-refunds','customer-service']))


def classify(text: str, settings: RouteSettings) -> dict:
    text = text.replace('-', ' ').replace('’', "'")
    clauses = [c.strip() for c in re.split(r'[;.!?]+|\b(?:and|but|then)\b', text.lower()) if c.strip()]
    scores, snippets, ids = {}, {}, set()
    unsupported = False
    for clause in clauses:
        found = {}
        for intent, (strong, weak) in RULES.items():
            if re.search(strong, clause): found[intent] = .82
            elif re.search(weak, clause): found[intent] = .45
        # Generic support/analytics words must not create extra agents beside specific domains.
        if any(v == .82 for v in found.values()):
            found = {k:v for k,v in found.items() if v == .82}
        if Intent.INVENTORY in found and re.search(r'\b(?:next week|next month|tomorrow|likely|forecast)\b',clause):
            found[Intent.DEMAND] = .75
            ids.add('forward_stock_requires_demand')
        if Intent.ANALYTICS in found and re.search(r'\bwhy\b.*\bsales (?:drop|fell)\b',clause):
            found[Intent.DEMAND] = .75
            ids.add('sales_cause_requires_demand')
        if not found:
            unsupported = True
        for intent, score in found.items():
            scores[intent] = min(scores.get(intent,1),score)
            snippets.setdefault(intent,[]).append(clause)
            ids.add(intent.value.lower() + ('_strong' if score >= .75 else '_weak'))
    # Negated or alternative intent wording needs clarification, not automatic dispatch.
    ambiguous = bool(re.search(r"\b(?:not|never|ignore|instead|either|or)\b|n't\b",text.lower()))
    unrelated = bool(re.search(r'\b(?:stock market|share price|stock price|weather|bitcoin|returns on investment)\b',text.lower()))
    confidence = min(scores.values(), default=0)
    if unsupported or ambiguous or unrelated: confidence = min(confidence,.4)
    candidates = [i for i in ORDER if i in scores]
    reason = ('outside_retail_scope' if unrelated else 'ambiguous_or_negated_request' if ambiguous else
              'partly_unsupported_request' if unsupported and candidates else 'unknown_intent' if not candidates else
              'agent_limit_exceeded' if len(candidates)>settings.max_agents else
              'low_confidence' if confidence < settings.confidence_threshold else 'matched_rules')
    human = reason != 'matched_rules'
    return dict(candidates=candidates,confidence=confidence,requires_human=human,reason=reason,
                snippets=snippets,rule_ids=sorted(ids))


def make_plan(decision: dict) -> RoutingPlan:
    candidates = decision['candidates']
    human = decision['requires_human']
    tasks = []
    if not human:
        for i,intent in enumerate(candidates,1):
            tasks.append(Task(step_id=f'step-{i}',intent=intent,agent=AGENTS[intent],
                depends_on=[f'step-{i-1}'] if i>1 else [], subqueries=decision['snippets'][intent],
                reason_codes=[r for r in decision['rule_ids'] if r.startswith(intent.value.lower())]))
    return RoutingPlan(intent=Intent.UNKNOWN if human else Intent.MULTI_AGENT if len(candidates)>1 else candidates[0],
                       candidates=candidates,confidence=decision['confidence'],requires_human=human,
                       reason=decision['reason'],tasks=tasks,rule_ids=decision['rule_ids'])
