import pathlib
import pygame
import random
import requests

# Positioning constants:
WIDTH = 320
HEIGHT = 640
BUBBLE_MARGIN = 100
BOT_PADDING = 100
TOP_BAR_HEIGHT = 50
PROGRESS_BAR_LEFT = 100
PROGRESS_BAR_HEIGHT = 10

# Colour tuples
DARK_COLOUR = (37, 37, 50)
TOP_BAR_COLOUR = (75, 75, 100)
WHITE_COLOUR = (255, 255, 255)
RED_COLOUR = (250, 200, 200)
GREEN_COLOUR = (200, 250, 200)
BLUE_COLOUR = (200, 200, 250)
YELLOW_COLOUR = (250, 250, 200)

# Resources
RES_DIR = pathlib.Path(__file__).parent / 'resources'
BLUE_ROBOT_IMAGE_NAME = 'blue_robot.png'
RED_ROBOT_IMAGE_NAME = 'red_robot.png'
TROPHY_IMAGE_NAME = 'trophy.png'
FONT_NAME = None

# Misc config
API_URL = 'http://codingforfun.pmdx.me'
FLAIRS = [
    [':O', ':(', 'o.o'],
    [':D', ':)', '^.^']
]


def load_image(image_name, size=None):
    path = RES_DIR / image_name
    try:
        surface = pygame.image.load(str(path))
    except pygame.error as e:
        print(f'Cannot load image: {path}')
        raise e
    image = surface.convert_alpha()
    if size:
        image = pygame.transform.smoothscale(image, size)
    return image


class Bubble:
    def __init__(self, pos, alignment, text, colour=None):
        self.pos = pos
        self.alignment = alignment
        self.text = text
        self.colour = colour
        self._font = pygame.font.SysFont(FONT_NAME, 40)
        self._text_size = self._font.size(self.text)
        self._padding = 5

    def pos_modifier(self, alignment):
        """Maps -1, 1 to 0, -1 respectively"""
        return -0.5 * (alignment + 1)

    @property
    def main_rect_pos(self):
        return self.pos[0] + self.pos_modifier(self.alignment) * self.main_rect_size[0], self.pos[1]

    @property
    def main_rect_size(self):
        return self._text_size[0] + 2 * self._padding, self._text_size[1] + 2 * self._padding

    @property
    def avatar_image(self):
        image_name = BLUE_ROBOT_IMAGE_NAME if self.alignment == 1 else RED_ROBOT_IMAGE_NAME
        image = load_image(image_name, self.avatar_size)
        return image

    @property
    def avatar_pos(self):
        return self.pos[0] + (self.alignment * 3 * self._padding) + (
                self.pos_modifier(-self.alignment) * self.avatar_size[0]), self.pos[1] - self._padding

    @property
    def avatar_size(self):
        return self.main_rect_size[1] + 2 * self._padding, self.main_rect_size[1] + 2 * self._padding

    def draw_to(self, surface):
        pygame.draw.rect(surface, self.colour, pygame.Rect(self.main_rect_pos, self.main_rect_size))
        text_render = self._font.render(self.text, 1, DARK_COLOUR)
        surface.blit(text_render, (self.main_rect_pos[0] + self._padding, self.main_rect_pos[1] + self._padding))
        surface.blit(self.avatar_image, self.avatar_pos)


class TopBar:
    def __init__(self, score):
        self.score = score
        self.rect = pygame.Surface((WIDTH, TOP_BAR_HEIGHT))
        self.rect.fill(TOP_BAR_COLOUR)
        self._score_font = pygame.font.SysFont(FONT_NAME, 30)
        self._red_avatar = load_image(RED_ROBOT_IMAGE_NAME, (40, 40))
        self._blue_avatar = load_image(BLUE_ROBOT_IMAGE_NAME, (40, 40))

    def draw_score(self, surface, index):
        text = str(self.score[index])
        render = self._score_font.render(text, 1, WHITE_COLOUR)
        size = self._score_font.size(text)
        if index == 0:
            pos = (10, int((TOP_BAR_HEIGHT - size[1]) / 2))
        else:
            pos = (WIDTH - 10 - size[0], int((TOP_BAR_HEIGHT - size[1]) / 2))
        surface.blit(render, pos)

    def draw_to(self, surface):
        surface.blit(self.rect, (0, 0))
        self.draw_score(surface, index=0)
        self.draw_score(surface, index=1)
        surface.blit(self._red_avatar, (40, 5))
        surface.blit(self._blue_avatar, (WIDTH - self._blue_avatar.get_rect().width - 40, 5))


class ProgressBar:
    def __init__(self, game_version, score):
        self.game_version = game_version
        self.score = score
        self.rect = pygame.Rect(
            (PROGRESS_BAR_LEFT, int((TOP_BAR_HEIGHT - PROGRESS_BAR_HEIGHT) / 2)),
            (WIDTH - 2 * PROGRESS_BAR_LEFT, 10)
        )
        self.trophy_image = load_image(TROPHY_IMAGE_NAME, (2 * PROGRESS_BAR_HEIGHT, 2 * PROGRESS_BAR_HEIGHT))

    @property
    def number_of_wins(self):
        if self.game_version in (1, 2):
            return 5
        elif self.game_version == 3:
            return 2
        elif self.game_version == 4:
            return 3
        raise Exception(f'Unexpected game version: {self.game_version}')

    @property
    def pos_list(self):
        pos_list = []
        for i in range(2 * self.number_of_wins + 1):
            left = int(self.rect.left + i * (self.rect.width / (2 * self.number_of_wins)))
            top = int(self.rect.top + (self.rect.height / 2))
            pos_list.append((left, top))
        return pos_list

    def draw_to(self, surface):
        # Draw progress markers
        for trophy_pos in self.pos_list:
            pygame.draw.circle(surface, DARK_COLOUR, trophy_pos, 2)

        # Draw progress bars
        red_rect = pygame.Rect(
            (int(WIDTH / 2) - int(self.score[0] * self.rect.width / (2 * self.number_of_wins)), self.rect.top),
            (int(self.score[0] * self.rect.width / (2 * self.number_of_wins)), self.rect.height)
        )
        pygame.draw.rect(surface, RED_COLOUR, red_rect)
        blue_rect = pygame.Rect(
            (int(WIDTH / 2), self.rect.top),
            (int(self.score[1] * self.rect.width / (2 * self.number_of_wins)), self.rect.height)
        )
        pygame.draw.rect(surface, BLUE_COLOUR, blue_rect)

        # Draw trophy
        if self.score[0] == self.number_of_wins:
            surface.blit(self.trophy_image,
                         (self.rect.left - PROGRESS_BAR_HEIGHT, int(self.rect.top - PROGRESS_BAR_HEIGHT / 2)))
        elif self.score[1] == self.number_of_wins:
            surface.blit(self.trophy_image,
                         (self.rect.right - PROGRESS_BAR_HEIGHT, int(self.rect.top - PROGRESS_BAR_HEIGHT / 2)))


class Game:
    def __init__(self, game_code, game_version, robot_said):
        self.game_code = game_code
        self.game_version = game_version
        self.robot_said = robot_said
        self.agent_said = None
        self.score = [0, 0]
        self.outcome = None
        self.progress_bar = ProgressBar(self.game_version, self.score)
        self.bubbles = []

    @classmethod
    def start(cls, game_version):
        response = requests.post(f'{API_URL}/v{game_version}/new')
        data = response.json()
        game = cls(
            game_code=data['game_code'],
            game_version=game_version,
            robot_said=data['robot_says']
        )
        game.add_bubble(Bubble(
            pos=[BUBBLE_MARGIN, HEIGHT - BOT_PADDING],
            alignment=-1,
            text=f'{data["robot_says"]}?',
            colour=RED_COLOUR
        ))
        return game

    def parse_outcome(self, outcome):
        if 'Agent wins the game.' in outcome:
            self.outcome = 1
        elif 'Robot wins the game.' in outcome:
            self.outcome = 0

        if 'Agent wins this round.' in outcome:
            return 1
        elif 'Robot wins this round.' in outcome:
            return 0

    @staticmethod
    def flair(outcome):
        flair_set = FLAIRS[outcome]
        return flair_set[random.randint(0, len(flair_set) - 1)]

    def add_bubble(self, bubble):
        for bubble_ in self.bubbles:
            bubble_.pos[1] -= 50
        self.bubbles.append(bubble)

    def play_round(self, agent_says, auto=False):
        # Agent:
        self.agent_said = agent_says
        body = {'game_code': self.game_code, 'agent_says': agent_says}
        response = requests.post(f'{API_URL}/v{self.game_version}/play', json=body)

        colour = YELLOW_COLOUR if auto else BLUE_COLOUR
        self.add_bubble(Bubble(
            pos=[WIDTH - BUBBLE_MARGIN, HEIGHT - BOT_PADDING],
            alignment=1,
            text=f'{agent_says}!',
            colour=colour
        ))

        # Robot:
        data = response.json()
        outcome = self.parse_outcome(data['outcome'])
        self.robot_said = data.get('robot_says')

        robot_says_reply = f' {data["robot_says"]}?' if data.get('robot_says') else ''
        colour = GREEN_COLOUR if outcome == 1 else RED_COLOUR
        self.add_bubble(Bubble(
            pos=[BUBBLE_MARGIN, HEIGHT - BOT_PADDING],
            alignment=-1,
            text=self.flair(outcome) + robot_says_reply,
            colour=colour
        ))

        self.score[outcome] += 1

    def auto_play_round(self):
        """
        -=:: Big Brain Algorithm ::=-
               _---~~(~~-_.
            _{        )   )
          ,   ) -~~- ( ,-' )_
         (  `-,_..`., )-- '_,)
        ( ` _)  (  -~( -_ `,  }
        (_-  _  ~_-~~~~`,  ,' )
          `~ -^(    __;-,((()))
                ~~~~ {_ -_(())
                       `\  }
                         { }
        Win Rates:
            v1: 100%
            v2: 84%
            v3: 100%
            v4: 47%
        """
        agent_says = self.robot_said
        if self.game_version in (2, 4) and self.agent_said:
            calc = (self.robot_said + self.agent_said) % 10
            agent_says = 1 if calc == 0 else calc

        self.play_round(agent_says, auto=True)


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Chitchat')

    # Game variables
    game = None
    game_version = 1
    score = [0, 0]

    # UI objects
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    background = pygame.Surface(screen.get_size())
    background.fill(DARK_COLOUR)

    top_bar = TopBar(score)

    status_font = pygame.font.SysFont(FONT_NAME, 20)

    # Clock
    clock = pygame.time.Clock()
    app_active = True

    while app_active:
        clock.tick(60)

        # INPUT
        for event in pygame.event.get():
            # Exit game
            if event.type == pygame.QUIT:
                app_active = False
            elif event.type == pygame.KEYDOWN:
                # Start new game
                if event.key == pygame.K_RETURN:
                    game = Game.start(game_version)
                # Game inputs
                if game and game.outcome is None:
                    # Manual play
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        game.play_round(int(event.unicode))
                    # Auto play
                    elif event.key == pygame.K_SPACE:
                        game.auto_play_round()

                    if game.outcome is not None:
                        score[game.outcome] += 1
                # Change game version
                else:
                    if pygame.K_1 <= event.key <= pygame.K_4:
                        game_version = int(event.unicode)

        # DO
        status_text = f'{game.game_code if game else "No active game"}' + f' [v{game_version}]'

        # DRAW
        screen.blit(background, (0, 0))
        if game:
            for bubble in game.bubbles:
                bubble.draw_to(screen)

        top_bar.draw_to(screen)

        if game:
            game.progress_bar.draw_to(screen)

        status_text_render = status_font.render(status_text, 1, WHITE_COLOUR)
        screen.blit(status_text_render, (10, HEIGHT - 20))

        pygame.display.flip()

    pygame.quit()
