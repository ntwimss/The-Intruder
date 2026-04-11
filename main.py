import pygame
import math 
import random
import sys

pygame.init()

# --- Config ---
SCREEN_W, SCREEN_H = 800, 600
IMAGE_W, IMAGE_H = 1000, 600 # ขนาดรูป CCTV
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
HOLD_TIME_GOAL = 10  # 10 วินาที
pull_force_x = 0
pull_force_y = 0
charge_level = 50    # เริ่มที่ครึ่งหลอด
last_pull_time = 0
map_img = pygame.image.load("images/cam_roadmap-removebg-preview.png").convert_alpha()
map_img = pygame.transform.scale(map_img, (500, 300))
noise_img = pygame.image.load("images/noise-bg.jpg").convert_alpha()
noise_img = pygame.transform.scale(noise_img, (800,600))
noise_img.set_alpha(40)

#sound
pygame.mixer.init()
hit_sound = pygame.mixer.Sound("sounds/door-slamming-sound-effect-no-repeats-or-silence-2016.mp3")
door_knocking = pygame.mixer.Sound("sounds/door-knocking.mp3")
door_opening = pygame.mixer.Sound("sounds/fnaf-4-door-opening.mp3")
window_opening = pygame.mixer.Sound("sounds/door_EJ1ESwu.mp3")
camera_sound = pygame.mixer.Sound("sounds/fnaf2-camera.mp3")
open_camera_sound = pygame.mixer.Sound("sounds/fnaf-open-camera-sound.mp3")
chasing = pygame.mixer.Sound("sounds/chasing.mp3")
breathing = pygame.mixer.Sound("sounds/outofbreath.mp3")
breathing_scream = pygame.mixer.Sound("sounds/heavy-breathing-scream.mp3")
footstep = pygame.mixer.Sound("sounds/valorant-footstep.mp3")
ambient = pygame.mixer.Sound("sounds/among-us-reactor-ambient.mp3")
jumpscare = pygame.mixer.Sound("sounds/raaaaahhh.mp3")
# --- CCTV Setup ---
# 1. โหลดรูปกล้อง
cam_setup = {
    "CAM 1": {"empty": "images/up-left-conor.jpg", "ghost": "images/up-left-conor_G.jpg"},
    "CAM 2": {"empty": "images/windowcam.jpg",        "ghost": "images/windowcam_GN.jpg"},
    "CAM 3": {"empty": "images/d1cam.jpg",         "ghost": "images/d1cam_G.jpg"},
    "CAM 4": {"empty": "images/d2cam.jpg",         "ghost": "images/d2cam_G.jpg"},
    "CAM 5": {"empty": "images/roadcam.jpg",       "ghost": "images/roadcam_G.jpg"}
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

# 2. CCTV Variables
current_cam = "CAM 5"
cam_offset_x = 0
static_timer = 0
ghost_cctv_active = False
ghost_cctv_pos = "CAM 0" # ผีในกล้องเริ่มที่ CAM 5
ghost_nodes = {
    "CAM 0": ["CAM 5"],
    "CAM 1": ["CAM 2", "CAM 3"],
    "CAM 2": ["CAM 1", "CAM 4"],
    "CAM 3": ["CAM 1", "CAM 4", "CAM 5"],
    "CAM 4": ["CAM 2", "CAM 3", "CAM 5"],
    "CAM 5": ["CAM 3", "CAM 4"]
}

# 3. แผนที่ปุ่ม CCTV
class CamButton:
    def __init__(self, name, x, y):
        self.name = name
        # ปรับขนาด Rect ของปุ่มให้เล็กลง เหลือแค่พอดีตัวหนังสือ
        # (เช่น 40x20 หรือปรับตาม font)
        self.rect = pygame.Rect(x, y, 50, 30) 
        self.font = pygame.font.SysFont("Arial", 12, bold=True)
    def draw(self, screen, is_active):
        # 1. วาดพื้นหลังปุ่ม (Background)
        # ถ้าเลือกปุ่มนี้อยู่ (is_active) ให้เป็นสีเขียว ถ้าไม่ได้เลือกให้เป็นสีดำจางๆ
        bg_color = (0, 150, 0) if is_active else (30, 30, 30)
        pygame.draw.rect(screen, bg_color, self.rect) # วาดสี่เหลี่ยมทึบเป็นพื้นหลัง
        # 2. วาดกรอบสี่เหลี่ยมเล็กๆ เพื่อระบุตำแหน่งปุ่ม
        # ถ้าเลือกอยู่ให้เป็นสีเขียว (หรือสีที่คุณต้องการ) ถ้าไม่เลือกเป็นสีเทา
        border_color = (0, 255, 0) if is_active else (150, 150, 150)
        pygame.draw.rect(screen, border_color, self.rect, 1) # วาดแค่เส้นขอบ

        # 3. วาดตัวหนังสือ CAM อยู่ตรงกลาง
        text_color = (255, 255, 255) # ตัวหนังสือสีขาวเสมอก็ได้
        txt = self.font.render(self.name, True, text_color)
        
        # จัดตัวหนังสือให้อยู่ตรงกลางปุ่ม
        text_rect = txt.get_rect(center=self.rect.center)
        screen.blit(txt, text_rect)

map_x, map_y = 380,320
cctv_buttons = [
    # อิงตามรูปแรก: CAM 1 อยู่บนซ้าย, CAM 2 อยู่หน้าต่าง, CAM 5 อยู่บนถนน
    CamButton("CAM 1", map_x + 130,  map_y + 80),   # มุมซ้ายบน (YOU)
    CamButton("CAM 2", map_x + 220, map_y + 90),   # ตรงหน้าต่าง (window)
    CamButton("CAM 3", map_x + 130,  map_y + 180),  # ประตู D1
    CamButton("CAM 4", map_x + 365, map_y + 180),  # ประตู D2
    CamButton("CAM 5", map_x + 265, map_y + 240),  # บนถนน (ROAD)
]
# --- Load Assets ---
# (ใช้ try-except หรือตรวจสอบ path ให้ดีนะครับ)
try:
    tileset = pygame.image.load("assets/Tilesheets/roguelikeIndoor_transparent.png").convert_alpha()
    # โหลดรูปหน้าต่างและ jumpscare
    windowg0 = pygame.transform.scale(pygame.image.load("images/windowg0%.jpg"), (SCREEN_W, SCREEN_H))
    windowg30 = pygame.transform.scale(pygame.image.load("images/windowg30%.jpg"), (SCREEN_W, SCREEN_H))
    windowg70 = pygame.transform.scale(pygame.image.load("images/windowg70%.jpg"), (SCREEN_W, SCREEN_H))
    windowg99 = pygame.transform.scale(pygame.image.load("images/windowg99%.jpg"), (SCREEN_W, SCREEN_H))
    ghost_jump = pygame.transform.scale(pygame.image.load("images/gjump.jpg"), (SCREEN_W, SCREEN_H))
    door = pygame.transform.scale(pygame.image.load("images/door.jpg"), (SCREEN_W, SCREEN_H))
    doorg = pygame.transform.scale(pygame.image.load("images/doorg.jpg"), (SCREEN_W, SCREEN_H))
except:
    print("Warning: Some assets not found!")
    # สร้าง Surface เปล่ากัน Error สำหรับ Test
    windowg0 = windowg30 = windowg70 = windowg99 = ghost_jump = pygame.Surface((SCREEN_W, SCREEN_H))

def get_tile(col, row):
    rect = pygame.Rect(col * (TILE_SIZE + 1), row * (TILE_SIZE + 1), TILE_SIZE, TILE_SIZE)
    image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    image.blit(tileset, (0, 0), rect)
    return pygame.transform.scale(image, (DISPLAY_TILE, DISPLAY_TILE))

def reset():
    global ghost_active,ghost_cctv_active,breathing_playing,breathing_scream_playing,chasing_playing
    ghost_active = False
    ghost_cctv_active = True
    breathing_playing = False
    breathing_scream_playing = False
    chasing_playing = False

    chasing.stop()
    breathing.stop()
    breathing_scream.stop()
    hit_sound.stop()

map_data = [
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,13,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,13,-1,-1,-1],
    [-1,-1,13,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,13,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
]
decor_map = [
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,5,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,11,6,-1,-1,-1],
    [-1,-1,2,13,13,13,13,13,2,13,13,13,13,13,13,13,13,13,13,13,13,13,3,-1,-1,-1],
    [-1,-1,2,-1,-1,20,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,5,11,11,11,11,11,6,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,-1,-1,2,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,7,1,1,1,1,1,1,1,8,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,21,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,3,-1,-1,-1],
    [-1,-1,2,-1,-1,22,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,22,-1,-1,3,-1,-1,-1],
    [-1,-1,7,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,8,-1,-1,-1],
    [-1,-1,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
    [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],
]
tiles = {
    0: pygame.transform.scale(get_tile(23, 0), (16*SCALE, 16*SCALE)),
    1: pygame.transform.scale(get_tile(24, 0), (16*SCALE, 16*SCALE)),
    2: pygame.transform.scale(get_tile(25, 0), (16*SCALE, 16*SCALE)),
    4: pygame.transform.scale(get_tile(10, 13), (16*SCALE, 16*SCALE)),
    5: pygame.transform.scale(get_tile(10, 12), (16*SCALE, 16*SCALE)),
    -1: pygame.transform.scale(get_tile(-1, -1), (16*SCALE, 16*SCALE)),
    13: pygame.transform.scale(get_tile(10, 17), (16*SCALE, 16*SCALE)),
    
}
walls = {
    -1: pygame.transform.scale(get_tile(-1, -1), (16*SCALE, 16*SCALE)),
    1: pygame.transform.scale(get_tile(9, 16), (16*SCALE, 16*SCALE)),
    11: pygame.transform.scale(get_tile(3, 13), (16*SCALE, 16*SCALE)),
    12: pygame.transform.scale(get_tile(10, 17), (16*SCALE, 16*SCALE)),
    13: pygame.transform.scale(get_tile(10, 17), (16*SCALE, 16*SCALE)),
    2: pygame.transform.scale(get_tile(10, 13), (16*SCALE, 16*SCALE)),
    3: pygame.transform.scale(get_tile(11, 13), (16*SCALE, 16*SCALE)),
    5: pygame.transform.scale(get_tile(10, 12), (16*SCALE, 16*SCALE)),
    6: pygame.transform.scale(get_tile(11, 12), (16*SCALE, 16*SCALE)),
    7: pygame.transform.scale(get_tile(8, 16), (16*SCALE, 16*SCALE)),
    8: pygame.transform.scale(get_tile(10, 16), (16*SCALE, 16*SCALE)),
    20: pygame.transform.scale(get_tile(14, 14), (16*SCALE, 16*SCALE)),
    21: pygame.transform.scale(get_tile(19, 14), (16*SCALE, 16*SCALE)),
    22: pygame.transform.scale(get_tile(20, 17), (16*SCALE, 16*SCALE)),
}
tiles = { 1: get_tile(24, 0), 13: get_tile(10, 17) }
walls_img = {
    1: get_tile(9, 16), 2: get_tile(10, 13), 3: get_tile(11, 13),
    5: get_tile(10, 12), 6: get_tile(11, 12), 11: get_tile(3, 13),
    12: get_tile(10, 17), 13: get_tile(10, 17), 20: get_tile(14, 14),
    21: get_tile(19, 14), 22: get_tile(20, 17)
}

# --- Game Variables ---
player_size = 30
player_x, player_y = 400, 450
player_speed = 3
game_state = "main"
window_progress = 50
window_speed = 0.2
click_power = 1.5
jumpscare_timer = 0
shake_timer = 0
near_interact = False
near_window = False
near_door = False
near_computer = False
max_reached_progress = window_progress
last_pull_time = 0
pull_force_x = 0
pull_force_y = 0
charge_level = 0
ghost_active = False
ghost_target = None   # "window" หรือ "door"
ghost_spawn_time = 0
ghost_cooldown = 10000  # เวลาพักก่อนสุ่มตัวใหม่ (ms)
last_ghost_time = 0
last_door_attack_time = 0
door_attack_cooldown = 10000  # 8 วินาที
last_attack_cam = None
last_knock_time = 0
chasing_playing = False
breathing_playing = False
breathing_scream_playing = False
footstep_playing = False
ambient_playing = False
# Pre-calculate Rects
wall_rects = []
window_rects = []
door_rects = []
computer_rects = []
for r, row in enumerate(decor_map):
    for c, val in enumerate(row):
        rect = pygame.Rect(c * DISPLAY_TILE, r * DISPLAY_TILE, DISPLAY_TILE, DISPLAY_TILE)
        if val in [1, 2, 3, 5, 6, 7, 8, 11, 12, 13]:
            wall_rects.append(rect)
        if val in [20]:
            computer_rects.append(rect)
        if val in [21]:
            window_rects.append(rect)
        if val in [22]:
            door_rects.append(rect)
        

# Custom Events
GHOST_CCTV_MOVE = pygame.USEREVENT + 1
pygame.time.set_timer(GHOST_CCTV_MOVE, 5000)

# --- Main Loop ---
running = True
while running:
    screen.fill((0, 0, 0))
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    spacebar_press = False  # รีเซ็ตทุกเฟรม

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == GHOST_CCTV_MOVE:  
            if current_time - last_ghost_time < ghost_cooldown:
                continue
            
            if game_state in ["window", "door"]:
                continue
            # ถ้ามีผี active อยู่แล้ว → ไม่ต้อง spawn ซ้ำ
            if ghost_active:
                continue

            move = False
            # =========================
            # 🎯 CAM 2 → WINDOW LOGIC
            # =========================
            if ghost_cctv_pos == "CAM 2":
                if random.random() < 0.5 and current_time - last_door_attack_time > door_attack_cooldown:
                    ghost_active = True
                    ghost_target = "window"
                    ghost_spawn_time = current_time
                    last_door_attack_time = current_time
                    window_opening.play()
                    print("Ghost attack from CAM 2 -> WINDOW")
                else:
                    ghost_cctv_pos = random.choice(["CAM 1", "CAM 4"])
                    move = True

            # =========================
            # 🚪 CAM 3 → DOOR LOGIC
            # =========================
            elif ghost_cctv_pos == "CAM 3":
                if random.random() < 0.3 and current_time - last_door_attack_time > door_attack_cooldown:
                    ghost_active = True
                    ghost_target = "door"
                    ghost_spawn_time = current_time
                    last_door_attack_time = current_time
                    door_opening.play()
                    print("Ghost attack from CAM 3 -> DOOR")
                else:
                    ghost_cctv_pos = random.choice(["CAM 1", "CAM 4", "CAM 5"])
                    move = True

            # =========================
            # 🚪 CAM 4 → DOOR LOGIC
            # =========================
            
            elif ghost_cctv_pos == "CAM 4":
                if random.random() < 0.3 and current_time - last_door_attack_time > door_attack_cooldown:
                    ghost_active = True
                    ghost_target = "door"
                    ghost_spawn_time = current_time
                    last_door_attack_time = current_time
                    door_knocking.stop()   # 💥 หยุดเสียงเคาะทันที
                    door_opening.play()
                    print("Ghost attack from CAM 4 -> DOOR")
                else:
                    ghost_cctv_pos = random.choice(["CAM 2","CAM 5", "CAM 3"])
                    move = True

            # =========================
            # 👻 DEFAULT MOVE
            # =========================
            else:
                ghost_cctv_pos = random.choice(ghost_nodes[ghost_cctv_pos])
                move = True

            if move:
                static_timer = 15
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or pygame.K_e:
                spacebar_press = True

            if game_state == "main" and event.key == pygame.K_e:
                if near_window:
                    # ✅ มีผี → เข้าเกม
                    footstep.stop()
                    if ghost_active and ghost_target == "window":
                        game_state = "window"
                        window_progress = 30

                        ghost_active = False
                        last_ghost_time = current_time

                    # ❌ ไม่มีผี → แค่ดูเฉยๆ
                    else:
                        game_state = "window_idle"

                elif near_door:
                    # ✅ มีผี → เข้าเกม
                    footstep.stop()
                    if ghost_active and ghost_target == "door":
                        game_state = "door"
                        charge_level = 50

                        ghost_active = False
                        last_ghost_time = current_time

                    # ❌ ไม่มีผี → แค่ดูเฉยๆ
                    else:
                        game_state = "door_idle"
                        footstep.stop()
                elif near_computer:
                    game_state = "computer"
                    static_timer = 20
                    footstep.stop()
                    open_camera_sound.play()
                    ambient.play(-1)

            elif game_state in ["window_idle", "door_idle", "computer"] and event.key == pygame.K_q:
                game_state = "main"
                ambient.stop()
        if event.type == pygame.MOUSEBUTTONDOWN and game_state == "computer":
            for btn in cctv_buttons:
                if btn.rect.collidepoint(event.pos):
                    current_cam = btn.name
                    static_timer = 20 # Noise เมื่อเปลี่ยนกล้อง
                    camera_sound.play()
                    footstep.stop()
    # 2. Update Logic
    
    if ghost_cctv_pos == "CAM 4" and not ghost_active and game_state != "door":
                if current_time - last_knock_time > 2000:  # ทุก 2 วิ
                    door_knocking.play()
                    last_knock_time = current_time

    # --- GHOST TIMER CHECK ---
    if ghost_active and game_state in ["main", "window_idle", "door_idle","computer"]:
        if ghost_target == "window":
            time_limit = 10000  # 10 วิ

        elif ghost_target == "door":
            time_limit = 20000  # 20 วิ


        # ถ้าเวลาเกิน → ตาย
        if current_time - ghost_spawn_time > time_limit:
            game_state = "jumpscare"
            jumpscare_timer = 90
            reset()

    if game_state == "main":
        moving = False
        keys = pygame.key.get_pressed()
        new_x, new_y = player_x, player_y
        
        if keys[pygame.K_a]: 
            new_x -= player_speed
            moving = True
        if keys[pygame.K_d]: 
            new_x += player_speed
            moving = True
        # Check Collision X
        p_rect = pygame.Rect(new_x, player_y, player_size, player_size)
        if any(p_rect.colliderect(w) for w in wall_rects): new_x = player_x
        
        if keys[pygame.K_w]: 
            new_y -= player_speed
            moving = True
        if keys[pygame.K_s]: 
            new_y += player_speed
            moving = True
        
        # ▶️ ถ้าเดิน → เปิดเสียง
        if moving:
            if not footstep_playing:
                footstep.play(-1)   # 🔁 loop
                footstep_playing = True

        # ⏹️ ถ้าหยุด → หยุดเสียง
        else:
            if footstep_playing:
                footstep.stop()
                footstep_playing = False

        # Check Collision Y
        p_rect = pygame.Rect(new_x, new_y, player_size, player_size)
        if any(p_rect.colliderect(w) for w in wall_rects): new_y = player_y

        player_x, player_y = new_x, new_y

        # Interaction Check
        p_rect = pygame.Rect(player_x, player_y, player_size, player_size)
        near_window = any(p_rect.inflate(20, 20).colliderect(i) for i in window_rects)
        near_door = any(p_rect.inflate(20, 20).colliderect(i) for i in door_rects)
        near_computer = any(p_rect.inflate(20, 20).colliderect(i) for i in computer_rects)

    elif game_state == "window":
        if not chasing_playing:
            chasing.play(-1)   # 🔁 loop
            chasing_playing = True
    # --- INIT (ใส่ก่อน loop จริงครั้งแรก) ---
    # if not defined:
    # max_reached_progress = window_progress
        shake_timer = 10
        # 🎧 SOUND CONTROL
        # ▶️ เข้า minigame ครั้งแรก → เปิด breathing
        if not breathing_playing and not breathing_scream_playing:
            breathing.play(-1)
            breathing_playing = True

        # 😱 ถ้าเกิน 80 → เปลี่ยนเป็น scream
        if window_progress > 70:
            if not breathing_scream_playing:
                breathing.stop()
                breathing_playing = False

                breathing_scream.play(-1)
                breathing_scream_playing = True

    # 1. อัปเดตค่าที่เคยสูงสุด
        if window_progress > max_reached_progress:
            max_reached_progress = window_progress

    # 2. คำนวณความเร็วผี (อิงจาก "จุดที่เคยแย่สุด")
        base_speed = 0.15
        max_ghost_speed = 1

    # ยิ่งเคยใกล้ตาย → ผียิ่งแรง
        target_speed = base_speed + (max_reached_progress * 0.01)

    # ถ้าผู้เล่นดันกลับได้ (progress ปัจจุบัน < จุดพีค)
        if window_progress < max_reached_progress:
            target_speed *= 0.5   # ลดความโหดลง 30%
            click_power += 0.01
    # clamp ไม่ให้เกินลิมิต
        current_push_speed = min(max_ghost_speed, target_speed)

    # ผีดัน
        window_progress += current_push_speed

    # 3. โบนัสฮึดสู้ (เหมือนเดิม แต่ปรับให้นุ่มขึ้น)
        bonus_power = (window_progress / 100) * 2.0

        if spacebar_press:
            window_progress -= (click_power + bonus_power)

    # 4. clamp ค่า
        window_progress = max(0, min(100, window_progress))

    # 5. reset peak ถ้าผู้เล่นเอาอยู่จริง
        if window_progress < max_reached_progress - 20:
            max_reached_progress = window_progress

    # 6. เช็คแพ้/ชนะ
        if window_progress >= 100:
            game_state = "jumpscare"
            jumpscare_timer = 90

        elif window_progress <= 0:
            game_state = "main"
            window_progress = 20
            max_reached_progress = window_progress
            click_power = 1.5
            last_ghost_time = current_time   
            ghost_cctv_pos = random.choice(["CAM 4", "CAM 5","CAM 1"])  
            last_ghost_time = current_time
            reset()
    
    elif game_state == "door":

        if not chasing_playing:
            chasing.play(-1)  
            chasing_playing = True

        # 1. ระบบสุ่มแรงดึงทุกๆ 2 วินาที (2000 ms)
        if current_time - last_pull_time > 2000:
            # สุ่มทิศทาง 360 องศา และความแรง
            angle = random.uniform(0, 2 * math.pi)
            strength = random.uniform(10, 25) # ปรับความโหดตรงนี้

            pull_force_x = math.cos(angle) * strength
            pull_force_y = math.sin(angle) * strength

            last_pull_time = current_time

            shake_timer = 15
            hit_sound.play()

        # 2. คำนวณตำแหน่งเมาส์ + แรงดึง
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # ค่อยๆ ลดแรงดึงลง (Damping) เพื่อให้เมาส์ไม่ไหลเตลิดไปตลอดกาล
        pull_force_x *= 0.95
        pull_force_y *= 0.95

        # "หลอก" ตำแหน่งเมาส์ (ใน Pygame เราเซ็ตตำแหน่งเมาส์จริงได้ด้วย pygame.mouse.set_pos)
        new_mouse_x = mouse_x + pull_force_x
        new_mouse_y = mouse_y + pull_force_y
        pygame.mouse.set_pos([new_mouse_x, new_mouse_y])

        # 3. เช็คว่าเมาส์อยู่ในวงกลมไหม
        dist = math.hypot(new_mouse_x - CIRCLE_POS[0], new_mouse_y - CIRCLE_POS[1])

        if dist < CIRCLE_RADIUS:
            charge_level += 0.3  
        else:
            charge_level -= 0.6  

        # 4. เงื่อนไขแพ้/ชนะ
        if charge_level >= 100:
            game_state = "main"
            last_ghost_time = current_time  
            ghost_cctv_pos = "CAM 5"
            last_ghost_time = current_time
            reset()

        elif charge_level <= 0:
            game_state = "jumpscare"
            jumpscare_timer = 90

    elif game_state == "computer":
        # CCTV Panning
        cam_offset_x = max(SCREEN_W - IMAGE_W, min(0, cam_offset_x))
        if mouse_pos[0] < 100 and cam_offset_x < 0: cam_offset_x += 7
        elif mouse_pos[0] > SCREEN_W - 100 and cam_offset_x > (SCREEN_W - IMAGE_W): cam_offset_x -= 7
        

    elif game_state == "jumpscare":
        jumpscare_timer -= 1
        if jumpscare_timer <= 0:
            game_state = "main"
            window_progress = 50
            charge_level = 50
            ghost_cctv_pos = "CAM 5"
            player_x, player_y = 400, 450
            reset()

    # 3. Rendering
    if game_state == "main":
        # Draw Floor
        for r, row in enumerate(map_data):
            for c, val in enumerate(row):
                if val in tiles: screen.blit(tiles[val], (c * DISPLAY_TILE, r * DISPLAY_TILE))
        # Draw Walls
        for r, row in enumerate(decor_map):
            for c, val in enumerate(row):
                if val in walls_img: screen.blit(walls_img[val], (c * DISPLAY_TILE, r * DISPLAY_TILE))
        
        # Draw Player
        pygame.draw.rect(screen, (0, 200, 255), (player_x, player_y, player_size, player_size))
        
        if near_window:
            txt = font_small.render("Press [E] to Close Window", True, (255,255,0))
            screen.blit(txt, (player_x - 50, player_y - 40))
        elif near_door:
            txt = font_small.render("Press [E] to Hold Door", True, (255,255,0))
            screen.blit(txt, (player_x - 50, player_y - 40))
        elif near_computer:
            txt = font_small.render("Press [E] to Use Computer", True, (255, 255, 0))
            screen.blit(txt, (player_x - 50, player_y - 40))
        
        if ghost_active:
            txt = font_small.render(f"GHOST: {ghost_target}", True, (255,0,0))
            screen.blit(txt, (10, 10))

    elif game_state == "window":
        # Window Images
        if window_progress < 40: img = windowg0
        elif window_progress < 60: img = windowg30 
        elif window_progress < 80: img = windowg70
        else: img = windowg99

        shake_x, shake_y = 0, 0

        if shake_timer > 0:
            shake_x = random.randint(-7, 7)
            shake_y = random.randint(-7, 7)
            shake_timer -= 1

        screen.blit(img, (shake_x, shake_y))
        # UI Bar
        pygame.draw.rect(screen, (50, 50, 50), (200, 530, 400, 25))
        pygame.draw.rect(screen, (200, 0, 0), (200, 530, int(window_progress * 4), 25))
        txt = font_small.render("CLICK RAPIDLY TO HOLD THE WINDOW!", True, (255, 255, 255))
        screen.blit(txt, (230, 500))
    
    elif game_state == "door":
        if charge_level <= 70:
            img = doorg
        else:
            img = door

        shake_x, shake_y = 0, 0

        if shake_timer > 0:
            shake_x = random.randint(-10, 10)
            shake_y = random.randint(-10, 10)
            shake_timer -= 1

        screen.blit(img, (shake_x, shake_y))

        #วาดวงกลมเป้าหมาย
        pygame.draw.circle(screen, (255, 0, 0), CIRCLE_POS, CIRCLE_RADIUS, 3)

        #วาดจุดเมาส์
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (255, 50, 50), (int(mouse_x), int(mouse_y)), 5)

        #แถบพลัง
        pygame.draw.rect(screen, (50, 50, 50), (200, 530, 400, 25))
        pygame.draw.rect(screen, (0, 200, 0), (200, 530, int(charge_level * 4), 25))
        txt = font_small.render("KEEP CURSOR IN CIRCLE!", True, (255, 255, 255))

    elif game_state == "computer":
        # 1. วาดรูปกล้อง
        if ghost_active:
            state = "empty" 
        else:
            state = "ghost" if current_cam == ghost_cctv_pos else "empty"
        screen.blit(cameras[current_cam][state], (cam_offset_x, 0))

        # 2. วาด Noise
        # วาด scanline
        scanline = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        for y in range(0, SCREEN_H, 3):
            pygame.draw.line(scanline, (255,255,255,20), (0,y), (SCREEN_W,y))

        
        offset_y = random.randint(-2, 2)
        # วาด noise
        screen.blit(scanline, (0,0))
        screen.blit(noise_img, (0, offset_y))
        
        if static_timer > 0: 
            for _ in range(400): 
                nx, ny = random.randint(0, SCREEN_W), random.randint(0, SCREEN_H) 
                nc = random.randint(150, 255) 
                pygame.draw.rect(screen, (nc, nc, nc), (nx, ny, 3, 3)) 
                static_timer -= 1

        # 3. วาดแผนที่และปุ่ม
        map_bg_rect = pygame.Rect(map_x - 10, map_y - 10, 250, 200)
        # วาดรูป cam_roadmap
        screen.blit(map_img, (map_x, map_y)) 
        

        # 4. วาดปุ่มทับลงไปตามตำแหน่งที่เซ็ตไว้
        for btn in cctv_buttons:
            btn.draw(screen, btn.name == current_cam)
            
        # 5. UI
        screen.blit(font_small.render(f"LIVE: {current_cam}", True, (255, 0, 0)), (20, 20))
        screen.blit(font_small.render("Press [Q] to Exit", True, (255, 255, 255)), (20, SCREEN_H - 40))

    elif game_state == "window_idle":   
        screen.blit(windowg0, (0, 0))

        txt = font_small.render("Nothing here... (Q to exit)", True, (255,255,255))
        screen.blit(txt, (300, 500))

    elif game_state == "door_idle":
        screen.blit(door, (0, 0))

        txt = font_small.render("Nothing here... (Q to exit)", True, (255,255,255))
        screen.blit(txt, (300, 500))

    elif game_state == "jumpscare":
        jumpscare.play()
        screen.blit(ghost_jump, (0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()