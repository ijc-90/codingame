import sys
from collections import namedtuple
from math import *

TYPE_MONSTER = 0
TYPE_MY_HERO = 1
TYPE_OP_HERO = 2

HERO_SPEED = 800
MONSTER_SPEED = 400
HERO_RANGE = 2200
WIND_RANGE = 1280
BASE_RANGE = 6000
BASE_SPIDER_RANGE = 5000

class SteeringBehaviour():
    pass

def vdiff(a, b):
    x1, y1 = a if isinstance(a, tuple) else (a.x, a.y)
    x2, y2 = b if isinstance(b, tuple) else (b.x, b.y)
    
    return (x1 - x2, y1 - y2)

def dist(a, b):
    w, h = vdiff(a, b)
    return sqrt(w*w + h*h)

def out_of_bounds(p):
    x, y = p
    return x < 0 or x > 17630 or y < 0 or y > 9000

################################
# THIS IS HOW I ROLL
################################
IS_ARENA = False
STATE_DEBUG = True

LYRICS = """
We're no strangers to_love
You know the rules and_so do_I
A_full commitment's what_I'm _ thinking of
You wouldn't get_this from any other guy
I just wanna tell you how I'm feeling
Gotta make you understand

Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you

We've known each other for so_long
Your heart's been aching but you're too_shy to say_it
Inside we_both know what's been going_on
We_know the_game and we're gonna play it
And if_you ask_me how_I'm feeling
Don't tell_me you're too blind to_see

Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give you up
Never gonna let you down
Never gonna run around and desert you
Never gonna make you cry
Never gonna say goodbye
Never gonna tell a lie and hurt you
Never gonna give, never gonna give
"""

WORDS = []
CURRENT_SINGING_HERO = 0

for line in LYRICS.splitlines():
    if line.strip() == "":
        WORDS.append("")
        continue
    for word in line.strip().split():
        WORDS.append(word)
    WORDS.append("")

WORDS = [w.replace('_', ' ') for w in WORDS]

print(f"KIND WORDS TO SAY: {len(WORDS)}", file=sys.stderr, flush=True)

################################
# RNG
################################

SEED = 382479
RNG_A = 1103515245
RNG_C = 12345
RNG_M = 2**31

def randint():
    global SEED
    SEED = (RNG_A * SEED + RNG_C) % RNG_M
    return SEED

def choose(xs):
    return xs[randint() % len(xs)]

################################
# GAME MODEL
################################

_RES = 1
_RANGE = list(range(-1000, 1001, 100 * _RES))
_POS = [(x, y) for x in _RANGE for y in _RANGE if sqrt(x * x + y * y) <= 1030]

class Entity():
    def __init__(self, game, turn):
        self._game = game
        self._turn = turn
        self.will_be_controlled_by = None
        (
            self._id,            # _id: Unique identifier
            self._type,          # _type: 0=monster, 1=your hero, 2=opponent hero
            self.x, self.y,      # x,y: Position of this entity
            self.shield_life,    # shield_life: Count down until shield spell fades
            self.is_controlled,  # is_controlled: Equals 1 when this entity is under a control spell
            self.health,         # health: Remaining health of this monster
            self.vx, self.vy,    # vx,vy: Trajectory of this monster
            self.near_base,      # near_base: 0=monster with no target yet, 1=monster targeting a base
            self.threat_for      # threat_for: Given this monster's trajectory, is it a threat to 1=your base, 2=your opponent's base, 0=neither
        ) = [int(j) for j in input().split()]
        self._index_hero()

    def is_shielded(self):
        return self.shield_life > 0

    def move_positions(self):
        return [
            (x+self.x, y+self.y) 
            for (x, y) in _POS 
            if not out_of_bounds((x+self.x, y+self.y))
        ]

    def best_position_for(self, *score_functions):
        return max(
            self.move_positions(),
            key=lambda p: sum(cf(p) for cf in score_functions)
        )

    def _index_hero(self):
        self.index = None
        if self._type == TYPE_MY_HERO:
            self.index = self._id
            if not self._game.playing_left():
                self.index -= 3

    def threat_for_us(self):
        return self.threat_for == 1

    def threat_for_enemy(self):
        return self.threat_for == 2

    def orientation_to(self, position):
        tx, ty = vdiff(position, self)
        mx, my = self.vx, self.vy
        return cos(atan2(tx, ty) - atan2(mx, my))

    def indicate_that_it_will_be_controlled_by(self, hero):
        self.will_be_controlled_by = hero

    def will_be_controlled(self):
        return self.will_be_controlled_by is not None

    def just_entered_base(self):
        return (
            self.distance_to_our_base() <= BASE_SPIDER_RANGE and
            self.before().distance_to_our_base() > BASE_SPIDER_RANGE
        )

    def can_leave_base_using_control(self):
        return (
            self.distance_to_our_base() < BASE_SPIDER_RANGE + 500 and
            self.distance_to_our_base() > BASE_SPIDER_RANGE # - 100
        )

    def vector_to_our_base(self):
        return (self.x - self._game.base_x, self.y - self._game.base_y)

    def distance_to_our_base(self):
        x, y = self.vector_to_our_base()
        return sqrt(x*x + y*y)

    def distance_to_enemy_base(self):
        eb = self._game.pos('enemy_base')
        return dist(eb, self)

    def distance_to_my_hero(self, i):
        h = self._turn.my_heroes[i]
        return dist(self, h)

    def distance_to_other(self, other_entity):
        return dist(self, other_entity)

    def at_enemy_range(self):
        return len(self.enemies_at_range()) > 0

    def at_enemy_wind_range(self):
        return len(self.enemies_at_wind_range()) > 0

    def enemies_at_wind_range(self):
        return [
            h for h in self._turn.opp_heroes
            if dist(self, h) < WIND_RANGE
        ]

    def enemies_at_range(self):
        return [
            h for h in self._turn.opp_heroes
            if dist(self, h) < HERO_RANGE
        ]

    def monsters_at_wind_range(self):
        return [
            m for m in self._turn.monsters
            if dist(m, self) < WIND_RANGE
        ]

    def monsters_at_hero_range(self):
        return [
            m for m in self._turn.monsters
            if dist(m, self) < HERO_RANGE
        ]

    def before(self):
        if not self._turn._previous_turn:
            return self
        return self._turn._previous_turn.get_entity_by_id(self._id) or self

    def was_blown(self):
        return dist(self, self.before()) > 1000

    def was_blown_in(self):
        return (
            self.was_blown() and
            self.got_closer()
        )
    
    def was_blown_out(self):
        return (
            self.was_blown() and
            not self.got_closer()
        )

    def got_closer(self):
        return self.distance_to_our_base() < self.before().distance_to_our_base()

    def priority(self):
        d = self.distance_to_our_base()
        if self.near_base and self.threat_for_us():
            return d
        if self.threat_for_us():
            return 20000 + d
        return 40000 + d

    def turns_to_reach(self, hero):
        _, _, turns = self.intercept_info(hero)
        return turns

    def intercept_position(self, hero):
        mx, my, _ = self.intercept_info(hero)
        return mx, my

    def position_next_turn(self):
        if self._type != TYPE_MONSTER:
            return self.x, self.y
        return self.x + self.vx, self.x + self.vy
        
    def intercept_info(self, hero):
        mx, my = self.x, self.y
        turns = 0
        while True:
            turns += 1
            mx, my = mx + self.vx, my + self.vy
            d = dist(hero, (mx, my))
            if d <= HERO_SPEED * turns:
                break
            if out_of_bounds((mx, my)):
                mx, my = mx - self.vx, my - self.vy
                break
        return mx, my, turns

    def __repr__(self):
        return f"Entity {self._id}"

  
class TurnState():
    def __init__(self, game, previous_turn):
        self._previous_turn = previous_turn
        self._game = game
        self.my_health, self.my_mana = [int(j) for j in input().split()]
        self.enemy_health, self.enemy_mana = [int(j) for j in input().split()]
        self.entity_count = int(input())  # Amount of heros and monsters you can see
        self.number = previous_turn.number + 1 if previous_turn else 0
        self.entities: dict[int, Entity] = {}
        self.monsters: list[Entity] = []
        self.my_heroes: list[Entity] = []
        self.opp_heroes: list[Entity] = []
        for i in range(self.entity_count):
            entity = Entity(game, self)
            self.entities[entity._id] = entity
            if entity._type == TYPE_MONSTER:
                self.monsters.append(entity)
            elif entity._type == TYPE_MY_HERO:
                self.my_heroes.append(entity)
            elif entity._type == TYPE_OP_HERO:
                self.opp_heroes.append(entity)

    def enough_mana(self):
        return self.my_mana >= 10

    def get_entity_by_id(self, id):
        return self.entities.get(id, None)

    def monsters_near(self, position, radius):
        return [m for m in self.monsters if dist(m, position) <= radius]

    def monsters_near_next_turn(self, position, radius):
        return [
            m for m in self.monsters
            if dist(m.position_next_turn(), position) <= radius
        ]

    def opp_heroes_in_base(self):
        return [
            h for h in self.opp_heroes
            if h.distance_to_our_base() < BASE_RANGE
        ]

    def base_being_invaded(self):
        return len(self.opp_heroes_in_base()) > 0

    def top_priority_threats_changed(self):
        if not self._previous_turn:
            return False
        ot = self._previous_turn.top_priority_threats()
        nt = self.top_priority_threats()
        # compare order and ids
        return [m._id for m in ot] != [m._id for m in nt]
        
    def top_priority_threats(self):
        pm = sorted(
            (m for m in self.monsters if m.threat_for_us()), 
            key=lambda m: m.priority()
        )
        return pm[:3]

    def update(self, entity):
        return self.entities.get(entity._id, None)

class GameState():
    def __init__(self):
        # base_x,base_y: The corner of the map representing your base
        self.base_x, self.base_y = [int(i) for i in input().split()]
        self.heroes_per_player = int(input())
        self.positions = {
            'low': (2740, 6400),
            'mid': (6540, 4940),
            'high': (7930, 1800),
            'door': (3550, 3230),
            'left': (5400, 2250),
            'right': (2900, 5000),
            'spidercorner': (5000, 8000),
            'spidersink': (12700, 8300),
            'spidersink2': (17500, 4300),
            'center': (8800, 4600),
            'enemy_base': (17530, 8900),
            'attack_right': (12000, 7000),
            'attack_left': (15500, 3100),
            'base': (1800, 2100),
            'sp1': (5000, 8500),
            'sp2': (8700, 8500),
            'sp3': (8900, 400),
            'sp4': (12000, 400),
        }
        self._spawn_points = [
            p for (k,p) in self.positions.items()
            if k in ['sp1', 'sp2', 'sp3', 'sp4']
        ]
        if not self.playing_left():
            self._mirror_positions()

    def pos(self, position_name):
        return self.positions[position_name]

    def spawn_points(self):
        return self._spawn_points

    def playing_left(self):
        return self.base_x < 1000

    def _mirror_positions(self):
        for p in self.positions.keys():
            x, y = self.positions[p]
            self.positions[p] = self.base_x - x, self.base_y - y


################################
# HERO FSM
################################

class Msg():
    def __init__(self, type, content):
        self.type = type
        self.content = content

class TeamMind():
    def __init__(self, members):
        self.members: list[HeroMind] = members
        self.enemies_that_blow_out = set()
        self.enemies_that_mind_control = set()

    def update(self, turn: TurnState):
        for mind in self.members:
            if mind.hero.is_controlled:
                for enemy in mind.hero.before().enemies_at_range():
                    self.enemies_that_mind_control.add(enemy._id)
                mind.queue_message(Msg('you_were_mind_controlled', {}))

            if mind.hero.at_enemy_range():
                enemies = set(e._id for e in mind.hero.enemies_at_range()) 
                if enemies & self.enemies_that_mind_control:
                    mind.queue_message(Msg('careful_mindboggers_nearby', {'enemy_ids': enemies}))

            if mind.hero.was_blown_out():
                for enemy in mind.hero.before().enemies_at_wind_range():
                    self.enemies_that_blow_out.add(enemy._id)
                mind.queue_message(Msg('you_were_blown_out', {}))

            if mind.hero.at_enemy_wind_range():
                enemies = set(e._id for e in mind.hero.enemies_at_wind_range()) 
                if enemies & self.enemies_that_blow_out:
                    mind.queue_message(Msg('careful_blowers_nearby', {'enemy_ids': enemies}))

        if not turn.top_priority_threats_changed():
            return
        
        assignation = self.assign_heroes(
            [m.hero for m in self.members if m.is_currently(Defend)],
            turn.top_priority_threats()
        )
        for m, h in assignation.items():
            mind = [mind for mind in self.members if mind.hero == h][0]
            mind.queue_message(Msg('threat_assignation_changed', {'spider': m}))

    def assign_heroes(self, available_heroes, monsters):
        assignation = {}
        for m in monsters:
            min_d = 8000000
            closest_h = None
            if not available_heroes:
                break
            for h in available_heroes:
                i = h.index
                d = dist(m, h)
                if d < min_d:
                    min_d = d
                    closest_h = h
            assert(closest_h is not None)
            assignation[m] = closest_h
            available_heroes.remove(closest_h)
        return assignation

class HeroMind():
    def __init__(self, hero_index, initial_state):
        self.state_stack = [SelfDefense(), initial_state]
        self.hero_index = hero_index
        self.state_debug = ""
        self.inbox: list[Msg] = []

    def update(self, team, turn):
        self.hero: Entity = turn.my_heroes[self.hero_index]
        self.team = team

    def queue_message(self, msg: Msg):
        self.inbox.append(msg)

    def process_messages(self, turn):
        while self.inbox:
            msg = self.inbox.pop(0)
            self.process_message(turn, msg)

    def process_message(self, turn, msg: Msg):
        for state in reversed(self.state_stack):
            handled = state.handle_message(mind, turn, msg)
            if handled:
                break

    def pop_until(self, state):
        assert(state in self.state_stack)
        while self.current_state() != state:
            self.pop_state()

    def step(self, turn):
        self.action = None
        self.text = ""
        print(f"|UPDATING HERO {self.hero._id}", file=sys.stderr, flush=True)
        while not self.has_an_action():
            print(f"| {self}", file=sys.stderr, flush=True)
            self.current_state().update(self, turn)
        print(f"'", file=sys.stderr, flush=True)
        self.emit_action(turn)

    def others(self):
        return [m for m in self.team.members if m != self]

    def emit_action(self, turn):
        if STATE_DEBUG:
            print(self.action, self.state_debug)
        elif not IS_ARENA:
            print(self.action, self.text)
        else:
            if (
                CURRENT_SINGING_HERO == self.hero.index and
                turn.number < len(WORDS)
            ):
                print(self.action, WORDS[turn.number])
            else:
                print(self.action)

    def push_state(self, new_state):
        self.state_stack.append(new_state)

    def pop_state(self):
        self.state_stack.pop()

    def new_objective(self, new_root_state):
        self.state_stack = [SelfDefense(), new_root_state]

    def is_currently(self, state_cls):
        return any(
            isinstance(s, state_cls)
            for s in self.state_stack
        )

    def change_state(self, new_state):
        self.pop_state()
        self.push_state(new_state)

    def current_state(self):
        return self.state_stack[-1]

    def DO(self, *action):
        self.state_debug = "".join(s.display() for s in self.state_stack)
        self.action = " ".join(self._to_str(p) for p in action)

    def _to_str(self, x):
        if isinstance(x, float):
            return str(int(x))
        if isinstance(x, tuple):
            return " ".join(self._to_str(p) for p in x)
        else:
            return str(x)

    def SAY(self, *text):
        self.text = " ".join(str(p) for p in text)

    def has_an_action(self):
        return self.action is not None

    def __repr__(self):
        return "/".join(s.__repr__() for s in self.state_stack)

class HeroState():
    def update(self, mind: HeroMind, turn: TurnState):
        raise NotImplemented("HeroState.update")

    def handle_message(self, mind: HeroMind, turn: TurnState, msg: Msg):
        pass

    def display(self):
        return self.__class__.__name__[0]

    def __repr__(self):
        return self.__class__.__name__


################################
# HERO STATES
################################

class SelfDefense(HeroState):
    def __init__(self):
        pass

    def display(self):
        return 'S'

    def handle_message(self, mind: HeroMind, turn: TurnState, msg: Msg):
        if msg.type == "you_were_blown_out":
            mind.push_state(CastShieldOnMyself())
            return True
        if msg.type == "careful_blowers_nearby":
            mind.push_state(CastShieldOnMyself())
            return True
        if msg.type == "you_were_mind_controlled":
            mind.push_state(CastShieldOnMyself())
            return True
        if msg.type == "careful_mindboggers_nearby":
            mind.push_state(CastShieldOnMyself())
            return True

    def update(self, mind: HeroMind, turn: TurnState):
        mind.DO("WAIT")
        mind.SAY("._.")


class CastShieldOnMyself(HeroState):
    def update(self, mind: HeroMind, turn: TurnState):
        if not mind.hero.is_shielded():
            mind.DO("SPELL SHIELD", mind.hero._id)
            mind.SAY("noway")
        mind.pop_state()

    def display(self):
        return 'S'


class Defend(HeroState):
    def __init__(self):
        pass

    def display(self):
        return 'D'

    def handle_message(self, mind: HeroMind, turn: TurnState, msg: Msg):
        if msg.type == "threat_assignation_changed":
            mind.pop_until(self)
            mind.push_state(DefendFromSpider(msg.content['spider']))
            return True

    def targetable_monsters(self, hero: Entity):
        return [
            m for m in hero.monsters_at_hero_range()
            if m.distance_to_our_base() < 6300
        ]
    def update(self, mind: HeroMind, turn: TurnState):
        monsters = turn.top_priority_threats()
        if monsters:
            mind.push_state(
                DefendFromSpider(monsters[0])
            )
            return

        # TODO: Check if we got a little bit far from base before horsing around

        monsters = self.targetable_monsters(mind.hero)
        if monsters:
            t = min(monsters, key=lambda m: dist(m, mind.hero) + m.distance_to_our_base())
            mind.push_state(
                # this could be another kind of defend
                DefendFromSpider(t)
            )
            return
        
        # TODO: an enemy is TOOO close to our base and could whoosh a spider in
    
        mind.push_state(
            Wander(
                around_position="door",
                until=lambda h: len(self.targetable_monsters(h)) > 0,
                radius=3000
            )
        )


L_MONSTER_THREAT = lambda hero: any(m.threat_for_us() for m in hero._turn.monsters)
L_MONSTER_NEARBY = lambda hero: len(hero.monsters_at_hero_range()) > 0
L_MONSTER_THREAT_OR_NEARBY = lambda h: L_MONSTER_THREAT(h) or L_MONSTER_NEARBY(h)
L_NEVER = lambda hero: False


class Wander(HeroState):
    def __init__(self, around_position=None, until=L_MONSTER_NEARBY, radius=3000):
        self.position = around_position
        self.until = until
        self.radius = radius
        self.current = choose([1, 3, 5, 7, 9, 11])

    def display(self):
        return 'W'

    def node(self, i, turn):
        r = self.radius / 3
        x, y = (
            turn._game.pos(self.position) 
            if isinstance(self.position, str)
            else self.position
        )
        return {
            1: (x+r, y-2*r),
            3: (x+3*r, y),
            5: (x+r, y+2*r),
            7: (x-r, y+2*r),
            9: (x-3*r, y),
           11: (x-r, y-2*r),
        }[i]

    def edges(self, i):
        return {
            1: (5, 7, 9),
            3: (7, 9, 11),
            5: (9, 11, 1),
            7: (11, 1, 3),
            9: (1, 3, 5),
           11: (3, 5, 7),
        }[i]

    def update(self, mind: HeroMind, turn: TurnState):
        if not self.position:
            self.position = mind.hero.x, mind.hero.y

        if self.until(mind.hero):
            mind.pop_state()
            return
            
        self.current = choose(self.edges(self.current))
        cp = self.node(self.current, turn)

        mind.push_state(GoTo(cp, stop_if=self.until))


class DefendFromSpider(HeroState):
    def __init__(self, target: Entity):
        self.target = target

    def display(self):
        return 'd' + str(self.target._id)

    def handle_message(self, mind: HeroMind, turn: TurnState, msg: Msg):
        if msg.type == "threat_assignation_changed":
            m = msg.content['spider']
            if m._id == self.target:
                # just ack cuz we are already onto it
                return True
        
    def update(self, mind: HeroMind, turn: TurnState):
        t = next((m for m in turn.monsters if m._id == self.target._id), None)
        if t is None:
            mind.pop_state()
            return
        self.target = t
        h, t = mind.hero, self.target

        # TODO: Abandon if spider is too far from base or changed direction
        if not t.threat_for_us() and t.distance_to_our_base() > 6400:
            mind.pop_state()
            return

        # can just control target away
        if (
            t.can_leave_base_using_control() and
            dist(t, h) < HERO_RANGE and
            t.threat_for_us() and
            t.health > 10 and
            not t.will_be_controlled() and
            not t.before().will_be_controlled() and
            dist(t, h) > 1000 and
            not t.is_shielded()
        ):
            # TODO: check if can be controlled to the enemy base (sometimes
            #   because of the angle the spider may end up not leaving)
            mind.push_state(ControlSpiderToEnemy(t))
            return

        # enemy just whooshed this spider
        if (
            dist(t, h) < WIND_RANGE and
            t.was_blown_in() and
            t.near_base and
            t.at_enemy_range() and
            not t.is_shielded()
            and turn.enough_mana()
        ):
            x, y = h.x + t.x - turn._game.base_x, h.y + t.y - turn._game.base_y
            mind.DO('SPELL WIND', x, y)
            return

        # we just whooshed this weak spider out but there is an enemy so we shield it
        if (
            dist(t, h) < HERO_RANGE and
            t.was_blown_out() and
            not t.near_base and
            t.at_enemy_range() and
            t.health > 10 and
            not t.is_shielded()
            and turn.enough_mana()
        ):
            mind.DO('SPELL SHIELD', t._id)
            return

        # is too close so we whoosh it
        if t.distance_to_our_base() < 800 and t.distance_to_my_hero(i) < 1200:
            x, y = h.x + t.x - turn._game.base_x, h.y + t.y - turn._game.base_y
            mind.DO('SPELL WIND', x, y)
            return

        
        # if on whoosh range and theres an enemy hero near base we whosh
        if (
            dist(t, h) < WIND_RANGE and
            t.near_base and
            t.at_enemy_wind_range() and
            turn.opp_heroes_in_base() and
            # t.health > 4 and
            not t.is_shielded()
            and turn.enough_mana()
        ):
            x, y = h.x + t.x - turn._game.base_x, h.y + t.y - turn._game.base_y
            mind.DO('SPELL WIND', x, y)
            return

        # if spider can get outside by whooshing we whoosh
        mawr = h.monsters_at_wind_range()
        if (
            t in mawr and
            t.near_base and
            t.distance_to_our_base() > 3500 and
            t.health > 5 and
            not t.is_shielded()
            and turn.enough_mana()
        ):
            x, y = h.x + t.x - turn._game.base_x, h.y + t.y - turn._game.base_y
            mind.DO('SPELL WIND', x, y)
            return


        # if there are many spiders nearby in base we whoosh
        mawr = h.monsters_at_wind_range()
        if (
            len(mawr) > 1 and
            t in mawr and
            t.near_base and
            max(m.health for m in mawr) > 10 and
            not t.is_shielded()
            and turn.enough_mana()
        ):
            x, y = h.x + t.x - turn._game.base_x, h.y + t.y - turn._game.base_y
            mind.DO('SPELL WIND', x, y)
            return

        # no other alternative so we just attack
        ip_x, ip_y, turns_to_reach = t.intercept_info(h)
        mind.DO('MOVE', ip_x, ip_y)
        if turns_to_reach > 1:
            mind.SAY(t._id, 'in', turns_to_reach - 1)
        else:
            mind.SAY(t._id)


class SlaySpider(HeroState):
    def __init__(self, target: Entity):
        self.target = target

    def display(self):
        return 's' + str(self.target._id)

    def update(self, mind: HeroMind, turn: TurnState):
        t = next((m for m in turn.monsters if m._id == self.target._id), None)
        if t is None:
            mind.pop_state()
            return
        self.target = t
        h = mind.hero

        enemy_base = turn._game.pos("enemy_base")
        
        #spidercorner = turn._game.pos("spidercorner")
        #if (
        #    dist(t, spidercorner) < 1500 and
        #    t.threat_for_us() and
        #    dist(t, h) < HERO_RANGE and
        #    not t.will_be_controlled()
        #):
        #    t.indicate_that_it_will_be_controlled_by(h)
        #    mind.DO('SPELL CONTROL', t._id, turn._game.pos("spidersink"))
        #   mind.pop_state()
        #    return

        # if happens im at the enemy base I just whoosh the spider in
        if (
            dist(t, enemy_base) < 2500 and
            dist(t, h) < WIND_RANGE and
            not t.is_shielded()
        ):
            mind.push_state(WhooshSpiderToEnemy(t))
            return
    
        ip_x, ip_y, turns_to_reach = t.intercept_info(h)
        mind.DO('MOVE', ip_x, ip_y)
        if turns_to_reach > 1:
            mind.SAY(t._id, 'in', turns_to_reach - 1)
        else:
            mind.SAY(t._id)


class GoTo(HeroState):
    def __init__(self, pos, stop_if=L_MONSTER_NEARBY, max_steps=30):
        self.pos = pos
        self.stop_condition = stop_if
        self.remaining_steps = max_steps
    
    def display(self):
        return 'g'

    def update(self, mind: HeroMind, turn: TurnState):
        p = turn._game.pos(self.pos) if isinstance(self.pos, str) else self.pos
        h = mind.hero
        if dist(h, p) < 400:
            mind.pop_state()
            return


        if out_of_bounds(p):
            mind.pop_state()
            return

        mind.DO("MOVE", p)

        self.remaining_steps -= 1
        if self.remaining_steps <= 0:
            mind.pop_state()
            return

        if self.stop_condition(mind.hero):
            mind.pop_state()
            return


class Farm(HeroState):
    def display(self):
        return 'F'
    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero

        if turn.my_mana > 120 and (
            turn.number > 100 or 
            (turn.number > 40 and turn.base_being_invaded())
        ):
            pass
            mind.change_state(Attack())
            return

        p = h.best_position_for(
            lambda p: sum(-sqrt(dist(p, sp)) for sp in turn._game.spawn_points()) * 0.01,
            lambda p: 800 if any(
                    m.orientation_to(sp) > 0.9 
                    for m in turn.monsters_near(p, 800)
                    for sp in turn._game.spawn_points()
                ) else 0,
            lambda p: sum(300 for m in turn.monsters_near(p, 800)),
            lambda p: sum(sqrt(sqrt(dist(p, turn.my_heroes[i]))) for i in [0, 1, 2] if i != h.index) * 0.08
        )

        mind.DO('MOVE', p)
        return


class ControlSpiderToEnemy(HeroState):
    def display(self):
        return 'c' + str(self.spider._id)

    def __init__(self, spider: Entity, direction=None):
        self.spider = spider
        self.direction = direction
        
    def update(self, mind: HeroMind, turn: TurnState):
        self.spider = turn.update(self.spider)
        if not self.spider:
            mind.pop_state()
            return
        t = self.spider
        cs = self.closest_sink(turn) if not self.direction else turn._game.pos(self.direction)
        t.indicate_that_it_will_be_controlled_by(mind.hero)
        mind.DO('SPELL CONTROL', t._id, cs)
        mind.pop_state()

    def closest_sink(self, turn):
        t = self.spider
        closest_sink = None
        distance = 100000
        for sink in ["spidersink", "spidersink2"]:
            s = turn._game.pos(sink)
            if dist(s, t) < distance:
                distance = dist(s, t)
                closest_sink = s
        return closest_sink


class Attack(HeroState):
    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        if h.distance_to_enemy_base() > 6000: # 9000
            mind.push_state(GlideToEnemyBase())
            return
        
        if turn.my_mana < 40:
            mind.change_state(Farm())

        mind.push_state(WaitForAnOpportunity())


class GlideToEnemyBase(HeroState):
    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        if h.distance_to_enemy_base() < 6000:
            mind.pop_state()
        enemy_base = turn._game.pos('enemy_base')
        p = h.best_position_for(
            lambda p: -sqrt(dist(p, enemy_base)),
            lambda p: 1000 if any(
                    m.orientation_to(enemy_base) > 0.8 for m in turn.monsters_near(p, 800)
                ) else 0,
            lambda p: sum(400 for m in turn.monsters_near(p, 800))
        )
        mind.DO('MOVE', p)


ENEMY_WHOOSHES_SPIDERS_AWAY = None


class WaitForAnOpportunity(HeroState):
    def update(self, mind: HeroMind, turn: TurnState):
        # *1
        h = mind.hero
        if FollowEnemy.followable_enemies(h):
            if ENEMY_WHOOSHES_SPIDERS_AWAY:
                mind.change_state(FetchSpiderFromCorner())
            else:
                mind.change_state(FollowEnemy())
        else:
            mind.change_state(FetchSpiderFromCorner())


        #   si no se como juega:
        #     lo sigo analizando la situación *2
        #   si sé que deja que las arañas se acerquen:
        #     lo sigo analizando la situación *2
        #   si juega a sacarla arañas al toque:
        #     voy a buscar alguna araña en una esquina
        # si no veo a algun defensor:
        #   voy a buscar alguna araña en una esquina
        #   


class FollowEnemy(HeroState):

    def __init__(self):
        self.remaining_time = 20

    @staticmethod
    def followable_enemies(h):
        return [e for e in h.enemies_at_range() if e.distance_to_enemy_base() < 6000]

    def check_last_mile_whoosh(self, mind, turn):
        h = mind.hero
        whooshable = [
            m for m in h.monsters_at_wind_range()
            if not m.is_shielded()
            and m.distance_to_enemy_base() < 2500
        ]
        if whooshable:
            mind.change_state(WhooshSpiderToEnemy(whooshable[0]))
            return True

    def check_spiders_to_protect(self, mind, turn):
        h = mind.hero
        es = h.enemies_at_range()
        if len(es) != 1: return
        e = es[0]
        if e.is_shielded(): return
        ms = [
            m for m in h.monsters_at_hero_range()
            if m.distance_to_enemy_base() < 6000
            and m.health > 8
            and m.distance_to_enemy_base() < e.distance_to_enemy_base() + 400
        ]
        if ms:
            mind.change_state(ProtectSpiderConvoy())
            return True

    def check_for_opportunistic_whooshes(self, mind, turn):
        h = mind.hero
        if (
            not h.enemies_at_wind_range()
            and h.monsters_at_wind_range()
        ):
            mind.change_state(WhooshInto(turn._game.pos('enemy_base')))
            return True

    def update(self, mind: HeroMind, turn: TurnState):
        self.remaining_time -= 1
        # *2
        h = mind.hero
        es = FollowEnemy.followable_enemies(h)
        if not es:
            mind.pop_state()
            return

        if self.check_last_mile_whoosh(mind, turn):
            return
        if self.check_spiders_to_protect(mind, turn):
            return
        if self.check_for_opportunistic_whooshes(mind, turn):
            return

        if self.remaining_time <= 0:
            mind.pop_state()
            return
            
        e = min(es, key=lambda e: dist(h, e))
        enemy_base = turn._game.pos('enemy_base')

        p = h.best_position_for(
            lambda p: -sqrt(dist(p, e)),
            lambda p: -2000 if dist(p, e) < 1300 else 0,
            lambda p: 3000 if any(
                    m.distance_to_enemy_base() < 2200
                    for m in turn.monsters_near(p, 1200)
                ) else 0,
            lambda p: sum(1000 for m in turn.monsters_near(p, 1200)),
            lambda p: -sum(2000 for m in turn.monsters_near(p, 800)),
            lambda p: -sqrt(dist(p, enemy_base)) * 0.01,
        )

        mind.DO('MOVE', p)
        # si veo que deja entrar arañas cerca de la base:
        #   elijo entre:
        #     se las whoosheo bien adentro
        #     lo controlo alejandolo de las arañas
        # si veo que las pushea afuera rápido:
        #   voy a buscar alguna araña en una esquina *3
        # si veo que se aleja de la base:
        #    aborto


class FetchSpiderFromCorner(HeroState):
    def __init__(self):
        self.corners = {'l': 'attack_left', 'r': 'attack_right'}
        self.corner_code = None

    def display(self):
        return 'Q' + str(self.corner_code)

    def corner(self, turn):
        if not self.corner_code:
            return None
        return turn._game.pos(self.corners[self.corner_code])

    def change_corner(self, turn):
        if not self.corner_code:
            self.corner_code = choose(['l', 'r'])
        else:
            self.corner_code = 'l' if self.corner_code == 'r' else 'r'
        return self.corner(turn)

    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        corner = self.corner(turn)
        if not corner or dist(h, corner) < 600:
            corner = self.change_corner(turn)
        enemy_base = turn._game.pos('enemy_base')

        if choose([True, False]) and self.check_if_follow_hero(mind, turn):
            return
        if self.check_if_whoosh_spiders(mind, turn):
            return
        if self.check_if_send_spiders(mind, turn):
            return

        p = h.best_position_for(
            lambda p: -sqrt(dist(p, corner)),
            lambda p: sqrt(dist(p, enemy_base)) * 0.2,
            lambda p: 1000 if any(
                    m.orientation_to(corner) > 0.8 for m in turn.monsters_near(p, 800)
                ) else 0,
            lambda p: -1000 if any(
                    m.orientation_to(enemy_base) > 0.8 for m in turn.monsters_near(p, 800)
                ) else 0,
            lambda p: -sum(400 for m in turn.monsters_near(p, 800))
        )
        mind.DO('MOVE', p)

    def check_if_whoosh_spiders(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        if h.enemies_at_range():
            return
        if h.distance_to_enemy_base() > 5500:
            return
        ms = [
            m for m in h.monsters_at_wind_range()
            if not m.is_shielded()
            and m.distance_to_enemy_base() > h.distance_to_enemy_base() + 100
        ]
        if ms:
            mind.change_state(WhooshIn(ms[0]))
            return True

    def check_if_send_spiders(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        if h.enemies_at_range():
            return
        ms = [
            m for m in h.monsters_at_hero_range()
            if not m.is_shielded()
        ]
        if len(ms) >= choose([1, 2, 2, 3, 3, 3]):
            mind.change_state(SendSpiders())
            return True

    def check_if_follow_hero(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        ms = [
            m for m in h.monsters_at_hero_range()
            if m.distance_to_enemy_base() < 6000
        ]
        enemies = [
            e for e in FollowEnemy.followable_enemies(h)
            if not e.is_shielded()
            and dist(h, e) < 1300
            and any(dist(e, m) < 800 for m in ms)
        ]
        if enemies:
            mind.change_state(FollowEnemy())
            return True
        # *3
        # elijo una esquina
        # camino hasta alla
        # si me topo con arañas (afuera):
        #   si van para otro lado que no sea la esquina:
        #     las controlo para que vayan a la esquina
        #   si no hay enemigos cerca y las puedo whoosher y tirar escudo:
        #     las whoosheo y les tiro escudo
        #   si estan a punto de entrar a la base:
        #     les tiro escudo
        # si mandé un par de arañas así:
        #   decido entre:
        #     ir a buscar alguna araña en la otra esquina *3
        #     seguir al grupo de arañas y alejar a los heroes *4
        #     espero una oportunidad *1


class WhooshIn(HeroState):
    def __init__(self, spider):
        self.spider = spider
        self.times = 0

    def update(self, mind: HeroMind, turn: TurnState):
        self.spider = turn.update(self.spider)
        if not self.spider:
            mind.pop_state()
            return
        h = mind.hero

        if self.spider in h.monsters_at_wind_range() and not self.spider.is_shielded():
            self.times += 1
            mind.push_state(WhooshSpiderToEnemy(self.spider))
            return

        if self.spider in h.monsters_at_hero_range() and not self.spider.is_shielded():
            mind.push_state(ShieldSpider(self.spider))
            return

        if self.spider.distance_to_enemy_base() > 5000 and not self.spider.threat_for_enemy():
            mind.pop_state()
            return
        
        if choose([True, False]):
            mind.change_state(ProtectSpiderConvoy())
            mind.push_state(GoTo(
                pos='enemy_base',
                stop_if=L_NEVER,
                max_steps=2
            ))
        else:
            mind.pop_state()

class SendSpiders(HeroState):
    def __init__(self):
        self.remaining = choose([2, 3, 3, 4])

    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        there_are_enemies = len(h.enemies_at_range()) > 0
        #TODO: Check if can whoosh-in&shield
        ms = [
            m for m in h.monsters_at_hero_range()
            if not m.is_shielded() and not m.threat_for_enemy()
        ]
        if ms and not there_are_enemies and self.remaining > 0:
            m = max(ms, key=lambda m: dist(m,h))
            self.remaining -= 1
            mind.push_state(ControlSpiderToEnemy(m))
            return


        ms = [
            m for m in h.monsters_at_hero_range()
            if not m.is_shielded() and m.threat_for_enemy()
            and (
                m.distance_to_enemy_base() < 5500
                or there_are_enemies
            )
            and not m.enemies_at_wind_range()
        ]
        if ms:
            m = min(ms, key=lambda m: m.distance_to_enemy_base())
            mind.push_state(ShieldSpider(m))
            return

        if h.distance_to_enemy_base() < 5000:
            if there_are_enemies and choose([True, False]):
                mind.change_state(FetchSpiderFromCorner())
                return
            else:
                mind.change_state(ProtectSpiderConvoy())
                return


        ms = [
            m for m in h.monsters_at_hero_range()
        ]
        if not ms:
            mind.pop_state()
            return

        ms_distance_to_enemy_base = min(
            m.distance_to_enemy_base()
            for m in ms
        )

        enemy_base = turn._game.pos('enemy_base')
        p = h.best_position_for(
            lambda p: -sum(1000 for m in turn.monsters_near(p, 1000)),
            lambda p: 500 if turn.monsters_near(p, 1500) else 0,
            lambda p: -sqrt(dist(p, enemy_base)) * 0.1,
            lambda p: -1500 if dist(p, enemy_base) < ms_distance_to_enemy_base else 0
        )

        mind.DO('MOVE', p)



class ProtectSpiderConvoy(HeroState):
    def __init__(self):
        self.got_inside = False

    def update(self, mind: HeroMind, turn: TurnState):
        
        h = mind.hero
        convoy = [
            m for m in h.monsters_at_hero_range()
            if m.distance_to_enemy_base() < 6000
        ]
        # TODO: Change this to 5000

        if not convoy:
            mind.pop_state()
            return

        if self.got_inside and h.distance_to_enemy_base() > 3500:
            mind.pop_state()
            return

        if h.distance_to_enemy_base() < 3000:
            self.got_inside = True

        convoy_distance_to_enemy_base = min(
            m.distance_to_enemy_base()
            for m in convoy
        )
        unsh_enemies = [
            e for e in h.enemies_at_range()
            if not e.is_shielded()
            and any(dist(e, m) < 1200 for m in convoy)
        ]
        if unsh_enemies:
            e = min(unsh_enemies, key=lambda e: e.distance_to_enemy_base())
            mind.push_state(ControlEnemyFromSpiders(e))
            return

        unsh_convoy = [m for m in convoy if not m.is_shielded()]
        if unsh_convoy:
            m = unsh_convoy[0]
            mind.push_state(ShieldSpider(m))
            return

        enemy_base = turn._game.pos('enemy_base')
        p = h.best_position_for(
            lambda p: -sum(1000 for m in turn.monsters_near(p, 1000)),
            lambda p: 500 if turn.monsters_near(p, 1500) else 0,
            lambda p: -sqrt(dist(p, enemy_base)) * 0.1,
            lambda p: -1500 if dist(p, enemy_base) < convoy_distance_to_enemy_base else 0
        )

        mind.DO('MOVE', p)



        
        # *4
        # camino hacia la base buscando un lugar:
        #   a distancia whoosh de las arañas
        #   sin pegarle a las arañas
        #   acercandome un poco a algun enemigo
        #   buscando el punto medio entre las arañas y el enemigo
        # si hay enemigos cerca:
        #   si los puedo alejar con whoosh sin correr las arañas:
        #     los whoosheo lejos
        #   si no:
        #     los controlo lejos de las arañas
        # si hay una araña del convoy sin escudo y no hay un enemigo cerca que la pueda whooshear:
        #   le tiro escudo
        # si los enemigos se escudan:
        #   shrug 
        # si perdí de vista al convoy o este se debilitó:
        #   espero una oportunidad *1


class ControlEnemyFromSpiders(HeroState):
    def display(self):
        return 'c' + str(self.enemy._id)

    def __init__(self, enemy: Entity, direction=None):
        self.enemy = enemy
        self.direction = direction
        self.times = choose([1, 1, 2])
        
    def update(self, mind: HeroMind, turn: TurnState):
        self.enemy = turn.update(self.enemy)
        if not self.enemy:
            mind.pop_state()
            return
        h = mind.hero
        ms = [
            m for m in h.monsters_at_hero_range()
        ]
        if not ms:
            mind.pop_state()
            return
        enemy_base = turn._game.pos('enemy_base')
        p = self.enemy.best_position_for(
            lambda p: sum(dist(p, m) for m in ms) / len(ms) * 1,
            lambda p: dist(p, enemy_base) * 2,
            lambda p: 500 if turn.monsters_near(p, 1200) else 0,
        )

        self.enemy.indicate_that_it_will_be_controlled_by(mind.hero)
        mind.DO('SPELL CONTROL', self.enemy._id, p)
        self.times -= 1
        if self.times <= 0:
            mind.pop_state()


class AttackChaotically(HeroState):
    def display(self):
        return 'X'

    def update(self, mind: HeroMind, turn: TurnState):
        h = mind.hero
        enemy_base = turn._game.pos('enemy_base')
        if turn.my_mana < 50:
            mind.change_state(Farm())
            return

        controllable = lambda h, m: (
            m in h.monsters_at_hero_range() and
            not m.threat_for_enemy() and
            not m.will_be_controlled()
        )

        if not mind.hero.is_shielded():
            mind.push_state(CastShieldOnMyself())
            return
        
        whooshable = lambda h, m: (
            m in h.monsters_at_wind_range() and
            m.threat_for_enemy() and
            not m.is_shielded()
            # and m.distance_to_enemy_base() > h.distance_to_enemy_base() - 500
        )

        shieldable = lambda h, m: (
            m in h.monsters_at_hero_range() and
            m.threat_for_enemy() and
            not m.is_shielded() and
            not m.at_enemy_wind_range() and
            m.health > 10 and
            m.distance_to_enemy_base() < 8000 and
            m.distance_to_enemy_base() > 5000
        )

        controllables = [m for m in turn.monsters if controllable(h, m)]
        whooshables = [m for m in turn.monsters if whooshable(h, m)]
        shieldables = [m for m in turn.monsters if shieldable(h, m)]

        coin = choose([True, False, False])

        if (controllables and len(whooshables) < 3 and coin):
            t = min(controllables, key=lambda m: dist(m, h))
            mind.push_state(ControlSpiderToEnemy(t, direction='enemy_base'))
            return

        if (shieldables):
            t = min(shieldables, key=lambda m: dist(m, h))
            mind.push_state(ShieldSpider(t))
            return

        unshielded_enemies_in_front = [
            e for e in h.enemies_at_range()
            if e.distance_to_enemy_base() < h.distance_to_enemy_base()
            and not e.is_shielded()
        ]

        coin = choose([True, False, False])
        if (unshielded_enemies_in_front and coin): # and len(whooshables) > 2
            t = min(unshielded_enemies_in_front, key=lambda m: dist(m, h))
            mind.push_state(ShieldSpider(t))

        if (whooshables):
            t = min(whooshables, key=lambda m: dist(m, h))
            mind.push_state(GoTo(enemy_base))
            mind.push_state(WhooshSpiderToEnemy(t))
            return

        #if (unshielded_enemies_in_front and whooshables):
            #mind.push_state(WhooshAwayFrom(enemy_base))
            #return

        flank = choose(["attack_left", "attack_right"])

        if h.distance_to_enemy_base() > 9000:
            mind.push_state(GoTo(flank))
            return

        if h.distance_to_enemy_base() < 4000:
            mind.push_state(GoTo(flank))
            return

        shielded_enemies_nearby = [
            e for e in h.enemies_at_range()
            if e.distance_to_enemy_base() < h.distance_to_enemy_base()
            and e.is_shielded()
        ]

        unshielded_spiders_in_front = [
            m for m in h.monsters_at_hero_range()
            if m.distance_to_enemy_base() < h.distance_to_enemy_base()
            and not m.is_shielded()
        ]

        if (shielded_enemies_nearby and whooshables):
            mind.push_state(WhooshInto(enemy_base))
            return

        if (shielded_enemies_nearby and not whooshables and unshielded_spiders_in_front):
            mind.push_state(GoTo(enemy_base, max_steps=3))

        mind.push_state(Wander(
            until=lambda h: any(
                controllable(h, m) or whooshable(h, m) #or shieldable(h, m)
                for m in h.monsters_at_hero_range()
            )
        ))


class ShieldSpider(HeroState):
    def __init__(self, spider: Entity):
        self.spider = spider

    def display(self):
        return 's' + str(self.spider._id)
        
    def update(self, mind: HeroMind, turn: TurnState):
        self.spider = turn.update(self.spider)
        if not self.spider:
            mind.pop_state()
            return
        if not self.spider.is_shielded() and dist(self.spider, mind.hero) < HERO_RANGE:
            mind.DO("SPELL SHIELD", self.spider._id)
        mind.pop_state()


class WhooshSpiderToEnemy(HeroState):
    def __init__(self, spider: Entity):
        self.spider = spider

    def display(self):
        return 'we' + str(self.spider._id)
        
    def update(self, mind: HeroMind, turn: TurnState):
        self.spider = turn.update(self.spider)
        if not self.spider:
            mind.pop_state()
            return
        eb_x, eb_y = turn._game.pos("enemy_base")
        h, t = mind.hero, self.spider
        if not t.is_shielded() and dist(t, h) < HERO_RANGE:
            x, y = h.x + eb_x - t.x, h.y + eb_y - t.y
            mind.DO('SPELL WIND', x, y)
        mind.pop_state()


class WhooshAwayFrom(HeroState):
    def __init__(self, position):
        self.position = position

    def display(self):
        return 'wa'

    def update(self, mind: HeroMind, turn: TurnState):
        h, (px, py) = mind.hero, self.position
        x, y = h.x + h.x - px, h.y + h.y - py
        mind.DO('SPELL WIND', x, y)
        mind.pop_state()


class WhooshInto(HeroState):
    def __init__(self, position):
        self.position = position

    def display(self):
        return 'wi'

    def update(self, mind: HeroMind, turn: TurnState):
        mind.DO('SPELL WIND', self.position)
        mind.pop_state()


################################
# MAIN LOOP
################################

game = GameState()


hero_minds = {
    0: HeroMind(0, Farm()),
    1: HeroMind(1, Farm()),
    2: HeroMind(2, Defend())
}
hero_mindsss = {
    0: HeroMind(0, Defend()),
    1: HeroMind(1, Defend()),
    2: HeroMind(2, Defend())
}
team = TeamMind(hero_minds.values())

turn = None

# game loop
while True:
    turn = TurnState(game, turn)
    
    # if SEED == 0:
    #    SEED = turn._hash_for_rng()

    if turn.base_being_invaded() and turn.number > 40:
        hero_minds[0].new_objective(Defend())

    if turn.number == 90:
        hero_minds[0].new_objective(Defend())

    if turn.number < len(WORDS) and WORDS[turn.number] == "":
        CURRENT_SINGING_HERO = (CURRENT_SINGING_HERO + 1) % 3

    print(f"{hero_minds}", file=sys.stderr, flush=True)

    for i, mind in hero_minds.items():
        mind.update(team, turn)
    team.update(turn)
    for i, mind in hero_minds.items():
        mind.process_messages(turn)
    for i, mind in hero_minds.items():
        mind.step(turn)
