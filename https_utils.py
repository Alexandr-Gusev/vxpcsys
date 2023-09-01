from OpenSSL import crypto
from time import time
import os
import ssl


def generate_crt_and_key(hostname):
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    x509 = crypto.X509()
    subject = x509.get_subject()
    subject.commonName = hostname
    x509.set_issuer(subject)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(50 * 365 * 24 * 60 * 60)
    x509.set_pubkey(key)
    x509.set_serial_number(int(time()))
    x509.set_version(2)
    x509.sign(key, "SHA256")

    return crypto.dump_certificate(crypto.FILETYPE_PEM, x509), crypto.dump_privatekey(crypto.FILETYPE_PEM, key)


def create_ssl_context(crt_file, key_file, hostname=None):
    crt_file_exists = os.path.exists(crt_file)
    key_file_exists = os.path.exists(key_file)
    if (crt_file_exists and not key_file_exists) or (not crt_file_exists and key_file_exists):
        raise RuntimeError("can not find crt or key file")
    if not crt_file_exists and not key_file_exists:
        if hostname is None:
            raise RuntimeError("can not find hostname")
        cert, key = generate_crt_and_key(hostname)
        with open(crt_file, "wb") as f:
            f.write(cert)
        with open(key_file, "wb") as f:
            f.write(key)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(crt_file, key_file)
    return context
