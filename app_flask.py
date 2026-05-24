# -*- coding: utf-8 -*-
"""
Created on Sat May 23 16:12:32 2026
@author: Admin
"""
from flask import Flask, render_template_string

app = Flask(__name__)

WS_SERVEUR = "ws://127.0.0.1:8765"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>pyDrone — Mission Planner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg:#050b14; --panel:#0a1628; --input:#071220;
            --border:rgba(0,200,255,0.15); --glow:rgba(0,200,255,0.45);
            --accent:#00c8ff; --green:#00ff9d; --gold:#ffd700;
            --ok:#00e676; --err:#ff3d57; --warn:#ffab40; --info:#40c4ff;
            --t1:#e8f4ff; --t2:#7ba3c8; --t3:#3d6080;
        }
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Share Tech Mono',monospace;background:var(--bg);color:var(--t1);min-height:100vh;}
        body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
            background-image:linear-gradient(rgba(0,200,255,0.03) 1px,transparent 1px),
                             linear-gradient(90deg,rgba(0,200,255,0.03) 1px,transparent 1px);
            background-size:40px 40px;}
        .hdr{position:relative;z-index:10;display:flex;align-items:center;justify-content:space-between;
            padding:0 24px;height:60px;background:rgba(10,22,40,0.97);border-bottom:1px solid var(--glow);}
        .hdr-logo{display:flex;align-items:center;gap:10px;}
        .hdr-hex{width:34px;height:34px;background:linear-gradient(135deg,var(--accent),var(--green));
            clip-path:polygon(50% 0%,95% 25%,95% 75%,50% 100%,5% 75%,5% 25%);
            display:flex;align-items:center;justify-content:center;font-size:15px;
            animation:pulse 3s ease-in-out infinite;}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.7}}
        .hdr-name{font-family:'Rajdhani',sans-serif;font-size:24px;font-weight:700;
            letter-spacing:3px;color:var(--accent);text-transform:uppercase;}
        .hdr-sub{font-size:9px;color:var(--t2);letter-spacing:2px;text-transform:uppercase;}
        .hdr-right{display:flex;align-items:center;gap:16px;}
        .ws-status{display:flex;align-items:center;gap:6px;font-size:10px;letter-spacing:1px;}
        .ws-dot{width:8px;height:8px;border-radius:50%;background:var(--err);
            box-shadow:0 0 8px var(--err);transition:all .3s;}
        .ws-dot.on{background:var(--ok);box-shadow:0 0 8px var(--ok);animation:blink 2s ease-in-out infinite;}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
        .hdr-batt-val{font-size:18px;font-weight:700;color:var(--green);
            font-family:'Share Tech Mono',monospace;}
        .container{position:relative;z-index:1;display:grid;
            grid-template-columns:420px 1fr;gap:14px;max-width:1500px;margin:0 auto;padding:14px;}
        .left-col{display:flex;flex-direction:column;gap:14px;}
        .right-col{display:flex;flex-direction:column;gap:14px;min-width:0;}
        .map-panel{background:var(--panel);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
        .map-hdr{padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--border);
            display:flex;align-items:center;justify-content:space-between;}
        .map-title{font-family:'Rajdhani',sans-serif;font-size:13px;font-weight:600;
            letter-spacing:2px;text-transform:uppercase;color:var(--accent);}
        .panel{background:var(--panel);border:1px solid var(--border);border-radius:10px;
            padding:14px;position:relative;overflow:hidden;}
        .panel::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
            background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.5;}
        .panel-warn::before{background:linear-gradient(90deg,transparent,var(--warn),transparent);}
        .ptitle{font-family:'Rajdhani',sans-serif;font-size:12px;font-weight:700;
            letter-spacing:2.5px;text-transform:uppercase;color:var(--accent);
            margin-bottom:10px;display:flex;align-items:center;gap:6px;}
        .btn{font-family:'Rajdhani',sans-serif;font-size:12px;font-weight:700;
            letter-spacing:1.5px;text-transform:uppercase;padding:7px 13px;border-radius:6px;
            border:1px solid;cursor:pointer;transition:all .2s;background:none;
            display:inline-flex;align-items:center;gap:5px;white-space:nowrap;}
        .btn:hover{transform:translateY(-1px);}
        .ba{border-color:var(--accent);color:var(--accent);}
        .ba:hover{background:rgba(0,200,255,.15);box-shadow:0 0 12px rgba(0,200,255,.3);}
        .bg{border-color:var(--ok);color:var(--ok);}
        .bg:hover{background:rgba(0,230,118,.15);}
        .br{border-color:var(--err);color:var(--err);}
        .br:hover{background:rgba(255,61,87,.15);}
        .bw{border-color:var(--warn);color:var(--warn);}
        .bw:hover{background:rgba(255,171,64,.15);}
        .bi{border-color:var(--info);color:var(--info);}
        .bi:hover{background:rgba(64,196,255,.15);}
        .bsm{font-size:10px;padding:4px 9px;letter-spacing:1px;}
        .bfull{width:100%;justify-content:center;}
        .brow{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center;}
        .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;}
        .chip{background:var(--input);border:1px solid var(--border);border-radius:6px;
            padding:6px 12px;flex:1;min-width:150px;}
        .chip label{font-size:9px;color:var(--t3);display:block;letter-spacing:1px;
            text-transform:uppercase;margin-bottom:3px;}
        .chip span{color:var(--accent);font-size:13px;}
        .wp-item{display:flex;align-items:center;gap:7px;padding:5px 9px;
            background:var(--input);border:1px solid var(--border);
            border-radius:5px;margin-bottom:4px;}
        .wp-badge{background:rgba(0,200,255,.15);border:1px solid var(--accent);
            color:var(--accent);border-radius:4px;padding:1px 6px;
            font-size:9px;font-weight:700;letter-spacing:1px;white-space:nowrap;}
        .wp-coords{color:var(--t2);flex:1;font-size:11px;word-break:break-all;}
        .ack{display:inline-flex;align-items:center;gap:5px;font-size:10px;
            padding:3px 9px;border-radius:20px;border:1px solid;
            font-weight:700;letter-spacing:1px;transition:all .4s;}
        .ack-p{border-color:var(--warn);color:var(--warn);}
        .ack-s{border-color:var(--ok);color:var(--ok);}
        .ack-e{border-color:var(--err);color:var(--err);}
        .ack-dot{width:5px;height:5px;border-radius:50%;background:currentColor;}
        .blink{animation:blink 1s ease-in-out infinite;}
        .sep{height:1px;background:var(--border);margin:10px 0;}
        .telem-box{background:var(--input);border:1px solid var(--border);
            border-radius:7px;padding:10px 13px;margin-bottom:7px;}
        .telem-box label{font-size:9px;color:var(--t3);display:block;
            letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
        .telem-val{font-size:22px;font-weight:700;color:var(--gold);text-align:center;}
        .telem-unit{font-size:9px;color:var(--t3);text-align:center;margin-top:2px;}
        .telem-batt-val{font-size:28px;font-weight:700;color:var(--green);
            text-align:center;font-family:'Share Tech Mono',monospace;letter-spacing:2px;}
        .telem-coord{font-size:14px;color:var(--accent);word-break:break-all;line-height:1.5;}
        .log-box{background:var(--input);border:1px solid var(--border);
            border-radius:6px;height:180px;overflow-y:auto;
            padding:7px 10px;font-size:10px;color:var(--t2);}
        .log-entry{padding:2px 0;border-bottom:1px solid rgba(0,200,255,0.06);}
        .log-entry.sent{color:var(--accent);}
        .log-entry.recv{color:var(--ok);}
        .log-entry.err{color:var(--err);}
        .log-entry.warn{color:var(--warn);}
        .log-entry span{color:var(--t3);margin-right:6px;}
        .cmd-input-row{display:flex;gap:6px;align-items:center;margin-top:8px;}
        .cmd-input{flex:1;background:var(--input);border:1px solid var(--border);
            border-radius:6px;padding:7px 11px;font-family:'Share Tech Mono',monospace;
            font-size:12px;color:var(--t1);outline:none;transition:border-color .2s;}
        .cmd-input:focus{border-color:var(--accent);}
        .cmd-input::placeholder{color:var(--t3);}

        /* Ajouts pour modals et commandes cachées */
        .modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,.75); z-index:9000; align-items:center; justify-content:center; }
        .modal-overlay.active { display:flex; }
        .modal-box { background:var(--panel); border:1px solid var(--glow); border-radius:12px; padding:22px; min-width:340px; max-width:560px; width:90%; }
        .mtitle { font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--accent); margin-bottom:16px; padding-bottom:10px; border-bottom:1px solid var(--border); }
        .mitem { display:flex; align-items:center; gap:10px; padding:10px 12px; background:var(--input); border:1px solid var(--border); border-radius:5px; margin-bottom:6px; font-size:11px; cursor:pointer; }
        .mitem:hover { border-color:var(--accent); background:rgba(0,200,255,.08); }
        .mitem-name { color:var(--accent); font-weight:700; flex:1; }
        .mitem-meta { color:var(--t3); font-size:10px; }
        .mitem-load { font-size:10px; color:var(--ok); padding:2px 8px; border:1px solid var(--ok); border-radius:4px; }
        .mitem-delete { font-size:10px; color:var(--err); padding:2px 8px; border:1px solid var(--err); border-radius:4px; cursor:pointer; }

        .cmd-ref { background:var(--input); border:1px solid var(--border); border-radius:6px; margin-top:7px; overflow:hidden; }
        .cmd-ref-hdr { display:flex; align-items:center; justify-content:space-between; padding:6px 11px; cursor:pointer; }
        .cmd-ref-hdr:hover { background:rgba(0,200,255,.06); }
        .cmd-ref-title { font-size:10px; color:var(--accent); letter-spacing:1.5px; text-transform:uppercase; }
        .cmd-ref-arrow { font-size:10px; color:var(--t3); transition:transform .22s; }
        .cmd-ref-arrow.open { transform:rotate(180deg); }
        .cmd-ref-body { display:none; max-height:180px; overflow-y:auto; padding:5px 7px; }
        .cmd-ref-body.open { display:block; }
        .cmd-ref-item { display:flex; align-items:baseline; gap:8px; padding:5px 6px; border-radius:4px; cursor:pointer; }
        .cmd-ref-item:hover { background:rgba(0,200,255,.1); }
        .cri-name { font-size:11px; color:var(--accent); font-weight:700; min-width:160px; }
        .cri-args { font-size:9px; color:var(--warn); }
        .cri-desc { font-size:10px; color:var(--t3); }
    </style>
</head>
<body>

<!-- MODALS -->
<div class="modal-overlay" id="modal-browse-wp">
    <div class="modal-box">
        <div class="mtitle">📂 Missions WP Sauvegardées</div>
        <div id="mission-list-wp" style="max-height:320px;overflow-y:auto;margin-bottom:12px;"></div>
        <button class="btn bi" onclick="closeModal('modal-browse-wp')">Fermer</button>
    </div>
</div>
<div class="modal-overlay" id="modal-browse-home">
    <div class="modal-box">
        <div class="mtitle">📂 Home Points Sauvegardés</div>
        <div id="mission-list-home" style="max-height:320px;overflow-y:auto;margin-bottom:12px;"></div>
        <button class="btn bi" onclick="closeModal('modal-browse-home')">Fermer</button>
    </div>
</div>

<!-- HEADER -->
<header class="hdr">
    <div class="hdr-logo">
        <div class="hdr-hex">🚁</div>
        <div>
            <div class="hdr-name">pyDrone</div>
            <div class="hdr-sub">Mission Planner · Système Réel</div>
        </div>
    </div>
    <div class="hdr-right">
        <div class="ws-status">
            <div class="ws-dot" id="ws-dot"></div>
            <span id="ws-label">DÉCONNECTÉ</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:9px;color:var(--t3);text-transform:uppercase;letter-spacing:1px;">BATT</span>
            <span class="hdr-batt-val" id="hdr-batt">—</span>
            <span style="font-size:11px;color:var(--t2);">%</span>
        </div>
    </div>
</header>

<div class="container">
    <div class="left-col">
        <!-- STATUT DRONE -->
        <div class="panel">
            <div class="ptitle">🚁 Statut Drone</div>
            <div class="drone-status">
                <div class="drone-status-dot" id="drone-dot"></div>
                <span class="drone-status-text" id="drone-status-text">Non connecté</span>
            </div>
        </div>

        <!-- GPS -->
        <div class="panel">
            <div class="ptitle">📡 Mesure GPS</div>
            <button class="btn ba bfull" onclick="demanderMesureGPS()">
                ⊕ Mesurer Position Actuelle
            </button>
            <div class="chips">
                <div class="chip">
                    <label>LATITUDE</label>
                    <span id="c-lat">—</span>
                </div>
                <div class="chip">
                    <label>LONGITUDE</label>
                    <span id="c-lon">—</span>
                </div>
            </div>
            <div class="sep"></div>
            <div class="brow">
                <button class="btn bi bsm" onclick="saveTo('WP')">→ Ajouter WP</button>
                <button class="btn bi bsm" onclick="saveTo('HOME')">→ Home Point</button>
            </div>
        </div>

        <!-- WAYPOINTS -->
        <div class="panel">
            <div class="ptitle">📍 Waypoints <small id="wp-count">(0)</small></div>
            <div id="waypoints_list" style="max-height:130px;overflow-y:auto;"></div>
            <div class="brow">
                <button class="btn bg bsm" onclick="envoyerWaypoints()">▶ Envoyer au drone</button>
                <button class="btn ba bsm" onclick="saveWPMission()">💾 Sauvegarder</button>
                <button class="btn bi bsm" onclick="openBrowseWPModal()">📂</button>
                <button class="btn bw bsm" onclick="resetWaypoints()">⟳ Effacer</button>
                <div id="ack-wp" class="ack ack-p">
                    <div class="ack-dot blink"></div>EN ATTENTE
                </div>
            </div>
        </div>

        <!-- HOME POINT -->
        <div class="panel">
            <div class="ptitle">🏠 Home Point</div>
            <div id="home_point_div" style="font-size:12px;color:var(--t3);padding:4px 0;word-break:break-all;">Non défini</div>
            <div class="brow">
                <button class="btn bg bsm" onclick="envoyerHomePoint()">▶ Envoyer</button>
                <button class="btn ba bsm" onclick="openSaveHomeModal()">💾 Sauvegarder</button>
                <button class="btn bi bsm" onclick="openBrowseHomeModal()">📂</button>
                <button class="btn bw bsm" onclick="resetHomePoint()">⟳ Effacer</button>
                <div id="ack-home" class="ack ack-p">
                    <div class="ack-dot blink"></div>EN ATTENTE
                </div>
            </div>
        </div>

        <!-- TÉLÉMÉTRIE -->
        <div class="panel">
            <div class="ptitle">📡 Télémétrie WiFi</div>
            <div class="telem-box">
                <label>VITESSE</label>
                <div class="telem-val" id="telem-speed">—</div>
                <div class="telem-unit">m/s</div>
            </div>
            <div class="telem-box">
                <label>BATTERIE</label>
                <div class="telem-batt-val" id="batt-pct-main">—</div>
                <div class="telem-unit">CHARGE RESTANTE</div>
            </div>
            <div class="telem-box">
                <label>ALTITUDE</label>
                <div class="telem-val" id="telem-alt" style="color:var(--accent);">—</div>
                <div class="telem-unit">m</div>
            </div>
            <div class="telem-box">
                <label>LATITUDE</label>
                <div class="telem-coord" id="telem-lat">—</div>
            </div>
            <div class="telem-box">
                <label>LONGITUDE</label>
                <div class="telem-coord" id="telem-lon">—</div>
            </div>
        </div>
    </div>

    <div class="right-col">
        <!-- CARTE -->
        <div class="map-panel">
            <div class="map-hdr">
                <div class="map-title">🗺 Carte Mission</div>
                <div style="font-size:10px;color:var(--t2);" id="map-coords">Survoler pour coordonnées</div>
            </div>
            <div id="map" style="height:480px;width:100%;"></div>
        </div>

        <!-- TERMINAL -->
        <div class="panel panel-warn">
            <div class="ptitle" style="color:var(--warn);">🎮 Terminal <small style="color:var(--t3);">COMMANDES DRONE</small></div>
            <div class="log-box" id="cmd-log">
                <div class="log-entry" style="color:var(--t3);font-style:italic;">
                    Terminal prêt — en attente de connexion drone...
                </div>
            </div>
            <div class="cmd-input-row">
                <div style="font-size:11px;color:var(--warn);white-space:nowrap;">CMD&gt;</div>
                <input class="cmd-input" type="text" id="cmd-input"
                       placeholder="Ex: get_telemetries"
                       onkeydown="if(event.key==='Enter') envoyerCommande()"
                       autocomplete="off" spellcheck="false"/>
                <button class="btn bw bsm" onclick="envoyerCommande()">▶ Envoyer</button>
                <button class="btn br bsm" onclick="envoyerUrgence()">⛔ ABORT</button>
            </div>

            <!-- Commandes cachées -->
            <div class="cmd-ref">
                <div class="cmd-ref-hdr" onclick="toggleCmdRef()">
                    <span class="cmd-ref-title">📋 Liste des commandes</span>
                    <span class="cmd-ref-arrow" id="cmd-ref-arrow">▼</span>
                </div>
                <div class="cmd-ref-body" id="cmd-ref-body"></div>
            </div>

            <div style="margin-top:10px;">
                <div class="ptitle" style="font-size:10px;margin-bottom:5px;">
                    📨 Messages WebSocket
                </div>
                <div class="log-box" id="ws-log" style="height:120px;"></div>
            </div>
        </div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
// ============================================================
// VARIABLES
// ============================================================
let ws = null;
let map = null;
let waypoints = [];
let homePoint = null;
let currentPos = null;
let wpMarkers = [];
let homeMarker = null;
let droneMarker = null;
let polyline = null;
let droneConnecte = false;

let savedMissions = [];
let savedHomes = [];
let missionCounter = 1;
let homeCounter = 1;

const WS_URL = "{{ ws_url }}";

const wpIcon = i => L.divIcon({
    className: '',
    html: `<div style="background:rgba(0,200,255,.15);border:1.5px solid #00c8ff;color:#00c8ff;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:700;">W${i}</div>`,
    iconSize: [26,26], iconAnchor: [13,13]
});
const homeIcon = L.divIcon({
    className: '',
    html: '<div style="font-size:24px;filter:drop-shadow(0 0 6px rgba(0,255,157,.9));">🏠</div>',
    iconSize: [28,28], iconAnchor: [14,14]
});
const droneIcon = L.divIcon({
    className: '',
    html: '<div style="font-size:22px;filter:drop-shadow(0 0 8px rgba(0,200,255,.9));animation:pulse 1s infinite;">🚁</div>',
    iconSize: [28,28], iconAnchor: [14,14]
});

// ============================================================
// INITIALISATION
// ============================================================
window.onload = function() {
    map = L.map('map').setView([-18.8792, 47.5079], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    polyline = L.polyline([], {
        color: '#00c8ff', weight: 2, dashArray: '6,10', opacity: .8
    }).addTo(map);

    map.on('mousemove', e => {
        document.getElementById('map-coords').textContent =
            'Lat: ' + e.latlng.lat.toFixed(6) + ' | Lon: ' + e.latlng.lng.toFixed(6);
    });

    connecterWS();
    updateWPList();
    buildCmdRef();
    setTimeout(() => map.invalidateSize(), 400);
};

// ============================================================
// SAUVEGARDE & CHARGEMENT (Nouveau)
// ============================================================
function saveWPMission(){
    if(waypoints.length === 0) return alert("Aucun waypoint à sauvegarder !");
    const name = prompt("Nom de la mission :", `Mission ${missionCounter}`);
    if(name === null) return;
    const finalName = name.trim() || `Mission ${missionCounter++}`;
    savedMissions.push({name: finalName, waypoints: JSON.parse(JSON.stringify(waypoints))});
    localStorage.setItem('pyDroneMissions', JSON.stringify(savedMissions));
    logCmd(`💾 Mission sauvegardée : ${finalName}`, "recv");
}

function openBrowseWPModal(){
    const listDiv = document.getElementById('mission-list-wp');
    listDiv.innerHTML = '';
    if(savedMissions.length === 0){
        listDiv.innerHTML = '<div style="font-size:11px;color:var(--t3);padding:10px;">Aucune mission sauvegardée</div>';
    } else {
        savedMissions.forEach((m, idx) => {
            const el = document.createElement('div');
            el.className = 'mitem';
            el.innerHTML = `<span class="mitem-name">${m.name}</span>
                            <span class="mitem-meta">${m.waypoints.length} WP</span>
                            <span class="mitem-load" onclick="loadMission(${idx});closeModal('modal-browse-wp');">Charger</span>
                            <span class="mitem-delete" onclick="deleteMission(${idx});">🗑</span>`;
            listDiv.appendChild(el);
        });
    }
    document.getElementById('modal-browse-wp').classList.add('active');
}

function loadMission(idx){
    waypoints = JSON.parse(JSON.stringify(savedMissions[idx].waypoints));
    updateWPList();
    logCmd(`📂 Mission chargée : ${savedMissions[idx].name}`, "recv");
}

function deleteMission(idx){
    if(confirm(`Supprimer ${savedMissions[idx].name} ?`)){
        savedMissions.splice(idx, 1);
        localStorage.setItem('pyDroneMissions', JSON.stringify(savedMissions));
        openBrowseWPModal();
    }
}

function openSaveHomeModal(){
    if(!homePoint) return alert("Aucun Home Point défini !");
    const name = prompt("Nom du Home Point :", `Base ${homeCounter}`);
    if(name === null) return;
    const finalName = name.trim() || `Base ${homeCounter++}`;
    savedHomes.push({name: finalName, homePoint: {...homePoint}});
    localStorage.setItem('pyDroneHomes', JSON.stringify(savedHomes));
    logCmd(`💾 Home Point sauvegardé : ${finalName}`, "recv");
}

function openBrowseHomeModal(){
    const listDiv = document.getElementById('mission-list-home');
    listDiv.innerHTML = '';
    if(savedHomes.length === 0){
        listDiv.innerHTML = '<div style="font-size:11px;color:var(--t3);padding:10px;">Aucun home point sauvegardé</div>';
    } else {
        savedHomes.forEach((h, idx) => {
            const el = document.createElement('div');
            el.className = 'mitem';
            el.innerHTML = `<span class="mitem-name">${h.name}</span>
                            <span class="mitem-meta">Lat: ${h.homePoint.lat.toFixed(6)}</span>
                            <span class="mitem-load" onclick="loadHome(${idx});closeModal('modal-browse-home');">Charger</span>
                            <span class="mitem-delete" onclick="deleteHome(${idx});">🗑</span>`;
            listDiv.appendChild(el);
        });
    }
    document.getElementById('modal-browse-home').classList.add('active');
}

function loadHome(idx){
    homePoint = {...savedHomes[idx].homePoint};
    document.getElementById('home_point_div').innerHTML = "Lat: " + homePoint.lat.toFixed(6) + "<br>Lon: " + homePoint.lon.toFixed(6);
    if (homeMarker) homeMarker.remove();
    homeMarker = L.marker([homePoint.lat, homePoint.lon], {icon: homeIcon}).addTo(map);
    logCmd(`📂 Home Point chargé : ${savedHomes[idx].name}`, "recv");
}

function deleteHome(idx){
    if(confirm(`Supprimer ${savedHomes[idx].name} ?`)){
        savedHomes.splice(idx, 1);
        localStorage.setItem('pyDroneHomes', JSON.stringify(savedHomes));
        openBrowseHomeModal();
    }
}

window.closeModal = function(id) {
    document.getElementById(id).classList.remove('active');
};

// Command list collapsible
function buildCmdRef(){
    const body = document.getElementById('cmd-ref-body');
    body.innerHTML = `
        <div class="cmd-ref-item" onclick="execCmd('get_telemetries')"><span class="cri-name">get_telemetries</span><span class="cri-desc">Lire télémétries</span></div>
        <div class="cmd-ref-item" onclick="execCmd('takeoff')"><span class="cri-name">takeoff</span><span class="cri-desc">Décollage</span></div>
        <div class="cmd-ref-item" onclick="execCmd('land')"><span class="cri-name">land</span><span class="cri-desc">Atterrissage</span></div>
        <div class="cmd-ref-item" onclick="execCmd('hover')"><span class="cri-name">hover</span><span class="cri-desc">Stationnaire</span></div>
        <div class="cmd-ref-item" onclick="execCmd('return_to_home')"><span class="cri-name">return_to_home</span><span class="cri-desc">Retour à la base</span></div>
    `;
}

function toggleCmdRef(){
    const body = document.getElementById('cmd-ref-body');
    const arrow = document.getElementById('cmd-ref-arrow');
    const isOpen = body.classList.toggle('open');
    arrow.textContent = isOpen ? '▲' : '▼';
}

// ============================================================
// Le reste du code original (inchangé)
// ============================================================
function connecterWS() {
    logWS("Connexion à " + WS_URL + "...", "warn");
    ws = new WebSocket(WS_URL);
    ws.onopen = function() {
        ws.send(JSON.stringify({type: "IDENTIFICATION", role: "WEB"}));
        setWSStatut(true);
        logWS("✓ Connecté au serveur WebSocket", "recv");
        logCmd("✓ Connecté — en attente du drone...", "recv");
    };
    ws.onmessage = function(event) {
        traiterMessageEntrant(event.data);
    };
    ws.onclose = function() {
        setWSStatut(false);
        logWS("⚠ Connexion perdue — reconnexion dans 3s...", "warn");
        setTimeout(connecterWS, 3000);
    };
    ws.onerror = function(e) {
        logWS("✗ Erreur WebSocket", "err");
    };
}

function setWSStatut(connecte) {
    const dot = document.getElementById('ws-dot');
    const label = document.getElementById('ws-label');
    if (connecte) {
        dot.classList.add('on');
        label.textContent = 'CONNECTÉ';
    } else {
        dot.classList.remove('on');
        label.textContent = 'DÉCONNECTÉ';
    }
}

function setDroneStatut(statut) {
    const dot = document.getElementById('drone-dot');
    const text = document.getElementById('drone-status-text');
    dot.className = 'drone-status-dot';
    if (statut === 'pret') {
        dot.classList.add('pret');
        text.textContent = 'Drone connecté — prêt';
        droneConnecte = true;
    } else if (statut === 'vol') {
        dot.classList.add('vol');
        text.textContent = 'En vol';
    } else {
        text.textContent = 'Non connecté';
        droneConnecte = false;
    }
}

function traiterMessageEntrant(data) {
    let msg;
    try {
        msg = JSON.parse(data);
    } catch(e) {
        logWS("JSON invalide : " + data.substring(0,50), "err");
        return;
    }
    const type = msg.type || "";
    const d = msg.data || {};
    logWS("← " + type, "recv");

    if (type === "TELEMETRIE") majTelemetrie(d);
    else if (type === "STATUT") {
        const s = d.statut || "";
        logCmd("◀ STATUT : " + s, "recv");
        if (s === "DRONE_PRET") setDroneStatut('pret');
        else if (s === "EN_VOL") setDroneStatut('vol');
        else if (s === "POSE_OK") setDroneStatut('pret');
    }
    else if (type === "ACK_WAYPOINTS") {
        setAck('ack-wp', 'sent');
        setAck('ack-home', 'sent');
        logCmd("◀ ✓ Drone a reçu " + d.nb_waypoints + " waypoints", "recv");
    }
    else if (type === "GPS_MESURE") {
        currentPos = {lat: d.lat, lon: d.lon};
        document.getElementById('c-lat').textContent = d.lat.toFixed(6);
        document.getElementById('c-lon').textContent = d.lon.toFixed(6);
        logCmd("◀ GPS mesuré : " + d.lat.toFixed(6) + ", " + d.lon.toFixed(6), "recv");
        map.panTo([d.lat, d.lon]);
    }
    else if (type === "CMD_ACK") {
        logCmd("◀ ACK " + d.commande + " → " + d.statut, "recv");
    }
    // ... (autres types restent identiques)
}

function majTelemetrie(d) { /* code original inchangé */ 
    if (d.vitesse_ms !== undefined) document.getElementById('telem-speed').textContent = d.vitesse_ms.toFixed(2);
    if (d.altitude_m !== undefined) document.getElementById('telem-alt').textContent = d.altitude_m.toFixed(2);
    if (d.batterie_pct !== undefined) {
        const b = Math.round(d.batterie_pct);
        document.getElementById('batt-pct-main').textContent = b + "%";
        document.getElementById('hdr-batt').textContent = b;
    }
    if (d.lat !== undefined) {
        document.getElementById('telem-lat').textContent = d.lat.toFixed(7);
        document.getElementById('telem-lon').textContent = d.lon.toFixed(7);
        if (droneMarker) droneMarker.remove();
        droneMarker = L.marker([d.lat, d.lon], {icon: droneIcon}).addTo(map);
    }
}

function envoyerAuDrone(obj) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        logCmd("✗ WebSocket non connecté", "err");
        return false;
    }
    ws.send(JSON.stringify(obj));
    return true;
}

function envoyerCommande() {
    const input = document.getElementById('cmd-input');
    const cmd = input.value.trim().toLowerCase();
    if (!cmd) return;
    logCmd("▶ " + cmd, "sent");
    envoyerAuDrone({type: cmd});
    input.value = '';
}

function execCmd(cmd) {
    logCmd("▶ " + cmd, "sent");
    envoyerAuDrone({type: cmd});
}

function envoyerUrgence() {
    logCmd("▶ ⛔ ABORT", "err");
    envoyerAuDrone({type: "abort"});
}

function demanderMesureGPS() {
    logCmd("▶ Demande mesure GPS...", "sent");
    envoyerAuDrone({type: "measure_gps"});
}

function saveTo(type) {
    if (!currentPos) {
        alert("Cliquez d'abord sur 'Mesurer Position Actuelle'");
        return;
    }
    if (type === 'WP') {
        const id = waypoints.length + 1;
        waypoints.push({id : id, lat: currentPos.lat, lon: currentPos.lon, x : id * 100, y : 0, action: "photo"});
        updateWPList();
        logCmd("+ WP" + id + " ajouté : " + currentPos.lat.toFixed(6) + ", " + currentPos.lon.toFixed(6), "recv");
    } else {
        homePoint = {...currentPos};
        document.getElementById('home_point_div').innerHTML = "Lat: " + homePoint.lat.toFixed(6) + "<br>Lon: " + homePoint.lon.toFixed(6);
        if (homeMarker) homeMarker.remove();
        homeMarker = L.marker([homePoint.lat, homePoint.lon], {icon: homeIcon}).addTo(map);
        logCmd("+ Home Point défini", "recv");
    }
}

function envoyerWaypoints() {
    if (waypoints.length === 0) {
        alert("Aucun waypoint défini !");
        return;
    }
    const payload = {
        type : "WAYPOINTS",
        waypoints: waypoints,
        home : homePoint || {lat: 0, lon: 0, x: 0, y: 0}
    };
    if (envoyerAuDrone(payload)) {
        logCmd("▶ Envoi de " + waypoints.length + " waypoints au drone...", "sent");
    }
}

function envoyerHomePoint() {
    if (!homePoint) {
        alert("Aucun home point défini !");
        return;
    }
    envoyerAuDrone({type: "WAYPOINTS", waypoints: [], home: homePoint});
    logCmd("▶ Home Point envoyé", "sent");
}

function resetWaypoints() {
    waypoints = [];
    wpMarkers.forEach(m => m.remove());
    wpMarkers = [];
    polyline.setLatLngs([]);
    currentPos = null;
    document.getElementById('c-lat').textContent = '—';
    document.getElementById('c-lon').textContent = '—';
    updateWPList();
    setAck('ack-wp', 'reset');
}

function resetHomePoint() {
    homePoint = null;
    if (homeMarker) homeMarker.remove();
    homeMarker = null;
    document.getElementById('home_point_div').textContent = 'Non défini';
    setAck('ack-home', 'reset');
}

function updateWPList() {
    const c = document.getElementById('waypoints_list');
    c.innerHTML = '';
    document.getElementById('wp-count').textContent = "(" + waypoints.length + ")";
    if (waypoints.length === 0) {
        c.innerHTML = '<div style="font-size:11px;color:var(--t3);padding:6px;">Aucun waypoint</div>';
        return;
    }
    waypoints.forEach((wp, i) => {
        const div = document.createElement('div');
        div.className = 'wp-item';
        div.innerHTML = '<span class="wp-badge">W' + (i+1) + '</span>' +
                        '<span class="wp-coords">' + wp.lat.toFixed(6) + ', ' + wp.lon.toFixed(6) + '</span>';
        c.appendChild(div);
    });
    wpMarkers.forEach(m => m.remove());
    wpMarkers = [];
    waypoints.forEach((wp, i) => {
        wpMarkers.push(L.marker([wp.lat, wp.lon], {icon: wpIcon(i+1)}).addTo(map));
    });
    polyline.setLatLngs(waypoints.map(w => [w.lat, w.lon]));
}

function setAck(id, state) {
    const el = document.getElementById(id);
    el.className = 'ack';
    if (state === 'sent') {
        el.classList.add('ack-s');
        el.innerHTML = '<div class="ack-dot"></div>REÇU ✓';
    } else {
        el.classList.add('ack-p');
        el.innerHTML = '<div class="ack-dot blink"></div>EN ATTENTE';
    }
}

function logCmd(msg, type) {
    const log = document.getElementById('cmd-log');
    const ts = new Date().toTimeString().slice(0,8);
    const el = document.createElement('div');
    el.className = 'log-entry ' + (type || '');
    el.innerHTML = '<span>[' + ts + ']</span>' + msg;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
}

function logWS(msg, type) {
    const log = document.getElementById('ws-log');
    const ts = new Date().toTimeString().slice(0,8);
    const el = document.createElement('div');
    el.className = 'log-entry ' + (type || '');
    el.innerHTML = '<span>[' + ts + ']</span>' + msg;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(
        HTML_TEMPLATE,
        ws_url=WS_SERVEUR
    )

if __name__ == '__main__':
    print("=" * 50)
    print(" pyDrone Mission Planner")
    print(" http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000)