# Valorant Match Tracker (Auto Mode)

A Python script that automatically displays match information and can auto-lock or prelock agents in Valorant matches.

## ⚠️ WARNING

**Using auto-lock features may violate Valorant's Terms of Service and could result in a ban. Use at your own risk.**

This tool is for educational purposes only. The developers are not responsible for any consequences resulting from the use of this software.

## Features

- **Automatic Display**: Automatically shows match information without user interaction
- **Pre-Game Info**: Displays map, side (Attackers/Defenders), and team names after 2 seconds
- **In-Game Info**: Automatically displays all players with their agents and teams
- **Auto-Lock**: Automatically instalocks your preferred agent when entering agent select
- **Auto-Lightlock**: Automatically prelocks (selects but doesn't lock) your preferred agent

## Installation

1. **Install Python 3.8+** if you haven't already

2. **Clone or download this repository**

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv valorant_env
   ```

4. **Activate the virtual environment**:
   - Windows: `valorant_env\Scripts\activate`
   - Linux/Mac: `source valorant_env/bin/activate`

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.json` to configure the tracker:

```json
{
  "autolock": false,
  "autolightlock": false,
  "preferred_agent": null,
  "agents_per_map": {},
  "check_interval": 5,
  "region": null
}
```

### Configuration Options

- **`autolock`** (boolean): If `true`, automatically instalocks the agent (from `agents_per_map` or `preferred_agent`)
- **`autolightlock`** (boolean): If `true`, automatically prelocks (selects but doesn't lock) the agent (from `agents_per_map` or `preferred_agent`)
- **`preferred_agent`** (string or null): Default agent name in lowercase for all maps (e.g., `"jett"`, `"sova"`, `"brimstone"`). Used as fallback if no map-specific agent is set.
- **`agents_per_map`** (object): Map-specific agents. Keys are map names in lowercase (e.g., `"ascent"`, `"bind"`, `"haven"`), values are agent names in lowercase. If a map is not specified, `preferred_agent` is used.
- **`check_interval`** (number): How often to check for game state changes (in seconds, default: 5)
- **`region`** (string or null): Your region (`"na"`, `"eu"`, `"ap"`, `"kr"`, `"latam"`, `"br"`), or `null` for auto-detection

### Example Configuration

**Auto-lock Jett on all maps:**
```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett",
  "agents_per_map": {},
  "check_interval": 5,
  "region": null
}
```

**Auto-lock different agents per map:**
```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett",
  "agents_per_map": {
    "ascent": "jett",
    "bind": "sova",
    "breeze": null,
    "fracture": null,
    "haven": "brimstone",
    "icebox": "sage",
    "lotus": null,
    "pearl": null,
    "split": "raze",
    "sunset": null,
    "abyss": null
  },
  "check_interval": 5,
  "region": null
}
```

**Auto-prelock with map-specific agents (fallback to Sova if map not specified):**
```json
{
  "autolock": false,
  "autolightlock": true,
  "preferred_agent": "sova",
  "agents_per_map": {
    "ascent": "jett",
    "bind": "sova",
    "breeze": null,
    "fracture": null,
    "haven": null,
    "icebox": null,
    "lotus": null,
    "pearl": null,
    "split": null,
    "sunset": null,
    "abyss": null
  },
  "check_interval": 5,
  "region": "eu"
}
```

**Note:** 
- All maps are already listed in `agents_per_map` with `null` values
- Simply replace `null` with the agent name (lowercase) for the maps you want
- Map names are case-insensitive, but use lowercase: `"ascent"`, `"bind"`, `"haven"`, `"split"`, `"icebox"`, `"breeze"`, `"fracture"`, `"pearl"`, `"lotus"`, `"sunset"`, `"abyss"`, `"corrode"`, `"district"`, `"kasbah"`, `"piazza"`, `"drift"`, `"glitch"`, `"skirmish"`
- If a map is set to `null`, the `preferred_agent` will be used as fallback

## Usage

1. **Make sure Valorant is running** and you're logged in

2. **Run the script**:
   ```bash
   python valorant_match_info_auto.py
   ```

3. **Wait for a match** - The script will automatically:
   - When entering agent select: Show map, side, and team names (after 2 seconds)
   - Auto-lock or prelock your agent if configured
   - When entering the game: Show all players with their agents and teams

## How It Works

### Pre-Game (Agent Select)

1. **Immediately shows**:
   - Map name
   - Side (Attackers or Defenders)

2. **After 2 seconds**:
   - Shows all player names in your team
   - Shows agent selections and lock status

3. **Auto-lock/lightlock** (if enabled):
   - Automatically locks or prelocks your preferred agent

### In-Game

- **Automatically displays**:
  - All players in the match
  - Their selected agents
  - Their team (Blue or Red)

## Troubleshooting

### "Unable to activate; is VALORANT running?"

- Make sure Valorant is **fully started** (main menu visible)
- Wait a few seconds after starting Valorant before running the script
- Try restarting Valorant

### "Local API port not accessible"

- Valorant might still be starting up
- Wait a bit longer and try again
- Make sure Valorant is running (not just the launcher)

### Agent names not showing

- This is normal if players haven't fully loaded yet
- The script will retry automatically
- Some API calls may take a moment

### Auto-lock not working

- Make sure `autolock` or `autolightlock` is set to `true` in `config.json`
- Make sure `preferred_agent` is set to a valid agent name (lowercase)
- Check the log file `valorant_tracker.log` for errors

## Disclaimer

This tool is provided as-is for educational purposes. Using auto-lock features may violate Valorant's Terms of Service. Use at your own risk. The developers are not responsible for any bans or consequences resulting from the use of this software.

## Credits

- Uses [valclient](https://github.com/colinhartigan/valclient.py) for Valorant API interaction
- Agent and map data from [valorant-api.com](https://valorant-api.com)

## License

This project is provided as-is without any warranty.
