# -*- coding: utf-8 -*-
"""SQLite veritabanı: kamera, aydınlatma ve kalibrasyon preset'leri."""

import json
import sqlite3
from pathlib import Path

from config import DB_PATH

def _get_conn():
    path = Path(DB_PATH)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS camera_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                resolution TEXT,
                fps INTEGER,
                image_mode TEXT,
                light_filter TEXT,
                gamma REAL,
                clahe_clip REAL,
                zoom REAL,
                focus_mode TEXT,
                focus_value INTEGER,
                pan_x INTEGER,
                pan_y INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS lighting_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                brightness_r INTEGER,
                brightness_g INTEGER,
                brightness_b INTEGER,
                location TEXT,
                leds_mask INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS calibration_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                width_mm REAL,
                height_mm REAL,
                distance_mm REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS startup_preset (
                kind TEXT PRIMARY KEY,
                preset_name TEXT
            );
        """)
        conn.commit()
    finally:
        conn.close()

# --- Kamera preset ---
def camera_save(name, data):
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO camera_presets
            (name, resolution, fps, image_mode, light_filter, gamma, clahe_clip,
             zoom, focus_mode, focus_value, pan_x, pan_y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            json.dumps(data.get("resolution", [9152, 6944])),
            data.get("fps", 10),
            data.get("image_mode", "Renkli"),
            data.get("light_filter", "Gamma"),
            data.get("gamma", 1.0),
            data.get("clahe_clip", 2.0),
            data.get("zoom", 1.0),
            data.get("focus_mode", "Manual"),
            data.get("focus_value", 9.0),
            data.get("pan_x", 0),
            data.get("pan_y", 0),
        ))
        conn.commit()
    finally:
        conn.close()

def camera_list():
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT name FROM camera_presets ORDER BY name").fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()

def camera_load(name):
    conn = _get_conn()
    try:
        r = conn.execute(
            "SELECT * FROM camera_presets WHERE name = ?", (name,)
        ).fetchone()
        if not r:
            return None
        res = json.loads(r["resolution"]) if r["resolution"] else [9152, 6944]
        return {
            "resolution": tuple(res),
            "fps": r["fps"] or 10,
            "image_mode": r["image_mode"] or "Renkli",
            "light_filter": r["light_filter"] or "Gamma",
            "gamma": r["gamma"] if r["gamma"] is not None else 1.0,
            "clahe_clip": r["clahe_clip"] if r["clahe_clip"] is not None else 2.0,
            "zoom": r["zoom"] if r["zoom"] is not None else 1.0,
            "focus_mode": r["focus_mode"] or "Manual",
            "focus_value": float(r["focus_value"]) if r["focus_value"] is not None else 9.0,
            "pan_x": r["pan_x"] or 0,
            "pan_y": r["pan_y"] or 0,
        }
    finally:
        conn.close()

def camera_delete(name):
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM camera_presets WHERE name = ?", (name,))
        conn.commit()
    finally:
        conn.close()

# --- Aydınlatma preset ---
def lighting_save(name, data):
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO lighting_presets
            (name, brightness_r, brightness_g, brightness_b, location, leds_mask)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            name,
            data.get("brightness_r", 128),
            data.get("brightness_g", 128),
            data.get("brightness_b", 128),
            data.get("location", "Yok"),
            data.get("leds_mask", 0),
        ))
        conn.commit()
    finally:
        conn.close()

def lighting_list():
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT name FROM lighting_presets ORDER BY name").fetchall()
        return [r["name"] for r in rows]
    finally:
        conn.close()

def lighting_load(name):
    conn = _get_conn()
    try:
        r = conn.execute(
            "SELECT * FROM lighting_presets WHERE name = ?", (name,)
        ).fetchone()
        if not r:
            return None
        return {
            "brightness_r": r["brightness_r"] or 128,
            "brightness_g": r["brightness_g"] or 128,
            "brightness_b": r["brightness_b"] or 128,
            "location": r["location"] or "Yok",
            "leds_mask": r["leds_mask"] or 0,
        }
    finally:
        conn.close()

def lighting_delete(name):
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM lighting_presets WHERE name = ?", (name,))
        conn.commit()
    finally:
        conn.close()

# --- Kalibrasyon preset ---
def calibration_save(name, width_mm, height_mm, distance_mm):
    conn = _get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO calibration_presets (name, width_mm, height_mm, distance_mm)
            VALUES (?, ?, ?, ?)
        """, (name, width_mm, height_mm, distance_mm))
        conn.commit()
    finally:
        conn.close()

def calibration_list():
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT name, width_mm, height_mm, distance_mm FROM calibration_presets ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def calibration_load(name):
    conn = _get_conn()
    try:
        r = conn.execute(
            "SELECT * FROM calibration_presets WHERE name = ?", (name,)
        ).fetchone()
        if not r:
            return None
        return {
            "width_mm": r["width_mm"],
            "height_mm": r["height_mm"],
            "distance_mm": r["distance_mm"],
        }
    finally:
        conn.close()

# --- Başlangıç preset'leri ---
def startup_set(kind, preset_name):
    conn = _get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO startup_preset (kind, preset_name) VALUES (?, ?)",
            (kind, preset_name),
        )
        conn.commit()
    finally:
        conn.close()

def startup_get(kind):
    conn = _get_conn()
    try:
        r = conn.execute(
            "SELECT preset_name FROM startup_preset WHERE kind = ?", (kind,)
        ).fetchone()
        return r["preset_name"] if r else None
    finally:
        conn.close()
