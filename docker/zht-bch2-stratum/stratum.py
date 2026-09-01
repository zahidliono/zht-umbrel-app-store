#!/usr/bin/env python3
"""BCH2 Solo Stratum Server — Stratum v1 for SHA-256 solo mining."""

import asyncio, hashlib, json, logging, os, struct, time
import urllib.request, base64, binascii

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stratum")

# ── Config ────────────────────────────────────────────────────────────────────
RPC_HOST = os.getenv("RPC_HOST", "umbrel-host")
RPC_PORT = int(os.getenv("RPC_PORT", "9010"))
RPC_USER = os.getenv("RPC_USER", "zahidliono")
RPC_PASS = os.getenv("RPC_PASS", "Idd=9108")
PAYOUT   = os.getenv("PAYOUT_ADDRESS", "bitcoincashii:qqrdx0ayq4zduygkv03qd6hs55lxs0345syv78d9v3")
PORT     = int(os.getenv("STRATUM_PORT", "4582"))
DIFF     = int(os.getenv("DIFFICULTY", "1"))
CB_MSG   = os.getenv("COINBASE_MSG", "ZHT")[:96]

# ── Crypto ────────────────────────────────────────────────────────────────────
def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def varint(n: int) -> bytes:
    if n < 0xfd:   return struct.pack("B", n)
    if n <= 0xffff: return b"\xfd" + struct.pack("<H", n)
    return b"\xfe" + struct.pack("<I", n)

# ── Address → P2PKH script ────────────────────────────────────────────────────
_CASHADDR = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BASE58   = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def _cashaddr_hash160(addr: str) -> bytes:
    payload = addr.lower().split(":")[-1]
    vals = [_CASHADDR.index(c) for c in payload][:-8]   # strip 8-char checksum
    bits = acc = 0
    out = bytearray()
    for v in vals:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xff)
    return bytes(out[1:21])   # skip version byte, take 20-byte hash

def _base58_hash160(addr: str) -> bytes:
    n = 0
    for c in addr:
        n = n * 58 + _BASE58.index(c)
    return n.to_bytes(25, "big")[1:21]

def address_to_script(addr: str) -> bytes:
    try:
        h = _cashaddr_hash160(addr) if (":" in addr or addr[:1] == "q") else _base58_hash160(addr)
    except Exception:
        h = b"\x00" * 20
    return b"\x76\xa9\x14" + h + b"\x88\xac"

# ── RPC ───────────────────────────────────────────────────────────────────────
def rpc(method: str, params=None):
    body = json.dumps({"jsonrpc": "1.1", "id": 1, "method": method,
                        "params": params or []}).encode()
    creds = base64.b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode()
    req = urllib.request.Request(
        f"http://{RPC_HOST}:{RPC_PORT}/",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if resp.get("error"):
        raise RuntimeError(resp["error"])
    return resp["result"]

# ── Merkle helpers ────────────────────────────────────────────────────────────
def merkle_branches(txids: list) -> list:
    """Branches for stratum: coinbase pairs with each successive sibling."""
    if not txids:
        return []
    nodes = [b"\x00" * 32] + list(txids)
    steps = []
    while len(nodes) > 1:
        if len(nodes) % 2:
            nodes.append(nodes[-1])
        steps.append(nodes[1])
        nodes = [sha256d(nodes[i] + nodes[i + 1]) for i in range(0, len(nodes), 2)]
    return steps

def apply_branches(cb_txid: bytes, steps: list) -> bytes:
    root = cb_txid
    for s in steps:
        root = sha256d(root + s)
    return root

# ── Job ───────────────────────────────────────────────────────────────────────
EN1_LEN = 4
EN2_LEN = 4

class Job:
    __slots__ = ("id", "version", "prevhash", "bits", "curtime",
                 "height", "en1", "cb1", "cb2", "branches", "txns")

    def __init__(self, tpl: dict, en1: bytes):
        self.id       = binascii.hexlify(os.urandom(4)).decode()
        self.version  = tpl["version"]
        self.prevhash = tpl["previousblockhash"]
        self.bits     = tpl["bits"]
        self.curtime  = tpl["curtime"]
        self.height   = tpl["height"]
        self.en1      = en1
        self.txns     = tpl.get("transactions", [])

        value   = tpl.get("coinbasevalue", 0)
        h_enc   = self.height.to_bytes(max(1, (self.height.bit_length() + 7) // 8), "little")
        msg     = CB_MSG.encode()
        sigpfx  = bytes([len(h_enc)]) + h_enc + bytes([len(msg)]) + msg
        sig_len = len(sigpfx) + EN1_LEN + EN2_LEN
        out_s   = address_to_script(PAYOUT)

        self.cb1 = (
            struct.pack("<I", 1) + b"\x01" +
            b"\x00" * 32 + struct.pack("<I", 0xffffffff) +
            varint(sig_len) + sigpfx + en1
        ).hex()
        self.cb2 = (
            struct.pack("<I", 0xffffffff) + b"\x01" +
            struct.pack("<Q", value) + varint(len(out_s)) + out_s +
            struct.pack("<I", 0)
        ).hex()

        txids = [bytes.fromhex(t["txid"])[::-1] for t in self.txns]
        self.branches = merkle_branches(txids)

    # ── Stratum notify params ─────────────────────────────────────────────────
    def notify_params(self, clean=True) -> list:
        ph = bytes.fromhex(self.prevhash)
        # Reverse the order of 4-byte groups; bytes within each group stay intact.
        ph_stratum = b"".join(ph[i:i+4] for i in range(28, -1, -4)).hex()
        return [
            self.id,
            ph_stratum,
            self.cb1, self.cb2,
            [s.hex() for s in self.branches],
            struct.pack("<I", self.version).hex(),   # version little-endian
            self.bits,                                # bits big-endian (as-is)
            format(self.curtime, "08x"),              # ntime big-endian
            clean,
        ]

    # ── Share validation ──────────────────────────────────────────────────────
    def _coinbase_txid(self, en2: str) -> bytes:
        raw = bytes.fromhex(self.cb1) + bytes.fromhex(en2) + bytes.fromhex(self.cb2)
        return sha256d(raw)

    def merkle_root(self, en2: str) -> bytes:
        return apply_branches(self._coinbase_txid(en2), self.branches)

    def _header(self, en2: str, ntime: str, nonce: str) -> bytes:
        return (
            struct.pack("<I", self.version) +
            bytes.fromhex(self.prevhash)[::-1] +     # display→internal
            self.merkle_root(en2) +
            bytes.fromhex(ntime)[::-1] +              # BE hex → LE bytes
            bytes.fromhex(self.bits)[::-1] +          # BE hex → LE bytes
            bytes.fromhex(nonce)[::-1]                # BE hex → LE bytes
        )

    def hash_value(self, en2: str, ntime: str, nonce: str) -> int:
        h = sha256d(self._header(en2, ntime, nonce))
        return int.from_bytes(h[::-1], "big")

    def build_block(self, en2: str, ntime: str, nonce: str) -> str:
        cb_raw = bytes.fromhex(self.cb1) + bytes.fromhex(en2) + bytes.fromhex(self.cb2)
        tx_list = [cb_raw] + [bytes.fromhex(t["data"]) for t in self.txns if "data" in t]
        block = self._header(en2, ntime, nonce) + varint(len(tx_list))
        for tx in tx_list:
            block += tx
        return block.hex()

# ── Difficulty ────────────────────────────────────────────────────────────────
DIFF1 = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

def diff_to_target(d: int) -> int:
    return DIFF1 // d

def bits_to_target(bits_hex: str) -> int:
    b = int(bits_hex, 16)
    return (b & 0xffffff) * (2 ** (8 * ((b >> 24) - 3)))

# ── Miner session ─────────────────────────────────────────────────────────────
class MinerSession:
    def __init__(self, reader, writer, server):
        self.reader  = reader
        self.writer  = writer
        self.server  = server
        self.peer    = writer.get_extra_info("peername")
        self.en1     = os.urandom(EN1_LEN)
        self.target  = diff_to_target(DIFF)
        self.jobs: dict[str, Job] = {}

    def _send(self, obj: dict):
        self.writer.write((json.dumps(obj) + "\n").encode())

    async def run(self):
        log.info("Miner connected %s", self.peer)
        try:
            while True:
                line = await asyncio.wait_for(self.reader.readline(), timeout=600)
                if not line:
                    break
                await self._dispatch(json.loads(line.decode().strip()))
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError, EOFError):
            pass
        except Exception as e:
            log.error("Session %s error: %s", self.peer, e)
        finally:
            log.info("Miner disconnected %s", self.peer)
            self.writer.close()
            self.server.sessions.discard(self)

    async def _dispatch(self, msg: dict):
        mid, method, params = msg.get("id"), msg.get("method", ""), msg.get("params", [])

        if method == "mining.subscribe":
            self._send({"id": mid, "result": [
                [["mining.notify", "zht01"]],
                self.en1.hex(), EN2_LEN], "error": None})
            self._send({"id": None, "method": "mining.set_difficulty", "params": [DIFF]})
            self.push_job(self.server.template, clean=True)

        elif method == "mining.authorize":
            worker = params[0] if params else "?"
            log.info("Worker authorized %s @ %s", worker, self.peer)
            self._send({"id": mid, "result": True, "error": None})

        elif method == "mining.submit":
            await self._submit(mid, params)

        elif method == "mining.get_transactions":
            self._send({"id": mid, "result": [], "error": None})

        else:
            if mid is not None:
                self._send({"id": mid, "result": None, "error": None})

    def push_job(self, tpl: dict | None, clean: bool = False):
        if tpl is None:
            return
        job = Job(tpl, self.en1)
        self.jobs[job.id] = job
        if len(self.jobs) > 20:
            oldest = next(iter(self.jobs))
            del self.jobs[oldest]
        self._send({"id": None, "method": "mining.notify", "params": job.notify_params(clean)})

    async def _submit(self, mid, params):
        try:
            if len(params) < 5:
                raise ValueError
            _, job_id, en2, ntime, nonce = params[0], params[1], params[2], params[3], params[4]
            # params[5] would be version_bits (BIP320 AsicBoost) — ignored for now
        except (ValueError, TypeError, IndexError):
            log.warning("Malformed submit params from %s: %s", self.peer, params)
            self._send({"id": mid, "result": False, "error": [20, "Malformed params", None]})
            return

        job = self.jobs.get(job_id)
        if not job:
            self._send({"id": mid, "result": False, "error": [21, "Job not found", None]})
            return

        log.info("Share submitted: en2=%s ntime=%s nonce=%s job=%s", en2, ntime, nonce, job_id)

        # Accept all shares unconditionally (solo mining — no one to cheat).
        # Only check network difficulty to detect block solutions.
        self._send({"id": mid, "result": True, "error": None})
        log.info("Share accepted from %s  height=%d", self.peer, job.height)

        # Check both nonce byte orders in case firmware differs from our convention.
        net_target = bits_to_target(job.bits)
        for n in (nonce, bytes.fromhex(nonce)[::-1].hex()):
            val = job.hash_value(en2, ntime, n)
            if val <= net_target:
                log.info("*** BLOCK FOUND at height %d! Submitting ***", job.height)
                blk = job.build_block(en2, ntime, n)
                loop = asyncio.get_event_loop()
                try:
                    result = await loop.run_in_executor(None, rpc, "submitblock", [blk])
                    if result is None:
                        log.info("Block accepted by the network!")
                    else:
                        log.warning("submitblock returned: %s", result)
                except Exception as e:
                    log.error("submitblock error: %s", e)
                break

# ── Server ────────────────────────────────────────────────────────────────────
class StratumServer:
    def __init__(self):
        self.sessions: set[MinerSession] = set()
        self.template: dict | None = None
        self._last_height = -1

    async def _poll(self):
        while True:
            try:
                tpl = await asyncio.get_event_loop().run_in_executor(
                    None, rpc, "getblocktemplate", [{}])
                height = tpl["height"]
                clean  = height != self._last_height
                if clean:
                    log.info("New block height=%d  bits=%s", height, tpl["bits"])
                    self._last_height = height
                self.template = tpl
                for s in set(self.sessions):
                    s.push_job(tpl, clean)
                    clean = False   # only first push is clean
            except Exception as e:
                log.error("getblocktemplate error: %s", e)
            await asyncio.sleep(0.5)

    async def _accept(self, reader, writer):
        s = MinerSession(reader, writer, self)
        self.sessions.add(s)
        await s.run()

    async def _status(self):
        """Tiny HTTP status page on port 8080 (non-privileged)."""
        async def handle(r, w):
            await r.readline()  # consume request line
            body = (
                f"<h1>BCH2 Solo Stratum</h1>"
                f"<p>Height: {self._last_height}</p>"
                f"<p>Miners connected: {len(self.sessions)}</p>"
                f"<p>Stratum port: {PORT}</p>"
                f"<p>Payout: {PAYOUT}</p>"
            ).encode()
            w.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n"
                    b"Connection: close\r\n\r\n" + body)
            await w.drain()
            w.close()
        srv = await asyncio.start_server(handle, "0.0.0.0", 8080)
        async with srv:
            await srv.serve_forever()

    async def run(self):
        stratum = await asyncio.start_server(self._accept, "0.0.0.0", PORT)
        log.info("Stratum listening on port %d  payout=%s", PORT, PAYOUT)
        asyncio.create_task(self._poll())
        asyncio.create_task(self._status())
        async with stratum:
            await stratum.serve_forever()

if __name__ == "__main__":
    asyncio.run(StratumServer().run())
