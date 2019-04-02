from nullroute.core import Core
import subprocess

def store_libsecret(label, secret, attributes):
    Core.trace("libsecret store: %r %r", label, attributes)
    cmd = ["secret-tool", "store", "--label=%s" % label]
    for k, v in attributes.items():
        cmd += [str(k), str(v)]

    r = subprocess.run(cmd, input=secret.encode(),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise IOError("libsecret store failed: (%r, %r)" % (r.returncode,
                                                            r.stderr.decode()))

def get_libsecret(attributes):
    Core.trace("libsecret query: %r", attributes)
    cmd = ["secret-tool", "lookup"]
    for k, v in attributes.items():
        cmd += [str(k), str(v)]

    r = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise KeyError("libsecret lookup failed: %r" % r.stderr.decode())

    return r.stdout.decode()

def clear_libsecret(attributes):
    Core.trace("libsecret clear: %r", attributes)
    cmd = ["secret-tool", "clear"]
    for k, v in attributes.items():
        cmd += [str(k), str(v)]

    r = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise KeyError("libsecret clear failed: %r" % r.stderr.decode())

def get_netrc(machine, login=None, service=None):
    if service:
        machine = "%s/%s" % (service, machine)

    keys = ["%m", "%l", "%p", "%a"]
    cmd = ["getnetrc", "-d", "-n", "-f", "\n".join(keys), machine]
    if login:
        cmd.append(login)

    r = subprocess.run(cmd, stdout=subprocess.PIPE)
    if r.returncode != 0:
        raise KeyError("~/.netrc lookup for %r failed" % machine)

    keys = ["machine", "login", "password", "account"]
    vals = r.stdout.decode().split("\n")
    if len(keys) != len(vals):
        raise IOError("'getnetrc' returned weird data %r" % r)

    return dict(zip(keys, vals))

def get_netrc_service(machine, service, **kw):
    return get_netrc("%s/%s" % (service, machine), **kw)

def seal_windpapi(secret: bytes, entropy=None) -> bytes:
    import win32crypt
    sealed = win32crypt.CryptProtectData(secret,
                                         None, # description
                                         entropy,
                                         None, # reserved
                                         None, # prompt
                                         0x01) # flags
    return sealed

def unseal_windpapi(sealed: bytes, entropy=None) -> bytes:
    import win32crypt
    (desc, secret) = win32crypt.CryptUnprotectData(sealed,
                                                   entropy,
                                                   None, # reserved
                                                   None, # prompt
                                                   0x01) # flags
    return secret
