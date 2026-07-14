from __future__ import annotations

import pytest

from tck.param.token import WipeTokenParams


pytestmark = pytest.mark.unit


def test_wipe_token_params_rejects_non_integer_serial_numbers():
    params = {
        "sessionId": "test-session",
        "serialNumbers": ["abc"],
    }

    with pytest.raises(ValueError, match=r"Each serialNumbers item must be a valid integer string"):
        WipeTokenParams.parse_json_params(params)
