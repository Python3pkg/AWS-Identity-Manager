import string

import pytest

@pytest.fixture
def identity_fixures():
    l = []
    for i, c in enumerate(string.ascii_uppercase):
        l.append(dict(
            name='identity_{0}'.format(i),
            access_key_id='someaccesskey_{0}'.format(c),
            secret_access_key='notasecret_{0}_{1}'.format(i, c),
        ))
    return l

@pytest.fixture
def identity_store(tmpdir):
    from awsident.storage import IdentityStore
    identity_store = IdentityStore(config_path=str(tmpdir))
    def fin():
        identity_store.identities.clear()
        identity_store.save_to_config()
    return identity_store

@pytest.fixture
def identity_store_with_data(tmpdir):
    from awsident.storage import IdentityStore, IdentityExists
    identity_store = IdentityStore(config_path=str(tmpdir))
    for data in identity_fixures():
        try:
            identity_store.add_identity(data)
        except IdentityExists:
            pass
    def fin():
        identity_store.identities.clear()
        identity_store.save_to_config()
    return identity_store