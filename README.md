# VALORANT Instalocker & Name Revealer

A VALORANT instalocker with hidden name revealer - automatically lock agents and reveal player names in your matches.

## ⚠️ WARNING - READ THIS FIRST

**Instalocking is a bannable offense. You likely won't get banned unless you go around telling everyone you have an auto-locker. I wouldn't recommend keeping it running for long periods of time because it sends API requests instead of listening to the websocket. This is a very small project for educational purposes so I won't provide features like failsafes, that is up to you. Even if Riot detects this (through .exe blacklisting or pregame request measurement), you will likely only receive a 7 day ban for API abuse. That's still unlikely to occur and hasn't happened yet.**

> **Important:** With all programs like this, there is no guarantee that it's safe because using the VALORANT API in this manner is against Riot's Terms of Service. However, this program does not use an autoclicker to select the agent, read the game's memory, or change the game's files; therefore, the anticheat shouldn't be triggered. No suspensions have been reported so far from using this method of exploit.

**Use at your own risk. The developers are not responsible for any bans or consequences resulting from the use of this software.**

## 🎯 What This Script Can Do

This script provides 5 main features:

1. **🔒 Instalock** - Automatically lock your preferred agent instantly when entering agent select
2. **○ Prelock** - Automatically select (but don't lock) your preferred agent, allowing you to lock manually
3. **⚔️ Show Side** - Display which side you're on (Attackers or Defenders) in the pre-game lobby
4. **👥 Reveal Player Names** - Show all player names in your game (both your team and enemy team)
5. **🎨 Party Detection** - See which players are grouped together in parties (color-coded by party)

## 🎡 Features

* **Auto-Lock**: Automatically instalocks your preferred agent when entering agent select
* **Auto-Lightlock**: Automatically prelocks (selects but doesn't lock) your preferred agent
* **Hidden Name Revealer**: Reveals all player names in your game (both your team and enemy team) - even before they're visible in-game
* **Party Detection**: Shows which players are grouped together in parties with color-coded indicators
* **Map-Specific Agents**: Configure different agents for different maps
* **Manual Region Configuration**: Set your region manually in config.json (required)
* **Pre-Game Info**: Displays map, side (Attackers/Defenders), and team names
* **In-Game Info**: Automatically displays all players with their agents and teams
* **Fast Auto-Lock**: Optimized for instant agent locking (no delays)
* **Clean UI**: Beautiful formatted boxes for all information (no console log spam)
* Works separately from the game through the VALORANT API using valclient
* Clean console-based UI with formatted match information

## 📩 Installation

1. **Install Python 3.8+** if you haven't already

2. **Clone or download this repository**

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv valorant_env
   ```

4. **Activate the virtual environment**:
   - **Windows**: `valorant_env\Scripts\activate`
   - **Linux/Mac**: `source valorant_env/bin/activate`

5. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ❔ How to Use

### Basic Setup

1. **Start VALORANT** and make sure you're logged in (main menu visible)

2. **Configure your settings** in `config.json` (see Configuration section below)

3. **Run the script**:
   ```bash
   python valorant_match_info_auto.py
   ```

4. **Wait for a match** - The script will automatically:
   - Display your username and region in a startup box
   - When entering agent select: Show map, side, and team names
   - Auto-lock or prelock your agent instantly if configured (with confirmation box)
   - When entering the game: Show all players with their agents and teams
   - Display party information with color-coded indicators

### Configuration

Edit `config.json` to configure the tracker. Here's what each option does:

#### Setting Your Region

**⚠️ REQUIRED: You MUST set your region in config.json**

Auto-detection is not reliable, so you need to manually set your region:

```json
{
  "region": "eu"
}
```

**Available regions:**
- `"na"` - North America
- `"eu"` - Europe
- `"latam"` - Latin America
- `"br"` - Brazil
- `"ap"` - Asia Pacific
- `"kr"` - Korea

**Important:** If you don't set the region, the script will not start and show an error message.

#### Setting Up Auto-Lock

**Enable Auto-Lock:**
```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett"
}
```
This will automatically instalock the agent when entering agent select.

**Enable Auto-Lightlock (Prelock):**
```json
{
  "autolock": false,
  "autolightlock": true,
  "preferred_agent": "jett"
}
```
This will automatically select (but not lock) the agent - you can lock it manually in-game.

#### Adding Agents Per Map

You can set different agents for different maps. **Map-specific agents take priority over `preferred_agent`.**

**Priority order:**
1. **Map-specific agent** (if set in `agents_per_map` and not `null`) → **This is used first**
2. **Preferred agent** (fallback if map-specific is `null` or not set)

**Example: Map-specific takes priority**
```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett",
  "agents_per_map": {
    "ascent": "reyna"
  }
}
```
On Ascent, it will pick **Reyna** (not Jett), because the map-specific agent takes priority. On all other maps, it will use **Jett** (the preferred agent).

**Example: Different agent for each map**
```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett",
  "agents_per_map": {
    "ascent": "jett",
    "bind": "sova",
    "breeze": "viper",
    "fracture": "breach",
    "haven": "brimstone",
    "icebox": "sage",
    "lotus": "omen",
    "pearl": "astra",
    "split": "raze",
    "sunset": "gekko",
    "abyss": "clove",
    "corrode": null,
    "district": null,
    "kasbah": null,
    "piazza": null,
    "drift": null,
    "glitch": null,
    "skirmish": null
  }
}
```

**How it works:**
- **Map-specific agents take priority**: If a map is set to an agent name (lowercase), that agent will be used for that map (even if `preferred_agent` is set)
- **Fallback to preferred agent**: If a map is set to `null` or not specified, the `preferred_agent` will be used
- Map names must be in **lowercase**: `"ascent"`, `"bind"`, `"haven"`, `"split"`, `"icebox"`, `"breeze"`, `"fracture"`, `"pearl"`, `"lotus"`, `"sunset"`, `"abyss"`, `"corrode"`, `"district"`, `"kasbah"`, `"piazza"`, `"drift"`, `"glitch"`, `"skirmish"`

**Example: Jett on Ascent, Sova on Bind, Jett everywhere else**
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
    "haven": null,
    "icebox": null,
    "lotus": null,
    "pearl": null,
    "split": null,
    "sunset": null,
    "abyss": null,
    "corrode": null,
    "district": null,
    "kasbah": null,
    "piazza": null,
    "drift": null,
    "glitch": null,
    "skirmish": null
  }
}
```

#### Other Settings

- **`check_interval`**: How often to check for game state changes (in seconds, default: 5). Lower values = faster detection but more API requests.

### Complete Configuration Example

```json
{
  "autolock": true,
  "autolightlock": false,
  "preferred_agent": "jett",
  "agents_per_map": {
    "ascent": "jett",
    "bind": "sova",
    "breeze": "viper",
    "fracture": null,
    "haven": "brimstone",
    "icebox": "sage",
    "lotus": null,
    "pearl": null,
    "split": "raze",
    "sunset": null,
    "abyss": null,
    "corrode": null,
    "district": null,
    "kasbah": null,
    "piazza": null,
    "drift": null,
    "glitch": null,
    "skirmish": null
  },
  "check_interval": 5,
  "region": "eu"
}
```

## ❌ Troubleshooting

### "Unable to activate; is VALORANT running?"

- Make sure Valorant is **fully started** (main menu visible)
- Wait a few seconds after starting Valorant before running the script
- Try restarting Valorant
- Make sure you're **logged into Valorant** (not just the launcher)

### "Local API port not accessible"

- Valorant might still be starting up
- Wait a bit longer and try again
- Make sure Valorant is running (not just the launcher)

### Auto-lock not working

- Make sure `autolock` or `autolightlock` is set to `true` in `config.json`
- Make sure `preferred_agent` is set to a valid agent name (lowercase)
- Check that the agent name is spelled correctly (e.g., `"jett"`, `"sova"`, `"brimstone"`)
- Check the log file `valorant_tracker.log` for errors
- Make sure you're in agent select (pre-game)

### Agent names not showing

- This is normal if players haven't fully loaded yet
- The script will retry automatically
- Some API calls may take a moment

### Region configuration issues

- **You MUST set your region manually in `config.json`** - auto-detection is not supported
- Make sure the region code is correct: `"na"` (North America), `"latam"` (Latin America), `"br"` (Brazil), `"eu"` (Europe), `"kr"` (Korea), `"ap"` (Asia Pacific)
- If the region is not set or invalid, the script will exit with an error message

## ❓ Can I Get Banned?

**Instalocking is a bannable offense.** You likely won't get banned unless you go around telling everyone you have an auto-locker. I wouldn't recommend keeping it running for long periods of time because it sends API requests instead of listening to the websocket. This is a very small project for educational purposes so I won't provide features like failsafes, that is up to you. Even if Riot detects this (through .exe blacklisting or pregame request measurement), you will likely only receive a 7 day ban for API abuse. That's still unlikely to occur and hasn't happened yet.

> **Important:** With all programs like this, there is no guarantee that it's safe because using the VALORANT API in this manner is against Riot's Terms of Service. However, this program does not use an autoclicker to select the agent, read the game's memory, or change the game's files; therefore, the anticheat shouldn't be triggered. No suspensions have been reported so far from using this method of exploit.

**Use at your own risk.**

## 🤷‍♀️ Support / Feedback

* Check the log file `valorant_tracker.log` for detailed error messages
* Make sure your `config.json` is valid JSON (use a JSON validator if needed)
* Ensure all agent names are in lowercase
* Make sure Valorant is fully running and you're logged in before starting the script

## 📰 Credits

* Uses [valclient](https://github.com/colinhartigan/valclient.py) for Valorant API interaction
* Agent and map data from [valorant-api.com](https://valorant-api.com)
* Inspired by similar Valorant API projects

## Legal

This is not affiliated with Riot Games. If you are a representative of Riot and wish to have this repository taken down, please reach out via the repository issues.

## About

A VALORANT instalocker with hidden name revealer - automatically lock agents and reveal player names in your matches. This tool is provided as-is for educational purposes only.

### Notes

* I do not plan on developing this further extensively, but I will maintain the code and update agents - this will continue to work.
* I am also not responsible for **misuse** of this application, I do not condone using this and this only exists as an educational resource.
* This project uses the VALORANT API in a way that may violate Riot's Terms of Service. Use at your own risk.
