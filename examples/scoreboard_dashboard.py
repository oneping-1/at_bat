#!/usr/bin/env python3
"""Single-file responsive MLB dashboard powered by ScoreboardData.

Run from the repository root:
    python examples/scoreboard_dashboard.py

Open http://127.0.0.1:8000. For another device on the same network, use
http://<computer-lan-ip>:8000.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections.abc import Mapping, Sequence
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import statsapi
from at_bat.scoreboard_data import ScoreboardData

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#07111f">
<title>Ballpark Live</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0d1d31;--line:#29405d;--text:#f4f8ff;--muted:#8fa5bf;--green:#5ee6a8;--blue:#58a9ff;--red:#ff6878;--yellow:#ffd166}
*{box-sizing:border-box}body{margin:0;min-width:320px;background:radial-gradient(circle at 10% 0,#16375b 0,transparent 30rem),linear-gradient(#0a1728,#07111f 35rem);color:var(--text);font-family:Inter,system-ui,sans-serif}button,input{font:inherit}.wrap{width:min(1320px,100%);margin:auto;padding:0 14px 40px}.top{position:sticky;top:0;z-index:5;margin:0 -14px;padding:12px 14px;background:#07111fdd;backdrop-filter:blur(16px);border-bottom:1px solid #20344e}.topin{width:min(1292px,100%);margin:auto;display:flex;align-items:center;gap:10px}.brand{font-weight:900;letter-spacing:-.03em}.sub,.muted{color:var(--muted)}.sub{font-size:.7rem}.controls{margin-left:auto;display:flex;gap:7px;flex-wrap:wrap}.control,button{border:1px solid var(--line);border-radius:11px;background:#ffffff08;color:var(--text);min-height:38px}.control{display:flex;align-items:center;gap:7px;padding:5px 9px}.control label{font-size:.65rem;color:var(--muted);text-transform:uppercase;font-weight:800}.control input{border:0;background:transparent;color:var(--text);outline:0;min-width:0}#date{width:128px}#delay{width:68px;text-align:right}button{padding:0 12px;cursor:pointer;font-weight:800}button.active{background:var(--green);color:#07111f;border-color:transparent}.games{display:flex;gap:9px;overflow-x:auto;padding:16px 0 10px}.game{flex:0 0 205px;text-align:left;padding:10px 12px;background:#0c1b2ddd}.game.sel{border-color:var(--green);box-shadow:inset 0 0 0 1px #5ee6a844}.ghead,.grow{display:flex;justify-content:space-between;gap:8px}.ghead{font-size:.66rem;color:var(--muted);text-transform:uppercase;margin-bottom:6px}.grow{font-weight:800;line-height:1.5}.live{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--red);margin-right:5px}.loading,.error,.empty{padding:28px;text-align:center;border:1px solid var(--line);border-radius:20px;background:var(--panel)}.hidden{display:none!important}.dash,.col{display:grid;gap:13px}.hero,.card{border:1px solid var(--line);background:#0d1d31e8;border-radius:21px;overflow:hidden}.hero{background:radial-gradient(circle at 50% 0,#1b406666,transparent 55%),linear-gradient(135deg,#112640,#0a1728)}.meta,.head{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:11px 15px;border-bottom:1px solid #243a55;color:var(--muted);font-size:.75rem}.title{font-weight:900;font-size:.8rem;letter-spacing:.05em}.eyebrow{font-size:.66rem;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);font-weight:800}.hero-scroll{overflow-x:auto;padding:20px 16px 24px}.hero-score{min-width:650px;width:100%;border-collapse:separate;border-spacing:0;font:800 clamp(.86rem,1.7vw,1.05rem) ui-monospace,monospace}.hero-score th,.hero-score td{padding:11px 10px;text-align:center;border-bottom:1px solid #ffffff16}.hero-score thead th{color:var(--muted);font-size:.7rem}.hero-score th:first-child,.hero-score td:first-child{position:sticky;left:0;z-index:2;text-align:left;min-width:150px;background:#10223a}.hero-score tbody tr:last-child td{border-bottom:0}.hero-score .teamcell{display:flex;align-items:center;gap:9px}.teamabv{font:900 1.25rem system-ui,sans-serif}.teamrecord{font:500 .68rem system-ui,sans-serif;color:var(--muted)}.hero-score .total{font-size:1.35rem;color:var(--yellow);background:#ffffff08}.hero-score .current{background:#5ee6a815;color:var(--green)}.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(300px,.7fr);gap:13px;align-items:start}.body{padding:15px}.atbat{display:grid;grid-template-columns:minmax(250px,.8fr) minmax(300px,1.2fr);gap:15px}.field{display:grid;grid-template-columns:1fr 1fr;align-items:center}.bases{width:126px;height:108px;position:relative;margin:auto}.base{position:absolute;width:36px;height:36px;transform:rotate(45deg);border:2px solid #dbe8f5aa;border-radius:4px}.base.on{background:var(--yellow);border-color:var(--yellow);box-shadow:0 0 20px #ffd16655}.b2{left:45px}.b3{left:7px;top:38px}.b1{right:7px;top:38px}.plate{position:absolute;left:49px;bottom:0;width:28px;height:22px;border:2px solid #dbe8f5aa;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%)}.counts{display:grid;gap:8px;margin-top:12px}.crow{display:grid;grid-template-columns:58px 1fr;align-items:center}.dots{display:flex;gap:6px}.dot{width:12px;height:12px;border:1px solid var(--line);border-radius:50%}.dot.ball.on{background:#59d982}.dot.strike.on{background:var(--red)}.dot.out.on{background:#fff}.pitchplot{width:190px;height:245px;position:relative;margin:auto;border:1px solid #ffffff14;border-radius:16px;background:linear-gradient(#ffffff04,#ffffff01);overflow:hidden}.plot-zone{position:absolute;border:2px solid #e4edf7dd;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr)}.plot-zone i{border:1px solid #ffffff20}.plot-plate{position:absolute;left:calc(50% - 16px);bottom:5px;width:32px;height:23px;border:2px solid #dbe8f5aa;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%)}.marker{position:absolute;width:22px;height:22px;border:2px solid white;border-radius:50%;background:var(--green);color:#07111f;display:grid;place-items:center;transform:translate(-50%,-50%);font:900 .65rem ui-monospace,monospace;box-shadow:0 0 18px #5ee6a855}.marker.edge{background:var(--yellow)}.desc{text-align:center;color:#cbd8e7;font-size:.78rem;margin-top:6px}.coords{text-align:center;color:var(--muted);font:.68rem ui-monospace,monospace;margin-top:3px}.match{display:grid;grid-template-columns:1fr auto 1fr;gap:9px}.player{padding:13px;border:1px solid var(--line);border-radius:14px;background:#ffffff05}.player:last-child{text-align:right}.pname{font-weight:900;font-size:1.05rem;margin:4px 0 10px}.stats{display:flex;gap:12px;flex-wrap:wrap}.player:last-child .stats{justify-content:flex-end}.stat b,.metric b{display:block;font:850 1rem ui-monospace,monospace}.stat small,.metric small{color:var(--muted);font-size:.62rem;text-transform:uppercase}.vs{display:grid;place-items:center;color:var(--muted);font:700 .7rem ui-monospace,monospace}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.metric{padding:11px;border:1px solid var(--line);border-radius:13px;background:#ffffff05;min-width:0}.metric b{font-size:1.1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}.wp{display:grid;gap:8px}.wplabel{display:flex;justify-content:space-between;font-size:.8rem}.bar{height:14px;border:1px solid var(--line);border-radius:999px;overflow:hidden;display:flex}.awaybar{background:var(--blue)}.homebar{background:var(--green)}.mix{display:grid;gap:10px}.mix-head,.mrow{display:grid;grid-template-columns:minmax(90px,1fr) minmax(100px,2fr) 58px 64px;gap:9px;align-items:center}.mix-head{color:var(--muted);font-size:.6rem;text-transform:uppercase;font-weight:800}.mrow{font-size:.75rem}.track{display:block;width:100%;height:10px;background:#ffffff12;border:1px solid #ffffff12;border-radius:999px;overflow:hidden}.fill{display:block;height:100%;min-width:2px;background:linear-gradient(90deg,var(--blue),var(--green));border-radius:inherit}.mix-num{text-align:right;font-family:ui-monospace,monospace}.order{display:grid;grid-template-columns:1fr;gap:5px}.orow{display:grid;grid-template-columns:20px 32px minmax(0,1fr) 54px;gap:7px;padding:8px 9px;border-radius:9px;font-size:.76rem}.orow.now{background:#5ee6a818;border:1px solid #5ee6a844}.orow span:nth-child(3){white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:800}.mono{font-family:ui-monospace,monospace}.ump{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
@media(max-width:900px){.grid{grid-template-columns:1fr}.right{grid-template-columns:repeat(2,1fr)}.right .card:first-child{grid-column:1/-1}}
@media(max-width:700px){.atbat,.field{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.match{grid-template-columns:1fr}.player:last-child{text-align:left}.player:last-child .stats{justify-content:flex-start}.right{grid-template-columns:1fr}.right .card:first-child{grid-column:auto}}
@media(max-width:520px){.sub,.control label{display:none}#date{width:116px}#delay{width:58px}.ump{grid-template-columns:1fr}.mix-head,.mrow{grid-template-columns:minmax(75px,1fr) minmax(75px,1.4fr) 46px 56px;gap:6px}.hero-scroll{padding-left:10px;padding-right:10px}}
</style>
</head>
<body>
<div class="top"><div class="topin"><div><div class="brand">Ballpark Live</div><div class="sub">scoreboard_data dashboard</div></div><div class="controls"><div class="control"><label for="date">Date</label><input id="date" type="date"></div><div class="control"><label for="delay">Delay</label><input id="delay" type="number" inputmode="numeric" min="0" step="1" value="0" aria-label="Feed delay in seconds"><span class="sub">sec</span></div><button id="auto" class="active" type="button">Auto</button><button id="refresh" type="button" aria-label="Refresh">↻</button></div></div></div>
<main class="wrap">
<div id="games" class="games"></div><div id="loading" class="loading">Loading games…</div><div id="error" class="error hidden"></div><div id="empty" class="empty hidden">No MLB games found for this date.</div>
<section id="dash" class="dash hidden">
<article class="hero"><div class="meta"><span id="status">Scheduled</span><span id="time">—</span></div><div class="hero-scroll"><table id="heroScore" class="hero-score"></table></div></article>
<div class="grid"><div class="col">
<article class="card"><div class="head"><span class="title">LIVE AT-BAT</span><span id="updated" class="eyebrow">Waiting</span></div><div class="body atbat"><div class="field"><div><div class="bases"><div id="b2" class="base b2"></div><div id="b3" class="base b3"></div><div id="b1" class="base b1"></div><div class="plate"></div></div><div class="counts"><div class="crow"><span class="eyebrow">Balls</span><span id="balls" class="dots"></span></div><div class="crow"><span class="eyebrow">Strikes</span><span id="strikes" class="dots"></span></div><div class="crow"><span class="eyebrow">Outs</span><span id="outs" class="dots"></span></div></div></div><div><div class="pitchplot"><div id="plotZone" class="plot-zone"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><div class="plot-plate"></div><div id="marker" class="marker hidden">•</div></div><div id="pdesc" class="desc">No pitch yet</div><div id="coords" class="coords">—</div></div></div><div><div class="match"><div class="player"><div class="eyebrow">Batter</div><div id="batter" class="pname">—</div><div class="stats"><div class="stat"><b id="bline">—</b><small>Today</small></div><div class="stat"><b id="bavg">—</b><small>AVG</small></div><div class="stat"><b id="bops">—</b><small>OPS</small></div></div></div><div class="vs">VS</div><div class="player"><div class="eyebrow">Pitcher</div><div id="pitcher" class="pname">—</div><div class="stats"><div class="stat"><b id="pip">—</b><small>IP</small></div><div class="stat"><b id="pks">—</b><small>K</small></div><div class="stat"><b id="pcount">—</b><small>S / P</small></div></div></div></div><div class="metrics"><div class="metric"><small>Pitch</small><b id="ptype">—</b></div><div class="metric"><small>Velocity</small><b id="pspeed">—</b></div><div class="metric"><small>Horizontal</small><b id="ph">—</b></div><div class="metric"><small>Induced Vert.</small><b id="pv">—</b></div></div></div></div></article>
<article class="card"><div class="head"><span class="title">GAME LEVERAGE</span><span id="gamepk" class="eyebrow">Game</span></div><div class="body"><div class="wp"><div class="wplabel"><span id="wal">Away 50%</span><span id="whl">Home 50%</span></div><div class="bar"><div id="wab" class="awaybar" style="width:50%"></div><div id="whb" class="homebar" style="width:50%"></div></div></div><div class="metrics"><div class="metric"><small>Expected runs</small><b id="re">—</b></div><div class="metric"><small>Chance to score</small><b id="ts">—</b></div><div class="metric"><small>Exit velocity</small><b id="ev">—</b></div><div class="metric"><small>xBA / xSLG</small><b id="xcontact">—</b></div></div></div></article>
</div><div class="col right">
<article class="card"><div class="head"><span class="title">PITCH MIX</span><span id="ptotal" class="eyebrow">0 pitches</span></div><div class="body mix"><div class="mix-head"><span>Pitch</span><span>Usage</span><span style="text-align:right">S/P</span><span style="text-align:right">Avg mph</span></div><div id="mix" class="mix"></div></div></article>
<article class="card"><div class="head"><span class="title">BATTING ORDER</span><span id="side" class="eyebrow">Batting</span></div><div id="order" class="body order"></div></article>
<article class="card"><div class="head"><span class="title">UMPIRE IMPACT</span><span id="call" class="eyebrow">Tracking calls</span></div><div class="body ump"><div class="metric"><small>Missed</small><b id="missed">0 / 0</b></div><div class="metric"><small>Run favor</small><b id="favor">0.00</b></div><div class="metric"><small>Win prob.</small><b id="uwp">0.0%</b></div></div></article>
</div></div></section></main>
<script>
const $=id=>document.getElementById(id),S={games:[],gamepk:null,paused:false,timer:null,busy:false};
function txt(id,v,f='—'){const e=$(id);if(e)e.textContent=v===null||v===undefined||v===''?f:String(v)}function safe(o,p,f=null){for(const k of p.split('.')){if(!o||typeof o!=='object')return f;o=o[k]}return o??f}function n(v,d=0){v=Number(v);return Number.isFinite(v)?v.toFixed(d):'—'}function pct(v){v=Number(v);return Number.isFinite(v)?(v*100).toFixed(1)+'%':'—'}function dec(v){v=Number(v);if(!Number.isFinite(v))return'—';const s=v.toFixed(3);return s[0]==='0'?s.slice(1):s}function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]))}async function get(u){const r=await fetch(u,{cache:'no-store'}),j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||`Request failed ${r.status}`);return j}function localDate(){const d=new Date(Date.now()-new Date().getTimezoneOffset()*60000);return d.toISOString().slice(0,10)}function delayValue(){const x=Math.floor(Number($('delay').value)),v=Number.isFinite(x)&&x>=0?x:0;$('delay').value=v;return v}function kind(s=''){s=s.toLowerCase();if(s.includes('progress')||s.includes('live')||s.includes('inning'))return'live';if(s.includes('final'))return'final';return'scheduled'}
function renderGames(){const p=$('games');p.innerHTML='';for(const g of S.games){const b=document.createElement('button');b.type='button';b.className='game '+(Number(g.gamepk)===Number(S.gamepk)?'sel':'');const k=kind(g.status),score=k!=='scheduled';b.innerHTML=`<div class="ghead"><span>${k==='live'?'<i class="live"></i>':''}${esc(g.status||'Scheduled')}</span><span>${esc(g.venue||'')}</span></div><div class="grow"><span>${esc(g.away_abv||g.away)}</span><span>${score?esc(g.away_score??0):''}</span></div><div class="grow"><span>${esc(g.home_abv||g.home)}</span><span>${score?esc(g.home_score??0):''}</span></div>`;b.addEventListener('click',()=>select(g.gamepk));p.appendChild(b)}}
async function schedule(pref){$('loading').classList.remove('hidden');$('error').classList.add('hidden');$('empty').classList.add('hidden');try{const j=await get('/api/schedule?date='+encodeURIComponent($('date').value));S.games=j.games||[];if(!S.games.length){$('dash').classList.add('hidden');$('empty').classList.remove('hidden');return}const want=S.games.find(g=>Number(g.gamepk)===Number(pref||S.gamepk)),live=S.games.find(g=>kind(g.status)==='live');S.gamepk=(want||live||S.games[0]).gamepk;renderGames();await load()}catch(e){$('error').textContent=e.message;$('error').classList.remove('hidden')}finally{$('loading').classList.add('hidden')}}async function select(pk){S.gamepk=Number(pk);renderGames();const u=new URL(location);u.searchParams.set('gamepk',pk);u.searchParams.set('date',$('date').value);history.replaceState({},'',u);await load()}
function dots(id,a,total,type){const p=$(id);p.innerHTML='';for(let i=0;i<total;i++){const d=document.createElement('i');d.className='dot '+type+(i<a?' on':'');p.appendChild(d)}}function status(g){return({L:'In Progress',F:'Final',P:'Scheduled',D:'Delayed',S:'Suspended / Postponed'})[g.game_state]||g.detailedState||'Game'}function record(t){return`${t.wins??'—'}-${t.losses??'—'}`}
function renderLinescore(g){const a=g.away||{},h=g.home||{},innings=Array.isArray(g.linescore)?g.linescore:[],current=Math.max(1,Number(g.inning)||1),count=Math.max(9,current,innings.length),labels=Array.from({length:count},(_,i)=>i+1);const runs=(side,i)=>{const x=innings.find(v=>Number(v.inning)===i);return x?x[side]??'':''};$('heroScore').innerHTML=`<thead><tr><th>Team</th>${labels.map(i=>`<th class="${i===current&&g.game_state==='L'?'current':''}">${i}</th>`).join('')}<th>R</th><th>H</th><th>E</th></tr></thead><tbody><tr><td><div class="teamcell"><span class="teamabv">${esc(a.abv||'AWY')}</span><span class="teamrecord">${esc(record(a))}</span></div></td>${labels.map(i=>`<td class="${i===current&&g.inning_state==='T'?'current':''}">${esc(runs('away',i))}</td>`).join('')}<td class="total">${esc(a.runs??0)}</td><td>${esc(a.hits??0)}</td><td>${esc(a.errors??0)}</td></tr><tr><td><div class="teamcell"><span class="teamabv">${esc(h.abv||'HME')}</span><span class="teamrecord">${esc(record(h))}</span></div></td>${labels.map(i=>`<td class="${i===current&&g.inning_state==='B'?'current':''}">${esc(runs('home',i))}</td>`).join('')}<td class="total">${esc(h.runs??0)}</td><td>${esc(h.hits??0)}</td><td>${esc(h.errors??0)}</td></tr></tbody>`}
function fallbackPosition(z){return({1:[43,35],2:[50,35],3:[57,35],4:[43,50],5:[50,50],6:[57,50],7:[43,65],8:[50,65],9:[57,65],11:[24,25],12:[76,25],13:[24,78],14:[76,78]})[z]}
function renderPitchPlot(p){const zone=$('plotZone'),marker=$('marker'),px=Number(p.px),pz=Number(p.pz),top=Number(p.sz_top),bottom=Number(p.sz_bottom),xMin=-2.5,xMax=2.5,yMin=0,yMax=5,validZone=Number.isFinite(top)&&Number.isFinite(bottom)&&top>bottom;const zoneTop=validZone?top:3.5,zoneBottom=validZone?bottom:1.5;zone.style.left=((-.83-xMin)/(xMax-xMin)*100)+'%';zone.style.width=((1.66)/(xMax-xMin)*100)+'%';zone.style.top=((yMax-zoneTop)/(yMax-yMin)*100)+'%';zone.style.height=((zoneTop-zoneBottom)/(yMax-yMin)*100)+'%';let x,y,edge=false;if(Number.isFinite(px)&&Number.isFinite(pz)){x=(px-xMin)/(xMax-xMin)*100;y=(yMax-pz)/(yMax-yMin)*100;edge=x<3||x>97||y<3||y>97;x=Math.min(97,Math.max(3,x));y=Math.min(97,Math.max(3,y));txt('coords',`px ${px.toFixed(2)} · pz ${pz.toFixed(2)}`)}else{const f=fallbackPosition(Number(p.zone));if(f){[x,y]=f;txt('coords','zone '+p.zone)}else{x=null;txt('coords','—')}}if(x===null||x===undefined){marker.classList.add('hidden');return}marker.classList.remove('hidden');marker.classList.toggle('edge',edge);marker.style.left=x+'%';marker.style.top=y+'%';marker.textContent=p.at_bat_pitch_count||'•'}
function render(g){const a=g.away||{},h=g.home||{},m=g.matchup||{},b=m.batter||{},p=m.pitcher||{},pd=g.pitch_details||{};txt('status',status(g));txt('time',g.start_time?new Date(g.start_time).toLocaleString():null);txt('updated','Updated '+new Date().toLocaleTimeString());txt('gamepk','Game '+g.gamepk);renderLinescore(g);$('b1').classList.toggle('on',!!(g.runners&1));$('b2').classList.toggle('on',!!(g.runners&2));$('b3').classList.toggle('on',!!(g.runners&4));dots('balls',safe(g,'count.balls',0),3,'ball');dots('strikes',safe(g,'count.strikes',0),2,'strike');dots('outs',safe(g,'count.outs',0),3,'out');txt('batter',b.name);txt('bline',Number.isFinite(Number(b.hits))&&Number.isFinite(Number(b.at_bats))?`${b.hits} / ${b.at_bats}`:'—');txt('bavg',b.avg?String(b.avg).replace(/^0/,''):'—');txt('bops',b.ops?String(b.ops).replace(/^0/,''):'—');txt('pitcher',p.name);txt('pip',p.innings_pitched);txt('pks',p.strike_outs);txt('pcount',Number.isFinite(Number(p.strikes))&&Number.isFinite(Number(p.pitches))?`${p.strikes} / ${p.pitches}`:'—');txt('ptype',pd.type==='Four-Seam Fastball'?'4-Seam':pd.type);txt('pspeed',Number.isFinite(Number(pd.speed))?n(pd.speed,1)+' mph':'—');txt('ph',Number.isFinite(Number(pd.break_horizontal))?n(pd.break_horizontal,1)+' in':'—');txt('pv',Number.isFinite(Number(pd.break_vertical_induced))?n(pd.break_vertical_induced,1)+' in':'—');txt('pdesc',pd.description,'No pitch yet');renderPitchPlot(pd);let aw=Number(safe(g,'win_probability.away',.5)),hw=Number(safe(g,'win_probability.home',.5)),t=aw+hw||1;aw/=t;hw/=t;$('wab').style.width=aw*100+'%';$('whb').style.width=hw*100+'%';txt('wal',`${a.abv||'Away'} ${pct(aw)}`);txt('whl',`${h.abv||'Home'} ${pct(hw)}`);txt('re',n(safe(g,'run_expectancy.average_runs'),2));txt('ts',pct(safe(g,'run_expectancy.to_score')));txt('ev',Number.isFinite(Number(safe(g,'hit_details.exit_velo')))?n(safe(g,'hit_details.exit_velo'),1)+' mph':'—');txt('xcontact',`${dec(safe(g,'hit_details.xba'))} / ${dec(safe(g,'hit_details.xslg'))}`);renderMix(g.pitch_counts||{});renderOrder(g.batting_order||{},g.inning_state,a,h);const u=g.umpire||{};txt('missed',`${u.num_missed??0} / ${u.total_calls??0}`);txt('favor',Math.abs(Number(u.home_favor||0)).toFixed(2));txt('uwp',Math.abs(Number(u.home_wpa||0)*100).toFixed(1)+'%');txt('call',pd.umpire_missed_call?'Latest call missed':'Tracking calls');$('dash').classList.remove('hidden')}
function renderMix(raw){const rows=Object.entries(raw).map(([name,v])=>typeof v==='number'?{name,total:Number(v),strikes:null,avg:null}:{name,total:Number(v?.total??v?.count??0),strikes:Number.isFinite(Number(v?.strikes))?Number(v.strikes):null,avg:Number.isFinite(Number(v?.avg_speed))?Number(v.avg_speed):null}).filter(x=>x.name&&x.total>0).sort((a,b)=>b.total-a.total).slice(0,7),p=$('mix'),total=rows.reduce((s,x)=>s+x.total,0);txt('ptotal',total+(total===1?' pitch':' pitches'));p.innerHTML=rows.length?'':'<span class="muted">No pitch data yet.</span>';for(const r of rows){const percent=total?r.total/total*100:0,d=document.createElement('div');d.className='mrow';d.innerHTML=`<span>${esc(r.name.replace('Four-Seam Fastball','4-Seam').replace('Knuckle Curve','Knuckle'))}</span><span class="track" title="${percent.toFixed(1)}% usage"><span class="fill" style="width:${percent.toFixed(2)}%"></span></span><span class="mix-num">${r.strikes===null?r.total:r.strikes+'/'+r.total}</span><span class="mix-num">${r.avg===null?'—':r.avg.toFixed(1)}</span>`;p.appendChild(d)}}
function renderOrder(o,state,a,h){const rows=Array.isArray(o.batting_order)?o.batting_order:[],p=$('order');txt('side',(state==='B'?h.abv:a.abv)+' batting');p.innerHTML=rows.length?'':'<span class="muted">Lineup unavailable.</span>';for(const r of rows){const d=document.createElement('div');d.className='orow '+(Number(r.order)===Number(o.at_bat_index)?'now':'');d.innerHTML=`<span class="mono">${esc(r.order)}</span><span class="mono">${esc(r.position||'')}</span><span>${esc(r.last_name||'—')}</span><span class="mono">${esc(String(r.ops||'—').replace(/^0/,''))}</span>`;p.appendChild(d)}}
async function load(){if(!S.gamepk||S.busy)return;S.busy=true;try{const j=await get(`/api/game?gamepk=${S.gamepk}&delay=${delayValue()}`);render(j.game);const g=S.games.find(x=>Number(x.gamepk)===Number(S.gamepk));if(g){g.away_score=j.game.away?.runs;g.home_score=j.game.home?.runs;g.status=status(j.game);renderGames()}start()}catch(e){$('error').textContent=e.message;$('error').classList.remove('hidden')}finally{S.busy=false}}function start(){clearInterval(S.timer);if(!S.paused)S.timer=setInterval(load,5000)}$('date').addEventListener('change',()=>schedule());$('delay').addEventListener('change',load);$('delay').addEventListener('keydown',e=>{if(e.key==='Enter')load()});$('refresh').addEventListener('click',load);$('auto').addEventListener('click',()=>{S.paused=!S.paused;$('auto').classList.toggle('active',!S.paused);$('auto').textContent=S.paused?'Paused':'Auto';start()});const q=new URLSearchParams(location.search);$('date').value=q.get('date')||localDate();$('delay').value=q.get('delay')||'0';schedule(q.get('gamepk'));
</script>
</body></html>'''

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SCHEDULE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
GAME_CACHE: dict[tuple[int, int], tuple[float, dict[str, Any]]] = {}


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except (TypeError, ValueError):
            pass
    return str(value)


def schedule_payload(day: str) -> dict[str, Any]:
    now = time.monotonic()
    cached = SCHEDULE_CACHE.get(day)
    if cached and now - cached[0] < 30:
        return cached[1]
    games = []
    for game in statsapi.schedule(date=day):
        gamepk = game.get("game_id") or game.get("gamePk")
        if not gamepk:
            continue
        games.append({
            "gamepk": int(gamepk),
            "away": game.get("away_name") or game.get("away_team") or "Away",
            "home": game.get("home_name") or game.get("home_team") or "Home",
            "away_abv": game.get("away_abbreviation") or game.get("away_code"),
            "home_abv": game.get("home_abbreviation") or game.get("home_code"),
            "away_score": game.get("away_score"),
            "home_score": game.get("home_score"),
            "status": game.get("status") or game.get("detailed_state") or "Scheduled",
            "game_datetime": game.get("game_datetime") or game.get("game_date"),
            "venue": game.get("venue_name") or game.get("venue") or "",
        })
    payload = {"date": day, "games": json_safe(games)}
    SCHEDULE_CACHE[day] = (now, payload)
    return payload


def linescore_from_scoreboard(scoreboard: ScoreboardData) -> list[dict[str, Any]]:
    """Read inning totals from the Game already owned by ScoreboardData."""
    game_dict = getattr(scoreboard.game, "_game_dict", {})
    innings = game_dict.get("liveData", {}).get("linescore", {}).get("innings", [])
    result = []
    for index, inning in enumerate(innings, start=1):
        result.append({
            "inning": inning.get("num", index),
            "away": inning.get("away", {}).get("runs"),
            "home": inning.get("home", {}).get("runs"),
        })
    return result


def add_pitch_coordinates(scoreboard: ScoreboardData, game: dict[str, Any]) -> None:
    """Expose the latest Statcast plate coordinates through the dashboard payload."""
    pitch = game.setdefault("pitch_details", {})
    dataframe = scoreboard.dataframe
    if dataframe is None or dataframe.empty:
        return
    row = dataframe.iloc[-1]
    for output_key, column in (
        ("px", "px"),
        ("pz", "pz"),
        ("sz_top", "strike_zone_top"),
        ("sz_bottom", "strike_zone_bottom"),
    ):
        value = row.get(column, None)
        pitch[output_key] = json_safe(value)


def game_payload(gamepk: int, delay: int) -> dict[str, Any]:
    key = (gamepk, delay)
    now = time.monotonic()
    cached = GAME_CACHE.get(key)
    if cached and now - cached[0] < 2:
        return cached[1]
    scoreboard = ScoreboardData(gamepk=gamepk, delay_seconds=delay)
    game = json_safe(scoreboard.to_dict())
    game["linescore"] = json_safe(linescore_from_scoreboard(scoreboard))
    add_pitch_coordinates(scoreboard, game)
    payload = {"game": game}
    GAME_CACHE[key] = (now, payload)
    return payload


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "BallparkLive/1.2"

    def log_message(self, format_string: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format_string % args}")

    def send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self) -> None:
        body = HTML.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/":
                self.send_html()
                return
            if parsed.path == "/api/schedule":
                day = query.get("date", [date.today().isoformat()])[0]
                if not DATE_RE.fullmatch(day):
                    raise ValueError("date must use YYYY-MM-DD")
                self.send_json(schedule_payload(day))
                return
            if parsed.path == "/api/game":
                gamepk = int(query.get("gamepk", [""])[0])
                delay_value = float(query.get("delay", ["0"])[0])
                if not math.isfinite(delay_value):
                    raise ValueError("delay must be a non-negative number")
                delay = int(delay_value)
                if gamepk <= 0:
                    raise ValueError("gamepk must be a positive integer")
                if delay < 0:
                    raise ValueError("delay must be zero or greater")
                self.send_json(game_payload(gamepk, delay))
                return
            self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self.send_json({"error": f"Unable to load MLB data: {error}"}, HTTPStatus.BAD_GATEWAY)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Ballpark Live dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"Ballpark Live running at http://127.0.0.1:{args.port}")
    print(f"LAN access: http://<this-computer-ip>:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Ballpark Live")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
