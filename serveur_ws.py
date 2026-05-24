# -*- coding: utf-8 -*-
"""
Created on Sat May 23 16:07:19 2026
@author: Admin
"""
# ============================================================
# SERVEUR WEBSOCKET pyDrone - Version Finale Spyder
# ============================================================

import nest_asyncio
nest_asyncio.apply()   # Résout le conflit avec Spyder

import asyncio
import websockets
import json
from datetime import datetime

HOST = "0.0.0.0"
PORT = 8765

clients = set()
client_web = None
client_drone = None

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

async def handler(websocket):
    global client_web, client_drone
    clients.add(websocket)
    
    try:
        log(f"Nouveau client connecté — {websocket.remote_address}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                type_msg = data.get("type", "")
                
                if type_msg == "IDENTIFICATION":
                    role = data.get("role", "")
                    if role == "WEB":
                        client_web = websocket
                        log("✓ Page Web connectée")
                    elif role == "DRONE":
                        client_drone = websocket
                        log("✓ Drone connecté")
                    continue
                
                # Drone → Web
                if websocket == client_drone:
                    log(f"🚁 DRONE → WEB : {type_msg}")
                    if client_web and client_web.open:
                        await client_web.send(message)
                
                # Web → Drone
                elif websocket == client_web:
                    log(f"🌐 WEB → DRONE : {type_msg}")
                    if client_drone and client_drone.open:
                        await client_drone.send(message)
                    else:
                        log("⚠ Drone non connecté")
                        
            except json.JSONDecodeError:
                log("❌ Message non-JSON reçu")
                
    except Exception as e:
        log(f"Erreur : {e}")
    finally:
        clients.discard(websocket)
        if websocket == client_web:
            client_web = None
            log("Page Web déconnectée")
        elif websocket == client_drone:
            client_drone = None
            log("Drone déconnecté")


# ====================== LANCEMENT ======================
if __name__ == "__main__":
    log("=" * 70)
    log("🚀 SERVEUR WEBSOCKET pyDrone DÉMARRÉ")
    log(f"   Écoute sur ws://{HOST}:{PORT}")
    log("=" * 70)
    
    try:
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(websockets.serve(handler, HOST, PORT))
        log("✅ Serveur en écoute active - En attente de connexions")
        loop.run_forever()
    except KeyboardInterrupt:
        log("Serveur arrêté par l'utilisateur")
    except Exception as e:
        log(f"Erreur critique : {e}")
    finally:
        if 'server' in locals():
            server.close()
            loop.run_until_complete(server.wait_closed())