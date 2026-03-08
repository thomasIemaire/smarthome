"""
Smart Home Controller - Backend Python Flask
Compatible: Shelly (Gen1 + Gen2), Meross (cloud), mode simulation
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
import os
import asyncio
import threading
import socket
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ─────────────────────────────────────────────
# FICHIER DE PERSISTANCE
# ─────────────────────────────────────────────
DEVICES_FILE = os.path.join(os.path.dirname(__file__), "devices.json")
GROUPS_FILE = os.path.join(os.path.dirname(__file__), "groups.json")

# Liste des appareils découverts (en mémoire)
DEVICES = []
device_states = {}

# Liste des groupes (en mémoire)
GROUPS = []

# ─────────────────────────────────────────────
# MEROSS - Event loop async en arrière-plan
# ─────────────────────────────────────────────
_meross_loop = None
_meross_thread = None
_meross_manager = None
_meross_http_client = None


def _start_meross_loop():
    """Démarre un event loop asyncio dans un thread séparé."""
    global _meross_loop
    _meross_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_meross_loop)
    _meross_loop.run_forever()


def run_async(coro):
    """Exécute une coroutine async depuis du code synchrone Flask."""
    if _meross_loop is None or not _meross_loop.is_running():
        return None
    future = asyncio.run_coroutine_threadsafe(coro, _meross_loop)
    return future.result(timeout=30)


def init_meross():
    """Initialise la connexion Meross (une seule fois)."""
    global _meross_manager, _meross_http_client, _meross_thread

    email = os.getenv("MEROSS_EMAIL")
    password = os.getenv("MEROSS_PASSWORD")
    if not email or not password:
        print("[Meross] Pas d'identifiants dans .env - Meross désactivé")
        return False

    # Démarrer le thread async si pas encore fait
    if _meross_thread is None:
        _meross_thread = threading.Thread(target=_start_meross_loop, daemon=True)
        _meross_thread.start()
        import time
        time.sleep(0.5)  # attendre que le loop démarre

    try:
        from meross_iot.http_api import MerossHttpClient
        from meross_iot.manager import MerossManager

        async def _init():
            global _meross_http_client, _meross_manager
            _meross_http_client = await MerossHttpClient.async_from_user_password(
                email=email,
                password=password,
                api_base_url="https://iotx-eu.meross.com"
            )
            _meross_manager = MerossManager(http_client=_meross_http_client)
            await _meross_manager.async_init()
            await _meross_manager.async_device_discovery()

        run_async(_init())
        print("[Meross] Connecté avec succès")
        return True
    except Exception as e:
        print(f"[Meross] Erreur d'initialisation: {e}")
        return False


def shutdown_meross():
    """Ferme proprement la connexion Meross."""
    global _meross_manager, _meross_http_client, _meross_loop
    try:
        if _meross_manager:
            _meross_manager.close()
        if _meross_http_client:
            run_async(_meross_http_client.async_logout())
    except Exception:
        pass
    if _meross_loop and _meross_loop.is_running():
        _meross_loop.call_soon_threadsafe(_meross_loop.stop)


# ─────────────────────────────────────────────
# PERSISTANCE devices.json
# ─────────────────────────────────────────────

def load_devices_from_file():
    """Charge les appareils depuis devices.json."""
    global DEVICES, device_states
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                DEVICES = json.load(f)
            device_states = {d["id"]: d.get("state", False) for d in DEVICES}
            print(f"[Config] {len(DEVICES)} appareils chargés depuis devices.json")
            return True
        except Exception as e:
            print(f"[Config] Erreur lecture devices.json: {e}")
    return False


def save_devices_to_file():
    """Sauvegarde les appareils dans devices.json."""
    try:
        data = []
        for d in DEVICES:
            data.append({**d, "state": device_states.get(d["id"], False)})
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[Config] {len(DEVICES)} appareils sauvegardés dans devices.json")
    except Exception as e:
        print(f"[Config] Erreur écriture devices.json: {e}")


def load_groups_from_file():
    """Charge les groupes depuis groups.json."""
    global GROUPS
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                GROUPS = json.load(f)
            print(f"[Config] {len(GROUPS)} groupes chargés depuis groups.json")
        except Exception as e:
            print(f"[Config] Erreur lecture groups.json: {e}")


def save_groups_to_file():
    """Sauvegarde les groupes dans groups.json."""
    try:
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(GROUPS, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Config] Erreur écriture groups.json: {e}")


# ─────────────────────────────────────────────
# DÉCOUVERTE RÉSEAU - SHELLY
# ─────────────────────────────────────────────

def get_local_subnet():
    """Détecte le sous-réseau local."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume /24
        parts = local_ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    except Exception:
        return "192.168.1.0/24"


def check_shelly(ip):
    """Vérifie si une IP est un appareil Shelly."""
    try:
        r = requests.get(f"http://{ip}/shelly", timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            gen = data.get("gen", 1)
            # Déterminer le nom et le type
            if gen >= 2:
                name = data.get("app", data.get("id", f"Shelly-{ip}"))
                model = data.get("model", "")
            else:
                name = data.get("type", f"Shelly-{ip}")
                model = data.get("type", "")

            # Deviner le type (light ou plug)
            device_type = "plug"
            name_lower = (name + model).lower()
            if any(kw in name_lower for kw in ["dimmer", "bulb", "rgbw", "duo", "vintage", "light"]):
                device_type = "light"

            return {
                "ip": str(ip),
                "info": data,
                "gen": gen,
                "name": name,
                "model": model,
                "device_type": device_type,
            }
    except (requests.ConnectionError, requests.Timeout, ValueError):
        pass
    return None


def scan_shelly_devices(subnet=None):
    """Scanne le réseau pour trouver des appareils Shelly."""
    if subnet is None:
        subnet = get_local_subnet()
    print(f"[Shelly] Scan du réseau {subnet}...")

    found = []
    ips = list(ipaddress.IPv4Network(subnet, strict=False).hosts())

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_shelly, str(ip)): ip for ip in ips}
        for future in as_completed(futures):
            result = future.result()
            if result:
                found.append(result)
                print(f"[Shelly] Trouvé: {result['name']} à {result['ip']} (Gen{result['gen']})")

    return found


def get_shelly_state(ip, gen=1):
    """Récupère l'état on/off d'un appareil Shelly."""
    try:
        if gen >= 2:
            r = requests.get(f"http://{ip}/rpc/Switch.GetStatus?id=0", timeout=3)
            data = r.json()
            return data.get("output", False)
        else:
            r = requests.get(f"http://{ip}/relay/0", timeout=3)
            data = r.json()
            return data.get("ison", False)
    except Exception as e:
        print(f"[Shelly] Erreur lecture état {ip}: {e}")
        return None


# ─────────────────────────────────────────────
# DÉCOUVERTE MEROSS
# ─────────────────────────────────────────────

def discover_meross_devices():
    """Découvre les appareils Meross via le cloud."""
    if _meross_manager is None:
        return []

    try:
        run_async(_meross_manager.async_device_discovery())
        meross_devs = _meross_manager.find_devices()
        found = []
        for dev in meross_devs:
            run_async(dev.async_update())
            is_on = False
            if hasattr(dev, "is_on"):
                try:
                    is_on = dev.is_on()
                except Exception:
                    is_on = False

            # Deviner le type
            device_type = "plug"
            type_lower = (dev.type or "").lower()
            name_lower = (dev.name or "").lower()
            if any(kw in type_lower + name_lower for kw in ["light", "bulb", "lamp", "led", "dimmer"]):
                device_type = "light"

            found.append({
                "name": dev.name,
                "type": dev.type,
                "online": str(dev.online_status),
                "is_on": is_on,
                "device_type": device_type,
                "uuid": dev.uuid,
            })
        return found
    except Exception as e:
        print(f"[Meross] Erreur découverte: {e}")
        return []


# ─────────────────────────────────────────────
# DRIVERS PAR PROTOCOLE
# ─────────────────────────────────────────────

def shelly_set(ip, state, gen=1):
    """Contrôle un appareil Shelly Gen1 ou Gen2."""
    try:
        if gen >= 2:
            on_str = "true" if state else "false"
            r = requests.get(f"http://{ip}/rpc/Switch.Set?id=0&on={on_str}", timeout=3)
            return r.status_code == 200
        else:
            action = "on" if state else "off"
            r = requests.get(f"http://{ip}/relay/0?turn={action}", timeout=3)
            return r.status_code == 200
    except Exception as e:
        print(f"[Shelly] Erreur {ip}: {e}")
        return False


def meross_set(device_id, state):
    """Contrôle un appareil Meross via le cloud."""
    if _meross_manager is None:
        print("[Meross] Manager non initialisé")
        return False
    try:
        devs = _meross_manager.find_devices(device_uuids=[device_id])
        if not devs:
            print(f"[Meross] Appareil {device_id} introuvable")
            return False
        dev = devs[0]
        if state:
            run_async(dev.async_turn_on(channel=0))
        else:
            run_async(dev.async_turn_off(channel=0))
        return True
    except Exception as e:
        print(f"[Meross] Erreur commande {device_id}: {e}")
        return False


def meross_get_state(device_id):
    """Récupère l'état d'un appareil Meross."""
    if _meross_manager is None:
        return None
    try:
        devs = _meross_manager.find_devices(device_uuids=[device_id])
        if not devs:
            return None
        dev = devs[0]
        run_async(dev.async_update())
        if hasattr(dev, "is_on"):
            return dev.is_on()
    except Exception:
        pass
    return None


def set_device_state(device, state):
    """Envoie une commande on/off à un appareil selon son protocole."""
    protocol = device.get("protocol", "simulation")
    if protocol == "shelly":
        return shelly_set(device["ip"], state, gen=device.get("gen", 1))
    elif protocol == "meross":
        return meross_set(device.get("meross_uuid", ""), state)
    else:
        print(f"[Simulation] {device['id']} -> {'ON' if state else 'OFF'}")
        return True


def get_real_state(device):
    """Récupère l'état réel d'un appareil (poll)."""
    protocol = device.get("protocol", "simulation")
    if protocol == "shelly":
        return get_shelly_state(device["ip"], gen=device.get("gen", 1))
    elif protocol == "meross":
        return meross_get_state(device.get("meross_uuid", ""))
    return device_states.get(device["id"], False)


# ─────────────────────────────────────────────
# ROUTES API
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Retourne tous les appareils avec leur état."""
    result = []
    for d in DEVICES:
        # Essayer de récupérer l'état réel
        real_state = get_real_state(d)
        if real_state is not None:
            device_states[d["id"]] = real_state

        result.append({
            **d,
            "state": device_states.get(d["id"], False)
        })
    return jsonify(result)


@app.route("/api/devices/<device_id>/toggle", methods=["POST"])
def toggle_device(device_id):
    """Bascule l'état d'un appareil."""
    device = next((d for d in DEVICES if d["id"] == device_id), None)
    if not device:
        return jsonify({"error": "Appareil introuvable"}), 404

    new_state = not device_states.get(device_id, False)
    success = set_device_state(device, new_state)

    if success:
        device_states[device_id] = new_state
        return jsonify({"id": device_id, "state": new_state, "success": True})
    else:
        return jsonify({"error": "Impossible de contacter l'appareil", "success": False}), 503


@app.route("/api/devices/<device_id>/state", methods=["POST"])
def set_state(device_id):
    """Définit l'état d'un appareil (on/off)."""
    device = next((d for d in DEVICES if d["id"] == device_id), None)
    if not device:
        return jsonify({"error": "Appareil introuvable"}), 404

    data = request.get_json()
    new_state = bool(data.get("state", False))
    success = set_device_state(device, new_state)

    if success:
        device_states[device_id] = new_state
        return jsonify({"id": device_id, "state": new_state, "success": True})
    else:
        return jsonify({"error": "Impossible de contacter l'appareil", "success": False}), 503


@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    """Retourne les pièces avec leurs appareils."""
    rooms = {}
    for d in DEVICES:
        room = d.get("room", "Sans pièce")
        if room not in rooms:
            rooms[room] = {"name": room, "devices": [], "active": 0}
        rooms[room]["devices"].append(d["id"])
        if device_states.get(d["id"]):
            rooms[room]["active"] += 1
    return jsonify(list(rooms.values()))


@app.route("/api/all/on", methods=["POST"])
def all_on():
    for d in DEVICES:
        set_device_state(d, True)
        device_states[d["id"]] = True
    return jsonify({"success": True, "message": "Tous les appareils allumés"})


@app.route("/api/all/off", methods=["POST"])
def all_off():
    for d in DEVICES:
        set_device_state(d, False)
        device_states[d["id"]] = False
    return jsonify({"success": True, "message": "Tous les appareils éteints"})


@app.route("/api/discover", methods=["POST"])
def discover():
    """Lance un scan réseau pour découvrir les appareils Shelly + Meross."""
    global DEVICES, device_states

    new_devices = []

    # 1. Scan Shelly
    shelly_found = scan_shelly_devices()
    for s in shelly_found:
        dev_id = f"shelly_{s['ip'].replace('.', '_')}"
        state = get_shelly_state(s["ip"], gen=s["gen"])
        new_devices.append({
            "id": dev_id,
            "name": s["name"],
            "room": "Non assigné",
            "type": s["device_type"],
            "protocol": "shelly",
            "ip": s["ip"],
            "gen": s["gen"],
            "model": s["model"],
            "state": state if state is not None else False,
            "icon": "bulb" if s["device_type"] == "light" else "plug",
        })

    # 2. Découverte Meross
    meross_found = discover_meross_devices()
    for m in meross_found:
        dev_id = f"meross_{m['uuid']}"
        new_devices.append({
            "id": dev_id,
            "name": m["name"],
            "room": "Non assigné",
            "type": m["device_type"],
            "protocol": "meross",
            "meross_uuid": m["uuid"],
            "ip": "",
            "state": m["is_on"],
            "icon": "bulb" if m["device_type"] == "light" else "plug",
        })

    # Fusionner : garder les personnalisations des anciens appareils
    old_data = {d["id"]: d for d in DEVICES}
    for d in new_devices:
        old = old_data.get(d["id"])
        if not old:
            continue
        if old.get("room", "Non assigné") != "Non assigné":
            d["room"] = old["room"]
        if old.get("name") and old["name"] != d["name"]:
            d["name"] = old["name"]
        if old.get("type") and old["type"] != d["type"]:
            d["type"] = old["type"]
            d["icon"] = "bulb" if old["type"] == "light" else "plug"

    DEVICES = new_devices
    device_states = {d["id"]: d.get("state", False) for d in DEVICES}
    save_devices_to_file()

    return jsonify({
        "success": True,
        "shelly_count": len(shelly_found),
        "meross_count": len(meross_found),
        "total": len(DEVICES),
        "devices": DEVICES,
    })


@app.route("/api/devices/<device_id>/rename", methods=["POST"])
def rename_device(device_id):
    """Renomme un appareil ou change sa pièce."""
    device = next((d for d in DEVICES if d["id"] == device_id), None)
    if not device:
        return jsonify({"error": "Appareil introuvable"}), 404

    data = request.get_json()
    if "name" in data:
        device["name"] = data["name"]
    if "room" in data:
        device["room"] = data["room"]
    if "type" in data and data["type"] in ("plug", "light"):
        device["type"] = data["type"]
        device["icon"] = "bulb" if data["type"] == "light" else "plug"

    save_devices_to_file()
    return jsonify({"success": True, "device": device})


# ─────────────────────────────────────────────
# ROUTES API - GROUPES
# ─────────────────────────────────────────────

@app.route("/api/groups", methods=["GET"])
def get_groups():
    """Retourne les groupes avec leur état calculé."""
    result = []
    for g in GROUPS:
        ids = g.get("device_ids", [])
        active = all(device_states.get(did, False) for did in ids) if ids else False
        result.append({**g, "active": active})
    return jsonify(result)


@app.route("/api/groups", methods=["POST"])
def create_group():
    """Crée un nouveau groupe."""
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Nom requis"}), 400

    group_id = f"group_{int(__import__('time').time() * 1000)}"
    group = {
        "id": group_id,
        "name": name,
        "device_ids": data.get("device_ids", []),
    }
    GROUPS.append(group)
    save_groups_to_file()
    return jsonify({"success": True, "group": group})


@app.route("/api/groups/<group_id>/toggle", methods=["POST"])
def toggle_group(group_id):
    """Toggle un groupe : si au moins un appareil off -> tout on, sinon tout off."""
    group = next((g for g in GROUPS if g["id"] == group_id), None)
    if not group:
        return jsonify({"error": "Groupe introuvable"}), 404

    ids = group.get("device_ids", [])
    all_on = all(device_states.get(did, False) for did in ids) if ids else False
    new_state = not all_on

    for did in ids:
        device = next((d for d in DEVICES if d["id"] == did), None)
        if device:
            set_device_state(device, new_state)
            device_states[did] = new_state

    return jsonify({"success": True, "group_id": group_id, "active": new_state})


@app.route("/api/groups/<group_id>", methods=["PUT"])
def update_group(group_id):
    """Modifie un groupe."""
    group = next((g for g in GROUPS if g["id"] == group_id), None)
    if not group:
        return jsonify({"error": "Groupe introuvable"}), 404

    data = request.get_json()
    if "name" in data:
        group["name"] = data["name"]
    if "device_ids" in data:
        group["device_ids"] = data["device_ids"]

    save_groups_to_file()
    return jsonify({"success": True, "group": group})


@app.route("/api/groups/<group_id>", methods=["DELETE"])
def delete_group(group_id):
    """Supprime un groupe."""
    global GROUPS
    GROUPS = [g for g in GROUPS if g["id"] != group_id]
    save_groups_to_file()
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# DÉMARRAGE
# ─────────────────────────────────────────────

# Charger les appareils sauvegardés
load_devices_from_file()
load_groups_from_file()

# Initialiser Meross si les identifiants sont présents
if os.getenv("MEROSS_EMAIL") and os.getenv("MEROSS_PASSWORD"):
    init_meross()

import atexit
atexit.register(shutdown_meross)

if __name__ == "__main__":
    print("Smart Home Controller demarre sur http://localhost:5000")
    print(f"  Appareils charges: {len(DEVICES)}")
    print(f"  Meross: {'active' if _meross_manager else 'desactive'}")
    print("  Cliquez 'Scanner' dans l'interface pour decouvrir vos appareils")
    app.run(debug=True, host="0.0.0.0", port=5000)
