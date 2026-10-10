import time
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode

import jwt
import pytest

from app.security import (
    InitDataError,
    create_session_token,
    decode_session_token,
    validate_init_data,
)
from tests.conftest import BOT_TOKEN, make_init_data

DAY = timedelta(hours=24)


def test_valid_init_data_is_accepted():
    data = validate_init_data(make_init_data(telegram_id=7, start_param="school12"), BOT_TOKEN, DAY)
    assert data.user.id == 7
    assert data.user.language_code == "ru"
    assert data.start_param == "school12"


def test_tampered_user_is_rejected():
    fields = dict(parse_qsl(make_init_data(telegram_id=7)))
    fields["user"] = fields["user"].replace('"id":7', '"id":8')
    with pytest.raises(InitDataError):
        validate_init_data(urlencode(fields), BOT_TOKEN, DAY)


def test_other_bot_token_is_rejected():
    with pytest.raises(InitDataError):
        validate_init_data(make_init_data(token="999:other"), BOT_TOKEN, DAY)


def test_missing_hash_is_rejected():
    fields = dict(parse_qsl(make_init_data()))
    del fields["hash"]
    with pytest.raises(InitDataError):
        validate_init_data(urlencode(fields), BOT_TOKEN, DAY)


def test_expired_init_data_is_rejected():
    old = int(time.time()) - 25 * 3600
    with pytest.raises(InitDataError, match="expired"):
        validate_init_data(make_init_data(auth_date=old), BOT_TOKEN, DAY)


def test_future_auth_date_is_rejected():
    future = int(time.time()) + 3600
    with pytest.raises(InitDataError, match="future"):
        validate_init_data(make_init_data(auth_date=future), BOT_TOKEN, DAY)


def test_session_token_roundtrip():
    token = create_session_token(15, "secret-a" * 4, timedelta(hours=1))
    assert decode_session_token(token, "secret-a" * 4) == 15


def test_session_token_with_wrong_secret_is_rejected():
    token = create_session_token(15, "secret-a" * 4, timedelta(hours=1))
    with pytest.raises(jwt.InvalidTokenError):
        decode_session_token(token, "secret-b" * 4)


def test_expired_session_token_is_rejected():
    token = create_session_token(15, "secret-a" * 4, timedelta(seconds=-1))
    with pytest.raises(jwt.InvalidTokenError):
        decode_session_token(token, "secret-a" * 4)
