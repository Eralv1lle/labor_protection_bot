import sys
import os
import subprocess
import signal
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

processes = []


def generate_ssl_cert():
    print("Генерация SSL сертификата...")

    try:
        from OpenSSL import crypto

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().C = "RU"
        cert.get_subject().ST = "Moscow"
        cert.get_subject().L = "Moscow"
        cert.get_subject().O = "LaborProtectionBot"
        cert.get_subject().OU = "Dev"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')

        with open("cert.pem", "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open("key.pem", "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

        print("✅ SSL сертификат сгенерирован")
        return True

    except ImportError:
        print("PyOpenSSL не установлен, используем adhoc SSL")
        return False
    except Exception as e:
        print(f"Ошибка генерации SSL: {e}")
        return False

def signal_handler(sig, frame):
    print('\nОстановка сервисов...')
    for proc in processes:
        proc.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()

    from backend.models import init_db

    init_db()
    generate_ssl_cert()

    flask_proc = subprocess.Popen(
        [sys.executable, os.path.join(PROJECT_ROOT, 'backend', 'app.py')],
        cwd=PROJECT_ROOT
    )
    processes.append(flask_proc)
    print(f'Flask started (PID: {flask_proc.pid})')

    time.sleep(2)

    bot_proc = subprocess.Popen(
        [sys.executable, os.path.join(PROJECT_ROOT, 'bot', 'bot.py')],
        cwd=PROJECT_ROOT,
        env={**os.environ, 'PYTHONPATH': PROJECT_ROOT}
    )
    processes.append(bot_proc)
    print(f'Bot started (PID: {bot_proc.pid})')

    for proc in processes:
        proc.wait()