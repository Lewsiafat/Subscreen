"""
Minimal asynchronous DNS server for Captive Portal functionality.
Intercepts all DNS queries and redirects them to a specific IP address.
"""
import uasyncio as asyncio
import usocket as socket
from logger import Logger

# DNS Protocol Constants
DNS_FLAGS_RESPONSE = b'\x81\x80'  # Standard query response, No error
DNS_TYPE_A = b'\x00\x01'          # Type A (Host Address)
DNS_CLASS_IN = b'\x00\x01'        # Class IN (Internet)
DNS_DEFAULT_TTL = b'\x00\x00\x00\x3c'  # TTL 60 seconds
DNS_ANSWER_PTR = b'\xc0\x0c'      # Compression pointer to offset 12
DNS_IPV4_LEN = b'\x00\x04'        # IPv4 address length
DNS_MIN_PACKET_LEN = 12           # Minimum valid DNS packet length


class DNSServer:
    """
    A minimal asynchronous DNS server for Captive Portal functionality.
    It intercepts all DNS queries and redirects them to a specific IP address.
    """

    def __init__(self, ip_address: str):
        """
        Initialize the DNS server.

        Args:
            ip_address: The local IP address to redirect all queries to.
        """
        self._log = Logger("DNSServer")
        self.ip_address = ip_address
        self._ip_bytes = self._validate_ip(ip_address)
        self._running = False
        self._task = None

    def _validate_ip(self, ip_str: str) -> bytes:
        """
        Validate and convert IP address string to bytes.

        Args:
            ip_str: IP address in dotted decimal format.

        Returns:
            IP address as 4 bytes, or None if invalid.
        """
        try:
            parts = ip_str.split('.')
            if len(parts) != 4:
                return None
            octets = [int(p) for p in parts]
            if all(0 <= o <= 255 for o in octets):
                return bytes(octets)
        except (ValueError, AttributeError):
            pass
        return None

    def start(self) -> None:
        """Starts the DNS server background task."""
        if not self._running:
            # Re-validate IP in case it was changed
            self._ip_bytes = self._validate_ip(self.ip_address)
            if not self._ip_bytes:
                self._log.error(f"Invalid IP: {self.ip_address}")
                return
            self._running = True
            self._task = asyncio.create_task(self._run())
            self._log.info(f"Started (redirect to {self.ip_address})")

    def stop(self) -> None:
        """Stops the DNS server and cancels the background task."""
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
            self._log.info("Stopped")

    async def _run(self) -> None:
        """Main loop for the DNS server listening on UDP port 53."""
        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)

        try:
            udps.bind(('0.0.0.0', 53))
        except Exception as e:
            self._log.error(f"Failed to bind port 53: {e}")
            udps.close()
            return

        try:
            while self._running:
                try:
                    data, addr = None, None
                    try:
                        data, addr = udps.recvfrom(1024)
                    except OSError:
                        pass  # No data available at this tick

                    if data and addr:
                        response = self._make_response(data)
                        if response:
                            udps.sendto(response, addr)

                    await asyncio.sleep_ms(100)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._log.error(f"Request error: {e}")
                    await asyncio.sleep(1)
        finally:
            udps.close()

    def _make_response(self, request: bytes) -> bytes:
        """
        Constructs a minimal DNS response (A record) pointing to the local IP.

        Args:
            request: The raw DNS request packet.

        Returns:
            The constructed DNS response packet, or None if invalid.
        """
        # Validate minimum packet length
        if len(request) < DNS_MIN_PACKET_LEN:
            return None

        # Validate IP bytes are available
        if not self._ip_bytes:
            return None

        try:
            # DNS Header
            tid = request[0:2]       # Transaction ID
            qdcount = request[4:6]   # Questions count (usually 1)
            ancount = b'\x00\x01'    # Answer count (1)
            nscount = b'\x00\x00'
            arcount = b'\x00\x00'

            packet = tid + DNS_FLAGS_RESPONSE + qdcount + ancount + nscount + arcount

            # Copy the question section from the original request
            payload = request[12:]

            # Answer Section using Compression Pointer
            answer = (DNS_ANSWER_PTR + DNS_TYPE_A + DNS_CLASS_IN +
                      DNS_DEFAULT_TTL + DNS_IPV4_LEN + self._ip_bytes)

            return packet + payload + answer

        except Exception as e:
            self._log.error(f"Response error: {e}")
            return None
