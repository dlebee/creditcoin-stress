import json
import threading
import time
from typing import Optional
from locust import HttpUser, between, task
from substrateinterface import SubstrateInterface, Keypair
import os, binascii

request_id = 1

def random_address() -> bytes:
    return bytes('0x', encoding='utf8') + binascii.b2a_hex(os.urandom(15))


headers = {
    'content-type': "application/json",
    'cache-control': "no-cache"
}

id_lock = threading.Lock()
user_id = 1
FUND_AMOUNT = 100_000_000_000_000_000_000 # 100 CTC


class CreditcoinUser(HttpUser):
    wait_time = between(1, 1)
    @task
    def register_address(self):
        self.create_and_send(
            module='Creditcoin',
            function='register_address',
            params={
                'blockchain': 'Ethereum',
                'address': random_address(),
            }
        )

    def create_and_send(self, module: str, function: str, params: dict, keypair: Optional[Keypair] = None):
        extrinsic = self.build_extrinsic(module, function, params, keypair)
        self.post_extrinsic(extrinsic)

    def post_extrinsic(self, extrinsic):
        global request_id
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

    def build_extrinsic(self, module, function, params, keypair = None):
        if not keypair:
            keypair = self.keypair
        call = self.substrate.compose_call(
            call_module=module,
            call_function=function,
            call_params=params
        )
        return self.substrate.create_signed_extrinsic(call, keypair)

    def free_balance(self, keypair=None):
        if not keypair:
            keypair = self.keypair
        return int(str(self.substrate.query('System', 'Account', [f'0x{keypair.public_key.hex()}'])['data']['free']))

    def on_start(self):
        global user_id, id_lock, request_id
        with id_lock:
            user_str = '//user//' + f'0000{user_id}'[-4:]
            user_id += 1
        
        alice = Keypair.create_from_uri('//Alice')
        self.keypair = Keypair.create_from_uri(user_str)
        url = self.host
        self.substrate = SubstrateInterface(
            url=url,
            ss58_format=42,
            type_registry_preset='substrate-node-template'
        )
        balance = self.free_balance()
        if balance < FUND_AMOUNT:
            self.create_and_send(
                'Balances',
                'transfer',
                {'dest': self.keypair.ss58_address, 'value': (FUND_AMOUNT - balance)},
                keypair=alice
            )
        while self.free_balance() <= balance:
            time.sleep(5)
        print('funded')
