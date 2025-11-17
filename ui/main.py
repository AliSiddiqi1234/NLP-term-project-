import pygame
import sys
import random
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
    "red": RED,
    "blue": BLUE,
    "green": GREEN,
    "yellow": YELLOW,
    "purple": PURPLE,
    "orange": ORANGE,
    "gray": GRAY,
}


class GameObject:
    def __init__(self, x, y, color, shape="block"):
        self.x = x
        self.y = y
        self.color = color
        self.shape = shape
        self.size = OBJECT_SIZE

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

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.size, self.size), 2)

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

        # Keep player on screen
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.size))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.size))

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
        self.input_active = False
        self.last_command = ""
        self.message = ""
        self.message_timer = 0

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

            if not parsed["action"]:
                self.message = "No action detected"
                self.message_timer = 120
                return

            # Handle movement commands
            if parsed["action"] == "move":
                if parsed["object"]:
                    target_objects = self.find_object_by_description(parsed["object"])
                    if target_objects:
                        target_obj = target_objects[0]

                        # Apply modifiers
                        if parsed["modifier"] == "closest" and parsed["ref_object"]:
                            ref_objects = self.find_object_by_description(
                                parsed["ref_object"]
                            )
                            if ref_objects:
                                target_obj = self.find_closest_object(
                                    target_objects, ref_objects[0].get_center()
                                )
                        elif parsed["modifier"] == "farthest" and parsed["ref_object"]:
                            ref_objects = self.find_object_by_description(
                                parsed["ref_object"]
                            )
                            if ref_objects:
                                target_obj = self.find_farthest_object(
                                    target_objects, ref_objects[0].get_center()
                                )

                        if target_obj:
                            # Move player towards target
                            dx = (
                                target_obj.get_center()[0] - self.player.get_center()[0]
                            )
                            dy = (
                                target_obj.get_center()[1] - self.player.get_center()[1]
                            )
                            distance = (dx**2 + dy**2) ** 0.5

                            if distance > 0:
                                # Normalize and apply movement
                                move_distance = min(distance, 50)  # Move in steps
                                dx = (dx / distance) * move_distance
                                dy = (dy / distance) * move_distance
                                self.player.move(dx, dy)

                                self.message = f"Moving towards {parsed['object']}"
                                self.message_timer = 120
                    else:
                        self.message = f"Object not found: {parsed['object']}"
                        self.message_timer = 120
                else:
                    # Simple directional movement based on relation
                    if parsed["relation"] == "left_of":
                        self.player.move(-30, 0)
                    elif parsed["relation"] == "right_of":
                        self.player.move(30, 0)
                    elif parsed["relation"] == "in_front_of":
                        self.player.move(0, -30)
                    elif parsed["relation"] == "behind":
                        self.player.move(0, 30)
                    else:
                        self.message = "Move where?"
                        self.message_timer = 120

        except Exception as e:
            self.message = f"Error: {str(e)}"
            self.message_timer = 120

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.input_active and self.input_text:
                        self.execute_nlp_command(self.input_text)
                        self.input_text = ""
                        self.input_active = False
                    else:
                        self.input_active = True

                elif event.key == pygame.K_ESCAPE:
                    self.input_active = False
                    self.input_text = ""

                elif self.input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    else:
                        self.input_text += event.unicode

                # Manual controls for testing
                elif not self.input_active:
                    if event.key == pygame.K_LEFT:
                        self.player.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.player.move(1, 0)
                    elif event.key == pygame.K_UP:
                        self.player.move(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.player.move(0, 1)

        return True

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1

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
            "Press ENTER to type command, arrow keys to move manually", True, WHITE
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
