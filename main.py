import pygame
import math 
import random
import sys

pygame.init()

# --- Config ---
SCREEN_W, SCREEN_H = 800, 600
IMAGE_W, IMAGE_H = 1000, 600
TILE_SIZE = 16
SCALE = 2
DISPLAY_TILE = TILE_SIZE * SCALE  # 32
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Horror Window Game")
clock = pygame.time.Clock()
font_small = pygame.font.SysFont(None, 30)
font_large = pygame.font.SysFont(None, 50)
CIRCLE_POS = (400, 300)
CIRCLE_RADIUS = 70
HOLD_TIME_GOAL = 10
pull_force_x = 0
pull_force_y = 0
last_pull_time = 0
map_img = pygame.image.load("images/CamMap-removebg-preview.png").convert_alpha()
map_img = pygame.transform.scale(map_img, (500, 300))
noise_img = pygame.image.load("images/noise-bg.jpg").convert_alpha()
noise_img = pygame.transform.scale(noise_img, (800,600))
noise_img.set_alpha(40)

dots_grid = [[None for _ in range(6)] for _ in range(6)]
completed_paths = {}
drawing_path = []
current_color = None
is_finishing_stroke = False
# --- CONFIGURATION ---
DOTS_GRID_SIZE = 6
DOTS_CELL_SIZE = 65
GRID_X_OFFSET = (SCREEN_W - DOTS_GRID_SIZE * DOTS_CELL_SIZE) // 2 + 50
GRID_Y_OFFSET = 130

C_RED    = (255, 50,  50)
C_GREEN  = (50,  255, 50)
C_BLUE   = (50,  80,  255)
C_YELLOW = (255, 255, 50)
C_ORANGE = (255, 150, 50)
C_PURPLE = (200, 50,  255)

LEVELS = [
    [(0,0, 4,2, C_RED),(0,5, 2,3, C_GREEN),(5,0, 3,2, C_BLUE),
     (4,0, 1,1, C_YELLOW),(1,4, 5,5, C_ORANGE),(2,4, 5,4, C_PURPLE)],
    [(0,0, 5,5, C_RED),(1,0, 5,0, C_GREEN),(1,1, 1,4, C_BLUE),
     (2,1, 4,1, C_YELLOW),(5,1, 5,4, C_ORANGE),(2,4, 4,4, C_PURPLE)],
    [(4,1, 4,5, C_RED),(2,0, 2,5, C_GREEN),(5,3, 5,5, C_BLUE),
     (3,0, 4,4, C_YELLOW),(1,1, 2,4, C_ORANGE),(1,2, 1,4, C_PURPLE)],
]

# ─────────────────────────────────────────────
# PHONE DIALOGUES
# ─────────────────────────────────────────────
PHONE_DIALOGUES = {
    1: [
        [("police", "Emergency 191, how can I help you?"),
         ("player", "Someone’s breaking into my house! I'm on—"),
         ("police", "Wait... Breaking in? Did they actually do anything to you yet?"),
         ("player", "Not yet, but I—"),
         ("police", "Then just wait and see for now. Might just be someone lost. Call back if something happens."),
         ("police", "...(The line dropped)")],

        [("police", "Emergency 191, what is your emergency?"),
         ("player", "I called before! He's still—"),
         ("police", "Yes, yes, I've got it... Look, all units are busy right now with an actual emergency."),
         ("police", "Try calling back later."),
         ("police", "...(The line dropped)")],

        None,  # 3rd Call+ → I can't get through.
    ],
    2: [
        [("police", "Emergency 191, go ahead."),
         ("player", "The power's out. He cut the lines. I need help—"),
         ("police", "You're the one who just called, right?"),
         ("police", "Listen, if there's no clear threat, we can't just send someone out."),
         ("police", "Gas is expensive, and your place is out in the middle of nowhere..."),
         ("police", "...(The line dropped)")],

        [("police", "Emergency 191."),
         ("player", "Can you hear me? Someone is inside my house—"),
         ("police", "I hear you, I hear you..."),
         ("police", "...Still no officers available right now."),
         ("police", "...(The line dropped)")],

        None,
    ],
    3: [
        [("police", "Emergency 191."),
         ("player", "I’ve been calling all night! He’s still here—"),
         ("police", "Understood. Where are you exactly?"),
         ("police", "We've received reports of a murder suspect at large in that area. We're coordinating now."),
         ("player", "When are you getting here then!?"),
         ("police", "About... two hours. Your house is a long way out."),
         ("police", "Just hang in there. Do not confront him."),
         ("police", "...(The line dropped)")],

        [("police", "Emergency 191."),
         ("police", "Acknowledged. We're doing our best."),
         ("police", "Stay strong...(The line dropped)")],
    ],
    4: [
        [("police", "Emergency 191."),
         ("player", "There's another one now! Help me—"),
         ("police", "Copy that. Units are currently heading your way."),
         ("police", "Find a place to hide. Do not engage, and make sure your doors are locked."),
         ("police", "Not much longer...(The line dropped)")],

        [("police", "Emergency 191."),
         ("police", "Still there? Good. We're almost there."),
         ("police", "Just a little longer. You can do this...(The line dropped)")],
    ],
    5: [
        [("police", "Emergency 191."),
         ("player", "Where are the police!?"),
         ("police", "Less than an hour away. The patrol car is entering the area."),
         ("police", "Do not leave the room under any circumstances. Stay hidden."),
         ("police", "...(The line dropped)")],

        [("police", "Emergency 191."),
         ("police", "Almost there. Just a bit more."),
         ("police", "You've got this...(The line dropped)")],
    ],
}

# --- Hour System ---
current_hour = 1
max_unlocked_hour = 1
game_time = 0
time_speed = 10
hour_duration = 60
game_won = False
hour_intro_shown = False

# --- Blackout System ---
is_blackout = False
blackout_timer = 0
next_blackout_time = 0
blackout_surface = None

# Hour Configurations
hour_configs = {
    1: {"name": "Intro",
        "intro_message": "Hour 1: The night begins...",
        "window_speed_base": 0.1, "ghost_cooldown": 10000,
        "door_attack_cooldown": 10000, "blackout": False,
        "camera_disabled": False, "phone_unlocked": False, "dual_intruder": False},
    2: {"name": "Blackout",
        "intro_message": "Hour 2: The power goes out...",
        "window_speed_base": 0.15, "ghost_cooldown": 9000,
        "door_attack_cooldown": 9000, "blackout": True,
        "camera_disabled": True, "phone_unlocked": False, "dual_intruder": False},
    3: {"name": "Police",
        "intro_message": "Hour 3: 3AM... I decided to call the police...",
        "window_speed_base": 0.2, "ghost_cooldown": 8000,
        "door_attack_cooldown": 8000, "blackout": False,
        "camera_disabled": False, "phone_unlocked": True, "dual_intruder": False},
    4: {"name": "Dual Threat",
        "intro_message": "Hour 4: There's more than 1 intruder! I need to block them both!",
        "window_speed_base": 0.25, "ghost_cooldown": 7000,
        "door_attack_cooldown": 7000, "blackout": False,
        "camera_disabled": False, "phone_unlocked": True, "dual_intruder": True},
    5: {"name": "Nightmare",
        "intro_message": "Hour 5: It's getting worse... Help me...",
        "window_speed_base": 0.3, "ghost_cooldown": 6000,
        "door_attack_cooldown": 6000, "blackout": False,
        "camera_disabled": False, "phone_unlocked": True, "dual_intruder": True},
}

# sound
pygame.mixer.init()
hit_sound        = pygame.mixer.Sound("sounds/door-slamming-sound-effect-no-repeats-or-silence-2016.mp3")
door_knocking    = pygame.mixer.Sound("sounds/door-knocking.mp3")
door_opening     = pygame.mixer.Sound("sounds/fnaf-4-door-opening.mp3")
window_opening   = pygame.mixer.Sound("sounds/door_EJ1ESwu.mp3")
camera_sound     = pygame.mixer.Sound("sounds/fnaf2-camera.mp3")
open_camera_sound= pygame.mixer.Sound("sounds/fnaf-open-camera-sound.mp3")
chasing          = pygame.mixer.Sound("sounds/chasing.mp3")
breathing        = pygame.mixer.Sound("sounds/outofbreath.mp3")
breathing_scream = pygame.mixer.Sound("sounds/heavy-breathing-scream.mp3")
footstep         = pygame.mixer.Sound("sounds/valorant-footstep.mp3")
ambient          = pygame.mixer.Sound("sounds/among-us-reactor-ambient.mp3")
jumpscare        = pygame.mixer.Sound("sounds/raaaaahhh.mp3")
try:
    blackout_sound = pygame.mixer.Sound("sounds/blackout.mp3")
except:
    blackout_sound = None
blackout_sound_playing = False

# --- CCTV Setup ---
cam_setup = {
    "CAM 1": {"empty": "images/cam1.jpg",  "ghost": "images/cam1ghost.jpg"},
    "CAM 2": {"empty": "images/cam2.jpg",  "ghost": "images/cam2ghostfar.jpg",  "ghost2": "images/cam2ghostnear.jpg"},
    "CAM 3": {"empty": "images/cam3.jpg",  "ghost": "images/cam3ghost.jpg"},
    "CAM 4": {"empty": "images/cam4.jpg",  "ghost": "images/cam4ghost.jpg"},
    "CAM 5": {"empty": "images/cam5.jpg",  "ghost": "images/cam5ghost.jpg"},
    "CAM 6": {"empty": "images/cam6.jpg",  "ghost": "images/cam6ghostfar.jpg",  "ghost2": "images/cam6ghostnear.jpg"},
    "CAM 7": {"empty": "images/cam7.jpg",  "ghost": "images/cam7ghost.jpg"},
    "CAM 8": {"empty": "images/cam8.jpg",  "ghost": "images/cam8ghost.jpg"},
    "CAM 9": {"empty": "images/cam9.jpg",  "ghost": "images/cam9ghost.jpg"},
}

cameras = {}
for cam_name, states in cam_setup.items():
    cameras[cam_name] = {}
    for state_name, path in states.items():
        try:
            img = pygame.image.load(path).convert()
            cameras[cam_name][state_name] = pygame.transform.scale(img, (IMAGE_W, IMAGE_H))
        except:
            dummy = pygame.Surface((IMAGE_W, IMAGE_H))
            dummy.fill((50, 50, 50))
            cameras[cam_name][state_name] = dummy

no_signal_surf = pygame.Surface((IMAGE_W, IMAGE_H))
no_signal_surf.fill((10, 10, 10))
ns_font = pygame.font.SysFont("Arial", 60, bold=True)
ns_text = ns_font.render("NO SIGNAL", True, (180, 180, 180))
no_signal_surf.blit(ns_text, (IMAGE_W//2 - ns_text.get_width()//2, IMAGE_H//2 - ns_text.get_height()//2))
ns_sub = pygame.font.SysFont("Arial", 28).render("Power failure — restore electricity", True, (120, 120, 120))
no_signal_surf.blit(ns_sub, (IMAGE_W//2 - ns_sub.get_width()//2, IMAGE_H//2 + 50))

try:
    _ns_cam_raw = pygame.image.load("images/no_signal_cam.jpg").convert()
    no_signal_cam_surf = pygame.transform.scale(_ns_cam_raw, (IMAGE_W, IMAGE_H))
except:
    no_signal_cam_surf = no_signal_surf

# CCTV Variables
current_cam = "CAM 1"
cam_offset_x = 0
static_timer = 0
ghost_cctv_active = False
ghost_cctv_pos = None
ghost_cctv_state = None
ghost_from_pos = None
ghost_spawn_delay = 5000
game_start_time = pygame.time.get_ticks()

ghost_nodes = {
    None:                [(("CAM 1","far"),  1.0)],
    ("CAM 1","far"):     [(("CAM 2","near"),0.6),(("CAM 2","far"),0.1),(("CAM 4","far"),0.3)],
    ("CAM 2","far"):     [(("CAM 3","far"), 0.7),(("CAM 2","near"),0.2),(("CAM 5","far"),0.1)],
    ("CAM 2","near"):    [(("CAM 2","far"), 0.2),(("CAM 5","far"),0.8)],
    ("CAM 3","far"):     [(("CAM 2","far"), 0.1),(("CAM 7","far"),0.1),(("CAM 8","far"),0.8)],
    ("CAM 4","far"):     [(("CAM 1","far"), 0.4),(("CAM 2","far"),0.1),(("CAM 3","far"),0.5)],
    ("CAM 5","far"):     [(("CAM 6","far"), 0.7),(("CAM 7","far"),0.2),(("CAM 8","far"),0.1)],
    ("CAM 6","far"):     [(("CAM 6","near"),0.6),(("CAM 7","far"),0.3),(("CAM 8","far"),0.1)],
    ("CAM 6","near"):    [(("CAM 6","near"),1.0)],
    ("CAM 7","far"):     [(("CAM 6","near"),0.45),(("CAM 8","far"),0.45),(("CAM 9","far"),0.1)],
    ("CAM 8","far"):     [(("CAM 7","far"), 0.15),(("CAM 3","far"),0.05),(("CAM 9","far"),0.8)],
    ("CAM 9","far"):     [(("CAM 9","far"), 1.0)],
}

class CamButton:
    def __init__(self, name, x, y):
        self.name = name
        self.rect = pygame.Rect(x, y, 50, 30)
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
    def draw(self, surface, is_active):
        bg_color     = (0, 150, 0)   if is_active else (30,  30,  30)
        border_color = (0, 255, 0)   if is_active else (150,150,150)
        pygame.draw.rect(surface, bg_color,     self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 1)
        txt = self.font.render(self.name, True, (255,255,255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))

map_x, map_y = 320, 320
cctv_buttons = [
    CamButton("CAM 1", map_x+120, map_y+60),
    CamButton("CAM 2", map_x+130, map_y+110),
    CamButton("CAM 3", map_x+355, map_y+90),
    CamButton("CAM 4", map_x+405, map_y+40),
    CamButton("CAM 5", map_x+180, map_y+170),
    CamButton("CAM 6", map_x+180, map_y+250),
    CamButton("CAM 7", map_x+300, map_y+190),
    CamButton("CAM 8", map_x+340, map_y+130),
    CamButton("CAM 9", map_x+405, map_y+150),
]

# --- Load Assets ---
try:
    tileset   = pygame.image.load("assets/Tilesheets/roguelikeIndoor_transparent.png").convert_alpha()
    windowg0  = pygame.transform.scale(pygame.image.load("images/windowg0%.jpg"),   (SCREEN_W, SCREEN_H))
    windowg30 = pygame.transform.scale(pygame.image.load("images/windowg30%.jpg"),  (SCREEN_W, SCREEN_H))
    windowg70 = pygame.transform.scale(pygame.image.load("images/windowg70%.jpg"),  (SCREEN_W, SCREEN_H))
    windowg99 = pygame.transform.scale(pygame.image.load("images/windowg99%.jpg"),  (SCREEN_W, SCREEN_H))
    ghost_jump= pygame.transform.scale(pygame.image.load("images/gjump.jpg"),       (SCREEN_W, SCREEN_H))
    door1     = pygame.transform.scale(pygame.image.load("images/door.jpg"),        (SCREEN_W, SCREEN_H))
    door1g    = pygame.transform.scale(pygame.image.load("images/doorg.jpg"),       (SCREEN_W, SCREEN_H))
    door2     = pygame.transform.scale(pygame.image.load("images/d2.jpg"),          (SCREEN_W, SCREEN_H))
    door2g    = pygame.transform.scale(pygame.image.load("images/d2_g.jpg"),        (SCREEN_W, SCREEN_H))
except:
    print("Warning: Some assets not found!")
    windowg0 = windowg30 = windowg70 = windowg99 = ghost_jump = pygame.Surface((SCREEN_W, SCREEN_H))

def get_tile(col, row):
    rect  = pygame.Rect(col*(TILE_SIZE+1), row*(TILE_SIZE+1), TILE_SIZE, TILE_SIZE)
    image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    image.blit(tileset, (0,0), rect)
    return pygame.transform.scale(image, (DISPLAY_TILE, DISPLAY_TILE))

def reset():
    global ghost_active, ghost_cctv_active, breathing_playing, breathing_scream_playing, chasing_playing, ghost_from_pos
    ghost_active           = False
    ghost_cctv_active      = True
    ghost_from_pos         = None
    breathing_playing      = False
    breathing_scream_playing = False
    chasing_playing        = False
    chasing.stop(); breathing.stop(); breathing_scream.stop(); hit_sound.stop()


def reset_game():
    global game_time, window_progress, charge_level, door2_progress, max_reached_progress, click_power
    global ghost_cctv_pos, ghost_cctv_state, ghost_active, last_ghost_time, game_start_time
    global window_speed, ghost_cooldown, door_attack_cooldown, hour_intro_shown
    global is_blackout, next_blackout_time, blackout_timer
    global phone_call_count, phone_dialog_active, phone_dialog_lines, phone_dialog_index
    global phone_no_signal, phone_no_signal_timer

    game_time            = 0
    window_progress      = 0
    charge_level         = 50
    door2_progress       = 20
    max_reached_progress = door2_progress
    click_power          = 1.5
    ghost_cctv_pos       = "CAM 1"
    ghost_cctv_state     = "far"
    ghost_active         = False
    last_ghost_time      = pygame.time.get_ticks()
    game_start_time      = pygame.time.get_ticks()
    hour_intro_shown     = False

    config = hour_configs[current_hour]
    window_speed         = config["window_speed_base"]
    ghost_cooldown       = config["ghost_cooldown"]
    door_attack_cooldown = config["door_attack_cooldown"]

    is_blackout          = False
    blackout_timer       = 0
    if current_hour >= 2:
        _schedule_next_blackout()

    # Reset phone state
    phone_call_count     = {}
    phone_dialog_active  = False
    phone_dialog_lines   = []
    phone_dialog_index   = 0
    phone_no_signal      = False
    phone_no_signal_timer= 0


def _get_blackout_interval():
    intervals = {2:(60000,90000), 3:(45000,70000), 4:(30000,55000), 5:(20000,40000)}
    lo, hi = intervals.get(current_hour, (60000,90000))
    return random.randint(lo, hi)

def _schedule_next_blackout():
    global next_blackout_time
    next_blackout_time = pygame.time.get_ticks() + _get_blackout_interval()

def trigger_blackout():
    global is_blackout, blackout_timer, blackout_sound_playing
    is_blackout    = True
    blackout_timer = pygame.time.get_ticks()
    if blackout_sound is not None and not blackout_sound_playing:
        blackout_sound.play(-1)
        blackout_sound_playing = True

def end_blackout():
    global is_blackout, blackout_sound_playing
    is_blackout = False
    _schedule_next_blackout()
    if blackout_sound is not None:
        blackout_sound.stop()
    blackout_sound_playing = False


def weighted_choice(choices):
    global ghost_from_pos
    if ghost_from_pos is not None:
        choices = [(item,w) for item,w in choices if item[0] != ghost_from_pos]
    if not choices:
        choices = [(item,w) for item,w in ghost_nodes.get((ghost_cctv_pos, ghost_cctv_state), [])]
        if ghost_from_pos is not None:
            choices = [(item,w) for item,w in choices if item[0] != ghost_from_pos]
        if not choices:
            choices = [(item,w) for item,w in ghost_nodes.get((ghost_cctv_pos, ghost_cctv_state), [])]
    total = sum(w for _,w in choices)
    if total == 0:
        return random.choice(choices)[0] if choices else None
    r, upto = random.random()*total, 0
    for item, w in choices:
        if upto + w >= r:
            return item
        upto += w
    return choices[-1][0]


def draw_window_warning(progress):
    if 60 <= progress <= 80:
        wt, wc = "WARNING", (255,255,0)
    elif 81 <= progress < 100:
        wt, wc = "DANGER",  (255,0,0)
    elif progress >= 100:
        wt, wc = "ATTACK",  (255,0,0)
    else:
        return
    pygame.draw.rect(screen, (0,0,0),   (620,10,170,60))
    pygame.draw.rect(screen, wc,        (632,22,36,36))
    screen.blit(font_small.render(wt,              True, wc), (675,18))
    screen.blit(font_small.render(f"{int(progress)}%", True, wc), (675,42))


def get_time_string():
    total_hours     = (current_hour-1) + int(game_time//60)
    display_minutes = int(game_time % 60 // 10) * 10
    if display_minutes == 0:
        return f"{total_hours:02d}:00 AM"
    elif display_minutes == 60:
        return f"{total_hours+1} AM"
    else:
        return f"{total_hours:02d}:{display_minutes:02d} AM"


def load_level():
    global dots_grid, completed_paths, drawing_path, current_color
    dots_grid       = [[None]*6 for _ in range(6)]
    completed_paths = {}
    drawing_path    = []
    current_color   = None
    level_data = random.choice(LEVELS)
    for x1,y1,x2,y2,color in level_data:
        dots_grid[y1][x1] = color
        dots_grid[y2][x2] = color

def get_grid_pos(mouse_pos):
    gx = (mouse_pos[0] - GRID_X_OFFSET) // DOTS_CELL_SIZE
    gy = (mouse_pos[1] - GRID_Y_OFFSET) // DOTS_CELL_SIZE
    if 0 <= gx < 6 and 0 <= gy < 6:
        return gx, gy
    return None


# ─────────────────────────────────────────────
# PHONE HELPER FUNCTIONS
# ─────────────────────────────────────────────
def get_phone_dialog(hour, call_index):
    #คืน list of (speaker,line) สำหรับ hour/call_index ที่กำหนด
       #คืน None → แสดงข้อความ 'โทรไม่ติด'"""
    dialogues = PHONE_DIALOGUES.get(hour, [])
    if not dialogues:
        return None
    if call_index >= len(dialogues):
        # เกินจำนวน → ใช้อันสุดท้าย (repeat)
        return dialogues[-1]
    return dialogues[call_index]


def start_phone_call():
    global phone_dialog_active, phone_dialog_lines, phone_dialog_index
    global phone_call_count, phone_no_signal, phone_no_signal_timer

    count  = phone_call_count.get(current_hour, 0)
    dialog = get_phone_dialog(current_hour, count)
    phone_call_count[current_hour] = count + 1

    if dialog is None:
        phone_no_signal       = True
        phone_no_signal_timer = 120   # 2 วิ ที่ 60fps
        return

    phone_dialog_active = True
    phone_dialog_lines  = dialog
    phone_dialog_index  = 0


def advance_phone_dialog():
    global phone_dialog_active, phone_dialog_index
    phone_dialog_index += 1
    if phone_dialog_index >= len(phone_dialog_lines):
        phone_dialog_active = False
        phone_dialog_index  = 0


def render_phone_ui():
    #วาด popup โทรศัพท์ทับบนหน้า STATE_MAIN"""
    global phone_no_signal, phone_no_signal_timer

    # ── โทรไม่ติด ──
    if phone_no_signal:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        screen.blit(overlay, (0,0))

        box = pygame.Rect(200, 220, 400, 120)
        pygame.draw.rect(screen, (30,30,30),  box, border_radius=10)
        pygame.draw.rect(screen, (150,0,0),   box, 2, border_radius=10)

        t1 = font_small.render("I can't get through...",               True, (255,80,80))
        t2 = font_small.render("No signal or line busy", True, (180,180,180))
        screen.blit(t1, (box.centerx - t1.get_width()//2, box.y+25))
        screen.blit(t2, (box.centerx - t2.get_width()//2, box.y+65))

        phone_no_signal_timer -= 1
        if phone_no_signal_timer <= 0:
            phone_no_signal = False
        return

    # ── Dialog popup ──
    if not phone_dialog_active:
        return

    speaker, text = phone_dialog_lines[phone_dialog_index]

    if speaker == "police":
        name_color   = (100,200,255)
        name_label   = "Officer"
        box_color    = (10,20,40)
        border_color = (100,200,255)
    else:
        name_color   = (200,255,150)
        name_label   = "You"
        box_color    = (20,30,10)
        border_color = (150,220,100)

    box = pygame.Rect(60, SCREEN_H-180, SCREEN_W-120, 140)
    pygame.draw.rect(screen, box_color,    box, border_radius=8)
    pygame.draw.rect(screen, border_color, box, 2, border_radius=8)

    icon_surf = font_small.render("Tel", True, (200,200,200))
    screen.blit(icon_surf, (box.x+14, box.y+10))
    name_surf = font_small.render(name_label, True, name_color)
    screen.blit(name_surf, (box.x+50, box.y+12))

    # word-wrap อย่างง่าย
    words = text.split()
    lines_wrapped, cur = [], ""
    for w in words:
        test = (cur+" "+w).strip()
        if font_small.size(test)[0] < box.width-40:
            cur = test
        else:
            lines_wrapped.append(cur)
            cur = w
    if cur:
        lines_wrapped.append(cur)

    for i, ln in enumerate(lines_wrapped[:3]):
        ts = font_small.render(ln, True, (240,240,240))
        screen.blit(ts, (box.x+20, box.y+45+i*28))

    is_last   = phone_dialog_index >= len(phone_dialog_lines)-1
    hint_text = "Press [E] to Hang Up" if is_last else "Press [E] to Continue"
    hint_surf = font_small.render(hint_text, True, (120,120,120))
    screen.blit(hint_surf, (box.right - hint_surf.get_width()-14, box.bottom-22))

    total = len(phone_dialog_lines)
    for di in range(total):
        color = (200,200,200) if di == phone_dialog_index else (60,60,60)
        pygame.draw.circle(screen, color, (box.x+20+di*14, box.bottom-16), 4)


# --- Game State Constants ---
STATE_MAIN         = "main"
STATE_WINDOW       = "window"
STATE_DOOR         = "door"
STATE_DOOR2        = "door2"
STATE_COMPUTER     = "computer"
STATE_DOOR_IDLE    = "door_idle"
STATE_DOOR2_IDLE   = "door2_idle"
STATE_JUMPSCARE    = "jumpscare"
STATE_MENU         = "menu"
STATE_GAME_OVER    = "game_over"
STATE_ELECTRIC_BOX = "electric_box"

input_state       = {"space": False}
current_menu_page = "main"

button_new_game  = pygame.Rect(300, 250, 200, 50)
button_continue  = pygame.Rect(300, 320, 200, 50)
button_hour_menu = {}


def set_state(new_state):
    global game_state
    game_state = new_state


def process_ghost_cctv_move(current_time):
    global ghost_cctv_pos, ghost_cctv_state, ghost_from_pos, static_timer
    global ghost_active, ghost_target, ghost_spawn_time, last_door_attack_time, last_ghost_time

    if current_time - last_ghost_time < ghost_cooldown:
        return
    if game_state in [STATE_DOOR, STATE_DOOR2]:
        return
    if ghost_active:
        return

    if ghost_cctv_pos is None:
        if current_time - game_start_time > ghost_spawn_delay:
            ghost_cctv_pos   = "CAM 1"
            ghost_cctv_state = "far"
            ghost_from_pos   = None
            static_timer     = 20
        return

    old_pos = ghost_cctv_pos
    move    = False

    if ghost_cctv_pos == "CAM 6" and ghost_cctv_state == "near":
        if current_time - last_door_attack_time > door_attack_cooldown:
            ghost_active          = True
            ghost_target          = "door"
            ghost_spawn_time      = current_time
            last_door_attack_time = current_time
            door_opening.play()

    elif ghost_cctv_pos == "CAM 6" and ghost_cctv_state == "far":
        ghost_cctv_pos, ghost_cctv_state = weighted_choice(ghost_nodes[(ghost_cctv_pos, ghost_cctv_state)])
        move = True

    elif ghost_cctv_pos == "CAM 9":
        if current_time - last_door_attack_time > door_attack_cooldown:
            ghost_active          = True
            ghost_target          = "door2"
            ghost_spawn_time      = current_time
            last_door_attack_time = current_time
            door_knocking.stop()
            door_opening.play()

    else:
        ghost_cctv_pos, ghost_cctv_state = weighted_choice(ghost_nodes[(ghost_cctv_pos, ghost_cctv_state)])
        move = True

    if move:
        ghost_from_pos = old_pos
        static_timer   = 15


def process_keydown(event, current_time):
    global input_state, ghost_active, ghost_target, game_state, charge_level, last_ghost_time, door2_progress
    global current_cam, static_timer, hour_intro_shown, current_menu_page

    if event.key == pygame.K_SPACE:
        input_state["space"] = True

    # Skip intro message
    if game_state == STATE_MAIN and not hour_intro_shown:
        hour_intro_shown = True
        return True

    # ── Phone dialog intercept — กิน E ก่อน interaction อื่นๆ ──
    if game_state == STATE_MAIN and (phone_dialog_active or phone_no_signal):
        if event.key == pygame.K_e and phone_dialog_active:
            advance_phone_dialog()
        return True

    if event.key == pygame.K_e and game_state == STATE_MAIN:
        if near_window:
            footstep.stop()
            set_state(STATE_WINDOW)

        elif near_door:
            footstep.stop()
            if ghost_active and ghost_target == "door":
                set_state(STATE_DOOR)
                charge_level = 50
                ghost_active = False
                last_ghost_time = current_time
            else:
                set_state(STATE_DOOR_IDLE)

        elif near_door2:
            footstep.stop()
            if ghost_active and ghost_target == "door2":
                set_state(STATE_DOOR2)
                door2_progress = 40
                ghost_active   = False
                last_ghost_time = current_time
            else:
                set_state(STATE_DOOR2_IDLE)

        elif near_computer:
            set_state(STATE_COMPUTER)
            static_timer = 20
            footstep.stop()
            open_camera_sound.play()
            ambient.play(-1)

        elif near_electric_box and current_hour >= 2:
            set_state(STATE_ELECTRIC_BOX)
            if is_blackout:
                load_level()
            footstep.stop()

        elif near_phone:
            footstep.stop()
            start_phone_call()

    if event.key == pygame.K_q and game_state in [STATE_DOOR2_IDLE, STATE_DOOR_IDLE, STATE_COMPUTER, STATE_WINDOW, STATE_ELECTRIC_BOX]:
        set_state(STATE_MAIN)
        ambient.stop()

    if game_state == STATE_GAME_OVER:
        if event.key == pygame.K_r:
            current_menu_page = "main"
            set_state(STATE_MENU)
            return True
        elif event.key == pygame.K_q:
            return False

    return True


def process_mouse_down(event):
    global current_cam, static_timer, current_hour, current_menu_page, max_unlocked_hour
    if game_state == STATE_COMPUTER:
        for btn in cctv_buttons:
            if btn.rect.collidepoint(event.pos):
                current_cam  = btn.name
                static_timer = 20
                camera_sound.play()
                footstep.stop()
    elif game_state == STATE_MENU:
        if current_menu_page == "main":
            if button_new_game.collidepoint(event.pos):
                current_menu_page = "hour_select"
            elif button_continue.collidepoint(event.pos) and max_unlocked_hour > 1:
                current_hour = max_unlocked_hour
                reset_game()
                set_state(STATE_MAIN)
        elif current_menu_page == "hour_select":
            back_btn = pygame.Rect(350, 450, 100, 40)
            if back_btn.collidepoint(event.pos):
                current_menu_page = "main"
            else:
                for hour_num, btn in button_hour_menu.items():
                    if btn.collidepoint(event.pos):
                        current_hour      = hour_num
                        current_menu_page = "main"
                        reset_game()
                        set_state(STATE_MAIN)
                        break


def handle_event(event, current_time):
    if event.type == pygame.QUIT:
        return False
    if event.type == GHOST_CCTV_MOVE:
        process_ghost_cctv_move(current_time)
    elif event.type == pygame.KEYDOWN:
        if not process_keydown(event, current_time):
            return False
    elif event.type == pygame.MOUSEBUTTONDOWN:
        process_mouse_down(event)
    return True


def update_window_progress(dt):
    global window_progress, jumpscare_timer
    current_speed = window_speed * 10
    if game_state in [STATE_DOOR, STATE_DOOR2]:
        current_speed = window_speed * 5
    if game_state != STATE_JUMPSCARE:
        window_progress += current_speed * dt
        if window_progress >= 100:
            window_progress = 100
            set_state(STATE_JUMPSCARE)
            jumpscare_timer = 90
            return True
    return False


def update_ghost_attack_timeout(current_time):
    global jumpscare_timer
    if ghost_active and game_state in [STATE_MAIN, STATE_DOOR2_IDLE, STATE_DOOR_IDLE, STATE_COMPUTER, STATE_WINDOW]:
        if current_time - ghost_spawn_time > 20000:
            set_state(STATE_JUMPSCARE)
            jumpscare_timer = 90
            reset()


def update_main(dt):
    global player_x, player_y, footstep_playing
    global near_window, near_door, near_door2, near_computer, near_electric_box, near_phone

    moving     = False
    keys       = pygame.key.get_pressed()
    new_x, new_y = player_x, player_y

    if keys[pygame.K_a]: new_x -= player_speed; moving = True
    if keys[pygame.K_d]: new_x += player_speed; moving = True
    if keys[pygame.K_w]: new_y -= player_speed; moving = True
    if keys[pygame.K_s]: new_y += player_speed; moving = True

    p_rect = pygame.Rect(new_x, player_y, player_size, player_size)
    if any(p_rect.colliderect(w) for w in wall_rects): new_x = player_x

    p_rect = pygame.Rect(new_x, new_y, player_size, player_size)
    if any(p_rect.colliderect(w) for w in wall_rects): new_y = player_y

    player_x, player_y = new_x, new_y

    if moving and not footstep_playing:
        footstep.play(-1); footstep_playing = True
    elif not moving and footstep_playing:
        footstep.stop();   footstep_playing = False

    p_rect = pygame.Rect(player_x, player_y, player_size, player_size)
    near_window       = any(p_rect.inflate(20,20).colliderect(i) for i in window_rects)
    near_door         = any(p_rect.inflate(20,20).colliderect(i) for i in door_rects)
    near_door2        = any(p_rect.inflate(20,20).colliderect(i) for i in door2_rects)
    near_computer     = any(p_rect.inflate(20,20).colliderect(i) for i in computer_rects)
    near_electric_box = any(p_rect.inflate(20,20).colliderect(i) for i in electric_box_rects)
    near_phone        = any(p_rect.inflate(20,20).colliderect(i) for i in phone_rects)


def update_window_state():
    global window_progress, button_color
    mouse_click = pygame.mouse.get_pressed()
    if button_rect.collidepoint(pygame.mouse.get_pos()) and mouse_click[0]:
        window_progress -= 0.2
        button_color = (100,0,0)
    else:
        button_color = (200,0,0)
    window_progress = max(0, window_progress)
    if window_progress >= 100:
        window_progress = 100
        set_state(STATE_JUMPSCARE)


def update_door_state(current_time):
    global charge_level, last_pull_time, pull_force_x, pull_force_y, shake_timer, chasing_playing
    global ghost_active, last_ghost_time, ghost_cctv_pos, ghost_cctv_state, jumpscare_timer

    if not chasing_playing:
        chasing.play(-1); chasing_playing = True

    if current_time - last_pull_time > 2000:
        angle         = random.uniform(0, 2*math.pi)
        strength      = random.uniform(10, 25)
        pull_force_x  = math.cos(angle)*strength
        pull_force_y  = math.sin(angle)*strength
        last_pull_time= current_time
        shake_timer   = 15
        hit_sound.play()

    mouse_x, mouse_y = pygame.mouse.get_pos()
    pull_force_x *= 0.95; pull_force_y *= 0.95
    new_mx = mouse_x + pull_force_x
    new_my = mouse_y + pull_force_y
    pygame.mouse.set_pos([new_mx, new_my])

    dist = math.hypot(new_mx-CIRCLE_POS[0], new_my-CIRCLE_POS[1])
    charge_level += 0.3 if dist < CIRCLE_RADIUS else -0.6

    if charge_level >= 100:
        set_state(STATE_MAIN)
        last_ghost_time  = current_time
        ghost_cctv_pos   = "CAM 1"
        ghost_cctv_state = "far"
        reset()
    elif charge_level <= 0:
        set_state(STATE_JUMPSCARE)
        jumpscare_timer = 90


def update_door2_state():
    global door2_progress, max_reached_progress, click_power, chasing_playing
    global breathing_playing, breathing_scream_playing, shake_timer
    global jumpscare_timer, last_ghost_time, ghost_cctv_pos, ghost_cctv_state

    if not chasing_playing:
        chasing.play(-1); chasing_playing = True
    if not breathing_playing and not breathing_scream_playing:
        breathing.play(-1); breathing_playing = True
    if door2_progress > 70 and not breathing_scream_playing:
        breathing.stop(); breathing_playing = False
        breathing_scream.play(-1); breathing_scream_playing = True

    if door2_progress > max_reached_progress:
        max_reached_progress = door2_progress

    base_speed      = 0.15
    target_speed    = base_speed + (max_reached_progress*0.01)
    if door2_progress < max_reached_progress:
        target_speed *= 0.5; click_power += 0.01
    door2_progress += min(1, target_speed)

    bonus_power = (door2_progress/100)*2.0
    if input_state["space"]:
        door2_progress -= (click_power + bonus_power)
        shake_timer = 5

    door2_progress = max(0, min(100, door2_progress))
    if door2_progress < max_reached_progress - 20:
        max_reached_progress = door2_progress

    if door2_progress >= 100:
        set_state(STATE_JUMPSCARE); jumpscare_timer = 90
    elif door2_progress <= 0:
        set_state(STATE_MAIN)
        door2_progress       = 20
        max_reached_progress = door2_progress
        click_power          = 1.5
        last_ghost_time      = pygame.time.get_ticks()
        ghost_cctv_pos       = "CAM 1"
        ghost_cctv_state     = "far"
        reset()


def update_computer_state():
    global cam_offset_x
    cam_offset_x = max(SCREEN_W-IMAGE_W, min(0, cam_offset_x))
    mx = pygame.mouse.get_pos()[0]
    if mx < 100 and cam_offset_x < 0:              cam_offset_x += 7
    elif mx > SCREEN_W-100 and cam_offset_x > (SCREEN_W-IMAGE_W): cam_offset_x -= 7


def update_electric_box_state():
    global drawing_path, current_color, completed_paths, is_finishing_stroke
    if not is_blackout:
        return

    mouse_pos     = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    grid_pos      = get_grid_pos(mouse_pos)

    if mouse_pressed:
        if is_finishing_stroke:
            return
        if grid_pos:
            gx, gy = grid_pos
            if not drawing_path:
                if dots_grid[gy][gx] is not None:
                    current_color = dots_grid[gy][gx]
                    if current_color in completed_paths:
                        del completed_paths[current_color]
                    drawing_path = [(gx,gy)]
            elif grid_pos != drawing_path[-1]:
                lx, ly = drawing_path[-1]
                if abs(gx-lx)+abs(gy-ly) == 1:
                    is_obstructed = any(grid_pos in path for path in completed_paths.values())
                    if not is_obstructed:
                        if dots_grid[gy][gx] is not None:
                            if dots_grid[gy][gx] == current_color and grid_pos != drawing_path[0]:
                                drawing_path.append(grid_pos)
                                completed_paths[current_color] = list(drawing_path)
                                drawing_path = []; current_color = None
                                is_finishing_stroke = True
                                if len(completed_paths) == 6:
                                    end_blackout(); set_state(STATE_MAIN)
                        else:
                            if grid_pos not in drawing_path:
                                drawing_path.append(grid_pos)
    else:
        is_finishing_stroke = False
        drawing_path        = []
        current_color       = None


def update_jumpscare_state():
    global jumpscare_timer, window_progress, charge_level, ghost_cctv_pos, ghost_cctv_state, player_x, player_y
    if jumpscare_timer == 90:
        jumpscare.play()
    jumpscare_timer -= 1
    if jumpscare_timer <= 0:
        set_state(STATE_MENU)
        window_progress  = 50
        charge_level     = 50
        ghost_cctv_pos   = "None"
        ghost_cctv_state = "far"
        player_x, player_y = 400, 400
        reset(); reset_game()


def update_state(dt, current_time):
    global game_time, game_won, max_unlocked_hour
    if update_window_progress(dt):
        return
    update_ghost_attack_timeout(current_time)
    if game_state not in [STATE_MENU, STATE_GAME_OVER]:
        game_time += time_speed * dt / 60
        if game_time >= hour_duration:
            game_won = True
            if current_hour < 5:
                max_unlocked_hour = current_hour + 1
            set_state(STATE_GAME_OVER)
        if current_hour >= 2 and not is_blackout and next_blackout_time > 0:
            if current_time >= next_blackout_time:
                trigger_blackout()
    if   game_state == STATE_MAIN:         update_main(dt)
    elif game_state == STATE_WINDOW:       update_window_state()
    elif game_state == STATE_DOOR:         update_door_state(current_time)
    elif game_state == STATE_DOOR2:        update_door2_state()
    elif game_state == STATE_COMPUTER:     update_computer_state()
    elif game_state == STATE_ELECTRIC_BOX: update_electric_box_state()
    elif game_state == STATE_JUMPSCARE:    update_jumpscare_state()


# ─────────────────────────────────────────────
# RENDER FUNCTIONS
# ─────────────────────────────────────────────
def render_main_state():
    for r, row in enumerate(map_data):
        for c, val in enumerate(row):
            if val in tiles:
                screen.blit(tiles[val], (c*DISPLAY_TILE, r*DISPLAY_TILE))
    for r, row in enumerate(decor_map):
        for c, val in enumerate(row):
            if val in walls_img:
                screen.blit(walls_img[val], (c*DISPLAY_TILE, r*DISPLAY_TILE))

    pygame.draw.rect(screen, (0,200,255), (player_x, player_y, player_size, player_size))

    # Blackout darkness
    if is_blackout:
        LIGHT_RADIUS = 110
        cx = player_x + player_size//2
        cy = player_y + player_size//2
        dark = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dark.fill((0,0,0,240))
        for r in range(LIGHT_RADIUS, 0, -1):
            alpha = int(240*(r/LIGHT_RADIUS)**2)
            pygame.draw.circle(dark, (0,0,0,alpha), (cx,cy), r)
        screen.blit(dark, (0,0))
        bo_txt = font_small.render("BLACKOUT — Fix the electric box!", True, (255,180,0))
        screen.blit(bo_txt, (SCREEN_W//2 - bo_txt.get_width()//2, 10))

    # Interaction prompts
    if near_window:
        txt = font_small.render("Press [E] to Close Window", True, (255,255,0))
        screen.blit(txt, (player_x-50, player_y-40))
    elif near_door:
        txt = font_small.render("Press [E] to Hold Door", True, (255,255,0))
        screen.blit(txt, (player_x-50, player_y-40))
    elif near_door2:
        txt = font_small.render("Press [E] to Hold Door", True, (255,255,0))
        screen.blit(txt, (player_x-50, player_y-40))
    elif near_computer:
        txt = font_small.render("Press [E] to Use Computer", True, (255,255,0))
        screen.blit(txt, (player_x-50, player_y-40))
    elif near_electric_box and current_hour >= 2:
        if is_blackout:
            txt = font_small.render("Press [E] to Fix Power", True, (255,200,0))
        else:
            txt = font_small.render("An electric box... nothing to do here", True, (180,180,180))
        screen.blit(txt, (player_x-80, player_y-40))
    elif near_phone:
        txt = font_small.render("Press [E] to Use Phone", True, (180,220,255))
        screen.blit(txt, (player_x-50, player_y-40))

    if ghost_active:
        screen.blit(font_small.render(f"GHOST: {ghost_target}", True, (255,0,0)), (10,10))
    screen.blit(font_small.render(get_time_string(), True, (255,255,255)), (10,30))
    draw_window_warning(window_progress)

    # Phone UI overlay (วาดก่อน hour intro เพื่อไม่ถูกบัง)
    render_phone_ui()

    # Hour Intro Message
    if not hour_intro_shown:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.fill((0,0,0)); overlay.set_alpha(200)
        screen.blit(overlay, (0,0))
        intro_surf = font_large.render(hour_configs[current_hour]["intro_message"], True, (255,200,100))
        screen.blit(intro_surf, (SCREEN_W//2 - intro_surf.get_width()//2, 250))
        press_text = font_small.render("Press any key to continue...", True, (200,200,200))
        screen.blit(press_text, (SCREEN_W//2 - press_text.get_width()//2, 400))


def render_window_state():
    if   window_progress < 30: screen.blit(windowg0,  (0,0))
    elif window_progress < 60: screen.blit(windowg30, (0,0))
    elif window_progress < 90: screen.blit(windowg70, (0,0))
    else:                      screen.blit(windowg99, (0,0))

    bar_color = (255,200,0)
    if 75 <= window_progress <= 90:   wt,wc,bar_color = "WARNING",(255,255,0),(255,180,0)
    elif 91 <= window_progress < 100: wt,wc,bar_color = "DANGER", (255,0,0), (255,120,0)
    elif window_progress >= 100:      wt,wc,bar_color = "ATTACK", (255,0,0), (255,0,0)
    else:                             wt,wc = None, None

    pygame.draw.rect(screen, (50,50,50), (200,530,400,25))
    pygame.draw.rect(screen, bar_color,  (200,530,int(window_progress*4),25))
    if wt:
        pygame.draw.rect(screen, (0,0,0), (620,520,170,60))
        pygame.draw.rect(screen, wc,      (632,532,36,36))
        screen.blit(font_small.render(wt,              True, wc), (675,528))
        screen.blit(font_small.render(f"{int(window_progress)}%", True, wc), (675,552))
    pygame.draw.rect(screen, button_color, button_rect)
    text_surf = font.render("HOLD", True, text_color)
    screen.blit(text_surf, text_surf.get_rect(center=button_rect.center))
    screen.blit(font_small.render("HOLD THE BUTTON TO CLOSE!", True, (255,255,255)), (250,500))


def render_door_state():
    global shake_timer
    img = door1g if charge_level <= 70 else door1
    sx = random.randint(-10,10) if shake_timer > 0 else 0
    sy = random.randint(-10,10) if shake_timer > 0 else 0
    if shake_timer > 0: shake_timer -= 1
    screen.blit(img, (sx,sy))
    pygame.draw.circle(screen, (255,0,0), CIRCLE_POS, CIRCLE_RADIUS, 3)
    mx, my = pygame.mouse.get_pos()
    pygame.draw.circle(screen, (255,50,50), (int(mx),int(my)), 5)
    pygame.draw.rect(screen, (50,50,50),  (200,530,400,25))
    pygame.draw.rect(screen, (0,200,0),   (200,530,int(charge_level*4),25))
    screen.blit(font_small.render("KEEP CURSOR IN CIRCLE!", True, (255,255,255)), (250,500))


def render_door2_state():
    global shake_timer
    img = door2 if door2_progress < 70 else door2g
    sx = random.randint(-7,7) if shake_timer > 0 else 0
    sy = random.randint(-7,7) if shake_timer > 0 else 0
    if shake_timer > 0: shake_timer -= 1
    screen.blit(img, (sx,sy))
    pygame.draw.rect(screen, (50,50,50),  (200,530,400,25))
    pygame.draw.rect(screen, (200,0,0),   (200,530,int(door2_progress*4),25))
    screen.blit(font_small.render("CLICK RAPIDLY TO HOLD THE WINDOW!", True, (255,255,255)), (230,500))


def render_computer_state():
    global static_timer
    if is_blackout:
        screen.blit(no_signal_cam_surf, (0,0))
        scanline = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 3):
            pygame.draw.line(scanline, (0,0,0,30), (0,y), (SCREEN_W,y))
        screen.blit(scanline, (0,0))
        screen.blit(font_small.render(f"LIVE: {current_cam}", True, (200,0,0)),   (20,20))
        screen.blit(font_small.render("Press [Q] to Exit",    True, (255,255,255)),(20,SCREEN_H-40))
        bo_warn = font_small.render("Power is out — find the electric box!", True, (255,180,0))
        screen.blit(bo_warn, (SCREEN_W//2 - bo_warn.get_width()//2, SCREEN_H//2+100))
        draw_window_warning(window_progress)
        screen.blit(map_img, (map_x,map_y))
        for btn in cctv_buttons: btn.draw(screen, btn.name == current_cam)
        return

    if ghost_active:
        state = "empty"
    elif current_cam == ghost_cctv_pos:
        state = "ghost2" if ghost_cctv_state == "near" and "ghost2" in cameras[current_cam] else "ghost"
    else:
        state = "empty"
    screen.blit(cameras[current_cam][state], (cam_offset_x,0))
    scanline = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)
    for y in range(0, SCREEN_H, 3):
        pygame.draw.line(scanline, (255,255,255,20), (0,y), (SCREEN_W,y))
    screen.blit(scanline, (0,0))
    screen.blit(noise_img, (0, random.randint(-2,2)))
    if static_timer > 0:
        for _ in range(200):
            nx,ny = random.randint(0,SCREEN_W), random.randint(0,SCREEN_H)
            nc = random.randint(150,255)
            pygame.draw.rect(screen, (nc,nc,nc), (nx,ny,3,3))
            static_timer -= 1
    screen.blit(font_small.render(f"LIVE: {current_cam}", True, (255,0,0)),    (20,20))
    screen.blit(font_small.render("Press [Q] to Exit",    True, (255,255,255)),(20,SCREEN_H-40))
    draw_window_warning(window_progress)
    screen.blit(map_img, (map_x,map_y))
    for btn in cctv_buttons: btn.draw(screen, btn.name == current_cam)


def render_idle_state(image):
    screen.blit(image, (0,0))
    screen.blit(font_small.render("Nothing here... (Q to exit)", True, (255,255,255)), (300,500))
    draw_window_warning(window_progress)


def render_electric_box_state():
    if not is_blackout:
        screen.fill((20,20,20))
        if electric_box_idle_img is not None:
            screen.blit(electric_box_idle_img, (0,0))
        else:
            screen.fill((25,25,30))
            box_rect = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2-120, 200, 200)
            pygame.draw.rect(screen, (60,60,70),   box_rect)
            pygame.draw.rect(screen, (100,100,110),box_rect, 3)
            bolt_font = pygame.font.SysFont("Arial", 80, bold=True)
            bolt = bolt_font.render("!", True, (180,180,100))
            screen.blit(bolt, (SCREEN_W//2 - bolt.get_width()//2, SCREEN_H//2-80))
        screen.blit(font_small.render("An electric box... nothing to do here", True, (200,200,200)),
                    (SCREEN_W//2 - font_small.size("An electric box... nothing to do here")[0]//2, SCREEN_H-100))
        screen.blit(font_small.render("Press [Q] to Exit", True, (160,160,160)),
                    (SCREEN_W//2 - font_small.size("Press [Q] to Exit")[0]//2, SCREEN_H-60))
        pygame.display.flip(); return

    screen.fill((25,25,25))
    title = font_large.render("RESTORE POWER", True, (255,215,0))
    screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 25))

    for r in range(DOTS_GRID_SIZE):
        for c in range(DOTS_GRID_SIZE):
            rect = pygame.Rect(GRID_X_OFFSET+c*DOTS_CELL_SIZE, GRID_Y_OFFSET+r*DOTS_CELL_SIZE, DOTS_CELL_SIZE, DOTS_CELL_SIZE)
            pygame.draw.rect(screen, (50,50,50), rect, 1)

    for color, path in completed_paths.items():
        if len(path) > 1:
            pts = [(GRID_X_OFFSET+p[0]*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2,
                    GRID_Y_OFFSET+p[1]*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2) for p in path]
            pygame.draw.lines(screen, color, False, pts, 15)

    if len(drawing_path) > 1:
        pts = [(GRID_X_OFFSET+p[0]*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2,
                GRID_Y_OFFSET+p[1]*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2) for p in drawing_path]
        pygame.draw.lines(screen, current_color, False, pts, 15)

    if len(dots_grid) == 6 and all(len(row)==6 for row in dots_grid):
        for r in range(6):
            for c in range(6):
                if dots_grid[r][c]:
                    center = (GRID_X_OFFSET+c*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2,
                              GRID_Y_OFFSET+r*DOTS_CELL_SIZE+DOTS_CELL_SIZE//2)
                    pygame.draw.circle(screen, dots_grid[r][c], center, 20)
                    pygame.draw.circle(screen, (255,255,255),   center, 20, 2)

    info = font_small.render(f"Completed: {len(completed_paths)}/6", True, (200,200,200))
    screen.blit(info, (SCREEN_W//2 - info.get_width()//2, 520))
    pygame.display.flip()


def render_menu():
    global button_hour_menu
    screen.fill((0,0,0))
    title = font_large.render("The Intruder", True, (255,255,255))
    screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))

    if current_menu_page == "main":
        subtitle = font.render("Main Menu", True, (200,200,200))
        screen.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 150))
        pygame.draw.rect(screen, (100,150,100), button_new_game)
        t = font.render("New Game", True, (255,255,255))
        screen.blit(t, (button_new_game.centerx-t.get_width()//2, button_new_game.centery-t.get_height()//2))
        if max_unlocked_hour > 1:
            pygame.draw.rect(screen, (100,100,150), button_continue)
            t = font.render(f"Continue (Hour {max_unlocked_hour})", True, (255,255,255))
        else:
            pygame.draw.rect(screen, (50,50,50), button_continue)
            t = font.render("Continue (Locked)", True, (100,100,100))
        screen.blit(t, (button_continue.centerx-t.get_width()//2, button_continue.centery-t.get_height()//2))

    elif current_menu_page == "hour_select":
        subtitle = font.render("Select Hour", True, (200,200,200))
        screen.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 150))
        button_hour_menu = {}
        for hour_num in range(1,6):
            btn = pygame.Rect(200+(hour_num-1)*120, 300, 100, 50)
            button_hour_menu[hour_num] = btn
            is_unlocked = hour_num <= max_unlocked_hour
            pygame.draw.rect(screen, (100,150,100) if is_unlocked else (50,50,50), btn)
            t = font_small.render(f"Hour {hour_num}", True, (255,255,255) if is_unlocked else (100,100,100))
            screen.blit(t, (btn.centerx-t.get_width()//2, btn.centery-t.get_height()//2))
        back_btn = pygame.Rect(350, 450, 100, 40)
        pygame.draw.rect(screen, (150,100,100), back_btn)
        t = font_small.render("Back", True, (255,255,255))
        screen.blit(t, (back_btn.centerx-t.get_width()//2, back_btn.centery-t.get_height()//2))


def render_game_over():
    screen.fill((0,0,0))
    if not hasattr(render_game_over, 'stopped'):
        ambient.stop(); render_game_over.stopped = True
    if game_won:
        text     = font_large.render(f"Hour {current_hour} Complete!", True, (0,255,0))
        subtext2 = font_small.render(f"Hour {current_hour+1} Unlocked!" if current_hour < 5 else "All Hours Complete!", True, (100,255,100) if current_hour < 5 else (255,200,0))
    else:
        text     = font_large.render("Game Over", True, (255,0,0))
        subtext2 = font_small.render("Try Again", True, (200,100,100))
    screen.blit(text,     (SCREEN_W//2-text.get_width()//2,     200))
    screen.blit(subtext2, (SCREEN_W//2-subtext2.get_width()//2, 300))
    subtext = font.render("Press R to Menu or Q to Quit", True, (255,255,255))
    screen.blit(subtext,  (SCREEN_W//2-subtext.get_width()//2,  400))


def render_jumpscare_state():
    screen.blit(ghost_jump, (0,0))


def render_state():
    if   game_state == STATE_MAIN:         render_main_state()
    elif game_state == STATE_WINDOW:       render_window_state()
    elif game_state == STATE_DOOR:         render_door_state()
    elif game_state == STATE_DOOR2:        render_door2_state()
    elif game_state == STATE_COMPUTER:     render_computer_state()
    elif game_state == STATE_ELECTRIC_BOX: render_electric_box_state()
    elif game_state == STATE_DOOR2_IDLE:   render_idle_state(door2)
    elif game_state == STATE_DOOR_IDLE:    render_idle_state(door1)
    elif game_state == STATE_JUMPSCARE:    render_jumpscare_state()
    elif game_state == STATE_MENU:         render_menu()
    elif game_state == STATE_GAME_OVER:    render_game_over()


# ─────────────────────────────────────────────
# MAP DATA
# ─────────────────────────────────────────────
map_data = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# tile 7 = โทรศัพท์บ้าน วางที่ row=8, col=18 (กลางห้องด้านบนขวา)
decor_map = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,6,0,0,0,3,0,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0,1,0,0,0],  # ← tile 7 = โทรศัพท์
    [0,0,1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,5,0,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

tiles     = {1: get_tile(24, 0)}
walls_img = {
    1: get_tile(5,  0),
    2: get_tile(24, 4),
    3: get_tile(24, 4),
    4: get_tile(24, 4),
    5: get_tile(24, 4),
    6: get_tile(24, 4),
    7: get_tile(24, 4),   # โทรศัพท์บ้าน — เปลี่ยน tile ได้ทีหลัง
}

# --- Game Variables ---
player_size  = 30
player_x, player_y = 400, 400
player_speed = 3
game_state   = STATE_MENU
window_progress = 0
window_speed    = 0.2
door2_progress  = 40
door2_speed     = 0.2
click_power     = 1.5
jumpscare_timer = 0
shake_timer     = 0
near_interact   = False
near_window     = False
near_door       = False
near_door2      = False
near_computer   = False
near_electric_box = False
near_phone      = False   # ← ใหม่

# Connect the Dots Variables
DOTS_COLORS       = [(255,0,0),(0,255,0),(0,0,255),(255,255,0)]
dots_grid         = [[None]*6 for _ in range(6)]
current_selection = None
drawing_path      = []
completed_matches = []
max_reached_progress = window_progress
last_pull_time    = 0
pull_force_x      = 0
pull_force_y      = 0
charge_level      = 0
ghost_active      = False
ghost_target      = None
ghost_spawn_time  = 0
ghost_cooldown    = 10000
last_ghost_time   = 0
last_door_attack_time = 0
door_attack_cooldown  = 10000
last_attack_cam   = None
last_knock_time   = 0
chasing_playing   = False
breathing_playing = False
breathing_scream_playing = False
footstep_playing  = False
ambient_playing   = False
button_rect  = pygame.Rect(SCREEN_W//2-60, 440, 100, 50)
button_color = (200,0,0)
text_color   = (255,255,255)
font         = pygame.font.SysFont("Arial", 24)

# Phone Variables ← ใหม่
phone_rects          = []
phone_call_count     = {}
phone_dialog_active  = False
phone_dialog_lines   = []
phone_dialog_index   = 0
phone_no_signal      = False
phone_no_signal_timer= 0

# Pre-calculate Rects
wall_rects        = []
window_rects      = []
door_rects        = []
door2_rects       = []
computer_rects    = []
electric_box_rects= []
phone_rects       = []   # ← ใหม่

for r, row in enumerate(decor_map):
    for c, val in enumerate(row):
        rect = pygame.Rect(c*DISPLAY_TILE, r*DISPLAY_TILE, DISPLAY_TILE, DISPLAY_TILE)
        if val == 1: wall_rects.append(rect)
        if val == 5: computer_rects.append(rect)
        if val == 4: window_rects.append(rect)
        if val == 2: door_rects.append(rect)
        if val == 3: door2_rects.append(rect)
        if val == 6: electric_box_rects.append(rect)
        if val == 7: phone_rects.append(rect)   # ← ใหม่

# Custom Events
GHOST_CCTV_MOVE = pygame.USEREVENT + 1
pygame.time.set_timer(GHOST_CCTV_MOVE, 7000)

# Electric box idle image
try:
    electric_box_idle_img = pygame.transform.scale(
        pygame.image.load("images/electric_box_idle.jpg").convert(), (SCREEN_W, SCREEN_H))
except:
    electric_box_idle_img = None

# --- Main Loop ---
game_running = True
while game_running:
    screen.fill((0,0,0))
    current_time = pygame.time.get_ticks()
    dt = clock.tick(60) / 1000
    input_state["space"] = False

    for event in pygame.event.get():
        if not handle_event(event, current_time):
            game_running = False
            break

    update_state(dt, current_time)
    render_state()
    pygame.display.flip()

pygame.quit()
