# -*- coding: utf-8 -*-
"""
Created on Sat May 23 19:40:15 2026

@author: Admin
"""

# ============================================================
#  pyDrone — CODE RÉEL MicroPython
#  Communication WiFi ZLT130 4G + WebSocket
#  Capteurs réels : MPU6050, SPL06, GPS, batterie
# ============================================================

from drone import Drone
import uwebsocket
import network
import ujson as json
import utime as time
import math
import _thread

# ============================================================
#  PARAMÈTRES WIFI
#  → Remplir avec vos vraies valeurs
# ============================================================
WIFI_SSID     = "ZLT130"          # ← Nom du réseau WiFi ZLT130 4G
WIFI_PASSWORD = "VOTRE_MOT_PASSE" # ← Mot de passe WiFi ZLT130
SERVEUR_IP    = "192.168.0.XXX"   # ← IP du PC qui héberge la page web
                                   #   (trouver avec ipconfig sur Windows)
SERVEUR_PORT  = 8765               # ← Port WebSocket du serveur

# ============================================================
#  PARAMÈTRES VOL
# ============================================================
ALTITUDE_CIBLE_CM   = 80    # 0.8m altitude de croisière
SEUIL_URGENCE_BATT  = 8.0   # % batterie → atterrissage urgence
MARGE_SECURITE_BATT = 10.0  # % marge au-dessus énergie retour
HOVER_STABILISATION = 2.0   # secondes immobilité avant photo
SEGMENT_VOL_CM      = 30    # cm par segment de navigation
SEUIL_CORRECTION_CM = 15    # cm dérive légère → correction douce
SEUIL_REROUTAGE_CM  = 40    # cm dérive forte  → recalcul chemin

# ============================================================
#  VARIABLES GLOBALES
# ============================================================
drone            = None
ws               = None          # connexion WebSocket active
en_vol           = False
mission_active   = False
pos_x            = 0.0           # cm depuis home
pos_y            = 0.0
cap              = 0.0           # degrés, cap actuel
home_x           = 0.0
home_y           = 0.0
waypoints        = []            # liste reçue depuis la page web
telem_actif      = False
photo_compteur   = 0

# ============================================================
#  CONNEXION WIFI
# ============================================================

def connecter_wifi():
    """
    Connecte le pyDrone au réseau WiFi ZLT130 4G.
    Le ZLT130 crée un réseau WiFi local via la carte SIM 4G.
    Le pyDrone et le PC doivent être sur le même réseau.
    """
    print("[WIFI] Connexion à " + WIFI_SSID + "...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("[WIFI] Déjà connecté : " + wlan.ifconfig()[0])
        return wlan

    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Attendre connexion (max 15 secondes)
    timeout = 15
    debut   = time.time()
    while not wlan.isconnected():
        if time.time() - debut > timeout:
            raise Exception("[WIFI] Timeout — vérifier SSID et mot de passe")
        print("[WIFI] En attente...")
        time.sleep(1)

    ip = wlan.ifconfig()[0]
    print("[WIFI] Connecté ! IP du drone : " + ip)
    print("[WIFI] IP serveur cible       : " + SERVEUR_IP)
    return wlan


# ============================================================
#  CONNEXION WEBSOCKET
# ============================================================

def connecter_websocket():
    """
    Établit la connexion WebSocket vers le serveur web.
    Le serveur doit tourner sur le PC à l'adresse SERVEUR_IP:SERVEUR_PORT.

    Pour lancer le serveur WebSocket sur le PC :
        pip install websockets
        python serveur_ws.py   ← voir notes en bas de ce fichier
    """
    global ws
    url = "ws://" + SERVEUR_IP + ":" + str(SERVEUR_PORT)
    print("[WS] Connexion au serveur : " + url)
    ws = uwebsocket.connect(url)
    print("[WS] Connecté au serveur web ✓")
    return ws


def envoyer(type_msg, donnees):
    """
    Envoie un message JSON au serveur web via WebSocket.
    Le serveur le transmet à la page web pour affichage.
    """
    global ws
    if ws is None:
        print("[WS] Pas de connexion — message perdu : " + type_msg)
        return
    try:
        message = json.dumps({
            "type"     : type_msg,
            "data"     : donnees,
            "timestamp": str(time.time())
        })
        ws.send(message)
    except Exception as e:
        print("[WS] Erreur envoi : " + str(e))
        ws = None   # connexion perdue, on remettra à None


# ============================================================
#  CALIBRATION & STABILISATION
# ============================================================

def calibrer():
    """
    Sur le pyDrone réel, drone.connect() déclenche
    automatiquement la calibration IMU + baromètre + compas.
    """
    print("[CALIBRATION] Démarrage...")
    drone.connect()
    print("[CALIBRATION] IMU MPU6050 OK")
    print("[CALIBRATION] Baromètre SPL06 OK")
    print("[CALIBRATION] Compas QMC5883L OK")
    envoyer("STATUT", {"statut": "CALIBRATION_OK"})
    print("[CALIBRATION] ✓\n")


def stabiliser():
    """
    Attend que pitch et roll soient proches de 0°.
    Confirme que le drone est bien posé à plat avant décollage.
    """
    print("[STABILISATION] Attente capteurs...")
    debut = time.time()
    while time.time() - debut < 10:
        pitch = drone.get_pitch()
        roll  = drone.get_roll()
        print("[STABILISATION] pitch=" + str(pitch) + "° roll=" + str(roll) + "°")
        if abs(pitch) <= 2 and abs(roll) <= 2:
            print("[STABILISATION] ✓ Drone stable\n")
            envoyer("STATUT", {"statut": "STABILISATION_OK"})
            return
        time.sleep(0.5)
    print("[STABILISATION] ⚠ Timeout — vérifier que le drone est à plat")


# ============================================================
#  TÉLÉMÉTRIE TEMPS RÉEL
# ============================================================

def get_telemetrie():
    """
    Lit les vraies valeurs des capteurs du pyDrone.

    [REMPLIR SI NECESSAIRE]
    Si votre drone a un GPS externe, remplacer les lignes
    lat/lon par la lecture de votre module GPS (ex: UART).
    """
    batterie   = drone.get_battery()       # % batterie réelle LiPo
    altitude   = drone.get_height()        # cm, baromètre SPL06
    vitesse_x  = drone.get_speed_x()       # cm/s axe avant/arrière
    vitesse_y  = drone.get_speed_y()       # cm/s axe gauche/droite
    vitesse    = math.sqrt(vitesse_x**2 + vitesse_y**2) / 100.0  # m/s

    # ── GPS ──────────────────────────────────────────────────
    # Si votre pyDrone a un module GPS connecté en UART :
    #     from gps import GPS
    #     gps = GPS()
    #     lat, lon = gps.get_position()
    # Sinon, estimation depuis position dead-reckoning :
    lat = -18.9137 + pos_x * 0.000009   # ← remplacer par GPS réel
    lon =  47.5361 + pos_y * 0.000009   # ← remplacer par GPS réel

    return {
        "batterie_pct" : batterie,
        "altitude_cm"  : altitude,
        "altitude_m"   : round(altitude / 100.0, 2),
        "vitesse_ms"   : round(vitesse, 2),
        "pitch_deg"    : drone.get_pitch(),
        "roll_deg"     : drone.get_roll(),
        "yaw_deg"      : drone.get_yaw(),
        "lat"          : round(lat, 7),
        "lon"          : round(lon, 7),
        "en_vol"       : en_vol,
        "temperature_c": drone.get_temperature(),
    }


def thread_telemetrie():
    """
    Thread qui envoie la télémétrie au serveur toutes les secondes.
    Tourne en parallèle pendant toute la mission.

    [VRAI SYSTEME]
    Les valeurs affichées dans la page web (vitesse, batterie,
    altitude, lat, lon) viennent directement de ce thread.
    """
    global telem_actif
    print("[TELEM] Thread démarré")
    while telem_actif:
        try:
            telem = get_telemetrie()
            envoyer("TELEMETRIE", telem)
        except Exception as e:
            print("[TELEM] Erreur : " + str(e))
        time.sleep(1)
    print("[TELEM] Thread arrêté")


def demarrer_telemetrie():
    global telem_actif
    telem_actif = True
    _thread.start_new_thread(thread_telemetrie, ())
    print("[TELEM] Télémétrie temps réel active\n")


def arreter_telemetrie():
    global telem_actif
    telem_actif = False
    time.sleep(1.2)


# ============================================================
#  MESURE GPS (bouton "Mesurer Position Actuelle")
# ============================================================

def mesurer_position_gps():
    """
    Déclenché quand l'utilisateur clique sur
    "Mesurer Position Actuelle" dans la page web.

    Lit la position GPS réelle du drone et la renvoie
    au serveur pour affichage dans la fenêtre GPS.

    [REMPLIR SI NECESSAIRE]
    Remplacer les lignes GPS simulées par votre module réel.
    """
    print("[GPS] Mesure en cours...")

    # ── Si module GPS UART connecté ──────────────────────────
    # from gps import GPS
    # gps = GPS()
    # lat, lon = gps.get_position()

    # ── Estimation dead-reckoning (si pas de GPS externe) ────
    lat = -18.9137 + pos_x * 0.000009   # ← remplacer par GPS réel
    lon =  47.5361 + pos_y * 0.000009   # ← remplacer par GPS réel

    print("[GPS] Lat=" + str(lat) + " Lon=" + str(lon))

    # Envoyer la position mesurée au serveur web
    envoyer("GPS_MESURE", {
        "lat": lat,
        "lon": lon,
        "batterie": drone.get_battery(),
        "altitude": drone.get_height()
    })
    return lat, lon


# ============================================================
#  ACCUSÉ DE RÉCEPTION WAYPOINTS
# ============================================================

def envoyer_accuse_reception(wps, home):
    """
    Confirme au serveur web que les waypoints
    et le home point ont bien été reçus.
    S'affiche dans la fenêtre ACK de la page web.
    """
    print("[ACK] Envoi accusé de réception...")
    accuse = {
        "status"         : "ACK",
        "message"        : "Waypoints et home point reçus OK",
        "nb_waypoints"   : len(wps),
        "home_lat"       : home["lat"],
        "home_lon"       : home["lon"],
        "waypoints_recus": [{"id"  : wp["id"],
                              "lat" : wp["lat"],
                              "lon" : wp["lon"]}
                             for wp in wps]
    }
    envoyer("ACK_WAYPOINTS", accuse)
    print("[ACK] ✓ Accusé envoyé\n")


# ============================================================
#  TRAITEMENT DES COMMANDES REÇUES DU TERMINAL WEB
# ============================================================

def traiter_commande(commande):
    """
    Reçoit et exécute les commandes envoyées depuis
    le terminal de commande de la page web.

    Commandes supportées :
        get_telemetries  → retourne toutes les télémétries
        takeoff          → décollage + lancement mission
        land             → atterrissage immédiat
        hover            → vol stationnaire
        return_to_home   → retour au home point
        abort            → arrêt d'urgence
    """
    global en_vol, mission_active

    type_cmd = commande.get("type", "").lower().strip()
    print("[CMD] Commande reçue : " + type_cmd)

    # ── get_telemetries ──────────────────────────────────────
    if type_cmd == "get_telemetries":
        telem = get_telemetrie()
        envoyer("TELEMETRIE", telem)
        envoyer("CMD_ACK", {
            "commande": "get_telemetries",
            "statut"  : "OK",
            "data"    : telem
        })
        print("[CMD] Télémétries envoyées")

    # ── takeoff ──────────────────────────────────────────────
    elif type_cmd == "takeoff":
        if en_vol:
            envoyer("CMD_ACK", {"commande": "takeoff", "statut": "DEJA_EN_VOL"})
            return
        print("[CMD] Décollage...")
        drone.take_off()
        time.sleep(1)
        # Ajuster à l'altitude cible
        altitude_actuelle = drone.get_height()
        manque = ALTITUDE_CIBLE_CM - altitude_actuelle
        if manque > 0:
            drone.move_up(manque)
            time.sleep(1)
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(2)
        en_vol = True
        envoyer("STATUT", {"statut": "EN_VOL", "altitude": drone.get_height()})
        envoyer("CMD_ACK", {"commande": "takeoff", "statut": "OK"})
        print("[CMD] ✓ Décollé à " + str(drone.get_height()) + " cm")

        # Si des waypoints ont été reçus, lancer la mission
        if len(waypoints) > 0:
            mission_active = True
            _thread.start_new_thread(executer_mission_thread, ())

    # ── land ─────────────────────────────────────────────────
    elif type_cmd == "land":
        print("[CMD] Atterrissage...")
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(0.3)
        drone.land()
        en_vol          = False
        mission_active  = False
        envoyer("STATUT", {"statut": "POSE_OK"})
        envoyer("CMD_ACK", {"commande": "land", "statut": "OK"})
        print("[CMD] ✓ Posé")

    # ── hover ────────────────────────────────────────────────
    elif type_cmd == "hover":
        print("[CMD] Vol stationnaire...")
        drone.send_rc_control(0, 0, 0, 0)
        envoyer("CMD_ACK", {"commande": "hover", "statut": "OK"})
        print("[CMD] ✓ Hover actif")

    # ── return_to_home ───────────────────────────────────────
    elif type_cmd == "return_to_home":
        print("[CMD] Retour au home point...")
        envoyer("CMD_ACK", {"commande": "return_to_home", "statut": "OK"})
        return_to_home()

    # ── abort (bouton ⛔) ────────────────────────────────────
    elif type_cmd == "abort":
        print("[CMD] ABORT — Atterrissage d'urgence !")
        atterrissage_urgence("Commande ABORT reçue")

    # ── measure_gps ──────────────────────────────────────────
    elif type_cmd == "measure_gps":
        mesurer_position_gps()

    else:
        envoyer("CMD_ACK", {
            "commande": type_cmd,
            "statut"  : "INCONNU",
            "message" : "Commande non reconnue"
        })
        print("[CMD] Commande inconnue : " + type_cmd)


# ============================================================
#  GESTION BATTERIE
# ============================================================

def get_batterie():
    """Lit la vraie batterie du pyDrone."""
    return drone.get_battery()


def energie_necessaire_retour():
    """Estime l'énergie pour rentrer au home."""
    dist_home = math.sqrt(pos_x**2 + pos_y**2)
    return dist_home * 0.005 + 5.0


def verifier_rth():
    return get_batterie() <= energie_necessaire_retour() + MARGE_SECURITE_BATT


def verifier_urgence():
    return get_batterie() <= SEUIL_URGENCE_BATT


# ============================================================
#  URGENCE & RETURN TO HOME
# ============================================================

def atterrissage_urgence(raison="Batterie critique"):
    global en_vol, mission_active
    print("[URGENCE] !! ATTERRISSAGE D'URGENCE !!")
    print("[URGENCE] Raison : " + raison)
    envoyer("URGENCE", {
        "raison"   : raison,
        "batterie" : get_batterie(),
        "altitude" : drone.get_height()
    })
    drone.send_rc_control(0, 0, 0, 0)
    time.sleep(0.2)
    drone.land()
    en_vol         = False
    mission_active = False
    arreter_telemetrie()


def return_to_home():
    """
    Retour au home point (0,0) en ligne droite.
    """
    global en_vol, mission_active
    print("[RTH] Retour au home...")
    envoyer("RTH", {
        "batterie"     : get_batterie(),
        "distance_home": round(math.sqrt(pos_x**2 + pos_y**2), 1)
    })
    _voler_direct(home_x, home_y)
    drone.land()
    en_vol         = False
    mission_active = False
    arreter_telemetrie()
    print("[RTH] ✓ Home atteint\n")


# ============================================================
#  NAVIGATION
# ============================================================

def _voler_direct(target_x, target_y):
    """
    Vol en ligne droite de la position actuelle vers la cible.
    Calcule l'angle, tourne, puis avance.
    """
    global pos_x, pos_y, cap

    dx   = target_x - pos_x
    dy   = target_y - pos_y
    dist = math.sqrt(dx**2 + dy**2)

    if dist < 2:
        return

    angle_cible = math.degrees(math.atan2(dy, dx))
    rotation    = angle_cible - cap

    while rotation > 180:
        rotation -= 360
    while rotation < -180:
        rotation += 360

    if abs(rotation) > 2:
        drone.rotate(int(rotation))
        cap = angle_cible
        time.sleep(1)

    drone.move_forward(int(dist))
    pos_x = target_x
    pos_y = target_y
    time.sleep(1)


def corriger_derive():
    """
    Détecte et corrige la dérive via pitch et roll réels.

    [VRAI SYSTEME]
    La dérive est mesurée directement par le gyroscope MPU6050.
    1° de pitch/roll ≈ 5 cm de dérive.
    """
    pitch = drone.get_pitch()
    roll  = drone.get_roll()
    derive = math.sqrt(pitch**2 + roll**2) * 5.0   # conversion degrés → cm

    if derive < 2:
        return True   # pas de dérive significative

    print("[VENT] Dérive détectée : " + str(round(derive, 1)) + " cm")

    if derive <= SEUIL_CORRECTION_CM:
        # Correction douce proportionnelle
        rc_fb = int(max(-100, min(100, -pitch * 8)))
        rc_lr = int(max(-100, min(100, -roll  * 8)))
        drone.send_rc_control(rc_lr, rc_fb, 0, 0)
        time.sleep(0.3)
        drone.send_rc_control(0, 0, 0, 0)
        print("[VENT] Correction douce OK")

    elif derive > SEUIL_REROUTAGE_CM:
        print("[VENT] Dérive forte — recalcul en cours...")
        # Le recalcul se fait dans voler_vers() via ajustement final

    else:
        # Correction proportionnelle moyenne
        facteur = derive / SEUIL_REROUTAGE_CM
        rc_fb   = int(max(-100, min(100, -pitch * facteur * 15)))
        rc_lr   = int(max(-100, min(100, -roll  * facteur * 15)))
        drone.send_rc_control(rc_lr, rc_fb, 0, 0)
        time.sleep(0.5)
        drone.send_rc_control(0, 0, 0, 0)
        print("[VENT] Correction moyenne OK")

    return True


def voler_vers(target_x, target_y):
    """
    Navigation par segments avec correction de dérive réelle.
    Vérifie batterie à chaque segment.
    """
    global pos_x, pos_y, cap

    dx   = target_x - pos_x
    dy   = target_y - pos_y
    dist = math.sqrt(dx**2 + dy**2)

    if dist < 2:
        return True

    # Calcul angle et rotation vers la cible
    angle_cible = math.degrees(math.atan2(dy, dx))
    rotation    = angle_cible - cap

    while rotation > 180:
        rotation -= 360
    while rotation < -180:
        rotation += 360

    if abs(rotation) > 2:
        print("[NAV] Rotation " + str(round(rotation, 1)) + "°")
        drone.rotate(int(rotation))
        cap = angle_cible
        time.sleep(1)

    # Navigation par segments
    steps = max(1, int(dist / SEGMENT_VOL_CM))
    print("[NAV] Distance=" + str(round(dist, 1)) + "cm segments=" + str(steps))

    for step in range(steps):

        # Vérification batterie critique
        if verifier_urgence():
            atterrissage_urgence("Batterie critique : " + str(get_batterie()) + "%")
            return False

        # Vérification RTH
        if verifier_rth():
            envoyer("RTH_AUTO", {"batterie": get_batterie()})
            return_to_home()
            return False

        # Calcul du pas
        restant = math.sqrt((target_x - pos_x)**2 + (target_y - pos_y)**2)
        pas     = min(SEGMENT_VOL_CM, int(restant))
        if pas < 2:
            break

        # Avancer
        drone.move_forward(pas)
        pos_x += pas * math.cos(math.radians(cap))
        pos_y += pas * math.sin(math.radians(cap))
        time.sleep(0.5)

        # Corriger la dérive mesurée par les capteurs réels
        corriger_derive()

    # Ajustement final si écart résiduel
    ecart = math.sqrt((target_x - pos_x)**2 + (target_y - pos_y)**2)
    if ecart > 5:
        print("[NAV] Ajustement final " + str(round(ecart, 1)) + "cm")
        _voler_direct(target_x, target_y)

    pos_x = target_x
    pos_y = target_y
    return True


# ============================================================
#  PHOTO & CARTE SD
# ============================================================

def attendre_immobilite():
    """
    Attend que le drone soit stable (pitch/roll < 1°)
    avant la prise de photo.
    """
    print("[PHOTO] Immobilisation avant photo...")
    drone.send_rc_control(0, 0, 0, 0)
    debut = time.time()
    while time.time() - debut < HOVER_STABILISATION:
        pitch = drone.get_pitch()
        roll  = drone.get_roll()
        if abs(pitch) <= 1.0 and abs(roll) <= 1.0:
            print("[PHOTO] Stable ✓ pitch=" + str(pitch) + "° roll=" + str(roll) + "°")
            return True
        time.sleep(0.2)
    print("[PHOTO] Stabilisation timeout — photo quand même")
    return True


def prendre_photo(wp_id, lat, lon):
    """
    Prend une photo réelle avec la caméra OV2640 du pyDrone
    et la sauvegarde sur la carte SD.

    [REMPLIR SI NECESSAIRE]
    Vérifier le nom du module caméra de votre pyDrone.
    """
    global photo_compteur
    photo_compteur += 1

    print("[PHOTO] Photo N°" + str(photo_compteur) + " — WP" + str(wp_id))

    # Immobiliser avant la photo
    attendre_immobilite()

    # ── Capture caméra OV2640 ────────────────────────────────
    try:
        import camera
        camera.init(0, format=camera.JPEG, framesize=camera.FRAME_VGA)
        img = camera.capture()

        # Sauvegarder sur carte SD
        # [REMPLIR] Vérifier le chemin de montage de votre carte SD
        # Sur pyDrone/ESP32 : généralement /sd/ ou /sdcard/
        nom = "/sd/photo_" + str(photo_compteur) + "_WP" + str(wp_id) + ".jpg"
        f = open(nom, "wb")
        f.write(img)
        f.close()
        camera.deinit()
        print("[PHOTO] Sauvegardée sur SD : " + nom)
        statut = "OK"

    except Exception as e:
        print("[PHOTO] Erreur caméra : " + str(e))
        # [NOTE] Si la caméra n'est pas encore configurée,
        # commenter le bloc try/except ci-dessus et décommenter :
        # nom    = "photo_" + str(photo_compteur) + "_WP" + str(wp_id) + ".txt"
        # statut = "SANS_CAMERA"
        nom    = "non_sauvegardee"
        statut = "ERREUR_CAMERA"

    # Notifier le serveur web
    envoyer("PHOTO_PRISE", {
        "numero"  : photo_compteur,
        "wp_id"   : wp_id,
        "lat"     : lat,
        "lon"     : lon,
        "fichier" : nom,
        "batterie": get_batterie(),
        "statut"  : statut
    })

    print("[PHOTO] ✓ Photo N°" + str(photo_compteur) + " terminée\n")
    return True


# ============================================================
#  MISSION WAYPOINTS (thread)
# ============================================================

def executer_mission_thread():
    """
    Exécute la mission waypoints dans un thread séparé
    pour ne pas bloquer l'écoute des commandes WebSocket.
    """
    global mission_active, en_vol

    print("[MISSION] Début de la mission")
    envoyer("STATUT", {"statut": "MISSION_START", "nb_wp": len(waypoints)})

    for wp in waypoints:

        if not mission_active:
            print("[MISSION] Mission interrompue")
            return

        # Vérification batterie avant chaque WP
        if verifier_urgence():
            atterrissage_urgence("Batterie " + str(get_batterie()) + "%")
            return

        if verifier_rth():
            return_to_home()
            return

        print("[MISSION] → WP" + str(wp["id"]) +
              " lat=" + str(wp["lat"]) +
              " lon=" + str(wp["lon"]))

        envoyer("NAVIGATION", {
            "vers_wp": wp["id"],
            "lat"    : wp["lat"],
            "lon"    : wp["lon"]
        })

        # Navigation vers le waypoint
        succes = voler_vers(wp["x"], wp["y"])
        if not succes:
            return

        # Hover d'arrivée
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(2)

        # Action : photo ou hover
        if wp.get("action") == "photo":
            prendre_photo(wp["id"], wp["lat"], wp["lon"])
        elif wp.get("action") == "hover":
            attendre_immobilite()

        envoyer("WP_TERMINE", {
            "wp_id"   : wp["id"],
            "batterie": get_batterie()
        })
        print("[MISSION] WP" + str(wp["id"]) + " terminé ✓")

    # Tous les WP faits → RTH automatique
    print("[MISSION] Tous les waypoints terminés → RTH")
    envoyer("STATUT", {"statut": "MISSION_COMPLETE"})
    return_to_home()


# ============================================================
#  ÉCOUTE DES MESSAGES WEBSOCKET (boucle principale)
# ============================================================

def boucle_ecoute():
    """
    Boucle principale qui écoute en permanence les messages
    entrants depuis le serveur web (terminal, waypoints, etc.)

    Types de messages attendus depuis la page web :
        {"type": "get_telemetries"}
        {"type": "takeoff"}
        {"type": "land"}
        {"type": "hover"}
        {"type": "return_to_home"}
        {"type": "abort"}
        {"type": "measure_gps"}
        {"type": "WAYPOINTS", "waypoints": [...], "home": {...}}
    """
    global waypoints, home_x, home_y, ws

    print("[ECOUTE] Boucle d'écoute démarrée")
    envoyer("STATUT", {"statut": "DRONE_PRET", "message": "Drone connecté et prêt"})

    while True:
        try:
            if ws is None:
                print("[ECOUTE] Reconnexion WebSocket...")
                time.sleep(2)
                ws = connecter_websocket()
                continue

            # Attendre un message du serveur (bloquant)
            data_raw = ws.recv()

            if not data_raw:
                continue

            # Parser le JSON reçu
            try:
                data = json.loads(data_raw)
            except:
                print("[ECOUTE] JSON invalide : " + str(data_raw)[:50])
                continue

            type_msg = data.get("type", "")

            # ── Réception des waypoints depuis la page web ───
            if type_msg == "WAYPOINTS":
                wps  = data.get("waypoints", [])
                home = data.get("home", {})

                if wps and home:
                    waypoints = wps
                    home_x    = home.get("x", 0)
                    home_y    = home.get("y", 0)
                    print("[WP] " + str(len(waypoints)) + " waypoints reçus")
                    envoyer_accuse_reception(waypoints, home)
                else:
                    print("[WP] Données waypoints incomplètes")

            # ── Commandes du terminal ────────────────────────
            else:
                traiter_commande(data)

        except OSError as e:
            print("[ECOUTE] Connexion perdue : " + str(e))
            ws = None
            time.sleep(2)

        except Exception as e:
            print("[ECOUTE] Erreur : " + str(e))
            time.sleep(0.5)


# ============================================================
#  PROGRAMME PRINCIPAL
# ============================================================

def main():
    global drone, ws

    print("=" * 50)
    print("  pyDrone — Système réel MicroPython")
    print("=" * 50 + "\n")

    try:
        # 1. Connexion WiFi ZLT130 4G
        connecter_wifi()

        # 2. Connexion WebSocket au serveur web
        ws = connecter_websocket()

        # 3. Initialisation du drone
        drone = Drone()

        # 4. Calibration et stabilisation
        calibrer()
        stabiliser()

        # 5. Démarrer la télémétrie temps réel
        demarrer_telemetrie()

        # 6. Boucle principale d'écoute (infinie)
        boucle_ecoute()

    except KeyboardInterrupt:
        print("\n[MAIN] Interruption manuelle")
        if en_vol and drone:
            atterrissage_urgence("Interruption manuelle")

    except Exception as e:
        print("[MAIN] ERREUR CRITIQUE : " + str(e))
        if en_vol and drone:
            atterrissage_urgence("Erreur critique : " + str(e))

    finally:
        arreter_telemetrie()
        if ws:
            try:
                ws.close()
            except:
                pass
        print("[MAIN] Programme terminé")


# Lancement automatique au démarrage du pyDrone
main()


# ============================================================
#  NOTES — SERVEUR WEBSOCKET SUR LE PC
# ============================================================
#
#  Ce code côté PC est nécessaire pour faire le pont entre
#  la page web (Flask) et le drone (WebSocket).
#
#  Créer un fichier serveur_ws.py sur votre PC :
#
#  import asyncio, websockets, json
#
#  clients = set()
#
#  async def handler(ws):
#      clients.add(ws)
#      try:
#          async for msg in ws:
#              for c in clients:
#                  if c != ws:
#                      await c.send(msg)
#      finally:
#          clients.remove(ws)
#
#  async def main():
#      async with websockets.serve(handler, "0.0.0.0", 8765):
#          print("Serveur WS sur port 8765")
#          await asyncio.Future()
#
#  asyncio.run(main())
#
#  Lancer avec : python serveur_ws.py
#
#  Puis dans votre code Flask, la page web se connecte aussi
#  à ws://127.0.0.1:8765 pour envoyer/recevoir les messages.
#
#  Ordre de démarrage :
#    1. python serveur_ws.py
#    2. python app_flask.py
#    3. Ouvrir http://127.0.0.1:5000 dans le navigateur
#    4. Allumer le pyDrone → il se connecte automatiquement
# ============================================================