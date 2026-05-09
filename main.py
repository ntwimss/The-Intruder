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
last_pull_time = 0
map_img = pygame.image.load("images/CamMap-removebg-preview.png").convert_alpha()
map_img = pygame.transform.scale(map_img, (500, 300))
noise_img = pygame.image.load("images/noise-bg.jpg").convert_alpha()
noise_img = pygame.transform.scale(noise_img, (800,600))
noise_img.set_alpha(40)

# --- Hour System ---
current_hour = 1
max_unlocked_hour = 1
game_time = 0  # นาทีเกม (0-60)
time_speed = 10  # เพิ่ม 10 นาทีต่อ 1 นาทีจริง
hour_duration = 60  # นาทีต่อ hour
game_won = False
hour_intro_shown = False

# Hour Configurations
hour_configs = {
    1: {
        "name": "Intro",
        "intro_message": "Hour 1: The night begins...",
        "window_speed_base": 0.1,
        "ghost_cooldown": 10000,
        "door_attack_cooldown": 10000,
        "blackout": False,
        "camera_disabled": False,
        "phone_unlocked": False,
        "dual_intruder": False,
    },
    2: {
        "name": "Blackout",
        "intro_message": "Hour 2: The power goes out...",
        "window_speed_base": 0.15,
        "ghost_cooldown": 9000,
        "door_attack_cooldown": 9000,
        "blackout": True,
        "camera_disabled": True,
        "phone_unlocked": False,
        "dual_intruder": False,
    },
    3: {
        "name": "Police",
        "intro_message": "Hour 3: 3AM... I decided to call the police...",
        "window_speed_base": 0.2,
        "ghost_cooldown": 8000,
        "door_attack_cooldown": 8000,
        "blackout": False,
        "camera_disabled": False,
        "phone_unlocked": True,
        "dual_intruder": False,
    },
    4: {
        "name": "Dual Threat",
        "intro_message": "Hour 4: There's more than 1 intruder! I need to block them both!",
        "window_speed_base": 0.25,
        "ghost_cooldown": 7000,
        "door_attack_cooldown": 7000,
        "blackout": False,
        "camera_disabled": False,
        "phone_unlocked": True,
        "dual_intruder": True,
    },
    5: {
        "name": "Nightmare",
        "intro_message": "Hour 5: It's getting worse... Help me...",
        "window_speed_base": 0.3,
        "ghost_cooldown": 6000,
        "door_attack_cooldown": 6000,
        "blackout": False,
        "camera_disabled": False,
        "phone_unlocked": True,
        "dual_intruder": True,
    },
}

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
    "CAM 1": {"empty": "images/cam1.jpg",           "ghost": "images/cam1ghost.jpg"},
    "CAM 2": {"empty": "images/cam2.jpg",        "ghost": "images/cam2ghostfar.jpg", "ghost2": "images/cam2ghostnear.jpg"},
    "CAM 3": {"empty": "images/cam3.jpg",         "ghost": "images/cam3ghost.jpg"},
    "CAM 4": {"empty": "images/cam4.jpg",         "ghost": "images/cam4ghost.jpg"},
    "CAM 5": {"empty": "images/cam5.jpg",       "ghost": "images/cam5ghost.jpg"},
    "CAM 6": {"empty": "images/cam6.jpg",       "ghost": "images/cam6ghostfar.jpg", "ghost2": "images/cam6ghostnear.jpg"},
    "CAM 7": {"empty": "images/cam7.jpg",       "ghost": "images/cam7ghost.jpg"},
    "CAM 8": {"empty": "images/cam8.jpg",       "ghost": "images/cam8ghost.jpg"},
    "CAM 9": {"empty": "images/cam9.jpg",       "ghost": "images/cam9ghost.jpg"},
    
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
current_cam = "CAM 1"
cam_offset_x = 0
static_timer = 0
ghost_cctv_active = False
ghost_cctv_pos = None
ghost_cctv_state = None
ghost_from_pos = None
ghost_spawn_delay = 5000  # 5 วิ
game_start_time = pygame.time.get_ticks()

ghost_nodes = {
    None: [(("CAM 1", "far"), 1.0)],
    ("CAM 1", "far"): [(("CAM 2", "near"), 0.6), (("CAM 2", "far"), 0.1), (("CAM 4", "far"), 0.3)],
    ("CAM 2", "far"): [(("CAM 3", "far"), 0.7),(("CAM 2", "near"), 0.2), (("CAM 5", "far"), 0.1)],
    ("CAM 2", "near"): [(("CAM 2", "far"), 0.2), (("CAM 5", "far"), 0.8)],
    ("CAM 3", "far"): [(("CAM 2", "far"), 0.1), (("CAM 7", "far"), 0.1), (("CAM 8", "far"), 0.8)],
    ("CAM 4", "far"): [(("CAM 1", "far"), 0.4), (("CAM 2", "far"), 0.1), (("CAM 3", "far"), 0.5)],
    ("CAM 5", "far"): [(("CAM 6", "far"), 0.7), (("CAM 7", "far"), 0.2), (("CAM 8", "far"), 0.1)],
    ("CAM 6", "far"): [(("CAM 6", "near"), 0.6), (("CAM 7", "far"), 0.3), (("CAM 8", "far"), 0.1)],
    ("CAM 6", "near"): [(("CAM 6", "near"), 1.0)],
    ("CAM 7", "far"): [(("CAM 6", "near"), 0.45), (("CAM 8", "far"), 0.45), (("CAM 9", "far"), 0.1)],
    ("CAM 8", "far"): [(("CAM 7", "far"), 0.15), (("CAM 3", "far"), 0.05), (("CAM 9", "far"), 0.8)],
    ("CAM 9", "far"): [(("CAM 9", "far"), 1.0)],
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

map_x, map_y = 320,320
cctv_buttons = [
    CamButton("CAM 1", map_x + 120,  map_y + 60),  
    CamButton("CAM 2", map_x + 130, map_y + 110),  
    CamButton("CAM 3", map_x + 355,  map_y + 90),  
    CamButton("CAM 4", map_x + 405, map_y + 40),  
    CamButton("CAM 5", map_x + 180, map_y + 170),  
    CamButton("CAM 6", map_x + 180, map_y + 250),
    CamButton("CAM 7", map_x + 300, map_y + 190),
    CamButton("CAM 8", map_x + 340,  map_y + 130),
    CamButton("CAM 9", map_x + 405, map_y + 150),
]
# --- Load Assets ---
try:
    tileset = pygame.image.load("assets/Tilesheets/roguelikeIndoor_transparent.png").convert_alpha()
    # โหลดรูปหน้าต่างและ jumpscare
    windowg0 = pygame.transform.scale(pygame.image.load("images/windowg0%.jpg"), (SCREEN_W, SCREEN_H))
    windowg30 = pygame.transform.scale(pygame.image.load("images/windowg30%.jpg"), (SCREEN_W, SCREEN_H))
    windowg70 = pygame.transform.scale(pygame.image.load("images/windowg70%.jpg"), (SCREEN_W, SCREEN_H))
    windowg99 = pygame.transform.scale(pygame.image.load("images/windowg99%.jpg"), (SCREEN_W, SCREEN_H))
    ghost_jump = pygame.transform.scale(pygame.image.load("images/gjump.jpg"), (SCREEN_W, SCREEN_H))
    door1 = pygame.transform.scale(pygame.image.load("images/door.jpg"), (SCREEN_W, SCREEN_H))
    door1g = pygame.transform.scale(pygame.image.load("images/doorg.jpg"), (SCREEN_W, SCREEN_H))
    door2 = pygame.transform.scale(pygame.image.load("images/d2.jpg"), (SCREEN_W,SCREEN_H))
    door2g = pygame.transform.scale(pygame.image.load("images/d2_g.jpg"), (SCREEN_W, SCREEN_H))

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
    global ghost_active,ghost_cctv_active,breathing_playing,breathing_scream_playing,chasing_playing,ghost_from_pos
    ghost_active = False
    ghost_cctv_active = True
    ghost_from_pos = None
    breathing_playing = False
    breathing_scream_playing = False
    chasing_playing = False

    chasing.stop()
    breathing.stop()
    breathing_scream.stop()
    hit_sound.stop()


def reset_game():
    global game_time, window_progress, charge_level, door2_progress, max_reached_progress, click_power
    global ghost_cctv_pos, ghost_cctv_state, ghost_active, last_ghost_time, game_start_time
    global window_speed, ghost_cooldown, door_attack_cooldown, hour_intro_shown

    game_time = 0
    window_progress = 0
    charge_level = 50
    door2_progress = 20
    max_reached_progress = door2_progress
    click_power = 1.5
    ghost_cctv_pos = "CAM 1"
    ghost_cctv_state = "far"
    ghost_active = False
    last_ghost_time = pygame.time.get_ticks()
    game_start_time = pygame.time.get_ticks()
    hour_intro_shown = False

    # Load difficulty from hour_configs
    config = hour_configs[current_hour]
    window_speed = config["window_speed_base"]
    ghost_cooldown = config["ghost_cooldown"]
    door_attack_cooldown = config["door_attack_cooldown"]


def weighted_choice(choices):
    global ghost_from_pos
    # Filter choices ที่ next_pos != ghost_from_pos เพื่อไม่ให้กลับไปตำแหน่งเดิม
    if ghost_from_pos is not None:
        choices = [(item, weight) for item, weight in choices if item[0] != ghost_from_pos]
    if not choices:
        # ถ้าไม่มีทางเลือกอื่น ให้ใช้ choices เดิม (เพื่อป้องกัน stuck)
        choices = [(item, weight) for item, weight in ghost_nodes.get((ghost_cctv_pos, ghost_cctv_state), [])]
        if ghost_from_pos is not None:
            choices = [(item, weight) for item, weight in choices if item[0] != ghost_from_pos]
        if not choices:
            # ถ้ายังไม่มี ให้สุ่มอะไรก็ได้
            choices = [(item, weight) for item, weight in ghost_nodes.get((ghost_cctv_pos, ghost_cctv_state), [])]
    
    total = sum(weight for _, weight in choices)
    if total == 0:
        return random.choice(choices)[0] if choices else None
    r = random.random() * total
    upto = 0
    for item, weight in choices:
        if upto + weight >= r:
            return item
        upto += weight
    return choices[-1][0]

def draw_window_warning(progress):
    warning_text = None
    warning_color = None
    if 60 <= progress <= 80:
        warning_text = "WARNING"
        warning_color = (255, 255, 0)
    elif 81 <= progress < 100:
        warning_text = "DANGER"
        warning_color = (255, 0, 0)
    elif progress >= 100:
        warning_text = "ATTACK"
        warning_color = (255, 0, 0)

    if warning_text:
        pygame.draw.rect(screen, (0, 0, 0), (620, 10, 170, 60))
        pygame.draw.rect(screen, warning_color, (632, 22, 36, 36))
        warn_surf = font_small.render(warning_text, True, warning_color)
        screen.blit(warn_surf, (675, 18))
        warn_pct = font_small.render(f"{int(progress)}%", True, warning_color)
        screen.blit(warn_pct, (675, 42))


def get_time_string():
    total_hours = (current_hour - 1) + int(game_time // 60)
    display_minutes = int(game_time % 60 // 10) * 10
    if display_minutes == 0:
        return f"{total_hours:02d}:00 AM"
    elif display_minutes == 60:
        return f"{total_hours + 1} AM"
    else:
        return f"{total_hours:02d}:{display_minutes:02d} AM"


# --- Game State Constants ---
STATE_MAIN = "main"
STATE_WINDOW = "window"
STATE_DOOR = "door"
STATE_DOOR2 = "door2"
STATE_COMPUTER = "computer"
STATE_DOOR_IDLE = "door_idle"
STATE_DOOR2_IDLE = "door2_idle"
STATE_JUMPSCARE = "jumpscare"
STATE_MENU = "menu"
STATE_GAME_OVER = "game_over"

input_state = {"space": False}
current_menu_page = "main"  # "main" หรือ "hour_select"

# Menu Buttons
button_new_game = pygame.Rect(300, 250, 200, 50)
button_continue = pygame.Rect(300, 320, 200, 50)
button_hour_menu = {}  # Dynamic buttons for hour selection


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
            ghost_cctv_pos = "CAM 1"
            ghost_cctv_state = "far"
            ghost_from_pos = None
            static_timer = 20
        return

    old_pos = ghost_cctv_pos
    move = False

    if ghost_cctv_pos == "CAM 6" and ghost_cctv_state == "near":
        if current_time - last_door_attack_time > door_attack_cooldown:
            ghost_active = True
            ghost_target = "door"
            ghost_spawn_time = current_time
            last_door_attack_time = current_time
            door_opening.play()
            print("Ghost attack from CAM 6 near -> DOOR")

    elif ghost_cctv_pos == "CAM 6" and ghost_cctv_state == "far":
        ghost_cctv_pos, ghost_cctv_state = weighted_choice(ghost_nodes[(ghost_cctv_pos, ghost_cctv_state)])
        move = True

    elif ghost_cctv_pos == "CAM 9":
        if current_time - last_door_attack_time > door_attack_cooldown:
            ghost_active = True
            ghost_target = "door2"
            ghost_spawn_time = current_time
            last_door_attack_time = current_time
            door_knocking.stop()
            door_opening.play()
            print("Ghost attack from CAM 9 -> DOOR2")

    else:
        ghost_cctv_pos, ghost_cctv_state = weighted_choice(ghost_nodes[(ghost_cctv_pos, ghost_cctv_state)])
        move = True

    if move:
        ghost_from_pos = old_pos
        static_timer = 15


def process_keydown(event, current_time):
    global input_state, ghost_active, ghost_target, game_state, charge_level, last_ghost_time, door2_progress
    global current_cam, static_timer, hour_intro_shown

    if event.key == pygame.K_SPACE:
        input_state["space"] = True

    # Skip intro message
    if game_state == STATE_MAIN and not hour_intro_shown:
        hour_intro_shown = True
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
                footstep.stop()

        elif near_door2:
            footstep.stop()
            if ghost_active and ghost_target == "door2":
                set_state(STATE_DOOR2)
                door2_progress = 40
                ghost_active = False
                last_ghost_time = current_time
            else:
                set_state(STATE_DOOR2_IDLE)
                footstep.stop()

        elif near_computer:
            set_state(STATE_COMPUTER)
            static_timer = 20
            footstep.stop()
            open_camera_sound.play()
            ambient.play(-1)

    if event.key == pygame.K_q and game_state in [STATE_DOOR2_IDLE, STATE_DOOR_IDLE, STATE_COMPUTER, STATE_WINDOW]:
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
                current_cam = btn.name
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
            # Check hour buttons and back button
            back_btn = pygame.Rect(350, 450, 100, 40)
            if back_btn.collidepoint(event.pos):
                current_menu_page = "main"
            else:
                for hour_num, btn in button_hour_menu.items():
                    if btn.collidepoint(event.pos):
                        current_hour = hour_num
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
    
    # 1. ตั้งความเร็วพื้นฐาน (ความเร็วปกติที่เพิ่มตลอดเวลา)
    current_speed = window_speed * 10
    
    # 2. ถ้าผีบุก และเรากำลังสู้ที่ประตู (STATE_DOOR/DOOR2) ให้ลดความเร็วลงตามที่คุณต้องการ
    if game_state in [STATE_DOOR, STATE_DOOR2]:
        current_speed = window_speed * 5  # ลดเหลือ 5 (ช้าลงครึ่งหนึ่งจากปกติ)
    # 3. ตรวจสอบว่าไม่ได้อยู่ในหน้า Jumpscare แล้วจึงทำการบวกค่า
    if game_state != STATE_JUMPSCARE:
        window_progress += current_speed * dt
        # 4. ตรวจสอบการแพ้ (Progress ถึง 100)
        if window_progress >= 100:
            window_progress = 100
            set_state(STATE_JUMPSCARE)
            jumpscare_timer = 90
            return True
            
    return False


def update_ghost_attack_timeout(current_time):
    global jumpscare_timer
    if ghost_active and game_state in [STATE_MAIN, STATE_DOOR2_IDLE, STATE_DOOR_IDLE, STATE_COMPUTER, STATE_WINDOW]:
        time_limit = 20000
        if current_time - ghost_spawn_time > time_limit:
            set_state(STATE_JUMPSCARE)
            jumpscare_timer = 90
            reset()


def update_main(dt):
    global player_x, player_y, footstep_playing, near_window, near_door, near_door2, near_computer

    moving = False
    keys = pygame.key.get_pressed()
    new_x, new_y = player_x, player_y

    if keys[pygame.K_a]:
        new_x -= player_speed
        moving = True
    if keys[pygame.K_d]:
        new_x += player_speed
        moving = True
    if keys[pygame.K_w]:
        new_y -= player_speed
        moving = True
    if keys[pygame.K_s]:
        new_y += player_speed
        moving = True

    p_rect = pygame.Rect(new_x, player_y, player_size, player_size)
    if any(p_rect.colliderect(w) for w in wall_rects):
        new_x = player_x

    p_rect = pygame.Rect(new_x, new_y, player_size, player_size)
    if any(p_rect.colliderect(w) for w in wall_rects):
        new_y = player_y

    player_x, player_y = new_x, new_y

    if moving and not footstep_playing:
        footstep.play(-1)
        footstep_playing = True
    elif not moving and footstep_playing:
        footstep.stop()
        footstep_playing = False

    p_rect = pygame.Rect(player_x, player_y, player_size, player_size)
    near_window = any(p_rect.inflate(20, 20).colliderect(i) for i in window_rects)
    near_door = any(p_rect.inflate(20, 20).colliderect(i) for i in door_rects)
    near_door2 = any(p_rect.inflate(20, 20).colliderect(i) for i in door2_rects)
    near_computer = any(p_rect.inflate(20, 20).colliderect(i) for i in computer_rects)


def update_window_state():
    global window_progress, button_color
    mouse_click = pygame.mouse.get_pressed()
    if button_rect.collidepoint(pygame.mouse.get_pos()) and mouse_click[0]:
        window_progress -= 0.2
        button_color = (100, 0, 0)
    else:
        button_color = (200, 0, 0)
    if window_progress < 0:
        window_progress = 0
    if window_progress >= 100:
        window_progress = 100
        set_state(STATE_JUMPSCARE)


def update_door_state(current_time):
    global charge_level, last_pull_time, pull_force_x, pull_force_y, shake_timer, chasing_playing
    global ghost_active, last_ghost_time, ghost_cctv_pos, ghost_cctv_state, jumpscare_timer

    if not chasing_playing:
        chasing.play(-1)
        chasing_playing = True

    if current_time - last_pull_time > 2000:
        angle = random.uniform(0, 2 * math.pi)
        strength = random.uniform(10, 25)
        pull_force_x = math.cos(angle) * strength
        pull_force_y = math.sin(angle) * strength
        last_pull_time = current_time
        shake_timer = 15
        hit_sound.play()

    mouse_x, mouse_y = pygame.mouse.get_pos()
    pull_force_x *= 0.95
    pull_force_y *= 0.95
    new_mouse_x = mouse_x + pull_force_x
    new_mouse_y = mouse_y + pull_force_y
    pygame.mouse.set_pos([new_mouse_x, new_mouse_y])

    dist = math.hypot(new_mouse_x - CIRCLE_POS[0], new_mouse_y - CIRCLE_POS[1])
    if dist < CIRCLE_RADIUS:
        charge_level += 0.3
    else:
        charge_level -= 0.6

    if charge_level >= 100:
        set_state(STATE_MAIN)
        last_ghost_time = current_time
        ghost_cctv_pos = "CAM 1"
        ghost_cctv_state = "far"
        reset()
    elif charge_level <= 0:
        set_state(STATE_JUMPSCARE)
        jumpscare_timer = 90


def update_door2_state():
    global door2_progress, max_reached_progress, click_power, chasing_playing, breathing_playing, breathing_scream_playing, shake_timer
    global jumpscare_timer, last_ghost_time, ghost_cctv_pos, ghost_cctv_state

    if not chasing_playing:
        chasing.play(-1)
        chasing_playing = True

    if not breathing_playing and not breathing_scream_playing:
        breathing.play(-1)
        breathing_playing = True

    if door2_progress > 70 and not breathing_scream_playing:
        breathing.stop()
        breathing_playing = False
        breathing_scream.play(-1)
        breathing_scream_playing = True

    if door2_progress > max_reached_progress:
        max_reached_progress = door2_progress

    base_speed = 0.15
    max_ghost_speed = 1
    target_speed = base_speed + (max_reached_progress * 0.01)
    if door2_progress < max_reached_progress:
        target_speed *= 0.5
        click_power += 0.01
    current_push_speed = min(max_ghost_speed, target_speed)
    door2_progress += current_push_speed

    bonus_power = (door2_progress / 100) * 2.0
    if input_state["space"]:
        door2_progress -= (click_power + bonus_power)
        shake_timer = 5

    door2_progress = max(0, min(100, door2_progress))

    if door2_progress < max_reached_progress - 20:
        max_reached_progress = door2_progress

    if door2_progress >= 100:
        set_state(STATE_JUMPSCARE)
        jumpscare_timer = 90
    elif door2_progress <= 0:
        set_state(STATE_MAIN)
        door2_progress = 20
        max_reached_progress = door2_progress
        click_power = 1.5
        last_ghost_time = pygame.time.get_ticks()
        ghost_cctv_pos = "CAM 1"
        ghost_cctv_state = "far"
        reset()


def update_computer_state():
    global cam_offset_x
    cam_offset_x = max(SCREEN_W - IMAGE_W, min(0, cam_offset_x))
    mouse_pos = pygame.mouse.get_pos()
    if mouse_pos[0] < 100 and cam_offset_x < 0:
        cam_offset_x += 7
    elif mouse_pos[0] > SCREEN_W - 100 and cam_offset_x > (SCREEN_W - IMAGE_W):
        cam_offset_x -= 7


def update_jumpscare_state():
    global jumpscare_timer, game_state, window_progress, charge_level, ghost_cctv_pos, ghost_cctv_state, player_x, player_y

    if jumpscare_timer == 90:
        jumpscare.play()
    jumpscare_timer -= 1
    if jumpscare_timer <= 0:
        set_state(STATE_MAIN)
        window_progress = 50
        charge_level = 50
        ghost_cctv_pos = "CAM 1"
        ghost_cctv_state = "far"
        player_x, player_y = 400, 400
        reset()


def update_state(dt, current_time):
    global game_time, game_won, max_unlocked_hour
    if update_window_progress(dt):
        return
    update_ghost_attack_timeout(current_time)
    if game_state not in [STATE_MENU, STATE_GAME_OVER]:
        game_time += time_speed * dt / 60
        if game_time >= hour_duration:
            game_won = True
            # Unlock next hour
            if current_hour < 5:
                max_unlocked_hour = current_hour + 1
            set_state(STATE_GAME_OVER)
    if game_state == STATE_MAIN:
        update_main(dt)
    elif game_state == STATE_WINDOW:
        update_window_state()
    elif game_state == STATE_DOOR:
        update_door_state(current_time)
    elif game_state == STATE_DOOR2:
        update_door2_state()
    elif game_state == STATE_COMPUTER:
        update_computer_state()
    elif game_state == STATE_JUMPSCARE:
        update_jumpscare_state()
    elif game_state == STATE_MENU:
        pass
    elif game_state == STATE_GAME_OVER:
        pass


def render_main_state():
    for r, row in enumerate(map_data):
        for c, val in enumerate(row):
            if val in tiles:
                screen.blit(tiles[val], (c * DISPLAY_TILE, r * DISPLAY_TILE))
    for r, row in enumerate(decor_map):
        for c, val in enumerate(row):
            if val in walls_img:
                screen.blit(walls_img[val], (c * DISPLAY_TILE, r * DISPLAY_TILE))
    pygame.draw.rect(screen, (0, 200, 255), (player_x, player_y, player_size, player_size))
    if near_window:
        txt = font_small.render("Press [E] to Close Window", True, (255,255,0))
        screen.blit(txt, (player_x - 50, player_y - 40))
    elif near_door:
        txt = font_small.render("Press [E] to Hold Door", True, (255,255,0))
        screen.blit(txt, (player_x - 50, player_y - 40))
    elif near_door2:
        txt = font_small.render("Press [E] to Hold Door", True, (255,255,0))
        screen.blit(txt, (player_x - 50, player_y - 40))
    elif near_computer:
        txt = font_small.render("Press [E] to Use Computer", True, (255, 255, 0))
        screen.blit(txt, (player_x - 50, player_y - 40))
    if ghost_active:
        txt = font_small.render(f"GHOST: {ghost_target}", True, (255,0,0))
        screen.blit(txt, (10, 10))
    screen.blit(font_small.render(get_time_string(), True, (255, 255, 255)), (10, 30))
    draw_window_warning(window_progress)
    
    # Hour Intro Message
    if not hour_intro_shown:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        intro_text = hour_configs[current_hour]["intro_message"]
        intro_surf = font_large.render(intro_text, True, (255, 200, 100))
        screen.blit(intro_surf, (SCREEN_W//2 - intro_surf.get_width()//2, 250))
        
        press_text = font_small.render("Press any key to continue...", True, (200, 200, 200))
        screen.blit(press_text, (SCREEN_W//2 - press_text.get_width()//2, 400))


def render_window_state():
    if window_progress < 30:
        current_window_img = windowg0
    elif window_progress < 60:
        current_window_img = windowg30
    elif window_progress < 90:
        current_window_img = windowg70
    else:
        current_window_img = windowg99
    screen.blit(current_window_img, (0, 0))
    bar_color = (255, 200, 0)
    warning_text = None
    warning_color = None
    if 75 <= window_progress <= 90:
        warning_text = "WARNING"
        warning_color = (255, 255, 0)
        bar_color = (255, 180, 0)
    elif 91 <= window_progress < 100:
        warning_text = "DANGER"
        warning_color = (255, 0, 0)
        bar_color = (255, 120, 0)
    elif window_progress >= 100:
        warning_text = "ATTACK"
        warning_color = (255, 0, 0)
        bar_color = (255, 0, 0)
    pygame.draw.rect(screen, (50, 50, 50), (200, 530, 400, 25))
    pygame.draw.rect(screen, bar_color, (200, 530, int(window_progress * 4), 25))
    if warning_text:
        pygame.draw.rect(screen, (0, 0, 0), (620, 520, 170, 60))
        pygame.draw.rect(screen, warning_color, (632, 532, 36, 36))
        warn_surf = font_small.render(warning_text, True, warning_color)
        screen.blit(warn_surf, (675, 528))
        warn_pct = font_small.render(f"{int(window_progress)}%", True, warning_color)
        screen.blit(warn_pct, (675, 552))
    pygame.draw.rect(screen, button_color, button_rect)
    text_surf = font.render("HOLD", True, text_color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    screen.blit(text_surf, text_rect)
    txt = font_small.render("HOLD THE BUTTON TO CLOSE!", True, (255, 255, 255))
    screen.blit(txt, (250, 500))


def render_door_state():
    global shake_timer
    if charge_level <= 70:
        img = door1g
    else:
        img = door1
        
    shake_x, shake_y = 0, 0
    if shake_timer > 0:
        shake_x = random.randint(-10, 10)
        shake_y = random.randint(-10, 10)
        shake_timer -= 1
    screen.blit(img, (shake_x, shake_y))
    pygame.draw.circle(screen, (255, 0, 0), CIRCLE_POS, CIRCLE_RADIUS, 3)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    pygame.draw.circle(screen, (255, 50, 50), (int(mouse_x), int(mouse_y)), 5)
    pygame.draw.rect(screen, (50, 50, 50), (200, 530, 400, 25))
    pygame.draw.rect(screen, (0, 200, 0), (200, 530, int(charge_level * 4), 25))
    txt = font_small.render("KEEP CURSOR IN CIRCLE!", True, (255, 255, 255))
    screen.blit(txt, (250, 500))


def render_door2_state():
    global shake_timer
    img = door2 if door2_progress < 70 else door2g
    shake_x, shake_y = 0, 0
    if shake_timer > 0:
        shake_x = random.randint(-7, 7)
        shake_y = random.randint(-7, 7)
        shake_timer -= 1
    screen.blit(img, (shake_x, shake_y))
    pygame.draw.rect(screen, (50, 50, 50), (200, 530, 400, 25))
    pygame.draw.rect(screen, (200, 0, 0), (200, 530, int(door2_progress * 4), 25))
    txt = font_small.render("CLICK RAPIDLY TO HOLD THE WINDOW!", True, (255, 255, 255))
    screen.blit(txt, (230, 500))


def render_computer_state():
    global static_timer
    if ghost_active:
        state = "empty"
    elif current_cam == ghost_cctv_pos:
        if ghost_cctv_state == "near" and "ghost2" in cameras[current_cam]:
            state = "ghost2"
        else:
            state = "ghost"
    else:
        state = "empty"
    screen.blit(cameras[current_cam][state], (cam_offset_x, 0))
    scanline = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    for y in range(0, SCREEN_H, 3):
        pygame.draw.line(scanline, (255,255,255,20), (0,y), (SCREEN_W,y))
    offset_y = random.randint(-2, 2)
    screen.blit(scanline, (0,0))
    screen.blit(noise_img, (0, offset_y))
    if static_timer > 0:
        for _ in range(200):
            nx, ny = random.randint(0, SCREEN_W), random.randint(0, SCREEN_H)
            nc = random.randint(150, 255)
            pygame.draw.rect(screen, (nc, nc, nc), (nx, ny, 3, 3))
            static_timer -= 1
    screen.blit(font_small.render(f"LIVE: {current_cam}", True, (255, 0, 0)), (20, 20))
    screen.blit(font_small.render("Press [Q] to Exit", True, (255, 255, 255)), (20, SCREEN_H - 40))
    draw_window_warning(window_progress)
    screen.blit(map_img, (map_x, map_y))
    for btn in cctv_buttons:
        btn.draw(screen, btn.name == current_cam)
    


def render_idle_state(image):
    screen.blit(image, (0, 0))
    txt = font_small.render("Nothing here... (Q to exit)", True, (255,255,255))
    screen.blit(txt, (300, 500))
    draw_window_warning(window_progress)


def render_menu():
    global button_hour_menu
    screen.fill((0, 0, 0))
    title = font_large.render("The Intruder", True, (255, 255, 255))
    screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 50))
    
    if current_menu_page == "main":
        subtitle = font.render("Main Menu", True, (200, 200, 200))
        screen.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 150))
        
        # New Game Button
        pygame.draw.rect(screen, (100, 150, 100), button_new_game)
        text_new = font.render("New Game", True, (255, 255, 255))
        screen.blit(text_new, (button_new_game.centerx - text_new.get_width()//2, button_new_game.centery - text_new.get_height()//2))
        
        # Continue Button (only if unlocked more than hour 1)
        if max_unlocked_hour > 1:
            pygame.draw.rect(screen, (100, 100, 150), button_continue)
            text_cont = font.render(f"Continue (Hour {max_unlocked_hour})", True, (255, 255, 255))
            screen.blit(text_cont, (button_continue.centerx - text_cont.get_width()//2, button_continue.centery - text_cont.get_height()//2))
        else:
            pygame.draw.rect(screen, (50, 50, 50), button_continue)
            text_cont = font.render("Continue (Locked)", True, (100, 100, 100))
            screen.blit(text_cont, (button_continue.centerx - text_cont.get_width()//2, button_continue.centery - text_cont.get_height()//2))
    
    elif current_menu_page == "hour_select":
        subtitle = font.render("Select Hour", True, (200, 200, 200))
        screen.blit(subtitle, (SCREEN_W//2 - subtitle.get_width()//2, 150))
        
        # Generate hour selection buttons
        button_hour_menu = {}
        for hour_num in range(1, 6):
            x = 200 + (hour_num - 1) * 120
            y = 300
            btn = pygame.Rect(x, y, 100, 50)
            button_hour_menu[hour_num] = btn
            
            # Disable locked hours
            is_unlocked = hour_num <= max_unlocked_hour
            color = (100, 150, 100) if is_unlocked else (50, 50, 50)
            text_color = (255, 255, 255) if is_unlocked else (100, 100, 100)
            
            pygame.draw.rect(screen, color, btn)
            text = font_small.render(f"Hour {hour_num}", True, text_color)
            screen.blit(text, (btn.centerx - text.get_width()//2, btn.centery - text.get_height()//2))
        
        # Back button
        back_btn = pygame.Rect(350, 450, 100, 40)
        pygame.draw.rect(screen, (150, 100, 100), back_btn)
        text_back = font_small.render("Back", True, (255, 255, 255))
        screen.blit(text_back, (back_btn.centerx - text_back.get_width()//2, back_btn.centery - text_back.get_height()//2))


def render_game_over():
    screen.fill((0, 0, 0))
    if game_won:
        text = font_large.render(f"Hour {current_hour} Complete!", True, (0, 255, 0))
        if current_hour < 5:
            subtext2 = font_small.render(f"Hour {current_hour + 1} Unlocked!", True, (100, 255, 100))
        else:
            subtext2 = font_small.render("All Hours Complete!", True, (255, 200, 0))
    else:
        text = font_large.render("Game Over", True, (255, 0, 0))
        subtext2 = font_small.render("Try Again", True, (200, 100, 100))
    
    screen.blit(text, (SCREEN_W//2 - text.get_width()//2, 200))
    screen.blit(subtext2, (SCREEN_W//2 - subtext2.get_width()//2, 300))
    subtext = font.render("Press R to Menu or Q to Quit", True, (255, 255, 255))
    screen.blit(subtext, (SCREEN_W//2 - subtext.get_width()//2, 400))


def render_jumpscare_state():
    screen.blit(ghost_jump, (0, 0))


def render_state():
    if game_state == STATE_MAIN:
        render_main_state()
    elif game_state == STATE_WINDOW:
        render_window_state()
    elif game_state == STATE_DOOR:
        render_door_state()
    elif game_state == STATE_DOOR2:
        render_door2_state()
    elif game_state == STATE_COMPUTER:
        render_computer_state()
    elif game_state == STATE_DOOR2_IDLE:
        render_idle_state(door2)
    elif game_state == STATE_DOOR_IDLE:
        render_idle_state(door1)
    elif game_state == STATE_JUMPSCARE:
        render_jumpscare_state()
    elif game_state == STATE_MENU:
        render_menu()
    elif game_state == STATE_GAME_OVER:
        render_game_over()

map_data = [ #0=empty 1=floor 
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
decor_map = [ #0=empty 1=wall
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,3,0,1,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0],
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

tiles = { 1: get_tile(24, 0) }

walls_img = {
    1: get_tile(5, 0), 2: get_tile(24, 4), 3: get_tile(24, 4),
    4: get_tile(24, 4),5: get_tile(24, 4)
}

# --- Game Variables ---
player_size = 30
player_x, player_y = 400, 400
player_speed = 3
game_state = STATE_MENU
window_progress = 0
window_speed = 0.2
door2_progress = 40
door2_speed = 0.2
click_power = 1.5
jumpscare_timer = 0
shake_timer = 0
near_interact = False
near_window = False
near_door = False
near_door2 = False
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
button_rect = pygame.Rect(SCREEN_W//2 - 60, 440, 100, 50)
button_color = (200, 0, 0)
text_color = (255, 255, 255)
font = pygame.font.SysFont("Arial", 24)
# Pre-calculate Rects
wall_rects = []
window_rects = []
door_rects = []
door2_rects = []
computer_rects = []
for r, row in enumerate(decor_map):
    for c, val in enumerate(row):
        rect = pygame.Rect(c * DISPLAY_TILE, r * DISPLAY_TILE, DISPLAY_TILE, DISPLAY_TILE)
        if val in [1]:
            wall_rects.append(rect)
        if val in [5]:
            computer_rects.append(rect)
        if val in [4]:
            window_rects.append(rect)
        if val in [2]:
            door_rects.append(rect)
        if val in [3]:
            door2_rects.append(rect)
        

# Custom Events
GHOST_CCTV_MOVE = pygame.USEREVENT + 1
pygame.time.set_timer(GHOST_CCTV_MOVE, 7000)

# --- Main Loop ---
game_running = True
while game_running:
    screen.fill((0, 0, 0))
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