VALORANT Game-State & Automation Companion
A Python-based utility designed to interface with the local VALORANT
API. This project serves as a technical exploration into real-time
game-state monitoring, automated request handling, and the visualization
of live match metadata.
---
🚀 Technical Highlights
Local API Integration: Leverages the `valclient` library to
securely communicate with the Riot Client's local webserver via
HTTPS requests.
Dynamic State Management: Implements a continuous polling
architecture to track and react to transitions between the Main
Menu, Agent Selection, and Active Gameplay.
Config-Driven Architecture: Features a robust `config.json`
system, allowing users to define complex logic (like map-specific
overrides) without modifying the core source code.
Data Parsing & Visualization: Processes nested JSON structures
from API responses to extract and display real-time player data,
party compositions, and match details in a structured CLI.
---
🛠️ Features
Automated Agent Selection: Configurable "Instalock" and
"Prelock" systems based on user-defined priority.
Match Intelligence: Identifies and reveals player names and
pre-made parties using color-coded console output.
Map-Specific Logic: Supports unique agent configurations per map
(e.g., automatically selecting Sova on Ascent but Jett on
Abyss).
Region-Specific Routing: Manual region configuration ensures
high compatibility across different global shards (NA, EU, AP,
etc.).
Error Handling: Built-in checks for client connectivity, local
port accessibility, and API state validation.
---
📥 Installation
Prerequisites: Ensure you have Python 3.8+ installed.
Clone the Repository:
``` bash
git clone https://github.com/zuhlaa/Valorant-companion.git
cd Valorant-companion
```
Setup Virtual Environment (Recommended):
``` bash
python -m venv venv
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate
```
Install Dependencies:
``` bash
pip install -r requirements.txt
```
---
⚙️ Configuration
The application behavior is defined in `config.json`. You must set your
region manually for the tool to function.
Example Configuration
``` json
{
  "region": "eu",
  "autolock": true,
  "preferred\_agent": "jett",
  "agents\_per\_map": {
    "ascent": "reyna",
    "bind": "sova",
    "haven": null
  },
  "check\_interval": 5
}
```
Fields:
region: `na`, `eu`, `latam`, `br`, `ap`, or `kr`
autolock: If true, the script will instantly lock the agent
autolightlock: If true, the script will hover the agent but not
lock
agents_per_map: Allows for map-specific overrides. If a map is
set to null, it defaults to `preferred\_agent`
---
⚠️ Disclaimer & Educational Purpose
This project was developed as a Proof of Concept to study local API
interactions, automation workflows, and real-time data processing.
Terms of Service: Interacting with game APIs in this manner may
violate the game's Terms of Service.
Security: This software does not modify game files, inject into
game memory, or use external overlays. It operates strictly through
official client API endpoints.
Risk: The developers are not responsible for any account
consequences. Use for educational research only.
---
🤝 Credits & Resources
Core API: valclient\
Game Data: valorant-api.com\
Inspiration: Built as a study of Python-based automation and
third-party client integration.
