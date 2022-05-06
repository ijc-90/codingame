import sys
import math
import random

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

# base_x: The corner of the map representing your base
base_x, base_y = [int(i) for i in input().split()]

heroes_per_player = int(input())  # Always 3
max_x = 17630
max_y = 9000
enemy_base_x = abs(base_x - max_x)
enemy_base_y = abs(base_y - max_y)
area_radius = 5000
area_radius_square = 5000 ** 2
base_radius = 300
distance_from_base_to_trigger_wind = 5200
wind_range = 1280
wind_application_distance = 2200
control_range = 2200
vision_range = 2200
current_turn = 0
heroe_velocity = 800
monster_velocity = 400
distance_opponent_to_base_to_chase = 10000
last_turn_offensive_wind = False
heroe_damage = 2
base_distance_to_patrol = 11000
mana = 0
monster_hitbox = 800
step = 50
# global enemy_used_control_on_me
enemy_used_control_on_me = False
far_away_danger_range = 9000

MONSTER_TYPE = 0
HEROE_TYPE = 1
OPPONENT_TYPE = 2

enemy_base = {
    "x": enemy_base_x,
    "y": enemy_base_y,
}

my_base = {
    "x": base_x,
    "y": base_y,
}


def entity_distance(entity, other_entity):
    return distance(
        entity["x"],
        entity["y"],
        other_entity["x"],
        other_entity["y"],
    )


def convert_pos_to_relative_to_base(x, y):
    x = abs(x - base_x)
    y = abs(y - base_y)
    return (x, y)


# farming_positions = [
#     convert_pos_to_relative_to_base(7000, 1500),
#     convert_pos_to_relative_to_base(2500, 6000),
#     convert_pos_to_relative_to_base(int(max_x / 2), int(max_y * 2 / 3)),
#     convert_pos_to_relative_to_base(int(max_x / 2), int(max_y * 4 / 5)),
# ]
triangle_height = heroe_velocity * math.sqrt(3) / 2
farming_positions = [
    convert_pos_to_relative_to_base(int(max_x / 2), int(max_y * 4 / 5)),
    convert_pos_to_relative_to_base(int((max_x / 2) - heroe_velocity), int(max_y * 4 / 5)),
    convert_pos_to_relative_to_base(int((max_x / 2) - (heroe_velocity / 2)), int((max_y * 4 / 5) - triangle_height)),
]
# print(farming_positions, file=sys.stderr,flush=True)

attack_waiting_positions = [
    (abs(enemy_base_x - 2900), abs(enemy_base_y - 2900)),
    (abs(enemy_base_x - 2350), abs(enemy_base_y - 2350))

]

resting_positions = [
    convert_pos_to_relative_to_base(7000, 1500),
    convert_pos_to_relative_to_base(2500, 6000),
    convert_pos_to_relative_to_base(5500, 4200),
]


def quad_distance(x, y, j, k):
    return (
            (x - j) ** 2
            +
            (y - k) ** 2)


def distance(x, y, j, k):
    return math.sqrt(quad_distance(x, y, j, k))


def patrol_base_perimeter(distance_to_base=area_radius) -> tuple[int, int]:
    x = random.randint(0, 5000)
    y = round(math.sqrt(distance_to_base - x ** 2))
    if base_x == 0:
        return x, y
    else:
        return max_x - x, max_y - y


def anchor_base_perimeter(i, heroe_ids, distance_to_base=area_radius) -> tuple[int, int]:
    distance_to_base = int(distance_to_base)
    if len(heroe_ids) == 1:
        x = math.sqrt((distance_to_base ** 2) / 2)
    elif len(heroe_ids) == 2:
        if i == heroe_ids[0]:
            x = int(distance_to_base / 3)
        else:
            x = int(distance_to_base * 0.9)

    elif len(heroe_ids) == 3:
        if i == 0:
            x = math.sqrt((distance_to_base ** 2) / 2)
        elif i == 1:
            x = int(distance_to_base / 3)
        else:
            x = int(distance_to_base * 0.9)

    # if i == 0:
    #     x = random.randint(0, int(distance_to_base/3))
    # if i ==1:
    #     x = random.randint(int(distance_to_base/3), int(distance_to_base*2/3))
    # else:
    #     x = random.randint(int(distance_to_base*2/3), distance_to_base)
    y = round(math.sqrt((distance_to_base ** 2) - (x ** 2)))
    if base_x == 0:
        return int(x), int(y)
    else:
        return int(max_x - x), int(max_y - y)


def go_to_base(i):
    return base_x, base_y


def chase_monster(heroe, monster) -> tuple[int, int]:
    return monster["x"] + monster["vx"], monster["y"] + monster["vy"]


def chase_second_most_dangerous_monster(heroe, monsters):
    if monsters:
        if len(monsters) > 1:
            return chase_monster(heroe, monsters[1])
        return chase_monster(heroe, monsters[0])
    else:
        return base_x, base_y


def chase_most_dangerous_monster(heroe, monsters):
    if monsters:
        return chase_monster(heroe, monsters[0])
    else:
        return base_x, base_y


def chase_closest_monster_by_turns(heroe, monsters):
    if monsters:
        new_monsters = sorted(
            monsters,
            key=lambda m: turns_to_reach(
                (heroe["x"], heroe["y"]),
                (m["x"], m["y"]),
                (m["vx"], m["vy"]),
                range_threeshold=heroe_velocity
            )
        )
        return chase_monster(heroe, new_monsters[0])
    else:
        return base_x, base_y


def chase_closest_monster_by_distance(heroe, monsters):
    if monsters:
        new_monsters = sorted(
            monsters,
            key=lambda m: (
                quad_distance(m["x"], m["y"], heroe["x"], heroe["y"])
            )
        )
        return chase_monster(heroe, new_monsters[0])
    else:
        return base_x, base_y


def chase_closest_monster_to_base(heroe, monsters):
    if monsters:
        new_monsters = sorted(
            monsters,
            key=lambda m: (
                quad_distance(m["x"], m["y"], base_x, base_y)
            )
        )
        return chase_monster(heroe, new_monsters[0])
    else:
        return base_x, base_y


def adopt_resting_position(heroes):
    for heroe in heroes:
        h_id = heroe["heroe_id"]
        x, y = resting_positions[h_id]
        print(f"MOVE {x} {y} {h_id}-REST")


def calculate_turns_for_monster_to_reach_base(monster, base):
    distance_to_base_radius = entity_distance(
        monster, base
    ) - base_radius
    if distance_to_base_radius <= 0:
        print("impossible print")
        return 0  # shouldnt happen

    # distance <= 400 -> 1 (end of this turn)
    # 400 < distance <= 800 2 (end of next turn)
    return math.ceil(distance_to_base_radius / monster_velocity)

    # old way
    # return math.ceil(entity_distance(monster, enemy_base)/monster_velocity)


def hits_to_kill(m):
    return math.ceil(m["health"] / heroe_damage)

def defending_rotation(heroe,monsters, heroes, opponents):
    sorted(opponents,
    key=lambda o: entity_distance(o,my_base)
    )
    opponent_dangerous = opponents and entity_distance(opponents[0],my_base) < 9000
    if not opponent_dangerous:
        return convert_pos_to_relative_to_base(2500,2500), "rotate"
    else:
        return (
            int((opponents[0]["x"]+my_base["x"])/2),
            int((opponents[0]["y"]+my_base["y"])/2),
        ), "def-heroe"



def defend_base(monsters, heroes, opponents):
    global enemy_used_control_on_me
    # print(f"enemy_used_control_on_me {enemy_used_control_on_me} ", file=sys.stderr, flush = True)
    farm_found = ""
    most_dangerous_monster = monsters[0]
    if len(monsters) > 1:
        second_most_dangerous_monster = monsters[1]
    else:
        second_most_dangerous_monster = monsters[0]

    turns_for_danger_to_reach_base = calculate_turns_for_monster_to_reach_base(
        most_dangerous_monster, my_base
    )

    sorted_heroes = sorted(heroes,
                           key=lambda h: quad_distance(
                               h["x"],
                               h["y"],
                               most_dangerous_monster["x"],
                               most_dangerous_monster["y"],
                           )
                           )
    closer_heroe = sorted_heroes[0]

    danger_is_far_away = entity_distance(most_dangerous_monster,my_base)>far_away_danger_range

    hits_needed_for_danger = hits_to_kill(most_dangerous_monster)
    hits_available = 0
    hits_available_by_heroe = {}
    turns_to_reach_danger_by_heroe = {}
    for heroe in heroes:
        turns_to_reach_danger_to_hit = turns_to_reach(
            (heroe["x"], heroe["y"]),
            (most_dangerous_monster["x"], most_dangerous_monster["y"]),
            (most_dangerous_monster["vx"], most_dangerous_monster["vy"])
        )
        turns_to_reach_danger_to_wind = turns_to_reach(
            (heroe["x"], heroe["y"]),
            (most_dangerous_monster["x"], most_dangerous_monster["y"]),
            (most_dangerous_monster["vx"], most_dangerous_monster["vy"]),
            wind_range,
            premove = False
        )
        turns_to_reach_danger_by_heroe[heroe["heroe_id"]] = {
            'hit': turns_to_reach_danger_to_hit,
            'wind': turns_to_reach_danger_to_wind
            }
        if turns_to_reach_danger_to_hit == 0:
            hits_available_this_heroe = turns_for_danger_to_reach_base
        else:
            # if reach time is 1 I reach it by this turn
            hits_available_this_heroe = turns_for_danger_to_reach_base - (turns_to_reach_danger_to_hit - 1)
        hits_available+=max(hits_available_this_heroe,0)
        hits_available_by_heroe[heroe["heroe_id"]] = hits_available_this_heroe

    danger_avoidable_by_hits = hits_available >= hits_needed_for_danger
    if turns_for_danger_to_reach_base <= most_dangerous_monster["shield_life"]:
        #Shield will be in place until reach base
        danger_avoidable_by_wind = False
    else:
        danger_avoidable_by_wind = (
            turns_to_reach_danger_by_heroe[closer_heroe["heroe_id"]]["wind"] 
            < turns_for_danger_to_reach_base
        )
        # Shield will be out before reaching_base
    
    danger_avoidable = (
        danger_avoidable_by_hits
        or danger_avoidable_by_wind
    )



    # print(f"closer heroe: {closer_heroe['id']}", file=sys.stderr,flush=True)
    # print(f"heroe: {closer_heroe['x'],closer_heroe['y']}", file=sys.stderr,flush=True)
    # print(f"monster: {most_dangerous_monster['id']}", file=sys.stderr,flush=True)
    # print(f"monster: {most_dangerous_monster['x'],most_dangerous_monster['y']}", file=sys.stderr,flush=True)
    # print(f"monsterv: {most_dangerous_monster['vx'],most_dangerous_monster['vy']}", file=sys.stderr,flush=True)
    # print(f"monster_shield: {most_dangerous_monster['shield_life']}", file=sys.stderr,flush=True)
    # print(f"hits_by_heroe: {hits_available_by_heroe}", file=sys.stderr,flush=True)
    # print(f"danger_avoidable: {danger_avoidable}", file=sys.stderr,flush=True)
    # print(f"by_hits: {danger_avoidable_by_hits}", file=sys.stderr,flush=True)
    # print(f"by_wind: {danger_avoidable_by_wind}", file=sys.stderr,flush=True)
    # print(f"turns_for_danger_to_reach_base {turns_for_danger_to_reach_base}", file=sys.stderr,flush=True)
    # print(f"turns_to_reach_danger {turns_to_reach_danger_by_heroe}", file=sys.stderr,flush=True)

    if not danger_avoidable:
        print(f"abandon hope: {most_dangerous_monster['id'],second_most_dangerous_monster['id']}", file=sys.stderr,flush=True)    
        most_dangerous_monster=second_most_dangerous_monster
    elif not danger_avoidable_by_wind:
        #only avoidable by hits
        if hits_available_by_heroe[closer_heroe["heroe_id"]] < hits_needed_for_danger:
            print(f"focus_fire: {most_dangerous_monster['id']}", file=sys.stderr,flush=True)    
            second_most_dangerous_monster = most_dangerous_monster
    


    # heroes_needed_to_kill = math.ceil(
    #     hits_needed_for_danger/turns_for_danger_to_reach_base
    # )
    # danger_unavoidable = (
    #     most_dangerous_monster["shield_life"]>=turns_for_danger_to_reach_base
    #     # and
    #     )

    # decidir si ir a buscar al primer bicho o no, cuanto tardo en llegar, si tiene escudo, etc


    for heroe in heroes:
        print(f"heroe {heroe['id']} has {heroe['shield_life']} shield", file=sys.stderr,flush=True)
        if heroe["is_controlled"]:
            print(f"heroe {heroe['id']} is controlled", file=sys.stderr,flush=True)
            enemy_used_control_on_me = True
            print("WAIT controlled")
            continue
        opponent_in_control_range = list(
            filter(
                lambda o: entity_distance(o, heroe) < control_range,
                opponents
            )
        )
        targeting_monster = most_dangerous_monster if heroe == closer_heroe else second_most_dangerous_monster
        if (
                # targeting_monster["near_base"] and
                distance(
                    targeting_monster['x'],
                    targeting_monster['y'],
                    base_x,
                    base_y
                ) < distance_from_base_to_trigger_wind and
                mana > 10 and
                distance(
                    targeting_monster['x'],
                    targeting_monster['y'],
                    heroe['x'],
                    heroe['y'],
                ) < wind_range
                and targeting_monster['shield_life'] <= 0
                # and not wind_used
        ):
            # wind_used = True
            x, y = int(abs(enemy_base_x)), int(abs(enemy_base_y))
            print(f"SPELL WIND {x} {y} {heroe['heroe_id']}-WIND")
        elif (
                opponent_in_control_range
                and mana > 10
                and heroe["shield_life"] <= 0
                and enemy_used_control_on_me
        ):
            print(f"SPELL SHIELD {heroe['id']} {heroe['heroe_id']}-protec")
        else:
            if danger_is_far_away and heroe != closer_heroe:
                (x,y), mes = defending_rotation(heroe,monsters, heroes, opponents)
            else:
                (x, y), farm_found = find_optimal_defending_position(heroe, targeting_monster, monsters)
                mes=f"DEF{farm_found}"
            print(f"MOVE {x} {y} {heroe['heroe_id']}-{mes}")


def chase_closest(monsters, heroes):
    for heroe in heroes:
        x, y = chase_closest_monster_by_distance(heroe, monsters)
        print(f"MOVE {x} {y} {heroe['heroe_id']}-chase_closest")


def default_chase(monsters, heroes):
    chase_within_quadrant(monsters, heroes)
    # chase_closest_to_base_within_resting_position(monsters, heroes)


def chase_within_quadrant(monsters, heroes):
    for heroe in heroes:
        if base_x == 0:
            if heroe["heroe_id"] == 0:
                condition = lambda m: m["x"] >= m["y"]
            else:
                condition = lambda m: m["x"] <= m["y"]
        else:
            if heroe["heroe_id"] == 1:
                condition = lambda m: m["x"] - 8630 >= m["y"]
            else:
                condition = lambda m: m["x"] - 8630 <= m["y"]
        new_monsters = [
            m for m in monsters
            if entity_distance(m, my_base) <= base_distance_to_patrol
               and condition(m)
        ]
        new_monsters.sort(
            key=lambda m: (
                entity_distance(m, heroe) + 1000 if m["threat_for"] in (0, 2)
                else entity_distance(m, heroe)
            )
        )

        if new_monsters:
            x, y = chase_monster(heroe, new_monsters[0])
            print(f"MOVE {x} {y} {heroe['heroe_id']}-CHASE")
        else:
            x, y = resting_positions[heroe["heroe_id"]]
            print(f"MOVE {x} {y} {heroe['heroe_id']}-REST")


def chase_closest_to_base_within_resting_position(monsters, heroes):
    for heroe in heroes:
        new_monsters = [
            m for m in monsters
            if distance(m["x"], m["y"], *resting_positions[heroe["heroe_id"]]) < vision_range
        ]
        new_monsters.sort(
            key=lambda m: (
                distance(m["x"], m["y"], base_x, base_y) + 1000 if m["threat_for"] in (0, 2)
                else distance(m["x"], m["y"], base_x, base_y)
            )
        )
        if new_monsters:
            x, y = chase_monster(heroe, new_monsters[0])
            # turns_to_reach_monster = turns_to_reach(
            #     (heroe["x"], heroe["y"]),
            #     (x, y),
            #     (new_monsters[0]["vx"], new_monsters[0]["vy"]),
            #     range_threeshold=0
            # )
            print(f"MOVE {x} {y} {heroe['heroe_id']}-chase_to_base_within_resting")
        else:
            x, y = resting_positions[heroe["heroe_id"]]
            print(f"MOVE {x} {y} {heroe['heroe_id']}-REST-chase_to_base_within_resting")


def chase_closest_within_resting_position(monsters, heroes):
    for heroe in heroes:
        x, y = chase_closest_monster_by_distance(heroe, monsters)

        if distance(x, y, *resting_positions[heroe["heroe_id"]]) < vision_range:
            print(f"MOVE {x} {y} {heroe['heroe_id']}-chase_closest_within_resting")
        else:
            x, y = resting_positions[heroe["heroe_id"]]
            print(f"MOVE {x} {y} {heroe['heroe_id']}-chase_closest_within_resting")


def find_optimal_farming_spot(heroe, monsters):
    optimal_spot_farm = 0
    optimal_spot = monsters[0]["x"], monsters[0]["x"]
    offset = heroe_velocity
    for i in range(heroe["x"] - offset, heroe["x"] + offset + step, step):
        for j in range(heroe["y"] - offset, heroe["y"] + offset + step, step):
            this_spot_entity = {"x": i, "y": j}
            if entity_distance(heroe, this_spot_entity) > heroe_velocity:
                # print(f"unreachable point{this_spot}", file=sys.stderr,flush=True)
                continue
            else:
                monsters_in_hit_range = [
                    m for m in monsters
                    if entity_distance(this_spot_entity, m) <= monster_hitbox
                ]
                if len(monsters_in_hit_range) > optimal_spot_farm:
                    optimal_spot_farm = len(monsters_in_hit_range)
                    optimal_spot = (i, j)
    return optimal_spot, optimal_spot_farm


def find_optimal_defending_position(heroe, targeting_monster, monsters):
    optimal_spot_farm = 0
    optimal_spot = chase_monster(heroe, targeting_monster)
    offset = heroe_velocity
    for i in range(heroe["x"] - offset, heroe["x"] + offset + step, step):
        for j in range(heroe["y"] - offset, heroe["y"] + offset + step, step):
            this_spot_entity = {"x": i, "y": j}
            if (
                    entity_distance(heroe, this_spot_entity) > heroe_velocity
                    or entity_distance(targeting_monster, this_spot_entity) > monster_hitbox
            ):
                # print(f"unreachable point{this_spot}", file=sys.stderr,flush=True)
                continue
            else:
                monsters_in_hit_range = [
                    m for m in monsters
                    if entity_distance(this_spot_entity, m) <= monster_hitbox
                ]
                if len(monsters_in_hit_range) > optimal_spot_farm:
                    optimal_spot_farm = len(monsters_in_hit_range)
                    optimal_spot = (i, j)
                elif len(monsters_in_hit_range) == optimal_spot_farm:
                    optimal_spot_entity = {"x": optimal_spot[0], "y": optimal_spot[1]}
                    if entity_distance(optimal_spot_entity, my_base) > entity_distance(this_spot_entity, my_base):
                        optimal_spot = (i, j)
    return optimal_spot, optimal_spot_farm


def farm_wild_mana(monsters, heroes, default_poistions, current_turn):
    # new_monsters.sort(
    #     key=lambda m: (
    #             distance(m["x"], m["y"], base_x, base_y) + (100000 * (1-m["threat_for"]))
    #     )
    # )

    for heroe in heroes:
        farm_found = ""

        new_monsters = [
            m for m in monsters
            if entity_distance(heroe, m) <= heroe_velocity + monster_hitbox
            # and not entity_distance(m,enemy_base) <= area_radius
            # not m["near_base"] and not m["threat_for"] == 1
        ]
        # for m in new_monsters:
        if len(new_monsters) == 1:
            x, y = new_monsters[0]["x"], new_monsters[0]["y"]
        elif new_monsters:
            spot, farm_found = find_optimal_farming_spot(heroe, new_monsters)
            x, y = spot

        else:
            p_index = current_turn % len(default_poistions)
            x, y = default_poistions[p_index]
        print(f"MOVE {x} {y} {heroe['heroe_id']}-farm{farm_found}")


def turns_to_reach(heroe_position, monster_position, monster_velocity, range_threeshold=800, premove=True, turns_so_far=0):
    if (
            distance(*heroe_position, *monster_position) <= range_threeshold
            or turns_so_far > 15
    ):
        return turns_so_far
    turns_so_far += 1
    new_monster_position = (
        monster_position[0] + monster_velocity[0],
        monster_position[1] + monster_velocity[1],
    )
    horoe_monster_vector = (
        new_monster_position[0] - heroe_position[0],
        new_monster_position[1] - heroe_position[1],
    )
    if premove:
        d = distance(*monster_position, *heroe_position)
    else:
        d = distance(*new_monster_position, *heroe_position)
    if d <= range_threeshold + heroe_velocity:
        return turns_so_far
    distance_to_next_position = distance(*new_monster_position, *heroe_position)
    heroe_monster_vector_normalized = (
        horoe_monster_vector[0] / distance_to_next_position,
        horoe_monster_vector[1] / distance_to_next_position,
    )

    heroe_position = (
        int(heroe_position[0] + (heroe_velocity * heroe_monster_vector_normalized[0])),
        int(heroe_position[1] + (heroe_velocity * heroe_monster_vector_normalized[1])),
    )
    return turns_to_reach(
        heroe_position,
        new_monster_position,
        monster_velocity,
        range_threeshold,
        premove=premove,
        turns_so_far=turns_so_far
    )


# def disrupt_enemy_with_wind(opponents, heroe):
#     global last_turn_offensive_wind
#     opponents = [
#         o for o in opponents
#         if distance(
#             o["x"],
#             o["y"],
#             enemy_base_x,
#             enemy_base_y
#         ) < distance_opponent_to_base_to_chase
#         and o["shield_life"] <= 0
#     ]
#     if not opponents:
#         if last_turn_offensive_wind:
#             x,y = abs(enemy_base_x), abs(enemy_base_y)
#             print(f"MOVE {enemy_base_x} {base_y} chase-WIND")
#         else:
#             x,y = abs(enemy_base_x - 2500), abs(enemy_base_y - 2500)
#             last_turn_offensive_wind=False
#             print(f"MOVE {x} {y} LOOKING")
#         return
#     opponents.sort(
#         key= lambda o: quad_distance(
#             o["x"],
#             o["x"],
#             enemy_base_x,
#             enemy_base_x,
#             )
#
#     )
#     if len(opponents) == 1:
#         o = opponents[0]
#         if False and entity_distance(o,heroe) < wind_range:
#             last_turn_offensive_wind=True
#             print(f"SPELL WIND {enemy_base_x} {base_y} WIND1")
#         elif (
#             entity_distance(o,heroe) < control_range
#             and distance(o["x"],o["y"],enemy_base_x,enemy_base_y) < 6000
#         ):
#             print(f"SPELL CONTROL {o['id']} {enemy_base_x} {base_y}")
#         else:
#             last_turn_offensive_wind=False
#             print(f"MOVE {o['x']} {o['y']} FOLLOW")
#     else:
#         opponents_in_range = [
#             o for o in opponents
#             if entity_distance(o,heroe) < wind_range
#         ]
#         if len(opponents_in_range) > 1:
#             last_turn_offensive_wind=True
#             print(f"SPELL WIND {enemy_base_x} {base_y} WIND2")
#         else:
#             x, y = (
#                 int((opponents[0]["x"]+opponents[1]["x"])/2),
#                 int((opponents[0]["y"]+opponents[1]["y"])/2),
#             )
#             last_turn_offensive_wind=False
#             print(f"MOVE {x} {y} PROMEDIO")

def attack_enemy_base(opponents, monsters, heroe):
    global enemy_used_control_on_me
    if heroe["is_controlled"]:
        enemy_used_control_on_me = True
        print("WAIT controled")
        return

    waiting_positions = [
        (abs(enemy_base_x - 3450), abs(enemy_base_y - 3450)),
        (abs(enemy_base_x - 2900), abs(enemy_base_y - 2900)),
        (abs(enemy_base_x - 2350), abs(enemy_base_y - 2350)),
        
    ]

    most_dangerous_monster_for_enemy = sorted(
        monsters,
        key=lambda m: entity_distance(m, enemy_base)
    )
    opponents = [
        o for o in opponents
        if distance(
            o["x"],
            o["y"],
            heroe["x"],
            heroe["y"]
        ) < control_range
           and o["shield_life"] <= 0
    ]
    # used to disrupt enemy most far away from dirsupting point
    # opponents.sort(
    #     key=lambda o: -distance(
    #         o["x"],
    #         o["y"],
    #         enemy_base_x,
    #         base_y
    #     )
    # )
    # prioritize enemies closer to monster threatening them
    if most_dangerous_monster_for_enemy:
        entity_to_compare_to = most_dangerous_monster_for_enemy[0]
    else:
        entity_to_compare_to = enemy_base
    opponents.sort(
        key=lambda o: entity_distance(
            o, entity_to_compare_to
        )
    )
    monsters_in_control_range = [
        m for m in monsters
        if m["threat_for"] in (0, 1)
           and entity_distance(m, heroe) < control_range
           and m["health"] >= 15
           and m["shield_life"] <= 0
    ]
    monsters_in_wind_range = [
        m for m in monsters
        if entity_distance(m, heroe) < wind_range
           and m["shield_life"] <= 0
    ]
    monsters_in_wind_range.sort(
        key=lambda m: entity_distance(
            m, enemy_base
        )
    )
    monsters_by_distance_to_enemy_base = sorted(
        monsters,
        key=lambda m: (
            quad_distance(m["x"], m["y"], enemy_base_x, enemy_base_y)
        )
    )
    # shield monster will kill against one heroe
    for m in monsters_by_distance_to_enemy_base:
        # turns_to_reach_base = math.ceil(entity_distance(m, enemy_base)/400)
        turns_to_reach_base = calculate_turns_for_monster_to_reach_base(m,enemy_base)
        turns_to_kill_by_one_heroe = hits_to_kill(m)
        if (
                m["near_base"]
                and m["threat_for"] == 2  # opponent base
                and turns_to_reach_base <= turns_to_kill_by_one_heroe
                and m["shield_life"] <= 0
        ):
            print(f"SPELL SHIELD {m['id']}")
            return

    if monsters_in_wind_range and (
        len(monsters_in_wind_range) >= 3
        or entity_distance(monsters_in_wind_range[0],enemy_base) <= wind_application_distance + base_radius
    ):
        print(f"SPELL WIND {enemy_base_x} {enemy_base_y}")
    elif opponents:
        o = opponents[0]
        print(f"SPELL CONTROL {o['id']} {enemy_base_x} {base_y}")
    elif (
            monsters_in_wind_range
            and entity_distance(enemy_base, monsters_in_wind_range[0]) < 7100
    ):
        print(f"SPELL WIND {enemy_base_x} {enemy_base_y}")
    elif monsters_in_control_range and mana > 60:
        m = monsters_in_control_range[0]
        print(f"SPELL CONTROL {m['id']} {enemy_base_x} {enemy_base_y}")
    else:
        x,y = waiting_positions[current_turn%len(waiting_positions)]
        # if (heroe["x"], heroe["y"]) == waiting_position:
        #     x, y = waiting_position_variant
        # else:
        #     x, y = waiting_position
        print(f"MOVE {x} {y}")


# game loop
should_attack = False
last_turn_to_farm = 40
while True:
    current_turn += 1
    monsters = []
    heroes = []
    opponents = []
    for i in range(2):
        # health: Your base health
        # mana: Ignore in the first league; Spend ten mana to cast a spell
        if i == 0:
            health, mana = [int(j) for j in input().split()]
        else:
            _, _ = [int(j) for j in input().split()]
        # print(f"mana {mana}", file=sys.stderr, flush=True)
    entity_count = int(input())  # Amount of heros and monsters you can see
    for i in range(entity_count):
        # _id: Unique identifier
        # _type: 0=monster, 1=your hero, 2=opponent hero
        # x: Position of this entity
        # shield_life: Ignore for this league; Count down until shield spell fades
        # is_controlled: Ignore for this league; Equals 1 when this entity is under a control spell
        # health: Remaining health of this monster
        # vx: Trajectory of this monster
        # near_base: 0=monster with no target yet, 1=monster targeting a base
        # threat_for: Given this monster's trajectory, is it a threat to 1=your base, 2=your opponent's base, 0=neither
        (
            _id,
            _type,
            x,
            y,
            shield_life,
            is_controlled,
            health,
            vx,
            vy,
            near_base,
            threat_for,
        ) = [int(j) for j in input().split()]
        a = vy / vx if vx > 0 else 99999
        entity = {
            "id": _id,
            "type": _type,
            "x": x,
            "y": y,
            "shield_life": shield_life,
            "is_controlled": is_controlled,
            "health": health,
            "vx": vx,
            "vy": vy,
            "a": a,
            "b": y - (x * a),
            "near_base": near_base,
            "threat_for": threat_for,
        }
        if entity["type"] == MONSTER_TYPE:
            monsters.append(entity)

        if entity["type"] == HEROE_TYPE:
            entity["heroe_id"] = entity["id"] % 3
            heroes.append(entity)

        if entity["type"] == OPPONENT_TYPE:
            entity["opponent_id"] = entity["id"] % 3
            opponents.append(entity)
    threatening_monsters = [
        m for m in monsters
        if m["threat_for"] == 1
    ]
    threatening_monsters.sort(
        key=lambda m: (
            quad_distance(m["x"], m["y"], base_x, base_y)
        )
    )
    def monster_priority(m):
        d = distance(m["x"], m["y"], base_x, base_y)
        if d > base_distance_to_patrol:
            d = d*3
        if m["threat_for"] != 1:
            d = d*2
        return d
    monsters.sort(
        key=monster_priority
    )

    defending_heroes = [
        heroes[0],
        heroes[1],
    ]

    attacking_heroes = [
        heroes[2]
    ]

    # defenders
    threat_inside_base = threatening_monsters and threatening_monsters[0]["near_base"]
    # if threat_inside_base:
    # defend_base(threatening_monsters, defending_heroes, opponents)
    # else:

    print(
        [
            {'id':o['id'],'pos':(o['x'],o['y'])}
            for o in opponents
        ]
    ,file=sys.stderr, flush=True)

    if monsters and \
    entity_distance(monsters[0],my_base) < base_distance_to_patrol:
        defend_base(monsters, defending_heroes, opponents)
        # dxefault_chase(monsters, defending_heroes)
    else:
        adopt_resting_position(defending_heroes)

    # attackers
    if should_attack:
        if mana <= 50:
            should_attack = False
        attack_enemy_base(opponents, monsters, attacking_heroes[0])
    else:
        farm_wild_mana(monsters, attacking_heroes, farming_positions, current_turn)
        if (current_turn >= last_turn_to_farm and mana > 100) or mana > 250:
            should_attack = True
