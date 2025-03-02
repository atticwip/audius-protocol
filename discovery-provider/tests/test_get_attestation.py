import pytest
import redis
from web3 import Web3
from eth_keys import keys
from eth_utils.conversions import to_bytes
from hexbytes import HexBytes

from src.queries.get_attestation import (
    Attestation,
    AttestationError,
    get_attestation,
)
from src.utils.db_session import get_db
from src.utils.config import shared_config
from src.tasks.index_oracles import oracle_addresses_key

from tests.test_get_challenges import setup_db

REDIS_URL = shared_config["redis"]["url"]
redis_handle = redis.Redis.from_url(url=REDIS_URL)


def test_get_attestation(app):
    with app.app_context():
        db = get_db()
        with db.scoped_session() as session:
            setup_db(session)

            # Tests:
            # - Happy path
            # - No user_challenge
            # - Challenge not finished
            # - No disbursement
            # - Invalid oracle
            oracle_address = "0x32a10e91820fd10366AC363eD0DEa40B2e598D22"
            redis_handle.set(oracle_addresses_key, oracle_address)

            delegate_owner_wallet, signature = get_attestation(
                session,
                user_id=1,
                challenge_id="boolean_challenge_2",
                oracle_address=oracle_address,
                specifier="1",
            )

            attestation = Attestation(
                amount=5,
                oracle_address=oracle_address,
                user_address="0x38C68fF3926bf4E68289672F75ee1543117dD9B3",
                challenge_id="boolean_challenge_2",
                challenge_specifier="1",
            )

            # Test happy path

            # confirm the attestation is what we think it should be
            config_owner_wallet = shared_config["delegate"]["owner_wallet"]
            config_private_key = shared_config["delegate"]["private_key"]

            # Ensure we returned the correct owner wallet
            assert delegate_owner_wallet == config_owner_wallet

            # Ensure we can derive the owner wallet from the signed stringified attestation
            attestation_bytes = attestation.get_attestation_bytes()
            to_sign_hash = Web3.keccak(attestation_bytes)
            private_key = keys.PrivateKey(HexBytes(config_private_key))
            public_key = keys.PublicKey.from_private(private_key)
            signture_bytes = to_bytes(hexstr=signature)
            msg_signature = keys.Signature(signature_bytes=signture_bytes, vrs=None)

            recovered_pubkey = public_key.recover_from_msg_hash(
                message_hash=to_sign_hash, signature=msg_signature
            )

            assert (
                Web3.toChecksumAddress(recovered_pubkey.to_address())
                == config_owner_wallet
            )

            # Test no matching user challenge
            with pytest.raises(AttestationError):
                get_attestation(
                    session,
                    user_id=1,
                    challenge_id="boolean_challenge_2",
                    oracle_address=oracle_address,
                    specifier="xyz",
                )

            # Test challenge not finished
            with pytest.raises(AttestationError):
                get_attestation(
                    session,
                    user_id=1,
                    challenge_id="boolean_challenge_3",
                    oracle_address=oracle_address,
                    specifier="1",
                )

            # Test challenge already disbursed
            with pytest.raises(AttestationError):
                get_attestation(
                    session,
                    user_id=1,
                    challenge_id="boolean_challenge_1",
                    oracle_address=oracle_address,
                    specifier="1",
                )

            # Test with bad AAO
            with pytest.raises(AttestationError):
                get_attestation(
                    session,
                    user_id=1,
                    challenge_id="boolean_challenge_2",
                    oracle_address="wrong_oracle_address",
                    specifier="1",
                )
