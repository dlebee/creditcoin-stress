import json
from locust import HttpUser, task
from substrateinterface import SubstrateInterface, Keypair
import os, binascii

substrate = SubstrateInterface(
    url="http://127.0.0.1:9933",
    ss58_format=42,
    type_registry_preset='substrate-node-template'
)

request_id = 1

def random_address() -> bytes:
    return bytes('0x', encoding='utf8') + binascii.b2a_hex(os.urandom(15))

url = "http://127.0.0.1:9933"

headers = {
    'content-type': "application/json",
    'cache-control': "no-cache"
}

user_id = 1

class CreditcoinUser(HttpUser):
    @task
    def register_address(self):
        global request_id
        call = substrate.compose_call(
            call_module='Creditcoin',
            call_function='register_address',
            call_params={
                'blockchain': 'ethereum',
                'address': random_address(),
                'network': 'mainnet'
            }
        )
        extrinsic = substrate.create_signed_extrinsic(call, self.keypair)
        method = 'author_submitExtrinsic'
        params = [str(extrinsic.data)]
        payload = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'id': request_id
        }
        request_id += 1
        self.client.post('', data=json.dumps(payload), headers=headers)

    def on_start(self):
        self.keypair = Keypair.create_from_uri('//Alice')
