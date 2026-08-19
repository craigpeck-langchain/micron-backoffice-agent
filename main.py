"""Quick smoke-test entry point.

For the full chat experience, run:

    uv run langgraph dev

and open Studio at http://localhost:2024.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv

load_dotenv(override=True)

from backoffice_agent.graph import graph  # noqa: E402

DEFAULT_EMAIL = """From: ap@northfield-components.com
Subject: Invoice INV-88213 for PO-10045

Hi team,

Please find our invoice INV-88213 attached for PO-10045, 480 units of
precision aluminum brackets at $12.40/unit, total $5,952.00, due net 30.

Thanks,
Northfield Components AP Team
"""


def main() -> None:
    email_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_EMAIL
    result = graph.invoke({"messages": [{"role": "user", "content": email_text}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
