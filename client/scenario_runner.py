# client/scenario_runner.py
import json
import asyncio
import logging
import sys

import websockets

from .client import ChargePoint

logging.basicConfig(level=logging.INFO)


async def run_scenario(path: str):
    with open(path) as f:
        scenario = json.load(f)

    cp_id = scenario["cp_id"]
    server_url = scenario["server_url"]

    async with websockets.connect(
        f"{server_url}/{cp_id}",
        subprotocols=["ocpp1.6"],
    ) as ws:
        cp = ChargePoint(cp_id, ws)

        # Listener task: handle incoming messages from CSMS
        listener_task = asyncio.create_task(cp.start())

        for step in scenario["script"]:
            action = step["action"]

            if action == "boot":
                await cp.send_boot_notification()

            elif action == "wait":
                seconds = step.get("seconds", 1)
                logging.info("Scenario: waiting %s seconds", seconds)
                await asyncio.sleep(seconds)

            elif action == "status":
                connector_id = step.get("connectorId", 1)
                status = step["status"]
                await cp.send_status_notification(connector_id, status)

            elif action == "authorize":
                id_tag = step["idTag"]
                await cp.send_authorize(id_tag)

            elif action == "start_transaction":
                connector_id = step.get("connectorId", 1)
                id_tag = step["idTag"]
                await cp.send_start_transaction(connector_id, id_tag)

            elif action == "meter_values":
                connector_id = step.get("connectorId", 1)
                values = step.get("values", [])
                await cp.send_meter_values(connector_id, values)

            elif action == "stop_transaction":
                meter_stop = step.get("meterStop", 100)
                await cp.send_stop_transaction(meter_stop)

            elif action == "exit":
                logging.info("Scenario: exit requested, stopping.")
                break

            else:
                logging.warning("Unknown action in scenario: %s", action)

        listener_task.cancel()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m client.scenario_runner <scenario.json>")
        sys.exit(1)

    scenario_path = sys.argv[1]
    asyncio.run(run_scenario(scenario_path))
