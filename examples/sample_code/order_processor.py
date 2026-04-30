"""订单处理模块 - 包含多种代码异味"""


class OrderProcessor:
    def __init__(self, inventory, payment, shipping, email):
        self.inventory = inventory
        self.payment = payment
        self.shipping = shipping
        self.email = email

    def process_order(self, order):
        """处理订单 - 300 行的巨型函数"""
        items = order.get("items", [])
        user = order.get("user", {})
        address = order.get("address", {})
        coupon = order.get("coupon")

        total = 0
        for item in items:
            price = item.get("price", 0)
            qty = item.get("qty", 1)
            total += price * qty

        if coupon:
            if coupon == "SAVE10":
                total = total * 0.9
            elif coupon == "SAVE20":
                total = total * 0.8
            elif coupon == "VIP50":
                total = total * 0.5
            elif coupon == "NEWUSER":
                total = total - 20
            else:
                pass

        for item in items:
            sku = item.get("sku")
            qty = item.get("qty", 1)
            stock = self.inventory.check(sku)
            if stock < qty:
                return {"error": "out of stock", "sku": sku}

        for item in items:
            sku = item.get("sku")
            qty = item.get("qty", 1)
            self.inventory.reserve(sku, qty)

        if total > 0:
            payment_ok = self.payment.charge(user.get("id"), total)
            if not payment_ok:
                for item in items:
                    sku = item.get("sku")
                    qty = item.get("qty", 1)
                    self.inventory.release(sku, qty)
                return {"error": "payment failed"}

        tracking = self.shipping.create_shipment(address, items)
        if not tracking:
            for item in items:
                sku = item.get("sku")
                qty = item.get("qty", 1)
                self.inventory.release(sku, qty)
                self.payment.refund(user.get("id"), total)
            return {"error": "shipping failed"}

        self.email.send(user.get("email"), "order_confirmation",
                        {"order": order, "tracking": tracking})

        return {"status": "ok", "tracking": tracking}
