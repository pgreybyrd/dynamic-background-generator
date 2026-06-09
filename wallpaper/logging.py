import datetime

def debug_log(message, debug=False, log_path=None):
    if not debug:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    print(message)