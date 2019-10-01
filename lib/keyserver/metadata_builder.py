from .addressmetadata_pb2 import Entry, Payload, AddressMetadata
from hashlib import sha256
from time import time


class MetadataBuilder:
    def __init__(self, addr: str = None, ttl: int = 3_000, signer=None):
        self.entries = []
        self.signer = signer
        self.addr = addr
        self.ttl = ttl

    def _is_incomplete(self):
        return (self.signer is None) or (self.addr is None)

    def set_signer(self, signer):
        self.signer = signer

    def set_addr(self, addr: str):
        self.addr = addr

    def set_ttl(self, ttl: int):
        self.ttl = ttl

    def add_entry(self, entry: Entry):
        self.entries.append(entry)

    def add_entry_batch(self, entries: list):
        self.entries.extend(entries)

    def remove_entry(self, index: int):
        del self.entries[index]

    def build(self):
        if self._is_incomplete():
            raise Exception("metadata incomplete")
        
        # Construct Payload
        timestamp = int(time())
        payload = Payload(timestamp=timestamp, ttl=self.ttl,
                          entries=self.entries)

        # Sign
        raw_payload = payload.SerializeToString()
        digest = sha256(raw_payload).digest()
        public_key, signature = self.signer(self.addr, digest)

        # Address metadata
        addr_metadata = AddressMetadata(
            pub_key=public_key, payload=payload, scheme=1, signature=signature)
        raw_addr_meta = addr_metadata.SerializeToString()

        return raw_addr_meta

