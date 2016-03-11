import os
import stat
import json

from awsident.identity import Identity, IdentityEncoder

CONFIG_PATH = os.path.expanduser('~/.aws-identity-manager')

class IdentityExists(Exception):
    def __init__(self, identity, existing):
        self.identity = identity
        self.existing = existing
    def __str__(self):
        msg = 'Cannot store {0!r}, it already exists as {1!r}'.format(
            self.idenity, self.existing
        )
        return msg

class IdentityStore(object):
    """Storage class for all known aws identities

    Provies loading and saving to protected config file
    """
    def __init__(self):
        self.identities = {}
        self._loading = True
        self.load_from_config()
        self._loading = False
    def load_from_config(self):
        self._loading = True
        if not os.path.exists(CONFIG_PATH):
            return
        fn = os.path.join(CONFIG_PATH, 'identities.json')
        if not os.path.exists(fn):
            return
        with open(fn, 'r') as f:
            s = f.read()
        data = json.loads(s)
        self.add_identities(*data.values())
        self._loading = False
    def save_to_config(self):
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        fn = os.path.join(CONFIG_PATH, 'identities.json')
        s = json.dumps(self.identities, indent=2, cls=IdentityEncoder)
        with open(fn, 'w') as f:
            f.write(s)
        os.chmod(fn, stat.S_IRUSR | stat.S_IWUSR)
    def add_identities(self, *args):
        for arg in args:
            self.add_identity(arg)
        if not self._loading:
            self.save_to_config()
    def add_identity(self, identity):
        if not isinstance(identity, Identity):
            identity = Identity(**identity)
        if identity.id in self.identities:
            existing = self.identities[identity.id]
            if identity != existing:
                raise IdentityExists(identity, existing)
        identity.storage = self
        self.identities[identity.id] = identity
        if not self._loading:
            self.save_to_config()
        return identity
    def on_identity_update(self, **kwargs):
        identity = kwargs.get('identity')
        value = kwargs.get('value')
        if value == identity.id:
            old = kwargs.get('old')
            if old in self.identities:
                del self.identities[old]
            self.identities[value] = identity
        self.save_to_config()
    def get(self, identity_id, default=None):
        return self.identities.get(identity_id, default)
    def keys(self):
        return sorted(self.identities.keys())
    def values(self):
        return (self.identities[key] for key in self.keys())
    def items(self):
        for key in self.keys():
            yield key, self.identities[key]

identity_store = IdentityStore()

class IdentityParser(object):
    """Base class for parsing identities

    When the instance is called, a `list` is returned containing instances of
    :class:`Indentity`
    """
    def __init__(self, filename):
        self.filename = filename
    def __call__(self):
        return self.parse()
    def parse(self):
        raise NotImplementedError('must be defined by subclasses')

class IAMCSVParser(IdentityParser):
    """Parser for csv files generated by the IAM Management Console
    """
    def parse(self):
        with open(self.filename, 'r') as f:
            s = f.read()
        header = None
        keys = ['name', 'access_key_id', 'secret_access_key']
        identities = []
        for line in s.splitlines():
            line = line.split(',')
            if header is None:
                header = line
                continue
            d = {k: line[i] for k, i in enumerate(keys)}
            identities.append(Identity(**d))
        return identities
