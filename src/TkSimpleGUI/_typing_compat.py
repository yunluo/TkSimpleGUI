"""typing compatibility for Python 3.7.

``typing.Literal`` only exists from 3.8 upwards.  The package targets
3.7, so Literal is imported from here everywhere:

- 3.8+: the real ``typing.Literal``
- 3.7:  ``typing_extensions.Literal`` (a conditional dependency of this
  package on Python 3.7, declared in pyproject.toml)

Static checkers resolve the TYPE_CHECKING branch to ``typing.Literal``.
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - static only
    from typing import Literal

elif sys.version_info >= (3, 8):  # pragma: no cover - version dependent
    from typing import Literal

else:  # pragma: no cover - version dependent
    from typing_extensions import Literal


__all__ = ["Literal"]
