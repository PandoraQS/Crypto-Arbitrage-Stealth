import asyncio
import ccxt.pro as ccxt
import redis
import json
import os
import time

r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0)

SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']
EXCHANGES = ['binance', 'kraken']

async def fetch_order_book(exchange_id, symbol):
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class()
    
    while True:
        try:
            orderbook = await exchange.watch_order_book(symbol)
            
            bid_depth = sum([b[1] for b in orderbook['bids'][:5]])
            ask_depth = sum([a[1] for a in orderbook['asks'][:5]])
            
            local_ts = time.time() * 1000
            latency = local_ts - orderbook['timestamp'] if orderbook['timestamp'] else 0
            
            data = {
                "exchange": exchange_id,
                "symbol": symbol,
                "bid": orderbook['bids'][0][0] if orderbook['bids'] else 0,
                "ask": orderbook['asks'][0][0] if orderbook['asks'] else 0,
                "bid_depth": bid_depth,
                "ask_depth": ask_depth,
                "latency": latency,
                "timestamp": orderbook['timestamp']
            }
            
            r.set(f"ticker:{exchange_id}:{symbol}", json.dumps(data))
            
        except Exception as e:
            await asyncio.sleep(5)

async def main():
    tasks = [fetch_order_book(ex, sym) for sym in SYMBOLS for ex in EXCHANGES]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    time.sleep(5)
    asyncio.run(main())