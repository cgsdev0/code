try:
    from .client_libldap import LdapClient
except ImportError:
    from .client_ldap3 import LdapClient

class NullrouteLdapClient(LdapClient):
    base = "dc=nullroute,dc=eu,dc=org"

    def __init__(self):
        super().__init__("ldaps://ldap.nullroute.eu.org")

def connect_auth():
    conn = NullrouteLdapClient()
    conn.bind_gssapi()
    return conn
