import sounddevice as sd
import numpy as np
from pygame import *
from random import randint

# ===== AUDIO =====
sr = 16000
block = 250
mic_level = 0.0  # поточний рівень гучності (згладжений)

def audio_cb(indata, frames, time, status):
    global mic_level
    if status:
        return
    rms = float(np.sqrt(np.mean(indata ** 2)))
    mic_level = 0.85 * mic_level + 0.15 * rms

# ===== PYGAME INIT =====
init()
window_size = (1200, 800)
window = display.set_mode(window_size)
display.set_caption("Flappy Bird (Voice Control)")
clock = time.Clock()

# ===== LOAD IMAGES =====
background_img = image.load("background.png").convert()
background_img = transform.scale(background_img, window_size)  # растягнути на весь екран
icon_img = image.load("icon.png").convert_alpha()
pipe_top_img = image.load("pipe_top.png").convert_alpha()
pipe_bottom_img = image.load("pipe_bottom.png").convert_alpha()

player_rect = Rect(150, 300, icon_img.get_width(), icon_img.get_height())

# ===== PIPES =====
def generate_pipes(count, pipe_width=140, gap=280,
                   min_height=50, max_height=440, distance=650):
    pipes = []
    start_x = window_size[0]

    for _ in range(count):
        height = randint(min_height, max_height)
        top_pipe = Rect(start_x, 0, pipe_width, height)
        bottom_pipe = Rect(
            start_x,
            height + gap,
            pipe_width,
            window_size[1] - (height + gap)
        )
        pipes.extend([top_pipe, bottom_pipe])
        start_x += distance

    return pipes

# ===== GAME VARS =====
pipes = generate_pipes(150)
main_font = font.Font(None, 100)

score = 0
lose = False
wait = 40

y_vel = 0.0
gravity = 0.6

THRESH = 0.001     # поріг спрацювання "стрибка"
IMPULSE = -8.0     # сила стрибка вгору

# ===== MAIN LOOP (WITH AUDIO STREAM) =====
with sd.InputStream(
        samplerate=sr,
        channels=1,
        blocksize=block,
        callback=audio_cb):

    while True:
        for e in event.get():
            if e.type == QUIT:
                quit()

        # ===== LOGIC =====
        if mic_level > THRESH:
            y_vel = IMPULSE

        y_vel += gravity
        player_rect.y += int(y_vel)

        # ===== DRAW =====
        window.blit(background_img, (0, 0))  # фон
        window.blit(icon_img, (player_rect.x, player_rect.y))  # гравець

        for pipe in pipes[:]:
            if not lose:
                pipe.x -= 10

            if pipe.y == 0:
                # верхня труба (перевертаємо)
                img = transform.scale(pipe_top_img, (pipe.width, pipe.height))
                img = transform.flip(img, False, True)
            else:
                # нижня труба
                img = transform.scale(pipe_bottom_img, (pipe.width, pipe.height))

            window.blit(img, (pipe.x, pipe.y))

            if pipe.x <= -100:
                pipes.remove(pipe)
                score += 0.5

            if player_rect.colliderect(pipe):
                lose = True

        if len(pipes) < 8:
            pipes += generate_pipes(150)

        # ===== SCORE =====
        score_text = main_font.render(f"{int(score)}", True, "black")
        window.blit(
            score_text,
            (window_size[0] // 2 - score_text.get_width() // 2, 40)
        )

        # ===== BOUNDS =====
        if player_rect.bottom > window_size[1]:
            player_rect.bottom = window_size[1]
            y_vel = 0.0

        if player_rect.top < 0:
            player_rect.top = 0
            if y_vel < 0:
                y_vel = 0.0

        # ===== RESET =====
        keys = key.get_pressed()
        if keys[K_r] and lose:
            lose = False
            score = 0
            pipes = generate_pipes(150)
            player_rect.y = window_size[1] // 2 - icon_img.get_height() // 2
            y_vel = 0.0

        if lose and wait > 1:
            for pipe in pipes:
                pipe.x += 8
            wait -= 1
        else:
            lose = False
            wait = 40

        display.update()
        clock.tick(60)
