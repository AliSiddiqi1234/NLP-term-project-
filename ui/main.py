import pygame
import sys
import random
import math
import threading
import speech_recognition as sr
from pathlib import Path

# Add parent directory to path to import nlp module
sys.path.append(str(Path(__file__).parent.parent))
try:
    from nlp import parse_command
except ImportError:
    print("Warning: Could not import nlp module, using fallback parser")

    # Fallback simple parser
    ACTION_KEYWORDS = {
        "move": ["move", "push", "slide", "shift", "go"],
        "pick": ["pick", "grab", "lift"],
        "place": ["place", "put", "drop", "set"],
    }

    COLORS = ["red", "blue", "green", "yellow", "purple", "orange", "gray"]
    SHAPES = ["block", "circle", "triangle"]

    def parse_command(text):
        text_lower = text.lower()

        # Detect action
        action = None
        for act, verbs in ACTION_KEYWORDS.items():
            for verb in verbs:
                if verb in text_lower:
                    action = act
                    break
            if action:
                break

        # Detect colors and shapes
        color = None
        shape = None
        for c in COLORS:
            if c in text_lower:
                color = c
                break
        for s in SHAPES:
            if s in text_lower:
                shape = s
                break

        return {
            "action": action,
            "object": {"color": color, "shape": shape} if (color or shape) else None,
            "relation": None,
            "ref_object": None,
            "modifier": None,
        }


RELATION_KEYWORDS = {
    "left_of": ["left of", "to the left of", "on the left of", "left"],
    "right_of": ["right of", "to the right of", "on the right of", "right"],
    "behind": ["behind", "back"],
    "in_front_of": ["in front of", "front"],
    "on_top_of": ["on top of", "over"],
}

MODIFIER_KEYWORDS = {
    "closest": ["closest", "closest to", "near", "nearest"],
    "farthest": ["farthest", "farthest from", "far"],
}

COLORS = ["red", "blue", "green", "yellow", "purple", "orange", "gray"]
SHAPES = ["block", "circle", "triangle"]


def simple_parse_command(text):
    """Simplified NLP parser for game commands"""
    text_lower = text.lower()

    # Detect action
    action = None
    for act, verbs in ACTION_KEYWORDS.items():
        for verb in verbs:
            if verb in text_lower:
                action = act
                break
        if action:
            break

    # Detect colors
    color = None
    for c in COLORS:
        if c in text_lower:
            color = c
            break

    # Detect shapes
    shape = None
    for s in SHAPES:
        if s in text_lower:
            shape = s
            break

    # Detect relations
    relation = None
    for rel, patterns in RELATION_KEYWORDS.items():
        for pattern in patterns:
            if pattern in text_lower:
                relation = rel
                break
        if relation:
            break

    # Detect modifiers
    modifier = None
    for mod, patterns in MODIFIER_KEYWORDS.items():
        for pattern in patterns:
            if pattern in text_lower:
                modifier = mod
                break
        if modifier:
            break

    # Extract reference object (second color/shape mentioned)
    ref_color = None
    ref_shape = None
    words = text_lower.split()

    # Find first occurrence of each type
    first_color_idx = -1
    first_shape_idx = -1

    for i, word in enumerate(words):
        if word in COLORS and first_color_idx == -1:
            first_color_idx = i
        elif word in SHAPES and first_shape_idx == -1:
            first_shape_idx = i

    # Find second occurrence for reference
    for i, word in enumerate(words):
        if word in COLORS and i != first_color_idx and not ref_color:
            ref_color = word
        elif word in SHAPES and i != first_shape_idx and not ref_shape:
            ref_shape = word

    primary_obj = {"color": color, "shape": shape} if (color or shape) else None
    ref_obj = (
        {"color": ref_color, "shape": ref_shape} if (ref_color or ref_shape) else None
    )

    return {
        "action": action,
        "object": primary_obj,
        "relation": relation,
        "ref_object": ref_obj,
        "modifier": modifier,
    }


# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 30
OBJECT_SIZE = 25
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)

COLOR_MAP = {
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "gray": (128, 128, 128),
}
# COLOR_MAP = {
#     "red": RED,
#     "blue": BLUE,
#     "green": GREEN,
#     "yellow": YELLOW,
#     "purple": PURPLE,
#     "orange": ORANGE,
#     "gray": GRAY,
# }


class GameObject:
    def __init__(self, x, y, color, shape="block"):
        self.x = x
        self.y = y
        self.color = color
        self.shape = shape
        self.size = OBJECT_SIZE

    def update_pos(self, x, y):
        self.x = x
        self.y = y

    def draw(self, screen):
        if self.shape == "block":
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
        elif self.shape == "circle":
            pygame.draw.circle(
                screen,
                self.color,
                (self.x + self.size // 2, self.y + self.size // 2),
                self.size // 2,
            )
        elif self.shape == "triangle":
            points = [
                (self.x + self.size // 2, self.y),
                (self.x, self.y + self.size),
                (self.x + self.size, self.y + self.size),
            ]
            pygame.draw.polygon(screen, self.color, points)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def get_center(self):
        return (self.x + self.size // 2, self.y + self.size // 2)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.color = WHITE
        self.speed = 5
        self.held_object = None

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.size, self.size), 2)
        if self.held_object:
            pygame.draw.rect(
                screen, (0, 255, 0), (self.x, self.y, self.size, self.size), 2
            )

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Keep player on screen
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.size))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.size))
        if self.held_object:
            self.held_object.update_pos(self.x + 5, self.y + 5)

    def pick_up(self, obj):
        self.held_object = obj

    def drop(self):
        self.held_object = None

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def get_center(self):
        return (self.x + self.size // 2, self.y + self.size // 2)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("NLP Controlled Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.input_font = pygame.font.Font(None, 20)

        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.objects = self.create_objects()
        self.input_text = ""
        self.input_active = True
        self.last_command = ""
        self.message = ""
        self.message_timer = 0

        self.auto_target = None
        self.auto_action = None

        self.recognizer = sr.Recognizer()
        self.voice_thread = None

    def create_objects(self):
        objects = []
        colors = ["red", "blue", "green", "yellow", "purple"]
        shapes = ["block", "circle", "triangle"]

        for i in range(8):
            x = random.randint(50, SCREEN_WIDTH - 100)
            y = random.randint(50, SCREEN_HEIGHT - 100)
            color = random.choice(colors)
            shape = random.choice(shapes)

            # Make sure objects don't overlap with player starting position
            while abs(x - SCREEN_WIDTH // 2) < 50 and abs(y - SCREEN_HEIGHT // 2) < 50:
                x = random.randint(50, SCREEN_WIDTH - 100)
                y = random.randint(50, SCREEN_HEIGHT - 100)

            objects.append(GameObject(x, y, COLOR_MAP[color], shape))

        return objects

    def start_voice_input(self):
        if self.voice_thread and self.voice_thread.is_alive():
            return
        self.voice_thread = threading.Thread(target=self._voice_listen)
        self.voice_thread.start()

    def _voice_listen(self):
        with sr.Microphone() as source:
            self.message = "Listening..."
            self.message_timer = 120
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                self.message = f"Recognized: {text[:30]}..."
                self.message_timer = 120
                self.execute_nlp_command(text)
            except sr.WaitTimeoutError:
                self.message = "No speech detected"
                self.message_timer = 120
            except sr.UnknownValueError:
                self.message = "Could not understand"
                self.message_timer = 120
            except sr.RequestError:
                self.message = "Speech service error"
                self.message_timer = 120

    # TODO improve
    def find_object_by_description(self, obj_desc):
        if not obj_desc:
            return None

        matching_objects = []
        for obj in self.objects:
            match = True

            if obj_desc.get("color"):
                color_name = None
                for name, color in COLOR_MAP.items():
                    if color == obj.color:
                        color_name = name
                        break
                if color_name != obj_desc["color"].lower():
                    match = False

            if obj_desc.get("shape"):
                if obj.shape != obj_desc["shape"].lower():
                    match = False

            if match:
                matching_objects.append(obj)

        return matching_objects

    def resolve_chain(self, chain):
        """
        Solves: [Blue, Red, Robot]
        1. Ref = Robot
        2. Find Red closest to Ref -> Result: specific Red Block
        3. Ref = that Red Block
        4. Find Blue closest to Ref -> Result: specific Blue Block
        """
        current_ref_pos = self.player.get_center()

        # Reverse list to process from Anchor (Robot) up to Target
        # Chain comes in as [Target, Intermediate, Anchor] usually
        # But nlp.py output depends on order. Let's assume input is [Target, Ref1, Ref2]
        # We need to process Ref2 -> Ref1 -> Target

        processed_target = None

        # Reverse the chain so we start with the last mentioned object (usually the anchor)
        for i in range(len(chain) - 1, -1, -1):
            desc = chain[i]

            # If explicit "robot", reset anchor to player
            if desc.get("color") == "you" or desc.get("shape") == "robot":
                current_ref_pos = self.player.get_center()
                continue

            candidates = self.find_object_by_description(desc)
            if not candidates:
                return None

            # Sort candidates by distance to current reference
            candidates.sort(key=lambda o: math.dist(o.get_center(), current_ref_pos))

            # The closest one becomes the reference for the NEXT iteration
            processed_target = candidates[0]
            current_ref_pos = processed_target.get_center()

        return processed_target

    def find_closest_object(self, objects, reference_point):
        if not objects:
            return None

        closest = None
        min_distance = float("inf")

        for obj in objects:
            dist = (
                (obj.get_center()[0] - reference_point[0]) ** 2
                + (obj.get_center()[1] - reference_point[1]) ** 2
            ) ** 0.5
            if dist < min_distance:
                min_distance = dist
                closest = obj

        return closest

    def find_farthest_object(self, objects, reference_point):
        if not objects:
            return None

        farthest = None
        max_distance = 0

        for obj in objects:
            dist = (
                (obj.get_center()[0] - reference_point[0]) ** 2
                + (obj.get_center()[1] - reference_point[1]) ** 2
            ) ** 0.5
            if dist > max_distance:
                max_distance = dist
                farthest = obj

        return farthest

    def execute_nlp_command(self, command_text):
        try:
            parsed = parse_command(command_text)
            self.last_command = str(parsed)

            action = parsed.get("action")
            if not action:
                self.message = "No action detected"
                self.message_timer = 120
                return

            # 1. HANDLE DROP/PLACE
            if action == "place":
                if self.player.drop():
                    self.message = "Dropped object"
                else:
                    self.message = "Not holding anything!"
                return

            # 2. RESOLVE TARGET (Smart Lookup)
            target_obj = None
            if parsed.get("object_chain") and len(parsed["object_chain"]) > 0:
                target_obj = self.resolve_chain(parsed["object_chain"])
            elif parsed.get("object"):
                # Fallback if chain is empty/simple
                objs = self.find_object_by_description(parsed["object"])
                if objs:
                    target_obj = objs[0]  # Default to first match if simple

            # 3. DECIDE MOVEMENT TYPE
            if target_obj:
                # --- A. OBJECT FOUND: PATHFINDING (Auto-Pilot) ---
                if action == "pick":
                    self.auto_target = target_obj
                    self.auto_action = "pick"
                    self.message = (
                        f"Picking up {target_obj.color} {target_obj.shape}..."
                    )
                elif action == "move":
                    self.auto_target = target_obj
                    self.auto_action = "move"
                    self.message = f"Moving to {target_obj.color} {target_obj.shape}..."

            else:
                relation = parsed.get("relation")

                if relation == "left_of":
                    self.player.move(-20, 0)
                    self.message = "Moving Left"
                elif relation == "right_of":
                    self.player.move(20, 0)
                    self.message = "Moving Right"
                elif relation == "in_front_of":  # "Up" in 2D
                    self.player.move(0, -20)
                    self.message = "Moving Up"
                elif relation == "behind":  # "Down" in 2D
                    self.player.move(0, 20)
                    self.message = "Moving Down"
                else:
                    if action == "move":
                        self.message = "Move where? (Left, Right, or name an object)"
                    else:
                        self.message = "I couldn't find that object."

        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.message_timer = 120
            print(f"Error executing command: {e}")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                # 1. Handle Enter Key (Send Command)
                if event.key == pygame.K_RETURN:
                    if self.input_text.strip():
                        print(f"Sending: {self.input_text}")  # Debug print
                        self.execute_nlp_command(self.input_text)
                        self.input_text = ""  # Clear input box

                # 2. Handle Backspace (Delete Character)
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]

                # 3. Handle Escape (Clear Input)
                elif event.key == pygame.K_ESCAPE:
                    self.input_text = ""

                # 4. Handle Voice Input (Ctrl+V)
                elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                    self.start_voice_input()

                # 5. Handle Normal Typing
                else:
                    self.input_text += event.unicode
        return True

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        # Auto-Pilot Logic
        if self.auto_target:
            t_pos = self.auto_target.get_center()
            p_pos = self.player.get_center()

            # Calculate distance
            dx = t_pos[0] - p_pos[0]
            dy = t_pos[1] - p_pos[1]
            dist = math.sqrt(dx**2 + dy**2)

            if dist < 10:  # We arrived
                if self.auto_action == "pick":
                    self.player.pick_up(self.auto_target)
                    self.message = "Picked up!"
                self.auto_target = None
                self.auto_action = None
            else:
                # Normalize and move
                speed = 5
                self.player.move((dx / dist), (dy / dist))

    def draw(self):
        self.screen.fill(BLACK)

        # Draw objects
        for obj in self.objects:
            obj.draw(self.screen)

        # Draw player
        self.player.draw(self.screen)

        # Draw UI
        y_offset = 10

        # Title
        title_text = self.font.render("NLP Controlled Game", True, WHITE)
        self.screen.blit(title_text, (10, y_offset))
        y_offset += 30

        # Instructions
        inst_text = self.input_font.render(
            "Press ENTER to type command, Ctrl+V for voice, arrow keys to move manually",
            True,
            WHITE,
        )
        self.screen.blit(inst_text, (10, y_offset))
        y_offset += 25

        # Input field
        input_color = WHITE if self.input_active else GRAY
        input_label = self.input_font.render("Command:", True, input_color)
        self.screen.blit(input_label, (10, y_offset))

        input_surface = self.input_font.render(self.input_text, True, input_color)
        self.screen.blit(input_surface, (80, y_offset))

        if self.input_active:
            pygame.draw.line(
                self.screen,
                WHITE,
                (80 + input_surface.get_width(), y_offset),
                (80 + input_surface.get_width() + 5, y_offset),
                2,
            )

        y_offset += 30

        # Last command
        if self.last_command:
            cmd_text = self.input_font.render(
                f"Last: {self.last_command[:50]}...", True, GRAY
            )
            self.screen.blit(cmd_text, (10, y_offset))
            y_offset += 25

        # Message
        if self.message_timer > 0:
            msg_text = self.font.render(self.message, True, YELLOW)
            self.screen.blit(msg_text, (10, y_offset))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
