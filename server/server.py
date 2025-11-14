# server/server.py
import asyncio
from datetime import datetime, timezone
import logging

import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from ocpp.routing import on
from ocpp.v16 import ChargePoint as CpBase
from ocpp.v16 import call_result
from ocpp.v16.enums import (
    Action,
    RegistrationStatus,
    AuthorizationStatus,
)
from ocpp.v16.datatypes import IdTagInfo

logging.basicConfig(level=logging.INFO)


class CentralSystemChargePoint(CpBase):
    @on(Action.boot_notification)
    async def on_boot_notification(self, charge_point_vendor, charge_point_model, **kwargs):
        logging.info(
            "BootNotification from CP '%s' - vendor=%s model=%s extra=%s",
            self.id, charge_point_vendor, charge_point_model, kwargs
        )

        return call_result.BootNotification(
            current_time=datetime.now(tz=timezone.utc).isoformat(),
            interval=10,
            status=RegistrationStatus.accepted,
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self):
        logging.info("Heartbeat from CP '%s'", self.id)
        return call_result.Heartbeat(
            current_time=datetime.now(tz=timezone.utc).isoformat()
        )

    # New: StatusNotification

    @on(Action.status_notification)
    async def on_status_notification(self, connector_id, error_code, status, **kwargs):
        logging.info(
            "StatusNotification from CP '%s' - connector=%s status=%s error=%s extra=%s",
            self.id, connector_id, status, error_code, kwargs,
        )
        # Response has no fields in OCPP 1.6
        return call_result.StatusNotification()

    # New: Authorize

    @on(Action.authorize)
    async def on_authorize(self, id_tag, **kwargs):
        logging.info("Authorize from CP '%s' - idTag=%s extra=%s",
                     self.id, id_tag, kwargs)
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.Authorize(id_tag_info=id_tag_info)

    # New: StartTransaction

    @on(Action.start_transaction)
    async def on_start_transaction(
        self,
        connector_id,
        id_tag,
        meter_start,
        timestamp,
        **kwargs,
    ):
        logging.info(
            "StartTransaction from CP '%s' - connector=%s idTag=%s meter_start=%s ts=%s extra=%s",
            self.id, connector_id, id_tag, meter_start, timestamp, kwargs,
        )
        # In a real system, generate/stash a transaction id.
        transaction_id = 1  # For now, always 1 or increment in your own logic.
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.StartTransaction(
            transaction_id=transaction_id,
            id_tag_info=id_tag_info,
        )

    # New: MeterValues

    @on(Action.meter_values)
    async def on_meter_values(self, connector_id, transaction_id, meter_value, **kwargs):
        logging.info(
            "MeterValues from CP '%s' - connector=%s tx_id=%s meter_value=%s extra=%s",
            self.id, connector_id, transaction_id, meter_value, kwargs,
        )
        return call_result.MeterValues()

    # New: StopTransaction

    @on(Action.stop_transaction)
    async def on_stop_transaction(self, transaction_id, meter_stop, timestamp, **kwargs):
        logging.info(
            "StopTransaction from CP '%s' - tx_id=%s meter_stop=%s ts=%s extra=%s",
            self.id, transaction_id, meter_stop, timestamp, kwargs,
        )
        id_tag_info = IdTagInfo(status=AuthorizationStatus.accepted)
        return call_result.StopTransaction(id_tag_info=id_tag_info)


async def on_connect(connection: websockets.ServerConnection):
    charge_point_id = connection.request.path.split("/")[-1]
    logging.info("New CP connected: %s", charge_point_id)

    cp = CentralSystemChargePoint(charge_point_id, connection)
    try:
        await cp.start()
    except ConnectionClosedOK:
        logging.info("CP '%s' disconnected normally.", charge_point_id)
    except ConnectionClosedError as e:
        logging.warning("CP '%s' disconnected with error: %s",
                        charge_point_id, e)
    except Exception:
        logging.exception("Unexpected error in connection handler for CP '%s'",
                          charge_point_id)


async def main():
    server = await websockets.serve(
        on_connect,
        host="0.0.0.0",
        port=9000,
        subprotocols=["ocpp1.6"],
    )
    logging.info("CSMS listening on ws://0.0.0.0:9000/")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
