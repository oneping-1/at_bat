#!/usr/bin/env python3
"""Single-file responsive dashboard powered by at_bat.scoreboard_data.

Run from the repository root:
    python scoreboard_dashboard.py

Then open http://127.0.0.1:8000. On another device on the same network, use
http://<computer-lan-ip>:8000.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections.abc import Mapping, Sequence
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

import statsapi
from at_bat.scoreboard_data import ScoreboardData

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#07111f"><title>Ballpark Live</title>
<style>
:root{color-scheme:dark;--bg:#07111f;--panel:#0e1d31;--panel2:#142844;--line:#29405d;--text:#f4f8ff;--muted:#8fa5bf;--green:#5ee6a8;--blue:#58a9ff;--red:#ff6878;--yellow:#ffd166}*{box-sizing:border-box}body{margin:0;min-width:320px;background:radial-gradient(circle at 10% 0,#16375b 0,transparent 30rem),linear-gradient(#0a1728,#07111f 35rem);color:var(--text);font-family:Inter,system-ui,sans-serif}.wrap{width:min(1320px,100%);margin:auto;padding:0 14px 40px}.top{position:sticky;top:0;z-index:5;margin:0 -14px;padding:12px 14px;background:#07111fd9;backdrop-filter:blur(16px);border-bottom:1px solid #20344e}.topin{width:min(1292px,100%);margin:auto;display:flex;align-items:center;gap:10px}.brand{font-weight:900;letter-spacing:-.03em}.sub,.muted{color:var(--muted)}.sub{font-size:.7rem}.controls{margin-left:auto;display:flex;gap:7px;flex-wrap:wrap}.control,button{border:1px solid var(--line);border-radius:11px;background:#ffffff08;color:var(--text);min-height:38px}.control{display:flex;align-items:center;gap:7px;padding:5px 9px}.control label{font-size:.65rem;color:var(--muted);text-transform:uppercase;font-weight:800}.control input,.control select{border:0;background:transparent;color:var(--text);outline:0}.control option{color:#07111f}button{padding:0 12px;cursor:pointer;font-weight:800}.active{background:var(--green);color:#07111f;border-color:transparent}.games{display:flex;gap:9px;overflow:auto;padding:16px 0 10px}.game{flex:0 0 205px;text-align:left;padding:10px 12px;background:#0c1b2ddd}.game.sel{border-color:var(--green);box-shadow:inset 0 0 0 1px #5ee6a844}.ghead,.grow{display:flex;justify-content:space-between}.ghead{font-size:.66rem;color:var(--muted);text-transform:uppercase;margin-bottom:6px}.grow{font-weight:800;line-height:1.5}.live{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--red);margin-right:5px}.loading,.error,.empty{padding:28px;text-align:center;border:1px solid var(--line);border-radius:20px;background:#0d1d31}.hidden{display:none!important}.dash{display:grid;gap:13px}.hero,.card{border:1px solid var(--line);background:#0d1d31e8;border-radius:21px;overflow:hidden}.hero{background:radial-gradient(circle at 50% 0,#1b406666,transparent 55%),linear-gradient(135deg,#112640,#0a1728)}.meta,.head{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:11px 15px;border-bottom:1px solid #243a55;color:var(--muted);font-size:.75rem}.score{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:clamp(10px,4vw,48px);padding:clamp(24px,4vw,42px)}.team:last-child{text-align:right}.city,.eyebrow{font-size:.66rem;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);font-weight:800}.name{font-size:clamp(1rem,2.5vw,1.8rem);font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.record{font-size:.75rem;color:var(--muted);margin-top:5px}.scorebox{display:flex;gap:14px;align-items:center;font:900 clamp(3.2rem,8vw,6.6rem)/.9 ui-monospace,monospace;letter-spacing:-.08em}.dashstate{display:grid;grid-template-columns:1fr auto 1fr;padding:11px 15px;border-top:1px solid #243a55;color:var(--muted);font-size:.75rem}.dashstate>*:last-child{text-align:right}.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(300px,.7fr);gap:13px;align-items:start}.col{display:grid;gap:13px}.title{font-weight:900;font-size:.8rem;letter-spacing:.05em}.body{padding:15px}.atbat{display:grid;grid-template-columns:minmax(240px,.8fr) minmax(300px,1.2fr);gap:15px}.field{display:grid;grid-template-columns:1fr 1fr;align-items:center}.bases{width:126px;height:108px;position:relative;margin:auto}.base{position:absolute;width:36px;height:36px;transform:rotate(45deg);border:2px solid #dbe8f5aa;border-radius:4px}.base.on{background:var(--yellow);border-color:var(--yellow);box-shadow:0 0 20px #ffd16655}.b2{left:45px}.b3{left:7px;top:38px}.b1{right:7px;top:38px}.plate{position:absolute;left:49px;bottom:0;width:28px;height:22px;border:2px solid #dbe8f5aa;clip-path:polygon(0 0,100% 0,100% 62%,50% 100%,0 62%)}.counts{display:grid;gap:8px;margin-top:12px}.crow{display:grid;grid-template-columns:58px 1fr;align-items:center}.dots{display:flex;gap:6px}.dot{width:12px;height:12px;border:1px solid var(--line);border-radius:50%}.dot.ball.on{background:#59d982}.dot.strike.on{background:var(--red)}.dot.out.on{background:#fff}.zone{width:150px;height:184px;position:relative;margin:auto;padding:22px}.zgrid{width:100%;height:100%;display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(3,1fr);border:2px solid #e4edf7cc}.zgrid i{border:1px solid #ffffff22}.marker{position:absolute;width:22px;height:22px;border:2px solid white;border-radius:50%;background:var(--green);color:#07111f;display:grid;place-items:center;transform:translate(-50%,-50%);font:900 .65rem ui-monospace,monospace}.desc{text-align:center;color:#cbd8e7;font-size:.78rem;margin-top:5px}.match{display:grid;grid-template-columns:1fr auto 1fr;gap:9px}.player{padding:13px;border:1px solid var(--line);border-radius:14px;background:#ffffff05}.player:last-child{text-align:right}.pname{font-weight:900;font-size:1.05rem;margin:4px 0 10px}.stats{display:flex;gap:12px;flex-wrap:wrap}.player:last-child .stats{justify-content:flex-end}.stat b,.metric b{display:block;font:850 1rem ui-monospace,monospace}.stat small,.metric small{color:var(--muted);font-size:.62rem;text-transform:uppercase}.vs{display:grid;place-items:center;color:var(--muted);font:700 .7rem ui-monospace,monospace}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.metric{padding:11px;border:1px solid var(--line);border-radius:13px;background:#ffffff05;min-width:0}.metric b{font-size:1.1rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:4px}.wp{display:grid;gap:8px}.wplabel{display:flex;justify-content:space-between;font-size:.8rem}.bar{height:14px;border:1px solid var(--line);border-radius:999px;overflow:hidden;display:flex}.awaybar{background:var(--blue)}.homebar{background:var(--green)}table{width:100%;border-collapse:collapse;font-size:.78rem}th,td{padding:9px 5px;text-align:right;border-bottom:1px solid #223852}th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-size:.62rem;text-transform:uppercase}.mix{display:grid;gap:10px}.mrow{display:grid;grid-template-columns:minmax(85px,1fr) 2fr auto;gap:8px;align-items:center;font-size:.75rem}.track{height:8px;background:#ffffff0b;border-radius:999px;overflow:hidden}.fill{height:100%;background:var(--blue)}.order{display:grid;grid-template-columns:1fr 1fr;gap:5px}.orow{display:grid;grid-template-columns:20px 27px minmax(0,1fr) auto;gap:5px;padding:7px;border-radius:9px;font-size:.72rem}.orow.now{background:#5ee6a818;border:1px solid #5ee6a844}.orow span:nth-child(3){white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:800}.mono{font-family:ui-monospace,monospace}.ump{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}@media(max-width:900px){.grid{grid-template-columns:1fr}.right{grid-template-columns:repeat(2,1fr)}.right .card:first-child{grid-column:1/-1}}@media(max-width:700px){.atbat,.field{grid-template-columns:1fr}.score{padding:24px 12px;gap:8px}.scorebox{font-size:clamp(2.8rem,15vw,4.7rem);gap:8px}.name{font-size:.95rem}.record{font-size:.65rem}.metrics{grid-template-columns:repeat(2,1fr)}.match{grid-template-columns:1fr}.player:last-child{text-align:left}.player:last-child .stats{justify-content:flex-start}.right{grid-template-columns:1fr}.right .card:first-child{grid-column:auto}.order{grid-template-columns:1fr}}@media(max-width:450px){.sub,.control label,.delay{display:none}.city{font-size:.55rem}.ump{grid-template-columns:1fr}}
</style></head><body><div class="top"><div class="topin"><div><div class="brand">Ballpark Live</div><div class="sub">scoreboard_data dashboard</div></div><div class="controls"><div class="control"><label>Date</label><input id="date" type="date"></div><div class="control delay"><label>Feed</label><select id="delay"><option value="0">Live</option><option value="15">15s</option><option value="30">30s</option><option value="38">38s</option></select></div><button id="auto" class="active">Auto</button><button id="refresh">↻</button></div></div></div><main class="wrap"><div id="games" class="games"></div><div id="loading" class="loading">Loading games…</div><div id="error" class="error hidden"></div><div id="empty" class="empty hidden">No MLB games found for this date.</div><section id="dash" class="dash hidden"><article class="hero"><div class="meta"><span id="status">Scheduled</span><span id="time">—</span></div><div class="score"><div class="team"><div id="acity" class="city">Away</div><div id="aname" class="name">—</div><div id="arec" class="record">—</div></div><div class="scorebox"><span id="ascore">0</span><span>–</span><span id="hscore">0</span></div><div class="team"><div id="hcity" class="city">Home</div><div id="hname" class="name">—</div><div id="hrec" class="record">—</div></div></div><div class="dashstate"><span id="aextra">0 H · 0 E</span><b id="inning" class="mono">—</b><span id="hextra">0 H · 0 E</span></div></article><div class="grid"><div class="col"><article class="card"><div class="head"><span class="title">LIVE AT-BAT</span><span id="updated" class="eyebrow">Waiting</span></div><div class="body atbat"><div class="field"><div><div class="bases"><div id="b2" class="base b2"></div><div id="b3" class="base b3"></div><div id="b1" class="base b1"></div><div class="plate"></div></div><div class="counts"><div class="crow"><span class="eyebrow">Balls</span><span id="balls" class="dots"></span></div><div class="crow"><span class="eyebrow">Strikes</span><span id="strikes" class="dots"></span></div><div class="crow"><span class="eyebrow">Outs</span><span id="outs" class="dots"></span></div></div></div><div><div class="zone"><div class="zgrid"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><div id="marker" class="marker hidden">•</div></div><div id="pdesc" class="desc">No pitch yet</div></div></div><div><div class="match"><div class="player"><div class="eyebrow">Batter</div><div id="batter" class="pname">—</div><div class="stats"><div class="stat"><b id="bline">—</b><small>Today</small></div><div class="stat"><b id="bavg">—</b><small>AVG</small></div><div class="stat"><b id="bops">—</b><small>OPS</small></div></div></div><div class="vs">VS</div><div class="player"><div class="eyebrow">Pitcher</div><div id="pitcher" class="pname">—</div><div class="stats"><div class="stat"><b id="pip">—</b><small>IP</small></div><div class="stat"><b id="pks">—</b><small>K</small></div><div class="stat"><b id="pcount">—</b><small>S / P</small></div></div></div></div><div class="metrics"><div class="metric"><small>Pitch</small><b id="ptype">—</b></div><div class="metric"><small>Velocity</small><b id="pspeed">—</b></div><div class="metric"><small>Horizontal</small><b id="ph">—</b></div><div class="metric"><small>Induced Vert.</small><b id="pv">—</b></div></div></div></div></article><article class="card"><div class="head"><span class="title">GAME LEVERAGE</span><span class="eyebrow">Live context</span></div><div class="body"><div class="wp"><div class="wplabel"><span id="wal">Away 50%</span><span id="whl">Home 50%</span></div><div class="bar"><div id="wab" class="awaybar" style="width:50%"></div><div id="whb" class="homebar" style="width:50%"></div></div></div><div class="metrics"><div class="metric"><small>Expected Runs</small><b id="re">—</b></div><div class="metric"><small>Chance to Score</small><b id="ts">—</b></div><div class="metric"><small>Exit Velo</small><b id="ev">—</b></div><div class="metric"><small>xBA / xSLG</small><b id="xcontact">—</b></div></div></div></article></div><div class="col right"><article class="card"><div class="head"><span class="title">LINE SCORE</span><span id="gamepk" class="eyebrow">—</span></div><div class="body"><table><thead><tr><th>Team</th><th>R</th><th>H</th><th>E</th><th>LOB</th><th>xBA</th><th>xSLG</th></tr></thead><tbody><tr><td id="lat">AWY</td><td id="lar">0</td><td id="lah">0</td><td id="lae">0</td><td id="lal">0</td><td id="laxba">.000</td><td id="laxslg">.000</td></tr><tr><td id="lht">HME</td><td id="lhr">0</td><td id="lhh">0</td><td id="lhe">0</td><td id="lhl">0</td><td id="lhxba">.000</td><td id="lhxslg">.000</td></tr></tbody></table></div></article><article class="card"><div class="head"><span class="title">PITCH MIX</span><span id="ptotal" class="eyebrow">0 pitches</span></div><div id="mix" class="body mix"><span class="muted">No pitch data yet.</span></div></article><article class="card"><div class="head"><span class="title">BATTING ORDER</span><span id="side" class="eyebrow">At bat</span></div><div id="order" class="body order"><span class="muted">Lineup unavailable.</span></div></article><article class="card"><div class="head"><span class="title">PLATE UMPIRE</span><span id="call" class="eyebrow">Tracking calls</span></div><div class="body ump"><div class="metric"><small>Missed</small><b id="missed">0 / 0</b></div><div class="metric"><small>Run Favor</small><b id="favor">0.00</b></div><div class="metric"><small>Win Prob.</small><b id="uwp">0.0%</b></div></div></article></div></div></section></main>
<script>
const $=id=>document.getElementById(id),S={games:[],gamepk:null,paused:false,timer:null,busy:false};function txt(id,v,f='—'){const e=$(id);if(e)e.textContent=v===null||v===undefined||v===''?f:String(v)}function safe(o,p,f=null){for(const k of p.split('.')){if(!o||typeof o!=='object')return f;o=o[k]}return o??f}function num(v,d=0){v=Number(v);return Number.isFinite(v)?v.toFixed(d):'—'}function pct(v){v=Number(v);return Number.isFinite(v)?(v*100).toFixed(1)+'%':'—'}function dec(v){v=Number(v);if(!Number.isFinite(v))return'—';const s=v.toFixed(3);return s[0]==='0'?s.slice(1):s}function esc(v){return String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]))}async function get(u){const r=await fetch(u,{cache:'no-store'}),j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.error||`Request failed ${r.status}`);return j}function localDate(){const d=new Date(Date.now()-new Date().getTimezoneOffset()*60000);return d.toISOString().slice(0,10)}function kind(s=''){s=s.toLowerCase();if(s.includes('progress')||s.includes('live')||s.includes('inning'))return'live';if(s.includes('final'))return'final';return'scheduled'}function renderGames(){const p=$('games');p.innerHTML='';for(const g of S.games){const b=document.createElement('button');b.className='game '+(Number(g.gamepk)===Number(S.gamepk)?'sel':'');const k=kind(g.status),score=k!=='scheduled';b.innerHTML=`<div class="ghead"><span>${k==='live'?'<i class="live"></i>':''}${esc(g.status||'Scheduled')}</span><span>${esc(g.venue||'')}</span></div><div class="grow"><span>${esc(g.away_abv||g.away)}</span><span>${score?esc(g.away_score??0):''}</span></div><div class="grow"><span>${esc(g.home_abv||g.home)}</span><span>${score?esc(g.home_score??0):''}</span></div>`;b.onclick=()=>select(g.gamepk);p.appendChild(b)}}async function schedule(pref){$('loading').classList.remove('hidden');$('error').classList.add('hidden');$('empty').classList.add('hidden');try{const j=await get('/api/schedule?date='+encodeURIComponent($('date').value));S.games=j.games||[];if(!S.games.length){$('dash').classList.add('hidden');$('empty').classList.remove('hidden');return}const want=S.games.find(g=>Number(g.gamepk)===Number(pref||S.gamepk)),live=S.games.find(g=>kind(g.status)==='live');S.gamepk=(want||live||S.games[0]).gamepk;renderGames();await load(true)}catch(e){$('error').textContent=e.message;$('error').classList.remove('hidden')}finally{$('loading').classList.add('hidden')}}async function select(pk){S.gamepk=Number(pk);renderGames();const u=new URL(location);u.searchParams.set('gamepk',pk);u.searchParams.set('date',$('date').value);history.replaceState({},'',u);await load(true)}function dots(id,n,total,type){const p=$(id);p.innerHTML='';for(let i=0;i<total;i++){const d=document.createElement('i');d.className='dot '+type+(i<n?' on':'');p.appendChild(d)}}function status(g){return({L:'In Progress',F:'Final',P:'Scheduled',D:'Delayed',S:'Suspended / Postponed'})[g.game_state]||g.detailedState||'Game'}function inning(g){if(g.game_state==='F')return'FINAL';if(g.game_state==='P')return'PREGAME';return`${g.inning_state==='B'?'▼':'▲'} ${g.inning||'—'}`}function record(t){return`${t.wins??'—'}-${t.losses??'—'}${t.division_rank?' · #'+t.division_rank:''}`}function ppos(z){return({1:[38,31],2:[50,31],3:[62,31],4:[38,50],5:[50,50],6:[62,50],7:[38,69],8:[50,69],9:[62,69],11:[18,22],12:[82,22],13:[18,78],14:[82,78]})[z]}function render(g){const a=g.away||{},h=g.home||{},m=g.matchup||{},b=m.batter||{},p=m.pitcher||{},pd=g.pitch_details||{};txt('status',status(g));txt('time',g.start_time?new Date(g.start_time).toLocaleString():null);txt('acity',a.location,'Away');txt('aname',a.name,a.abv);txt('arec',record(a));txt('hcity',h.location,'Home');txt('hname',h.name,h.abv);txt('hrec',record(h));txt('ascore',a.runs??0);txt('hscore',h.runs??0);txt('aextra',`${a.hits??0} H · ${a.errors??0} E`);txt('hextra',`${h.hits??0} H · ${h.errors??0} E`);txt('inning',inning(g));txt('updated','Updated '+new Date().toLocaleTimeString());txt('gamepk','Game '+g.gamepk);$('b1').classList.toggle('on',!!(g.runners&1));$('b2').classList.toggle('on',!!(g.runners&2));$('b3').classList.toggle('on',!!(g.runners&4));dots('balls',safe(g,'count.balls',0),3,'ball');dots('strikes',safe(g,'count.strikes',0),2,'strike');dots('outs',safe(g,'count.outs',0),3,'out');txt('batter',b.name);txt('bline',Number.isFinite(Number(b.hits))&&Number.isFinite(Number(b.at_bats))?`${b.hits} / ${b.at_bats}`:'—');txt('bavg',b.avg?String(b.avg).replace(/^0/, ''):'—');txt('bops',b.ops?String(b.ops).replace(/^0/, ''):'—');txt('pitcher',p.name);txt('pip',p.innings_pitched);txt('pks',p.strike_outs);txt('pcount',Number.isFinite(Number(p.strikes))&&Number.isFinite(Number(p.pitches))?`${p.strikes} / ${p.pitches}`:'—');txt('ptype',pd.type==='Four-Seam Fastball'?'4-Seam':pd.type);txt('pspeed',num(pd.speed,1));txt('ph',num(pd.break_horizontal,1));txt('pv',num(pd.break_vertical_induced,1));txt('pdesc',pd.description,'No pitch yet');const pos=ppos(Number(pd.zone)),mk=$('marker');if(pos){mk.classList.remove('hidden');mk.style.left=pos[0]+'%';mk.style.top=pos[1]+'%';mk.textContent=pd.at_bat_pitch_count||'•'}else mk.classList.add('hidden');let aw=Number(safe(g,'win_probability.away',.5)),hw=Number(safe(g,'win_probability.home',.5)),t=aw+hw||1;aw/=t;hw/=t;$('wab').style.width=aw*100+'%';$('whb').style.width=hw*100+'%';txt('wal',`${a.abv||'Away'} ${pct(aw)}`);txt('whl',`${h.abv||'Home'} ${pct(hw)}`);txt('re',num(safe(g,'run_expectancy.average_runs'),2));txt('ts',pct(safe(g,'run_expectancy.to_score')));txt('ev',num(safe(g,'hit_details.exit_velo'),1));txt('xcontact',`${dec(safe(g,'hit_details.xba'))} / ${dec(safe(g,'hit_details.xslg'))}`);line('la',a);line('lh',h);txt('lat',a.abv);txt('lht',h.abv);mix(g.pitch_counts||{});order(g.batting_order||{},g.inning_state,a,h);const u=g.umpire||{};txt('missed',`${u.num_missed??0} / ${u.total_calls??0}`);txt('favor',Math.abs(Number(u.home_favor||0)).toFixed(2));txt('uwp',Math.abs(Number(u.home_wpa||0)*100).toFixed(1)+'%');txt('call',pd.umpire_missed_call?'Latest call missed':'Tracking calls');$('dash').classList.remove('hidden')}function line(pre,t){txt(pre+'r',t.runs??0);txt(pre+'h',t.hits??0);txt(pre+'e',t.errors??0);txt(pre+'l',t.left_on_base??0);txt(pre+'xba',dec(t.xba));txt(pre+'xslg',dec(t.xslg))}function mix(raw){const rows=Object.entries(raw).map(([name,v])=>typeof v==='number'?{name,total:v,strikes:null}:{name,total:Number(v?.total??v?.count??0),strikes:v?.strikes}).filter(x=>x.name&&x.total>0).sort((a,b)=>b.total-a.total).slice(0,7),p=$('mix'),total=rows.reduce((s,x)=>s+x.total,0);txt('ptotal',total+' pitches');p.innerHTML=rows.length?'':'<span class="muted">No pitch data yet.</span>';for(const r of rows){const d=document.createElement('div');d.className='mrow';d.innerHTML=`<span>${esc(r.name.replace('Four-Seam Fastball','4-Seam'))}</span><span class="track"><i class="fill" style="width:${r.total/total*100}%"></i></span><span class="mono">${r.strikes==null?r.total:r.strikes+'/'+r.total}</span>`;p.appendChild(d)}}function order(o,state,a,h){const rows=Array.isArray(o.batting_order)?o.batting_order:[],p=$('order');txt('side',(state==='B'?h.abv:a.abv)+' batting');p.innerHTML=rows.length?'':'<span class="muted">Lineup unavailable.</span>';for(const r of rows){const d=document.createElement('div');d.className='orow '+(Number(r.order)===Number(o.at_bat_index)?'now':'');d.innerHTML=`<span class="mono">${esc(r.order)}</span><span class="mono">${esc(r.position||'')}</span><span>${esc(r.last_name||'—')}</span><span class="mono">${esc(String(r.ops||'—').replace(/^0/,''))}</span>`;p.appendChild(d)}}async function load(force=false){if(!S.gamepk||S.busy)return;S.busy=true;try{const j=await get(`/api/game?gamepk=${S.gamepk}&delay=${$('delay').value}`);render(j.game);const g=S.games.find(x=>Number(x.gamepk)===Number(S.gamepk));if(g){g.away_score=j.game.away?.runs;g.home_score=j.game.home?.runs;g.status=status(j.game);renderGames()}start()}catch(e){$('error').textContent=e.message;$('error').classList.remove('hidden')}finally{S.busy=false}}function start(){clearInterval(S.timer);if(!S.paused)S.timer=setInterval(()=>load(false),5000)}$('date').onchange=()=>schedule();$('delay').onchange=()=>load(true);$('refresh').onclick=()=>load(true);$('auto').onclick=()=>{S.paused=!S.paused;$('auto').classList.toggle('active',!S.paused);$('auto').textContent=S.paused?'Paused':'Auto';start()};const q=new URLSearchParams(location.search);$('date').value=q.get('date')||localDate();schedule(q.get('gamepk'));
</script></body></html>'''

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SCHEDULE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
GAME_CACHE: dict[tuple[int, int], tuple[float, dict[str, Any]]] = {}


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [json_safe(v) for v in value]
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


def game_payload(gamepk: int, delay: int) -> dict[str, Any]:
    key = (gamepk, delay)
    now = time.monotonic()
    cached = GAME_CACHE.get(key)
    if cached and now - cached[0] < 2:
        return cached[1]
    payload = {"game": json_safe(ScoreboardData(gamepk=gamepk, delay_seconds=delay).to_dict())}
    GAME_CACHE[key] = (now, payload)
    return payload


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.send_data(HTML.encode(), "text/html; charset=utf-8")
                return
            if parsed.path == "/health":
                self.send_json({"ok": True})
                return
            query = parse_qs(parsed.query)
            if parsed.path == "/api/schedule":
                day = query.get("date", [date.today().isoformat()])[0]
                if not DATE_RE.fullmatch(day):
                    self.send_json({"error": "date must use YYYY-MM-DD"}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json(schedule_payload(day))
                return
            if parsed.path == "/api/game":
                try:
                    gamepk = int(query.get("gamepk", [""])[0])
                    delay = int(query.get("delay", ["0"])[0])
                except ValueError:
                    self.send_json({"error": "gamepk and delay must be integers"}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json(game_payload(gamepk, delay))
                return
            self.send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.send_json({"error": f"Unable to load MLB data: {exc}"}, HTTPStatus.BAD_GATEWAY)

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_data(json.dumps(json_safe(payload), allow_nan=False).encode(), "application/json; charset=utf-8", status)

    def send_data(self, data: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the at_bat live dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Ballpark Live: http://127.0.0.1:{args.port}")
    print(f"Phone on same network: http://<computer-lan-ip>:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
