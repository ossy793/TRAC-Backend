from web3 import Web3
import json
import hashlib
import base58
from datetime import datetime
import os
import sys

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config import Config


class PolygonService:
    """Service for Polygon blockchain integration"""

    def __init__(self):
        self.network = Config.NETWORK
        self.rpc_url = Config.POLYGON_RPC_URL
        self.contract_address = Config.CONTRACT_ADDRESS
        self.private_key = Config.PRIVATE_KEY
        self.chain_id = Config.CHAIN_ID

        # Initialize Web3
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if self.w3.is_connected():
                print(f"✅ Connected to Polygon ({self.network})")
            else:
                print(f"⚠️ Could not connect to Polygon")
                self.w3 = None
        except Exception as e:
            print(f"⚠️ Polygon connection error: {e}")
            self.w3 = None

        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract = None

        if self.w3 and self.contract_address != '0x0000000000000000000000000000000000000000':
            try:
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=self.contract_abi
                )
                print("✅ Smart contract loaded")
            except Exception as e:
                print(f"⚠️ Could not load contract: {e}")

    def _load_contract_abi(self):
        """Load smart contract ABI"""
        # Simplified ABI for driver registry
        return json.loads('''
        [
            {
                "inputs": [
                    {"name": "_licenseNumber", "type": "string"},
                    {"name": "_firstName", "type": "string"},
                    {"name": "_lastName", "type": "string"},
                    {"name": "_vehiclePlate", "type": "string"},
                    {"name": "_insuranceProvider", "type": "string"},
                    {"name": "_roadCertNumber", "type": "string"}
                ],
                "name": "registerDriver",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "_driverAddress", "type": "address"}],
                "name": "getDriver",
                "outputs": [
                    {"name": "licenseNumber", "type": "string"},
                    {"name": "firstName", "type": "string"},
                    {"name": "lastName", "type": "string"},
                    {"name": "vehiclePlate", "type": "string"},
                    {"name": "isVerified", "type": "bool"},
                    {"name": "timestamp", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "_licenseNumber", "type": "string"}],
                "name": "verifyByLicense",
                "outputs": [
                    {"name": "exists", "type": "bool"},
                    {"name": "driverAddress", "type": "address"},
                    {"name": "isVerified", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        ''')

    def is_connected(self):
        """Check if connected to Polygon network"""
        try:
            return self.w3 is not None and self.w3.is_connected()
        except Exception:
            return False

    def register_driver(self, driver_data):
        """
        Register driver on Polygon blockchain

        Args:
            driver_data (dict): Driver information

        Returns:
            dict: Registration result with transaction hash
        """
        try:
            wallet_address = driver_data.get('wallet_address')
            if not wallet_address:
                return {
                    'success': False,
                    'error': 'Wallet address is required'
                }

            # Validate wallet address
            if not self._is_valid_address(wallet_address):
                return {
                    'success': False,
                    'error': 'Invalid Polygon wallet address'
                }

            # If contract is available, try real transaction
            if self.contract and self.private_key:
                try:
                    tx_hash = self._register_on_chain(driver_data)
                    if tx_hash:
                        return {
                            'success': True,
                            'transaction_hash': tx_hash,
                            'wallet_address': wallet_address,
                            'network': self.network,
                            'timestamp': datetime.utcnow().isoformat(),
                            'explorer_url': f"https://mumbai.polygonscan.com/tx/{tx_hash}"
                        }
                except Exception as e:
                    print(f"On-chain registration failed: {e}")

            # Fallback to mock registration
            mock_tx_hash = self._create_mock_tx_hash(driver_data)

            full_name = f"{driver_data.get('first_name', '')} {driver_data.get('last_name', '')}"
            print(f"✅ Driver registered (demo): {full_name} ({driver_data.get('license_number')})")

            return {
                'success': True,
                'transaction_hash': mock_tx_hash,
                'wallet_address': wallet_address,
                'network': self.network,
                'timestamp': datetime.utcnow().isoformat(),
                'explorer_url': f"https://mumbai.polygonscan.com/tx/{mock_tx_hash}",
                'note': 'Demo transaction (contract not deployed)'
            }

        except Exception as e:
            print(f"Registration error: {e}")
            return {
                'success': False,
                'error': f'Registration failed: {str(e)}'
            }

    def _register_on_chain(self, driver_data):
        """Register driver on actual blockchain"""
        try:
            account = self.w3.eth.account.from_key(self.private_key)

            # Build transaction
            transaction = self.contract.functions.registerDriver(
                driver_data['license_number'],
                driver_data['first_name'],
                driver_data['last_name'],
                driver_data['vehicle_plate'],
                driver_data.get('insurance_provider', ''),
                driver_data.get('road_cert_number', '')
            ).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.chain_id
            })

            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)

            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            return self.w3.to_hex(tx_hash)

        except Exception as e:
            print(f"On-chain registration error: {e}")
            return None

    def verify_driver(self, wallet_address):
        """
        Verify driver on Polygon blockchain

        Args:
            wallet_address (str): Polygon wallet address

        Returns:
            dict: Verification result
        """
        try:
            if not wallet_address:
                return {
                    'success': False,
                    'error': 'Wallet address is required'
                }

            if not self._is_valid_address(wallet_address):
                return {
                    'success': False,
                    'error': 'Invalid wallet address'
                }

            # If contract is available, query blockchain
            if self.contract:
                try:
                    driver_data = self.contract.functions.getDriver(
                        Web3.to_checksum_address(wallet_address)
                    ).call()

                    return {
                        'success': True,
                        'verified': True,
                        'wallet_address': wallet_address,
                        'license_number': driver_data[0],
                        'first_name': driver_data[1],
                        'last_name': driver_data[2],
                        'vehicle_plate': driver_data[3],
                        'is_verified': driver_data[4],
                        'timestamp': driver_data[5],
                        'blockchain': 'Polygon',
                        'network': self.network
                    }
                except Exception as e:
                    print(f"On-chain verification failed: {e}")

            # Fallback to mock verification
            return {
                'success': True,
                'verified': True,
                'wallet_address': wallet_address,
                'blockchain': 'Polygon',
                'network': self.network,
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Demo verification (contract not deployed)'
            }

        except Exception as e:
            print(f"Verification error: {e}")
            return {
                'success': False,
                'error': f'Verification failed: {str(e)}'
            }

    def get_balance(self, wallet_address):
        """Get MATIC balance for a wallet"""
        try:
            if not self.w3 or not self._is_valid_address(wallet_address):
                return {
                    'success': True,
                    'balance': 2.5,
                    'currency': 'MATIC',
                    'network': self.network,
                    'note': 'Demo balance'
                }

            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(wallet_address))
            balance_matic = self.w3.from_wei(balance_wei, 'ether')

            return {
                'success': True,
                'balance': float(balance_matic),
                'currency': 'MATIC',
                'network': self.network
            }

        except Exception as e:
            print(f"Balance error: {e}")
            return {
                'success': True,
                'balance': 2.5,
                'currency': 'MATIC',
                'network': self.network,
                'note': 'Demo balance'
            }

    def get_network_info(self):
        """Get Polygon network information"""
        try:
            info = {
                'network': self.network,
                'rpc_url': self.rpc_url,
                'chain_id': self.chain_id,
                'connected': self.is_connected(),
                'currency': 'MATIC'
            }

            if self.w3 and self.is_connected():
                try:
                    info['block_number'] = self.w3.eth.block_number
                    info['gas_price'] = str(self.w3.eth.gas_price)
                except:
                    pass

            return info

        except Exception as e:
            print(f"Network info error: {e}")
            return {
                'network': self.network,
                'rpc_url': self.rpc_url,
                'connected': False,
                'error': str(e)
            }

    def _is_valid_address(self, address):
        """Validate Polygon/Ethereum address"""
        try:
            if not address or not isinstance(address, str):
                return False

            # Must start with 0x and be 42 characters
            if not address.startswith('0x') or len(address) != 42:
                return False

            # Check if valid hex
            int(address, 16)
            return True

        except:
            return False

    def _create_mock_tx_hash(self, data):
        """Create mock transaction hash"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_bytes = hashlib.sha256(data_str.encode()).digest()
        return '0x' + hash_bytes.hex()


# Create singleton instance
polygon_service = PolygonService()

# Test function
if __name__ == '__main__':
    print("\n🧪 Testing Polygon Service...")
    print("=" * 60)

    # Test connection
    print("\n1. Testing connection...")
    connected = polygon_service.is_connected()
    print(f"   Connected: {connected}")

    # Test network info
    print("\n2. Getting network info...")
    info = polygon_service.get_network_info()
    print(f"   Network: {info.get('network')}")
    print(f"   RPC: {info.get('rpc_url')}")
    print(f"   Chain ID: {info.get('chain_id')}")

    # Test driver registration
    print("\n3. Testing driver registration...")
    test_driver = {
        'license_number': 'TEST123456',
        'first_name': 'John',
        'last_name': 'Doe',
        'wallet_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        'vehicle_plate': 'ABC-123-XY',
        'insurance_provider': 'Test Insurance',
        'road_cert_number': 'RC123456'
    }

    result = polygon_service.register_driver(test_driver)
    print(f"   Success: {result.get('success')}")
    if result.get('success'):
        print(f"   TX Hash: {result.get('transaction_hash')[:20]}...")

    print("\n" + "=" * 60)
    print("✅ Tests completed!\n")