# client/client.py
import asyncio
import logging
from datetime import datetime, timezone
from typing import List

import websockets

from ocpp.v16 import ChargePoint as CpBase
from ocpp.v16 import call, call_result
from ocpp.v16.enums import (
    RegistrationStatus,
    ChargePointStatus,
    ChargePointErrorCode,
)
from ocpp.v16.datatypes import MeterValue, SampledValue

logging.basicConfig(level=logging.INFO)


class ChargePoint(CpBase):
    def __init__(self, cp_id, websocket):
        super().__init__(cp_id, websocket)
        self.heartbeat_interval = 10  # default; updated from BootNotification
        self.current_transaction_id: int | None = None

    # Boot + Heartbeat

    async def send_boot_notification(self):
        request = call.BootNotification(
            charge_point_model="MyTestModel",
            charge_point_vendor="MyStartup",
        )

        logging.info("%s: sending BootNotification", self.id)
        response: call_result.BootNotification = await self.call(request)
        logging.info("%s: BootNotification response: %s", self.id, response)

        if response.status == RegistrationStatus.accepted:
            print("✓ Connected to central system.")
            self.heartbeat_interval = response.interval
            asyncio.create_task(self.heartbeat_loop())
        else:
            print("/!\ BootNotification not accepted:", response.status)

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            req = call.Heartbeat()
            logging.info("%s: sending Heartbeat", self.id)
            resp: call_result.Heartbeat = await self.call(req)
            logging.info("%s: Heartbeat response: %s", self.id, resp)

    # New: StatusNotification

    async def send_status_notification(self, connector_id: int, status: str):
        """
        Send a StatusNotification for a connector.
        'status' is a string like 'Available', 'Preparing', 'Charging', ...
        """
        # Map plain string to enum if possible, else pass as string
        status_enum = ChargePointStatus[status] if status in ChargePointStatus.__members__ else status

        req = call.StatusNotification(
            connector_id=connector_id,
            error_code=ChargePointErrorCode.no_error,
            status=status_enum,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        logging.info("%s: sending StatusNotification %s on connector %s",
                     self.id, status, connector_id)
        resp: call_result.StatusNotification = await self.call(req)
        logging.info("%s: StatusNotification response: %s", self.id, resp)

    # New: Authorize

    async def send_authorize(self, id_tag: str):
        req = call.Authorize(id_tag=id_tag)
        logging.info("%s: sending Authorize for idTag=%s", self.id, id_tag)
        resp: call_result.Authorize = await self.call(req)
        logging.info("%s: Authorize response: %s", self.id, resp)
        return resp

    # New: StartTransaction

    async def send_start_transaction(self, connector_id: int, id_tag: str):
        """
        Start a transaction, store transaction_id received from CSMS.
        """
        req = call.StartTransaction(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        logging.info(
            "%s: sending StartTransaction(connector=%s, idTag=%s)",
            self.id, connector_id, id_tag,
        )
        resp: call_result.StartTransaction = await self.call(req)
        logging.info("%s: StartTransaction response: %s", self.id, resp)

        self.current_transaction_id = resp.transaction_id
        logging.info("%s: stored transaction_id=%s",
                     self.id, self.current_transaction_id)
        return resp

    # New: MeterValues

    async def send_meter_values(self, connector_id: int, values: List[float]):
        """
        Send a sequence of MeterValues for current transaction.
        Very simplified: one sample per OCPP MeterValues call.
        """
        if self.current_transaction_id is None:
            logging.warning("%s: no active transaction, skipping MeterValues",
                            self.id)
            return

        for v in values:
            mv = MeterValue(
                timestamp=datetime.now(timezone.utc).isoformat(),
                sampled_value=[SampledValue(value=str(v))],
            )
            req = call.MeterValues(
                connector_id=connector_id,
                transaction_id=self.current_transaction_id,
                meter_value=[mv],
            )
            logging.info("%s: sending MeterValues value=%s", self.id, v)
            resp: call_result.MeterValues = await self.call(req)
            logging.info("%s: MeterValues response: %s", self.id, resp)

    # New: StopTransaction

    async def send_stop_transaction(self, meter_stop: int = 100):
        if self.current_transaction_id is None:
            logging.warning("%s: no active transaction, skipping StopTransaction",
                            self.id)
            return

        req = call.StopTransaction(
            transaction_id=self.current_transaction_id,
            meter_stop=meter_stop,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        logging.info(
            "%s: sending StopTransaction(transaction_id=%s, meter_stop=%s)",
            self.id, self.current_transaction_id, meter_stop,
        )
        resp: call_result.StopTransaction = await self.call(req)
        logging.info("%s: StopTransaction response: %s", self.id, resp)

        self.current_transaction_id = None

    # Default main (unused when using scenario_runner)

async def main():
    cp_id = "CP_1"

    async with websockets.connect(
        "ws://localhost:9000/" + cp_id,
        subprotocols=["ocpp1.6"],
    ) as ws:
        charge_point = ChargePoint(cp_id, ws)

        await asyncio.gather(
            charge_point.start(),
            charge_point.send_boot_notification(),
        )


if __name__ == "__main__":
    asyncio.run(main())
