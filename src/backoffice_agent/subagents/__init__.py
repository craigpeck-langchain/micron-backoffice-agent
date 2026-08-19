from backoffice_agent.subagents.invoice import invoice_subagent
from backoffice_agent.subagents.purchase_order import purchase_order_subagent
from backoffice_agent.subagents.remittance import remittance_subagent
from backoffice_agent.subagents.shipping_order import shipping_order_subagent

SUBAGENTS = [
    shipping_order_subagent,
    purchase_order_subagent,
    invoice_subagent,
    remittance_subagent,
]

__all__ = ["SUBAGENTS"]
