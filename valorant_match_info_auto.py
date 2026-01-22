import json
import requests
import time
import os
import logging
import socket
import threading
from datetime import datetime
from valclient.client import Client
from valclient.exceptions import ResponseError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('valorant_tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Separate file-only logger for frequent errors (to avoid console spam)
file_only_logger = logging.getLogger('file_only')
file_only_logger.setLevel(logging.ERROR)
file_handler = logging.FileHandler('valorant_tracker.log')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
file_only_logger.addHandler(file_handler)
file_only_logger.propagate = False  # Don't propagate to root logger

# Fetch agent and map data from public API
def fetch_api_data():
    """Fetch agent and map data from valorant-api.com"""
    try:
        agents_response = requests.get("https://valorant-api.com/v1/agents", timeout=10)
        if agents_response.status_code != 200:
            logger.error("Error fetching agent data from valorant-api.com")
            return None, None
        
        maps_response = requests.get("https://valorant-api.com/v1/maps", timeout=10)
        maps_data = maps_response.json()['data'] if maps_response.status_code == 200 else []
        
        agents_json = agents_response.json()['data']
        
        # Create name -> uuid mapping for locking
        agent_dict = {}
        # Create uuid -> display name mapping for display
        agent_uuid_to_name = {}
        
        for agent in agents_json:
            if agent.get('isPlayableCharacter', False):
                agent_dict[agent['displayName'].lower()] = agent['uuid']
                agent_uuid_to_name[agent['uuid']] = agent['displayName']
        
        # Create map uuid -> name mapping
        map_uuid_to_name = {}
        for map_data in maps_data:
            map_uuid_to_name[map_data['uuid']] = map_data['displayName']
        
        logger.info(f"Loaded {len(agent_dict)} agents and {len(map_uuid_to_name)} maps")
        return agent_dict, agent_uuid_to_name, map_uuid_to_name
    except Exception as e:
        logger.error(f"Error fetching API data: {e}")
        return None, None, None

agent_dict, agent_uuid_to_name, map_uuid_to_name = fetch_api_data()
if not agent_dict:
    logger.error("Failed to load agent data. Exiting.")
    exit(1)

def load_config():
    """Load configuration from config.json"""
    config_file = "config.json"
    default_config = {
        "autolock": False,
        "autolightlock": False,
        "preferred_agent": None,
        "agents_per_map": {},  # Map-specific agents, e.g. {"ascent": "jett", "bind": "sova"}
        "check_interval": 5,
        "region": None  # None = auto-detect, or specify: "na", "eu", "ap", "kr", "latam", "br"
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Error reading config: {e}. Using defaults.")
    else:
        # Create default config file
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config file: {config_file}")
        except Exception as e:
            logger.error(f"Error creating config file: {e}")
    
    return default_config

# Helper function to check if local API port is open
def check_local_api_port(port=63147):
    """Check if Valorant local API port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

# Load config first to get region preference
config = load_config()
preferred_region = config.get('region')

# Initialize client with region detection
print("Initializing Valorant client connection...")
print("   Checking if Valorant client is running...")

# Quick check if local API might be accessible
if not check_local_api_port():
    print("   ⚠ Local API port not accessible. Valorant might not be running or ready.")
    print("   Continuing anyway...")

client = None
try:
    # Use preferred region from config, or default to "na"
    initial_region = preferred_region if preferred_region else "na"
    if preferred_region:
        print(f"   Using region from config: {preferred_region}")
    else:
        print(f"   Using default region: {initial_region} (will auto-detect if possible)")
    
    # Try to create client - this should be fast
    print("   Creating client instance...")
    client = Client(region=initial_region)
    
    # Try to activate with timeout to prevent hanging
    print("   Activating client connection...")
    print("   (This may take a few seconds if Valorant just started)...")
    
    activation_success = [False]
    activation_error = [None]
    
    def try_activate():
        try:
            client.activate()
            activation_success[0] = True
        except Exception as e:
            activation_error[0] = e
    
    # Run activate in a thread with timeout
    activate_thread = threading.Thread(target=try_activate, daemon=True)
    activate_thread.start()
    activate_thread.join(timeout=10)  # Wait max 10 seconds
    
    if activate_thread.is_alive():
        print("\n✗ Client activation timed out after 10 seconds")
        print("\n⚠ The Valorant client API is not responding.")
        print("   This usually means:")
        print("   - Valorant is still starting up (wait a bit longer)")
        print("   - Valorant client API is not accessible")
        print("   - Try restarting Valorant and wait for it to fully load")
        print("\n   Please make sure Valorant is fully started before running the script.\n")
        exit(1)
    
    if activation_error[0]:
        error_msg = str(activation_error[0]).lower()
        print(f"\n✗ Failed to activate client: {activation_error[0]}")
        print("\n⚠ Troubleshooting:")
        
        if "unable to activate" in error_msg or "valorant" in error_msg:
            print("   - Valorant client is not running or not ready")
            print("   - Make sure Valorant is FULLY started (wait for main menu)")
            print("   - Wait for the Valorant client to fully load before running the script")
        elif "connection" in error_msg or "refused" in error_msg:
            print("   - Cannot connect to Valorant client API")
            print("   - Try restarting Valorant")
            print("   - Check if firewall/antivirus is blocking the connection")
        else:
            print("   - Make sure Valorant is running and fully loaded")
            print("   - Try restarting Valorant and running the script again")
        
        print("\n   The script needs the Valorant client to be running and accessible.")
        print("   Make sure Valorant is fully started (main menu visible).\n")
        exit(1)
    
    if activation_success[0]:
        print("✓ Client activated")

    # Detect region and verify login
    try:
        print("   Detecting region...")
        local = client.fetch(endpoint="/riotclient/region-locale", endpoint_type="local")
        api_region = local.get('region', local.get('affinity', '')).lower()
        
        # Try to get user info to verify login
        try:
            print("   Verifying login...")
            user_info = client.fetch(endpoint="/chat/v1/session", endpoint_type="local")
            if user_info:
                username = user_info.get('game_name', 'Unknown')
                tag = user_info.get('game_tag', '')
                print(f"✓ Connected as: {username}#{tag}")
        except Exception as login_error:
            print(f"⚠ Could not verify login: {login_error}")
            print("   Make sure you're logged into Valorant.")
        
        region_mapping = {
            'na': 'na',
            'eu': 'eu',
            'latam': 'latam',
            'br': 'br',
            'ap': 'ap',
            'kr': 'kr',
        }
        
        # Use detected region unless user specified one in config
        if preferred_region:
            # User specified region in config, use that
            if preferred_region.lower() in region_mapping:
                final_region = preferred_region.lower()
                print(f"   Using region from config: {final_region}")
            else:
                print(f"⚠ Invalid region in config: {preferred_region}")
                print(f"   Using detected region: {api_region}")
                final_region = region_mapping.get(api_region, 'na')
        else:
            # Auto-detect region
            if api_region in region_mapping:
                final_region = region_mapping[api_region]
                print(f"   Auto-detected region: {final_region}")
            else:
                print(f"⚠ Unknown region: {api_region}. Using default 'na'.")
                final_region = 'na'
        
        # Only recreate client if region changed
        if final_region != initial_region:
            print(f"   Switching to region: {final_region}")
            client = Client(region=final_region)
            client.activate()
        
        print(f"✓ Region: {final_region}")
    except Exception as region_error:
        print(f"⚠ Could not detect region: {region_error}")
        print("   Continuing with default region 'na'...")
        
except KeyboardInterrupt:
    print("\n\nInterrupted by user. Exiting...")
    exit(0)
except Exception as e:
    print(f"\n✗ Error initializing client: {type(e).__name__}: {e}")
    print("\n⚠ IMPORTANT: Make sure:")
    print("   1. Valorant is running (the game client, not just the launcher)")
    print("   2. You are LOGGED INTO Valorant")
    print("   3. The Valorant client is fully loaded")
    print("\n   The script needs access to the Valorant client API.")
    print("   If Valorant is running but this still fails, try:")
    print("   - Restarting Valorant")
    print("   - Running the script as administrator")
    print("   - Checking if antivirus/firewall is blocking the connection\n")
    exit(1)

def get_puuids_from_match(match_data, is_pre_game=True):
    puuids = []
    if is_pre_game:
        if 'AllyTeam' in match_data and match_data['AllyTeam']:
            if 'Players' in match_data['AllyTeam']:
                for player in match_data['AllyTeam']['Players']:
                    if 'Subject' in player:
                        puuids.append(player['Subject'])
        if 'EnemyTeam' in match_data and match_data['EnemyTeam']:
            if 'Players' in match_data['EnemyTeam']:
                for player in match_data['EnemyTeam']['Players']:
                    if 'Subject' in player:
                        puuids.append(player['Subject'])
    else:
        if 'Players' in match_data:
            for player in match_data['Players']:
                if 'Subject' in player:
                    puuids.append(player['Subject'])
    logger.debug(f"Extracted {len(puuids)} PUUIDs from match data")
    return puuids

def get_player_names(puuids):
    if not puuids:
        logger.warning("No PUUIDs provided to get_player_names")
        return {}
    
    # Try different methods to get player names
    # Method 1: Direct PUT request (standard valclient method)
    try:
        logger.debug(f"Fetching names for {len(puuids)} players using PUT method")
        # Try with list of PUUIDs as json_data parameter
        # Use exceptions parameter to handle non-200 status codes gracefully
        response = client.put("/name-service/v2/players", json_data=puuids, exceptions={404: None, 400: None, 500: None})
        
        # Check if response is an error object
        if isinstance(response, dict):
            if 'httpStatus' in response or 'errorCode' in response:
                error_msg = response.get('message', 'Unknown error')
                logger.warning(f"Name service returned error: {error_msg}")
                # Continue to try alternative
            elif 'Subject' in response and 'GameName' in response:
                # Single player response
                return {response['Subject']: f"{response['GameName']}#{response.get('TagLine', '')}"}
        
        if isinstance(response, list):
            name_map = {}
            for entry in response:
                if isinstance(entry, dict) and 'Subject' in entry and 'GameName' in entry:
                    name_map[entry['Subject']] = f"{entry['GameName']}#{entry.get('TagLine', '')}"
            
            if name_map:
                logger.debug(f"Successfully fetched {len(name_map)} player names")
                return name_map
    except Exception as e:
        error_str = str(e).lower()
        if "json decode" in error_str or "json" in error_str:
            logger.warning(f"PUT method failed with JSON decode error - API might be returning empty/non-JSON response: {e}")
            # The API might be returning an empty response or HTML error page
            # This can happen if the endpoint is not available or requires different authentication
        else:
            logger.warning(f"PUT method failed: {e}")
    
    # Method 2: Try using PUT with local endpoint type
    try:
        logger.debug("Trying PUT with local endpoint type...")
        # Try local endpoint instead of pd
        response = client.put("/name-service/v2/players", endpoint_type="local", json_data=puuids)
        if isinstance(response, list):
            name_map = {}
            for entry in response:
                if isinstance(entry, dict) and 'Subject' in entry and 'GameName' in entry:
                    name_map[entry['Subject']] = f"{entry['GameName']}#{entry.get('TagLine', '')}"
            if name_map:
                logger.debug(f"Successfully fetched {len(name_map)} player names using local fetch method")
                return name_map
    except Exception as e:
        logger.warning(f"Local fetch method failed: {e}")
    
    # Method 3: Try direct requests call to see raw response (bypass valclient JSON parsing)
    try:
        logger.debug("Trying direct requests call to bypass valclient JSON parsing...")
        # Get base URL and headers from client
        base_url = client.base_url if hasattr(client, 'base_url') else f"https://pd.{client.region}.a.pvp.net"
        headers = client.headers if hasattr(client, 'headers') else {}
        
        # Make direct PUT request
        url = f"{base_url}/name-service/v2/players"
        response = requests.put(url, headers=headers, json=puuids, timeout=5)
        
        # Check if response is valid
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    name_map = {}
                    for entry in data:
                        if isinstance(entry, dict) and 'Subject' in entry and 'GameName' in entry:
                            name_map[entry['Subject']] = f"{entry['GameName']}#{entry.get('TagLine', '')}"
                    if name_map:
                        logger.debug(f"Successfully fetched {len(name_map)} player names using direct requests")
                        return name_map
            except json.JSONDecodeError as json_err:
                logger.warning(f"Response is not valid JSON. Status: {response.status_code}")
                logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
        else:
            logger.warning(f"Direct request returned status {response.status_code}")
            logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
    except Exception as e:
        logger.warning(f"Direct requests method failed: {e}")
    
    # Method 4: Try fetching names one by one (slower but might work)
    logger.info(f"All batch methods failed, trying individual requests for {len(puuids)} players...")
    name_map = {}
    for puuid in puuids:  # Try all players (no limit)
        try:
            response = client.put("/name-service/v2/players", json_data=[puuid], exceptions={404: None, 400: None, 500: None})
            if isinstance(response, list) and len(response) > 0:
                entry = response[0]
                if isinstance(entry, dict) and 'Subject' in entry and 'GameName' in entry:
                    name_map[entry['Subject']] = f"{entry['GameName']}#{entry.get('TagLine', '')}"
            elif isinstance(response, dict) and 'Subject' in response and 'GameName' in response:
                name_map[response['Subject']] = f"{response['GameName']}#{response.get('TagLine', '')}"
            time.sleep(0.2)  # Small delay between requests
        except Exception as e:
            logger.debug(f"Failed to get name for individual PUUID {puuid[:8]}...: {e}")
            continue
    
    if name_map:
        logger.info(f"Successfully fetched {len(name_map)} player names using individual requests")
        return name_map
    
    logger.error(f"All methods failed to fetch player names for {len(puuids)} players")
    return {}

def get_agent_name(uuid):
    """Convert agent UUID to display name"""
    if not uuid:
        return "Not Selected"
    return agent_uuid_to_name.get(uuid, uuid[:8] + "...")

def get_map_name(map_id):
    """Convert map UUID to display name"""
    if not map_id:
        return "Unknown"
    
    # First try to get from map dictionary
    if map_id in map_uuid_to_name:
        return map_uuid_to_name[map_id]
    
    # If it's a path-like string (e.g., "/Game/Maps/Ascent/Ascent"), extract the map name
    if "/" in map_id:
        # Extract the last part before the final slash, or the last part if it's repeated
        parts = [p for p in map_id.split("/") if p and p != "Game" and p != "Maps"]
        if parts:
            # Return the last meaningful part (usually the map name)
            return parts[-1]
    
    # Fallback: show first 8 chars if it's a UUID
    return map_id[:8] + "..."

def get_agent_for_map(map_name, config):
    """Get the agent to use for a specific map, or fallback to preferred_agent"""
    if not map_name or map_name == "Unknown":
        # If map is unknown, use preferred_agent
        return config.get('preferred_agent')
    
    # Normalize map name to lowercase for lookup
    map_name_lower = map_name.lower()
    
    # Check if there's a map-specific agent
    agents_per_map = config.get('agents_per_map', {})
    if agents_per_map and map_name_lower in agents_per_map:
        agent = agents_per_map[map_name_lower]
        if agent:  # Make sure it's not None or empty
            return agent.lower().strip()
    
    # Fallback to preferred_agent for all maps
    return config.get('preferred_agent')

def save_match_history(match_data_dict):
    """Save match information to JSON file"""
    history_file = "match_history.json"
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading match history: {e}")
    
    match_data_dict['timestamp'] = datetime.now().isoformat()
    history.append(match_data_dict)
    
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.info(f"Match saved to {history_file}")
    except Exception as e:
        logger.error(f"Error saving match history: {e}")

def print_match_info(is_pre_game=True):
    try:
        if is_pre_game:
            player_data = client.pregame_fetch_player()
            match_id = player_data['MatchID']
            match_data = client.pregame_fetch_match()
            map_id = match_data.get('MapID', '')
        else:
            player_data = client.coregame_fetch_player()
            match_id = player_data['MatchID']
            match_data = client.coregame_fetch_match()
            map_id = match_data.get('MapID', '')
    except Exception as e:
        logger.error(f"Error fetching match data: {e}")
        return

    puuids = get_puuids_from_match(match_data, is_pre_game)
    name_map = get_player_names(puuids)
    map_name = get_map_name(map_id)

    # Prepare match data for saving
    match_info = {
        'match_id': match_id,
        'map': map_name,
        'map_id': map_id,
        'is_pre_game': is_pre_game,
        'timestamp': datetime.now().isoformat()
    }

    # Format match ID (show first 8 and last 8 chars for readability)
    match_id_short = match_id if len(match_id) <= 30 else f"{match_id[:12]}...{match_id[-8:]}"
    
    # Beautiful header
    header_text = f"{'PRE-GAME' if is_pre_game else 'IN-GAME'} MATCH INFO"
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + header_text.center(58) + "║")
    print("╠" + "═"*58 + "╣")
    # Map name - truncate if too long but show full name if possible
    map_display = map_name if len(map_name) <= 44 else map_name[:41] + "..."
    print(f"║ {'🗺️  Map:':<12} {map_display:<44} ║")
    print(f"║ {'🆔 Match ID:':<12} {match_id_short:<44} ║")
    
    if is_pre_game:
        if 'AllyTeam' in match_data and match_data['AllyTeam']:
            side = "Attackers" if match_data['AllyTeam']['TeamID'] == "Blue" else "Defenders"
            side_icon = "⚔️" if side == "Attackers" else "🛡️"
            print(f"║ {'Side:':<12} {side_icon} {side:<41} ║")
    print("╠" + "═"*58 + "╣")
    
    if is_pre_game:
        if 'AllyTeam' in match_data and match_data['AllyTeam']:
            ally_count = len(match_data['AllyTeam']['Players'])
            print(f"║" + f" ✅ YOUR TEAM ({ally_count} players) ".center(58, "─") + "║")
            print("╠" + "─"*58 + "╣")
            ally_team = []
            for idx, player in enumerate(match_data['AllyTeam']['Players'], 1):
                name = name_map.get(player['Subject'], "Unknown")
                agent_name = get_agent_name(player['CharacterID'])
                locked = "🔒" if player['CharacterSelectionState'] == 'locked' else "○"
                ally_team.append({
                    'name': name,
                    'agent': agent_name,
                    'locked': player['CharacterSelectionState'] == 'locked'
                })
                print(f"║ {idx:2}. {locked} {name:<22} │ {agent_name:<20} ║")
            match_info['ally_team'] = ally_team
            print("╠" + "═"*58 + "╣")
            
        if 'EnemyTeam' in match_data and match_data['EnemyTeam']:
            enemy_count = len(match_data['EnemyTeam']['Players'])
            print(f"║" + f" ⚠️  ENEMY TEAM ({enemy_count} players) ".center(58, "─") + "║")
            print("╠" + "─"*58 + "╣")
            enemy_team = []
            for idx, player in enumerate(match_data['EnemyTeam']['Players'], 1):
                name = name_map.get(player['Subject'], "Unknown")
                agent_name = get_agent_name(player['CharacterID'])
                locked = "🔒" if player['CharacterSelectionState'] == 'locked' else "○"
                enemy_team.append({
                    'name': name,
                    'agent': agent_name,
                    'locked': player['CharacterSelectionState'] == 'locked'
                })
                print(f"║ {idx:2}. {locked} {name:<22} │ {agent_name:<20} ║")
            match_info['enemy_team'] = enemy_team
            print("╠" + "═"*58 + "╣")
    else:
        print("║" + " ALL PLAYERS ".center(58, "─") + "║")
        print("╠" + "═"*58 + "╣")
        players_by_team = {'Blue': [], 'Red': []}
        for player in match_data['Players']:
            name = name_map.get(player['Subject'], "Unknown")
            agent_name = get_agent_name(player['CharacterID'])
            team = player['TeamID']
            players_by_team[team].append({
                'name': name,
                'agent': agent_name,
                'team': team
            })
        
        # Group by team for better display with consistent formatting
        for team_idx, team_id in enumerate(sorted(players_by_team.keys())):
            if players_by_team[team_id]:
                team_color = "🔵" if team_id == "Blue" else "🔴" if team_id == "Red" else "⚪"
                print(f"║" + f" {team_color} TEAM {team_id} ({len(players_by_team[team_id])} players) ".center(58, "─") + "║")
                print("╠" + "─"*58 + "╣")
                for idx, player_data in enumerate(players_by_team[team_id], 1):
                    print(f"║ {idx:2}. {player_data['name']:<24} │ {player_data['agent']:<20} ║")
                if team_idx < len(players_by_team) - 1:
                    print("╠" + "─"*58 + "╣")
        match_info['players'] = players_by_team
        print("╠" + "═"*58 + "╣")
    
    print("╚" + "═"*58 + "╝\n")
    
    # Save match info
    save_match_history(match_info)

def lock_agent(agent_name):
    """Lock an agent (select and lock)"""
    uuid = agent_dict.get(agent_name)
    if not uuid:
        logger.warning(f"Invalid agent name: {agent_name}")
        return False
    
    try:
        # First select the character
        client.pregame_select_character(uuid)
        time.sleep(0.2)  # Small delay to ensure selection is processed
        
        # Then lock it
        client.pregame_lock_character(uuid)
        time.sleep(0.1)  # Small delay after locking
        
        display_name = agent_uuid_to_name.get(uuid, agent_name.capitalize())
        logger.info(f"Locked {display_name} successfully.")
        return True
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Error locking agent: {e}")
        
        # Check if agent is already locked/selected
        if "already" in error_str or "selected" in error_str or "locked" in error_str:
            display_name = agent_uuid_to_name.get(uuid, agent_name.capitalize())
            logger.info(f"Agent {display_name} already locked/selected.")
            return True
        
        return False

def prelock_agent(agent_name):
    """Prelock an agent (select but don't lock)"""
    uuid = agent_dict.get(agent_name)
    if not uuid:
        logger.warning(f"Invalid agent name: {agent_name}")
        return False
    
    try:
        # Only select the character, don't lock
        client.pregame_select_character(uuid)
        time.sleep(0.1)  # Small delay after selecting
        
        display_name = agent_uuid_to_name.get(uuid, agent_name.capitalize())
        logger.info(f"Prelocked {display_name} successfully.")
        return True
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Error prelocking agent: {e}")
        
        # Check if agent is already selected
        if "already" in error_str or "selected" in error_str:
            display_name = agent_uuid_to_name.get(uuid, agent_name.capitalize())
            logger.info(f"Agent {display_name} already selected.")
            return True
        
        return False

def show_agent_selection(header="AVAILABLE AGENTS"):
    """Show numbered list of agents for selection"""
    sorted_agents = sorted(agent_dict.keys())
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + f" {header} ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    
    # Display agents in 2 columns for better layout
    agents_per_column = (len(sorted_agents) + 1) // 2
    for i in range(agents_per_column):
        left_idx = i + 1
        right_idx = i + agents_per_column + 1
        
        if left_idx <= len(sorted_agents):
            left_agent = sorted_agents[left_idx - 1]
            left_display = agent_uuid_to_name.get(agent_dict[left_agent], left_agent.capitalize())
            left_str = f"{left_idx:2}. {left_display:<20}"
        else:
            left_str = " " * 28
        
        if right_idx <= len(sorted_agents):
            right_agent = sorted_agents[right_idx - 1]
            right_display = agent_uuid_to_name.get(agent_dict[right_agent], right_agent.capitalize())
            right_str = f"{right_idx:2}. {right_display:<20}"
        else:
            right_str = " " * 28
        
        print(f"║ {left_str} │ {right_str} ║")
    
    print("╚" + "═"*58 + "╝")
    return sorted_agents

def select_agent_by_number(show_header="AVAILABLE AGENTS"):
    """Let user select an agent by number - FAST version"""
    sorted_agents = show_agent_selection(header=show_header)
    try:
        choice = input("\n👉 Enter agent number: ").strip()
        agent_idx = int(choice) - 1
        if 0 <= agent_idx < len(sorted_agents):
            return sorted_agents[agent_idx]
        else:
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " ❌ Invalid number ".center(58) + "║")
            print("║" + " Please try again ".center(58) + "║")
            print("╚" + "═"*58 + "╝")
            return None
    except ValueError:
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " ❌ Invalid input ".center(58) + "║")
        print("║" + " Please enter a number ".center(58) + "║")
        print("╚" + "═"*58 + "╝")
        return None

def save_config(config_data):
    """Save configuration to config.json"""
    config_file = "config.json"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        logger.info(f"Config saved to {config_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def show_names(match_data, name_map):
    """Show player names in a formatted way"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " PLAYER NAMES ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    
    total_players = 0
    if 'AllyTeam' in match_data and match_data['AllyTeam']:
        ally_count = len(match_data['AllyTeam'].get('Players', []))
        total_players += ally_count
        print(f"║" + f" YOUR TEAM ({ally_count} players) ".center(58, "─") + "║")
        print("╠" + "─"*58 + "╣")
        for idx, player in enumerate(match_data['AllyTeam']['Players'], 1):
            name = name_map.get(player.get('Subject', ''), "Unknown")
            agent_name = get_agent_name(player.get('CharacterID'))
            print(f"║ {idx:2}. {name:<25} │ {agent_name:<20} ║")
        print("╠" + "─"*58 + "╣")
    
    if 'EnemyTeam' in match_data and match_data['EnemyTeam']:
        enemy_count = len(match_data['EnemyTeam'].get('Players', []))
        total_players += enemy_count
        print(f"║" + f" ENEMY TEAM ({enemy_count} players) ".center(58, "─") + "║")
        print("╠" + "─"*58 + "╣")
        for idx, player in enumerate(match_data['EnemyTeam']['Players'], 1):
            name = name_map.get(player.get('Subject', ''), "Unknown")
            agent_name = get_agent_name(player.get('CharacterID'))
            print(f"║ {idx:2}. {name:<25} │ {agent_name:<20} ║")
        print("╠" + "─"*58 + "╣")
    
    if total_players > 0:
        print(f"║ {'Total:':<12} {total_players} players".ljust(58) + " ║")
    print("╚" + "═"*58 + "╝\n")

def show_site(match_data):
    """Show which side (Attackers/Defenders)"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " SIDE INFORMATION ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    if 'AllyTeam' in match_data and match_data['AllyTeam']:
        side = "Attackers" if match_data['AllyTeam']['TeamID'] == "Blue" else "Defenders"
        side_icon = "⚔️" if side == "Attackers" else "🛡️"
        print(f"║ {side_icon} Your Team: {side:<45} ║")
        print(f"║ {'Team ID:':<12} {match_data['AllyTeam']['TeamID']:<45} ║")
    elif 'Players' in match_data:
        # For ingame, check team from players
        for player in match_data['Players']:
            if player.get('TeamID'):
                print(f"║ {'Team ID:':<12} {player['TeamID']:<45} ║")
                break
    print("╚" + "═"*58 + "╝\n")

def show_pregame_auto(match_data, map_name):
    """Automatically display pre-game info: Map and Side immediately"""
    # Show Map and Side immediately
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " 🎮 PRE-GAME INFO ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    map_display = map_name if len(map_name) <= 44 else map_name[:41] + "..."
    print(f"║ {'🗺️  Map:':<12} {map_display:<44} ║")
    
    if 'AllyTeam' in match_data and match_data['AllyTeam']:
        side = "Attackers" if match_data['AllyTeam']['TeamID'] == "Blue" else "Defenders"
        side_icon = "⚔️" if side == "Attackers" else "🛡️"
        print(f"║ {'Side:':<12} {side_icon} {side:<41} ║")
    print("╚" + "═"*58 + "╝")
    
    # Wait 2 seconds, then show team names (will be called separately)
    print("\n⏳ Loading team names...")
    time.sleep(2)

def show_ingame_auto(match_data, name_map):
    """Automatically display in-game info: All players with agents and teams"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " 🎯 IN-GAME PLAYERS ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    
    if 'Players' in match_data:
        total_players = len(match_data['Players'])
        print(f"║ {'👥 Total Players:':<18} {total_players:<38} ║")
        print("╠" + "═"*58 + "╣")
        
        # Group by team
        teams = {}
        for player in match_data['Players']:
            team = player.get('TeamID', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(player)
        
        # Sort teams for consistent display
        for team_idx, team_id in enumerate(sorted(teams.keys())):
            players = teams[team_id]
            team_color = "🔵" if team_id == "Blue" else "🔴" if team_id == "Red" else "⚪"
            print(f"║" + f" {team_color} TEAM {team_id} ({len(players)} players) ".center(58, "─") + "║")
            print("╠" + "─"*58 + "╣")
            for idx, player in enumerate(players, 1):
                name = name_map.get(player.get('Subject', ''), "Unknown")
                agent_name = get_agent_name(player.get('CharacterID'))
                print(f"║ {idx:2}. {name:<24} │ {agent_name:<20} ║")
            if team_idx < len(teams) - 1:
                print("╠" + "─"*58 + "╣")
    else:
        print("║ ⚠️  No player data available".ljust(58) + " ║")
    print("╚" + "═"*58 + "╝\n")

def ingame_menu(match_data, name_map):
    """Interactive in-game menu"""
    while True:
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " IN-GAME MENU ".center(58) + "║")
        print("╠" + "═"*58 + "╣")
        print("║  1. 👥 Show Names                                        ║")
        print("║  2. 📊 Show Team Info                                    ║")
        print("║  0. ▶  Continue (no action)                              ║")
        print("╚" + "═"*58 + "╝")
        
        choice = input("\n👉 Enter your choice (0-2): ").strip()
        
        if choice == "1":
            # Show Names - refresh names first
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " 👥 Refreshing player names... ".center(58) + "║")
            print("╚" + "═"*58 + "╝")
            puuids = get_puuids_from_match(match_data, is_pre_game=False)
            refreshed_name_map = {}
            if not puuids:
                print("⚠️  No player PUUIDs found in match data.")
            else:
                print(f"   Found {len(puuids)} players, fetching names...")
                refreshed_name_map = get_player_names(puuids)
                if not refreshed_name_map:
                    print("⚠️  Could not fetch player names from API.")
                    print("   Trying alternative method...")
                    time.sleep(1)
                    refreshed_name_map = get_player_names(puuids)
                if refreshed_name_map:
                    print(f"✅ Successfully fetched {len(refreshed_name_map)} player names")
                else:
                    print("⚠️  Still couldn't fetch names. Showing what we have...")
            show_names_ingame(match_data, refreshed_name_map if refreshed_name_map else name_map)
        
        elif choice == "2":
            # Show Team Info
            show_team_info_ingame(match_data, name_map)
        
        elif choice == "0":
            # Continue
            break
        
        else:
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " ❌ Invalid choice ".center(58) + "║")
            print("║" + " Please enter a number between 0-2 ".center(58) + "║")
            print("╚" + "═"*58 + "╝")

def show_names_ingame(match_data, name_map):
    """Show player names in a formatted way for ingame"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " PLAYER NAMES (IN-GAME) ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    
    if 'Players' in match_data:
        total_players = len(match_data['Players'])
        print(f"║ {'👥 Total Players:':<18} {total_players:<38} ║")
        print("╠" + "═"*58 + "╣")
        
        # Group by team
        teams = {}
        for player in match_data['Players']:
            team = player.get('TeamID', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(player)
        
        # Sort teams for consistent display
        for team_idx, team_id in enumerate(sorted(teams.keys())):
            players = teams[team_id]
            team_color = "🔵" if team_id == "Blue" else "🔴" if team_id == "Red" else "⚪"
            print(f"║" + f" {team_color} TEAM {team_id} ({len(players)} players) ".center(58, "─") + "║")
            print("╠" + "─"*58 + "╣")
            for idx, player in enumerate(players, 1):
                name = name_map.get(player.get('Subject', ''), "Unknown")
                agent_name = get_agent_name(player.get('CharacterID'))
                print(f"║ {idx:2}. {name:<24} │ {agent_name:<20} ║")
            if team_idx < len(teams) - 1:
                print("╠" + "─"*58 + "╣")
    else:
        print("║ ⚠ No player data available.".ljust(58) + " ║")
    print("╚" + "═"*58 + "╝\n")

def show_team_info_ingame(match_data, name_map):
    """Show team information for ingame"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " 📊 TEAM INFORMATION ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    
    if 'Players' in match_data:
        teams = {}
        for player in match_data['Players']:
            team = player.get('TeamID', 'Unknown')
            if team not in teams:
                teams[team] = []
            teams[team].append(player)
        
        for team_idx, (team_id, players) in enumerate(sorted(teams.items())):
            team_color = "🔵" if team_id == "Blue" else "🔴" if team_id == "Red" else "⚪"
            print(f"║" + f" {team_color} TEAM {team_id} ({len(players)} players) ".center(58, "─") + "║")
            print("╠" + "─"*58 + "╣")
            for idx, player in enumerate(players, 1):
                name = name_map.get(player.get('Subject', ''), "Unknown")
                agent_name = get_agent_name(player.get('CharacterID'))
                print(f"║ {idx:2}. {name:<24} │ {agent_name:<20} ║")
            if team_idx < len(teams) - 1:
                print("╠" + "─"*58 + "╣")
    else:
        print("║ ⚠️  No player data available.".ljust(58) + " ║")
    print("╚" + "═"*58 + "╝\n")

def pregame_menu(match_data, name_map, config_ref):
    """Interactive pre-game menu"""
    global config
    
    while True:
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " PRE-GAME MENU ".center(58) + "║")
        print("╠" + "═"*58 + "╣")
        print("║  1. 🔒 Instalock (lock agent for this game)              ║")
        print("║  2. ○  Prelock (select agent, lock later)               ║")
        print("║  3. 👥 Show Names                                        ║")
        print("║  4. ⚔️ Show Site (Attackers/Defenders)                  ║")
        print("║  0. ▶  Continue (no action)                              ║")
        print("╠" + "═"*58 + "╣")
        print("║" + " Note: For permanent auto-lock, edit config.json: ".center(58) + "║")
        print("║" + " Set 'auto_lock': true and 'preferred_agent' ".center(58) + "║")
        print("╚" + "═"*58 + "╝")
        
        choice = input("\n👉 Enter your choice (0-4): ").strip()
        
        if choice == "1":
            # Instalock - lock agent for this game only (FAST - show agents immediately)
            agent_name = select_agent_by_number(show_header="🔒 INSTALOCK")
            if agent_name:
                if lock_agent(agent_name):
                    display_name = agent_uuid_to_name.get(agent_dict.get(agent_name, ''), agent_name.capitalize())
                    print(f"\n✅ Agent {display_name} locked for this game!")
        
        elif choice == "2":
            # Prelock - select agent but don't lock yet (FAST - show agents immediately)
            agent_name = select_agent_by_number(show_header="○ PRELOCK")
            if agent_name:
                uuid = agent_dict.get(agent_name)
                if uuid:
                    try:
                        client.pregame_select_character(uuid)
                        display_name = agent_uuid_to_name.get(uuid, agent_name.capitalize())
                        print(f"\n✅ Selected {display_name} (not locked yet)")
                        print("   You can lock it manually in the game.")
                    except Exception as e:
                        print(f"\n❌ Error selecting agent: {e}")
        
        elif choice == "3":
            # Show Names - refresh names first
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " 👥 Refreshing player names... ".center(58) + "║")
            print("╚" + "═"*58 + "╝")
            puuids = get_puuids_from_match(match_data, is_pre_game=True)
            refreshed_name_map = {}
            if not puuids:
                print("⚠️  No player PUUIDs found in match data.")
                print("   This might mean players haven't joined yet.")
            else:
                print(f"   Found {len(puuids)} players, fetching names...")
                refreshed_name_map = get_player_names(puuids)
                if not refreshed_name_map:
                    print("⚠️  Could not fetch player names from API.")
                    print("   This might be a temporary API issue.")
                    print("   Trying alternative method...")
                    # Try once more with delay
                    time.sleep(1)
                    refreshed_name_map = get_player_names(puuids)
                if refreshed_name_map:
                    print(f"✅ Successfully fetched {len(refreshed_name_map)} player names")
                else:
                    print("⚠️  Still couldn't fetch names. Showing what we have...")
            show_names(match_data, refreshed_name_map if refreshed_name_map else name_map)
        
        elif choice == "4":
            # Show Site
            show_site(match_data)
        
        elif choice == "0":
            # Continue
            break
        
        else:
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " ❌ Invalid choice ".center(58) + "║")
            print("║" + " Please enter a number between 0-4 ".center(58) + "║")
            print("╚" + "═"*58 + "╝")
    
    # Note: Auto-lock is now handled in the main loop before showing the menu
    # This ensures it happens immediately when entering pregame

# Config already loaded above during client initialization
check_interval = config.get('check_interval', 5)

# Main loop
logger.info("Starting Valorant Match Tracker (Auto Mode)...")
print("\n" + "╔" + "═"*58 + "╗")
print("║" + " VALORANT MATCH TRACKER (AUTO MODE) ".center(58) + "║")
print("╠" + "═"*58 + "╣")
autolock_status = "✅ Enabled" if config.get('autolock') else "❌ Disabled"
autolightlock_status = "✅ Enabled" if config.get('autolightlock') else "❌ Disabled"
print(f"║ {'Auto-lock:':<15} {autolock_status:<42} ║")
print(f"║ {'Auto-lightlock:':<15} {autolightlock_status:<42} ║")
if config.get('preferred_agent'):
    agent_display = agent_uuid_to_name.get(agent_dict.get(config.get('preferred_agent').lower(), ''), config.get('preferred_agent'))
    print(f"║ {'Preferred Agent:':<15} {agent_display:<42} ║")
print("╠" + "═"*58 + "╣")
print("║" + " Auto-display mode: Info shown automatically ".center(58) + "║")
print("║" + " Monitoring game state... Press Ctrl+C to exit. ".center(58) + "║")
print("╚" + "═"*58 + "╝\n")

# Test connection
try:
    test_session = client.session_fetch()
    if test_session is None:
        print("╔" + "═"*58 + "╗")
        print("║" + " ℹ No active session (this is normal when in menus) ".center(58) + "║")
        print("║" + " Waiting for a game to start... ".center(58) + "║")
        print("╚" + "═"*58 + "╝\n")
    else:
        state = test_session.get('loopState', 'UNKNOWN')
        print("╔" + "═"*58 + "╗")
        print("║" + f" ✅ Connected to Valorant client (State: {state}) ".center(58) + "║")
        print("╚" + "═"*58 + "╝\n")
except Exception as e:
    print("╔" + "═"*58 + "╗")
    print("║" + " ⚠️  Warning: Could not connect to Valorant client ".center(58) + "║")
    print("║" + f" {str(e)[:54]} ".center(58) + "║")
    print("║" + " Make sure Valorant is running and try again. ".center(58) + "║")
    print("╚" + "═"*58 + "╝\n")

# Exception counter for main loop (to avoid spam)
exception_counter = {'count': {}}
none_session_count = 0  # Track consecutive None sessions

last_state = None
last_pregame_match_id = None
while True:
    try:
        # Try multiple methods to detect game state
        session = None
        state = None
        
        # Method 1: Try session_fetch()
        try:
            session = client.session_fetch()
            if session and isinstance(session, dict) and 'loopState' in session:
                state = session['loopState']
        except Exception as fetch_error:
            # Don't show error yet, try alternative methods first
            file_only_logger.error(f"Error fetching session: {fetch_error}", exc_info=True)
        
        # Method 2: If session_fetch() failed or returned None, try checking pregame directly
        # Try multiple times with small delays, as pregame might not be ready immediately
        if state is None:
            for pregame_attempt in range(3):
                try:
                    player_data = client.pregame_fetch_player()
                    if player_data and isinstance(player_data, dict) and 'MatchID' in player_data:
                        state = "PREGAME"
                        match_id_short = str(player_data.get('MatchID', 'Unknown'))[:20]
                        print("\n" + "╔" + "═"*58 + "╗")
                        print("║" + " 🎮 PREGAME DETECTED ".center(58) + "║")
                        print("║" + f" Match ID: {match_id_short} ".center(58) + "║")
                        print("╚" + "═"*58 + "╝")
                        logger.info(f"Detected PREGAME via pregame_fetch_player() (attempt {pregame_attempt + 1})")
                        break
                except Exception as pregame_error:
                    # Not in pregame yet, try again with small delay or move to ingame check
                    if pregame_attempt < 2:
                        time.sleep(0.2)  # Small delay before retry
                    else:
                        file_only_logger.debug(f"Not in pregame after 3 attempts: {pregame_error}")
                        pass
        
        # Method 3: Try checking ingame
        if state is None:
            for ingame_attempt in range(2):
                try:
                    player_data = client.coregame_fetch_player()
                    if player_data and isinstance(player_data, dict) and 'MatchID' in player_data:
                        state = "INGAME"
                        match_id_short = str(player_data.get('MatchID', 'Unknown'))[:20]
                        print("\n" + "╔" + "═"*58 + "╗")
                        print("║" + " 🎯 INGAME DETECTED ".center(58) + "║")
                        print("║" + f" Match ID: {match_id_short} ".center(58) + "║")
                        print("╚" + "═"*58 + "╝")
                        logger.info(f"Detected INGAME via coregame_fetch_player() (attempt {ingame_attempt + 1})")
                        break
                except Exception as ingame_error:
                    # Not in game
                    if ingame_attempt < 1:
                        time.sleep(0.2)  # Small delay before retry
                    else:
                        file_only_logger.debug(f"Not in game after 2 attempts: {ingame_error}")
                        pass
        
        # If we still don't have a state, session was None
        if state is None:
            none_session_count += 1
            
            # Use shorter check interval when no session detected (to catch pregame faster)
            short_check_interval = 1  # Check every 1 second when no session
            
            # Try to re-activate client after many None sessions
            if none_session_count > 20:  # After 20 seconds (20 * 1s)
                try:
                    print("\n" + "╔" + "═"*58 + "╗")
                    print("║" + " 🔄 Attempting to reconnect to Valorant client... ".center(58) + "║")
                    print("╚" + "═"*58 + "╝")
                    client.activate()
                    none_session_count = 0  # Reset counter
                    print("✅ Client re-activated. Checking session...")
                except Exception as reactivate_error:
                    print("╔" + "═"*58 + "╗")
                    print("║" + " ❌ Failed to re-activate ".center(58) + "║")
                    print("║" + f" {str(reactivate_error)[:54]} ".center(58) + "║")
                    print("╚" + "═"*58 + "╝")
                    file_only_logger.error(f"Re-activation failed: {reactivate_error}")
            
            # Show debug info to help diagnose (only once)
            if 'shown_none_warning' not in exception_counter:
                print("\n" + "╔" + "═"*58 + "╗")
                print("║" + " ⚠️  No active session detected ".center(58) + "║")
                print("╠" + "═"*58 + "╣")
                print("║ This can happen if:".ljust(58) + " ║")
                print("║   • You're in the main menu".ljust(58) + " ║")
                print("║   • The game hasn't fully loaded".ljust(58) + " ║")
                print("║   • Valorant client API isn't ready".ljust(58) + " ║")
                print("║" + " Checking every 1 second... ".center(58) + "║")
                print("╚" + "═"*58 + "╝\n")
                exception_counter['shown_none_warning'] = True
            file_only_logger.debug(f"Session is None (count: {none_session_count}), waiting...")
            time.sleep(short_check_interval)
            continue
        
        # Reset counter if we got a valid session
        none_session_count = 0
        
        # Reset warning flag if we got a session
        if 'shown_none_warning' in exception_counter:
            del exception_counter['shown_none_warning']
        
        # We now have state from one of the methods above
        
        # Only print when state changes
        if state != last_state:
            print(f"\n>>> State changed: {last_state} -> {state}")
            logger.info(f"State changed: {last_state} -> {state}")
            last_state = state
            last_pregame_match_id = None  # Reset when state changes
        
        if state == "PREGAME":
            try:
                # Fetch match data with retry logic
                player_data = None
                for fetch_attempt in range(3):
                    try:
                        player_data = client.pregame_fetch_player()
                        if player_data and isinstance(player_data, dict) and 'MatchID' in player_data:
                            break
                    except Exception as fetch_err:
                        if fetch_attempt < 2:
                            logger.debug(f"Pregame fetch attempt {fetch_attempt + 1} failed, retrying...")
                            time.sleep(0.3)
                        else:
                            raise fetch_err
                
                if not player_data or 'MatchID' not in player_data:
                    logger.warning("Could not fetch pregame player data")
                    time.sleep(check_interval)
                    continue
                
                match_id = player_data['MatchID']
                
                # Only process once per pre-game
                if match_id != last_pregame_match_id:
                    logger.info(f"Detected PREGAME - Match ID: {match_id}")
                    
                    # Fetch match data with retry
                    match_data = None
                    for match_fetch_attempt in range(3):
                        try:
                            match_data = client.pregame_fetch_match()
                            if match_data and isinstance(match_data, dict):
                                break
                        except Exception as match_fetch_err:
                            if match_fetch_attempt < 2:
                                logger.debug(f"Match fetch attempt {match_fetch_attempt + 1} failed, retrying...")
                                time.sleep(0.3)
                            else:
                                raise match_fetch_err
                    
                    if not match_data:
                        logger.warning("Could not fetch pregame match data")
                        time.sleep(check_interval)
                        continue
                    
                    map_id = match_data.get('MapID', '')
                    map_name = get_map_name(map_id)
                    
                    # Get PUUIDs for both teams
                    all_puuids = []
                    if 'AllyTeam' in match_data and match_data['AllyTeam']:
                        if 'Players' in match_data['AllyTeam']:
                            for player in match_data['AllyTeam']['Players']:
                                if 'Subject' in player:
                                    all_puuids.append(player['Subject'])
                    if 'EnemyTeam' in match_data and match_data['EnemyTeam']:
                        if 'Players' in match_data['EnemyTeam']:
                            for player in match_data['EnemyTeam']['Players']:
                                if 'Subject' in player:
                                    all_puuids.append(player['Subject'])
                    
                    # Show Map and Side IMMEDIATELY (before anything else)
                    print("\n" + "╔" + "═"*58 + "╗")
                    print("║" + " 🎮 PRE-GAME INFO ".center(58) + "║")
                    print("╠" + "═"*58 + "╣")
                    map_display = map_name if len(map_name) <= 44 else map_name[:41] + "..."
                    print(f"║ {'🗺️  Map:':<12} {map_display:<44} ║")
                    
                    if 'AllyTeam' in match_data and match_data['AllyTeam']:
                        side = "Attackers" if match_data['AllyTeam']['TeamID'] == "Blue" else "Defenders"
                        side_icon = "⚔️" if side == "Attackers" else "🛡️"
                        print(f"║ {'Side:':<12} {side_icon} {side:<41} ║")
                    print("╚" + "═"*58 + "╝")
                    
                    # Auto-lock FIRST (immediately, before showing names)
                    agent_for_map = get_agent_for_map(map_name, config)
                    
                    if agent_for_map:
                        preferred = agent_for_map.lower().strip()
                        if preferred in agent_dict:
                            display_name = agent_uuid_to_name.get(agent_dict[preferred], preferred.capitalize())
                            
                            if config.get('autolock'):
                                # Auto-lock (instalock) - FAST retries (10x, no delays)
                                print("\n" + "╔" + "═"*58 + "╗")
                                print("║" + f" 🔒 Auto-locking {display_name} ".center(58) + "║")
                                print("╚" + "═"*58 + "╝")
                                
                                max_retries = 10
                                locked_successfully = False
                                for attempt in range(max_retries):
                                    try:
                                        if lock_agent(preferred):
                                            logger.info(f"Auto-locked {display_name} successfully on attempt {attempt + 1}")
                                            print(f"✅ {display_name} locked!")
                                            locked_successfully = True
                                            break
                                    except Exception as auto_lock_error:
                                        error_str = str(auto_lock_error).lower()
                                        # Check if agent is already locked/selected (this is actually success)
                                        if "already" in error_str or "selected" in error_str or "locked" in error_str:
                                            logger.info(f"Agent {display_name} already locked/selected")
                                            print(f"✅ {display_name} already locked!")
                                            locked_successfully = True
                                            break
                                
                                if not locked_successfully:
                                    logger.warning(f"Auto-lock failed for {display_name} after {max_retries} attempts")
                            
                            elif config.get('autolightlock'):
                                # Auto-lightlock (prelock only) - FAST retries (10x, no delays)
                                print("\n" + "╔" + "═"*58 + "╗")
                                print("║" + f" ○ Auto-prelocking {display_name} ".center(58) + "║")
                                print("╚" + "═"*58 + "╝")
                                
                                max_retries = 10
                                prelocked_successfully = False
                                for attempt in range(max_retries):
                                    try:
                                        if prelock_agent(preferred):
                                            logger.info(f"Auto-prelocked {display_name} successfully on attempt {attempt + 1}")
                                            print(f"✅ {display_name} prelocked (select manually to lock)!")
                                            prelocked_successfully = True
                                            break
                                    except Exception as auto_prelock_error:
                                        error_str = str(auto_prelock_error).lower()
                                        # Check if agent is already selected (this is actually success)
                                        if "already" in error_str or "selected" in error_str:
                                            logger.info(f"Agent {display_name} already selected")
                                            print(f"✅ {display_name} already selected!")
                                            prelocked_successfully = True
                                            break
                                
                                if not prelocked_successfully:
                                    logger.warning(f"Auto-prelock failed for {display_name} after {max_retries} attempts")
                    
                    # Wait 2 seconds, then fetch and show team names
                    print("\n⏳ Loading team names...")
                    time.sleep(2)
                    
                    # Fetch names
                    name_map = {}
                    if all_puuids:
                        name_map = get_player_names(all_puuids)
                        if not name_map:
                            name_map = get_player_names(all_puuids)
                    
                    # Show team names after the 2-second wait
                    # Show YOUR TEAM
                    print("\n" + "╔" + "═"*58 + "╗")
                    print("║" + " 👥 YOUR TEAM ".center(58) + "║")
                    print("╠" + "═"*58 + "╣")
                    if 'AllyTeam' in match_data and match_data['AllyTeam']:
                        ally_count = len(match_data['AllyTeam'].get('Players', []))
                        print(f"║ {'Total Players:':<15} {ally_count:<41} ║")
                        print("╠" + "─"*58 + "╣")
                        for idx, player in enumerate(match_data['AllyTeam']['Players'], 1):
                            name = name_map.get(player.get('Subject', ''), "Unknown")
                            agent_name = get_agent_name(player.get('CharacterID'))
                            locked = "🔒" if player.get('CharacterSelectionState') == 'locked' else "○"
                            print(f"║ {idx:2}. {locked} {name:<22} │ {agent_name:<20} ║")
                    else:
                        print("║ ⚠️  No team data available".ljust(58) + " ║")
                    print("╠" + "═"*58 + "╣")
                    
                    # Show ENEMY TEAM
                    if 'EnemyTeam' in match_data and match_data['EnemyTeam']:
                        enemy_count = len(match_data['EnemyTeam'].get('Players', []))
                        print(f"║" + f" ⚠️  ENEMY TEAM ({enemy_count} players) ".center(58, "─") + "║")
                        print("╠" + "─"*58 + "╣")
                        for idx, player in enumerate(match_data['EnemyTeam']['Players'], 1):
                            name = name_map.get(player.get('Subject', ''), "Unknown")
                            agent_name = get_agent_name(player.get('CharacterID'))
                            locked = "🔒" if player.get('CharacterSelectionState') == 'locked' else "○"
                            print(f"║ {idx:2}. {locked} {name:<22} │ {agent_name:<20} ║")
                        print("╠" + "═"*58 + "╣")
                    
                    print("╚" + "═"*58 + "╝\n")
                    
                    last_pregame_match_id = match_id
                
            except Exception as e:
                # Show error once to user, then log to file
                print("\n" + "╔" + "═"*58 + "╗")
                print("║" + " ❌ Error in pregame ".center(58) + "║")
                print("║" + f" {str(e)[:54]} ".center(58) + "║")
                print("║" + " Check valorant_tracker.log for details. ".center(58) + "║")
                print("╚" + "═"*58 + "╝")
                file_only_logger.error(f"Error in pregame: {e}")
                time.sleep(check_interval)
                    
        elif state == "INGAME":
            try:
                # Fetch match data
                player_data = client.coregame_fetch_player()
                match_id = player_data['MatchID']
                
                # Only process once per game
                if match_id != last_pregame_match_id:
                    logger.info(f"Detected INGAME - Match ID: {match_id}")
                    match_data = client.coregame_fetch_match()
                    puuids = get_puuids_from_match(match_data, is_pre_game=False)
                    
                    # Try to get names, with retry
                    name_map = get_player_names(puuids)
                    if not name_map and puuids:
                        logger.info("Retrying player name fetch for ingame...")
                        time.sleep(0.5)
                        name_map = get_player_names(puuids)
                    
                    # Automatically show all players with agents and teams
                    show_ingame_auto(match_data, name_map)
                    
                    last_pregame_match_id = match_id
            except Exception as e:
                # Show error once to user, then log to file
                print("\n" + "╔" + "═"*58 + "╗")
                print("║" + " ❌ Error in ingame ".center(58) + "║")
                print("║" + f" {str(e)[:54]} ".center(58) + "║")
                print("║" + " Check valorant_tracker.log for details. ".center(58) + "║")
                print("╚" + "═"*58 + "╝")
                file_only_logger.error(f"Error in ingame: {e}")
                time.sleep(check_interval)
        else:
            if state != last_state:  # Only print once per state change
                print("\n" + "╔" + "═"*58 + "╗")
                print("║" + f" ℹ Current state: {state or 'UNKNOWN'} ".center(58) + "║")
                print("║" + " Waiting for pre-game or in-game... ".center(58) + "║")
                print("╚" + "═"*58 + "╝")
                logger.info(f"Current state: {state}. Waiting for pre-game or in-game...")
        
        time.sleep(check_interval)
        
    except KeyboardInterrupt:
        logger.info("Exiting by user request.")
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + " 👋 Exiting. Goodbye! ".center(58) + "║")
        print("╚" + "═"*58 + "╝")
        break
    except Exception as e:
        # Show error once, then log to file (to avoid spam)
        error_key = str(type(e).__name__)
        if error_key not in exception_counter['count']:
            exception_counter['count'][error_key] = 0
        exception_counter['count'][error_key] += 1
        
        if exception_counter['count'][error_key] <= 1:  # Show first occurrence
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " ❌ Error in main loop ".center(58) + "║")
            print("║" + f" {str(e)[:54]} ".center(58) + "║")
            print("║" + " Further errors logged to valorant_tracker.log ".center(58) + "║")
            print("╚" + "═"*58 + "╝")
        file_only_logger.error(f"Error in main loop: {e}")
        time.sleep(check_interval)