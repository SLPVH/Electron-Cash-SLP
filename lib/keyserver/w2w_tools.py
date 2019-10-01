from .messaging_pb2 import Entry

def w2w_plain_text_entry(text: str):
    return Entry(kind="text_utf8", entry_data=text.encode("utf8"))