from backend import Cache, query_upstream
from config import load_config_or_exit, load_list
from domains import is_valid_domain, matches, normalize

def make_result(domain, source, status, ip="-", ttl="-"):
    return {"Domain": domain, "Source": source, "Status": status, "IP": ip, "TTL": ttl}

def print_block(result):
    """Always exactly five lines, then one blank line."""
    for label in ("Domain", "Source", "Status", "IP", "TTL"):
        print(f"{label} : {result[label]}")
    print()

def resolve(text, cfg, ad_list, sanction_list, cache):
    """Apply the fixed decision order and return the result dict."""
    if text == "":
        return make_result("(empty)", "NONE", "INVALID_INPUT")
    if not is_valid_domain(text):
        return make_result(text, "NONE", "INVALID_INPUT")

    name = normalize(text)

    if matches(name, ad_list):
        return make_result(name, "AD_BLOCK", "OK", cfg["sinkhole_ip"], cfg["local_ttl"])

    if matches(name, sanction_list):
        return make_result(name, "SANCTION", "OK", cfg["proxy_ip"], cfg["local_ttl"])

    if cfg["cache_enabled"]:
        hit = cache.get(name)
        if hit is not None:
            ip, remaining = hit
            return make_result(name, "CACHE", "OK", ip, remaining)

    try:
        status, ip, ttl = query_upstream(name, cfg)
    except Exception:
        status, ip, ttl = "SERVER_ERROR", None, None

    if status == "OK":
        if cfg["cache_enabled"] and ttl is not None and ttl > 0:
            cache.put(name, ip, ttl)
        return make_result(name, "UPSTREAM", "OK", ip, ttl)
    if status == "NOT_FOUND":
        return make_result(name, "UPSTREAM", "NOT_FOUND")
    return make_result(name, "UPSTREAM", "SERVER_ERROR")

def main():
    cfg = load_config_or_exit()
    ad_list = load_list(cfg["ad_list_file"])
    sanction_list = load_list(cfg["sanction_list_file"])
    cache = Cache()

    print("DNS Proxy ready.")
    while True:
        try:
            line = input("Enter domain (or exit): ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        text = line.strip()
        if text.lower() == "exit":
            print("Bye.")
            break

        print_block(resolve(text, cfg, ad_list, sanction_list, cache))

if __name__ == "__main__":
    main()
