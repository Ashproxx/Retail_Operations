from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.orchestration.router.classifier import classify, make_plan
from app.orchestration.router.contracts import RouteSettings, RoutingPlan


class RouterState(TypedDict, total=False):
    message: str
    decision: dict
    plan: RoutingPlan


def build_graph(settings: RouteSettings):
    graph = StateGraph(RouterState)
    graph.add_node('classify',lambda state: {'decision': classify(state['message'],settings)})
    graph.add_node('plan',lambda state: {'plan': make_plan(state['decision'])})
    graph.add_node('escalate',lambda state: {'plan': make_plan(state['decision'])})
    graph.add_edge(START,'classify')
    graph.add_conditional_edges('classify',lambda state: 'escalate' if state['decision']['requires_human'] else 'plan')
    graph.add_edge('plan',END)
    graph.add_edge('escalate',END)
    return graph.compile()
