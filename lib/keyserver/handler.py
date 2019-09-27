import random
import requests
from .addressmetadata_pb2 import Entry, Payload, AddressMetadata, Header


class Extracted:
    url = None
    metadata = None
    confidence = 0


class KSHandler:
    '''
    KSHandler deals with operations relating to the management of keyservers
    and GET and PUT requests
    '''
    # Hardcoded trusted nodes
    # TODO: Mainnet vs Testnet
    trusted_ks_urls = ["http://35.232.229.28", "http://34.67.137.105"]

    # Address holding peer list
    trusted_keyservers_addr = ""

    def __init__(self, ks_urls: list = None, default_sample_size: int = 6):
        self.default_sample_size = default_sample_size

        if ks_urls is None:
            self.ks_urls = self.trusted_ks_urls
        else:
            self.ks_urls = self.trusted_ks_urls + ks_urls

    def set_keyservers(self, urls: list):
        self.ks_urls = self.trusted_ks_urls + urls

    @staticmethod
    def _validate_sig(addr: str, payload: Payload):
        # TODO: Check signature
        # TODO: Check addr ~ pubkey
        return True

    @staticmethod
    def construct_metadata(ks_url: str, addr: str):
        url = "%s/keys/%s" % (ks_url, addr)
        response = requests.get(url=url)
        if response.status_code != 200:
            raise Exception("%s - %s" % (response.status_code, response.text))
        addr_metadata = AddressMetadata.FromString(response.content)
        return addr_metadata

    @staticmethod
    def _uniform_aggregate(ks_urls: list, addr: str, sample_size: int):
        best = None
        errors = []

        sample_size = min([len(ks_urls), sample_size])
        sample_set = random.sample(ks_urls, sample_size)

        for url in sample_set:
            try:
                new_metadata = KSHandler.construct_metadata(url, addr)
                new_timestamp = new_metadata.payload.timestamp

                if KSHandler._validate_sig(addr, new_metadata):
                    if best is None:
                        best = Extracted()
                        best.confidence = 1
                        best.url = url
                        best.metadata = new_metadata
                    else:
                        if new_timestamp < best.metadata.payload.timestamp:
                            raise Exception("older timestamp")

                        if new_metadata == best.metadata:
                            if new_timestamp > best.metadata.payload.timestamp:
                                best.confidence = 0
                                best.url = url
                            else:
                                best.confidence += 1
                        else:
                            best.metadata = new_metadata
                            best.confidence = 0
                            best.url = url

            except Exception as e:
                errors.append((url, e))

        if best is not None:
            # This is safe because it'll raise earlier if len is 0
            best.confidence = best.confidence / len(ks_urls)

        return best, errors

    def uniform_aggregate(self, addr: str, sample_size: int = None):
        if sample_size is None:
            sample_size = self.default_sample_size
        return KSHandler._uniform_aggregate(self.ks_urls, addr, sample_size=sample_size)

    def uniform_sample(self):
        return random.choice(self.ks_urls)
