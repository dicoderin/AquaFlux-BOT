# Diimpor dari library yang diperlukan
from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, json, time, re, os, pytz

# Inisialisasi zona waktu WIB
wib = pytz.timezone('Asia/Jakarta')

class AquaFlux:
    def __init__(self) -> None:
        self.HEADERS = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://playground.aquaflux.pro",
            "Referer": "https://playground.aquaflux.pro/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://api.aquaflux.pro/api/v1"
        self.RPC_URL = "https://testnet.dplabs-internal.com/"
        self.AQUAFLUX_NFT_ADDRESS = "0xCc8cF44E196CaB28DBA2d514dc7353af0eFb370E"
        self.AQUAFLUX_CONTRACT_ABI = json.loads('[{"type":"function","name":"claimTokens","stateMutability":"nonpayable","inputs":[],"outputs":[]},{"type":"function","name":"combineCS","stateMutability":"nonpayable","inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"outputs":[]},{"type":"function","name":"combinePC","stateMutability":"nonpayable","inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"outputs":[]},{"type":"function","name":"combinePS","stateMutability":"nonpayable","inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"outputs":[]},{"type":"function","name":"hasClaimedStandardNFT","stateMutability":"view","inputs":[{"internalType":"address","name":"owner","type":"address"}],"outputs":[{"internalType":"bool","name":"","type":"bool"}]},{"type":"function","name":"hasClaimedPremiumNFT","stateMutability":"view","inputs":[{"internalType":"address","name":"owner","type":"address"}],"outputs":[{"internalType":"bool","name":"","type":"bool"}]},{"type":"function","name":"mint","stateMutability":"nonpayable","inputs":[{"internalType":"enum AquafluxNFT.NFTType","name":"nftType","type":"uint8"},{"internalType":"uint256","name":"expiresAt","type":"uint256"},{"internalType":"bytes","name":"signature","type":"bytes"}],"outputs":[]}]')
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.used_nonce = {}
        self.mint_count = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%Y-%m-%d %H:%M:%S %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(f"""
    {Fore.GREEN + Style.BRIGHT}AquaFlux NFT{Fore.BLUE + Style.BRIGHT} Auto BOT
    {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
    """)

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def load_proxies(self, use_proxy_choice: bool):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f: f.write(content)
                self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
            else:
                self.log(f"{Fore.GREEN + Style.BRIGHT}Proxies Total : {Style.RESET_ALL}{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}")
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes): return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies: return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies: return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def build_proxy_config(self, proxy=None):
        if not proxy: return None, None, None
        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None
        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None
        raise Exception("Unsupported Proxy Type.")

    def generate_address(self, account: str):
        try:
            return Account.from_key(account).address
        except Exception: return None

    def mask_account(self, account):
        try: return account[:6] + '*' * 6 + account[-6:]
        except Exception: return None

    def generate_payload(self, account: str, address: str):
        try:
            timestamp = int(time.time()) * 1000
            message = f"Sign in to AquaFlux with timestamp: {timestamp}"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)
            return {"address": address, "message": message, "signature": signature}
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        if use_proxy and proxy: request_kwargs["proxy"] = proxy
        
        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                if web3.is_connected(): return web3
                else: raise Exception("Web3 is not connected.")
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")

    # --- FIX UTAMA: HELPER BARU UNTUK SEMUA RPC CALL ---
    async def rpc_call_with_retry(self, func_to_execute, retries=5):
        """
        Wrapper untuk mengeksekusi fungsi web3.py (spt .call() atau .estimate_gas())
        dengan mekanisme retry yang menangani error throttling RPC.
        """
        last_exception = None
        for attempt in range(retries):
            try:
                result = await asyncio.to_thread(func_to_execute)
                return result
            except Exception as e:
                last_exception = e
                error_message = str(e)
                if "EXCEED_THROTTLE" in error_message or "rate limit" in error_message.lower():
                    wait_time = 5 + (attempt * 3)
                    self.log(f"{Fore.YELLOW+Style.BRIGHT}[Attempt {attempt+1}/{retries}] RPC throttling on call. Waiting for {wait_time}s...{Style.RESET_ALL}")
                    await asyncio.sleep(wait_time)
                else:
                    self.log(f"{Fore.YELLOW+Style.BRIGHT}[Attempt {attempt+1}/{retries}] Other RPC error: {error_message}. Retrying...{Style.RESET_ALL}")
                    await asyncio.sleep(2 ** attempt)
        raise Exception(f"RPC call failed after {retries} retries.") from last_exception

    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        """Wrapper untuk mengirim transaksi, juga dengan penanganan throttling."""
        last_exception = None
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                return web3.to_hex(raw_tx)
            except Exception as e:
                last_exception = e
                error_message = str(e)
                if "EXCEED_THROTTLE" in error_message or "rate limit" in error_message.lower():
                    wait_time = 10 + (attempt * 5)
                    self.log(f"{Fore.YELLOW + Style.BRIGHT}[Attempt {attempt+1}/{retries}] RPC throttling on send. Waiting for {wait_time}s...{Style.RESET_ALL}")
                    await asyncio.sleep(wait_time)
                else:
                    self.log(f"{Fore.YELLOW + Style.BRIGHT}[Attempt {attempt+1}/{retries}] Send TX Error: {error_message}. Retrying...{Style.RESET_ALL}")
                    await asyncio.sleep(2 ** attempt)
        raise Exception(f"Failed to send transaction after {retries} retries.") from last_exception


    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except Exception as e:
                self.log(f"{Fore.YELLOW + Style.BRIGHT}[Attempt {attempt + 1}] Wait for Receipt Error: {str(e)}{Style.RESET_ALL}")
                await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")

    async def perform_onchain_action(self, account: str, address: str, use_proxy: bool, action_name: str, build_tx_func):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            tx_data = build_tx_func(web3, address)
            
            # Menggunakan helper baru untuk estimasi gas
            estimated_gas = await self.rpc_call_with_retry(lambda: tx_data.estimate_gas({"from": address}))
            
            max_priority_fee = web3.to_wei(1, "gwei")
            base_fee = (await self.rpc_call_with_retry(lambda: web3.eth.get_block('latest')))['baseFeePerGas']
            max_fee = base_fee * 2 + max_priority_fee
            
            tx = tx_data.build_transaction({
                "from": web3.to_checksum_address(address), "gas": int(estimated_gas * 1.5),
                "maxFeePerGas": int(max_fee), "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address], "chainId": web3.eth.chain_id,
            })
            
            tx_hash = await self.send_raw_transaction_with_retries(account, web3, tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            
            self.used_nonce[address] += 1
            return tx_hash, receipt.blockNumber
            
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error during '{action_name}': {str(e)}{Style.RESET_ALL}")
            return None, None

    async def perform_claim_tokens(self, account: str, address: str, use_proxy: bool):
        def build_tx(web3, addr):
            contract = web3.eth.contract(address=web3.to_checksum_address(self.AQUAFLUX_NFT_ADDRESS), abi=self.AQUAFLUX_CONTRACT_ABI)
            return contract.functions.claimTokens()
        return await self.perform_onchain_action(account, address, use_proxy, "Claim Tokens", build_tx)

    async def perform_combine_tokens(self, account: str, address: str, combine_option: str, use_proxy: bool):
        def build_tx(web3, addr):
            contract = web3.eth.contract(address=web3.to_checksum_address(self.AQUAFLUX_NFT_ADDRESS), abi=self.AQUAFLUX_CONTRACT_ABI)
            amount_to_wei = web3.to_wei(100, "ether")
            if combine_option == "Combine CS": return contract.functions.combineCS(amount_to_wei)
            elif combine_option == "Combine PC": return contract.functions.combinePC(amount_to_wei)
            else: return contract.functions.combinePS(amount_to_wei)
        return await self.perform_onchain_action(account, address, use_proxy, combine_option, build_tx)

    async def perform_mint_nft(self, account: str, address: str, nft_option: str, use_proxy: bool):
        try:
            nft_type = 0 if nft_option == "Standard NFT" else 1
            data = await self.get_signature(address, nft_type, use_proxy)
            if not data: raise Exception("Failed to GET Signature")
            
            expires_at = data["data"]["expiresAt"]
            signature_bytes = bytes.fromhex(data["data"]["signature"][2:])
            
            def build_tx(web3, addr):
                contract = web3.eth.contract(address=web3.to_checksum_address(self.AQUAFLUX_NFT_ADDRESS), abi=self.AQUAFLUX_CONTRACT_ABI)
                return contract.functions.mint(nft_type, expires_at, signature_bytes)
                
            return await self.perform_onchain_action(account, address, use_proxy, f"Mint {nft_option}", build_tx)
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error preparing mint: {str(e)}{Style.RESET_ALL}")
            return None, None
            
    # Menggunakan helper baru untuk check NFT status
    async def check_nft_status(self, address: str, option: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            contract = web3.eth.contract(address=web3.to_checksum_address(self.AQUAFLUX_NFT_ADDRESS), abi=self.AQUAFLUX_CONTRACT_ABI)
            func_to_call = contract.functions.hasClaimedStandardNFT if option == "Standard NFT" else contract.functions.hasClaimedPremiumNFT
            return await self.rpc_call_with_retry(lambda: func_to_call(web3.to_checksum_address(address)).call())
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Failed to check NFT status after retries: {str(e)}{Style.RESET_ALL}")
            return None

    async def print_timer(self):
        delay = random.randint(self.min_delay, self.max_delay)
        for remaining in range(delay, 0, -1):
            print(f"{Fore.CYAN + Style.BRIGHT}⏳ Waiting for {remaining} seconds...{Style.RESET_ALL}", end="\r", flush=True)
            await asyncio.sleep(1)
        print(" " * 80, end="\r")

    def print_question(self):
        while True:
            try:
                self.mint_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Enter Mint NFT Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if self.mint_count > 0: break
                else: print(f"{Fore.RED}Please enter a positive number.{Style.RESET_ALL}")
            except ValueError: print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")
        
        while True:
            try:
                self.min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Between Tx (seconds) -> {Style.RESET_ALL}").strip())
                if self.min_delay >= 0: break
                else: print(f"{Fore.RED}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError: print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")

        while True:
            try:
                self.max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Between Tx (seconds) -> {Style.RESET_ALL}").strip())
                if self.max_delay >= self.min_delay: break
                else: print(f"{Fore.RED}Max Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError: print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}\n1. Run With Free Proxyscrape Proxy\n2. Run With Private Proxy\n3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())
                if choose in [1, 2, 3]: break
                else: print(f"{Fore.RED}Please enter 1, 2, or 3.{Style.RESET_ALL}")
            except ValueError: print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")
        
        rotate = False
        if choose in [1, 2]:
            while True:
                rotate_input = input(f"{Fore.BLUE + Style.BRIGHT}Rotate proxy if invalid? [y/n] -> {Style.RESET_ALL}").strip().lower()
                if rotate_input in ["y", "n"]:
                    rotate = rotate_input == "y"; break
                else: print(f"{Fore.RED}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")
        return choose, rotate

    async def api_request(self, method: str, url: str, address_for_proxy: str, use_proxy: bool, **kwargs):
        for _ in range(5):
            proxy_url = self.get_next_proxy_for_account(address_for_proxy) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.request(method, url=url, proxy=proxy, proxy_auth=proxy_auth, **kwargs) as response:
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                self.log(f"{Fore.YELLOW+Style.BRIGHT}API request error: {e}. Retrying...{Style.RESET_ALL}")
                await asyncio.sleep(5)
        self.log(f"{Fore.RED+Style.BRIGHT}API request failed after all retries for {url}{Style.RESET_ALL}")
        return None

    async def wallet_login(self, account: str, address: str, use_proxy: bool):
        return await self.api_request("POST", f"{self.BASE_API}/users/wallet-login", address, use_proxy, headers={**self.HEADERS, "Content-Type": "application/json"}, json=self.generate_payload(account, address))
    async def check_binding_status(self, address: str, use_proxy: bool):
        return await self.api_request("GET", f"{self.BASE_API}/users/twitter/binding-status", address, use_proxy, headers={**self.HEADERS, "Authorization": f"Bearer {self.access_tokens[address]}"})
    async def get_signature(self, address: str, nft_type: int, use_proxy: bool):
        return await self.api_request("POST", f"{self.BASE_API}/users/get-signature", address, use_proxy, headers={**self.HEADERS, "Authorization": f"Bearer {self.access_tokens[address]}", "Content-Type": "application/json"}, json={"walletAddress": address, "requestedNftType": nft_type})
    
    def process_log(self, tx_hash, block_number, action_msg):
        explorer = f"https://testnet.pharosscan.xyz/tx/{tx_hash}"
        self.log(f"{Fore.GREEN+Style.BRIGHT}Status: {action_msg} Success{Style.RESET_ALL}")
        self.log(f"{Fore.WHITE+Style.BRIGHT}Block: {block_number} | Tx Hash: {tx_hash}{Style.RESET_ALL}")
        self.log(f"{Fore.WHITE+Style.BRIGHT}Explorer: {explorer}{Style.RESET_ALL}")
        
    async def process_wallet_login(self, account: str, address: str, use_proxy: bool):
        login_data = await self.wallet_login(account, address, use_proxy)
        if login_data and login_data.get("data", {}).get("accessToken"):
            self.access_tokens[address] = login_data["data"]["accessToken"]
            self.log(f"{Fore.GREEN + Style.BRIGHT}Status: Login Success{Style.RESET_ALL}")
            return True
        self.log(f"{Fore.RED + Style.BRIGHT}Status: Login Failed{Style.RESET_ALL}")
        return False

    async def process_onchain_task(self, task_name, task_func, *args):
        self.log(f"{Fore.BLUE+Style.BRIGHT}● Starting: {task_name}{Style.RESET_ALL}")
        tx_hash, block_number = await task_func(*args)
        if tx_hash and block_number:
            self.process_log(tx_hash, block_number, task_name)
            return True
        else:
            self.log(f"{Fore.RED+Style.BRIGHT}Status: {task_name} Failed{Style.RESET_ALL}")
            return False

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        if not await self.process_wallet_login(account, address, use_proxy): return

        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            # Menggunakan helper baru untuk get nonce
            self.used_nonce[address] = await self.rpc_call_with_retry(lambda: web3.eth.get_transaction_count(web3.to_checksum_address(address)))
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Failed to get initial nonce: {e}{Style.RESET_ALL}")
            return

        for i in range(self.mint_count):
            self.log(f"{Fore.MAGENTA+Style.BRIGHT}--- Mint Cycle {i+1} of {self.mint_count} ---{Style.RESET_ALL}")
            for nft_option in ["Standard NFT", "Premium NFT"]:
                self.log(f"{Fore.CYAN+Style.BRIGHT}Processing: {nft_option}{Style.RESET_ALL}")

                if nft_option == "Premium NFT":
                    binding = await self.check_binding_status(address, use_proxy)
                    if not binding or not binding.get("data", {}).get("bound"):
                        self.log(f"{Fore.YELLOW+Style.BRIGHT}Status: Not eligible for Premium NFT (Twitter not bound). Skipping.{Style.RESET_ALL}")
                        continue
                
                has_claimed = await self.check_nft_status(address, nft_option, use_proxy)
                if has_claimed:
                    self.log(f"{Fore.YELLOW+Style.BRIGHT}Status: {nft_option} already minted. Skipping.{Style.RESET_ALL}")
                    continue
                if has_claimed is None: # Gagal mengecek status setelah retry
                    self.log(f"{Fore.RED+Style.BRIGHT}Could not verify NFT status. Skipping this cycle.{Style.RESET_ALL}")
                    continue

                if not await self.process_onchain_task("Claim Tokens", self.perform_claim_tokens, account, address, use_proxy): continue
                await self.print_timer()

                combine_option = random.choice(["Combine CS", "Combine PC", "Combine PS"])
                if not await self.process_onchain_task(combine_option, self.perform_combine_tokens, account, address, combine_option, use_proxy): continue
                await self.print_timer()
                
                if not await self.process_onchain_task(f"Mint {nft_option}", self.perform_mint_nft, account, address, nft_option, use_proxy): continue
                await self.print_timer()
            self.log(f"{Fore.GREEN+Style.BRIGHT}--- End of Mint Cycle {i+1} ---{Style.RESET_ALL}\n")

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}"); return
            
        use_proxy_choice, rotate_proxy = self.print_question()
        use_proxy = use_proxy_choice in [1, 2]

        self.clear_terminal(); self.welcome()
        self.log(f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}")
        if use_proxy: await self.load_proxies(use_proxy_choice)
        
        separator = "=" * 25
        for account in accounts:
            if account:
                address = self.generate_address(account)
                if not address:
                    self.log(f"{Fore.RED + Style.BRIGHT}Invalid Private Key found. Skipping.{Style.RESET_ALL}"); continue
                
                self.log(f"{Fore.CYAN + Style.BRIGHT}{separator}[ {self.mask_account(address)} ]{separator}{Style.RESET_ALL}")
                await self.process_accounts(account, address, use_proxy, rotate_proxy)
                await asyncio.sleep(5)

        self.log(f"{Fore.GREEN+Style.BRIGHT}All accounts have been processed.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = AquaFlux()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED + Style.BRIGHT}[ EXIT ] AquaFlux NFT BOT Terminated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED+Style.BRIGHT}An unexpected critical error occurred: {e}{Style.RESET_ALL}")
