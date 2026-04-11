import pygame
import sys
import random

# ตั้งค่าหน้าจอ
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
IMAGE_WIDTH, IMAGE_HEIGHT = 1000, 600 

class CamButton:
    def __init__(self, name, x, y, width=60, height=30):
        self.name = name
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, screen, is_active):
        color = (255, 255, 255) if is_active else (50, 50, 50)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        font = pygame.font.SysFont("Arial", 12, bold=True)
        text_color = (0, 0, 0) if is_active else (255, 255, 255)
        text = font.render(self.name, True, text_color)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # --- 1. โหลดรูปภาพ (แก้ชื่อ CAM 5 ให้ถูกต้อง) ---
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
                cameras[cam_name][state_name] = pygame.transform.scale(img, (IMAGE_WIDTH, IMAGE_HEIGHT))
            except:
                dummy = pygame.Surface((IMAGE_WIDTH, IMAGE_HEIGHT))
                dummy.fill((100, 100, 100))
                cameras[cam_name][state_name] = dummy

    # --- 2. ระบบ Ghost AI & Nodes ---
    ghost_pos = "CAM 1" # ผีเริ่มที่ CAM 1
    # กำหนดเส้นทางที่ผีไปได้จากจุดต่างๆ
    ghost_nodes = {
        "CAM 1": ["CAM 2", "CAM 3"],
        "CAM 2": ["CAM 1", "CAM 4"],
        "CAM 3": ["CAM 1", "CAM 4", "CAM 5"],
        "CAM 4": ["CAM 2", "CAM 3", "CAM 5"],
        "CAM 5": ["CAM 3", "CAM 4"]
    }

    # ระบบสุ่มเวลาขยับ
    GHOST_MOVE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(GHOST_MOVE_EVENT, 5000) # ทุกๆ 5 วินาที ผีมีโอกาสขยับ

    static_timer = 0 # ตัวนับเวลา Noise
    noise_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # สำหรับวาด Noise

    # --- 3. UI & Layout ---
    map_x, map_y = 550, 400
    buttons = [
        CamButton("CAM 1", map_x + 0,   map_y + 0),
        CamButton("CAM 2", map_x + 120, map_y + 10),
        CamButton("CAM 3", map_x + 0,   map_y + 80),
        CamButton("CAM 4", map_x + 150, map_y + 80),
        CamButton("CAM 5", map_x + 80,  map_y + 140),
    ]

    current_cam = "CAM 1"
    cam_offset_x = 0

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == GHOST_MOVE_EVENT:
                # สุ่มว่าผีจะขยับไหม (เช่น โอกาส 50%)
                if random.random() > 0.5:
                    ghost_pos = random.choice(ghost_nodes[ghost_pos])
                    static_timer = 20 # ให้เกิด Noise 20 เฟรม
                    print(f"Ghost moved to {ghost_pos}")

            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(event.pos):
                        current_cam = btn.name
                        static_timer = 10 # เปลี่ยนกล้องแล้วมี Noise นิดๆ

        # ระบบ Panning
        if mouse_pos[0] < 100 and cam_offset_x < 0: cam_offset_x += 7
        elif mouse_pos[0] > SCREEN_WIDTH - 100 and cam_offset_x > (SCREEN_WIDTH - IMAGE_WIDTH): cam_offset_x -= 7

        # --- การวาดภาพ ---
        # เลือกรูป (มีผี หรือ ไม่มี)
        state = "ghost" if current_cam == ghost_pos else "empty"
        screen.blit(cameras[current_cam][state], (cam_offset_x, 0))

        # ระบบ Static Noise (วาดทับเมื่อมีการขยับหรือเปลี่ยนกล้อง)
        if static_timer > 0:
            for _ in range(500): # วาดจุดสุ่มสีเทา/ขาว
                nx, ny = random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)
                nc = random.randint(100, 255)
                pygame.draw.rect(screen, (nc, nc, nc), (nx, ny, 4, 4))
            static_timer -= 1

        # วาด Scanlines
        for i in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(screen, (0, 0, 0), (0, i), (SCREEN_WIDTH, i))

        # วาดแผนที่
        pygame.draw.rect(screen, (255, 255, 255), (map_x-10, map_y-10, 230, 190), 2)
        for btn in buttons:
            btn.draw(screen, btn.name == current_cam)

        # UI Text
        font = pygame.font.SysFont("Courier", 30, bold=True)
        screen.blit(font.render(f"LIVE: {current_cam}", True, (255, 0, 0)), (20, 20))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()