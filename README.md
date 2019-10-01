# Electron Cash SLP - Dynamic Metadata

The main component of this system is a new kind of keyserver that is currently under development.

* The keyserver allows users who hold a key pair to put metadata to the associated address.
* Only those able to sign with the private key are permitted to put to that address.
* In order to put to the keyserver you must pay a small fee using the BIP70 protocol.
* The metadata can be updated if the key owner supplies metadata containing a later timestamp.
* Anyone is able to get from any address and, as the metadata and timestamp are covered by the signature the clients can verify the authenticity of the data.
* The keyservers form a peer-to-peer network and the metadata is relayed and replicated across the network.

The use of BIP70 here allows us to mitigate spam attacks and provide a little revenue for the node operators. The employment of signatures means that malicious nodes can, at most, refuse to provide specific metadata - in which case, the relay network/redundancy provides censorship resistance.

The application of this to SLP is that one can insert an address into the genesis transaction. Once this address is cryptographically tied to the token one can use the keyserver/metadata to introduce all sorts of new dynamics to the token.

For the hackathon I've forked Electron Cash SLP to demonstrate how this could be done. We're able to tag a token with a logo, a contact card, HTML and other metadata very smoothly. We're then able to update the metadata at a later point (for example when we want to change email address and logo). Electron Cash's GUI is able to display this easily because it has access to the genesis transaction and hence is able to get from the keyserver.

Future use cases could get much more imaginative: tokens could commit to the token issuers address and have them update metadata as they interact with the world. e.g. this voucher has been upgraded to 30% off, this trading card has won 301 battles and has +10 strength, this cryptokitty is 3 years old and has these children. I could go on but I'll leave it at that for now :D

## Videos

### Uploading Metadata

https://www.youtube.com/watch?v=f9kWPuN9QQg

### Downloading and Updating Metadata

https://www.youtube.com/watch?v=-nDjO54seHA
