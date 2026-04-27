import pygame
import sys
import math
import random
import os
import csv
import json
import pygame.gfxdraw # Reikalinga glotniam rato piešimui

from game_data import (
    F1_TEAMS,
    TOTAL_WEIGHT,
    TEAM_DRIVERS_2025,
    DRIVER_COUNTRY,
    DRIVER_NUMBERS_2025,
    AI_DRIVER_NUMBERS,
    DRIVER_STATS,
    DRIVER_2025_STRENGTH,
    UPGRADE_POOL,
)
from f1_game.car_constants import (
    RARITY_STEPS,
    CAR_PARTS,
    MAX_CAR_TIER,
    PART_UPGRADE_CURVES,
    TEAM_CAR_BASE_PARTS,
    TEAM_ABBREV,
    RACE_TYRE_COMPOUNDS,
)
from f1_game.track_seed_data import SAO_PAULO_CENTERLINE_N, INTERLAGOS_PIT_TEMPLATE_N
from f1_game.season_calendar import SEASON_GP_CALENDAR
from f1_game.oop_rewards import DEFAULT_CHEST_REWARD_SERVICE
from f1_game.persistence import (
    CareerDataManager,
    CareerSnapshot,
    CarDevelopmentState,
    DriverIdentity,
    EconomyState,
    CareerMetaState,
    JsonSnapshotSerializer,
)

# --- INICIALIZACIJA ---
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("F1 Manager 2025")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- MUZIKOS GROTUVAS ---
playlist = [
    {"file": "sounds/song1.mp3", "title": "tv off", "artist": "Kendrick Lamar", "cover": "music_covers/song1.jpg"},
    {"file": "sounds/song2.mp3", "title": "3500", "artist": "Travis Scott", "cover": "music_covers/song2.jpg"},
    {"file": "sounds/song3.mp3", "title": "NEW DROP", "artist": "Don Toliver", "cover": "music_covers/song3.jpg"},
    {"file": "sounds/song4.mp3", "title": "Low", "artist": "SZA", "cover": "music_covers/song4.jpg"},
    {"file": "sounds/song5.mp3", "title": "I Wish", "artist": "Skee-Lo", "cover": "music_covers/song5.jpg"}
]

current_track_idx = 0
current_cover_surf = None
music_panel_dismissed = False
SONG_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(SONG_END)
tick_sound = None
win_sound = None

def load_and_convert_img(path, size):
    full_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        surf = pygame.Surface(size); surf.fill((80, 80, 80))
        return surf
    try:
        img = pygame.image.load(full_path).convert() if not full_path.lower().endswith('.png') else pygame.image.load(full_path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size); surf.fill((80, 80, 80))
        return surf

def play_track(idx):
    global current_cover_surf
    if idx < len(playlist):
        track = playlist[idx]
        if os.path.exists(track["file"]):
            try:
                pygame.mixer.music.load(track["file"])
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play()
                current_cover_surf = load_and_convert_img(track["cover"], (50, 50))
            except: pass

def load_sound(path, volume=0.5):
    full_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.exists(full_path):
        return None
    try:
        snd = pygame.mixer.Sound(full_path)
        snd.set_volume(volume)
        return snd
    except:
        return None

if playlist: play_track(current_track_idx)
tick_sound = load_sound("sounds/case_tick.wav", 0.35)
win_sound = load_sound("sounds/case_win.wav", 0.55)

# --- SPALVOS IR ŠRIFTAI ---
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GRAY, LIGHT_GRAY = (50, 50, 50), (120, 120, 120)
GOLD, ORANGE = (255, 215, 0), (255, 128, 0)
CYAN = (0, 255, 255)
BLOOD_RED, DRAMATIC_BLUE = (138, 3, 3), (0, 32, 96)

font_main = pygame.font.SysFont("Arial Black", 60)
font_ui = pygame.font.SysFont("Arial", 28, bold=True)
font_instr = pygame.font.SysFont("Arial", 22, italic=True, bold=True)
font_exit = pygame.font.SysFont("Arial", 16, bold=True)
font_music_bold = pygame.font.SysFont("Arial", 16, bold=True)
font_music_small = pygame.font.SysFont("Arial", 13)
font_hint = pygame.font.SysFont("Arial", 11, italic=True)
font_wheel_label = pygame.font.SysFont("Arial", 18, bold=True)
font_small = pygame.font.SysFont("Arial", 18, bold=True)

# --- LED LIETAUS SISTEMA ---
class LEDDrop:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, HEIGHT)
    def reset(self):
        self.x, self.y = random.randint(0, WIDTH), random.randint(-500, -50)
        self.speed = random.uniform(4, 9)
        self.width, self.length = random.randint(3, 5), random.randint(20, 60)
    def fall(self):
        self.y += self.speed
        if self.y > HEIGHT: self.reset()
    def draw(self, color):
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.length))

rain_drops = [LEDDrop() for _ in range(150)]

def get_led_color(offset=0):
    time = pygame.time.get_ticks() * 0.005 + offset
    return (int(127 + 127 * math.sin(time)), int(127 + 127 * math.sin(time + 2)), int(127 + 127 * math.sin(time + 4)))

def draw_text_with_outline(text, font, text_color, outline_color, x_pos, y_pos, align="center"):
    text_surf = font.render(str(text), True, text_color)
    if align == "center":
        text_rect = text_surf.get_rect(center=(x_pos, y_pos))
    elif align == "right":
        text_rect = text_surf.get_rect(topright=(x_pos, y_pos))
    else:
        text_rect = text_surf.get_rect(topleft=(x_pos, y_pos))
    for ox, oy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
        screen.blit(font.render(str(text), True, outline_color), (text_rect.x + ox, text_rect.y + oy))
    screen.blit(text_surf, text_rect)


def main_menu_career_rect():
    return pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 190, 440, 440)

# --- UŽKROVIMAS ---
title_bg = load_and_convert_img("images/title_bg.jpg", (WIDTH, HEIGHT))
career_img = load_and_convert_img("images/career_mode.jpg", (400, 400))
team_img = load_and_convert_img("images/team_mode.jpg", (400, 400))
guide_img = load_and_convert_img("images/mergina.jpg", (250, 300))
avatar_img = load_and_convert_img("images/avataras.jpg", (210, 210))
car_img = load_and_convert_img("images/masina.jpg", (370, 170))

game_state = "TITLE"
CAREER_POS, TEAM_POS = (WIDTH // 4, HEIGHT // 2 + 20), (3 * WIDTH // 4, HEIGHT // 2 + 20)

driver_data = {
    "Name": {"text": "", "rect": pygame.Rect(540, 200, 300, 45), "active": False},
    "Surname": {"text": "", "rect": pygame.Rect(540, 270, 300, 45), "active": False},
    "Number": {"text": "", "rect": pygame.Rect(540, 340, 100, 45), "active": False},
    "Country": {"text": "", "rect": pygame.Rect(540, 410, 300, 45), "active": False}
}

# --- RATO KINTAMIEJI ---
wheel_angle = 0 
is_spinning = False
winning_team_name = ""
wheel_center = (WIDTH // 2, HEIGHT // 2 + 70) # Nuleistas žemiau
wheel_radius = 240
btn_radius = 45
spin_start_angle = 0
spin_target_angle = 0
spin_start_time = 0
spin_duration_ms = 0
show_wheel_intro = True
guide_card_rect = pygame.Rect(WIDTH - 340, 120, 300, 470)
spin_button_rect = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 110, 180, 56)
reel_window = pygame.Rect(170, HEIGHT // 2 - 85, WIDTH - 340, 170)
reel_items = []
reel_start_offset = 0.0
reel_target_offset = 0.0
last_tick_slot = -1
sponsor_reel_windows = [pygame.Rect(120, 135, WIDTH - 240, 120), pygame.Rect(120, 395, WIDTH - 240, 120)]
sponsor_reel_rows = [[], []]
sponsor_offers = [[], []]
sponsor_titles = ["MAIN TITLE SPONSOR", "TECHNICAL PARTNER"]
teammate_result = ""
upgrade_result = ""
teammate_reel = []
upgrade_reel = []
open_teammate_btn = pygame.Rect(WIDTH // 2 - 240, 250, 220, 44)
open_upgrade_btn = pygame.Rect(WIDTH // 2 - 240, 510, 220, 44)
sponsor_reel_offsets = [0.0, 0.0]
sponsor_reel_targets = [0.0, 0.0]
sponsor_reel_spinning = [False, False]
sponsor_reel_start_time = [0, 0]
sponsor_reel_duration = [0, 0]
sponsor_last_tick_slot = [-1, -1]
selected_offer_idx = -1
sponsor_result_revealed = [False, False]
next_arrow_rect = pygame.Rect(WIDTH - 72, HEIGHT - 62, 42, 32)
profile_margin = 12
money_balance = 0
signing_bonus_given = False
career_profile_unlocked = False
selected_offer_name = ""
teammate_img = None
post_race_chest = None
chest_continue_rect = pygame.Rect(0, 0, 0, 0)
upgrade_inventory = {
    "Overtaking Upgrade": 0,
    "Defending Upgrade": 0,
    "Qualifying Upgrade": 0,
    "Race Start Upgrade": 0,
    "Tyre Management Upgrade": 0
}
upgrade_levels = {
    "Overtaking Upgrade": 0,
    "Defending Upgrade": 0,
    "Qualifying Upgrade": 0,
    "Race Start Upgrade": 0,
    "Tyre Management Upgrade": 0
}
upgrade_apply_buttons = {}

car_part_tiers = {part: 0 for part in CAR_PARTS}
teammate_car_tiers = {part: 2 for part in CAR_PARTS}
replaced_driver_name = ""
car_upgrade_buttons = {}
start_race_rect = pygame.Rect(WIDTH // 2 + 26, HEIGHT - 126, WIDTH // 2 - 48, 104)
pending_car_part = None
buy_button_rect = pygame.Rect(0, 0, 90, 30)
teammate_box_click_rect = pygame.Rect(0, 0, 0, 0)
profile_car_box_rect = pygame.Rect(0, 0, 0, 0)
show_teammate_card = False
teammate_card_close_rect = pygame.Rect(0, 0, 0, 0)
show_car_stats_card = False
car_stats_card_rect = pygame.Rect(0, 0, 0, 0)
car_stats_close_rect = pygame.Rect(0, 0, 0, 0)
season_started_once = False
season_gp_index = 0
# PRE_RACE: False = čempionato tvarka prieš kvalifikaciją; True = starto tinklelis po Q3.
pre_race_qualifying_done = False
track_geometry_cache = {}
track_geometry_cache_key = None

# --- Qualifying (Saturday) before race day (Sunday) ---
qual_session_cars = []
qual_random = None
qual_phase = ""
qual_anim_rows = []
qual_anim_start_tick = 0
qual_anim_duration_ms = 5200
qual_surv_q1 = set()
qual_surv_q2 = set()
qual_display_rank_prev = {}
qual_display_rank_curr = {}
qual_last_action_rect = pygame.Rect(0, 0, 0, 0)

# --- Race setup + live race session (būsenos kintamieji; RACE_TYRE_COMPOUNDS — f1_game.car_constants) ---
race_setup_selected_tyre = "MEDIUM"
race_setup_weather = "Dry"
race_setup_btn_rect = pygame.Rect(0, 0, 0, 0)
race_setup_tyre_rects = {}
race_session_cars = []
race_phase = "idle"  # idle|grid|lights|green|finished
race_phase_start_ms = 0
race_start_line_idx = 0
race_fastest_lap = {"car_idx": None, "ms": None}
race_elapsed_start_ms = 0
race_final_order = []
race_player_push_mode = 1
race_push_rects = {}
race_pit_now_rect = pygame.Rect(0, 0, 0, 0)
race_player_pit_request = False
race_pit_entry_s = 0.0
race_finish_continue_rect = pygame.Rect(0, 0, 0, 0)
race_points_awarded = False
race_podium_rows = []
race_safety_car_active = False
race_safety_car_end_ms = 0
race_safety_car_used = False
race_fastest_popup_text = ""
race_fastest_popup_until_ms = 0
# Kai visi finišavę — automatinis perėjimas į podiumą (ms deadline).
race_auto_podium_deadline_ms = 0
# Finišo tvarka užrakinama akimirksniu (kad pozicijos nebesikeistų).
race_finish_order = []
# Po lenktynių: pilna lentelė + komandų skirtukas.
race_post_results_rows = []
race_post_team_rows = []
race_results_tab = "drivers"
race_results_drivers_tab_rect = pygame.Rect(0, 0, 0, 0)
race_results_teams_tab_rect = pygame.Rect(0, 0, 0, 0)
race_results_continue_rect = pygame.Rect(0, 0, 0, 0)

error_msg, error_timer = "", 0
clock = pygame.time.Clock()

# --- Race track (São Paulo / Interlagos) + cars ---
TRACK_POINTS = []
TRACK_CUM = []
TRACK_TOTAL = 1.0
TRACK_OUTER = []
TRACK_INNER = []
# Pit lane / boxai (perskaičiuojama su build_track_cache)
TRACK_PIT_POLYGON = []
PIT_GARAGE_RECTS = []
# Jei yra tracks/pit_lane.geojson arba pit_lane.csv (lon,lat kaip interlagos) — pit braižomas pagal failą
PIT_LANE_CENTERLINE_N = []
# True kai pagrindinė trasa įkelta iš interlagos.* failo — švelnus glodinimas (ne dvigubas agresyvus pipeline).
INTERLAGOS_TRACK_RAW_FROM_FILE = False
# True kai naudojamas tiesioginis x,y [0..1] failas (be lon/lat bbox normalizavimo).
INTERLAGOS_DIRECT_NORMALIZED = False
# Stabilus režimas: naudoti rankinį Interlagos šabloną (be OSM/GeoJSON auto-segmentavimo).
FORCE_INTERLAGOS_TEMPLATE = False
pre_race_grid = []
# Championship points (PRE_RACE PTS column)
championship_points = {}
sim_race_laps_this_round = 12
RACE_MINIMAP_SURF = None
RACE_MINIMAP_BOUNDS = None



def _load_centerline_from_latlon_csv(csv_path):
    """CSV format: header lat,lon (or latitude,longitude). Returns normalized [0..1] points."""
    pts = []
    try:
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                lat_raw = row.get("lat", row.get("latitude"))
                lon_raw = row.get("lon", row.get("lng", row.get("longitude")))
                if lat_raw is None or lon_raw is None:
                    continue
                lat = float(str(lat_raw).strip())
                lon = float(str(lon_raw).strip())
                pts.append((lon, lat))
    except Exception:
        return None
    if len(pts) < 8:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    wx = max(maxx - minx, 1e-12)
    wy = max(maxy - miny, 1e-12)
    norm = [((x - minx) / wx, (y - miny) / wy) for x, y in pts]
    # Tik failo forma: tik beveik dubliai; be spike/loop kirpimo ir be retinimo — kitaip GPS sulūžta.
    return _dedupe_close_points(norm, min_dist=0.0002)


def _load_centerline_from_normalized_xy_csv(csv_path):
    """CSV format: x,y (arba nx,ny) jau [0..1] koordinačių sistemoje."""
    pts = []
    try:
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                x_raw = row.get("x", row.get("nx"))
                y_raw = row.get("y", row.get("ny"))
                if x_raw is None or y_raw is None:
                    continue
                x = float(str(x_raw).strip())
                y = float(str(y_raw).strip())
                pts.append((max(0.0, min(1.0, x)), max(0.0, min(1.0, y))))
    except Exception:
        return None
    if len(pts) < 8:
        return None
    return _dedupe_close_points(pts, min_dist=0.00008)


def _smooth_closed_points(points, passes=2):
    """Light smoothing for closed centerline loops."""
    if len(points) < 8:
        return list(points)
    out = list(points)
    for _ in range(max(1, int(passes))):
        nxt = []
        n = len(out)
        for i in range(n):
            p_prev = out[(i - 1) % n]
            p_cur = out[i]
            p_next = out[(i + 1) % n]
            x = 0.22 * p_prev[0] + 0.56 * p_cur[0] + 0.22 * p_next[0]
            y = 0.22 * p_prev[1] + 0.56 * p_cur[1] + 0.22 * p_next[1]
            nxt.append((x, y))
        out = nxt
    return out


def _dedupe_close_points(points, min_dist=0.0018):
    """Remove near-duplicate consecutive points to avoid spikes/triangles."""
    if len(points) < 3:
        return list(points)
    out = [points[0]]
    min_d2 = float(min_dist) * float(min_dist)
    for p in points[1:]:
        q = out[-1]
        dx = p[0] - q[0]
        dy = p[1] - q[1]
        if dx * dx + dy * dy >= min_d2:
            out.append(p)
    if len(out) >= 3:
        dx = out[0][0] - out[-1][0]
        dy = out[0][1] - out[-1][1]
        if dx * dx + dy * dy < min_d2:
            out.pop()
    return out if len(out) >= 3 else list(points)


def _seg_intersection(a, b, c, d):
    """True when AB and CD segments intersect or touch."""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    def on_seg(p, q, r):
        return (
            min(p[0], r[0]) - 1e-12 <= q[0] <= max(p[0], r[0]) + 1e-12 and
            min(p[1], r[1]) - 1e-12 <= q[1] <= max(p[1], r[1]) + 1e-12
        )
    o1 = orient(a, b, c)
    o2 = orient(a, b, d)
    o3 = orient(c, d, a)
    o4 = orient(c, d, b)
    if (o1 * o2 < 0.0) and (o3 * o4 < 0.0):
        return True
    if abs(o1) < 1e-12 and on_seg(a, c, b):
        return True
    if abs(o2) < 1e-12 and on_seg(a, d, b):
        return True
    if abs(o3) < 1e-12 and on_seg(c, a, d):
        return True
    if abs(o4) < 1e-12 and on_seg(c, b, d):
        return True
    return False


def _remove_sharp_spikes(points, min_angle_deg=52.0):
    """Drop very acute corners that create visible spikes."""
    if len(points) < 10:
        return list(points)
    out = list(points)
    min_cos = math.cos(math.radians(min_angle_deg))
    changed = True
    while changed and len(out) > 10:
        changed = False
        n = len(out)
        drop_idx = None
        for i in range(n):
            p_prev = out[(i - 1) % n]
            p = out[i]
            p_next = out[(i + 1) % n]
            v1x, v1y = p_prev[0] - p[0], p_prev[1] - p[1]
            v2x, v2y = p_next[0] - p[0], p_next[1] - p[1]
            l1 = math.hypot(v1x, v1y)
            l2 = math.hypot(v2x, v2y)
            if l1 < 1e-9 or l2 < 1e-9:
                drop_idx = i
                break
            cosang = (v1x * v2x + v1y * v2y) / (l1 * l2)
            if cosang > min_cos and max(l1, l2) < 0.09:
                drop_idx = i
                break
        if drop_idx is not None:
            out.pop(drop_idx)
            changed = True
    return out


def _remove_self_intersections(points, max_iter=80):
    """Remove small loops where centerline overlaps itself."""
    if len(points) < 12:
        return list(points)
    out = list(points)
    for _ in range(max(1, int(max_iter))):
        n = len(out)
        changed = False
        for i in range(n):
            a = out[i]
            b = out[(i + 1) % n]
            for j in range(i + 2, n):
                if (j + 1) % n == i:
                    continue
                c = out[j]
                d = out[(j + 1) % n]
                if not _seg_intersection(a, b, c, d):
                    continue
                forward = (j - i) % n
                backward = n - forward
                if forward <= backward:
                    new_pts = out[:i + 1] + out[j + 1:]
                else:
                    new_pts = out[j + 1:i + 1]
                if len(new_pts) >= 10:
                    out = _dedupe_close_points(new_pts, min_dist=0.0015)
                    changed = True
                break
            if changed:
                break
        if not changed or len(out) < 12:
            break
    return out


def _chaikin_closed(points, iterations=3):
    """Corner-cutting smoothing for closed loops; no spline overshoot artifacts."""
    if len(points) < 4:
        return list(points)
    out = list(points)
    for _ in range(max(1, int(iterations))):
        nxt = []
        n = len(out)
        for i in range(n):
            p0 = out[i]
            p1 = out[(i + 1) % n]
            qx = 0.75 * p0[0] + 0.25 * p1[0]
            qy = 0.75 * p0[1] + 0.25 * p1[1]
            rx = 0.25 * p0[0] + 0.75 * p1[0]
            ry = 0.25 * p0[1] + 0.75 * p1[1]
            nxt.append((qx, qy))
            nxt.append((rx, ry))
        out = nxt
    return out


def _load_centerline_from_geojson(geojson_path):
    """GeoJSON LineString reader. Expects coordinates as [lon, lat]."""
    try:
        with open(geojson_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None
    def _coords_to_lonlat(coords):
        pts_local = []
        for item in coords or []:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            pts_local.append((float(item[0]), float(item[1])))
        return pts_local

    def _merge_linestring_segments_lonlat(segments, join_eps=5e-5):
        if not segments:
            return []
        rem = [list(seg) for seg in segments if len(seg) >= 2]
        if not rem:
            return []
        chain = rem.pop(max(range(len(rem)), key=lambda i: len(rem[i])))

        def _d2(a, b):
            dx = a[0] - b[0]
            dy = a[1] - b[1]
            return dx * dx + dy * dy

        eps2 = join_eps * join_eps
        while rem:
            best = None
            best_i = -1
            best_mode = ""
            c0 = chain[0]
            c1 = chain[-1]
            for i, seg in enumerate(rem):
                s0 = seg[0]
                s1 = seg[-1]
                cand = [
                    (_d2(c1, s0), "append"),
                    (_d2(c1, s1), "append_rev"),
                    (_d2(c0, s1), "prepend"),
                    (_d2(c0, s0), "prepend_rev"),
                ]
                d2m, mode = min(cand, key=lambda t: t[0])
                if best is None or d2m < best:
                    best = d2m
                    best_i = i
                    best_mode = mode
            if best_i < 0 or best is None:
                break
            seg = rem.pop(best_i)
            if best_mode == "append":
                add = seg[1:] if best <= eps2 else seg
                chain.extend(add)
            elif best_mode == "append_rev":
                seg = list(reversed(seg))
                add = seg[1:] if best <= eps2 else seg
                chain.extend(add)
            elif best_mode == "prepend":
                add = seg[:-1] if best <= eps2 else seg
                chain = add + chain
            else:
                seg = list(reversed(seg))
                add = seg[:-1] if best <= eps2 else seg
                chain = add + chain
        return chain

    pts = []
    try:
        if data.get("type") == "FeatureCollection":
            main_segments = []
            fallback_first = None
            for feat in data.get("features", []):
                geom = feat.get("geometry", {})
                if geom.get("type") != "LineString":
                    continue
                seg = _coords_to_lonlat(geom.get("coordinates", []))
                if len(seg) < 2:
                    continue
                if fallback_first is None:
                    fallback_first = seg
                props = feat.get("properties", {}) or {}
                name_l = str(props.get("name", "")).lower()
                highway_l = str(props.get("highway", "")).lower()
                service_l = str(props.get("service", "")).lower()
                # OSM eksportuose atmetam pit + Formula E fragmentus, renkam GP raceway dalis.
                is_pit = ("pit" in name_l) or ("pit" in service_l)
                is_formula_e = ("formula e" in name_l)
                if highway_l == "raceway" and (not is_pit) and (not is_formula_e):
                    main_segments.append(seg)
            if main_segments:
                pts = _merge_linestring_segments_lonlat(main_segments, join_eps=8e-5)
            elif fallback_first is not None:
                pts = fallback_first
        elif data.get("type") == "Feature":
            geom = data.get("geometry", {})
            if geom.get("type") == "LineString":
                pts = _coords_to_lonlat(geom.get("coordinates", []))
        elif data.get("type") == "LineString":
            pts = _coords_to_lonlat(data.get("coordinates", []))
    except Exception:
        return None
    if not pts or len(pts) < 8:
        return None
    if len(pts) < 8:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    wx = max(maxx - minx, 1e-12)
    wy = max(maxy - miny, 1e-12)
    norm = [((x - minx) / wx, (y - miny) / wy) for x, y in pts]
    return _dedupe_close_points(norm, min_dist=0.0002)


def _discover_interlagos_centerline():
    """Searches project for interlagos CSV/GeoJSON and converts to normalized centerline."""
    global INTERLAGOS_TRACK_RAW_FROM_FILE, INTERLAGOS_DIRECT_NORMALIZED
    INTERLAGOS_TRACK_RAW_FROM_FILE = False
    INTERLAGOS_DIRECT_NORMALIZED = False
    normalized_candidates = [
        os.path.join(BASE_DIR, "tracks", "interlagos_xy.csv"),
        os.path.join(BASE_DIR, "tracks", "interlagos_n.csv"),
        os.path.join(BASE_DIR, "interlagos_xy.csv"),
        os.path.join(BASE_DIR, "interlagos_n.csv"),
    ]
    for path in normalized_candidates:
        if not os.path.exists(path):
            continue
        pts_n = _load_centerline_from_normalized_xy_csv(path)
        if pts_n:
            INTERLAGOS_TRACK_RAW_FROM_FILE = True
            INTERLAGOS_DIRECT_NORMALIZED = True
            return pts_n
    candidates = [
        os.path.join(BASE_DIR, "tracks", "interlagos.geojson"),
        os.path.join(BASE_DIR, "tracks", "interlagos.geajson"),
        os.path.join(BASE_DIR, "tracks", "interlagos.csv"),
        os.path.join(BASE_DIR, "interlagos.geojson"),
        os.path.join(BASE_DIR, "interlagos.geajson"),
        os.path.join(BASE_DIR, "interlagos.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            low = path.lower()
            if low.endswith(".csv"):
                pts = _load_centerline_from_latlon_csv(path)
            else:
                pts = _load_centerline_from_geojson(path)
            if pts:
                INTERLAGOS_TRACK_RAW_FROM_FILE = True
                INTERLAGOS_DIRECT_NORMALIZED = False
                return pts
    try:
        for root, _, files in os.walk(BASE_DIR):
            for fn in files:
                low = fn.lower()
                if "interlagos" not in low:
                    continue
                full = os.path.join(root, fn)
                if low.endswith(".csv"):
                    pts = _load_centerline_from_latlon_csv(full)
                elif low.endswith(".geojson") or low.endswith(".geajson"):
                    pts = _load_centerline_from_geojson(full)
                else:
                    pts = None
                if pts:
                    INTERLAGOS_TRACK_RAW_FROM_FILE = True
                    INTERLAGOS_DIRECT_NORMALIZED = False
                    return pts
    except Exception:
        pass
    return None


def _discover_interlagos_source_path():
    """Pirmas rastas interlagos šaltinio failas (CSV/GeoJSON) — ta pati bbox kaip trasai."""
    candidates = [
        os.path.join(BASE_DIR, "tracks", "interlagos.geojson"),
        os.path.join(BASE_DIR, "tracks", "interlagos.geajson"),
        os.path.join(BASE_DIR, "tracks", "interlagos.csv"),
        os.path.join(BASE_DIR, "interlagos.geojson"),
        os.path.join(BASE_DIR, "interlagos.geajson"),
        os.path.join(BASE_DIR, "interlagos.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    try:
        for root, _, files in os.walk(BASE_DIR):
            for fn in files:
                low = fn.lower()
                if "interlagos" not in low:
                    continue
                full = os.path.join(root, fn)
                if low.endswith(".csv") or low.endswith(".geojson") or low.endswith(".geajson"):
                    return full
    except Exception:
        pass
    return None


def _geojson_extract_first_linestring_lonlat(geojson_path):
    """Grąžina LineString koordinates kaip [(lon, lat), ...] arba None."""
    try:
        with open(geojson_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None
    coords = None
    try:
        if data.get("type") == "FeatureCollection":
            for feat in data.get("features", []):
                geom = feat.get("geometry", {})
                if geom.get("type") == "LineString":
                    coords = geom.get("coordinates", [])
                    break
        elif data.get("type") == "Feature":
            geom = data.get("geometry", {})
            if geom.get("type") == "LineString":
                coords = geom.get("coordinates", [])
        elif data.get("type") == "LineString":
            coords = data.get("coordinates", [])
    except Exception:
        return None
    if not coords or len(coords) < 4:
        return None
    out = []
    for item in coords:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((float(item[0]), float(item[1])))
    return out if len(out) >= 4 else None


def _geojson_collect_ordered_linestrings_lonlat(geojson_path):
    """Visos FeatureCollection LineString eilės tvarka — [(lon,lat), ...] sąrašai."""
    try:
        with open(geojson_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return []

    def _line_from_coords(cc):
        pts = []
        for item in cc or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                pts.append((float(item[0]), float(item[1])))
        return pts if len(pts) >= 2 else None

    out = []
    try:
        if data.get("type") == "FeatureCollection":
            for feat in data.get("features", []):
                geom = feat.get("geometry", {})
                if geom.get("type") != "LineString":
                    continue
                ln = _line_from_coords(geom.get("coordinates", []))
                if ln:
                    out.append(ln)
        elif data.get("type") == "Feature":
            geom = data.get("geometry", {})
            if geom.get("type") == "LineString":
                ln = _line_from_coords(geom.get("coordinates", []))
                if ln:
                    out.append(ln)
        elif data.get("type") == "LineString":
            ln = _line_from_coords(data.get("coordinates", []))
            if ln:
                out.append(ln)
    except Exception:
        return []
    return out


def _pit_lonlat_merged_from_interlagos_geojson(geojson_path):
    """Pit iš OSM GeoJSON: jungiami tik segmentai su pavadinimu/service, kuriuose yra 'pit'."""
    try:
        with open(geojson_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return None
    if data.get("type") != "FeatureCollection":
        return None

    def _coords_to_lonlat(coords):
        out = []
        for item in coords or []:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out.append((float(item[0]), float(item[1])))
        return out

    def _merge_segments(segs, join_eps=8e-5):
        if not segs:
            return []
        rem = [list(s) for s in segs if len(s) >= 2]
        if not rem:
            return []
        chain = rem.pop(max(range(len(rem)), key=lambda i: len(rem[i])))
        eps2 = join_eps * join_eps

        def _d2(a, b):
            dx = a[0] - b[0]
            dy = a[1] - b[1]
            return dx * dx + dy * dy

        while rem:
            best = None
            best_i = -1
            best_mode = ""
            end = chain[-1]
            for i, s in enumerate(rem):
                d_start = _d2(end, s[0])
                d_end = _d2(end, s[-1])
                if best is None or d_start < best:
                    best = d_start
                    best_i = i
                    best_mode = "fwd"
                if d_end < best:
                    best = d_end
                    best_i = i
                    best_mode = "rev"
            if best_i < 0:
                break
            seg = rem.pop(best_i)
            if best_mode == "rev":
                seg = list(reversed(seg))
            chain.extend(seg[1:] if best <= eps2 else seg)
        return chain

    pit_segments = []
    for feat in data.get("features", []):
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        props = feat.get("properties", {}) or {}
        name_l = str(props.get("name", "")).lower()
        service_l = str(props.get("service", "")).lower()
        if ("pit" not in name_l) and ("pit" not in service_l):
            continue
        seg = _coords_to_lonlat(geom.get("coordinates", []))
        if len(seg) >= 2:
            pit_segments.append(seg)
    merged = _merge_segments(pit_segments, join_eps=8e-5)
    return merged if len(merged) >= 4 else None


def _csv_read_lonlat_raw(csv_path):
    """CSV lat,lon / latitude,longitude — žali taškai be išlyginimo."""
    pts = []
    try:
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                lat_raw = row.get("lat", row.get("latitude"))
                lon_raw = row.get("lon", row.get("lng", row.get("longitude")))
                if lat_raw is None or lon_raw is None:
                    continue
                pts.append((float(str(lon_raw).strip()), float(str(lat_raw).strip())))
    except Exception:
        return None
    return pts if len(pts) >= 4 else None


def _lonlat_bbox_from_source_path(path):
    """(minx, maxx, miny, maxy, wx, wy) iš to paties formato kaip trasos failas."""
    if not path or not os.path.exists(path):
        return None
    low = path.lower()
    if low.endswith(".csv"):
        pts = _csv_read_lonlat_raw(path)
    elif low.endswith(".geojson") or low.endswith(".geajson"):
        lines = _geojson_collect_ordered_linestrings_lonlat(path)
        if not lines:
            pts = _geojson_extract_first_linestring_lonlat(path)
        else:
            pts = max(lines, key=len)
    else:
        return None
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    wx = max(maxx - minx, 1e-12)
    wy = max(maxy - miny, 1e-12)
    return (minx, maxx, miny, maxy, wx, wy)


def _reload_pit_lane_file_into_globals():
    """Įkelia pit polyliniją į PIT_LANE_CENTERLINE_N [0..1] pagal tą patį lon/lat bbox kaip interlagos."""
    global PIT_LANE_CENTERLINE_N
    PIT_LANE_CENTERLINE_N = []
    if FORCE_INTERLAGOS_TEMPLATE and len(INTERLAGOS_PIT_TEMPLATE_N) >= 4:
        gp = get_current_gp()
        PIT_LANE_CENTERLINE_N = transform_gp_centerline(
            list(INTERLAGOS_PIT_TEMPLATE_N),
            gp.get("track_transform", {}),
        )
        return
    pit_n_candidates = [
        os.path.join(BASE_DIR, "tracks", "pit_lane_xy.csv"),
        os.path.join(BASE_DIR, "tracks", "pit_lane_n.csv"),
        os.path.join(BASE_DIR, "pit_lane_xy.csv"),
        os.path.join(BASE_DIR, "pit_lane_n.csv"),
    ]
    for pp in pit_n_candidates:
        if not os.path.exists(pp):
            continue
        pts_n = _load_centerline_from_normalized_xy_csv(pp)
        if pts_n and len(pts_n) >= 4:
            gp = get_current_gp()
            PIT_LANE_CENTERLINE_N = transform_gp_centerline(pts_n, gp.get("track_transform", {}))
            return
    ref_path = _discover_interlagos_source_path()
    if not ref_path:
        return
    bbox = _lonlat_bbox_from_source_path(ref_path)
    if not bbox:
        return
    minx, maxx, miny, maxy, wx, wy = bbox
    pit_candidates = [
        os.path.join(BASE_DIR, "tracks", "pit_lane.geojson"),
        os.path.join(BASE_DIR, "tracks", "pit_lane.geajson"),
        os.path.join(BASE_DIR, "tracks", "pit_lane.csv"),
        os.path.join(BASE_DIR, "pit_lane.geojson"),
        os.path.join(BASE_DIR, "pit_lane.geajson"),
        os.path.join(BASE_DIR, "pit_lane.csv"),
    ]
    for pp in pit_candidates:
        if not os.path.exists(pp):
            continue
        low = pp.lower()
        pit_pts = None
        if low.endswith(".csv"):
            pit_pts = _csv_read_lonlat_raw(pp)
        elif low.endswith(".geojson") or low.endswith(".geajson"):
            pit_pts = _geojson_extract_first_linestring_lonlat(pp)
        if pit_pts and len(pit_pts) >= 4:
            raw_n = [((x - minx) / wx, (y - miny) / wy) for x, y in pit_pts]
            gp = get_current_gp()
            PIT_LANE_CENTERLINE_N = transform_gp_centerline(raw_n, gp.get("track_transform", {}))
            return
    if ref_path.lower().endswith(".geojson") or ref_path.lower().endswith(".geajson"):
        pit_ll = _pit_lonlat_merged_from_interlagos_geojson(ref_path)
        if pit_ll and len(pit_ll) >= 4:
            raw_n = [((x - minx) / wx, (y - miny) / wy) for x, y in pit_ll]
            gp = get_current_gp()
            PIT_LANE_CENTERLINE_N = transform_gp_centerline(raw_n, gp.get("track_transform", {}))


INTERLAGOS_BASE_CENTERLINE_N = (
    list(SAO_PAULO_CENTERLINE_N)
    if FORCE_INTERLAGOS_TEMPLATE
    else (_discover_interlagos_centerline() or list(SAO_PAULO_CENTERLINE_N))
)
TRACK_MARGIN_X = 64
TRACK_MARGIN_Y = 44
TRACK_HALF_WIDTH = 21
TRACK_INFIELD_COLOR = (24, 78, 32)



def transform_gp_centerline(base_pts, tr):
    sx = float(tr.get("scale_x", 1.0))
    sy = float(tr.get("scale_y", 1.0))
    shx = float(tr.get("shift_x", 0.0))
    shy = float(tr.get("shift_y", 0.0))
    deg = float(tr.get("rotate_deg", 0.0))
    cx, cy = 0.5, 0.5
    rad = math.radians(deg)
    cr, sr = math.cos(rad), math.sin(rad)
    out = []
    for nx, ny in base_pts:
        x, y = nx - cx, ny - cy
        xr = x * cr - y * sr
        yr = x * sr + y * cr
        x2 = cx + xr * sx + shx
        y2 = cy + yr * sy + shy
        out.append((max(0.03, min(0.97, x2)), max(0.03, min(0.97, y2))))
    return out


def get_current_gp():
    return SEASON_GP_CALENDAR[season_gp_index % len(SEASON_GP_CALENDAR)]


def championship_points_key(car):
    if car.get("driver") == "__PLAYER__":
        return ("__PLAYER__", str(car.get("tag", "YOU")))
    return ("drv", str(car.get("driver", car.get("tag", "?"))))


def register_championship_drivers_from_grid(grid):
    """Užtikrinti, kad kiekvienas tinklelio vairuotojas turi įrašą taškų lentelėje (pradedant nuo 0)."""
    for car in grid:
        championship_points.setdefault(championship_points_key(car), 0)


def get_championship_points_for_car(car):
    return championship_points.get(championship_points_key(car), 0)


def get_gp_pre_race_info_lines_en(gp):
    """Viena eilutė „Label: value“ angliškai (sim. ratai — globalus atsitiktinis 10–15)."""
    return [
        "Schedule: Qualifying (Saturday) — Race (Sunday)",
        f"Venue: {gp.get('venue_en', gp.get('venue_lt', '-'))}",
        f"Track: {gp.get('circuit_en', gp.get('circuit_lt', '-'))}",
        f"Laps (sim.): {sim_race_laps_this_round}",
        f"Air temp: ~{gp.get('air_c', '?')} °C",
        f"Conditions: {gp.get('air_condition_en', gp.get('air_condition_lt', '-'))}",
        f"Humidity: ~{gp.get('humidity_pct', 50)} %",
        f"Wind: {gp.get('wind_ms', '?')} m/s",
        f"Wind direction: {gp.get('wind_dir_en', gp.get('wind_dir_lt', '-'))}",
        f"Track temp: ~{gp.get('track_c', '?')} °C",
    ]


season_active_centerline_n = list(SAO_PAULO_CENTERLINE_N)


def _norm_to_track_xy(nx, ny):
    w = WIDTH - 2 * TRACK_MARGIN_X
    h = HEIGHT - 2 * TRACK_MARGIN_Y
    return (TRACK_MARGIN_X + nx * w, TRACK_MARGIN_Y + ny * h)


def _catmull_rom_closed_xy(control, steps_per_seg=14):
    """Uždara Catmull–Rom splaina (sklandi centrinė linija)."""
    n = len(control)
    if n < 4:
        return list(control)
    out = []
    for i in range(n):
        p0 = control[(i - 1) % n]
        p1 = control[i]
        p2 = control[(i + 1) % n]
        p3 = control[(i + 2) % n]
        for k in range(steps_per_seg):
            t = k / steps_per_seg
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            out.append((x, y))
    return out


def _offset_rail_polygon(centerline, half_w):
    """CCW centrinė: kairė = infield. edge_out = į išorinę pievą, edge_in = į vidinę pievą."""
    n = len(centerline)
    edge_out, edge_in = [], []
    for i in range(n):
        im1 = (i - 1) % n
        ip1 = (i + 1) % n
        dx = centerline[ip1][0] - centerline[im1][0]
        dy = centerline[ip1][1] - centerline[im1][1]
        ln = math.hypot(dx, dy) or 1.0
        lx, ly = -dy / ln, dx / ln
        cx, cy = centerline[i]
        edge_out.append((cx - lx * half_w, cy - ly * half_w))
        edge_in.append((cx + lx * half_w, cy + ly * half_w))
    return edge_out, edge_in


def _gp_is_brazil_interlagos():
    gp = get_current_gp()
    if "brazil" in (gp.get("short_en") or "").lower():
        return True
    c = (gp.get("circuit_en") or "").lower()
    if "interlagos" in c or "jose carlos" in c or "josé carlos" in c:
        return True
    v = (gp.get("venue_en") or "").lower()
    return "são paulo" in v or "sao paulo" in v


def _offset_open_polyline_xy(pts, dist):
    """Atvira polilinija: statmenas poslinkis (ekrano koordinatės)."""
    n = len(pts)
    if n < 2:
        return []
    out = []
    for i in range(n):
        if i == 0:
            dx = pts[1][0] - pts[0][0]
            dy = pts[1][1] - pts[0][1]
        elif i == n - 1:
            dx = pts[-1][0] - pts[-2][0]
            dy = pts[-1][1] - pts[-2][1]
        else:
            dx = pts[i + 1][0] - pts[i - 1][0]
            dy = pts[i + 1][1] - pts[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        out.append((pts[i][0] + nx * dist, pts[i][1] + ny * dist))
    return out


def _point_min_dist_to_closed_polyline(px, py, poly):
    """Min atstumas nuo taško iki uždaros polilinijos segmentų."""
    n = len(poly)
    if n < 2:
        return 1e9
    best = 1e9
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        abx, aby = bx - ax, by - ay
        ab2 = abx * abx + aby * aby
        if ab2 < 1e-12:
            cx, cy = ax, ay
        else:
            t = ((px - ax) * abx + (py - ay) * aby) / ab2
            t = max(0.0, min(1.0, t))
            cx = ax + t * abx
            cy = ay + t * aby
        d = math.hypot(px - cx, py - cy)
        if d < best:
            best = d
    return best


def _rebuild_pit_from_custom_polyline():
    """Pit plotas ir boxai pagal PIT_LANE_CENTERLINE_N (jau [0..1] normalizuota)."""
    global TRACK_PIT_POLYGON, PIT_GARAGE_RECTS
    TRACK_PIT_POLYGON = []
    PIT_GARAGE_RECTS = []
    # Pit koordinatės tik iš failo (normalizuotos + GP transform), be geometrinių stūmimų.
    pts = [_norm_to_track_xy(px, py) for px, py in PIT_LANE_CENTERLINE_N]
    if len(pts) < 4:
        return
    # Parenkame pusę, kuri toliau nuo pagrindinės trasos centro linijos (apsaugo nuo užlipimo ant trasos).
    side_a = _offset_open_polyline_xy(pts, 7.25)
    side_b = _offset_open_polyline_xy(pts, -7.25)
    if len(TRACK_POINTS) >= 8 and side_a and side_b:
        da = sum(_point_min_dist_to_closed_polyline(x, y, TRACK_POINTS) for x, y in side_a) / len(side_a)
        db = sum(_point_min_dist_to_closed_polyline(x, y, TRACK_POINTS) for x, y in side_b) / len(side_b)
        sign = 1.0 if da >= db else -1.0
    else:
        sign = 1.0
    inner = _offset_open_polyline_xy(pts, sign * -4.0)
    outer = _offset_open_polyline_xy(pts, sign * 16.0)
    TRACK_PIT_POLYGON = [(int(a), int(b)) for a, b in inner] + [(int(a), int(b)) for a, b in reversed(outer)]
    n_g = len(F1_TEAMS)
    m = len(outer)
    if m < 3:
        return
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    bx0, bx1 = min(xs), max(xs)
    by0, by1 = min(ys), max(ys)
    for k in range(n_g):
        t = (k + 0.5) / n_g
        j = min(m - 2, max(0, int(t * (m - 1))))
        x0, y0 = outer[j]
        x1, y1 = outer[j + 1]
        tx, ty = x1 - x0, y1 - y0
        tln = math.hypot(tx, ty) or 1.0
        px, py = -ty / tln * 11, tx / tln * 11
        # Siauresni boxai, kad tarp 10 komandų būtų aiškesni tarpai.
        gw, gh = 20, 13
        cx = int((x0 + x1) * 0.5 + px * 0.42)
        cy = int((y0 + y1) * 0.5 + py * 0.42)
        r = pygame.Rect(cx - gw // 2, cy - gh // 2, gw, gh)
        r.clamp_ip(pygame.Rect(bx0 - 6, by0 - 6, bx1 - bx0 + 14, by1 - by0 + 14))
        PIT_GARAGE_RECTS.append(r)


def _find_pit_straight_indices():
    """Ilgiausia ~tiesi centrinės linijos atkarpa (be persidengimo per rato galą) — pit prie tiesiosios."""
    n = len(TRACK_POINTS)
    if n < 80:
        i0 = int(0.065 * n)
        return i0, min(n - 2, i0 + 22)
    cos_lim = math.cos(math.radians(11.0))
    min_span = 20
    max_span = min(150, n // 2)
    best_len = -1.0
    best_i0, best_i1 = int(0.065 * n), min(n - 2, int(0.065 * n) + 24)
    for i0 in range(0, max(1, n - max_span - 4)):
        prev = None
        total_len = 0.0
        i_end = i0
        for k in range(1, max_span + 1):
            i = i0 + k - 1
            if i + 1 >= n:
                break
            dx = TRACK_POINTS[i + 1][0] - TRACK_POINTS[i][0]
            dy = TRACK_POINTS[i + 1][1] - TRACK_POINTS[i][1]
            ln = math.hypot(dx, dy)
            if ln < 1e-4:
                break
            ux, uy = dx / ln, dy / ln
            if prev is not None and (prev[0] * ux + prev[1] * uy) < cos_lim:
                break
            prev = (ux, uy)
            total_len += ln
            i_end = i0 + k
        if i_end - i0 >= min_span and total_len > best_len:
            best_len = total_len
            best_i0, best_i1 = i0, i_end - 1
    return best_i0, best_i1


def _rebuild_pit_and_garage_layout():
    """Pit lane + 10 boxų šalia tiesiosios, už trasos išorės (ant pievos), ne ant pilko asfalto."""
    global TRACK_PIT_POLYGON, PIT_GARAGE_RECTS
    TRACK_PIT_POLYGON = []
    PIT_GARAGE_RECTS = []
    if len(PIT_LANE_CENTERLINE_N) >= 6:
        _rebuild_pit_from_custom_polyline()
        return
    n = len(TRACK_OUTER)
    if n < 48 or len(TRACK_POINTS) != n:
        return
    i0, i1 = _find_pit_straight_indices()
    if i1 <= i0 + 10:
        i1 = min(n - 2, i0 + 22)
    pit_extra = 20
    pit_outer = []
    for i in range(i0, i1 + 1):
        cx, cy = TRACK_POINTS[i]
        ox, oy = TRACK_OUTER[i]
        vx, vy = ox - cx, oy - cy
        ln = math.hypot(vx, vy) or 1.0
        vx /= ln
        vy /= ln
        pit_outer.append((int(ox + vx * pit_extra), int(oy + vy * pit_extra)))
    if len(pit_outer) < 10:
        return
    TRACK_PIT_POLYGON = [TRACK_OUTER[i] for i in range(i0, i1 + 1)] + list(reversed(pit_outer))
    xs = [p[0] for p in pit_outer]
    ys = [p[1] for p in pit_outer]
    bx0, bx1 = min(xs), max(xs)
    by0, by1 = min(ys), max(ys)
    pit_len = len(pit_outer)
    n_garages = len(F1_TEAMS)
    for k in range(n_garages):
        t = (k + 0.5) / n_garages
        j = int(pit_len * (0.06 + t * 0.88))
        j = min(pit_len - 2, max(0, j))
        x0, y0 = pit_outer[j]
        x1, y1 = pit_outer[j + 1]
        tx, ty = x1 - x0, y1 - y0
        tln = math.hypot(tx, ty) or 1.0
        px, py = -ty / tln * 11, tx / tln * 11
        gw, gh = 20, 13
        cx = int((x0 + x1) * 0.5 + px * 0.42)
        cy = int((y0 + y1) * 0.5 + py * 0.42)
        r = pygame.Rect(cx - gw // 2, cy - gh // 2, gw, gh)
        r.clamp_ip(pygame.Rect(bx0 - 6, by0 - 6, bx1 - bx0 + 14, by1 - by0 + 14))
        PIT_GARAGE_RECTS.append(r)


def build_track_cache():
    global TRACK_POINTS, TRACK_CUM, TRACK_TOTAL, TRACK_OUTER, TRACK_INNER
    _reload_pit_lane_file_into_globals()
    src = season_active_centerline_n if len(season_active_centerline_n) >= 4 else SAO_PAULO_CENTERLINE_N
    if INTERLAGOS_TRACK_RAW_FROM_FILE:
        # Įkelta iš failo: nebekartoti agresyvaus Chaikin + spike + loop (sulaužydavo tikrą trasą).
        smooth_n = _dedupe_close_points(list(src), min_dist=0.00018)
        if len(smooth_n) < 260:
            smooth_n = _chaikin_closed(smooth_n, iterations=1)
        smooth_n = _smooth_closed_points(smooth_n, passes=1)
    else:
        smooth_n = _chaikin_closed(src, iterations=4)
        smooth_n = _remove_sharp_spikes(smooth_n, min_angle_deg=58.0)
        smooth_n = _remove_self_intersections(smooth_n, max_iter=140)
        smooth_n = _smooth_closed_points(smooth_n, passes=2)
    TRACK_POINTS = [_norm_to_track_xy(nx, ny) for nx, ny in smooth_n]
    TRACK_CUM = [0.0]
    total = 0.0
    n = len(TRACK_POINTS)
    for i in range(n):
        p = TRACK_POINTS[i]
        q = TRACK_POINTS[(i + 1) % n]
        dx = q[0] - p[0]
        dy = q[1] - p[1]
        seg = math.hypot(dx, dy)
        total += seg
        TRACK_CUM.append(total)
    TRACK_TOTAL = max(total, 1.0)

    track_hw = 18 if INTERLAGOS_TRACK_RAW_FROM_FILE else TRACK_HALF_WIDTH
    eo, ei = _offset_rail_polygon(TRACK_POINTS, track_hw)
    TRACK_OUTER = [(int(x), int(y)) for x, y in eo]
    TRACK_INNER = [(int(x), int(y)) for x, y in ei]
    _rebuild_pit_and_garage_layout()
    _race_build_minimap_cache()


def _race_build_minimap_cache():
    global RACE_MINIMAP_SURF, RACE_MINIMAP_BOUNDS
    mw, mh = 200, 128
    surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
    surf.fill((12, 14, 20, 248))
    if len(TRACK_POINTS) < 3:
        RACE_MINIMAP_SURF = surf
        RACE_MINIMAP_BOUNDS = None
        return
    xs = [p[0] for p in TRACK_POINTS]
    ys = [p[1] for p in TRACK_POINTS]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    pad = 10
    sx = (mw - 2 * pad) / max(maxx - minx, 1e-6)
    sy = (mh - 2 * pad) / max(maxy - miny, 1e-6)
    sc = min(sx, sy)
    pts = []
    for p in TRACK_POINTS:
        pts.append((int(pad + (p[0] - minx) * sc), int(pad + (p[1] - miny) * sc)))
    pygame.draw.lines(surf, (95, 100, 115), True, pts, 2)
    pygame.draw.lines(surf, (210, 215, 225), True, pts, 1)
    pygame.draw.rect(surf, (255, 50, 45, 220), surf.get_rect(), 1, border_radius=4)
    RACE_MINIMAP_SURF = surf
    RACE_MINIMAP_BOUNDS = (minx, miny, sc, pad, mw, mh)


def rebuild_season_track_geometry(force=False):
    """Perstatyti trasą pagal dabartinį sezono etapą (po lenktynių arba paleidimo)."""
    global season_active_centerline_n, track_geometry_cache_key
    global TRACK_POINTS, TRACK_CUM, TRACK_TOTAL, TRACK_OUTER, TRACK_INNER
    gp = get_current_gp()
    gp_idx = season_gp_index % len(SEASON_GP_CALENDAR)
    tr_key = json.dumps(gp.get("track_transform", {}), sort_keys=True)
    cache_key = (gp_idx, tr_key)
    if (not force) and cache_key == track_geometry_cache_key and len(TRACK_OUTER) >= 3 and len(TRACK_INNER) >= 3:
        if not TRACK_PIT_POLYGON:
            _rebuild_pit_and_garage_layout()
        return
    cached = track_geometry_cache.get(cache_key)
    if (not force) and cached:
        season_active_centerline_n = list(cached["centerline_n"])
        TRACK_POINTS = list(cached["track_points"])
        TRACK_CUM = list(cached["track_cum"])
        TRACK_TOTAL = float(cached["track_total"])
        TRACK_OUTER = list(cached["track_outer"])
        TRACK_INNER = list(cached["track_inner"])
        track_geometry_cache_key = cache_key
        _rebuild_pit_and_garage_layout()
        _race_build_minimap_cache()
        return
    season_active_centerline_n = transform_gp_centerline(INTERLAGOS_BASE_CENTERLINE_N, gp.get("track_transform", {}))
    build_track_cache()
    track_geometry_cache_key = cache_key
    track_geometry_cache[cache_key] = {
        "centerline_n": list(season_active_centerline_n),
        "track_points": list(TRACK_POINTS),
        "track_cum": list(TRACK_CUM),
        "track_total": float(TRACK_TOTAL),
        "track_outer": list(TRACK_OUTER),
        "track_inner": list(TRACK_INNER),
    }


def build_team_base_car_copy(team_name):
    b = TEAM_CAR_BASE_PARTS.get(team_name, {p: 2 for p in CAR_PARTS})
    return {p: max(0, min(MAX_CAR_TIER, int(b.get(p, 2)))) for p in CAR_PARTS}


def build_ai_car_tiers_for_driver(driver_full_name, team_name):
    """AI mašina: komandos bazė + 2025 sezono forma (stipresni aukštesni tieriai)."""
    base = build_team_base_car_copy(team_name)
    s = DRIVER_2025_STRENGTH.get(driver_full_name, 0.52)
    out = {}
    for i, part in enumerate(CAR_PARTS):
        tier_add = int(round((s - 0.52) * 3.05 + math.sin(i * 1.12 + s * 2.5)))
        out[part] = max(0, min(MAX_CAR_TIER, base[part] + tier_add))
    return out


def _tier_progress_to_beast(tier):
    return max(0.0, min(1.0, int(tier) / float(MAX_CAR_TIER)))


def player_pace_from_upgrade_curves():
    """Lenktynių greičio daugiklis pagal naują dalių kreivę (žaidėjo mašina)."""
    acc = 0.0
    for p in CAR_PARTS:
        f = _tier_progress_to_beast(car_part_tiers.get(p, 0))
        c = PART_UPGRADE_CURVES.get(p, {})
        acc += f * (
            c.get("speed", 0)
            + c.get("cornering", 0)
            + c.get("power_unit", 0)
            + c.get("qualifying", 0)
            + c.get("overtake", 0) * 0.22
        )
    return 0.66 + min(0.58, acc * 0.00105)


def pace_tier_multiplier(part_tiers):
    tot = sum(int(part_tiers.get(p, 0)) for p in CAR_PARTS)
    return 0.66 + (tot / max(1, len(CAR_PARTS) * MAX_CAR_TIER)) * 0.56


def driver_skill_multiplier(driver_full_name):
    st = DRIVER_STATS.get(driver_full_name)
    if not st:
        return 1.0
    avg = sum(st.values()) / max(len(st), 1)
    return 0.95 + (avg / 20.0) * 0.1


def player_upgrade_pace_bonus():
    return 1.0 + min(0.07, sum(int(upgrade_levels[k]) for k in upgrade_levels) * 0.001)


def race_ds_from_car(part_tiers, driver_full_name, is_player_custom):
    base = 0.00033
    if is_player_custom:
        m = player_pace_from_upgrade_curves()
        return base * m * player_upgrade_pace_bonus()
    m = pace_tier_multiplier(part_tiers)
    sk = driver_skill_multiplier(driver_full_name)
    form = DRIVER_2025_STRENGTH.get(driver_full_name, 0.52)
    form_mult = 0.72 + (form ** 1.15) * 0.46
    return base * m * sk * form_mult


def driver_short_tag(full_name):
    parts = (full_name or "").split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][:3]).upper()[:8]
    return (full_name or "?")[:8].upper()


def player_short_tag():
    n = (driver_data["Name"]["text"] or "P").strip()
    s = (driver_data["Surname"]["text"] or "LYR").strip()
    if n and s:
        return (n[0] + s[:3]).upper()[:8]
    return "PLY"


def team_color_rgb(team_name):
    for t in F1_TEAMS:
        if t["name"] == team_name:
            return t["color"]
    return (180, 180, 180)


def sync_roster_after_teammate_pick():
    global replaced_driver_name, teammate_car_tiers
    team = winning_team_name
    pair = TEAM_DRIVERS_2025.get(team, [])
    if len(pair) < 2 or not teammate_result:
        replaced_driver_name = ""
        teammate_car_tiers = build_team_base_car_copy(team) if team else {p: 2 for p in CAR_PARTS}
        return
    replaced_driver_name = next((d for d in pair if d != teammate_result), pair[0])
    teammate_car_tiers = build_ai_car_tiers_for_driver(teammate_result, team)


def build_race_cars_list():
    """Tas pats tinklelis kaip lenktynėse (be t pozicijų)."""
    out = []
    player_slot = ""
    teammate_slot = ""
    if winning_team_name:
        pair = TEAM_DRIVERS_2025.get(winning_team_name, [])
        if len(pair) >= 2:
            if teammate_result in pair:
                teammate_slot = teammate_result
                player_slot = next((d for d in pair if d != teammate_slot), pair[0])
            else:
                teammate_slot = pair[0]
                player_slot = pair[1]
    team_order = [t["name"] for t in F1_TEAMS]
    for team in team_order:
        for driver_full in TEAM_DRIVERS_2025.get(team, []):
            col = team_color_rgb(team)
            if team == winning_team_name and driver_full == player_slot:
                ptiers = {p: max(0, min(MAX_CAR_TIER, int(car_part_tiers[p]))) for p in CAR_PARTS}
                ds = race_ds_from_car(ptiers, "", True)
                out.append({
                    "t": 0.0,
                    "ds": ds,
                    "color": col,
                    "tag": player_short_tag(),
                    "team": team,
                    "driver": "__PLAYER__",
                    "is_player": True,
                    "part_tiers": ptiers,
                })
            elif team == winning_team_name and driver_full == teammate_slot:
                ttiers = build_ai_car_tiers_for_driver(driver_full, team)
                ds = race_ds_from_car(ttiers, driver_full, False)
                out.append({
                    "t": 0.0,
                    "ds": ds,
                    "color": col,
                    "tag": driver_short_tag(driver_full),
                    "team": team,
                    "driver": driver_full,
                    "is_player": False,
                    "part_tiers": ttiers,
                })
            elif team == winning_team_name:
                continue
            else:
                otiers = build_ai_car_tiers_for_driver(driver_full, team)
                ds = race_ds_from_car(otiers, driver_full, False)
                out.append({
                    "t": 0.0,
                    "ds": ds,
                    "color": col,
                    "tag": driver_short_tag(driver_full),
                    "team": team,
                    "driver": driver_full,
                    "is_player": False,
                    "part_tiers": otiers,
                })
    if len(out) == 0:
        out.append({
            "t": 0.0,
            "ds": 0.0004,
            "color": (220, 40, 40),
            "tag": "YOU",
            "team": "",
            "driver": "__PLAYER__",
            "is_player": True,
            "part_tiers": {p: 0 for p in CAR_PARTS},
        })
    return out


def sync_pre_race_provisional_grid_from_championship():
    """Prieš kvalifikaciją: pre_race_grid pagal čempionato taškus (tada ds)."""
    cars = build_race_cars_list()
    cars.sort(key=lambda c: (-get_championship_points_for_car(c), -float(c.get("ds", 0.0))))
    pre_race_grid[:] = cars


def draw_led_border_rect(rect, layers=10, thick=3):
    """Animuotas LED rėmelis aplink pygame.Rect."""
    t = pygame.time.get_ticks() * 0.004
    for i in range(layers):
        inset = i * 2
        if rect.width <= inset * 2 or rect.height <= inset * 2:
            break
        r = pygame.Rect(rect.x + inset, rect.y + inset, rect.width - 2 * inset, rect.height - 2 * inset)
        c = get_led_color(rect.x * 0.05 + i * 22 + t * 40)
        w = max(1, thick - i // 3)
        pygame.draw.rect(screen, c, r, width=w, border_radius=min(12, 4 + i))


def draw_thin_led_border_rect(rect):
    """Labai plonas animuotas LED rėmelis (1 px, keli sluoksniai)."""
    t = pygame.time.get_ticks() * 0.008
    for i in range(2):
        inset = i
        if rect.width <= 2 * inset + 4 or rect.height <= 2 * inset + 4:
            break
        rr = pygame.Rect(rect.x + inset, rect.y + inset, rect.width - 2 * inset, rect.height - 2 * inset)
        br = max(8, 12 - i * 2)
        hue = 0.5 + 0.5 * math.sin(t + i * 0.9)
        g = int(70 + 130 * hue)
        b = int(160 + 80 * hue)
        r = int(30 + 110 * (1.0 - hue))
        pygame.draw.rect(screen, (r, g, b), rr, width=1, border_radius=br)


def _pre_race_layout():
    """Left: wide grid + PTS; right: session info (top), START RACE bottom with thin LED frame."""
    margin = 16
    left_w = min(540, int(WIDTH * 0.42))
    split_x = margin + left_w
    gap = 12
    right_x = split_x + gap
    right_w = WIDTH - right_x - margin
    top_y = 44
    btn_h = 58
    btn_y = HEIGHT - margin - btn_h
    btn = pygame.Rect(right_x + 10, btn_y, right_w - 20, btn_h)
    gap_above_btn = 14
    info_h = max(210, btn_y - gap_above_btn - top_y)
    info_rect = pygame.Rect(right_x, top_y, right_w, info_h)
    grid_rect = pygame.Rect(margin, top_y, left_w, HEIGHT - top_y - margin)
    return {"grid_rect": grid_rect, "info_rect": info_rect, "btn": btn, "right_w": right_w}


def pre_race_start_button_rect():
    return _pre_race_layout()["btn"]


def draw_pre_race_screen():
    """Pre-race: left grid (larger text + PTS), right session info (English, label: value lines), START RACE bottom-right with thin LED border."""
    layout = _pre_race_layout()
    grid_outer = layout["grid_rect"]
    info_outer = layout["info_rect"]
    btn = layout["btn"]

    screen.fill(BLACK)
    for drop in rain_drops:
        drop.fall()
        drop.draw(get_led_color(drop.x + 140))

    draw_text_with_outline("ESC — profile", font_exit, (200, 200, 210), BLACK, 18, 18, align="left")

    pygame.draw.rect(screen, (10, 12, 18), grid_outer, border_radius=10)
    pygame.draw.rect(screen, (70, 85, 110), grid_outer, 1, border_radius=10)
    grid_hdr = "STARTING GRID" if pre_race_qualifying_done else "CHAMPIONSHIP STANDINGS"
    draw_text_with_outline(grid_hdr, pygame.font.SysFont("Arial", 20, bold=True), CYAN, BLACK, grid_outer.centerx, grid_outer.y + 10)

    row_y0 = grid_outer.y + 42
    row_h = 26
    max_rows = min(len(pre_race_grid), int((grid_outer.bottom - row_y0 - 12) // row_h))
    hdr_f = pygame.font.SysFont("Arial", 15, bold=True)
    col_pos = grid_outer.x + 12
    col_team = grid_outer.x + 56
    col_drv = grid_outer.x + 128
    col_pts = grid_outer.right - 52
    screen.blit(hdr_f.render("POS", True, (150, 155, 165)), (col_pos, row_y0 - 22))
    screen.blit(hdr_f.render("TEAM", True, (150, 155, 165)), (col_team, row_y0 - 22))
    screen.blit(hdr_f.render("DRIVER", True, (150, 155, 165)), (col_drv, row_y0 - 22))
    screen.blit(hdr_f.render("PTS", True, (200, 200, 120)), (col_pts, row_y0 - 22))
    cell_f = pygame.font.SysFont("Arial", 16, bold=True)
    any_champ_pts = any(v > 0 for v in championship_points.values())
    for i in range(max_rows):
        car = pre_race_grid[i]
        ry = row_y0 + i * row_h
        hi = car.get("is_player")
        if hi:
            pygame.draw.rect(screen, (26, 38, 68), (grid_outer.x + 6, ry - 2, grid_outer.width - 12, row_h), border_radius=4)
        ab = TEAM_ABBREV.get(car.get("team", ""), "-")[:3]
        tag = car.get("tag", "?")[:16]
        col = WHITE if hi else (205, 205, 210)
        screen.blit(cell_f.render(f"{i + 1}", True, GOLD if i == 0 else col), (col_pos + 2, ry + 2))
        screen.blit(cell_f.render(ab, True, (145, 165, 195)), (col_team, ry + 2))
        screen.blit(cell_f.render(tag, True, col), (col_drv, ry + 2))
        pts_val = get_championship_points_for_car(car) if any_champ_pts else 0
        screen.blit(cell_f.render(str(pts_val), True, (220, 200, 120)), (col_pts, ry + 2))

    gp = get_current_gp()
    ncal = len(SEASON_GP_CALENDAR)
    rno = season_gp_index % ncal + 1
    pygame.draw.rect(screen, (8, 10, 16), info_outer, border_radius=10)
    pygame.draw.rect(screen, (75, 95, 120), info_outer, 1, border_radius=10)

    ix = info_outer.x + 14
    iy = info_outer.y + 10
    title_f = pygame.font.SysFont("Arial", 18, bold=True)
    round_sub = f"ROUND {rno} / {ncal}"
    draw_text_with_outline(round_sub, title_f, ORANGE, BLACK, ix, iy, align="left")
    iy += 26
    line_f = pygame.font.SysFont("Arial", 15, bold=True)
    for line in get_gp_pre_race_info_lines_en(gp):
        draw_text_with_outline(line, line_f, LIGHT_GRAY, BLACK, ix, iy, align="left")
        iy += 22
        if iy > info_outer.bottom - 36:
            break

    small = pygame.font.SysFont("Arial", 12, bold=True)
    iy = info_outer.bottom - 30
    upcoming = [SEASON_GP_CALENDAR[j].get("short_en", SEASON_GP_CALENDAR[j]["short_lt"]) for j in range(season_gp_index + 1, ncal)]
    upcoming_txt = "Next: " + ", ".join(upcoming) if upcoming else "Next: new cycle from Brazil."
    draw_text_with_outline(upcoming_txt[:80] + ("…" if len(upcoming_txt) > 80 else ""), small, (120, 125, 140), BLACK, ix, iy, align="left")
    draw_text_with_outline(f"Team: {winning_team_name or '-'}", small, (140, 145, 160), BLACK, ix, iy + 14, align="left")

    pygame.draw.rect(screen, (22, 28, 38), btn, border_radius=10)
    draw_thin_led_border_rect(btn)
    btn_txt = "START RACE" if pre_race_qualifying_done else "GO TO QUALIFYING"
    draw_text_with_outline(btn_txt, pygame.font.SysFont("Arial", 26, bold=True), WHITE, BLACK, btn.centerx, btn.centery)


def _draw_pit_speed_markings(poly):
    """Baltos brūkšninės linijos palei pit stačiakampį (ilgosios kraštinės)."""
    if len(poly) < 4:
        return
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    dash, gap = 10, 8
    x = x0 + 3
    while x < x1 - 6:
        xe = min(x + dash, x1 - 3)
        pygame.draw.line(screen, (232, 232, 240), (int(x), int(y0 + 3)), (int(xe), int(y0 + 3)), 2)
        pygame.draw.line(screen, (232, 232, 240), (int(x), int(y1 - 3)), (int(xe), int(y1 - 3)), 2)
        x += dash + gap
    y = y0 + 5
    while y < y1 - 6:
        ye = min(y + dash, y1 - 3)
        pygame.draw.line(screen, (232, 232, 240), (int(x0 + 3), int(y)), (int(x0 + 3), int(ye)), 2)
        pygame.draw.line(screen, (232, 232, 240), (int(x1 - 3), int(y)), (int(x1 - 3), int(ye)), 2)
        y += dash + gap


def _draw_curbs_along_outer(edge, step=6, curb_len=5):
    """Raudonai/baltai segmentuoti kerbai palei trasos išorę."""
    n = len(edge)
    if n < 8:
        return
    for i in range(0, n, step):
        ox, oy = edge[i]
        cx, cy = TRACK_POINTS[i % len(TRACK_POINTS)]
        vx, vy = ox - cx, oy - cy
        ln = math.hypot(vx, vy) or 1.0
        vx /= ln
        vy /= ln
        c0 = (int(ox + vx * 1.5), int(oy + vy * 1.5))
        c1 = (int(ox + vx * curb_len), int(oy + vy * curb_len))
        col = (188, 28, 42) if (i // step) % 2 == 0 else (240, 238, 245)
        pygame.draw.line(screen, col, c0, c1, 3)


def _draw_center_road_line(points):
    """Plona kelio vidurio linija per trasos centrą."""
    if len(points) < 6:
        return
    center = [(int(p[0]), int(p[1])) for p in points[::2]]
    if len(center) >= 3:
        pygame.draw.lines(screen, (172, 176, 184), True, center, width=1)


def _draw_outer_f1_stripe(edge):
    """Raudona/balta juosta palei visą trasos išorę."""
    n = len(edge)
    if n < 10:
        return
    block = 3
    for i in range(n):
        p = edge[i]
        q = edge[(i + 1) % n]
        col = (206, 32, 42) if ((i // block) % 2 == 0) else (242, 242, 246)
        pygame.draw.line(screen, col, p, q, 4)


def _draw_start_finish_line():
    """Starto/finišo linija per trasą ties visų garažų viduriu."""
    if len(TRACK_POINTS) < 20 or len(TRACK_INNER) != len(TRACK_POINTS) or len(TRACK_OUTER) != len(TRACK_POINTS):
        return
    idx = _start_finish_index()
    a = TRACK_INNER[idx]
    b = TRACK_OUTER[idx]
    pygame.draw.line(screen, (246, 246, 250), a, b, 5)
    # Smulkus „checker“ efektas ant baltos linijos.
    steps = 10
    for k in range(steps):
        t0 = k / steps
        t1 = (k + 0.5) / steps
        x0 = int(a[0] * (1.0 - t0) + b[0] * t0)
        y0 = int(a[1] * (1.0 - t0) + b[1] * t0)
        x1 = int(a[0] * (1.0 - t1) + b[0] * t1)
        y1 = int(a[1] * (1.0 - t1) + b[1] * t1)
        if k % 2 == 0:
            pygame.draw.line(screen, (22, 22, 24), (x0, y0), (x1, y1), 3)


def _start_finish_index():
    if len(TRACK_POINTS) < 4:
        return 0
    if PIT_GARAGE_RECTS:
        gx = int(sum(r.centerx for r in PIT_GARAGE_RECTS) / len(PIT_GARAGE_RECTS))
        gy = int(sum(r.centery for r in PIT_GARAGE_RECTS) / len(PIT_GARAGE_RECTS))
        return min(
            range(len(TRACK_POINTS)),
            key=lambda i: (TRACK_POINTS[i][0] - gx) ** 2 + (TRACK_POINTS[i][1] - gy) ** 2,
        )
    i0, _ = _find_pit_straight_indices()
    return min(len(TRACK_POINTS) - 1, max(2, i0 + 2))


def _draw_infield_lake_and_environment():
    """Aplinkos akcentai be ežero/pastatų; medžiai piešiami tik toliau nuo trasos."""
    if len(TRACK_INNER) < 6:
        return
    xs = [p[0] for p in TRACK_INNER]
    ys = [p[1] for p in TRACK_INNER]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    # Keli „krūmai/medžiai“ aplink trasą, bet ne ant asfalto.
    deco = random.Random(7)
    for _ in range(42):
        rx = deco.randint(18, WIDTH - 18)
        ry = deco.randint(58, HEIGHT - 18)
        # Saugus filtras: nieko nepiešiam per arti trasos juostos.
        if _point_min_dist_to_closed_polyline(rx, ry, TRACK_POINTS) < 28:
            continue
        rad = deco.randint(3, 7)
        col = (10, deco.randint(72, 118), 18)
        pygame.draw.circle(screen, col, (rx, ry), rad)


def _draw_interlagos_backdrop(grass_rgb, runoff_rgb):
    """Dangus, pieva su atspalviais, tolimos medžių siluetai — Interlagos atmosfera."""
    g = grass_rgb
    pygame.draw.rect(screen, (88, 128, 178), (0, 0, WIDTH, 46))
    pygame.draw.rect(screen, (108, 148, 198), (0, 46, WIDTH, 28))
    y0 = 74
    y_max = HEIGHT - 100
    band_h = max(24, (y_max - y0) // 4)
    shades = (_blend_rgb(g, 0.58), _blend_rgb(g, 0.76), _blend_rgb(g, 0.9), g)
    for col in shades:
        y1 = min(y_max, y0 + band_h)
        pygame.draw.rect(screen, col, (0, y0, WIDTH, max(1, y1 - y0)))
        y0 = y1
        if y0 >= y_max:
            break
    pygame.draw.rect(screen, _blend_rgb(runoff_rgb, 0.9), (0, y_max, WIDTH, HEIGHT - y_max))
    tre = random.Random(42)
    for k in range(34):
        bx = int(k * (WIDTH // 26) + tre.randint(-10, 20))
        bw = tre.randint(22, 50)
        bh = tre.randint(26, 54)
        pygame.draw.ellipse(screen, (8, 34, 12), (bx, HEIGHT - bh - 8, bw, bh))


def _blend_rgb(rgb, factor):
    """factor < 1 tamsina, factor > 1 šviesina (ribojama 255)."""
    r, g, b = rgb
    if factor <= 1.0:
        return (max(0, int(r * factor)), max(0, int(g * factor)), max(0, int(b * factor)))
    return (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)))


def draw_track_base():
    """Piešia trasą (be antraščių) — žalia pieva, asfaltas ir pit be kerbų / baltų linijų."""
    if len(TRACK_OUTER) < 3 or len(TRACK_INNER) < 3:
        rebuild_season_track_geometry()
    gp = get_current_gp()
    grass = gp.get("grass_rgb", (18, 62, 24))
    inf = gp.get("infield_rgb", TRACK_INFIELD_COLOR)
    screen.fill(grass)
    if len(TRACK_OUTER) >= 3 and len(TRACK_INNER) >= 3:
        asphalt = list(TRACK_OUTER) + list(reversed(TRACK_INNER))
        base_asphalt = (46, 48, 52)
        mid_asphalt = (42, 44, 48)
        pygame.draw.polygon(screen, base_asphalt, asphalt)
        pygame.draw.polygon(screen, mid_asphalt, asphalt, width=2)
        pygame.draw.polygon(screen, inf, TRACK_INNER)
        _draw_infield_lake_and_environment()
        _draw_center_road_line(TRACK_POINTS)
        _draw_outer_f1_stripe(TRACK_OUTER)
        _draw_start_finish_line()
        # Švelnios asfalto briaunos (panašiau į realų kelią).
        pygame.draw.lines(screen, (86, 88, 95), True, TRACK_INNER, width=1)
        pygame.draw.lines(screen, (30, 32, 36), True, TRACK_OUTER, width=2)

        # 10 komandų garažų su komandos spalvomis ant tiesiosios.
        n_teams = min(len(PIT_GARAGE_RECTS), len(F1_TEAMS))
        for i in range(n_teams):
            gr0 = PIT_GARAGE_RECTS[i]
            # Mažas shrink, kad tarp garažų matytųsi bent keli px tarpas.
            gr = gr0.inflate(-2, -2)
            if gr.w < 6 or gr.h < 6:
                continue
            tc = F1_TEAMS[i]["color"]
            body = (max(20, int(tc[0] * 0.45)), max(20, int(tc[1] * 0.45)), max(20, int(tc[2] * 0.45)))
            pygame.draw.rect(screen, body, gr, border_radius=2)
            roof_h = max(3, min(5, gr.h // 3))
            roof = pygame.Rect(gr.x + 1, gr.y + 1, gr.w - 2, roof_h)
            pygame.draw.rect(screen, tc, roof, border_radius=2)
            pygame.draw.rect(screen, (18, 20, 24), gr, 1, border_radius=2)
    else:
        fallback_rect = pygame.Rect(180, 130, WIDTH - 360, HEIGHT - 250)
        pygame.draw.ellipse(screen, (44, 46, 52), fallback_rect)
        pygame.draw.ellipse(screen, inf, fallback_rect.inflate(-120, -80))
        pygame.draw.ellipse(screen, (34, 38, 42), fallback_rect.inflate(-120, -80), 1)
        pygame.draw.ellipse(screen, (32, 34, 38), fallback_rect, 1)


def clone_car_for_qualifying(c):
    n = dict(c)
    if isinstance(c.get("part_tiers"), dict):
        n["part_tiers"] = dict(c["part_tiers"])
    n["qual_q1_time"] = None
    n["qual_q2_time"] = None
    n["qual_q3_time"] = None
    return n


def car_qualifying_parts_bonus(part_tiers):
    acc = 0.0
    for p in CAR_PARTS:
        f = _tier_progress_to_beast(int(part_tiers.get(p, 0)))
        cu = PART_UPGRADE_CURVES.get(p, {})
        acc += f * cu.get("qualifying", 0)
    return 1.0 + min(0.24, acc * 0.00115)


def qualifying_best_lap_center_seconds(car, rng, track_scale=1.0):
    """Geriausio sim. rato centras (sek.): mažiau = greičiau — ds, Qualifying stat, mašina."""
    ds = max(1e-9, float(car.get("ds", 0.00033)))
    if car.get("is_player"):
        qlv = int(upgrade_levels.get("Qualifying Upgrade", 0))
        q_stat = 11 + min(9, qlv)
        qfac = 0.86 + (q_stat / 20.0) * 0.22
    else:
        drv = car.get("driver", "")
        st = DRIVER_STATS.get(drv, {})
        qv = st.get("Qualifying", 12)
        qfac = 0.84 + (qv / 20.0) * 0.26
    qfac *= car_qualifying_parts_bonus(car.get("part_tiers", {}))
    pace = ds * qfac
    base = 69.2
    noise = rng.gauss(0, 0.14)
    t = (base * (0.00038 / pace)) * track_scale + noise
    return max(62.0, min(88.0, t))


def qual_generate_three_lap_times(car, rng, track_scale=1.0):
    """Trys skirtingi sim. ratai (l1 > l2 > l3), galutinis rezultatas = geriausias."""
    best = qualifying_best_lap_center_seconds(car, rng, track_scale=track_scale)
    l3 = best + rng.uniform(-0.05, 0.06)
    l2 = l3 + rng.uniform(0.16, 0.48) + rng.gauss(0, 0.035)
    l1 = l2 + rng.uniform(0.22, 0.62) + rng.gauss(0, 0.04)
    return l1, l2, l3, min(l1, l2, l3)


def format_qual_time_msm(t_sec):
    """Rodomas laikas: min:sek.milisek (pvz. 1:09.247)."""
    if t_sec is None:
        return "--:--.---"
    t_sec = float(t_sec)
    if t_sec <= 0 or math.isnan(t_sec):
        return "--:--.---"
    t_sec = max(0.0, t_sec)
    ms_total = int(round(t_sec * 1000))
    minutes = ms_total // 60000
    rem = ms_total % 60000
    seconds = rem // 1000
    millis = rem % 1000
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def qual_display_name(car):
    if car.get("is_player"):
        n = (driver_data.get("Name") or {}).get("text", "").strip()
        s = (driver_data.get("Surname") or {}).get("text", "").strip()
        if n or s:
            return f"{n} {s}".strip()[:22]
        return car.get("tag", "YOU")
    return (car.get("driver") or car.get("tag") or "?")[:26]


def setup_qualifying_session_from_profile():
    """Paruošia kvalifikaciją po „Start race“ profilyje."""
    global qual_session_cars, qual_random, qual_phase, qual_anim_rows, qual_surv_q1, qual_surv_q2
    global qual_display_rank_prev, qual_display_rank_curr, qual_anim_start_tick
    rebuild_season_track_geometry()
    qual_session_cars[:] = [clone_car_for_qualifying(c) for c in build_race_cars_list()]
    qual_random = random.Random(pygame.time.get_ticks() % 1_000_000_007)
    qual_phase = ""
    qual_anim_rows = []
    qual_surv_q1 = set()
    qual_surv_q2 = set()
    qual_display_rank_prev = {}
    qual_display_rank_curr = {}
    qual_anim_start_tick = 0


def qual_start_q1_animation():
    global qual_phase, qual_anim_rows, qual_anim_start_tick, qual_display_rank_prev, qual_display_rank_curr
    qual_anim_rows = []
    for i in range(len(qual_session_cars)):
        c = qual_session_cars[i]
        l1, l2, l3, best = qual_generate_three_lap_times(c, qual_random, track_scale=1.0)
        start_disp = l1 + qual_random.uniform(0.45, 1.25)
        qual_anim_rows.append(
            {"idx": i, "lap1": l1, "lap2": l2, "lap3": l3, "targ": best, "start": start_disp, "disp": start_disp}
        )
    qual_anim_start_tick = pygame.time.get_ticks()
    qual_phase = "q1_anim"
    qual_display_rank_prev = {}
    qual_display_rank_curr = {}


def qual_start_q2_animation():
    global qual_phase, qual_anim_rows, qual_anim_start_tick, qual_display_rank_prev, qual_display_rank_curr
    qual_anim_rows = []
    for i in sorted(qual_surv_q1):
        c = qual_session_cars[i]
        l1, l2, l3, best = qual_generate_three_lap_times(c, qual_random, track_scale=0.992)
        start_disp = l1 + qual_random.uniform(0.35, 1.05)
        qual_anim_rows.append(
            {"idx": i, "lap1": l1, "lap2": l2, "lap3": l3, "targ": best, "start": start_disp, "disp": start_disp}
        )
    qual_anim_start_tick = pygame.time.get_ticks()
    qual_phase = "q2_anim"
    qual_display_rank_prev = {}
    qual_display_rank_curr = {}


def qual_start_q3_animation():
    global qual_phase, qual_anim_rows, qual_anim_start_tick, qual_display_rank_prev, qual_display_rank_curr
    qual_anim_rows = []
    for i in sorted(qual_surv_q2):
        c = qual_session_cars[i]
        l1, l2, l3, best = qual_generate_three_lap_times(c, qual_random, track_scale=0.985)
        start_disp = l1 + qual_random.uniform(0.28, 0.88)
        qual_anim_rows.append(
            {"idx": i, "lap1": l1, "lap2": l2, "lap3": l3, "targ": best, "start": start_disp, "disp": start_disp}
        )
    qual_anim_start_tick = pygame.time.get_ticks()
    qual_phase = "q3_anim"
    qual_display_rank_prev = {}
    qual_display_rank_curr = {}


def qualifying_advance_from_anim():
    """Animacijos pabaiga: užfiksuoti laikus ir pereiti į tarpinį rezultatų ekraną."""
    global qual_phase, qual_surv_q1, qual_surv_q2
    if qual_phase == "q1_anim":
        for row in qual_anim_rows:
            qual_session_cars[row["idx"]]["qual_q1_time"] = row["targ"]
        ordered = sorted(qual_anim_rows, key=lambda r: r["targ"])
        qual_surv_q1 = set(r["idx"] for r in ordered[:15])
        qual_phase = "q1_done"
    elif qual_phase == "q2_anim":
        for row in qual_anim_rows:
            qual_session_cars[row["idx"]]["qual_q2_time"] = row["targ"]
        ordered = sorted(qual_anim_rows, key=lambda r: r["targ"])
        qual_surv_q2 = set(r["idx"] for r in ordered[:10])
        qual_phase = "q2_done"
    elif qual_phase == "q3_anim":
        for row in qual_anim_rows:
            qual_session_cars[row["idx"]]["qual_q3_time"] = row["targ"]
        qual_phase = "q3_done"


def qual_unified_anim_rankings():
    """Animacijos metu visa lentelė: aktyvūs pagal disp, apačioje Q1 OUT (ir Q2 OUT Q3 etape)."""
    if qual_phase == "q1_anim":
        return [r["idx"] for r in sorted(qual_anim_rows, key=lambda r: r["disp"])]
    if qual_phase == "q2_anim" and qual_surv_q1:
        active = [r["idx"] for r in sorted(qual_anim_rows, key=lambda r: r["disp"])]
        q1e = sorted(
            [i for i in range(len(qual_session_cars)) if i not in qual_surv_q1],
            key=lambda j: qual_session_cars[j]["qual_q1_time"],
        )
        return active + q1e
    if qual_phase == "q3_anim" and qual_surv_q2:
        active = [r["idx"] for r in sorted(qual_anim_rows, key=lambda r: r["disp"])]
        q2e = sorted(qual_surv_q1 - qual_surv_q2, key=lambda j: qual_session_cars[j]["qual_q2_time"])
        q1e = sorted(
            [i for i in range(len(qual_session_cars)) if i not in qual_surv_q1],
            key=lambda j: qual_session_cars[j]["qual_q1_time"],
        )
        return active + q2e + q1e
    return []


def qualifying_tick_frame():
    """Animuotas timing board: 3 ratai (skirtingi laikai), kiekvienas trečdalis animacijos."""
    global qual_anim_rows, qual_display_rank_prev, qual_display_rank_curr
    if game_state != "QUALIFYING_RUN":
        return
    if qual_phase not in ("q1_anim", "q2_anim", "q3_anim"):
        return
    elapsed = pygame.time.get_ticks() - qual_anim_start_tick
    if elapsed >= qual_anim_duration_ms:
        for row in qual_anim_rows:
            row["disp"] = row["targ"]
        qualifying_advance_from_anim()
        return
    alpha = min(1.0, elapsed / float(qual_anim_duration_ms))
    seg_f = alpha * 3.0
    seg = min(2, int(seg_f))
    local = seg_f - float(seg)
    ease_seg = 1.0 - (1.0 - min(1.0, local)) ** 2

    for row in qual_anim_rows:
        l1, l2 = row["lap1"], row["lap2"]
        best = row["targ"]
        start = row["start"]
        if seg == 0:
            row["disp"] = start + (l1 - start) * ease_seg
        elif seg == 1:
            row["disp"] = l1 + (l2 - l1) * ease_seg
        else:
            row["disp"] = l2 + (best - l2) * ease_seg

    order = qual_unified_anim_rankings()
    if not order:
        order = [r["idx"] for r in sorted(qual_anim_rows, key=lambda r: r["disp"])]
    new_ranks = {}
    for pos, idx in enumerate(order, start=1):
        tag = qual_session_cars[idx].get("tag", "?")
        new_ranks[tag] = pos
    qual_display_rank_prev = dict(qual_display_rank_curr)
    qual_display_rank_curr = new_ranks


def qual_apply_results_to_pre_race_grid():
    """F1 taisyklės: P1–P10 iš Q3, P11–P15 iš Q2 lėčiausio penketo, P16–P20 iš Q1 lėčiausio penketo."""
    top10 = sorted(qual_surv_q2, key=lambda i: qual_session_cars[i]["qual_q3_time"])
    q2_ordered = sorted(qual_surv_q1, key=lambda i: qual_session_cars[i]["qual_q2_time"])
    q2_out_sorted = q2_ordered[10:]
    q1_elim = [i for i in range(len(qual_session_cars)) if i not in qual_surv_q1]
    q1_out_sorted = sorted(q1_elim, key=lambda i: qual_session_cars[i]["qual_q1_time"])
    order = top10 + q2_out_sorted + q1_out_sorted
    pre_race_grid[:] = [qual_session_cars[i] for i in order]
    register_championship_drivers_from_grid(pre_race_grid)


def qual_best_time_display(car):
    if car.get("qual_q3_time") is not None:
        return car["qual_q3_time"]
    if car.get("qual_q2_time") is not None:
        return car["qual_q2_time"]
    return car.get("qual_q1_time") or 0.0


def qualifying_intro_button_rect():
    panel = pygame.Rect(WIDTH // 2 - 320, HEIGHT // 2 - 160, 640, 320)
    return pygame.Rect(WIDTH // 2 - 175, panel.bottom - 78, 350, 52)


def draw_qualifying_intro_screen():
    draw_track_base()
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 205))
    screen.blit(ov, (0, 0))
    panel = pygame.Rect(WIDTH // 2 - 320, HEIGHT // 2 - 160, 640, 320)
    pygame.draw.rect(screen, (14, 16, 22), panel, border_radius=14)
    pygame.draw.rect(screen, (80, 120, 180), panel, 2, border_radius=14)
    draw_text_with_outline("QUALIFYING", font_main, ORANGE, BLACK, WIDTH // 2, panel.y + 52)
    draw_text_with_outline("Saturday — one day before race Sunday", font_ui, LIGHT_GRAY, BLACK, WIDTH // 2, panel.y + 108)
    gp = get_current_gp()
    draw_text_with_outline(gp.get("circuit_en", gp.get("circuit_lt", "Grand Prix")), font_ui, WHITE, BLACK, WIDTH // 2, panel.y + 146)
    btn = qualifying_intro_button_rect()
    pygame.draw.rect(screen, (28, 36, 52), btn, border_radius=10)
    draw_thin_led_border_rect(btn)
    draw_text_with_outline("START QUALIFYING", pygame.font.SysFont("Arial", 24, bold=True), WHITE, BLACK, btn.centerx, btn.centery)


def draw_qualifying_run_screen():
    global qual_last_action_rect
    draw_track_base()
    ov_alpha = 150 if qual_phase in ("q1_anim", "q2_anim", "q3_anim") else 175
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, ov_alpha))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(40, 36, WIDTH - 80, HEIGHT - 72)
    pygame.draw.rect(screen, (12, 14, 20), panel, border_radius=12)
    pygame.draw.rect(screen, (65, 90, 130), panel, 2, border_radius=12)

    title = "QUALIFYING"
    if qual_phase == "q1_anim":
        title = "Q1 — LIVE TIMING"
    elif qual_phase == "q1_done":
        title = "Q1 COMPLETE — slowest 5 eliminated"
    elif qual_phase == "q2_anim":
        title = "Q2 — LIVE TIMING (15 drivers)"
    elif qual_phase == "q2_done":
        title = "Q2 COMPLETE — slowest 5 eliminated"
    elif qual_phase == "q3_anim":
        title = "Q3 — POLE SHOOTOUT (10 drivers)"
    elif qual_phase == "q3_done":
        title = "QUALIFYING COMPLETE — starting grid"
    if qual_phase in ("q1_anim", "q2_anim", "q3_anim"):
        elapsed = pygame.time.get_ticks() - qual_anim_start_tick
        if elapsed < qual_anim_duration_ms:
            lap_n = min(3, int(elapsed / float(qual_anim_duration_ms) * 3.0) + 1)
            title = f"{title} — Lap {lap_n}/3"
    draw_text_with_outline(title, pygame.font.SysFont("Arial", 24, bold=True), CYAN, BLACK, panel.centerx, panel.y + 22)

    row_y0 = panel.y + 56
    row_h = 22
    max_rows = int((panel.bottom - row_y0 - 88) // row_h)
    hdr = pygame.font.SysFont("Arial", 13, bold=True)
    col_pos = panel.x + 14
    col_team = panel.x + 48
    col_drv = panel.x + 108
    col_time = panel.right - 118
    screen.blit(hdr.render("POS", True, (140, 145, 155)), (col_pos, row_y0 - 20))
    screen.blit(hdr.render("TM", True, (140, 145, 155)), (col_team, row_y0 - 20))
    screen.blit(hdr.render("DRIVER", True, (140, 145, 155)), (col_drv, row_y0 - 20))
    screen.blit(hdr.render("TIME", True, (140, 145, 155)), (col_time, row_y0 - 20))
    cell = pygame.font.SysFont("Arial", 14, bold=True)

    rows_data = []
    row_by_idx = {r["idx"]: r for r in qual_anim_rows}
    if qual_phase in ("q1_anim", "q2_anim", "q3_anim"):
        order = qual_unified_anim_rankings()
        if not order and qual_phase == "q1_anim":
            order = [r["idx"] for r in sorted(qual_anim_rows, key=lambda r: r["disp"])]
        for pos, idx in enumerate(order[:max_rows], start=1):
            car = qual_session_cars[idx]
            is_q1_out = len(qual_surv_q1) > 0 and idx not in qual_surv_q1
            is_q2_out = len(qual_surv_q2) > 0 and idx in qual_surv_q1 and idx not in qual_surv_q2
            if idx in row_by_idx:
                tsec = row_by_idx[idx]["disp"]
            elif is_q1_out:
                tsec = car["qual_q1_time"]
            elif is_q2_out:
                tsec = car["qual_q2_time"]
            else:
                tsec = 0.0
            rows_data.append((pos, car, tsec, is_q1_out, is_q2_out, False))
    elif qual_phase == "q1_done":
        board = sorted(range(len(qual_session_cars)), key=lambda i: qual_session_cars[i]["qual_q1_time"])
        for pos, idx in enumerate(board[:max_rows], start=1):
            car = qual_session_cars[idx]
            is_q1_out = idx not in qual_surv_q1
            rows_data.append((pos, car, car["qual_q1_time"], is_q1_out, False, False))
    elif qual_phase == "q2_done":
        surv2 = sorted(qual_surv_q2, key=lambda i: qual_session_cars[i]["qual_q2_time"])
        q2e = sorted(qual_surv_q1 - qual_surv_q2, key=lambda i: qual_session_cars[i]["qual_q2_time"])
        q1e = sorted(
            [i for i in range(len(qual_session_cars)) if i not in qual_surv_q1],
            key=lambda i: qual_session_cars[i]["qual_q1_time"],
        )
        full = surv2 + q2e + q1e
        for pos, idx in enumerate(full[:max_rows], start=1):
            car = qual_session_cars[idx]
            is_q1_out = idx not in qual_surv_q1
            is_q2_out = idx in qual_surv_q1 and idx not in qual_surv_q2
            if idx in qual_surv_q2:
                tsec = car["qual_q2_time"]
            elif is_q2_out:
                tsec = car["qual_q2_time"]
            else:
                tsec = car["qual_q1_time"]
            rows_data.append((pos, car, tsec, is_q1_out, is_q2_out, False))
    elif qual_phase == "q3_done":
        top10 = sorted(qual_surv_q2, key=lambda i: qual_session_cars[i]["qual_q3_time"])
        q2e = sorted(qual_surv_q1 - qual_surv_q2, key=lambda i: qual_session_cars[i]["qual_q2_time"])
        q1e = sorted(
            [i for i in range(len(qual_session_cars)) if i not in qual_surv_q1],
            key=lambda i: qual_session_cars[i]["qual_q1_time"],
        )
        full = top10 + q2e + q1e
        for pos, idx in enumerate(full[:max_rows], start=1):
            car = qual_session_cars[idx]
            is_q1_out = idx not in qual_surv_q1
            is_q2_out = idx in qual_surv_q1 and idx not in qual_surv_q2
            if idx in qual_surv_q2:
                tsec = car["qual_q3_time"]
            elif is_q2_out:
                tsec = car["qual_q2_time"]
            else:
                tsec = car["qual_q1_time"]
            rows_data.append((pos, car, tsec, is_q1_out, is_q2_out, pos == 1))

    for pos, car, tsec, is_q1_out, is_q2_out, is_pole in rows_data:
        ry = row_y0 + (pos - 1) * row_h
        tag = car.get("tag", "?")
        rank_guess = pos
        prev = qual_display_rank_prev.get(tag)
        hi = car.get("is_player")
        if is_q1_out:
            row_col = (72, 18, 28)
        elif is_q2_out:
            row_col = (52, 22, 30)
        elif hi:
            row_col = (26, 48, 78)
        else:
            row_col = (20, 22, 28)
        pygame.draw.rect(screen, row_col, (panel.x + 8, ry - 1, panel.width - 16, row_h), border_radius=4)
        if prev is not None and prev > rank_guess and qual_phase in ("q1_anim", "q2_anim", "q3_anim"):
            pygame.draw.rect(screen, (30, 90, 45), (panel.x + 8, ry - 1, panel.width - 16, row_h), 1, border_radius=4)
        if is_pole:
            pygame.draw.rect(screen, (120, 90, 20), (panel.x + 8, ry - 1, panel.width - 16, row_h), 1, border_radius=4)
        ab = TEAM_ABBREV.get(car.get("team", ""), "-")[:3]
        tstr = format_qual_time_msm(tsec) if isinstance(tsec, (int, float)) else str(tsec)
        if is_q1_out or is_q2_out:
            cdrv = (255, 160, 160) if hi else (255, 190, 190)
        else:
            cdrv = GOLD if hi else WHITE
        screen.blit(cell.render(str(pos), True, GOLD if pos == 1 else (200, 200, 205)), (col_pos + 2, ry + 2))
        screen.blit(cell.render(ab, True, (150, 165, 190)), (col_team, ry + 2))
        screen.blit(cell.render(qual_display_name(car)[:20], True, cdrv), (col_drv, ry + 2))
        screen.blit(cell.render(tstr, True, (210, 220, 235)), (col_time, ry + 2))

    btn = pygame.Rect(panel.centerx - 180, panel.bottom - 58, 360, 46)
    pygame.draw.rect(screen, (26, 34, 48), btn, border_radius=10)
    draw_thin_led_border_rect(btn)
    label = "CONTINUE"
    if qual_phase == "q1_done":
        label = "START Q2"
    elif qual_phase == "q2_done":
        label = "START Q3"
    elif qual_phase == "q3_done":
        label = "START RACE"
    if qual_phase in ("q1_anim", "q2_anim", "q3_anim"):
        label = ""
    if label:
        draw_text_with_outline(label, pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, btn.centerx, btn.centery)
    qual_last_action_rect = btn if label else pygame.Rect(0, 0, 0, 0)


def _track_xy_and_tangent_at_s(dist_s):
    """Returns (x,y,tx,ty) on closed centerline by traveled distance."""
    n = len(TRACK_POINTS)
    if n < 2 or len(TRACK_CUM) < n + 1 or TRACK_TOTAL <= 1e-9:
        return WIDTH * 0.5, HEIGHT * 0.5, 1.0, 0.0
    s = float(dist_s) % float(TRACK_TOTAL)
    i = 0
    while i < n and TRACK_CUM[i + 1] < s:
        i += 1
    i = min(n - 1, i)
    a = TRACK_POINTS[i]
    b = TRACK_POINTS[(i + 1) % n]
    sa = TRACK_CUM[i]
    sb = TRACK_CUM[i + 1]
    seg = max(1e-9, sb - sa)
    t = max(0.0, min(1.0, (s - sa) / seg))
    x = a[0] * (1.0 - t) + b[0] * t
    y = a[1] * (1.0 - t) + b[1] * t
    tx = b[0] - a[0]
    ty = b[1] - a[1]
    ln = math.hypot(tx, ty) or 1.0
    return x, y, tx / ln, ty / ln


def _weather_is_wet_label(label):
    s = str(label).lower()
    return ("rain" in s) or ("lietus" in s) or ("storm" in s) or ("wet" in s)


def _pick_ai_tyre(weather_label):
    wet = _weather_is_wet_label(weather_label)
    if wet:
        return random.choices(["WET", "INTER"], weights=[60, 40], k=1)[0]
    return random.choices(["SOFT", "MEDIUM", "HARD"], weights=[32, 48, 20], k=1)[0]


def init_race_setup_from_grid():
    global race_setup_selected_tyre, race_setup_weather, race_setup_tyre_rects, race_setup_btn_rect
    gp = get_current_gp()
    race_setup_selected_tyre = "MEDIUM"
    race_setup_weather = gp.get("air_condition_en", gp.get("air_condition_lt", "Dry"))
    race_setup_tyre_rects = {}
    race_setup_btn_rect = pygame.Rect(0, 0, 0, 0)


def _grid_order_for_race():
    if pre_race_grid:
        return list(pre_race_grid)
    return build_race_cars_list()


def start_race_session_from_setup():
    global race_session_cars, race_phase, race_phase_start_ms, race_start_line_idx, race_fastest_lap
    global race_elapsed_start_ms, race_final_order, race_player_pit_request, race_pit_entry_s
    global race_finish_continue_rect, race_points_awarded, race_podium_rows
    global race_safety_car_active, race_safety_car_end_ms, race_safety_car_used
    global race_fastest_popup_text, race_fastest_popup_until_ms, race_finish_order
    rebuild_season_track_geometry()
    order = _grid_order_for_race()
    n = len(order)
    if n <= 0:
        race_session_cars = []
        race_phase = "idle"
        return
    race_start_line_idx = _start_finish_index()
    pit_in_idx, _ = _find_pit_straight_indices()
    pit_in_idx = max(0, min(len(TRACK_POINTS) - 1, pit_in_idx))
    race_pit_entry_s = TRACK_CUM[pit_in_idx] if pit_in_idx < len(TRACK_CUM) else 0.0
    base_s = TRACK_CUM[race_start_line_idx] if race_start_line_idx < len(TRACK_CUM) else 0.0
    row_gap = TRACK_HALF_WIDTH * 2.7
    race_session_cars = []
    wet = _weather_is_wet_label(race_setup_weather)
    for pos, car in enumerate(order):
        row = pos // 2
        side = -1.0 if (pos % 2 == 0) else 1.0
        st = dict(car)
        st["grid_pos"] = pos + 1
        # Visi vienodas lap skaitiklis (0), grid tik per s — kad visi finišuotų po tiek pat ratų.
        st["lap"] = 0
        st["s"] = (base_s - row * row_gap) % TRACK_TOTAL
        st["grid_back_m"] = float(row * row_gap)
        st["start_cross_pending"] = (((st["s"] - base_s) % max(1e-9, TRACK_TOTAL)) > 1.0)
        st["lane_side"] = side
        st["last_cross_ms"] = pygame.time.get_ticks()
        st["best_lap_ms"] = None
        st["tyre"] = race_setup_selected_tyre if st.get("is_player") else _pick_ai_tyre(race_setup_weather)
        # Dinaminė rato forma: fastest lap galimybė ne vienam vairuotojui.
        st["lap_variation"] = max(0.93, min(1.08, random.gauss(1.0, 0.022)))
        st["tyre_age"] = 0.0
        st["pit_count"] = 0
        st["in_pit"] = False
        st["pit_timer"] = 0.0
        st["pit_elapsed"] = 0.0
        st["pit_total"] = 0.0
        if st.get("is_player"):
            st["pit_avg_s"] = max(1.6, float(get_player_car_showroom_stats().get("pit_s", 2.6)))
        else:
            st["pit_avg_s"] = max(2.0, min(3.8, 2.9 - min(0.45, float(st.get("ds", 0.00033)) * 700.0) + random.uniform(-0.18, 0.18)))
        st["pit_plan_lap"] = None
        st["pit_request"] = False
        st["pit_request_reason"] = None  # None | "manual" | "mandatory" | "tyre"
        st["race_finished"] = False
        wear_laps = float(RACE_TYRE_COMPOUNDS[st["tyre"]]["wear_laps"])
        if not st.get("is_player"):
            if wet:
                st["pit_plan_lap"] = None
            else:
                # 10-15 lap sim: dažnai 0-1 sustojimas pagal dėvėjimą.
                if wear_laps < sim_race_laps_this_round * 0.82:
                    st["pit_plan_lap"] = max(4, min(sim_race_laps_this_round - 3, int(wear_laps * random.uniform(0.72, 0.9))))
                else:
                    st["pit_plan_lap"] = None
        race_session_cars.append(st)
    race_fastest_lap = {"car_idx": None, "ms": None}
    race_phase = "grid"
    race_phase_start_ms = pygame.time.get_ticks()
    race_elapsed_start_ms = pygame.time.get_ticks()
    race_final_order = []
    race_player_pit_request = False
    race_finish_continue_rect = pygame.Rect(0, 0, 0, 0)
    race_points_awarded = False
    race_podium_rows = []
    race_safety_car_active = False
    race_safety_car_end_ms = 0
    race_safety_car_used = False
    race_fastest_popup_text = ""
    race_fastest_popup_until_ms = 0
    race_auto_podium_deadline_ms = 0
    race_finish_order = []
    race_post_results_rows = []
    race_post_team_rows = []
    race_results_tab = "drivers"


def _pick_next_tyre_after_pit(car, weather_label, laps_left):
    wet = _weather_is_wet_label(weather_label)
    if wet:
        return "WET" if laps_left > 4 else "INTER"
    if laps_left <= 6:
        return "SOFT"
    if laps_left <= 10:
        return random.choice(["SOFT", "MEDIUM"])
    return random.choice(["MEDIUM", "HARD"])


def _race_progress_value(car):
    if TRACK_TOTAL <= 1e-9:
        return 0.0
    start_s = TRACK_CUM[race_start_line_idx] if race_start_line_idx < len(TRACK_CUM) else 0.0
    rel = (float(car.get("s", 0.0)) - start_s) % TRACK_TOTAL
    prog = float(car.get("lap", 0)) * TRACK_TOTAL + rel
    # Jei bolidas startavo prieš pat start/finišo liniją, iki pirmo kirtimo laikom jį "už linijos".
    if car.get("start_cross_pending"):
        prog -= TRACK_TOTAL
    # Grid fazėje išlaikom starto išdėstymą; vos prasidėjus lenktynėms rikiuojam tik pagal realų progresą.
    if race_phase in ("grid", "lights"):
        prog -= float(car.get("grid_back_m", 0.0))
    return prog


def _race_live_order_indices():
    """Gyvas orderis: finišavę užrakinti pagal realią finišo seką, likę pagal progresą."""
    locked = [i for i in race_finish_order if 0 <= i < len(race_session_cars)]
    locked_set = set(locked)
    active = [i for i in range(len(race_session_cars)) if i not in locked_set]
    active_sorted = sorted(active, key=lambda i: _race_progress_value(race_session_cars[i]), reverse=True)
    return locked + active_sorted


def _race_car_speed(car):
    ds = float(car.get("ds", 0.00033))
    base = 150.0 + ds * 220000.0
    tyre = RACE_TYRE_COMPOUNDS.get(car.get("tyre", "MEDIUM"), RACE_TYRE_COMPOUNDS["MEDIUM"])
    wear_laps = max(1.0, float(tyre["wear_laps"]))
    age_ratio = min(2.0, float(car.get("tyre_age", 0.0)) / wear_laps)
    wear_drop = max(0.80, 1.0 - 0.14 * max(0.0, age_ratio - 0.9))
    lap_variation = float(car.get("lap_variation", 1.0))
    v = base * float(tyre["pace"]) * wear_drop * lap_variation
    if car.get("is_player"):
        if race_player_push_mode == 0:      # viena geltona rodyklė
            v *= 0.965
        elif race_player_push_mode == 2:    # trys raudonos rodyklės
            v *= 1.035
    if race_safety_car_active:
        v *= 0.68
    return v


def race_tick_frame():
    global race_phase, race_phase_start_ms, race_fastest_lap, race_final_order, race_player_pit_request
    global race_safety_car_active, race_safety_car_end_ms, race_safety_car_used
    global race_fastest_popup_text, race_fastest_popup_until_ms
    global race_auto_podium_deadline_ms, race_finish_order
    if game_state != "RACE" or not race_session_cars:
        return
    now = pygame.time.get_ticks()
    if race_phase == "grid":
        if now - race_phase_start_ms > 1200:
            race_phase = "lights"
            race_phase_start_ms = now
        return
    if race_phase == "lights":
        if now - race_phase_start_ms > 5200:
            race_phase = "green"
            race_phase_start_ms = now
        return
    if race_phase != "green":
        return

    # Simple safety car event once per race.
    if (not race_safety_car_used) and (not race_safety_car_active) and race_session_cars:
        active_idx = [i for i, c in enumerate(race_session_cars) if not c.get("race_finished")]
        if active_idx:
            lead_idx_tmp = max(active_idx, key=lambda k: _race_progress_value(race_session_cars[k]))
            if int(race_session_cars[lead_idx_tmp].get("lap", 0)) >= 2 and random.random() < 0.0009:
                race_safety_car_active = True
                race_safety_car_used = True
                race_safety_car_end_ms = now + random.randint(9000, 13000)
    if race_safety_car_active and now >= race_safety_car_end_ms:
        race_safety_car_active = False

    dt = min(0.06, clock.get_time() / 1000.0)
    start_s = TRACK_CUM[race_start_line_idx] if race_start_line_idx < len(TRACK_CUM) else 0.0
    for i, car in enumerate(race_session_cars):
        if car.get("race_finished"):
            continue
        if car.get("in_pit"):
            car["pit_elapsed"] = float(car.get("pit_elapsed", 0.0)) + dt
            car["pit_timer"] = max(0.0, float(car.get("pit_timer", 0.0)) - dt)
            if car["pit_timer"] <= 0.0:
                car["in_pit"] = False
                car["pit_count"] = int(car.get("pit_count", 0)) + 1
                laps_left = max(0, sim_race_laps_this_round - int(car.get("lap", 0)))
                car["tyre"] = _pick_next_tyre_after_pit(car, race_setup_weather, laps_left)
                car["tyre_age"] = 0.0
            continue

        # Pit decision (player + AI)
        tyre_key = car.get("tyre", "MEDIUM")
        wear_laps = float(RACE_TYRE_COMPOUNDS.get(tyre_key, RACE_TYRE_COMPOUNDS["MEDIUM"])["wear_laps"])
        age = float(car.get("tyre_age", 0.0))
        laps_left = max(0, sim_race_laps_this_round - int(car.get("lap", 0)))
        mandatory_window_open = int(car.get("lap", 0)) >= max(2, sim_race_laps_this_round // 2 - 1)
        should_pit = False
        if car.get("is_player"):
            if race_player_pit_request:
                car["pit_request"] = True
                car["pit_request_reason"] = "manual"
                race_player_pit_request = False
            elif int(car.get("pit_count", 0)) < 1 and mandatory_window_open and laps_left > 2:
                # Privalomas bent vienas pit stop per lenktynes.
                car["pit_request"] = True
                car["pit_request_reason"] = "mandatory"
            elif age > wear_laps * 1.05 and laps_left > 1:
                car["pit_request"] = True
                car["pit_request_reason"] = "tyre"
        else:
            plan = car.get("pit_plan_lap")
            if plan is not None and int(car.get("lap", 0)) >= int(plan):
                car["pit_request"] = True
            elif int(car.get("pit_count", 0)) < 1 and mandatory_window_open and laps_left > 2:
                # Privalomas bent vienas pit stop per lenktynes.
                car["pit_request"] = True
            elif age > wear_laps * 1.08 and laps_left > 1:
                car["pit_request"] = True
        if car.get("pit_request"):
            dist_to_entry = (race_pit_entry_s - float(car.get("s", 0.0))) % max(1e-9, TRACK_TOTAL)
            trigger_window = max(16.0, _race_car_speed(car) * dt * 1.7)
            if dist_to_entry <= trigger_window:
                should_pit = True
        if should_pit:
            car["in_pit"] = True
            car["pit_request"] = False
            car["pit_request_reason"] = None
            base_pit = max(1.5, float(car.get("pit_avg_s", 2.8)))
            car["pit_total"] = max(1.5, base_pit + random.uniform(0.22, 0.85))
            car["pit_elapsed"] = 0.0
            car["pit_timer"] = car["pit_total"]
            continue

        old_s = float(car["s"])
        v = _race_car_speed(car)
        new_s = (old_s + v * dt) % TRACK_TOTAL
        car["s"] = new_s
        wear_mul = 1.0
        if car.get("is_player"):
            if race_player_push_mode == 0:
                wear_mul = 0.82
            elif race_player_push_mode == 2:
                wear_mul = 1.25
        car["tyre_age"] = float(car.get("tyre_age", 0.0)) + dt * (v / max(TRACK_TOTAL, 1.0)) * wear_mul
        # Pilnas ratas tik tada, kai kertama ta pati start/finish linija.
        old_rel = (old_s - start_s) % TRACK_TOTAL
        new_rel = (new_s - start_s) % TRACK_TOTAL
        if new_rel < old_rel:
            if car.get("start_cross_pending"):
                # Pirmas kirtimas tik pradeda 1-ą ratą, bet jo neužskaito kaip pilno.
                car["start_cross_pending"] = False
                car["last_cross_ms"] = now
                car["lap_variation"] = max(0.93, min(1.08, random.gauss(1.0, 0.022)))
                continue
            car["lap"] = int(car.get("lap", 0)) + 1
            lap_ms = now - int(car.get("last_cross_ms", now))
            car["last_cross_ms"] = now
            car["lap_variation"] = max(0.93, min(1.08, random.gauss(1.0, 0.022)))
            if int(car.get("lap", 0)) >= int(sim_race_laps_this_round):
                car["race_finished"] = True
                car["pit_request"] = False
                car["pit_request_reason"] = None
                if i not in race_finish_order:
                    race_finish_order.append(i)
            if lap_ms > 20000:
                best = car.get("best_lap_ms")
                if (best is None) or (lap_ms < best):
                    car["best_lap_ms"] = lap_ms
                if (race_fastest_lap["ms"] is None) or (lap_ms < race_fastest_lap["ms"]):
                    race_fastest_lap = {"car_idx": i, "ms": lap_ms}
                    race_fastest_popup_text = f"FASTEST LAP  {qual_display_name(car)}  {format_qual_time_msm(lap_ms / 1000.0)}"
                    race_fastest_popup_until_ms = now + 2400
    # Lenktynės baigiasi tik kai visi finišavę; tada taškai ir automatinis podiumas.
    if race_phase == "green" and race_session_cars and all(c.get("race_finished") for c in race_session_cars):
        race_phase = "finished"
        race_final_order = list(race_finish_order)
        missing = [k for k in range(len(race_session_cars)) if k not in race_final_order]
        if missing:
            missing.sort(key=lambda k: _race_progress_value(race_session_cars[k]), reverse=True)
            race_final_order.extend(missing)
        _award_race_points_and_prepare_podium()
        race_auto_podium_deadline_ms = now + 1800


def _draw_race_start_lights():
    if race_phase not in ("grid", "lights", "green"):
        return
    green_elapsed = pygame.time.get_ticks() - race_phase_start_ms if race_phase == "green" else 0
    if race_phase == "green" and green_elapsed > 900:
        return
    box = pygame.Rect(WIDTH // 2 - 110, 34, 220, 58)
    pygame.draw.rect(screen, (14, 16, 20), box, border_radius=8)
    pygame.draw.rect(screen, (60, 66, 76), box, 1, border_radius=8)
    on_count = 0
    all_green = False
    if race_phase == "lights":
        elapsed = pygame.time.get_ticks() - race_phase_start_ms
        on_count = min(5, max(0, int(elapsed / 900) + 1))
    elif race_phase == "green":
        all_green = True
    for i in range(5):
        cx = box.x + 28 + i * 40
        cy = box.centery
        if all_green:
            col = (72, 214, 102)
        else:
            col = (220, 24, 34) if i < on_count else (58, 18, 22)
        pygame.draw.circle(screen, col, (cx, cy), 12)
    if race_phase == "grid":
        draw_text_with_outline("GRID READY", pygame.font.SysFont("Arial", 14, bold=True), WHITE, BLACK, box.centerx, box.bottom + 16)
    # Po užsidegimo žaliai šviesoforas dingsta (kaip prašei).
    if race_safety_car_active:
        draw_text_with_outline("SAFETY CAR", pygame.font.SysFont("Arial", 18, bold=True), (252, 214, 70), BLACK, box.centerx, box.bottom + 36)


def _draw_pit_entry_exit_markers():
    if len(TRACK_POINTS) < 10:
        return
    i0, i1 = _find_pit_straight_indices()
    i0 = max(0, min(len(TRACK_POINTS) - 1, i0))
    i1 = max(0, min(len(TRACK_POINTS) - 1, i1))
    for idx, label, col in ((i0, "PIT IN", (255, 190, 70)), (i1, "PIT OUT", (120, 220, 130))):
        x, y = TRACK_POINTS[idx]
        pygame.draw.circle(screen, col, (int(x), int(y)), 4)
        draw_text_with_outline(label, pygame.font.SysFont("Arial", 11, bold=True), col, BLACK, int(x), int(y - 14))


def _draw_race_leaderboard():
    if not race_session_cars:
        return
    panel = pygame.Rect(10, 10, 112, 458)
    ps = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
    pygame.draw.rect(ps, (12, 14, 20, 150), ps.get_rect(), border_radius=10)
    pygame.draw.rect(ps, (70, 85, 108, 180), ps.get_rect(), 1, border_radius=10)
    screen.blit(ps, panel.topleft)
    draw_text_with_outline("LIVE", pygame.font.SysFont("Arial", 15, bold=True), CYAN, BLACK, panel.centerx, panel.y + 10)
    order = race_final_order if (race_phase == "finished" and race_final_order) else _race_live_order_indices()
    row_h = 18
    y0 = panel.y + 26
    shown = min(20, len(order))
    for pos in range(shown):
        i = order[pos]
        car = race_session_cars[i]
        ry = y0 + pos * row_h
        if ry + row_h > panel.bottom - 18:
            break
        pygame.draw.rect(screen, (22, 24, 30, 170), (panel.x + 4, ry, panel.w - 8, row_h - 1), border_radius=3)
        tc = car.get("color", (180, 180, 180))
        pygame.draw.rect(screen, tc, (panel.x + 6, ry + 2, 4, row_h - 5), border_radius=2)
        drv = car.get("driver")
        if drv == "__PLAYER__":
            nm = "YOU"
        else:
            nm = (str(drv).split(" ")[-1][:3]).upper()
        draw_text_with_outline(f"{pos+1:>2}", pygame.font.SysFont("Arial", 11, bold=True), WHITE, BLACK, panel.x + 8, ry + 2, align="left")
        nm_col = (190, 150, 255) if race_fastest_lap["car_idx"] == i else WHITE
        draw_text_with_outline(nm, pygame.font.SysFont("Arial", 11, bold=True), nm_col, BLACK, panel.x + 25, ry + 2, align="left")


def _draw_race_cars():
    if not race_session_cars:
        return
    order = _race_live_order_indices()
    # Pirma nupiešiam visus AI, žaidėją - paskutinį, kad jis būtų aiškiai matomas.
    draw_order = [i for i in reversed(order) if not race_session_cars[i].get("is_player")] + [i for i in reversed(order) if race_session_cars[i].get("is_player")]
    for i in draw_order:
        car = race_session_cars[i]
        if car.get("race_finished"):
            continue
        x, y, tx, ty = _track_xy_and_tangent_at_s(car["s"])
        nx, ny = -ty, tx
        lane = float(car.get("lane_side", 0.0))
        cx = x + nx * lane * 5.0
        cy = y + ny * lane * 5.0
        car_len, car_w = 24, 13
        p0 = (cx + tx * car_len * 0.5, cy + ty * car_len * 0.5)
        p1 = (cx - tx * car_len * 0.5 + nx * car_w * 0.5, cy - ty * car_len * 0.5 + ny * car_w * 0.5)
        p2 = (cx - tx * car_len * 0.5 - nx * car_w * 0.5, cy - ty * car_len * 0.5 - ny * car_w * 0.5)
        if car.get("is_player"):
            # Ryškus kontūras/halo aplink player bolidą, kad visada kristų į akis.
            pygame.draw.circle(screen, (255, 226, 102), (int(cx), int(cy)), 11, 2)
        pygame.draw.polygon(screen, car.get("color", (200, 200, 200)), [(int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))])
        edge_col = (255, 240, 170) if car.get("is_player") else (16, 16, 18)
        edge_w = 2 if car.get("is_player") else 1
        pygame.draw.polygon(screen, edge_col, [(int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))], edge_w)
        dname = car.get("driver")
        if dname == "__PLAYER__":
            num_txt = (driver_data.get("Number") or {}).get("text", "") or str(int(car.get("grid_pos", 0)))
        else:
            num_txt = str(DRIVER_NUMBERS_2025.get(dname, int(car.get("grid_pos", 0))))
        num_col = (255, 250, 220) if car.get("is_player") else WHITE
        draw_text_with_outline(num_txt, pygame.font.SysFont("Arial", 11, bold=True), num_col, BLACK, int(cx), int(cy))


def _draw_race_hud_counters():
    if not race_session_cars:
        return
    elapsed_ms = max(0, pygame.time.get_ticks() - race_elapsed_start_ms)
    mm = elapsed_ms // 60000
    ss = (elapsed_ms % 60000) // 1000
    active = [i for i, c in enumerate(race_session_cars) if not c.get("race_finished")]
    if active:
        lead_idx = max(active, key=lambda k: _race_progress_value(race_session_cars[k]))
        lead_lap = min(sim_race_laps_this_round, max(1, int(race_session_cars[lead_idx].get("lap", 0)) + 1))
    else:
        lead_lap = sim_race_laps_this_round
    txt = f"LAP {lead_lap}/{sim_race_laps_this_round}   TIME {mm:02d}:{ss:02d}"
    draw_text_with_outline(txt, pygame.font.SysFont("Arial", 18, bold=True), WHITE, BLACK, WIDTH // 2, 18)
    now = pygame.time.get_ticks()
    if race_fastest_popup_text and now < race_fastest_popup_until_ms:
        draw_text_with_outline(race_fastest_popup_text, pygame.font.SysFont("Arial", 18, bold=True), (190, 150, 255), BLACK, WIDTH // 2, 48)


def _draw_player_push_panel():
    global race_push_rects, race_pit_now_rect
    panel = pygame.Rect(WIDTH - 318, HEIGHT - 132, 304, 116)
    ps = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
    pygame.draw.rect(ps, (12, 14, 20, 180), ps.get_rect(), border_radius=10)
    pygame.draw.rect(ps, (70, 85, 108, 200), ps.get_rect(), 1, border_radius=10)
    screen.blit(ps, panel.topleft)
    draw_text_with_outline("PUSH MODE", pygame.font.SysFont("Arial", 14, bold=True), CYAN, BLACK, panel.x + 12, panel.y + 8, align="left")
    race_push_rects = {}
    labels = [
        (0, ">", (238, 208, 72), "Save tyres"),
        (1, ">>", (70, 156, 236), "Balanced"),
        (2, ">>>", (220, 56, 56), "Attack"),
    ]
    x = panel.x + 10
    for mode, arrows, col, desc in labels:
        rr = pygame.Rect(x, panel.y + 28, 88, 46)
        race_push_rects[mode] = rr
        pygame.draw.rect(screen, (26, 30, 40), rr, border_radius=6)
        br = col if race_player_push_mode == mode else (96, 102, 116)
        pygame.draw.rect(screen, br, rr, 2, border_radius=6)
        draw_text_with_outline(arrows, pygame.font.SysFont("Arial", 20, bold=True), col, BLACK, rr.centerx, rr.y + 8)
        draw_text_with_outline(desc, pygame.font.SysFont("Arial", 10, bold=True), LIGHT_GRAY, BLACK, rr.centerx, rr.y + 28)
        x += 96
    # PIT NOW kairėje — nepersidengia su trečiu PUSH (Attack), kuris baigiasi ties ~panel.x+290.
    race_pit_now_rect = pygame.Rect(panel.x + 8, panel.y + 78, 124, 26)
    pygame.draw.rect(screen, (36, 74, 120), race_pit_now_rect, border_radius=5)
    pygame.draw.rect(screen, (120, 170, 235), race_pit_now_rect, 1, border_radius=5)
    draw_text_with_outline("PIT NOW", pygame.font.SysFont("Arial", 12, bold=True), WHITE, BLACK, race_pit_now_rect.centerx, race_pit_now_rect.centery)
    # Recommendation for player pit stop
    ply = next((c for c in race_session_cars if c.get("is_player")), None)
    if ply and (not ply.get("in_pit")) and race_phase == "green":
        tyre = RACE_TYRE_COMPOUNDS.get(ply.get("tyre", "MEDIUM"), RACE_TYRE_COMPOUNDS["MEDIUM"])
        age = float(ply.get("tyre_age", 0.0))
        wear = float(tyre["wear_laps"])
        life = max(0.0, 1.0 - age / max(1e-9, wear))
        draw_text_with_outline(
            f"Tyre life: {int(life*100):02d}%",
            pygame.font.SysFont("Arial", 12, bold=True),
            WHITE,
            BLACK,
            panel.x + 10,
            panel.bottom - 44,
            align="left",
        )
        if age > wear * 0.86:
            draw_text_with_outline("RECOMMENDED: PIT THIS LAP", pygame.font.SysFont("Arial", 12, bold=True), ORANGE, BLACK, panel.x + 10, panel.bottom - 28, align="left")
        elif ply.get("pit_request"):
            reason = ply.get("pit_request_reason")
            if reason == "manual":
                pit_msg = "PIT: YOUR REQUEST"
            elif reason == "mandatory":
                pit_msg = "PIT: REQUIRED (RULE)"
            else:
                pit_msg = "PIT: TYRE WEAR"
            draw_text_with_outline(pit_msg, pygame.font.SysFont("Arial", 12, bold=True), CYAN, BLACK, panel.x + 10, panel.bottom - 28, align="left")
    elif ply:
        tyre = RACE_TYRE_COMPOUNDS.get(ply.get("tyre", "MEDIUM"), RACE_TYRE_COMPOUNDS["MEDIUM"])
        age = float(ply.get("tyre_age", 0.0))
        wear = float(tyre["wear_laps"])
        life = max(0.0, 1.0 - age / max(1e-9, wear))
        draw_text_with_outline(
            f"Tyre life: {int(life*100):02d}%",
            pygame.font.SysFont("Arial", 12, bold=True),
            WHITE,
            BLACK,
            panel.x + 10,
            panel.bottom - 44,
            align="left",
        )
    if ply and ply.get("in_pit"):
        pit_elapsed = float(ply.get("pit_elapsed", 0.0))
        pit_total = max(0.01, float(ply.get("pit_total", 0.0)))
        pit_avg = max(0.01, float(ply.get("pit_avg_s", pit_total)))
        draw_text_with_outline(
            f"PIT {pit_elapsed:.1f}s / {pit_total:.1f}s",
            pygame.font.SysFont("Arial", 12, bold=True),
            CYAN,
            BLACK,
            panel.x + 10,
            panel.bottom - 28,
            align="left",
        )
        draw_text_with_outline(
            f"Avg pit: {pit_avg:.2f}s",
            pygame.font.SysFont("Arial", 10, bold=True),
            LIGHT_GRAY,
            BLACK,
            panel.x + 10,
            panel.bottom - 12,
            align="left",
        )


def _award_race_points_and_prepare_podium():
    """F1 taškai TOP10 + greičiausio rato taškas (tik jei FL vairuotojas TOP10)."""
    global race_points_awarded, race_podium_rows, race_post_results_rows, race_post_team_rows
    if race_points_awarded or not race_final_order:
        return
    points_scale = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
    race_podium_rows = []
    race_post_results_rows = []
    race_post_team_rows = []
    fl_idx = race_fastest_lap.get("car_idx")

    for pos, idx in enumerate(race_final_order):
        car = race_session_cars[idx]
        pts = points_scale[pos] if pos < 10 else 0
        fl_bonus = 0
        if fl_idx is not None and pos < 10 and idx == fl_idx:
            fl_bonus = 1
        total = pts + fl_bonus
        k = championship_points_key(car)
        championship_points[k] = championship_points.get(k, 0) + total
        race_post_results_rows.append({"idx": idx, "pos": pos + 1, "pts": pts, "fl": fl_bonus, "total": total})
        if pos < 3:
            race_podium_rows.append(dict(car))

    team_pts = {}
    for row in race_post_results_rows:
        car = race_session_cars[row["idx"]]
        tn = car.get("team", "")
        team_pts[tn] = team_pts.get(tn, 0) + row["total"]
    race_post_team_rows = sorted(team_pts.items(), key=lambda x: (-x[1], x[0]))
    race_points_awarded = True


def _team_championship_totals_from_session():
    """Komandų sezono taškai pagal dabartinę čempionato lentelę (abu komandos bolidai)."""
    m = {}
    for c in race_session_cars:
        tn = c.get("team", "")
        m[tn] = m.get(tn, 0) + get_championship_points_for_car(c)
    return sorted(m.items(), key=lambda x: (-x[1], x[0]))


def _driver_photo_for_car(car, size):
    drv = car.get("driver")
    if drv == "__PLAYER__":
        return pygame.transform.scale(avatar_img, size)
    surname = str(drv or "").split(" ")[-1].strip()
    p = f"images/{surname}.jpg" if surname else "images/avataras.jpg"
    return load_and_convert_img(p, size)


def draw_race_podium_screen():
    screen.fill((10, 12, 18))
    # LED stiliaus fonas.
    t = pygame.time.get_ticks() * 0.004
    for y in range(0, HEIGHT, 18):
        hue = 0.5 + 0.5 * math.sin(t + y * 0.02)
        col = (int(18 + 40 * hue), int(24 + 70 * hue), int(46 + 120 * hue))
        pygame.draw.line(screen, col, (0, y), (WIDTH, y), 1)
    for k in range(42):
        x = int((k * 61 + pygame.time.get_ticks() * 0.08) % (WIDTH + 120)) - 60
        y = 86 + (k * 23) % (HEIGHT - 120)
        pygame.draw.circle(screen, (40, 120, 255), (x, y), 2)
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 120))
    screen.blit(ov, (0, 0))
    draw_text_with_outline("RACE PODIUM", pygame.font.SysFont("Arial", 48, bold=True), ORANGE, BLACK, WIDTH // 2, 66)
    if not race_podium_rows:
        draw_text_with_outline("No podium data", pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, WIDTH // 2, HEIGHT // 2)
        return
    bases = [(WIDTH // 2 - 220, HEIGHT - 120, 140), (WIDTH // 2, HEIGHT - 150, 185), (WIDTH // 2 + 220, HEIGHT - 100, 110)]
    order_idx = [1, 0, 2]  # show P2, P1, P3 left-center-right
    for slot, pidx in enumerate(order_idx):
        if pidx >= len(race_podium_rows):
            continue
        car = race_podium_rows[pidx]
        x, y, h = bases[slot]
        w = 140
        rect = pygame.Rect(x - w // 2, y - h, w, h)
        pygame.draw.rect(screen, (34, 38, 52), rect, border_radius=8)
        pygame.draw.rect(screen, (96, 106, 134), rect, 2, border_radius=8)
        ph = _driver_photo_for_car(car, (92, 92))
        screen.blit(ph, ph.get_rect(center=(x, rect.y - 56)))
        # Numeris tiksliai dėžės viduryje.
        draw_text_with_outline(str(pidx + 1), pygame.font.SysFont("Arial", 44, bold=True), GOLD, BLACK, x, rect.centery)
        draw_text_with_outline(qual_display_name(car), pygame.font.SysFont("Arial", 16, bold=True), WHITE, BLACK, x, rect.bottom + 10)
    draw_text_with_outline("Click for full results", pygame.font.SysFont("Arial", 20, bold=True), CYAN, BLACK, WIDTH // 2, HEIGHT - 34)


def draw_race_results_screen():
    """Po podiumo: pilna vairuotojų lentelė su taškais (F1) arba komandų įskaita."""
    global race_results_drivers_tab_rect, race_results_teams_tab_rect, race_results_continue_rect
    screen.fill((10, 12, 18))
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 100))
    screen.blit(ov, (0, 0))
    draw_text_with_outline("RACE RESULTS", pygame.font.SysFont("Arial", 40, bold=True), ORANGE, BLACK, WIDTH // 2, 42)
    race_results_drivers_tab_rect = pygame.Rect(WIDTH // 2 - 260, 86, 250, 36)
    race_results_teams_tab_rect = pygame.Rect(WIDTH // 2 + 10, 86, 250, 36)
    for rect, label, tab in (
        (race_results_drivers_tab_rect, "DRIVER STANDINGS", "drivers"),
        (race_results_teams_tab_rect, "TEAM STANDINGS", "teams"),
    ):
        on = race_results_tab == tab
        pygame.draw.rect(screen, (32, 40, 58) if on else (22, 24, 30), rect, border_radius=8)
        pygame.draw.rect(screen, (120, 170, 230) if on else (70, 80, 96), rect, 2, border_radius=8)
        draw_text_with_outline(label, pygame.font.SysFont("Arial", 15, bold=True), WHITE if on else LIGHT_GRAY, BLACK, rect.centerx, rect.centery)
    panel = pygame.Rect(40, 132, WIDTH - 80, HEIGHT - 200)
    pygame.draw.rect(screen, (14, 16, 22), panel, border_radius=12)
    pygame.draw.rect(screen, (70, 90, 120), panel, 2, border_radius=12)
    hdr = pygame.font.SysFont("Arial", 13, bold=True)
    cell = pygame.font.SysFont("Arial", 14, bold=True)
    row_h = 22
    y0 = panel.y + 14

    if race_results_tab == "drivers":
        screen.blit(hdr.render("POS", True, (150, 160, 175)), (panel.x + 16, y0))
        screen.blit(hdr.render("DRIVER", True, (150, 160, 175)), (panel.x + 58, y0))
        screen.blit(hdr.render("TEAM", True, (150, 160, 175)), (panel.x + 280, y0))
        screen.blit(hdr.render("PTS", True, (150, 160, 175)), (panel.right - 120, y0))
        screen.blit(hdr.render("NOTES", True, (150, 160, 175)), (panel.right - 280, y0))
        y = y0 + 26
        for row in race_post_results_rows:
            if y > panel.bottom - 28:
                break
            car = race_session_cars[row["idx"]]
            notes = "Fastest lap +1" if row["fl"] else ""
            if row["fl"] and row["pts"]:
                pts_cell = f"{row['pts']}+{row['fl']} = {row['total']}"
            elif row["fl"]:
                pts_cell = f"+{row['fl']} = {row['total']}"
            else:
                pts_cell = str(row["total"])
            nm = qual_display_name(car)[:28]
            ab = TEAM_ABBREV.get(car.get("team", ""), "-")[:4]
            pygame.draw.rect(screen, (24, 26, 34), (panel.x + 8, y - 2, panel.w - 16, row_h), border_radius=4)
            screen.blit(cell.render(str(row["pos"]), True, GOLD if row["pos"] == 1 else WHITE), (panel.x + 18, y))
            screen.blit(cell.render(nm, True, GOLD if car.get("is_player") else WHITE), (panel.x + 58, y))
            screen.blit(cell.render(ab, True, (160, 175, 195)), (panel.x + 280, y))
            screen.blit(cell.render(pts_cell, True, CYAN), (panel.right - 200, y))
            screen.blit(cell.render(notes, True, (190, 150, 255)), (panel.right - 420, y))
            y += row_h
    else:
        season_rows = _team_championship_totals_from_session()
        season_map = {t: p for t, p in season_rows}
        screen.blit(hdr.render("POS", True, (150, 160, 175)), (panel.x + 16, y0))
        screen.blit(hdr.render("TEAM", True, (150, 160, 175)), (panel.x + 58, y0))
        screen.blit(hdr.render("THIS RACE", True, (150, 160, 175)), (panel.x + 340, y0))
        screen.blit(hdr.render("SEASON PTS", True, (150, 160, 175)), (panel.right - 130, y0))
        y = y0 + 26
        for pos, (tname, tr_pts) in enumerate(race_post_team_rows, start=1):
            if y > panel.bottom - 28:
                break
            se = season_map.get(tname, 0)
            pygame.draw.rect(screen, (24, 26, 34), (panel.x + 8, y - 2, panel.w - 16, row_h), border_radius=4)
            screen.blit(cell.render(str(pos), True, WHITE), (panel.x + 18, y))
            screen.blit(cell.render(tname[:32], True, WHITE), (panel.x + 58, y))
            screen.blit(cell.render(str(tr_pts), True, CYAN), (panel.x + 340, y))
            screen.blit(cell.render(str(se), True, GOLD), (panel.right - 130, y))
            y += row_h
    race_results_continue_rect = pygame.Rect(WIDTH // 2 - 180, HEIGHT - 72, 360, 44)
    pygame.draw.rect(screen, (28, 38, 54), race_results_continue_rect, border_radius=10)
    pygame.draw.rect(screen, (120, 160, 220), race_results_continue_rect, 2, border_radius=10)
    draw_text_with_outline("CONTINUE", pygame.font.SysFont("Arial", 22, bold=True), WHITE, BLACK, race_results_continue_rect.centerx, race_results_continue_rect.centery)
    draw_text_with_outline("ESC — profile", font_exit, (200, 200, 210), BLACK, 18, 18, align="left")


def _apply_post_race_chest_rewards():
    """Po varžybų duoda chest su progresuojančiais prizais: pinigai + upgrade tokenai."""
    global post_race_chest, money_balance
    if post_race_chest is not None:
        return
    player_pos = 20
    if race_post_results_rows:
        for row in race_post_results_rows:
            c = race_session_cars[row["idx"]]
            if c.get("is_player"):
                player_pos = int(row["pos"])
                break
    reward = DEFAULT_CHEST_REWARD_SERVICE.build_reward(
        player_position=player_pos,
        upgrade_pool=UPGRADE_POOL,
        upgrade_inventory=upgrade_inventory,
        rng=random,
    )
    money_balance += reward.cash
    post_race_chest = {"tier": reward.tier, "cash": reward.cash, "upgrades": reward.upgrades}


def draw_post_race_chest_screen():
    global chest_continue_rect
    _apply_post_race_chest_rewards()
    screen.fill((10, 12, 18))
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 120))
    screen.blit(ov, (0, 0))
    tier = post_race_chest["tier"] if post_race_chest else "CHEST"
    draw_text_with_outline(f"{tier} CHEST", pygame.font.SysFont("Arial", 44, bold=True), GOLD, BLACK, WIDTH // 2, 66)
    panel = pygame.Rect(WIDTH // 2 - 360, 120, 720, 430)
    pygame.draw.rect(screen, (14, 16, 24), panel, border_radius=12)
    pygame.draw.rect(screen, (90, 120, 170), panel, 2, border_radius=12)
    draw_text_with_outline(f"Money: +${post_race_chest['cash']}", pygame.font.SysFont("Arial", 28, bold=True), CYAN, BLACK, panel.centerx, panel.y + 60)
    draw_text_with_outline("Upgrade rewards:", pygame.font.SysFont("Arial", 24, bold=True), WHITE, BLACK, panel.centerx, panel.y + 110)
    y = panel.y + 154
    for upg in post_race_chest["upgrades"]:
        draw_text_with_outline(f"+1 {upg}", pygame.font.SysFont("Arial", 21, bold=True), LIGHT_GRAY, BLACK, panel.centerx, y)
        y += 42
    chest_continue_rect = pygame.Rect(WIDTH // 2 - 180, panel.bottom - 62, 360, 44)
    pygame.draw.rect(screen, (28, 38, 54), chest_continue_rect, border_radius=10)
    pygame.draw.rect(screen, (120, 160, 220), chest_continue_rect, 2, border_radius=10)
    draw_text_with_outline("CONTINUE", pygame.font.SysFont("Arial", 22, bold=True), WHITE, BLACK, chest_continue_rect.centerx, chest_continue_rect.centery)


def draw_race_setup_screen():
    global race_setup_btn_rect, race_setup_tyre_rects
    draw_track_base()
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 190))
    screen.blit(ov, (0, 0))
    panel = pygame.Rect(120, 74, WIDTH - 240, HEIGHT - 148)
    pygame.draw.rect(screen, (14, 16, 24), panel, border_radius=12)
    pygame.draw.rect(screen, (74, 96, 130), panel, 2, border_radius=12)
    draw_text_with_outline("RACE SETUP", pygame.font.SysFont("Arial", 34, bold=True), ORANGE, BLACK, panel.centerx, panel.y + 30)
    draw_text_with_outline(f"Weather: {race_setup_weather}", pygame.font.SysFont("Arial", 20, bold=True), CYAN, BLACK, panel.x + 24, panel.y + 70, align="left")
    race_setup_tyre_rects = {}
    y = panel.y + 108
    for key in ("SOFT", "MEDIUM", "HARD", "INTER", "WET"):
        td = RACE_TYRE_COMPOUNDS[key]
        rr = pygame.Rect(panel.x + 24, y, panel.w - 48, 60)
        race_setup_tyre_rects[key] = rr
        pygame.draw.rect(screen, (26, 30, 40), rr, border_radius=8)
        br = td["color"] if key == race_setup_selected_tyre else (84, 90, 104)
        pygame.draw.rect(screen, br, rr, 2, border_radius=8)
        chip = pygame.Rect(rr.x + 8, rr.y + 10, 18, 40)
        pygame.draw.rect(screen, td["color"], chip, border_radius=3)
        draw_text_with_outline(key, pygame.font.SysFont("Arial", 18, bold=True), WHITE, BLACK, rr.x + 36, rr.y + 8, align="left")
        draw_text_with_outline(td["comment"], pygame.font.SysFont("Arial", 14, bold=True), LIGHT_GRAY, BLACK, rr.x + 132, rr.y + 10, align="left")
        exp_stops = max(1, int(sim_race_laps_this_round / max(1, td["wear_laps"])))
        draw_text_with_outline(
            f"Pace x{td['pace']:.3f} | Wear ~{td['wear_laps']} laps | Est. stops: {exp_stops}",
            pygame.font.SysFont("Arial", 13, bold=True),
            (180, 186, 200),
            BLACK,
            rr.x + 132,
            rr.y + 32,
            align="left",
        )
        y += 66
    race_setup_btn_rect = pygame.Rect(panel.centerx - 170, panel.bottom - 64, 340, 46)
    pygame.draw.rect(screen, (30, 42, 60), race_setup_btn_rect, border_radius=10)
    draw_thin_led_border_rect(race_setup_btn_rect)
    draw_text_with_outline("START RACE", pygame.font.SysFont("Arial", 24, bold=True), WHITE, BLACK, race_setup_btn_rect.centerx, race_setup_btn_rect.centery)


def draw_race_screen():
    """Lenktynių ekranas: grid + šviesoforai + live leaderboard + fastest lap."""
    draw_track_base()
    _draw_pit_entry_exit_markers()
    _draw_race_cars()
    _draw_race_start_lights()
    _draw_race_hud_counters()
    _draw_race_leaderboard()
    if race_phase == "green":
        ply = next((c for c in race_session_cars if c.get("is_player")), None)
        if ply and (not ply.get("race_finished")):
            _draw_player_push_panel()
    if race_phase == "finished":
        draw_text_with_outline("RACE COMPLETE", pygame.font.SysFont("Arial", 36, bold=True), ORANGE, BLACK, WIDTH // 2, 58)
        draw_text_with_outline("Podium loading…", pygame.font.SysFont("Arial", 18, bold=True), LIGHT_GRAY, BLACK, WIDTH // 2, 98)


rebuild_season_track_geometry()

def get_team_arc_bounds():
    bounds = []
    current_acc = 0.0
    for team in F1_TEAMS:
        team_arc = (team["weight"] / TOTAL_WEIGHT) * 360.0
        bounds.append((team, current_acc, current_acc + team_arc))
        current_acc += team_arc
    return bounds

def start_weighted_spin():
    global is_spinning, winning_team_name
    global spin_start_time, spin_duration_ms
    global reel_items, reel_start_offset, reel_target_offset
    global last_tick_slot

    selected_team = random.choices(
        F1_TEAMS, weights=[team["weight"] for team in F1_TEAMS], k=1
    )[0]
    reel_items = [random.choices(F1_TEAMS, weights=[t["weight"] for t in F1_TEAMS], k=1)[0] for _ in range(70)]
    final_idx = random.randint(52, 60)
    reel_items[final_idx] = selected_team

    card_w, gap = 135, 14
    center_x = reel_window.centerx
    reel_start_offset = 0.0
    desired_item_center_x = reel_window.x + final_idx * (card_w + gap) + card_w / 2
    reel_target_offset = desired_item_center_x - center_x

    spin_duration_ms = random.randint(4200, 5600)
    spin_start_time = pygame.time.get_ticks()
    winning_team_name = selected_team["name"]
    is_spinning = True
    last_tick_slot = -1

def generate_sponsor_screen():
    global sponsor_reel_rows, sponsor_offers, teammate_result, upgrade_result, teammate_reel, upgrade_reel
    global sponsor_reel_offsets, sponsor_reel_targets, sponsor_reel_spinning, sponsor_reel_start_time, sponsor_reel_duration, sponsor_last_tick_slot, selected_offer_idx, sponsor_result_revealed
    global signing_bonus_given, selected_offer_name
    drivers = TEAM_DRIVERS_2025.get(winning_team_name, ["Driver A", "Driver B"])
    teammate_result = random.choice(drivers)  # 50/50
    upgrade_result = random.choice(UPGRADE_POOL)

    teammate_reel = [random.choice(drivers) for _ in range(18)]
    teammate_reel[9] = teammate_result
    upgrade_reel = [random.choice(UPGRADE_POOL) for _ in range(18)]
    upgrade_reel[9] = upgrade_result
    sponsor_reel_rows = [teammate_reel, upgrade_reel]
    sponsor_reel_offsets = [0.0, 0.0]
    sponsor_reel_targets = [0.0, 0.0]
    sponsor_reel_spinning = [False, False]
    sponsor_reel_start_time = [0, 0]
    sponsor_reel_duration = [0, 0]
    sponsor_last_tick_slot = [-1, -1]
    selected_offer_idx = -1
    sponsor_result_revealed = [False, False]
    signing_bonus_given = False
    selected_offer_name = ""

    sponsor_offers = [[
        "Revolut Offer: $10 signing bonus",
        "$7 per race win",
        "$5 every two races + bonuses"
    ], [
        "Nike Offer: $12 signing bonus",
        "$5 per race win",
        "$6 every two races + bonuses"
    ], [
        "Rolex Offer: $11 signing bonus",
        "$8 per race win",
        "$4 every two races + bonuses"
    ]]
    sync_roster_after_teammate_pick()

def get_offer_signing_bonus(idx):
    return [10, 12, 11][idx]

def get_offer_name(idx):
    return ["Revolut", "Nike", "Rolex"][idx]


def get_player_car_showroom_stats():
    """Statistikos iš PART_UPGRADE_CURVES: bazė 7; pit = 7×1s dalys, kiekviena dalis su upgrade trumpina savo sekundę."""
    base = 7
    sb = cb = pb = qb = ob = 0.0
    pit_total = 0.0
    for part in CAR_PARTS:
        tier = int(car_part_tiers.get(part, 0))
        f = _tier_progress_to_beast(tier)
        c = PART_UPGRADE_CURVES.get(part, {})
        sb += c.get("speed", 0) * f
        cb += c.get("cornering", 0) * f
        pb += c.get("power_unit", 0) * f
        qb += c.get("qualifying", 0) * f
        ob += c.get("overtake", 0) * f
        saved = c.get("pit_saved_at_max", 0) * f
        pit_total += 1.0 - saved
    ssum = sum(int(car_part_tiers.get(p, 0)) for p in CAR_PARTS)
    if ssum == 0:
        return {
            "speed": base,
            "power_unit": base,
            "cornering": base,
            "qualifying": base,
            "pit_s": 7.0,
            "overtake_mode": 0,
        }
    return {
        "speed": int(round(base + sb)),
        "power_unit": int(round(base + pb)),
        "cornering": int(round(base + cb)),
        "qualifying": int(round(base + qb)),
        "pit_s": max(1.85, pit_total),
        "overtake_mode": int(round(ob)),
    }


def draw_profile_screen():
    global teammate_card_close_rect, profile_car_box_rect, car_stats_card_rect, car_stats_close_rect
    teammate_card_close_rect = pygame.Rect(0, 0, 0, 0)
    car_stats_close_rect = pygame.Rect(0, 0, 0, 0)
    left_rect = pygame.Rect(profile_margin, profile_margin + 34, WIDTH // 2 - profile_margin - 6, HEIGHT - 2 * profile_margin - 34)
    right_main = pygame.Rect(WIDTH // 2 + 6, profile_margin + 34, WIDTH // 2 - profile_margin - 6, HEIGHT - 2 * profile_margin - 34 - 128)

    for rect in [left_rect, right_main]:
        pygame.draw.rect(screen, (14, 14, 20), rect, border_radius=10)
        pygame.draw.rect(screen, (80, 160, 255), rect, 2, border_radius=10)

    # Left side: avatar + teammate + profile + upgrades + offer
    avatar_box = pygame.Rect(left_rect.x + 18, left_rect.y + 20, 190, 190)
    teammate_box = pygame.Rect(left_rect.x + left_rect.width - 208, left_rect.y + 20, 190, 190)
    teammate_box_click_rect.x, teammate_box_click_rect.y = teammate_box.x, teammate_box.y
    teammate_box_click_rect.width, teammate_box_click_rect.height = teammate_box.width, teammate_box.height
    pygame.draw.rect(screen, (40, 40, 50), avatar_box, border_radius=8)
    pygame.draw.rect(screen, WHITE, avatar_box, 2, border_radius=8)
    screen.blit(pygame.transform.scale(avatar_img, (190, 190)), avatar_box.topleft)
    pygame.draw.rect(screen, (40, 40, 50), teammate_box, border_radius=8)
    pygame.draw.rect(screen, WHITE, teammate_box, 2, border_radius=8)
    if teammate_img:
        screen.blit(teammate_img, teammate_box.topleft)

    draw_text_with_outline(driver_data["Name"]["text"] or "-", pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, avatar_box.centerx, avatar_box.bottom + 22)
    draw_text_with_outline(driver_data["Surname"]["text"] or "-", pygame.font.SysFont("Arial", 18, bold=True), LIGHT_GRAY, BLACK, avatar_box.centerx, avatar_box.bottom + 46)
    draw_text_with_outline(driver_data["Country"]["text"] or "-", pygame.font.SysFont("Arial", 16, bold=True), LIGHT_GRAY, BLACK, avatar_box.centerx, avatar_box.bottom + 68)

    teammate_country = DRIVER_COUNTRY.get(teammate_result, "-")
    teammate_name = teammate_result.split(" ")[0] if teammate_result else "-"
    teammate_surname = teammate_result.split(" ")[-1] if teammate_result else "-"
    draw_text_with_outline(teammate_name, pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, teammate_box.centerx, teammate_box.bottom + 22)
    draw_text_with_outline(teammate_surname, pygame.font.SysFont("Arial", 18, bold=True), LIGHT_GRAY, BLACK, teammate_box.centerx, teammate_box.bottom + 46)
    draw_text_with_outline(teammate_country, pygame.font.SysFont("Arial", 16, bold=True), LIGHT_GRAY, BLACK, teammate_box.centerx, teammate_box.bottom + 68)

    table_y = avatar_box.bottom + 96
    draw_text_with_outline("Driver Upgrades", pygame.font.SysFont("Arial", 24, bold=True), ORANGE, BLACK, left_rect.x + 20, table_y, align="left")
    upgrade_apply_buttons.clear()
    for i, upg in enumerate(UPGRADE_POOL):
        row_y = table_y + 26 + i * 44
        row_rect = pygame.Rect(left_rect.x + 18, row_y, left_rect.width - 36, 36)
        pygame.draw.rect(screen, (24, 24, 30), row_rect, border_radius=6)
        pygame.draw.rect(screen, (95, 95, 120), row_rect, 1, border_radius=6)
        draw_text_with_outline(upg.replace(" Upgrade", ""), pygame.font.SysFont("Arial", 17, bold=True), WHITE, BLACK, row_rect.x + 8, row_rect.y + 8, align="left")
        draw_text_with_outline(f"Lvl {upgrade_levels[upg]}/20 | Tokens {upgrade_inventory[upg]}", pygame.font.SysFont("Arial", 16, bold=True), LIGHT_GRAY, BLACK, row_rect.x + 260, row_rect.y + 8, align="left")
        btn = pygame.Rect(row_rect.right - 96, row_rect.y + 4, 88, 28)
        upgrade_apply_buttons[upg] = btn
        pygame.draw.rect(screen, (70, 150, 255), btn, border_radius=6)
        pygame.draw.rect(screen, WHITE, btn, 1, border_radius=6)
        draw_text_with_outline("APPLY", pygame.font.SysFont("Arial", 14, bold=True), WHITE, BLACK, btn.centerx, btn.centery)

    if selected_offer_idx != -1:
        offer = sponsor_offers[selected_offer_idx]
        draw_text_with_outline("Selected Offer Terms:", pygame.font.SysFont("Arial", 18, bold=True), GOLD, BLACK, left_rect.x + 20, left_rect.bottom - 104, align="left")
        for i, line in enumerate(offer):
            draw_text_with_outline(line, pygame.font.SysFont("Arial", 14, bold=True), WHITE, BLACK, left_rect.x + 20, left_rect.bottom - 80 + i * 16, align="left")
    else:
        draw_text_with_outline("Selected Offer: -", pygame.font.SysFont("Arial", 18, bold=True), GOLD, BLACK, left_rect.x + 20, left_rect.bottom - 28, align="left")

    # Right side: larger car + better upgrade layout
    car_box = pygame.Rect(right_main.x + 16, right_main.y + 16, right_main.width - 32, 210)
    pygame.draw.rect(screen, (30, 30, 38), car_box, border_radius=8)
    pygame.draw.rect(screen, WHITE, car_box, 2, border_radius=8)
    screen.blit(car_img, car_img.get_rect(center=car_box.center))
    profile_car_box_rect = pygame.Rect(car_box)
    draw_text_with_outline("Car Development", pygame.font.SysFont("Arial", 23, bold=True), ORANGE, BLACK, right_main.x + 20, car_box.bottom + 16, align="left")
    car_upgrade_buttons.clear()
    btn_w = (right_main.width - 40 - 14) // 2
    top_y = car_box.bottom + 42
    row_gap = 40
    positions = [
        (right_main.x + 16, top_y), (right_main.x + 16 + btn_w + 14, top_y),
        (right_main.x + 16, top_y + row_gap), (right_main.x + 16 + btn_w + 14, top_y + row_gap),
        (right_main.x + 16, top_y + row_gap * 2), (right_main.x + 16 + btn_w + 14, top_y + row_gap * 2),
        (right_main.x + 16 + (btn_w + 14) // 2, top_y + row_gap * 3),
    ]
    for i, part in enumerate(CAR_PARTS):
        bx, by = positions[i]
        tier = car_part_tiers[part]
        rarity_name, rarity_color, next_cost = RARITY_STEPS[tier]
        txt_cost = "MAX" if next_cost is None else f"Next: ${next_cost}"
        btn = pygame.Rect(bx, by, btn_w, 34)
        car_upgrade_buttons[part] = btn
        pygame.draw.rect(screen, rarity_color, btn, border_radius=6)
        pygame.draw.rect(screen, WHITE, btn, 1, border_radius=6)
        draw_text_with_outline(f"{part} | {rarity_name} | {txt_cost}", pygame.font.SysFont("Arial", 13, bold=True), WHITE, BLACK, btn.x + 6, btn.y + 9, align="left")

    # Start season / season (tas pats mygtukas kaip lenktynės)
    pygame.draw.rect(screen, ORANGE, start_race_rect, 3, border_radius=10)
    season_btn_txt = "SEASON" if season_started_once else "START SEASON"
    season_btn_font = pygame.font.SysFont("Arial", 30 if season_started_once else 28, bold=True)
    draw_text_with_outline(season_btn_txt, season_btn_font, WHITE, BLACK, start_race_rect.centerx, start_race_rect.centery)
    if pending_car_part and pending_car_part in car_upgrade_buttons:
        active_btn = car_upgrade_buttons[pending_car_part]
        buy_button_rect.x = active_btn.right - 64
        buy_button_rect.y = active_btn.y + 2
        buy_button_rect.width = 60
        buy_button_rect.height = active_btn.height - 4
        pygame.draw.rect(screen, (50, 190, 80), buy_button_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, buy_button_rect, 1, border_radius=6)
        draw_text_with_outline("BUY", pygame.font.SysFont("Arial", 15, bold=True), WHITE, BLACK, buy_button_rect.centerx, buy_button_rect.centery)

    if show_teammate_card:
        card_w, card_h = 560, 660
        card_rect = pygame.Rect(WIDTH // 2 - card_w // 2, HEIGHT // 2 - card_h // 2, card_w, card_h)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (18, 18, 24), card_rect, border_radius=12)
        pygame.draw.rect(screen, (90, 160, 255), card_rect, 2, border_radius=12)
        header_cy = card_rect.y + 24
        teammate_card_close_rect = pygame.Rect(card_rect.right - 40, card_rect.y + 8, 30, 30)
        pygame.draw.rect(screen, BLOOD_RED, teammate_card_close_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, teammate_card_close_rect, 2, border_radius=6)
        draw_text_with_outline("X", pygame.font.SysFont("Arial", 22, bold=True), WHITE, BLACK, teammate_card_close_rect.centerx, teammate_card_close_rect.centery)
        draw_text_with_outline("TEAMMATE CARD", pygame.font.SysFont("Arial", 24, bold=True), ORANGE, BLACK, card_rect.centerx, header_cy)
        photo_size = 240
        photo_x = card_rect.x + (card_rect.width - photo_size) // 2
        photo_y = card_rect.y + 50
        photo_rect = pygame.Rect(photo_x, photo_y, photo_size, photo_size)
        pygame.draw.rect(screen, (40, 40, 50), photo_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, photo_rect, 2, border_radius=10)
        if teammate_img:
            screen.blit(pygame.transform.scale(teammate_img, (photo_size, photo_size)), photo_rect.topleft)
        draw_text_with_outline(teammate_result or "-", pygame.font.SysFont("Arial", 22, bold=True), WHITE, BLACK, card_rect.centerx, photo_rect.bottom + 22)
        draw_text_with_outline(DRIVER_COUNTRY.get(teammate_result, "-"), pygame.font.SysFont("Arial", 17, bold=True), LIGHT_GRAY, BLACK, card_rect.centerx, photo_rect.bottom + 48)
        stats = DRIVER_STATS.get(teammate_result, {"Overtaking": 10, "Defending": 10, "Qualifying": 10, "Race Start": 10, "Tyre Management": 10})
        stat_font = pygame.font.SysFont("Arial", 18, bold=True)
        small_font = pygame.font.SysFont("Arial", 17, bold=True)
        row_h = 44
        pad_x = 28
        base_y = photo_rect.bottom + 78
        for i, (key, value) in enumerate(stats.items()):
            y = base_y + i * row_h
            lvl = max(1, min(20, int(value)))
            row_rect = pygame.Rect(card_rect.x + pad_x, y, card_rect.width - 2 * pad_x, row_h - 4)
            pygame.draw.rect(screen, (28, 28, 36), row_rect, border_radius=8)
            pygame.draw.rect(screen, (70, 90, 120), row_rect, 1, border_radius=8)
            draw_text_with_outline(key, stat_font, WHITE, BLACK, row_rect.x + 14, row_rect.y + 8, align="left")
            draw_text_with_outline(f"{lvl}/20", small_font, GOLD, BLACK, row_rect.right - 14, row_rect.y + 8, align="right")
            bar_y = row_rect.y + 28
            bar_inner_w = row_rect.width - 24
            pygame.draw.rect(screen, (50, 50, 58), (row_rect.x + 12, bar_y, bar_inner_w, 14), border_radius=5)
            fill_w = max(0, int(bar_inner_w * lvl / 20))
            pygame.draw.rect(screen, (70, 170, 255), (row_rect.x + 12, bar_y, fill_w, 14), border_radius=5)

    if show_car_stats_card:
        ctw, cth = 520, 440
        car_stats_card_rect = pygame.Rect(WIDTH // 2 - ctw // 2, HEIGHT // 2 - cth // 2, ctw, cth)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (18, 18, 24), car_stats_card_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 140, 40), car_stats_card_rect, 2, border_radius=12)
        car_stats_close_rect = pygame.Rect(car_stats_card_rect.right - 40, car_stats_card_rect.y + 8, 30, 30)
        pygame.draw.rect(screen, BLOOD_RED, car_stats_close_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, car_stats_close_rect, 2, border_radius=6)
        draw_text_with_outline("X", pygame.font.SysFont("Arial", 22, bold=True), WHITE, BLACK, car_stats_close_rect.centerx, car_stats_close_rect.centery)
        draw_text_with_outline("CAR STATS", pygame.font.SysFont("Arial", 24, bold=True), ORANGE, BLACK, car_stats_card_rect.centerx, car_stats_card_rect.y + 22)
        car_preview = pygame.transform.scale(car_img, (280, 130))
        screen.blit(car_preview, car_preview.get_rect(center=(car_stats_card_rect.centerx, car_stats_card_rect.y + 118)))
        st = get_player_car_showroom_stats()
        row_font = pygame.font.SysFont("Arial", 17, bold=True)
        lab_x = car_stats_card_rect.x + 36
        y0 = car_stats_card_rect.y + 200
        lines = [
            ("Car speed", str(st["speed"])),
            ("Power unit", str(st["power_unit"])),
            ("Cornering", str(st["cornering"])),
            ("Qualifying", str(st["qualifying"])),
            ("Average pit stop time", f"{st['pit_s']:.2f}s"),
            ("Overtake mode", str(st["overtake_mode"])),
        ]
        for i, (lab, val) in enumerate(lines):
            yy = y0 + i * 34
            draw_text_with_outline(lab, row_font, LIGHT_GRAY, BLACK, lab_x, yy, align="left")
            draw_text_with_outline(val, row_font, GOLD if i < 4 else WHITE, BLACK, car_stats_card_rect.right - 40, yy, align="right")

def music_panel_layout():
    """Muzikos skydelis ir mažas uždarymo kvadratas (X) — kairėje, kad nesidengtų su cover."""
    panel_rect = pygame.Rect(WIDTH - 275, 15, 260, 70)
    close_rect = pygame.Rect(panel_rect.x + 6, panel_rect.y + 6, 18, 18)
    return panel_rect, close_rect


def draw_music_info():
    if not playlist or music_panel_dismissed:
        return
    track = playlist[current_track_idx]
    panel_rect, close_rect = music_panel_layout()
    s = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 140), s.get_rect(), border_radius=8)
    screen.blit(s, (panel_rect.x, panel_rect.y))
    pygame.draw.rect(screen, (55, 55, 62), close_rect, border_radius=4)
    pygame.draw.rect(screen, (130, 130, 140), close_rect, 1, border_radius=4)
    cx, cy = close_rect.centerx, close_rect.centery
    d = 4
    pygame.draw.line(screen, (220, 220, 228), (cx - d, cy - d), (cx + d, cy + d), 2)
    pygame.draw.line(screen, (220, 220, 228), (cx - d, cy + d), (cx + d, cy - d), 2)
    if current_cover_surf:
        screen.blit(current_cover_surf, (panel_rect.right - 60, panel_rect.y + 10))
    tx0 = panel_rect.x + 30
    draw_text_with_outline(track["title"], font_music_bold, WHITE, BLACK, tx0, panel_rect.y + 10, align="left")
    draw_text_with_outline(track["artist"], font_music_small, LIGHT_GRAY, BLACK, tx0, panel_rect.y + 32, align="left")
    screen.blit(font_hint.render("Press 'N' for next track", True, (180, 180, 180)), (tx0, panel_rect.y + 52))

def draw_team_label(name, x_pos, y_pos, max_width, color):
    words = name.split(" ")
    lines = [name] if len(words) == 1 else [" ".join(words[:-1]), words[-1]]
    font_size = 19
    while font_size >= 10:
        fnt = pygame.font.SysFont("Arial", font_size, bold=True)
        widths = [fnt.size(line)[0] for line in lines]
        if max(widths) <= max_width:
            break
        font_size -= 1
    fnt = pygame.font.SysFont("Arial", max(font_size, 10), bold=True)
    line_gap = 3
    line_height = fnt.get_height()
    total_height = len(lines) * line_height + (len(lines) - 1) * line_gap
    start_y = y_pos - total_height // 2
    for i, line in enumerate(lines):
        draw_text_with_outline(line, fnt, color, BLACK, x_pos, start_y + i * (line_height + line_gap))

def draw_wrapped_center_text(text, max_width, center_x, y_start, color, min_size=13, max_size=20):
    words = text.split()
    chosen_font = pygame.font.SysFont("Arial", max_size, bold=True)
    chosen_lines = [text]

    for font_size in range(max_size, min_size - 1, -1):
        trial_font = pygame.font.SysFont("Arial", font_size, bold=True)
        lines = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if trial_font.size(trial)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        if len(lines) <= 2:
            chosen_font = trial_font
            chosen_lines = lines
            break

    line_h = chosen_font.get_height()
    for idx, line in enumerate(chosen_lines):
        draw_text_with_outline(line, chosen_font, color, BLACK, center_x, y_start + idx * (line_h + 3))

def draw_wheel_scene():
    global is_spinning, last_tick_slot

    card_w, card_h, gap = 135, 140, 14
    center_x = reel_window.centerx
    current_offset = reel_start_offset
    just_finished = False
    if is_spinning:
        elapsed = pygame.time.get_ticks() - spin_start_time
        progress = min(1.0, elapsed / spin_duration_ms)
        eased = 1.0 - (1.0 - progress) ** 3
        current_offset = reel_start_offset + (reel_target_offset - reel_start_offset) * eased
        step = card_w + gap
        center_idx = int((current_offset + center_x - reel_window.x - card_w / 2) / step)
        if center_idx != last_tick_slot:
            if tick_sound:
                tick_sound.play()
            last_tick_slot = center_idx
        if progress >= 1.0:
            is_spinning = False
            current_offset = reel_target_offset
            if win_sound:
                win_sound.play()
            just_finished = True

    panel = pygame.Surface((reel_window.width, reel_window.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (12, 12, 18, 230), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (80, 160, 255), panel.get_rect(), 2, border_radius=10)
    screen.blit(panel, (reel_window.x, reel_window.y))

    clip_backup = screen.get_clip()
    screen.set_clip(reel_window)
    for idx, team in enumerate(reel_items):
        x = reel_window.x + idx * (card_w + gap) - current_offset
        y = reel_window.y + (reel_window.height - card_h) // 2
        if x + card_w < reel_window.x - 20 or x > reel_window.right + 20:
            continue
        pygame.draw.rect(screen, team["color"], (x, y, card_w, card_h), border_radius=8)
        pygame.draw.rect(screen, WHITE, (x, y, card_w, card_h), 2, border_radius=8)
        draw_team_label(team["name"], int(x + card_w / 2), int(y + card_h / 2), card_w - 16, BLACK if sum(team["color"]) > 420 else WHITE)
    screen.set_clip(clip_backup)

    pygame.draw.rect(screen, WHITE, (center_x - 4, reel_window.y - 14, 8, reel_window.height + 28), border_radius=4)
    pygame.draw.polygon(screen, ORANGE, [(center_x, reel_window.y - 22), (center_x - 16, reel_window.y - 2), (center_x + 16, reel_window.y - 2)])

    btn_color = (90, 170, 255) if is_spinning else ORANGE
    pygame.draw.rect(screen, btn_color, spin_button_rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, spin_button_rect, 2, border_radius=10)
    draw_text_with_outline("OPEN CASE", pygame.font.SysFont("Arial", 24, bold=True), WHITE, BLACK, spin_button_rect.centerx, spin_button_rect.centery)
    return just_finished

def draw_sponsor_reel(row_names, reel_rect, reel_idx):
    global sponsor_reel_spinning, sponsor_reel_offsets, sponsor_last_tick_slot, sponsor_result_revealed, upgrade_inventory
    card_w, card_h, gap = 125, 92, 10
    current_offset = sponsor_reel_offsets[reel_idx]
    if sponsor_reel_spinning[reel_idx]:
        elapsed = pygame.time.get_ticks() - sponsor_reel_start_time[reel_idx]
        progress = min(1.0, elapsed / sponsor_reel_duration[reel_idx])
        eased = 1.0 - (1.0 - progress) ** 3
        current_offset = sponsor_reel_offsets[reel_idx] + (sponsor_reel_targets[reel_idx] - sponsor_reel_offsets[reel_idx]) * eased
        step = card_w + gap
        center_idx = int((current_offset + reel_rect.centerx - reel_rect.x - card_w / 2) / step)
        if center_idx != sponsor_last_tick_slot[reel_idx]:
            if tick_sound:
                tick_sound.play()
            sponsor_last_tick_slot[reel_idx] = center_idx
        if progress >= 1.0:
            sponsor_reel_spinning[reel_idx] = False
            current_offset = sponsor_reel_targets[reel_idx]
            sponsor_reel_offsets[reel_idx] = current_offset
            sponsor_result_revealed[reel_idx] = True
            if reel_idx == 1:
                upgrade_inventory[upgrade_result] += 1
            if win_sound:
                win_sound.play()
    panel = pygame.Surface((reel_rect.width, reel_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (12, 12, 18, 230), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (80, 160, 255), panel.get_rect(), 2, border_radius=10)
    screen.blit(panel, (reel_rect.x, reel_rect.y))
    clip_backup = screen.get_clip()
    screen.set_clip(reel_rect)
    for idx, name in enumerate(row_names):
        x = reel_rect.x + 8 + idx * (card_w + gap) - current_offset
        y = reel_rect.y + (reel_rect.height - card_h) // 2
        if x + card_w < reel_rect.x - 10 or x > reel_rect.right + 10:
            continue
        color = F1_TEAMS[(idx + reel_idx) % len(F1_TEAMS)]["color"]
        pygame.draw.rect(screen, color, (x, y, card_w, card_h), border_radius=8)
        pygame.draw.rect(screen, WHITE, (x, y, card_w, card_h), 2, border_radius=8)
        draw_team_label(name, x + card_w // 2, y + card_h // 2, card_w - 12, BLACK if sum(color) > 420 else WHITE)
    screen.set_clip(clip_backup)
    pygame.draw.rect(screen, WHITE, (reel_rect.centerx - 3, reel_rect.y - 8, 6, reel_rect.height + 16), border_radius=3)


SAVE_FILE_PATH = os.path.join(BASE_DIR, "saves", "career_progress.json")
career_data_manager = CareerDataManager(serializer=JsonSnapshotSerializer())


def _serialize_championship_points():
    out = {}
    for key, value in championship_points.items():
        if isinstance(key, tuple) and len(key) == 2:
            out[f"{key[0]}::{key[1]}"] = int(value)
    return out


def _deserialize_championship_points(raw):
    out = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        if not isinstance(key, str) or "::" not in key:
            continue
        a, b = key.split("::", 1)
        out[(a, b)] = int(value)
    return out


def build_career_snapshot():
    return CareerSnapshot(
        driver=DriverIdentity(
            name=driver_data.get("Name", {}).get("text", ""),
            surname=driver_data.get("Surname", {}).get("text", ""),
            number=driver_data.get("Number", {}).get("text", ""),
            country=driver_data.get("Country", {}).get("text", ""),
        ),
        economy=EconomyState(
            money_balance=int(money_balance),
            upgrade_inventory=dict(upgrade_inventory),
            upgrade_levels=dict(upgrade_levels),
        ),
        car_development=CarDevelopmentState(
            car_part_tiers=dict(car_part_tiers),
            teammate_car_tiers=dict(teammate_car_tiers),
        ),
        meta=CareerMetaState(
            winning_team_name=winning_team_name,
            teammate_result=teammate_result,
            season_gp_index=int(season_gp_index),
            championship_points=_serialize_championship_points(),
            career_profile_unlocked=bool(career_profile_unlocked),
            season_started_once=bool(season_started_once),
            signing_bonus_given=bool(signing_bonus_given),
            selected_offer_name=selected_offer_name,
        ),
    )


def apply_career_snapshot(snapshot):
    global money_balance, winning_team_name, teammate_result, season_gp_index
    global career_profile_unlocked, season_started_once, signing_bonus_given, selected_offer_name
    global championship_points, teammate_img, post_race_chest

    driver_data["Name"]["text"] = snapshot.driver.name
    driver_data["Surname"]["text"] = snapshot.driver.surname
    driver_data["Number"]["text"] = snapshot.driver.number
    driver_data["Country"]["text"] = snapshot.driver.country

    money_balance = int(snapshot.economy.money_balance)
    for k in upgrade_inventory.keys():
        upgrade_inventory[k] = int(snapshot.economy.upgrade_inventory.get(k, 0))
    for k in upgrade_levels.keys():
        upgrade_levels[k] = int(snapshot.economy.upgrade_levels.get(k, 0))
    for k in car_part_tiers.keys():
        car_part_tiers[k] = int(snapshot.car_development.car_part_tiers.get(k, car_part_tiers[k]))
    for k in teammate_car_tiers.keys():
        teammate_car_tiers[k] = int(snapshot.car_development.teammate_car_tiers.get(k, teammate_car_tiers[k]))

    winning_team_name = snapshot.meta.winning_team_name
    teammate_result = snapshot.meta.teammate_result
    season_gp_index = int(snapshot.meta.season_gp_index) % max(1, len(SEASON_GP_CALENDAR))
    championship_points = _deserialize_championship_points(snapshot.meta.championship_points)
    career_profile_unlocked = bool(snapshot.meta.career_profile_unlocked)
    season_started_once = bool(snapshot.meta.season_started_once)
    signing_bonus_given = bool(snapshot.meta.signing_bonus_given)
    selected_offer_name = snapshot.meta.selected_offer_name

    post_race_chest = None
    if teammate_result:
        teammate_surname = teammate_result.split(" ")[-1]
        teammate_img_path = f"images/{teammate_surname}.jpg"
        teammate_img = load_and_convert_img(teammate_img_path, (190, 190))

    rebuild_season_track_geometry(force=True)


def save_career_state_to_file():
    try:
        career_data_manager.save_snapshot(SAVE_FILE_PATH, build_career_snapshot())
    except Exception:
        # Persistence must never break gameplay flow.
        pass


def load_career_state_from_file():
    try:
        snapshot = career_data_manager.load_snapshot(SAVE_FILE_PATH)
        if snapshot is not None:
            apply_career_snapshot(snapshot)
    except Exception:
        pass


load_career_state_from_file()

# --- PAGRINDINIS CIKLAS ---
running = True
while running:
    screen.fill(BLACK)
    any_field_active = any(f["active"] for f in driver_data.values())
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == SONG_END:
            current_track_idx = (current_track_idx + 1) % len(playlist); play_track(current_track_idx)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if (
                event.button == 1
                and playlist
                and not music_panel_dismissed
            ):
                _, music_close_rect = music_panel_layout()
                if music_close_rect.collidepoint(event.pos):
                    music_panel_dismissed = True
                    continue
            if game_state == "MAIN_MENU" and event.button == 1:
                if main_menu_career_rect().collidepoint(event.pos):
                    if career_profile_unlocked:
                        game_state = "PROFILE"
                    else:
                        game_state = "CHARACTER_CREATION"
            elif game_state == "CHARACTER_CREATION":
                for f in driver_data.values(): f["active"] = f["rect"].collidepoint(event.pos)
            elif game_state == "WHEEL_SPIN":
                if event.button == 1 and show_wheel_intro and guide_card_rect.collidepoint(event.pos):
                    show_wheel_intro = False
                elif event.button == 1 and not is_spinning and not show_wheel_intro:
                    if spin_button_rect.collidepoint(event.pos):
                        start_weighted_spin()
            elif game_state == "SPONSOR_OFFERS":
                if event.button == 1:
                    if open_teammate_btn.collidepoint(event.pos):
                        drivers = TEAM_DRIVERS_2025.get(winning_team_name, ["Driver A", "Driver B"])
                        teammate_result = random.choice(drivers)
                        sync_roster_after_teammate_pick()
                        teammate_reel = [random.choice(drivers) for _ in range(30)]
                        final_idx = random.randint(22, 27)
                        teammate_reel[final_idx] = teammate_result
                        sponsor_reel_rows[0] = teammate_reel
                        card_w, gap = 125, 10
                        sponsor_reel_offsets[0] = 0.0
                        sponsor_reel_targets[0] = (sponsor_reel_windows[0].x + 8 + final_idx * (card_w + gap) + card_w / 2) - sponsor_reel_windows[0].centerx
                        sponsor_reel_start_time[0] = pygame.time.get_ticks()
                        sponsor_reel_duration[0] = random.randint(2800, 4200)
                        sponsor_reel_spinning[0] = True
                        sponsor_last_tick_slot[0] = -1
                        sponsor_result_revealed[0] = False
                    elif open_upgrade_btn.collidepoint(event.pos):
                        upgrade_result = random.choice(UPGRADE_POOL)
                        upgrade_reel = [random.choice(UPGRADE_POOL) for _ in range(30)]
                        final_idx = random.randint(22, 27)
                        upgrade_reel[final_idx] = upgrade_result
                        sponsor_reel_rows[1] = upgrade_reel
                        card_w, gap = 125, 10
                        sponsor_reel_offsets[1] = 0.0
                        sponsor_reel_targets[1] = (sponsor_reel_windows[1].x + 8 + final_idx * (card_w + gap) + card_w / 2) - sponsor_reel_windows[1].centerx
                        sponsor_reel_start_time[1] = pygame.time.get_ticks()
                        sponsor_reel_duration[1] = random.randint(2800, 4200)
                        sponsor_reel_spinning[1] = True
                        sponsor_last_tick_slot[1] = -1
                        sponsor_result_revealed[1] = False
                    else:
                        offer_box_w = 360
                        offer_box_h = 95
                        start_x = 45
                        y_box = HEIGHT - 118
                        for idx in range(3):
                            box_x = start_x + idx * (offer_box_w + 25)
                            if pygame.Rect(box_x, y_box, offer_box_w, offer_box_h).collidepoint(event.pos):
                                selected_offer_idx = idx
                                break
                    if selected_offer_idx != -1 and next_arrow_rect.collidepoint(event.pos) and all(sponsor_result_revealed):
                        if not signing_bonus_given:
                            money_balance += get_offer_signing_bonus(selected_offer_idx)
                            selected_offer_name = get_offer_name(selected_offer_idx)
                            signing_bonus_given = True
                        teammate_surname = teammate_result.split(" ")[-1] if teammate_result else ""
                        teammate_img_path = f"images/{teammate_surname}.jpg" if teammate_surname else "images/avataras.jpg"
                        teammate_img = load_and_convert_img(teammate_img_path, (190, 190))
                        career_profile_unlocked = True
                        game_state = "PROFILE"
                        save_career_state_to_file()
            elif game_state == "PROFILE" and event.button == 1:
                card_w, card_h = 560, 660
                profile_card_rect = pygame.Rect(WIDTH // 2 - card_w // 2, HEIGHT // 2 - card_h // 2, card_w, card_h)
                ctw, cth = 520, 440
                car_stats_modal = pygame.Rect(WIDTH // 2 - ctw // 2, HEIGHT // 2 - cth // 2, ctw, cth)
                car_stats_xbtn = pygame.Rect(car_stats_modal.right - 40, car_stats_modal.y + 8, 30, 30)
                absorbed = False
                if show_car_stats_card and car_stats_xbtn.collidepoint(event.pos):
                    show_car_stats_card = False
                    absorbed = True
                elif show_car_stats_card and car_stats_modal.collidepoint(event.pos):
                    absorbed = True
                elif show_teammate_card and teammate_card_close_rect.collidepoint(event.pos):
                    show_teammate_card = False
                    absorbed = True
                elif show_teammate_card and profile_card_rect.collidepoint(event.pos):
                    absorbed = True
                elif start_race_rect.collidepoint(event.pos):
                    show_teammate_card = False
                    show_car_stats_card = False
                    season_started_once = True
                    if winning_team_name and not teammate_result:
                        pair = TEAM_DRIVERS_2025.get(winning_team_name, [])
                        if pair:
                            teammate_result = pair[0]
                    sync_roster_after_teammate_pick()
                    sim_race_laps_this_round = random.randint(5, 8)
                    setup_qualifying_session_from_profile()
                    register_championship_drivers_from_grid(qual_session_cars)
                    pre_race_qualifying_done = False
                    music_panel_dismissed = False
                    sync_pre_race_provisional_grid_from_championship()
                    game_state = "PRE_RACE"
                    absorbed = True
                elif profile_car_box_rect.width > 0 and profile_car_box_rect.collidepoint(event.pos):
                    show_car_stats_card = not show_car_stats_card
                    if show_car_stats_card:
                        show_teammate_card = False
                    absorbed = True
                elif teammate_box_click_rect.collidepoint(event.pos):
                    show_teammate_card = not show_teammate_card
                    if show_teammate_card:
                        show_car_stats_card = False
                    absorbed = True
                if not absorbed:
                    for upg, btn in upgrade_apply_buttons.items():
                        if btn.collidepoint(event.pos) and upgrade_inventory[upg] > 0 and upgrade_levels[upg] < 20:
                            upgrade_inventory[upg] -= 1
                            upgrade_levels[upg] += 1
                            save_career_state_to_file()
                    if pending_car_part and buy_button_rect.collidepoint(event.pos):
                        tier = car_part_tiers[pending_car_part]
                        _, _, next_cost = RARITY_STEPS[tier]
                        if next_cost is not None and money_balance >= next_cost:
                            money_balance -= next_cost
                            car_part_tiers[pending_car_part] += 1
                            save_career_state_to_file()
                        pending_car_part = None
                    else:
                        for part, btn in car_upgrade_buttons.items():
                            if btn.collidepoint(event.pos):
                                tier = car_part_tiers[part]
                                _, _, next_cost = RARITY_STEPS[tier]
                                if next_cost is not None:
                                    pending_car_part = part
                                break
            elif game_state == "QUALIFYING_INTRO" and event.button == 1:
                if qualifying_intro_button_rect().collidepoint(event.pos):
                    game_state = "QUALIFYING_RUN"
                    qual_start_q1_animation()
            elif game_state == "QUALIFYING_RUN" and event.button == 1:
                if qual_last_action_rect.width > 0 and qual_last_action_rect.collidepoint(event.pos):
                    if qual_phase == "q1_done":
                        qual_start_q2_animation()
                    elif qual_phase == "q2_done":
                        qual_start_q3_animation()
                    elif qual_phase == "q3_done":
                        qual_apply_results_to_pre_race_grid()
                        pre_race_qualifying_done = True
                        rebuild_season_track_geometry()
                        init_race_setup_from_grid()
                        game_state = "RACE_SETUP"
            elif game_state == "PRE_RACE" and event.button == 1:
                if pre_race_start_button_rect().collidepoint(event.pos):
                    if pre_race_qualifying_done:
                        init_race_setup_from_grid()
                        game_state = "RACE_SETUP"
                    else:
                        music_panel_dismissed = False
                        game_state = "QUALIFYING_INTRO"
            elif game_state == "RACE_SETUP" and event.button == 1:
                for tyre_key, rr in race_setup_tyre_rects.items():
                    if rr.collidepoint(event.pos):
                        race_setup_selected_tyre = tyre_key
                        break
                if race_setup_btn_rect.width > 0 and race_setup_btn_rect.collidepoint(event.pos):
                    start_race_session_from_setup()
                    game_state = "RACE"
            elif game_state == "RACE" and event.button == 1:
                if race_phase == "green":
                    hit_push = False
                    for mode, rr in race_push_rects.items():
                        if rr.collidepoint(event.pos):
                            race_player_push_mode = mode
                            hit_push = True
                            break
                    if (
                        (not hit_push)
                        and race_pit_now_rect.width > 0
                        and race_pit_now_rect.collidepoint(event.pos)
                    ):
                        race_player_pit_request = True
            elif game_state == "RACE_PODIUM" and event.button == 1:
                game_state = "RACE_RESULTS"
                race_results_tab = "drivers"
            elif game_state == "RACE_RESULTS" and event.button == 1:
                if race_results_drivers_tab_rect.collidepoint(event.pos):
                    race_results_tab = "drivers"
                elif race_results_teams_tab_rect.collidepoint(event.pos):
                    race_results_tab = "teams"
                elif race_results_continue_rect.width > 0 and race_results_continue_rect.collidepoint(event.pos):
                    post_race_chest = None
                    game_state = "CHEST_REWARD"
            elif game_state == "CHEST_REWARD" and event.button == 1:
                if chest_continue_rect.width > 0 and chest_continue_rect.collidepoint(event.pos):
                    season_gp_index = (season_gp_index + 1) % len(SEASON_GP_CALENDAR)
                    rebuild_season_track_geometry()
                    game_state = "PROFILE"
                    save_career_state_to_file()

        if event.type == pygame.KEYDOWN:
            typing_in_driver_form = game_state == "CHARACTER_CREATION" and any(f["active"] for f in driver_data.values())
            if event.key == pygame.K_n and playlist and not typing_in_driver_form:
                current_track_idx = (current_track_idx + 1) % len(playlist)
                play_track(current_track_idx)
            
            if event.key == pygame.K_ESCAPE:
                if game_state == "TITLE":
                    running = False
                elif game_state == "RACE":
                    race_auto_podium_deadline_ms = 0
                    music_panel_dismissed = False
                    game_state = "PROFILE"
                    season_gp_index = (season_gp_index + 1) % len(SEASON_GP_CALENDAR)
                    rebuild_season_track_geometry()
                elif game_state == "RACE_PODIUM":
                    game_state = "RACE_RESULTS"
                    race_results_tab = "drivers"
                elif game_state == "RACE_RESULTS":
                    post_race_chest = None
                    game_state = "CHEST_REWARD"
                elif game_state == "CHEST_REWARD":
                    season_gp_index = (season_gp_index + 1) % len(SEASON_GP_CALENDAR)
                    rebuild_season_track_geometry()
                    game_state = "PROFILE"
                    save_career_state_to_file()
                elif game_state == "RACE_SETUP":
                    game_state = "PROFILE"
                elif game_state == "PRE_RACE":
                    game_state = "PROFILE"
                elif game_state in ("QUALIFYING_INTRO", "QUALIFYING_RUN"):
                    game_state = "PROFILE"
                else:
                    game_state = "MAIN_MENU" if game_state != "MAIN_MENU" else "TITLE"
            elif event.key == pygame.K_F5:
                save_career_state_to_file()
            elif event.key == pygame.K_F9:
                load_career_state_from_file()
            
            elif game_state == "TITLE" and event.key == pygame.K_SPACE: game_state = "MAIN_MENU"
            elif game_state == "MAIN_MENU" and event.key == pygame.K_LEFT:
                if career_profile_unlocked:
                    game_state = "PROFILE"
                else:
                    game_state = "CHARACTER_CREATION"
            
            elif game_state == "CHARACTER_CREATION":
                if event.key == pygame.K_RETURN:
                    all_filled = all(len(f["text"].strip()) > 0 for f in driver_data.values())
                    num_str = driver_data["Number"]["text"]
                    if not all_filled: error_msg, error_timer = "PLEASE FILL ALL FIELDS!", 120
                    elif num_str == "1": error_msg, error_timer = "NUMBER 1 IS FOR THE CHAMPION ONLY!", 150
                    elif not (num_str.isdigit() and 2 <= int(num_str) <= 99): error_msg, error_timer = "INVALID NUMBER! CHOOSE 2-99", 150
                    elif int(num_str) in AI_DRIVER_NUMBERS: error_msg, error_timer = "NUMBER USED BY F1 AI DRIVER!", 170
                    else:
                        for f in driver_data.values():
                            f["active"] = False
                        game_state = "WHEEL_SPIN"
                        show_wheel_intro = True
                        winning_team_name = ""
                        save_career_state_to_file()

                for key, field in driver_data.items():
                    if field["active"]:
                        if event.key == pygame.K_BACKSPACE: field["text"] = field["text"][:-1]
                        elif key == "Number":
                            if event.unicode.isnumeric() and len(field["text"]) < 2: field["text"] += event.unicode
                        elif len(field["text"]) < 15: field["text"] += event.unicode

    qualifying_tick_frame()
    race_tick_frame()
    if (
        game_state == "RACE"
        and race_phase == "finished"
        and race_auto_podium_deadline_ms
        and pygame.time.get_ticks() >= race_auto_podium_deadline_ms
    ):
        game_state = "RACE_PODIUM"
        race_auto_podium_deadline_ms = 0

    # --- PIEŠIMAS ---
    if game_state == "TITLE":
        if title_bg: screen.blit(title_bg, (0, 0))
        draw_text_with_outline("Press space if you are ready to WIN", font_ui, BLOOD_RED, ORANGE, WIDTH // 2, 540)
        
    elif game_state == "MAIN_MENU":
        for drop in rain_drops: drop.fall(); drop.draw(get_led_color(drop.x))
        pulse_t = pygame.time.get_ticks() * 0.008
        card = main_menu_career_rect()
        pygame.draw.rect(screen, BLACK, card, border_radius=10)
        screen.blit(career_img, career_img.get_rect(center=card.center))
        for i in range(5):
            inset = i * 2
            rr = card.inflate(-inset * 2, -inset * 2)
            if rr.width <= 6 or rr.height <= 6:
                break
            amp = 0.55 + 0.45 * math.sin(pulse_t + i * 0.7)
            led_col = (
                min(255, int(ORANGE[0] * amp + 18)),
                min(255, int(ORANGE[1] * amp + 18)),
                min(255, int(ORANGE[2] * amp + 18)),
            )
            pygame.draw.rect(screen, led_col, rr, width=1 if i > 1 else 2, border_radius=10)
        draw_text_with_outline("CAREER MODE", font_ui, ORANGE, (255, 220, 120), card.centerx, card.y - 36)
        draw_text_with_outline("CLICK ON IT", font_instr, WHITE, BLACK, card.centerx, card.bottom + 34)
        
    elif game_state == "CHARACTER_CREATION":
        screen.fill(BLACK)
        for drop in rain_drops:
            drop.fall()
            drop.draw(get_led_color(drop.x + 90))
        draw_text_with_outline("CREATE YOUR DRIVER", font_main, BLOOD_RED, ORANGE, WIDTH // 2, 80)
        # Solid panel behind fields so LED rain doesn't distract near inputs.
        field_panel = pygame.Rect(356, 170, 540, 320)
        pygame.draw.rect(screen, (8, 10, 14), field_panel, border_radius=10)
        pygame.draw.rect(screen, (90, 96, 110), field_panel, 2, border_radius=10)
        for label, field in driver_data.items():
            screen.blit(font_ui.render(f"{label}:", True, WHITE), (380, field["rect"].y + 5))
            pygame.draw.rect(screen, GOLD if field["active"] else LIGHT_GRAY, field["rect"], 2)
            screen.blit(font_ui.render(field["text"], True, WHITE), (field["rect"].x + 10, field["rect"].y + 5))
        if error_timer > 0:
            color = BLOOD_RED if any(x in error_msg for x in ["INVALID", "ONLY", "FILL"]) else GOLD
            draw_text_with_outline(error_msg, font_ui, color, WHITE, WIDTH // 2, 520); error_timer -= 1
        draw_text_with_outline("PRESS ENTER TO CONFIRM", font_instr, WHITE, BLACK, WIDTH // 2, 650)

    elif game_state == "WHEEL_SPIN":
        screen.fill(BLACK)
        for drop in rain_drops:
            drop.fall()
            drop.draw(get_led_color(drop.x))
        draw_text_with_outline("Team Case Opening", font_main, WHITE, DRAMATIC_BLUE, WIDTH // 2, 70)
        if show_wheel_intro:
            draw_wheel_scene()
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 165))
            screen.blit(overlay, (0, 0))
            card_surf = pygame.Surface((guide_card_rect.width, guide_card_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (18, 18, 24, 242), card_surf.get_rect(), border_radius=12)
            pygame.draw.rect(card_surf, (90, 160, 255), card_surf.get_rect(), 2, border_radius=12)
            screen.blit(card_surf, (guide_card_rect.x, guide_card_rect.y))
            screen.blit(guide_img, guide_img.get_rect(center=(guide_card_rect.centerx, guide_card_rect.y + 165)))
            player_name = driver_data["Name"]["text"].strip() or "Driver"
            draw_text_with_outline("Career Guide", font_ui, (120, 200, 255), BLACK, guide_card_rect.centerx, guide_card_rect.y + 330)
            draw_wrapped_center_text(f"Welcome to Career Mode, {player_name}.", 250, guide_card_rect.centerx, guide_card_rect.y + 356, WHITE)
            draw_text_with_outline("Your first team will now be decided.", pygame.font.SysFont("Arial", 17, bold=True), LIGHT_GRAY, BLACK, guide_card_rect.centerx, guide_card_rect.y + 417)
            draw_text_with_outline("CLICK ON ME TO BEGIN", font_instr, ORANGE, BLACK, guide_card_rect.centerx, guide_card_rect.y + 438)
        else:
            finished_now = draw_wheel_scene()
            if finished_now:
                generate_sponsor_screen()
                game_state = "SPONSOR_OFFERS"

    elif game_state == "SPONSOR_OFFERS":
        screen.fill(BLACK)
        for drop in rain_drops:
            drop.fall()
            drop.draw(get_led_color(drop.x + 100))
        draw_text_with_outline("SPONSOR OFFERS", font_main, WHITE, DRAMATIC_BLUE, WIDTH // 2, 50)
        draw_text_with_outline(f"CONGRATULATIONS! YOU JOINED {winning_team_name.upper()}", font_ui, GOLD, BLACK, WIDTH // 2, 90)

        draw_sponsor_reel(sponsor_reel_rows[0], sponsor_reel_windows[0], 0)
        pygame.draw.rect(screen, (70, 150, 255), open_teammate_btn, border_radius=8)
        pygame.draw.rect(screen, WHITE, open_teammate_btn, 2, border_radius=8)
        draw_text_with_outline("OPEN TEAMMATE CASE", pygame.font.SysFont("Arial", 19, bold=True), WHITE, BLACK, open_teammate_btn.centerx, open_teammate_btn.centery)
        if sponsor_result_revealed[0]:
            draw_text_with_outline(f"Result: {teammate_result}", pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, WIDTH // 2 + 250, open_teammate_btn.centery)

        draw_sponsor_reel(sponsor_reel_rows[1], sponsor_reel_windows[1], 1)
        pygame.draw.rect(screen, (70, 150, 255), open_upgrade_btn, border_radius=8)
        pygame.draw.rect(screen, WHITE, open_upgrade_btn, 2, border_radius=8)
        draw_text_with_outline("OPEN UPGRADE CASE", pygame.font.SysFont("Arial", 19, bold=True), WHITE, BLACK, open_upgrade_btn.centerx, open_upgrade_btn.centery)
        if sponsor_result_revealed[1]:
            draw_text_with_outline(f"Result: {upgrade_result}", pygame.font.SysFont("Arial", 20, bold=True), WHITE, BLACK, WIDTH // 2 + 250, open_upgrade_btn.centery)

        offer_box_w = 360
        offer_box_h = 95
        start_x = 45
        y_box = HEIGHT - 118
        for idx, offer_lines in enumerate(sponsor_offers):
            box_x = start_x + idx * (offer_box_w + 25)
            pygame.draw.rect(screen, (16, 16, 22), (box_x, y_box, offer_box_w, offer_box_h), border_radius=10)
            border_color = ORANGE
            if selected_offer_idx == idx:
                led = get_led_color(idx * 2.5)
                border_color = led
            pygame.draw.rect(screen, border_color, (box_x, y_box, offer_box_w, offer_box_h), 3, border_radius=10)
            for line_idx, text in enumerate(offer_lines):
                draw_text_with_outline(text, pygame.font.SysFont("Arial", 18, bold=True), WHITE, BLACK, box_x + 12, y_box + 12 + line_idx * 25, align="left")

        if selected_offer_idx != -1 and all(sponsor_result_revealed):
            pygame.draw.polygon(
                screen,
                BLOOD_RED,
                [
                    (next_arrow_rect.x, next_arrow_rect.y),
                    (next_arrow_rect.x, next_arrow_rect.y + next_arrow_rect.height),
                    (next_arrow_rect.right, next_arrow_rect.y + next_arrow_rect.height // 2),
                ],
            )
            draw_text_with_outline("NEXT", pygame.font.SysFont("Arial", 12, bold=True), WHITE, BLACK, next_arrow_rect.x - 6, next_arrow_rect.y + next_arrow_rect.height // 2)

    elif game_state == "PROFILE":
        screen.fill(BLACK)
        for drop in rain_drops:
            drop.fall()
            drop.draw(get_led_color(drop.x + 160))
        draw_profile_screen()

    elif game_state == "QUALIFYING_INTRO":
        screen.fill(BLACK)
        draw_qualifying_intro_screen()
        draw_text_with_outline("ESC — profile", font_exit, (200, 200, 210), BLACK, 18, 18, align="left")

    elif game_state == "QUALIFYING_RUN":
        screen.fill(BLACK)
        draw_qualifying_run_screen()
        draw_text_with_outline("ESC — profile", font_exit, (200, 200, 210), BLACK, 18, 18, align="left")

    elif game_state == "PRE_RACE":
        draw_pre_race_screen()

    elif game_state == "RACE_SETUP":
        draw_race_setup_screen()

    elif game_state == "RACE":
        draw_race_screen()
    elif game_state == "RACE_PODIUM":
        draw_race_podium_screen()
    elif game_state == "RACE_RESULTS":
        draw_race_results_screen()
    elif game_state == "CHEST_REWARD":
        draw_post_race_chest_screen()

    if game_state == "PROFILE":
        draw_text_with_outline(f"MONEY: ${money_balance}", pygame.font.SysFont("Arial", 22, bold=True), GOLD, BLACK, WIDTH // 2, 22)

    if game_state not in ("TITLE", "RACE", "RACE_PODIUM", "RACE_RESULTS", "CHEST_REWARD", "RACE_SETUP", "PRE_RACE", "QUALIFYING_INTRO", "QUALIFYING_RUN"):
        draw_text_with_outline("PRESS ESC TO GO BACK", font_exit, WHITE, BLACK, 20, 20, align="left")

    draw_music_info()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()