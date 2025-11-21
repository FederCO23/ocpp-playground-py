# ocpp-playground-py

This repository contains a **Charge Point (CP) client** and a **Central Management System (CMS) server** playground built on top of **OCPP 1.6J** (JSON over WebSockets).

It is meant for experimenting with:

- How a CP boots and connects to a CMS  
- Heartbeats and basic OCPP messages  
- Scenario-based simulations using JSON files  

---

## Project Structure

```text
ocpp-playground-py/
├── client/         # CP (Charge Point) implementation + scenario runner
├── server/         # CMS (Central System) implementation
├── scenarios/      # JSON scenarios describing CP behaviour
├── requirements.txt
├── instructions.txt
└── README.md
```

Key pieces:

- client/ – Contains the CP logic and a scenario_runner module that reads a scenario file and drives the CP behaviour.
- server/ – Minimal CMS implementation that accepts OCPP 1.6J connections.
- scenarios/ – JSON files describing the sequence of CP messages (e.g., BootNotification + Heartbeat).
- instructions.txt – Internal development notes.

---

## Requirements

- Python 3.10+
- Dependencies listed in requirements.txt

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start
1. Clone the repository
```bash
git clone https://github.com/FederCO23/ocpp-playground-py.git
cd ocpp-playground-py
```

2. Start the CMS (server)

Run the CMS entrypoint inside the server/ directory (check the file name you want to use):
```bash
python server/<your_server_file>.py
```

3. Run a CP scenario

From the project root:
```bash
python -m client.scenario_runner scenarios/boot_and_heartbeat_1.json
```

This will:

- Open a WebSocket connection to the CMS
- Execute the scenario steps (BootNotification, Heartbeat, etc.)
- Print logs of all requests and responses

To create your own scenarios, copy any .json file from the scenarios/ directory and modify:
- CMS URL
- Message sequence
- Timing/delays


## Scenarios
Included scenarios demonstrate:
- Boot + Heartbeat flow
- Basic CP–CMS interaction

Future scenarios may include:
- Start/Stop transaction
- StatusNotification variants
- Error testing
- Multiple CPs connecting concurrently

## Development Notes

This repository is intended as a learning playground for understanding OCPP 1.6J flows.

Potential future improvements:
- Add more scenario definitions
- Expand CMS support for additional OCPP operations
- Add automated tests
- Provide Docker images for CP + CMS

## License

This project is for personal learning and experimentation.
Feel free to fork and adapt it. A formal license can be added later.