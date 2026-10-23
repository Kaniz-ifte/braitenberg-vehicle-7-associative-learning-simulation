# source ~/braitenberg-env/bin/activate 
# python vehicle7_base.py

import pygame
import math

pygame.init()

# Setup Pygame window
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Braitenberg Vehicle 7 - Concepts & Association")

# Setup clock for controlling frame rate / fps = frame per second
clock = pygame.time.Clock()
fps = 60  

# Setup font for debug info
font = pygame.font.SysFont("consolas", 16)


# ── Mnemotrix Wire (Hebbian learning connection) ───────────────────────────────
class MnemotrixWire:
    """
    Strengthens when both connected nodes fire simultaneously.
    Decays slowly when they don't co-activate.
    This gives the vehicle associative memory (learning).
    """
    def __init__(self, learn_rate=0.015, decay_rate=0.0005):
        self.weight     = 0.0
        self.learn_rate = learn_rate
        self.decay_rate = decay_rate

    def update(self, pre_active, post_active):
        if pre_active and post_active:    #Red detector = "True" & Motor neuron = "True" then Learn
            self.weight = min(1.0, self.weight + self.learn_rate)
        else:
            self.weight = max(0.0, self.weight - self.decay_rate)

    @property
    def strength(self):
        return self.weight


# ── Threshold Device (artificial neuron) ──────────────────────────────────────
class ThresholdDevice:
    """
    Fires +1 (excitatory) or -1 (inhibitory) when activation crosses threshold.
    Uses leaky integration so recent history matters (short-term memory).
    """
    def __init__(self, threshold=0.45, inhibitory=False):
        self.threshold   = threshold
        self.inhibitory  = inhibitory
        self._activation = 0.0
        self._output     = 0.0

    def update(self, inputs):
        # inputs: list of (value, weight) tuples
        total = sum(v * w for v, w in inputs)
        # Leaky integration: remember recent signals, without leaky 
        # current, the vehicle would only react to the most recent light intensity, 
        # which could make its behavior erratic. By integrating over time, 
        # it can respond more smoothly to changes in light intensity.
        self._activation = 0.65 * self._activation + 0.35 * total 
        raw = 1.0 if self._activation >= self.threshold else 0.0
        if self.inhibitory:
            raw = -raw
        self._output = raw

    @property
    def output(self):
        return self._output

    @property
    def activation(self):
        return self._activation


# ── Vehicle 7 ─────────────────────────────────────────────────────────────────


 
class Vehicle:
    def __init__(self, x, y, radius=20, heading=0):
        # Vehicle state
        self.x = x
        self.y = y
        self.radius = radius
        self.heading = heading  #Which direction is the vehicle facing?

        # Sensor configuration
        self.sensor_offset_angle = math.radians(30)  # Angle of sensors relative to vehicle heading
        self.sensor_dist = self.radius

        # ── Vehicle 7 brain ──
        # Threshold devices
        self.td_danger_l  = ThresholdDevice(threshold=0.4)               # red left sensor
        self.td_danger_r  = ThresholdDevice(threshold=0.4)               # red right sensor
        self.td_neutral_l = ThresholdDevice(threshold=0.4)               # blue left sensor
        self.td_neutral_r = ThresholdDevice(threshold=0.4)               # blue right sensor
        self.td_motor_l   = ThresholdDevice(threshold=0.5, inhibitory=True)  # left motor driver
        self.td_motor_r   = ThresholdDevice(threshold=0.5, inhibitory=True)  # right motor driver

        # Mnemotrix wires: connect danger ↔ neutral sensors
        self.mw_left  = MnemotrixWire()   # danger-L ↔ neutral-L
        self.mw_right = MnemotrixWire()   # danger-R ↔ neutral-R

        # Store for debug display
        self.intensity_left  = 0.0  #store how much total light the left sensor currently sees.
        self.intensity_right = 0.0
        self.left_motor_speed  = 1.0
        self.right_motor_speed = 1.0

    # Calculate sensor positions based on vehicle position and heading
    def _sensor_positions(self):
        angle    = self.sensor_offset_angle
        distance = self.sensor_dist

        left_local_x  = math.cos(+angle) * distance  # x = r * cos (theta)
        left_local_y  = math.sin(+angle) * distance
        right_local_x = math.cos(-angle) * distance
        right_local_y = math.sin(-angle) * distance

        cos_heading = math.cos(self.heading)
        sin_heading = math.sin(self.heading)
        
        #For a point (x,y) rotated by angle θ,the new coordinates are 
        # new_x = cosθ × x − sinθ × y 
        # new_y = sinθ × x + cosθ × y
        left_world_x  = self.x + cos_heading * left_local_x  - sin_heading * left_local_y  #This converts the sensor position relative to vehicle into actual screen coordinates
        left_world_y  = self.y + sin_heading * left_local_x  + cos_heading * left_local_y
        right_world_x = self.x + cos_heading * right_local_x - sin_heading * right_local_y
        right_world_y = self.y + sin_heading * right_local_x + cos_heading * right_local_y

        return (left_world_x, left_world_y), (right_world_x, right_world_y)

    # Calculate intensity of a light source at a given sensor point
    def _intensity_at(self, point_x, point_y, light_x, light_y):
        # Inverse-square law: brighter when closer
        d2 = (point_x - light_x) ** 2 + (point_y - light_y) ** 2 + 1e-6
        return min(1.0, 5000.0 / d2)

    # Aggregate intensities from multiple sources of a given type
    def _sense_type(self, sensor_x, sensor_y, lights, color_key):
        total = 0.0
        for light in lights:
            if light.color_key == color_key:
                total += self._intensity_at(sensor_x, sensor_y, light.x, light.y)
        return min(total, 1.0)  #neurons are designed to work with values between 0 and 1.

    def update(self, lights):
        left_sensor, right_sensor = self._sensor_positions()

        # Sense each stimulus type separately
        red_l  = self._sense_type(left_sensor[0],  left_sensor[1],  lights, 'red')  #calculate intensity of red light in the left sensor 
        red_r  = self._sense_type(right_sensor[0], right_sensor[1], lights, 'red')
        blue_l = self._sense_type(left_sensor[0],  left_sensor[1],  lights, 'blue')
        blue_r = self._sense_type(right_sensor[0], right_sensor[1], lights, 'blue')

        self.intensity_left  = red_l + blue_l
        self.intensity_right = red_r + blue_r

        # Mnemotrix learned association: blue drives danger pathway
        # proportional to how strong the wire has grown
        assoc_l = self.mw_left.strength  * blue_l  # mw_left.strength is the output(weight) of MnemotrixWire, which is a value between 0 and 1. It represents how much the vehicle has learned to associate blue light with danger on the left side.
        assoc_r = self.mw_right.strength * blue_r

        # Update threshold devices
        self.td_danger_l.update( [(red_l,  1.0)])
        self.td_danger_r.update( [(red_r,  1.0)])
        self.td_neutral_l.update([(blue_l, 1.0)])
        self.td_neutral_r.update([(blue_r, 1.0)])

        # Motor inhibitors: activated by direct danger OR learned association
        self.td_motor_l.update([(self.td_danger_l.output, 1.0), (assoc_l, 1.0)])
        self.td_motor_r.update([(self.td_danger_r.output, 1.0), (assoc_r, 1.0)])

        # Hebbian learning: strengthen wire when danger & neutral fire together
        self.mw_left.update(
            self.td_danger_l.output > 0,
            self.td_neutral_l.output > 0
        )
        self.mw_right.update(
            self.td_danger_r.output > 0,
            self.td_neutral_r.output > 0
        )

        # Motor speeds:
        # Base speed + inhibitory output (-1 when danger detected → slows down)
        # Also: mild attraction to unconditioned blue (fades as wire strengthens)
        # The vehicle is almost always moving forward. It turns away when one motor becomes slower than the other. 
        # It only slows down (or stops) when both motors become slow together.
        base_speed = 2.0
        uncond_blue_l = blue_l * (1.0 - self.mw_left.strength)
        uncond_blue_r = blue_r * (1.0 - self.mw_right.strength)

        left_motor_speed  = max(0.3, base_speed
                                + self.td_motor_l.output * 3.5
                                + uncond_blue_r * 1.5)
        right_motor_speed = max(0.3, base_speed
                                + self.td_motor_r.output * 3.5
                                + uncond_blue_l * 1.5)
        ''''
        If we don't use 0.3 as a minimum speed, the vehicle can get stuck
        in a "dead zone" where both motors are inhibited and it doesn't move at all. 
        This ensures it always has some forward motion.'''''
        # left_motor_speed  = base_speed + self.td_motor_l.output * 3.5 + uncond_blue_r * 1.5
        # right_motor_speed = base_speed + self.td_motor_r.output * 3.5 + uncond_blue_l * 1.5

        self.left_motor_speed  = left_motor_speed
        self.right_motor_speed = right_motor_speed

        # Differential steering
        forward_speed = (left_motor_speed + right_motor_speed) / 2.0
        turning_rate  = (right_motor_speed - left_motor_speed) / (2.0 * self.radius)

        # Update vehicle position and heading
        self.heading += turning_rate * 0.15
        self.x += forward_speed * math.cos(self.heading) * 0.75
        self.y += forward_speed * math.sin(self.heading) * 0.75

        self.x %= WIDTH
        self.y %= HEIGHT

    def draw(self, surface):
        pygame.draw.circle(surface, (0, 0, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (0, 0, 0),   (int(self.x), int(self.y)), self.radius, 2)

        left_sensor, right_sensor = self._sensor_positions()
        pygame.draw.circle(surface, (255, 0, 0),   (int(left_sensor[0]),  int(left_sensor[1])),  5)
        pygame.draw.circle(surface, (255, 0, 0),   (int(right_sensor[0]), int(right_sensor[1])), 5)

        # Debug info
        if font:
            surface.blit(font.render(
                f"Speed=L:{self.left_motor_speed:.2f} R:{self.right_motor_speed:.2f}",
                True, (255, 255, 255)), (10, 10))
            surface.blit(font.render(
                f"Left={self.intensity_left:.2f}  Right={self.intensity_right:.2f}",
                True, (255, 255, 255)), (10, 30))
            surface.blit(font.render(
                f"Mnemotrix L={self.mw_left.strength:.2f}  R={self.mw_right.strength:.2f}",
                True, (255, 255, 255)), (10, 50))
            surface.blit(font.render(
                f"MotorTD L={self.td_motor_l.output:+.0f}  R={self.td_motor_r.output:+.0f}",
                True, (255, 255, 255)), (10, 70))


# ── Light source ───────────────────────────────────────────────────────────────
class Light:
    def __init__(self, x, y, radius=10, color_key='red'):
        self.x, self.y   = x, y
        self.radius      = radius
        self.color_key   = color_key  # 'red' = danger, 'blue' = neutral
        self.draw_color  = (220, 50, 50) if color_key == 'red' else (60, 130, 220)
        # self.draw_color  = (253, 216, 8) if color_key == 'yellow' else (60, 130, 220)

    def move_light(self, new_position):
        self.x, self.y = new_position

    def pos(self):
        return (self.x, self.y)

    def draw(self, surface):
        pygame.draw.circle(surface, self.draw_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (0, 0, 0),       (int(self.x), int(self.y)), self.radius, 2)


# ── Instructions overlay ───────────────────────────────────────────────────────
def draw_instructions(surface):
    lines = [
        "Left-click : place RED (danger) light",
        "Right-click: place BLUE (neutral) light",
        "R: reset vehicle   ESC: quit",
    ]
    for i, line in enumerate(lines):
        surface.blit(font.render(line, True, (255, 255, 255)), (10, HEIGHT - 60 + i * 18))


# ── Create instances ───────────────────────────────────────────────────────────
# One danger (red) and one neutral (blue) light, placed near each other
# so the vehicle quickly learns to associate them
# lights = [
#     Light(WIDTH // 2,       HEIGHT // 3,       radius=15, color_key='red'),
#     Light(WIDTH // 2 + 80,  HEIGHT // 3 + 40,  radius=15, color_key='blue'),
# ]
lights = []
vehicle = Vehicle(WIDTH // 2 - 150, HEIGHT // 2, radius=20, heading=0)

running = True
while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Left-click: place red (danger) light
        # Right-click: place blue (neutral) light
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                lights.append(Light(event.pos[0], event.pos[1], radius=15, color_key='red'))
            elif event.button == 3:
                lights.append(Light(event.pos[0], event.pos[1], radius=15, color_key='blue'))

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                vehicle = Vehicle(WIDTH // 2 - 150, HEIGHT // 2, radius=20, heading=0)
                lights  = [
                    # Light(WIDTH // 2,      HEIGHT // 3,      radius=15, color_key='red'),
                    # Light(WIDTH // 2 + 80, HEIGHT // 3 + 40, radius=15, color_key='blue'),
                ]
            elif event.key == pygame.K_ESCAPE:
                running = False

    # Draw light sources
    for light in lights:
        light.draw(screen)

    # Update and draw vehicle
    vehicle.update(lights)
    vehicle.draw(screen)

    draw_instructions(screen)

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()

# Light                                           
#    │
#    ▼
# Sensor
# (red = 0.8)

#    │
#    ▼
# ThresholdDevice.update()

# inputs = [
#     (0.8, 1.0)
# ]

#         │
#         ▼
# total = 0.8×1.0

#         │
#         ▼
# activation

#         │
#         ▼
# output (0 or 1)

#         │
#         ▼
# Motor Threshold Device

# inputs = [
#     (danger_output,1.0),
#     (learned_association,1.0)
# ]

#         │
#         ▼
# Motor speed

    #                 LEFT SENSOR
    #              /               \
    #       red_l                   blue_l
    #         |                       |
    #         v                       v
    #  td_danger_l            td_neutral_l
    #         |                       |
    #         |<---- Mnemotrix -------|
    #         |
    #     assoc_l
    #         |
    #         --------------------
    #                            |
    #                            v
    #                      td_motor_l
    #                            |
    #                            |
    #                      Left wheel

    #                 RIGHT SENSOR
    #              /                \
    #       red_r                    blue_r
    #         |                        |
    #         v                        v
    #  td_danger_r             td_neutral_r
    #         |                        |
    #         |<---- Mnemotrix --------|
    #         |
    #     assoc_r
    #         |
    #         --------------------
    #                            |
    #                            v
    #                      td_motor_r
    #                            |
    #                            |
    #                     Right wheel