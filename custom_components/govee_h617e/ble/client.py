"""Async BLE transport for Govee H617E."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from bleak import BleakClient, BleakError

from ..const import GOVEE_WRITE_CHAR_UUID

_LOGGER = logging.getLogger(__name__)


class GoveeBleClient:
    """Wrapper around bleak with serialized command writes and reconnect behavior."""

    def __init__(
        self,
        address: str,
        connect_timeout: float,
        retry_count: int,
        client_factory: Callable[[str], BleakClient] | None = None,
    ) -> None:
        self._address = address
        self._connect_timeout = connect_timeout
        self._retry_count = retry_count
        self._client_factory = client_factory or (lambda addr: BleakClient(addr, timeout=connect_timeout))
        self._client: BleakClient | None = None
        self._write_lock = asyncio.Lock()
        self._available = False

    @property
    def available(self) -> bool:
        return self._available

    async def async_connect(self) -> None:
        if self._client and self._client.is_connected:
            self._available = True
            return

        self._client = self._client_factory(self._address)
        await asyncio.wait_for(self._client.connect(), timeout=self._connect_timeout)
        self._available = True

    async def async_disconnect(self) -> None:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._available = False

    async def async_write(self, payload: bytes) -> None:
        async with self._write_lock:
            last_error: Exception | None = None
            for attempt in range(self._retry_count + 1):
                try:
                    await self.async_connect()
                    assert self._client is not None
                    await self._client.write_gatt_char(GOVEE_WRITE_CHAR_UUID, payload, response=False)
                    self._available = True
                    return
                except (BleakError, TimeoutError, asyncio.TimeoutError) as err:
                    last_error = err
                    self._available = False
                    _LOGGER.warning(
                        "BLE write failed for %s on attempt %s/%s: %s",
                        self._address,
                        attempt + 1,
                        self._retry_count + 1,
                        err,
                    )
                    await self.async_disconnect()
                    await asyncio.sleep(min(0.5 * (attempt + 1), 2))

            raise RuntimeError(f"Unable to write BLE payload after retries: {last_error}")

    async def async_ping(self) -> None:
        """Connection health-check used by coordinator polling."""
        await self.async_connect()
