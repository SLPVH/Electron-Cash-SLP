import time
from .addressmetadata_pb2 import Entry, Payload, AddressMetadata, Header


def plain_text_entry(text: str):
    body = text.encode('utf8')
    entry = Entry(kind="text_utf8", headers=[], entry_data=body)
    return entry


def telegram_entry(handle: str):
    body = handle.encode('utf8')
    entry = Entry(kind="telegram", headers=[], entry_data=body)
    return entry


def ks_urls_entry(urls: list):
    from .keyservers_pb2 import Keyservers

    body = Keyservers(urls=urls).SerializeToString()
    entry = Entry(kind="ks_urls", headers=[], entry_data=body)
    return entry


def pubkey_entry(pubkey: bytes):
    entry = Entry(kind="pubkey", headers=[], entry_data=pubkey)
    return entry


def vcard_entry(card: dict):
    import vobject

    v = vobject.vCard()
    v.add('fn')
    v.fn.value = card["name"]
    v.add('email')
    v.email.value = card["email"]
    v.add('tel')
    v.tel.type_param = "MOBILE"
    v.tel.value = card["mobile"]
    body = v.serialize().encode('utf8')

    entry = Entry(kind="vcard", headers=[], entry_data=body)
    return entry

def icon_entry(logo: bytes):
    entry = Entry(kind="icon", headers=[], entry_data=logo)
    return entry

def html_entry(html: str):
    body = html.encode('utf8')
    entry = Entry(kind="html", headers=[], entry_data=body)
    return entry
  