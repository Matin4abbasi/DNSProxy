
import socket
import time
import ipaddress
import math


class Cache:
    def __init__(self):
        # هر ورودی شامل IP، TTL اولیه و زمان دریافت است
        self.data = {}

    def get(self, name):
        # یکسان‌سازی نام دامنه برای کلید Cache
        key = name.lower().rstrip(".")

        if key not in self.data:
            return None

        ip, ttl, received_time = self.data[key]

        # محاسبه زمان سپری‌شده
        elapsed = int(time.monotonic() - received_time)

        # محاسبه TTL باقی‌مانده
        remaining_ttl = ttl - elapsed

        # حذف ورودی منقضی‌شده
        if remaining_ttl < 1:
            del self.data[key]
            return None

        return ip, remaining_ttl

    def put(self, name, ip, ttl):
        # فقط TTL مثبت در Cache ذخیره می‌شود
        if ttl <= 0:
            return

        key = name.lower().rstrip(".")

        # زمان دریافت پاسخ
        received_time = time.monotonic()

        self.data[key] = (ip, ttl, received_time)

    def clear(self):
        # پاک کردن تمام اطلاعات Cache
        self.data.clear()


def query_upstream(name, cfg):
    """
    ارسال درخواست UDP به سرور Upstream

    خروجی‌ها:
        ("OK", ip, ttl)
        ("NOT_FOUND", None, None)
        ("SERVER_ERROR", None, None)
    """

    try:
        # خواندن تنظیمات
        upstream_ip = str(
            ipaddress.IPv4Address(cfg["upstream_ip"])
        )

        upstream_port = int(cfg["upstream_port"])
        timeout = float(cfg["upstream_timeout_sec"])

        # اعتبارسنجی پورت
        if not 1 <= upstream_port <= 65535:
            return ("SERVER_ERROR", None, None)

        # اعتبارسنجی Timeout
        # باید عددی مثبت و محدود باشد
        if not math.isfinite(timeout) or timeout <= 0:
            return ("SERVER_ERROR", None, None)

        # ساخت پیام درخواست
        message = f"QUERY {name}".encode("utf-8")

        # ساخت سوکت UDP
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        ) as client:

            # تنظیم Timeout
            client.settimeout(timeout)

            # ارسال درخواست
            client.sendto(
                message,
                (upstream_ip, upstream_port)
            )

            # دریافت فقط یک پاسخ؛ بدون تلاش مجدد
            response, _ = client.recvfrom(1024)

            # تبدیل پاسخ به متن
            response = response.decode("utf-8").strip()
            parts = response.split()

            # بررسی پاسخ OK
            if len(parts) == 3 and parts[0] == "OK":

                ip = parts[1]

                # بررسی معتبر بودن IPv4
                ipaddress.IPv4Address(ip)

                # TTL باید عدد صحیح نامنفی باشد
                if not parts[2].isdecimal():
                    return ("SERVER_ERROR", None, None)

                ttl = int(parts[2])

                return ("OK", ip, ttl)

            # پاسخ دامنه پیدا نشد
            if response == "NOT_FOUND":
                return ("NOT_FOUND", None, None)

            # هر پاسخ دیگری نامعتبر است
            return ("SERVER_ERROR", None, None)

    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        OverflowError
    ):
        # خطای ارتباط، Timeout یا پاسخ نامعتبر
        return ("SERVER_ERROR", None, None)
