import base64
import hashlib
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Util.Padding import pad, unpad
from Cryptodome.Cipher import PKCS1_OAEP


def get_pssh(inia):
    raw = base64.b64decode(inia) if isinstance(inia, str) else inia
    offset = raw.rfind(b"pssh")
    d = base64.b64encode(raw[offset - 4 : offset - 4 + raw[offset - 1]])
    return d.decode("utf-8")


# def is_dir(path):
#     if not os.path.exists(path):
#         os.makedirs(path)


# def check_file():
#     files = ["./cache", "./download"]
#     for file in files:
#         is_dir(file)


def b64decode(data: str):
    data = data + "=" * (4 - len(data) % 4)
    return base64.b64decode(data)


def djb2Hash(e):
    if e is None:
        return
    t = 5381
    for r in range(len(e)):
        t += (t << 5) + ord(e[r])
    return t & 2147483647


def aes_encrypt(key: bytes, data: bytes, iv: Optional[bytes] = None):
    if iv is None:
        iv = b"\x00" * 16
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = pad(data, cipher.block_size)
    return cipher.encrypt(data)


def aes_decrypt(key: bytes, data: bytes, iv: Optional[bytes] = None):
    if iv is None:
        iv = b"\x00" * 16
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = cipher.decrypt(data)
    return unpad(data, cipher.block_size)


def rsa_dec(prikey, data: bytes):
    key = RSA.importKey(prikey)
    cipher = PKCS1_OAEP.new(key)
    ret = b""
    k = cipher._key.size_in_bytes()
    for i in range(0, len(data), k):
        ret += cipher.decrypt(data[i : i + k])
    return ret.decode()


def sha1withrsa(prikey, data: bytes):
    key = RSA.importKey(prikey)
    h = SHA1.new(data)
    signer = pkcs1_15.new(key)
    signature = signer.sign(h)
    return base64.b64encode(signature).decode()


def dealck(cookie: str):
    cks = cookie.split(";")
    ckdict = {}
    if not cks:
        raise Exception("cookie is empty")
    for item in cks:
        item = item.strip()
        items = item.split("=")
        ckdict[items[0]] = items[1]
    return ckdict


def md5(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()


def get_size(size: int | float) -> str:
    size_suffixes = ["B", "KB", "MB", "GB"]
    for suffix in size_suffixes:
        if size < 1024:
            return f"{size:.2f}{suffix}"
        size /= 1024
    return f"{size:.2f}TB"
