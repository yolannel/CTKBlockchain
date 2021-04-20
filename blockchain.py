# https://hackernoon.com/learn-blockchains-by-building-one-117428612f46
import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.tx = []
        self.chain = []
        self.nodes = set()
        self.mine_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Add a new node
        :parameter address: Address of node. For example, 'http://127.0.0.1:5000' where 5000 is the port
        """

        url = urlparse(address)
        if url.netloc:
            self.nodes.add(url.netloc)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Make sure chain is fully connected with valid proofs.
        :parameter chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]

        for i, block in enumerate(chain):
            if i == 0:
                continue
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False
            last_block = block
        return True

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Check proof is valid.
        :parameter last_proof: previous proof
        :parameter proof: current proof
        :parameter last_hash: hash of the previous block
        :return: True if correct, False if not.
        """
        test = f'{last_proof}{proof}{last_hash}'.encode()
        guess = hashlib.sha256(test).hexdigest()
        return guess[:4] == "0000"

    def resolve(self):
        """
        Achieve consensus by always validating the longest chain as truth.
        :return: True if our chain was replaced, False if not
        """

        nodes = self.nodes
        other = None
        max_length = len(self.chain)

        for node in nodes:
            testchain = requests.get(f'http://{node}/chain')

            if testchain.status_code == 200:
                length = testchain.json()['length']
                chain = testchain.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    other = chain

        if other:
            print("CHAIN WAS REPLACED")
            self.chain = other
            return True

        return False

    def mine_block(self, proof, previous_hash):
        """
        Mine a new block.
        :parameter proof: proof of work algorithm
        :parameter previous_hash: hash of previous block
        :return: new block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'tx': self.tx,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.tx = []
        self.chain.append(block)
        return block

    def new_tx(self, sender, receiver, amount):
        """
        Create a new transaction.
        :parameter sender: address of sender
        :parameter receiver: address of receiver
        :parameter amount: tx amount
        :return: The index of the Block that will hold this tx
        """
        self.tx.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Uses SHA-256 to create a hash.
        :parameter block: block
        """

        block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block).hexdigest()

    def proof_of_work(self, last_block):
        """
        Find a number b such that hash(ab) contains 4 leading zeros when a is the previous proof, and b is the new proof
        :parameter last_block: last block
        :return: int value
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)
        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1
        return proof


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/tx/new', methods=['POST'])
def new_tx():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'receiver', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new tx
    index = blockchain.new_tx(values['sender'], values['receiver'], values['amount'])

    response = {'message': f'tx will be added to block {index}'}
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)
    # reward the miner for mining new block
    blockchain.new_tx(
        sender="0",
        receiver=node_identifier,
        amount=1,
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.mine_block(proof, previous_hash)

    response = {
        'message': "New block was forged",
        'index': block['index'],
        'tx': block['tx'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Nodes invalid", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New node(s) added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
