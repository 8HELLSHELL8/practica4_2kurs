import requests
import random
import time
import threading

class TradingBot:
    def __init__(self, api_url, port, username):
        self.api_url = f"{api_url}:{port}"
        self.username = username
        self.api_key = self.register_user()

    def register_user(self):
        try:
            payload = {"username": self.username}
            response = requests.post(f"{self.api_url}/user", json=payload)
            response.raise_for_status()
            data = response.json()
            key = data.get("key")
            if not key:
                raise ValueError("Сервер не вернул ключ пользователя.")
            return key
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения: {e}")
            raise
        except ValueError as e:
            print(f"Ошибка данных: {e}")
            raise

    def send_order(self, order_type, pair_id, quantity, price):
        payload = {
            "pair_id": pair_id,
            "quantity": quantity,
            "price": price,
            "type": order_type  # "buy" или "sell"
        }
        headers = {"X-USER-KEY": self.api_key}
        try:
            response = requests.post(f"{self.api_url}/order", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка отправки ордера: {e}")
            return {"error": str(e)}

class RandomBot(TradingBot):
    def get_price(self, pair_id):
        headers = {"X-USER-KEY": self.api_key}
        try:
            response = requests.get(f"{self.api_url}/pair", headers=headers)
            response.raise_for_status()
            pairs = response.json()
            for pair in pairs:
                if pair["pair_id"] == pair_id:
                    return pair["sale_lot_id"]
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения цены: {e}")
        return None

    def trade(self, pair_id):
        while True:
            price = self.get_price(pair_id)
            if not price:
                print("Ошибка получения цены.")
                continue

            order_type = random.choice(["buy", "sell"])
            quantity = random.uniform(0.01, 1.0)  # Случайный объем
            order_price = float(price) * random.uniform(0.95, 1.05)  # Случайное отклонение

            result = self.send_order(order_type, pair_id, quantity, order_price)
            print(f"RandomBot: {result}")
            time.sleep(3)  # Один ордер в секунду

class AlgorithmicBot(TradingBot):
    def get_order_list(self):
        headers = {"X-USER-KEY": self.api_key}
        try:
            response = requests.get(f"{self.api_url}/orderlist", headers=headers)
            response.raise_for_status()
            orders = response.json()
            if isinstance(orders, list):
                return orders
            else:
                print(f"Ошибка: неожиданный формат ответа: {orders}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения при запросе списка ордеров: {e}")
            return []

    def trade(self, pair_id):
        while True:
            orders = self.get_order_list()
            if not orders:
                print("Нет доступных ордеров для анализа.")
                time.sleep(1)
                continue

            relevant_orders = [
                order for order in orders
                if order["lot_id"] == pair_id and order["closed"] == "open"
            ]

            if not relevant_orders:
                print("Нет активных ордеров для данной пары.")
                time.sleep(1)
                continue

            relevant_orders = [
                order for order in relevant_orders if order["user_id"] != self.username
            ]

            if not relevant_orders:
                print("Нет подходящих ордеров для выполнения.")
                time.sleep(1)
                continue

            buy_orders = [order for order in relevant_orders if order["type"] == "buy"]
            sell_orders = [order for order in relevant_orders if order["type"] == "sell"]

            if buy_orders:
                best_buy_order = max(buy_orders, key=lambda x: float(x["price"]))
                result = self.send_order(
                    "sell",
                    pair_id,
                    best_buy_order["quantity"],
                    float(best_buy_order["price"])
                )
                print(f"AlgorithmicBot (Sell): {result}")

            if sell_orders:
                best_sell_order = min(sell_orders, key=lambda x: float(x["price"]))
                result = self.send_order(
                    "buy",
                    pair_id,
                    best_sell_order["quantity"],
                    float(best_sell_order["price"])
                )
                print(f"AlgorithmicBot (Buy): {result}")

            time.sleep(3)  

if __name__ == "__main__":
    api_url = "http://localhost"
    port = 8080
    pair_id = 5  

    random_bot = RandomBot(api_url, port, "random_user")
    threading.Thread(target=random_bot.trade, args=(pair_id,)).start()

    algorithmic_bot = AlgorithmicBot(api_url, port, "algorithmic_user")
    threading.Thread(target=algorithmic_bot.trade, args=(pair_id,)).start()
