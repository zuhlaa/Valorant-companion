# VALORANT Game-State & Automation Companion

A Python-based utility designed to interface with the local VALORANT API. This project explores real-time game-state monitoring, automated request handling, and visualization of live match metadata.

---

## 🚀 Technical Highlights

- **Local API Integration:** Uses `valclient` to securely communicate with the Riot Client’s local HTTPS API
- **Dynamic State Management:** Continuous polling system tracking transitions between menu, agent select, and gameplay
- **Config-Driven Architecture:** `config.json` enables flexible logic without modifying source code
- **Data Parsing & Visualization:** Extracts and formats nested JSON data into structured CLI output

---

## 🛠️ Features

- **Automated Agent Selection:** Configurable instalock and prelock behavior
- **Match Intelligence:** Detects player names and parties with color-coded output
- **Map-Specific Logic:** Per-map agent overrides (e.g. Sova on Ascent, Jett on Abyss)
- **Region Routing:** Manual shard selection (NA, EU, AP, etc.)
- **Error Handling:** Validates client connection, ports, and API state

---

## 📥 Installation

### 1. Prerequisites
- Python 3.8+

### 2. Clone Repository
```bash
git clone https://github.com/zuhlaa/Valorant-companion.git
cd Valorant-companion
```

### 3. Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate


### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

The application is controlled via `config.json`.

### Example
```json
{
  "region": "eu",
  "autolock": true,
  "preferred_agent": "jett",
  "agents_per_map": {
    "ascent": "reyna",
    "bind": "sova",
    "haven": null
  },
  "check_interval": 5
}
```

### Fields

| Field            | Description |
|------------------|------------|
| `region`         | `na`, `eu`, `latam`, `br`, `ap`, `kr` |
| `autolock`       | Instantly locks agent |
| `autolightlock`  | Hovers agent without locking |
| `agents_per_map` | Map-specific overrides |
| `check_interval` | Polling interval (seconds) |

---

## ⚠️ Disclaimer

This project is a proof of concept for studying:
- Local API interaction
- Automation workflows
- Real-time data processing

**Terms of Service:** May violate Riot's ToS  
**Security:** No memory injection or file modification  
**Risk:** Use at your own discretion  

---

## 🤝 Credits

- **valclient**
- **valorant-api.com**

Built as a technical exploration of Python automation and client integration.
