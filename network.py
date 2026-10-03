"""Игра вдвоем по локальной сети.

Схема «хост — клиент»: хост считает весь игровой мир, клиент отправляет
только свои нажатия клавиш и получает снимки состояния мира (60 раз в секунду).
Сообщения — JSON-строки, разделенные переводом строки, поверх TCP.
Поиск игр в сети — UDP-широковещание хоста раз в секунду.
"""
import json
import socket
import threading
import time
from collections import deque

from settings import NET_PORT, DISCOVERY_PORT, PROTOCOL_VERSION

DISCOVERY_TAG = "alien_invasion"


class Connection:
    """TCP-соединение: отправка и фоновый прием JSON-сообщений."""

    def __init__(self, sock):
        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(None)
        self.alive = True
        self._send_lock = threading.Lock()
        self._inbox = deque()
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buffer = b""
        try:
            while self.alive:
                data = self.sock.recv(65536)
                if not data:
                    break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line:
                        self._inbox.append(json.loads(line))
        except (OSError, ValueError):
            pass
        self.alive = False

    def send(self, message):
        if not self.alive:
            return
        data = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        try:
            with self._send_lock:
                self.sock.sendall(data)
        except OSError:
            self.alive = False

    def receive_all(self):
        """Все сообщения, пришедшие с прошлого вызова."""
        messages = []
        while self._inbox:
            messages.append(self._inbox.popleft())
        return messages

    def close(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


class HostServer:
    """Сервер хоста: ждет одного напарника и объявляет игру в сети."""

    def __init__(self, port=NET_PORT):
        self.port = port
        self.conn = None
        self.running = True
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("", port))
        self.listener.listen(2)
        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._announce_loop, daemon=True).start()

    @property
    def connected(self):
        return self.conn is not None and self.conn.alive

    def _accept_loop(self):
        while self.running:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                break
            if self.connected:
                sock.close()   # место уже занято
            else:
                self.conn = Connection(sock)

    def _announce_loop(self):
        # Отдельный сокет на каждый сетевой интерфейс: иначе при VPN или
        # нескольких адаптерах широковещание уходит не в ту сеть.
        senders = []
        for ip in local_ips():
            try:
                udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                udp.bind((ip, 0))
                subnet_broadcast = ip.rsplit(".", 1)[0] + ".255"
                senders.append((udp, ("255.255.255.255", subnet_broadcast)))
            except OSError:
                pass
        while self.running:
            message = json.dumps({"game": DISCOVERY_TAG, "ver": PROTOCOL_VERSION,
                                  "port": self.port, "name": socket.gethostname(),
                                  "busy": self.connected}).encode()
            for udp, addresses in senders:
                for address in addresses:
                    try:
                        udp.sendto(message, (address, DISCOVERY_PORT))
                    except OSError:
                        pass
            time.sleep(1)
        for udp, _ in senders:
            udp.close()

    def send(self, message):
        if self.connected:
            self.conn.send(message)

    def receive_all(self):
        return self.conn.receive_all() if self.conn else []

    def close(self):
        self.running = False
        if self.conn:
            self.conn.send({"t": "bye"})
            self.conn.close()
        self.listener.close()


class HostFinder:
    """Слушает объявления хостов в локальной сети."""

    def __init__(self):
        self.hosts = {}   # ip -> (имя, порт, занят, время последнего объявления)
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(("", DISCOVERY_PORT))
        except OSError:
            self.running = False
            return
        self.sock.settimeout(0.5)
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        while self.running:
            try:
                data, (ip, _) = self.sock.recvfrom(4096)
                info = json.loads(data)
            except socket.timeout:
                continue
            except (OSError, ValueError):
                break
            if info.get("game") == DISCOVERY_TAG and info.get("ver") == PROTOCOL_VERSION:
                self.hosts[ip] = (info.get("name", ip), info.get("port", NET_PORT),
                                  info.get("busy", False), time.time())

    def active_hosts(self):
        """Найденные хосты; адреса домашних сетей (192.168.x) идут первыми."""
        now = time.time()
        hosts = [(ip, name, port, busy) for ip, (name, port, busy, seen)
                 in list(self.hosts.items()) if now - seen < 3]
        hosts.sort(key=lambda h: (not h[0].startswith("192.168."), h[0]))
        # Один компьютер с несколькими адаптерами показываем один раз
        unique, names = [], set()
        for host in hosts:
            if host[1] not in names:
                names.add(host[1])
                unique.append(host)
        return unique

    def close(self):
        self.running = False
        self.sock.close()


class ClientConnector:
    """Подключение к хосту в фоне, чтобы окно игры не зависало."""

    def __init__(self, ip, port=NET_PORT):
        self.conn = None
        self.error = None
        self.done = False
        threading.Thread(target=self._connect, args=(ip, port), daemon=True).start()

    def _connect(self, ip, port):
        try:
            sock = socket.create_connection((ip, port), timeout=4)
            self.conn = Connection(sock)
        except OSError as e:
            self.error = str(e)
        self.done = True


def local_ips():
    """IP-адреса этого компьютера в локальной сети."""
    ips = []
    try:
        # Пакет не отправляется: так лишь узнаем, через какой адрес идет трафик
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        ips.append(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except OSError:
        pass
    return ips or ["127.0.0.1"]
