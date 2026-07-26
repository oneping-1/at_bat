#!/usr/bin/env python3
"""Single-file responsive MLB dashboard powered by ScoreboardData.

Run from the at_bat repository root:
    python scoreboard_dashboard.py

Open http://127.0.0.1:8000. For another device on the same network, use
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
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
  <meta name="theme-color" content="#07111f">
  <title>Ballpark Live</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07111f;
      --panel: #0d1d31;
      --panel2: #142844;
      --line: #29405d;
      --text: #f4f8ff;
      --muted: #8fa5bf;
      --green: #5ee6a8;
      --blue: #58a9ff;
      --red: #ff6878;
      --yellow: #ffd166;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-width: 320px;
      background: radial-gradient(circle at 10% 0, #16375b 0, transparent 30rem),
                  linear-gradient(#0a1728, #07111f 35rem);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    button, input { font: inherit; }
    .wrap { width: min(1320px, 100%); margin: auto; padding: 0 14px 40px; }
    .top {
      position: sticky;
      top: 0;
      z-index: 5;
      margin: 0 -14px;
      padding: 12px 14px;
      background: #07111fdd;
      backdrop-filter: blur(16px);
      border-bottom: 1px solid #20344e;
    }
    .topin { width: min(1292px, 100%); margin: auto; display: flex; align-items: center; gap: 10px; }
    .brand { font-weight: 900; letter-spacing: -.03em; }
    .sub, .muted { color: var(--muted); }
    .sub { font-size: .7rem; }
    .controls { margin-left: auto; display: flex; gap: 7px; flex-wrap: wrap; }
    .control, button {
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #ffffff08;
      color: var(--text);
      min-height: 38px;
    }
    .control { display: flex; align-items: center; gap: 7px; padding: 5px 9px; }
    .control label { font-size: .65rem; color: var(--muted); text-transform: uppercase; font-weight: 800; }
    .control input { border: 0; background: transparent; color: var(--text); outline: 0; min-width: 0; }
    #date { width: 128px; }
    #delay { width: 70px; text-align: right; }
    button { padding: 0 12px; cursor: pointer; font-weight: 800; }
    button.active { background: var(--green); color: #07111f; border-color: transparent; }
    .games { display: flex; gap: 9px; overflow-x: auto; padding: 16px 0 10px; }
    .game { flex: 0 0 205px; text-align: left; padding: 10px 12px; background: #0c1b2ddd; }
    .game.sel { border-color: var(--green); box-shadow: inset 0 0 0 1px #5ee6a844; }
    .ghead, .grow { display: flex; justify-content: space-between; gap: 8px; }
    .ghead { font-size: .66rem; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }
    .grow { font-weight: 800; line-height: 1.5; }
    .live { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--red); margin-right: 5px; }
    .loading, .error, .empty { padding: 28px; text-align: center; border: 1px solid var(--line); border-radius: 20px; background: var(--panel); }
    .hidden { display: none !important; }
    .dash { display: grid; gap: 13px; }
    .hero, .card { border: 1px solid var(--line); background: #0d1d31e8; border-radius: 21px; overflow: hidden; }
    .hero { background: radial-gradient(circle at 50% 0, #1b406666, transparent 55%), linear-gradient(135deg, #112640, #0a1728); }
    .meta, .head { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 11px 15px; border-bottom: 1px solid #243a55; color: var(--muted); font-size: .75rem; }
    .score { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: clamp(10px, 4vw, 48px); padding: clamp(24px, 4vw, 42px); }
    .team:last-child { text-align: right; }
    .city, .eyebrow { font-size: .66rem; letter-spacing: .11em; text-transform: uppercase; color: var(--muted); font-weight: 800; }
    .name { font-size: clamp(1rem, 2.5vw, 1.8rem); font-weight: 900; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .record { font-size: .75rem; color: var(--muted); margin-top: 5px; }
    .scorebox { display: flex; gap: 14px; align-items: center; font: 900 clamp(3.2rem, 8vw, 6.6rem)/.9 ui-monospace, monospace; letter-spacing: -.08em; }
    .dashstate { display: grid; grid-template-columns: 1fr auto 1fr; padding: 11px 15px; border-top: 1px solid #243a55; color: var(--muted); font-size: .75rem; }
    .dashstate > *:last-child { text-align: right; }
    .grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(300px, .7fr); gap: 13px; align-items: start; }
    .col { display: grid; gap: 13px; }
    .title { font-weight: 900; font-size: .8rem; letter-spacing: .05em; }
    .body { padding: 15px; }
    .atbat { display: grid; grid-template-columns: minmax(240px, .8fr) minmax(300px, 1.2fr); gap: 15px; }
    .field { display: grid; grid-template-columns: 1fr 1fr; align-items: center; }
    .bases { width: 126px; height: 108px; position: relative; margin: auto; }
    .base { position: absolute; width: 36px; height: 36px; transform: rotate(45deg); border: 2px solid #dbe8f5aa; border-radius: 4px; }
    .base.on { background: var(--yellow); border-color: var(--yellow); box-shadow: 0 0 20px #ffd16655; }
    .b2 { left: 45px; }
    .b3 { left: 7px; top: 38px; }
    .b1 { right: 7px; top: 38px; }
    .plate { position: absolute; left: 49px; bottom: 0; width: 28px; height: 22px; border: 2px solid #dbe8f5aa; clip-path: polygon(0 0, 100% 0, 100% 62%, 50% 100%, 0 62%); }
    .counts { display: grid; gap: 8px; margin-top: 12px; }
    .crow { display: grid; grid-template-columns: 58px 1fr; align-items: center; }
    .dots { display: flex; gap: 6px; }
    .dot { width: 12px; height: 12px; border: 1px solid var(--line); border-radius: 50%; }
    .dot.ball.on { background: #59d982; }
    .dot.strike.on { background: var(--red); }
    .dot.out.on { background: #fff; }
    .zone { width: 150px; height: 184px; position: relative; margin: auto; padding: 22px; }
    .zgrid { width: 100%; height: 100%; display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr); border: 2px solid #e4edf7cc; }
    .zgrid i { border: 1px solid #ffffff22; }
    .marker { position: absolute; width: 22px; height: 22px; border: 2px solid white; border-radius: 50%; background: var(--green); color: #07111f; display: grid; place-items: center; transform: translate(-50%, -50%); font: 900 .65rem ui-monospace, monospace; }
    .desc { text-align: center; color: #cbd8e7; font-size: .78rem; margin-top: 5px; }
    .match { display: grid; grid-template-columns: 1fr auto 1fr; gap: 9px; }
    .player { padding: 13px; border: 1px solid var(--line); border-radius: 14px; background: #ffffff05; }
    .player:last-child { text-align: right; }
    .pname { font-weight: 900; font-size: 1.05rem; margin: 4px 0 10px; }
    .stats { display: flex; gap: 12px; flex-wrap: wrap; }
    .player:last-child .stats { justify-content: flex-end; }
    .stat b, .metric b { display: block; font: 850 1rem ui-monospace, monospace; }
    .stat small, .metric small { color: var(--muted); font-size: .62rem; text-transform: uppercase; }
    .vs { display: grid; place-items: center; color: var(--muted); font: 700 .7rem ui-monospace, monospace; }
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 12px; }
    .metric { padding: 11px; border: 1px solid var(--line); border-radius: 13px; background: #ffffff05; min-width: 0; }
    .metric b { font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 4px; }
    .wp { display: grid; gap: 8px; }
    .wplabel { display: flex; justify-content: space-between; font-size: .8rem; }
    .bar { height: 14px; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; display: flex; }
    .awaybar { background: var(--blue); }
    .homebar { background: var(--green); }
    table { width: 100%; border-collapse: collapse; font-size: .78rem; }
    th, td { padding: 9px 5px; text-align: right; border-bottom: 1px solid #223852; }
    th:first-child, td:first-child { text-align: left; }
    th { color: var(--muted); font-size: .62rem; text-transform: uppercase; }
    .mix { display: grid; gap: 10px; }
    .mix-head, .mrow { display: grid; grid-template-columns: minmax(90px, 1fr) minmax(100px, 2fr) 58px 64px; gap: 9px; align-items: center; }
    .mix-head { color: var(--muted); font-size: .6rem; text-transform: uppercase; font-weight: 800; }
    .mrow { font-size: .75rem; }
    .track { display: block; width: 100%; height: 10px; background: #ffffff12; border: 1px solid #ffffff12; border-radius: 999px; overflow: hidden; }
    .fill { display: block; height: 100%; min-width: 2px; background: linear-gradient(90deg, var(--blue), var(--green)); border-radius: inherit; }
    .mix-num { text-align: right; font-family: ui-monospace, monospace; }
    .order { display: grid; grid-template-columns: 1fr; gap: 5px; }
    .orow { display: grid; grid-template-columns: 20px 32px minmax(0, 1fr) 54px; gap: 7px; padding: 8px 9px; border-radius: 9px; font-size: .76rem; }
    .orow.now { background: #5ee6a818; border: 1px solid #5ee6a844; }
    .orow span:nth-child(3) { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 800; }
    .mono { font-family: ui-monospace, monospace; }
    .ump { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .right { grid-template-columns: repeat(2, 1fr); }
      .right .card:first-child { grid-column: 1 / -1; }
    }
    @media (max-width: 700px) {
      .atbat, .field { grid-template-columns: 1fr; }
      .score { padding: 24px 12px; gap: 8px; }
      .scorebox { font-size: clamp(2.8rem, 15vw, 4.7rem); gap: 8px; }
      .name { font-size: .95rem; }
      .record { font-size: .65rem; }
      .metrics { grid-template-columns: repeat(2, 1fr); }
      .match { grid-template-columns: 1fr; }
      .player:last-child { text-align: left; }
      .player:last-child .stats { justify-content: flex-start; }
      .right { grid-template-columns: 1fr; }
      .right .card:first-child { grid-column: auto; }
    }
    @media (max-width: 520px) {
      .sub, .control label { display: none; }
      #date { width: 116px; }
      #delay { width: 58px; }
      .city { font-size: .55rem; }
      .ump { grid-template-columns: 1fr; }
      .mix-head, .mrow { grid-template-columns: minmax(75px, 1fr) minmax(75px, 1.4fr) 46px 56px; gap: 6px; }
    }
  </style>
</head>
<body>
  <div class="top">
    <div class="topin">
      <div>
        <div class="brand">Ballpark Live</div>
        <div class="sub">scoreboard_data dashboard</div>
      </div>
      <div class="controls">
        <div class="control"><label for="date">Date</label><input id="date" type="date"></div>
        <div class="control"><label for="delay">Delay</label><input id="delay" type="number" inputmode="numeric" min="0" step="1" value="0" aria-label="Feed delay in seconds"><span class="sub">sec</span></div>
        <button id="auto" class="active" type="button">Auto</button>
        <button id="refresh" type="button" aria-label="Refresh">↻</button>
      </div>
    </div>
  </div>

  <main class="wrap">
    <div id="games" class="games"></div>
    <div id="loading" class="loading">Loading games…</div>
    <div id="error" class="error hidden"></div>
    <div id="empty" class="empty hidden">No MLB games found for this date.</div>

    <section id="dash" class="dash hidden">
      <article class="hero">
        <div class="meta"><span id="status">Scheduled</span><span id="time">—</span></div>
        <div class="score">
          <div class="team">
            <div id="acity" class="city">Away</div><div id="aname" class="name">—</div><div id="arec" class="record">—</div>
          </div>
          <div class="scorebox"><span id="ascore">0</span><span>–</span><span id="hscore">0</span></div>
          <div class="team">
            <div id="hcity" class="city">Home</div><div id="hname" class="name">—</div><div id="hrec" class="record">—</div>
          </div>
        </div>
        <div class="dashstate"><span id="aextra">0 H · 0 E</span><b id="inning" class="mono">—</b><span id="hextra">0 H · 0 E</span></div>
      </article>

      <div class="grid">
        <div class="col">
          <article class="card">
            <div class="head"><span class="title">LIVE AT-BAT</span><span id="updated" class="eyebrow">Waiting</span></div>
            <div class="body atbat">
              <div class="field">
                <div>
                  <div class="bases"><div id="b2" class="base b2"></div><div id="b3" class="base b3"></div><div id="b1" class="base b1"></div><div class="plate"></div></div>
                  <div class="counts">
                    <div class="crow"><span class="eyebrow">Balls</span><span id="balls" class="dots"></span></div>
                    <div class="crow"><span class="eyebrow">Strikes</span><span id="strikes" class="dots"></span></div>
                    <div class="crow"><span class="eyebrow">Outs</span><span id="outs" class="dots"></span></div>
                  </div>
                </div>
                <div>
                  <div class="zone"><div class="zgrid"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div><div id="marker" class="marker hidden">•</div></div>
                  <div id="pdesc" class="desc">No pitch yet</div>
                </div>
              </div>
              <div>
                <div class="match">
                  <div class="player"><div class="eyebrow">Batter</div><div id="batter" class="pname">—</div><div class="stats"><div class="stat"><b id="bline">—</b><small>Today</small></div><div class="stat"><b id="bavg">—</b><small>AVG</small></div><div class="stat"><b id="bops">—</b><small>OPS</small></div></div></div>
                  <div class="vs">VS</div>
                  <div class="player"><div class="eyebrow">Pitcher</div><div id="pitcher" class="pname">—</div><div class="stats"><div class="stat"><b id="pip">—</b><small>IP</small></div><div class="stat"><b id="pks">—</b><small>K</small></div><div class="stat"><b id="pcount">—</b><small>S / P</small></div></div></div>
                </div>
                <div class="metrics">
                  <div class="metric"><small>Pitch</small><b id="ptype">—</b></div>
                  <div class="metric"><small>Velocity</small><b id="pspeed">—</b></div>
                  <div class="metric"><small>Horizontal</small><b id="ph">—</b></div>
                  <div class="metric"><small>Induced Vert.</small><b id="pv">—</b></div>
                </div>
              </div>
            </div>
          </article>

          <article class="card">
            <div class="head"><span class="title">GAME LEVERAGE</span><span id="gamepk" class="eyebrow">Game</span></div>
            <div class="body">
              <div class="wp"><div class="wplabel"><span id="wal">Away 50%</span><span id="whl">Home 50%</span></div><div class="bar"><div id="wab" class="awaybar" style="width:50%"></div><div id="whb" class="homebar" style="width:50%"></div></div></div>
              <div class="metrics"><div class="metric"><small>Expected runs</small><b id="re">—</b></div><div class="metric"><small>Chance to score</small><b id="ts">—</b></div><div class="metric"><small>Exit velocity</small><b id="ev">—</b></div><div class="metric"><small>xBA / xSLG</small><b id="xcontact">—</b></div></div>
            </div>
          </article>

          <article class="card">
            <div class="head"><span class="title">LINE SCORE</span><span class="eyebrow">R H E LOB xBA xSLG</span></div>
            <div class="body">
              <table><thead><tr><th>Team</th><th>R</th><th>H</th><th>E</th><th>LOB</th><th>xBA</th><th>xSLG</th></tr></thead><tbody>
                <tr><td id="lat">Away</td><td id="lar">0</td><td id="lah">0</td><td id="lae">0</td><td id="lal">0</td><td id="laxba">—</td><td id="laxslg">—</td></tr>
                <tr><td id="lht">Home</td><td id="lhr">0</td><td id="lhh">0</td><td id="lhe">0</td><td id="lhl">0</td><td id="lhxba">—</td><td id="lhxslg">—</td></tr>
              </tbody></table>
            </div>
          </article>
        </div>

        <div class="col right">
          <article class="card">
            <div class="head"><span class="title">PITCH MIX</span><span id="ptotal" class="eyebrow">0 pitches</span></div>
            <div class="body mix">
              <div class="mix-head"><span>Pitch</span><span>Usage</span><span style="text-align:right">S/P</span><span style="text-align:right">Avg mph</span></div>
              <div id="mix" class="mix"></div>
            </div>
          </article>

          <article class="card">
            <div class="head"><span class="title">BATTING ORDER</span><span id="side" class="eyebrow">Batting</span></div>
            <div id="order" class="body order"></div>
          </article>

          <article class="card">
            <div class="head"><span class="title">UMPIRE IMPACT</span><span id="call" class="eyebrow">Tracking calls</span></div>
            <div class="body ump">
              <div class="metric"><small>Missed</small><b id="missed">0 / 0</b></div>
              <div class="metric"><small>Run favor</small><b id="favor">0.00</b></div>
              <div class="metric"><small>Win prob.</small><b id="uwp">0.0%</b></div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </main>

  <script>
    const $ = id => document.getElementById(id);
    const S = {games: [], gamepk: null, paused: false, timer: null, busy: false};

    function txt(id, value, fallback = '—') {
      const element = $(id);
      if (element) element.textContent = value === null || value === undefined || value === '' ? fallback : String(value);
    }
    function safe(object, path, fallback = null) {
      for (const key of path.split('.')) {
        if (!object || typeof object !== 'object') return fallback;
        object = object[key];
      }
      return object ?? fallback;
    }
    function num(value, digits = 0) {
      value = Number(value);
      return Number.isFinite(value) ? value.toFixed(digits) : '—';
    }
    function pct(value) {
      value = Number(value);
      return Number.isFinite(value) ? (value * 100).toFixed(1) + '%' : '—';
    }
    function dec(value) {
      value = Number(value);
      if (!Number.isFinite(value)) return '—';
      const formatted = value.toFixed(3);
      return formatted[0] === '0' ? formatted.slice(1) : formatted;
    }
    function esc(value) {
      return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    }
    async function get(url) {
      const response = await fetch(url, {cache: 'no-store'});
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw Error(body.error || `Request failed ${response.status}`);
      return body;
    }
    function localDate() {
      const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000);
      return now.toISOString().slice(0, 10);
    }
    function delayValue() {
      const parsed = Math.floor(Number($('delay').value));
      const delay = Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
      $('delay').value = delay;
      return delay;
    }
    function kind(status = '') {
      status = status.toLowerCase();
      if (status.includes('progress') || status.includes('live') || status.includes('inning')) return 'live';
      if (status.includes('final')) return 'final';
      return 'scheduled';
    }
    function renderGames() {
      const panel = $('games');
      panel.innerHTML = '';
      for (const game of S.games) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'game ' + (Number(game.gamepk) === Number(S.gamepk) ? 'sel' : '');
        const state = kind(game.status);
        const showScore = state !== 'scheduled';
        button.innerHTML = `<div class="ghead"><span>${state === 'live' ? '<i class="live"></i>' : ''}${esc(game.status || 'Scheduled')}</span><span>${esc(game.venue || '')}</span></div><div class="grow"><span>${esc(game.away_abv || game.away)}</span><span>${showScore ? esc(game.away_score ?? 0) : ''}</span></div><div class="grow"><span>${esc(game.home_abv || game.home)}</span><span>${showScore ? esc(game.home_score ?? 0) : ''}</span></div>`;
        button.addEventListener('click', () => select(game.gamepk));
        panel.appendChild(button);
      }
    }
    async function schedule(preferred) {
      $('loading').classList.remove('hidden');
      $('error').classList.add('hidden');
      $('empty').classList.add('hidden');
      try {
        const response = await get('/api/schedule?date=' + encodeURIComponent($('date').value));
        S.games = response.games || [];
        if (!S.games.length) {
          $('dash').classList.add('hidden');
          $('empty').classList.remove('hidden');
          return;
        }
        const wanted = S.games.find(game => Number(game.gamepk) === Number(preferred || S.gamepk));
        const live = S.games.find(game => kind(game.status) === 'live');
        S.gamepk = (wanted || live || S.games[0]).gamepk;
        renderGames();
        await load(true);
      } catch (error) {
        $('error').textContent = error.message;
        $('error').classList.remove('hidden');
      } finally {
        $('loading').classList.add('hidden');
      }
    }
    async function select(gamepk) {
      S.gamepk = Number(gamepk);
      renderGames();
      const url = new URL(location);
      url.searchParams.set('gamepk', gamepk);
      url.searchParams.set('date', $('date').value);
      history.replaceState({}, '', url);
      await load(true);
    }
    function dots(id, active, total, type) {
      const panel = $(id);
      panel.innerHTML = '';
      for (let index = 0; index < total; index++) {
        const dot = document.createElement('i');
        dot.className = 'dot ' + type + (index < active ? ' on' : '');
        panel.appendChild(dot);
      }
    }
    function status(game) {
      return ({L:'In Progress', F:'Final', P:'Scheduled', D:'Delayed', S:'Suspended / Postponed'})[game.game_state] || game.detailedState || 'Game';
    }
    function inning(game) {
      if (game.game_state === 'F') return 'FINAL';
      if (game.game_state === 'P') return 'PREGAME';
      return `${game.inning_state === 'B' ? '▼' : '▲'} ${game.inning || '—'}`;
    }
    function record(team) {
      return `${team.wins ?? '—'}-${team.losses ?? '—'}${team.division_rank ? ' · #' + team.division_rank : ''}`;
    }
    function pitchPosition(zone) {
      return ({1:[38,31],2:[50,31],3:[62,31],4:[38,50],5:[50,50],6:[62,50],7:[38,69],8:[50,69],9:[62,69],11:[18,22],12:[82,22],13:[18,78],14:[82,78]})[zone];
    }
    function render(game) {
      const away = game.away || {};
      const home = game.home || {};
      const matchup = game.matchup || {};
      const batter = matchup.batter || {};
      const pitcher = matchup.pitcher || {};
      const pitch = game.pitch_details || {};

      txt('status', status(game));
      txt('time', game.start_time ? new Date(game.start_time).toLocaleString() : null);
      txt('acity', away.location, 'Away'); txt('aname', away.name, away.abv); txt('arec', record(away));
      txt('hcity', home.location, 'Home'); txt('hname', home.name, home.abv); txt('hrec', record(home));
      txt('ascore', away.runs ?? 0); txt('hscore', home.runs ?? 0);
      txt('aextra', `${away.hits ?? 0} H · ${away.errors ?? 0} E`);
      txt('hextra', `${home.hits ?? 0} H · ${home.errors ?? 0} E`);
      txt('inning', inning(game));
      txt('updated', 'Updated ' + new Date().toLocaleTimeString());
      txt('gamepk', 'Game ' + game.gamepk);

      $('b1').classList.toggle('on', !!(game.runners & 1));
      $('b2').classList.toggle('on', !!(game.runners & 2));
      $('b3').classList.toggle('on', !!(game.runners & 4));
      dots('balls', safe(game, 'count.balls', 0), 3, 'ball');
      dots('strikes', safe(game, 'count.strikes', 0), 2, 'strike');
      dots('outs', safe(game, 'count.outs', 0), 3, 'out');

      txt('batter', batter.name);
      txt('bline', Number.isFinite(Number(batter.hits)) && Number.isFinite(Number(batter.at_bats)) ? `${batter.hits} / ${batter.at_bats}` : '—');
      txt('bavg', batter.avg ? String(batter.avg).replace(/^0/, '') : '—');
      txt('bops', batter.ops ? String(batter.ops).replace(/^0/, '') : '—');
      txt('pitcher', pitcher.name);
      txt('pip', pitcher.innings_pitched);
      txt('pks', pitcher.strike_outs);
      txt('pcount', Number.isFinite(Number(pitcher.strikes)) && Number.isFinite(Number(pitcher.pitches)) ? `${pitcher.strikes} / ${pitcher.pitches}` : '—');
      txt('ptype', pitch.type === 'Four-Seam Fastball' ? '4-Seam' : pitch.type);
      txt('pspeed', Number.isFinite(Number(pitch.speed)) ? num(pitch.speed, 1) + ' mph' : '—');
      txt('ph', Number.isFinite(Number(pitch.break_horizontal)) ? num(pitch.break_horizontal, 1) + ' in' : '—');
      txt('pv', Number.isFinite(Number(pitch.break_vertical_induced)) ? num(pitch.break_vertical_induced, 1) + ' in' : '—');
      txt('pdesc', pitch.description, 'No pitch yet');

      const position = pitchPosition(Number(pitch.zone));
      const marker = $('marker');
      if (position) {
        marker.classList.remove('hidden');
        marker.style.left = position[0] + '%';
        marker.style.top = position[1] + '%';
        marker.textContent = pitch.at_bat_pitch_count || '•';
      } else {
        marker.classList.add('hidden');
      }

      let awayWin = Number(safe(game, 'win_probability.away', .5));
      let homeWin = Number(safe(game, 'win_probability.home', .5));
      const totalWin = awayWin + homeWin || 1;
      awayWin /= totalWin;
      homeWin /= totalWin;
      $('wab').style.width = awayWin * 100 + '%';
      $('whb').style.width = homeWin * 100 + '%';
      txt('wal', `${away.abv || 'Away'} ${pct(awayWin)}`);
      txt('whl', `${home.abv || 'Home'} ${pct(homeWin)}`);
      txt('re', num(safe(game, 'run_expectancy.average_runs'), 2));
      txt('ts', pct(safe(game, 'run_expectancy.to_score')));
      txt('ev', Number.isFinite(Number(safe(game, 'hit_details.exit_velo'))) ? num(safe(game, 'hit_details.exit_velo'), 1) + ' mph' : '—');
      txt('xcontact', `${dec(safe(game, 'hit_details.xba'))} / ${dec(safe(game, 'hit_details.xslg'))}`);

      line('la', away); line('lh', home); txt('lat', away.abv); txt('lht', home.abv);
      renderMix(game.pitch_counts || {});
      renderOrder(game.batting_order || {}, game.inning_state, away, home);

      const umpire = game.umpire || {};
      txt('missed', `${umpire.num_missed ?? 0} / ${umpire.total_calls ?? 0}`);
      txt('favor', Math.abs(Number(umpire.home_favor || 0)).toFixed(2));
      txt('uwp', Math.abs(Number(umpire.home_wpa || 0) * 100).toFixed(1) + '%');
      txt('call', pitch.umpire_missed_call ? 'Latest call missed' : 'Tracking calls');
      $('dash').classList.remove('hidden');
    }
    function line(prefix, team) {
      txt(prefix + 'r', team.runs ?? 0); txt(prefix + 'h', team.hits ?? 0); txt(prefix + 'e', team.errors ?? 0); txt(prefix + 'l', team.left_on_base ?? 0);
      txt(prefix + 'xba', dec(team.xba)); txt(prefix + 'xslg', dec(team.xslg));
    }
    function renderMix(raw) {
      const rows = Object.entries(raw).map(([name, value]) => {
        if (typeof value === 'number') return {name, total: Number(value), strikes: null, avgSpeed: null};
        return {
          name,
          total: Number(value?.total ?? value?.count ?? 0),
          strikes: Number.isFinite(Number(value?.strikes)) ? Number(value.strikes) : null,
          avgSpeed: Number.isFinite(Number(value?.avg_speed)) ? Number(value.avg_speed) : null
        };
      }).filter(row => row.name && row.total > 0).sort((a, b) => b.total - a.total).slice(0, 7);

      const panel = $('mix');
      const total = rows.reduce((sum, row) => sum + row.total, 0);
      txt('ptotal', total + (total === 1 ? ' pitch' : ' pitches'));
      panel.innerHTML = rows.length ? '' : '<span class="muted">No pitch data yet.</span>';

      for (const row of rows) {
        const percent = total ? (row.total / total * 100) : 0;
        const displayName = row.name.replace('Four-Seam Fastball', '4-Seam').replace('Knuckle Curve', 'Knuckle');
        const item = document.createElement('div');
        item.className = 'mrow';
        item.innerHTML = `<span>${esc(displayName)}</span><span class="track" title="${percent.toFixed(1)}% usage"><span class="fill" style="width:${percent.toFixed(2)}%"></span></span><span class="mix-num">${row.strikes === null ? row.total : row.strikes + '/' + row.total}</span><span class="mix-num">${row.avgSpeed === null ? '—' : row.avgSpeed.toFixed(1)}</span>`;
        panel.appendChild(item);
      }
    }
    function renderOrder(order, inningState, away, home) {
      const rows = Array.isArray(order.batting_order) ? order.batting_order : [];
      const panel = $('order');
      txt('side', (inningState === 'B' ? home.abv : away.abv) + ' batting');
      panel.innerHTML = rows.length ? '' : '<span class="muted">Lineup unavailable.</span>';
      for (const row of rows) {
        const item = document.createElement('div');
        item.className = 'orow ' + (Number(row.order) === Number(order.at_bat_index) ? 'now' : '');
        item.innerHTML = `<span class="mono">${esc(row.order)}</span><span class="mono">${esc(row.position || '')}</span><span>${esc(row.last_name || '—')}</span><span class="mono">${esc(String(row.ops || '—').replace(/^0/, ''))}</span>`;
        panel.appendChild(item);
      }
    }
    async function load() {
      if (!S.gamepk || S.busy) return;
      S.busy = true;
      try {
        const response = await get(`/api/game?gamepk=${S.gamepk}&delay=${delayValue()}`);
        render(response.game);
        const summary = S.games.find(game => Number(game.gamepk) === Number(S.gamepk));
        if (summary) {
          summary.away_score = response.game.away?.runs;
          summary.home_score = response.game.home?.runs;
          summary.status = status(response.game);
          renderGames();
        }
        start();
      } catch (error) {
        $('error').textContent = error.message;
        $('error').classList.remove('hidden');
      } finally {
        S.busy = false;
      }
    }
    function start() {
      clearInterval(S.timer);
      if (!S.paused) S.timer = setInterval(load, 5000);
    }

    $('date').addEventListener('change', () => schedule());
    $('delay').addEventListener('change', load);
    $('delay').addEventListener('keydown', event => { if (event.key === 'Enter') load(); });
    $('refresh').addEventListener('click', load);
    $('auto').addEventListener('click', () => {
      S.paused = !S.paused;
      $('auto').classList.toggle('active', !S.paused);
      $('auto').textContent = S.paused ? 'Paused' : 'Auto';
      start();
    });

    const query = new URLSearchParams(location.search);
    $('date').value = query.get('date') || localDate();
    $('delay').value = query.get('delay') || '0';
    schedule(query.get('gamepk'));
  </script>
</body>
</html>'''

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SCHEDULE_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
GAME_CACHE: dict[tuple[int, int], tuple[float, dict[str, Any]]] = {}


def json_safe(value: Any) -> Any:
    """Convert pandas/numpy values and non-finite floats into JSON-safe values."""
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


def game_payload(gamepk: int, delay: int) -> dict[str, Any]:
    key = (gamepk, delay)
    now = time.monotonic()
    cached = GAME_CACHE.get(key)
    if cached and now - cached[0] < 2:
        return cached[1]

    scoreboard = ScoreboardData(gamepk=gamepk, delay_seconds=delay)
    payload = {"game": json_safe(scoreboard.to_dict())}
    GAME_CACHE[key] = (now, payload)
    return payload


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "BallparkLive/1.1"

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
        except Exception as error:  # Keep API failures readable in the browser.
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
