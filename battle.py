from time import sleep
import random
import csv
import sys
import os

# Logic is mixed between main and trainer classes for decisions
# It's becoming increasingly convoluted how I handle turns / skipping them

csv_read = lambda name: csv.DictReader(open(os.path.join(os.getcwd(), 'pokemon data', name)))
print_pause = lambda msg, sleep_time=2: (sys.stdout.write(msg+'\n'), sleep(sleep_time))


class Main:

    def __init__(self):
        ## Having two full rosters of pokemon makes the load time ~1.30 seconds, make that better

        level_range = lambda: random.randint(14, 17)

        self.player = Trainer('Player', 'Red', computer=False)
        self.opponent = Trainer('Rival', 'Steven')

        starters = [
            Pokemon(level=16, pokemon_id='1'),  # Bulbasaur
            Pokemon(level=16, pokemon_id='4'),  # Charmander
            Pokemon(level=16, pokemon_id='7')   # Squirtle
        ]

        self.player.roster_add_pokemon(starters.pop(starters.index(random.choice(starters))))
        self.opponent.roster_add_pokemon(starters.pop(starters.index(random.choice(starters))))

        self.player.roster_add_pokemon(Pokemon('25', level_range()))     # Pikachu
        self.player.roster_add_pokemon(Pokemon('12', level_range()))     # Butterfree
        self.player.roster_add_pokemon(Pokemon('17', level_range()))     # Pidgeotto
        self.player.roster_add_pokemon(Pokemon('35', level_range()))     # Clefairy

        self.opponent.roster_add_pokemon(Pokemon('125', level_range()))  # Electabuzz
        self.opponent.roster_add_pokemon(Pokemon('27', level_range()))   # Sandshrew
        self.opponent.roster_add_pokemon(Pokemon('32', level_range()))   # Nidoran
        self.opponent.roster_add_pokemon(Pokemon('37', level_range()))   # Vulpix

        self.player.item_receive(Item('17'))    # Potion
        self.player.item_receive(Item('17'))    # Potion
        self.player.item_receive(Item('26'))    # Super Potion

        self.opponent.item_receive(Item('17'))    # Potion
        self.opponent.item_receive(Item('17'))    # Potion
        self.opponent.item_receive(Item('26'))    # Super Potion

        self.battle(self.opponent)

    ###

    def battle(self, trainer):
        print_pause('{} {} has challenged you to a fight!'.format(trainer.title, trainer.name))
        print_pause('{} sends out {}!'.format(trainer.name, trainer.lead_pokemon.nickname))
        print_pause('Go, {}!\n'.format(self.player.lead_pokemon.nickname))

        self.player.battling = True
        self.player.current_pokemon = self.player.lead_pokemon
        self.player.run_away_attempts = 0

        trainer.current_pokemon = trainer.lead_pokemon

        while self.player.battling:
            self.player_input(trainer)

    def player_input(self, opponent):
        functions = {'Attack': self.menu_attack, 'Items': self.menu_item,
                     'Pokemon': self.menu_pokemon, 'Run': self.menu_run}
        options = {1: 'Attack', 2: 'Pokemon', 3: 'Items', 4: 'Run'}
        formatting = ['[ {0}: {1: ^15} ]'.format(x, y) for x, y in options.iteritems()]
        turn_over = False

        while not turn_over:
            print '{}       {}\n{}       {}'.format(*formatting)
            choice = raw_input('Choice [#]: ')
            print

            if choice.isdigit() and options.get(int(choice), None):

                function = functions[options[int(choice)]]
                action = function(opponent)

                if action:
                    if isinstance(action, Ability):
                        self.attack_turn(opponent, action)
                    if isinstance(action, Item):
                        if not self.player.item_use(action):
                            break
                        self.free_turn_opponent(opponent)
                    if action == 'Escape Failed.\n':
                        print_pause(action)
                        self.free_turn_opponent(opponent)

                    turn_over = True

    def attack_turn(self, opponent, action):
        opponent_decision = opponent.computer_ai_turn()

        if isinstance(opponent_decision, Ability):
            turn_order = self.determine_turn(opponent, action, opponent_decision)

            for pokemon, enemy, skill in turn_order:
                pokemon.attack(enemy, skill)
                if self.pokemon_condition_changed(opponent):
                    break

        elif isinstance(opponent_decision, Item):
            opponent.item_use(opponent_decision)
            self.free_turn_player(opponent, action)

    def pokemon_condition_changed(self, opponent):
        if opponent.current_pokemon.fainted:
            print '{} has fainted!'.format(opponent.current_pokemon.nickname)

            exp_earned = self.player.current_pokemon.calculate_experience(opponent.current_pokemon)
            evs_earned = opponent.current_pokemon.retrieve_effort_values()
            self.player.current_pokemon.receive_effort_values(evs_earned)
            self.player.current_pokemon.receive_experience(exp_earned)

            self.battle_knockout(opponent)

            if opponent.out_of_pokemon:
                print '{} is out of pokemon. You won!'.format(opponent.name)
                self.player.battling = False

            return True

        if self.player.current_pokemon.fainted:
            print '{} has fainted!'.format(self.player.current_pokemon.nickname)
            self.battle_knockout(self.player)

            if self.player.out_of_pokemon:
                print 'You are out of pokemon. You lose!'
                self.player.battling = False

            return True

    ###

    def menu_attack(self, *args):
        # TODO: Account for moves that do not do damage (statuses, field effects, etc)
        # TODO: Set and reset battle variables, like increasing critical stages

        null_finder = lambda attack: attack.proper_name if attack else '-----'
        current_pokemon = self.player.current_pokemon
        skills = current_pokemon.skill_set
        formatting = ['[ {0}: {1: ^15} ]'.format(x+1, null_finder(y)) for x, y in skills.iteritems()]

        while True:
            print '{}       {}\n{}       {}'.format(*formatting)
            choice = raw_input('Choice [#]: ')

            if choice.isdigit() and skills.get(int(choice)-1, None):
                skill = skills[int(choice)-1]

                if skill.damage_type == 'status':
                    print "Didn't code status changing moves in yet.\n"  # TODO
                    return False

                if skill.pp == 0:
                    print 'Not enough PP to use this move!\n'
                    return False

                print
                return skill

            print
            return False

    def menu_pokemon(self, opponent):
        roster = self.player.roster

        while True:
            for slot, pokemon in roster.iteritems():
                if pokemon:
                    print '{}: {} ({}), {}/{} hp'.format(slot+1, *pokemon.retrieve_pokemon_sheet_stats())

            choice = raw_input('\nSend out another pokemon? [y/n]: ')

            if choice == 'y':
                pokemon_roster_number = raw_input('Who do you want to send out? [#]: ')

                if pokemon_roster_number.isdigit() and roster.get(int(pokemon_roster_number)-1, None):
                    pokemon = roster[int(pokemon_roster_number)-1]
                    confirm_choice = raw_input('Send out {}? [y/n]: '.format(pokemon.nickname))

                    if confirm_choice == 'y':
                        if pokemon == self.player.current_pokemon:
                            print '{} is already out.'.format(pokemon.nickname)

                        elif pokemon.current_hp == 0:
                            print "{} is out of HP.".format(pokemon.nickname)

                        else:
                            print_pause('\nCome back, {}!'.format(self.player.current_pokemon.nickname))
                            self.player.current_pokemon = pokemon
                            print_pause('Go, {}!\n'.format(pokemon.nickname))

                            opponents_skill = opponent.computer_ai_turn()
                            opponent.current_pokemon.attack(pokemon, opponents_skill)
                            self.pokemon_condition_changed(self.player)

                            print
                            return True

            if choice == 'n':
                print
                return False

    def menu_item(self, *args):
        inventory = self.player.battle_inventory()
        items = {}
        amount = {}

        for item_type, item_list in inventory.iteritems():
            for item in item_list:
                if item.name in [x for x in items.iterkeys()]:
                    amount[item.name] += 1
                    items[item.name].append(item)
                else:
                    amount[item.name] = 1
                    items[item.name] = [item]

        choice_list = dict(enumerate((key for key in amount.iterkeys()), start=1))

        # todo: Find a way to also show the KEY of the item
        for number, item in choice_list.iteritems():
            print '{0}: {1: <15} [amount: {2}]'.format(number, item.capitalize(), amount[item])

        choice = raw_input('\nWhat will you choose? [#]: ')
        print

        if choice.isdigit() and choice_list.get(int(choice), None):
            item_choice = choice_list[int(choice)]
            item = items[item_choice].pop(0)

            # todo
            if item.purpose != 'healing':
                print 'No item types other than healing have been coded to work in the game yet.\n'
                items[item_choice].append(item)
                return False

            return item

        return False

    def menu_run(self, opponent):
        player_speed = self.player.current_pokemon.stats['speed']['total']
        opponent_speed = (opponent.current_pokemon.stats['speed']['total'] / 4) % 256
        attempts = self.player.run_away_attempts + 1
        formula = (((player_speed * 32) / opponent_speed) + 30) * attempts
        roll = random.randint(0, 255)

        print_pause('Trying to escape ...')

        if formula >= 255 or roll < formula:
            print 'Escape successful!\n'
            self.player.battling = False

        else:
            self.player.run_away_attempts += 1
            return 'Escape failed.\n'

    ###

    def battle_knockout(self, trainer):
        trainer.knocked_out.append(trainer.current_pokemon)
        pokemon_choices = trainer.roster_retrieve_capable_pokemon()

        if pokemon_choices:
            self.battle_swap(pokemon_choices, trainer)
        else:
            trainer.out_of_pokemon = True

    def battle_swap(self, pokemon_choices, trainer):
        if trainer.computer:
            new_pokemon = random.choice(pokemon_choices)

            while True:

                choice = raw_input('{} is about to send out {}. Swap pokemon? [y/n]: '
                                   .format(trainer.name, new_pokemon.nickname))
                if choice == 'y':
                    roster = self.player.roster_retrieve_capable_pokemon()
                    for slot, pokemon in enumerate(roster, start=1):
                        print '{}: {} ({}), {}/{} hp'.format(slot, *pokemon.retrieve_pokemon_sheet_stats())
                    pokemon_roster_number = raw_input('\nWho do you want to send out? [#]: ')

                    if pokemon_roster_number.isdigit() and int(pokemon_roster_number)-1 in range(0, len(roster)):
                        pokemon = roster[int(pokemon_roster_number)-1]
                        confirm_choice = raw_input('Send out {}? [y/n]: '.format(pokemon.nickname))

                        if confirm_choice == 'y':
                            print_pause('\nReturn, {}!'.format(self.player.current_pokemon.nickname))
                            self.player.current_pokemon = pokemon
                            print_pause('Go, {}!\n'.format(pokemon.nickname))
                            break

                if choice == 'n':
                    break

            print_pause('Return, {}!'.format(trainer.current_pokemon.nickname))
            trainer.current_pokemon = new_pokemon
            print_pause('Go, {}!\n'.format(new_pokemon.nickname))

        else:
            while True:
                for slot, pokemon in enumerate(pokemon_choices, start=1):
                    print '{}: {} ({}), {}/{} hp'.format(slot, *pokemon.retrieve_pokemon_sheet_stats())
                pokemon_roster_number = raw_input('\nWho do you want to send out? [#]: ')

                if pokemon_roster_number.isdigit() and int(pokemon_roster_number)-1 in range(len(pokemon_choices)):
                    pokemon = pokemon_choices[int(pokemon_roster_number)-1]
                    confirm_choice = raw_input('Send out {}? [y/n]: '.format(pokemon.nickname))

                    if confirm_choice == 'y':
                        print_pause('\nReturn, {}!'.format(trainer.current_pokemon.nickname))
                        trainer.current_pokemon = pokemon
                        print_pause('Go, {}!\n'.format(pokemon.nickname))

                        return True

    def determine_turn(self, opponent, players_skill, opponents_skill):
        player_pokemon = self.player.current_pokemon
        opponent_pokemon = opponent.current_pokemon

        player_speed = player_pokemon.stats['speed']['total']
        opponent_speed = opponent_pokemon.stats['speed']['total']

        player_tuple = (player_pokemon, opponent_pokemon, players_skill)
        opponent_tuple = (opponent_pokemon, player_pokemon, opponents_skill)

        if players_skill.priority == opponents_skill.priority:
            if player_speed > opponent_speed:
                return player_tuple, opponent_tuple
            return opponent_tuple, player_tuple

        if players_skill.priority > opponents_skill.priority:
            return player_tuple, opponent_tuple
        return opponent_tuple, player_tuple

    def free_turn_opponent(self, opponent):
        opponent_action = opponent.computer_ai_turn()

        if isinstance(opponent_action, Ability):
            opponent.current_pokemon.attack(self.player.current_pokemon, opponent_action)
            self.pokemon_condition_changed(self.player)

        if isinstance(opponent_action, Item):
            opponent.item_use(opponent_action)

    def free_turn_player(self, opponent, players_skill):
        self.player.current_pokemon.attack(opponent.current_pokemon, players_skill)
        self.pokemon_condition_changed(opponent)


class Trainer:
    """ An object representing player/CPU capable of fighting """

    def __init__(self, title, name, computer=True):
        self.title = title
        self.name = name
        self.computer = computer

        self.roster = {x: '' for x in range(6)}
        self.lead_pokemon = None
        self.current_pokemon = None
        self.knocked_out = []

        self.inventory = {
            'Items': [],
            'Medicine': [],
            'Poke Balls': [],
            'TMs and HMs': [],
            'Berries': [],
            'Mail': [],
            'Battle Items': [],
            'Key Items': []
        }

        self.battling = False
        self.out_of_pokemon = False
        self.run_away_attempts = 1
        self.badges = 0
        self.money = 0

    def __repr__(self):
        return 'Trainer(title={}, name={}, computer={})'.format(self.title, self.name, self.computer)

    ###

    def inventory_has_items(self):
        inventory = []
        for item_category, item_list in self.inventory.iteritems():
            for item in item_list:
                inventory.append(item)
        return len(inventory) > 0

    def battle_inventory(self):
        keys = ['Medicine', 'Poke Balls', 'Battle Items']
        show = {key: value for key, value in self.inventory.iteritems() if key in keys}
        return show

    def item_receive(self, item):
        slot = item.pocket_slot
        self.inventory[slot].append(item)

    def item_use(self, item):
        if item.purpose == 'healing':
            if self.computer:
                pokemon = self.current_pokemon
                max_heal = pokemon.max_hp - pokemon.current_hp
                amount = int(''.join(x for x in item.prose if x.isdigit()))
                healed = amount if amount < max_heal else max_heal

                print_pause('{} used {} on {}, and healed for {}!\n'.format(
                    self.name, item.name, pokemon.nickname, healed))

                self.inventory[item.pocket_slot].remove(item)
                pokemon.current_hp += healed

            else:
                for slot, pokemon in self.roster.iteritems():
                    if pokemon:
                        print '{}: {} ({}), {}/{} hp'.format(slot+1, *pokemon.retrieve_pokemon_sheet_stats())

                choice = raw_input('\nWho do you want to use {} on? [#]: '.format(item.proper_name))
                if choice.isdigit() and self.roster.get(int(choice)-1, None):
                    pokemon = self.roster[int(choice)-1]

                    confirm_choice = raw_input('Use {} on {}? [y/n]: '.format(
                        item.proper_name, pokemon.nickname))

                    if confirm_choice == 'y':
                        if pokemon.current_hp == pokemon.max_hp:
                            print '{} already has full HP.\n'.format(pokemon.nickname)
                            return False

                        elif pokemon.current_hp == 0:
                            print "{} is out of HP.\n".format(pokemon.nickname)
                            return False

                        else:
                            max_heal = pokemon.max_hp - pokemon.current_hp
                            amount = int(''.join(x for x in item.prose if x.isdigit()))
                            healed = amount if amount < max_heal else max_heal

                            print_pause('Used {} on {}, and healed for {}!\n'.format(
                                item.name, pokemon.nickname, healed))

                            self.inventory[item.pocket_slot].remove(item)
                            pokemon.current_hp += healed
                            return True

    def item_delete(self, item):
        pass

    ###

    def roster_display(self):
        return {x: y.nickname for x, y in self.roster.iteritems() if y}

    def roster_retrieve_capable_pokemon(self):
        pokemon_choices = []
        for slot, pokemon in self.roster.iteritems():
            if pokemon and pokemon not in self.knocked_out:
                pokemon_choices.append(pokemon)
        return pokemon_choices

    def roster_add_pokemon(self, pokemon):
        open_slots = [x for x, y in self.roster.iteritems() if y == '']
        if open_slots:
            self.roster[open_slots[0]] = pokemon
            self.lead_pokemon = self.roster[0]
            pokemon.wild = False
        else:
            print 'No open slots left for {}.'.format(pokemon.nickname)

    def roster_remove_pokemon(self, pokemon):
        pass

    def roster_swap_position(self, pokemon_a, pokemon_b):
        # For swapping position on the roster, like lead to last, etc
        pass

    ###

    def computer_ai_turn(self):
        roll = random.randint(0, 100)
        pokemon = self.current_pokemon

        if roll > 10 or not self.inventory_has_items() or pokemon.current_hp == pokemon.max_hp:
            moves_to_use = []
            for slot, move in pokemon.skill_set.iteritems():
                if move and not move.damage_type == 'status' and not move.pp == 0:
                    moves_to_use.append(move)
            return random.choice(moves_to_use)

        elif roll <= 10:
            items_to_use = []
            for item_category, item_list in self.battle_inventory().iteritems():
                for item in item_list:
                    if item.purpose == 'healing':            # Temporary
                        items_to_use.append(item)
            return random.choice(items_to_use)


class Pokemon:
    """ An instance of a specific pokemon for battle or use """

    def __init__(self, pokemon_id, level=5, nickname=None):
        self.pokemon_id = pokemon_id
        self.level = level

        # Initialization of pokemon stats
        self.name, self.base_experience = self.gather_pokemon_base_data()
        self.pokemon_type = self.gather_pokemon_type()
        self.evolution = self.gather_pokemon_evolution()
        self.species = self.gather_pokemon_species()
        self.skill_list = self.gather_pokemon_skills()
        self.experience = self.gather_pokemon_experience()
        self.abilities = self.gather_pokemon_ability()
        self.stats = self.gather_pokemon_stats()
        self.nature_id = str(random.randint(1, 25))
        self.nature = self.gather_pokemon_nature()
        self.nickname = nickname if nickname else self.name.capitalize()

        # Priming to use pokemon as an object
        self.calculate_stat_changes()
        self.ev_total = 0
        self.skill_set = {0: None, 1: None, 2: None, 3: None}
        self.current_hp = self.stats['hp']['total']
        self.max_hp = self.stats['hp']['total']
        self.wild = False
        self.traded = False
        self.holding = ''
        self.affection = '0'

        self.current_experience = 0
        self.remaining_experience = self.retrieve_remaining_lvlup_experience()
        self.evolve_level = self.evolution['level'] if self.evolution else None
        self.initialize_skill_set()

        # Battle stats
        self.fainted = False
        self.accuracy_stage = 0
        self.evasion_stage = 0
        self.critical_stage = 0

    def __repr__(self):
        return 'Pokemon(pokemon_id="{}", level={}, nickname="{}")'.format(
            self.pokemon_id, self.level, self.nickname)

    def gather_pokemon_evolution(self):
        #evolution_triggers = {x['id']: x['identifier'] for x in csv_read('evolution_triggers.csv')}
        pokemon_evolution = {}
        for x in csv_read('pokemon_evolution.csv'):
            if x['id'] == self.pokemon_id:
                pokemon_evolution = {'level': x['minimum_level'], 'evolves into': x['evolved_species_id']}
            if x['id'] == str(int(self.pokemon_id) + 1):
                break
        return pokemon_evolution

    def gather_pokemon_experience(self):
        pokemon_experience = []
        for x in csv_read('experience.csv'):
            if x['growth_rate_id'] == self.species['growth rate']:
                pokemon_experience.append({'level': int(x['level']), 'experience': int(x['experience'])})
            if x['growth_rate_id'] == str(int(self.species['growth rate']) + 1):
                break
        return pokemon_experience

    def gather_pokemon_species(self):
        pokemon_species = {}
        for x in csv_read('pokemon_species.csv'):
            if x['id'] == self.pokemon_id:
                capture_rate = x['capture_rate']
                growth_rate = x['growth_rate_id']
                evolves_from = x['evolves_from_species_id']
                pokemon_species = {'growth rate': growth_rate, 'capture rate': capture_rate,
                                   'evolve from': evolves_from}
            if x['id'] == str(int(self.pokemon_id) + 1):
                break
        return pokemon_species

    def gather_pokemon_ability(self):
        abilities = {x['id']: x['identifier'] for x in csv_read('abilities.csv')}
        slots = {'1': 'primary', '2': 'secondary', '3': 'hidden'}
        pokemon_ability = {}

        for x in csv_read('pokemon_abilities.csv'):
            if x['pokemon_id'] == self.pokemon_id:
                pokemon_ability[slots[x['slot']]] = abilities[x['ability_id']]
            if x['pokemon_id'] == str(int(self.pokemon_id)+1):
                break
        return pokemon_ability

    def gather_pokemon_stats(self):
        stats = {x['id']: x['identifier'] for x in csv_read('stats.csv')}
        full_stats = {}

        for x in csv_read('pokemon_stats.csv'):
            if x['pokemon_id'] == self.pokemon_id:
                stat_name = stats[x['stat_id']]
                iv = random.randint(0, 31)
                full_stats[stat_name] = {'base': int(x['base_stat']), 'effort': int(x['effort']),
                                         'IV': iv, 'EV': 0}
            if x['pokemon_id'] == str(int(self.pokemon_id) + 1):
                break

        return full_stats

    def gather_pokemon_skills(self):
        skills = {'level-up': [], 'machine': []}
        pokemon_move_byte_space = {x['pokemon_id']: x['byte_location'] for x in csv_read('pokemon_moves_bytes.csv')}
        move_methods = {x['id']: x['identifier'] for x in csv_read('pokemon_move_methods.csv')}
        fields = csv.DictReader(open(os.path.join(os.getcwd(), 'pokemon data', 'pokemon_moves.csv'))).fieldnames

        with open(os.path.join(os.getcwd(), 'pokemon data', 'pokemon_moves.csv')) as f:
            f.seek(int(pokemon_move_byte_space[self.pokemon_id]))
            for x in f.read().split('\n'):
                line = dict(zip(fields, x.split(',')))
                if line['pokemon_id'] == str(int(self.pokemon_id) + 1):
                    break
                method = move_methods[line['pokemon_move_method_id']]
                if method in list(skills.keys()):
                    formatted = {'move': line['move_id'], 'level': int(line['level']),
                                 'order': line['order']}
                    if formatted not in skills[method]:
                        skills[method].append(formatted)
        return skills

    def gather_pokemon_type(self):
        pokemon_types = {x['type_id']: x['name'] for x in csv_read('type_names.csv') if x['local_language_id'] == '9'}
        slots = {'1': 'primary', '2': 'secondary', '3': 'hidden'}
        pokemon_type = {}

        for x in csv_read('pokemon_types.csv'):
            if x['pokemon_id'] == self.pokemon_id:
                pokemon_type[slots[x['slot']]] = {x['type_id']: pokemon_types[x['type_id']]}
            if x['pokemon_id'] == str(int(self.pokemon_id) + 1):
                break
        return pokemon_type

    def gather_pokemon_base_data(self):
        for pokemon in csv_read('pokemon.csv'):
            if self.pokemon_id in pokemon['id']:
                return pokemon['identifier'], int(pokemon['base_experience'])

    def gather_pokemon_nature(self):
        nature = {}

        for stat in csv_read('natures.csv'):
            if stat['id'] == self.nature_id:
                nature = stat
                break

        return nature

    ###

    def initialize_skill_set(self):
        possible_skills = []
        good_skills = []
        required_attack_skills = 2

        for skill in self.skill_list['level-up']:
            if skill['level'] <= self.level and skill['move'] not in possible_skills:
                possible_skills.append(skill['move'])

        for skill in possible_skills:
            ability = Ability(skill)

            if required_attack_skills > 0:
                if not ability.damage_type == 'status':
                    good_skills.append(skill)
                    possible_skills.remove(skill)
                    required_attack_skills -= 1

        random.shuffle(possible_skills)
        skills = good_skills + possible_skills

        for number, skill in enumerate(skills[0:4]):
            self.skill_set[number] = Ability(skill)

    def learn_skill(self, new_skill, silent=False):
        open_slots = [x for x, y in self.skill_set.iteritems() if y is None]

        if open_slots:
            slot = open_slots[0]
            self.skill_set[slot] = new_skill

            if not silent:
                print '{} has learned {}!\n'.format(self.nickname, new_skill.proper_name)

        else:
            while True:
                formatting = '{} is trying to learn {}. Forget a skill? [y/n]: '. \
                    format(self.nickname, new_skill.name)
                decision = raw_input(formatting)

                if decision == 'y':
                    skills = ', '.join([skill.name for skill in self.skill_set.itervalues() if skill])
                    skill_choice = raw_input('Which skill? [{}]: '.format(skills))

                    if any(skill_choice.lower() == x.name for x in self.skill_set.itervalues()):
                        choice = raw_input('Are you sure? [y/n]: ')
                        if choice == 'y':
                            index = [x.name for x in self.skill_set.itervalues()].index(skill_choice)
                            self.skill_set[index] = new_skill
                            print '{} has forgotten {}, and learned {}!\n'.\
                                format(self.nickname, skill_choice, new_skill.proper_name)
                            break

                elif decision == 'n':
                    choice = raw_input('Are you sure? [y/n]: ')
                    if choice == 'y':
                        print '{} did not learn {}.\n'.format(self.nickname, new_skill.name)
                        break

    def attack(self, opponent, skill):
        skill.pp -= 1

        print_pause('{} uses {}!'.format(self.nickname, skill.proper_name))

        if not skill.will_hit(self, opponent):
            print_pause('Attack missed.\n')
            return True

        damage = self.calculate_skill_damage(opponent, skill)
        opponent.receive_damage(damage)

        print_pause('{} has {} hp remaining.\n'.format(opponent.nickname, opponent.current_hp))

    def level_up(self):
        print '{0} has leveled up!\n{0} is now level {1}.\n'.format(self.nickname, self.level+1)

        self.calculate_stat_changes()
        self.max_hp = self.stats['hp']['total']
        self.level += 1

        for skill in self.retrieve_pokemon_skills_at_level(self.level):
            self.learn_skill(skill)

    ###

    def retrieve_types__string(self):
        l = []
        for pokemon_type in self.pokemon_type:
            for type_id, name in self.pokemon_type[pokemon_type].iteritems():
                l.append(name)
        return '/'.join(l)

    def retrieve_types__list(self):
        l = []
        for slot, type_info in self.pokemon_type.iteritems():
            for type_id, type_name in type_info.iteritems():
                l.append(type_id)
        return l

    def retrieve_nature_name(self):
        return self.nature['identifier']

    def retrieve_pokemon_skills_at_level(self, level):
        known_skills = []
        for skill in self.skill_set.itervalues():
            if skill:
                known_skills.append(str(skill.move_id))

        skills = []
        for skill in self.skill_list['level-up']:
            if skill['level'] == level and not str(skill['move']) in known_skills:
                skills.append(Ability(skill['move']))

        return skills

    def retrieve_effort_values(self):
        receivable = []

        for stat in self.stats:
            if self.stats[stat]['effort'] != '0':
                receivable.append({stat: self.stats[stat]['effort']})

        return receivable

    def retrieve_remaining_lvlup_experience(self):
        for level in self.experience:
            if level['level'] == self.level:
                return int(level['experience']) - int(self.current_experience)

    def retrieve_pokemon_sheet_stats(self):
        return self.nickname, self.retrieve_types__string(), self.current_hp, self.max_hp

    ###

    def receive_effort_values(self, effort_values):
        for ev in effort_values:
            for name, value in ev.iteritems():
                if self.ev_total < 510:
                    if (self.stats[name]['EV'] + value) >= 255:
                        value = 255 - self.stats[name]['EV']
                    self.stats[name]['EV'] += value
                    self.ev_total += value

    def receive_experience(self, experience):
        remaining = self.retrieve_remaining_lvlup_experience() - self.current_experience

        if experience > remaining:
            difference = experience - remaining
            self.current_experience = difference
            self.level_up()
            self.remaining_experience = self.retrieve_remaining_lvlup_experience()

        else:
            self.current_experience += experience

    def receive_damage(self, damage):
        self.current_hp -= damage

        if self.current_hp <= 0:
            self.current_hp = 0
            self.fainted = True

    ###

    def calculate_stat_changes(self):
        stats = {x['id']: x['identifier'] for x in csv_read('stats.csv')}
        increased_stat_by_nature = stats[self.nature['increased_stat_id']]
        decreased_stat_by_nature = stats[self.nature['decreased_stat_id']]

        for stat in self.stats:
            base = self.stats[stat]['base']
            iv = self.stats[stat]['IV']
            ev = self.stats[stat]['EV']
            nature = 1.10 if increased_stat_by_nature == stat else \
                0.90 if decreased_stat_by_nature == stat else 1

            if stat == 'hp':
                self.stats[stat]['total'] = ((((iv + (2 * base)) + (ev / 4) + 100) * int(self.level)) / 100)
                self.stats[stat]['total'] += 10
            else:
                self.stats[stat]['total'] = (((((iv + (2 * base)) + (ev / 4)) * int(self.level)) / 100) + 5)
                self.stats[stat]['total'] *= nature

    def calculate_critical_strike(self):
        stages = {0: 1.0 / 16, 1: 1.0 / 8, 2: 1.0 / 4, 3: 1.0 / 3, 4: 1.0 / 2}
        chance = stages[self.critical_stage] * 100
        roll = random.uniform(0.00, 100.00)
        return chance >= roll

    def calculate_skill_damage(self, opponent, attack):
        attack_type = {'physical': 'attack', 'special': 'special-attack'}
        defend_type = {'attack': 'defense', 'special-attack': 'special-defense'}

        a_type = attack_type[attack.damage_type]
        d_type = defend_type[a_type]

        attack_dmg = float(self.stats[a_type]['total'])
        defend_amt = opponent.stats[d_type]['total']

        stab = 1.5 if attack.move_type in self.retrieve_types__string() else 1.0
        attack_mod = attack.retrieve_damage_modifier(*opponent.retrieve_types__list())
        critical = 2.0 if self.calculate_critical_strike() else 1.0
        other = 1  # TODO: add advantages for held items, abilities, and field advantages
        modifier = stab * attack_mod * critical * other * random.uniform(0.85, 1.00)

        damage = ((2.0 * int(self.level) + 10) / 250) * (attack_dmg / defend_amt) * attack.power + 2.0
        damage *= modifier

        if critical > 1:
            print 'Critical strike! '
        if attack_mod > 1:
            print "It's super effective! "
        if 0 < attack_mod < 1:
            print 'Not very effective ...'
        if attack_mod == 0:
            print "It doesn't affect the pokemon..."

        return int(damage)

    def calculate_experience(self, opponent):
        pokemon_owned_by_trainer = 1 if opponent.wild else 1.5
        base_experience = opponent.base_experience
        lucky_egg = 1.5 if self.holding == 'Lucky Egg' else 1
        affection = 1.2 if self.affection >= 2 else 1
        losers_level = opponent.level
        winners_level = self.level
        exp_modifier = 1  # TODO figure out exp mod stuff
        pokemon_used = 1  # trainer.pokemon_used - trainer.fainted  # TODO figure exp share stuff
        traded_modifier = 1 if self.traded else 1.5
        not_evolved = 1.2 if self.level >= self.evolve_level else 1

        experience = (pokemon_owned_by_trainer * base_experience * losers_level) / (5 * pokemon_used)
        experience *= ((2 * losers_level + 10) ** 2.5) / ((losers_level + winners_level + 10) ** 2.5)
        experience += 1
        experience *= traded_modifier * lucky_egg * exp_modifier
        experience *= affection * not_evolved

        return int(experience)


class Ability:
    """ An instance of an ability to be added to a pokemon's skill set """

    def __init__(self, move_id):
        self.move_id = move_id
        self.information = self.retrieve_move_info()

        self.name = self.information['name']
        self.proper_name = self.name.capitalize()
        self.type_id = self.information['type_id']
        self.description = self.information['description']
        self.power = self.information['power']
        self.pp = self.information['pp']
        self.pp_max = self.information['pp']

        self.target = self.information['target']
        self.damage_type = self.information['damage_type']
        self.effect_chance = self.information['effect_chance']
        self.priority = self.information['priority']
        self.move_type = self.information['move_type']
        self.accuracy = self.information['accuracy']

    def __repr__(self):
        return 'Ability(move_id={})'.format(self.move_id)

    def retrieve_damage_modifier(self, target_type_id, secondary_type_id=None):
        """ Retrieves the damage modifier against pokemon's type """

        efficacy = csv_read('type_efficacy.csv')
        damage_modifier = 1.00

        for match_up in efficacy:
            if match_up['damage_type_id'] == self.type_id and match_up['target_type_id'] == target_type_id:
                damage_modifier *= (int(match_up['damage_factor']) / 100.0)

            if secondary_type_id is not None:
                if match_up['damage_type_id'] == self.type_id and match_up['target_type_id'] == secondary_type_id:
                    damage_modifier *= (int(match_up['damage_factor']) / 100.0)

        return damage_modifier

    def will_hit(self, pokemon, opponent):
        """ Retrieves accuracy stages, rolls a dice, and determines hit or miss """

        accuracy_stages = {-6: 3.0/9, -5: 3.0/8, -4: 3.0/7,
                           -3: 3.0/6, -2: 3.0/5, -1: 3.0/4,
                           0: 1.0, 1: 4.0/3, 2: 5.0/3,
                           3: 2.0, 4: 7.0/3, 5: 8.0/3,
                           6: 3.0}

        skill_accuracy = self.accuracy / 100.0
        pokemon_accuracy = accuracy_stages[pokemon.accuracy_stage]
        opponent_accuracy = accuracy_stages[opponent.accuracy_stage]

        chance = skill_accuracy * (pokemon_accuracy / opponent_accuracy)
        roll = random.uniform(0.00, 100.00)

        if roll < chance * 100 or chance > 1:
            return True
        return False

    def retrieve_move_info(self):
        """ Gathers all relevant info for moves and keeps it instantiated for use in battle """

        damage_classes = {x['id']: x['identifier'] for x in csv_read('move_damage_classes.csv')}
        target_classes = {x['id']: x['identifier'] for x in csv_read('move_targets.csv')}

        move = {}
        for move in csv_read('moves.csv'):
            if move['id'] == self.move_id:
                move = move
                break

        move_type = ''
        for x in csv_read('types.csv'):
            if x['id'] == move['type_id']:
                move_type = x['identifier']
                break

        description = ''
        for x in csv_read('move_effect_prose.csv'):
            if x['move_effect_id'] == move['effect_id']:
                description = x['short_effect']
                break

        target = target_classes[move['target_id']]
        damage_type = damage_classes[move['damage_class_id']]

        return {'name': move['identifier'],
                'description': description,
                'damage_type': damage_type,
                'move_type': move_type.capitalize(),
                'accuracy': int(move['accuracy'] if move['accuracy'] else 100),
                'priority': int(move['priority']),
                'pp': int(move['pp']),
                'power': int(move['power'] if move['power'] else 0),
                'effect_chance': move['effect_chance'],
                'target': target,
                'type_id': move['type_id'],
                'move_id': int(self.move_id)}


class Item:
    """ An instance of an item to be used in a players inventory"""

    def __init__(self, item_id):
        self.item_id = item_id

        self.base = self.gather_base_item_data()
        self.name = self.base['identifier']
        self.proper_name = self.name.capitalize()
        self.fling_power = self.base['fling_power']
        self.flint_effect_id = self.base['fling_effect_id']
        self.cost = self.base['cost']

        self.purpose, self.pocket_id = self.gather_item_category()
        self.prose = self.gather_item_prose()
        self.flags = self.gather_item_flags()
        self.pocket_slot = self.gather_pocket_slot()
        self.gather_item_prose()

    def __repr__(self):
        return 'Item(item_id={})'.format(self.item_id)

    def gather_base_item_data(self):
        for item in csv_read('items.csv'):
            if item['id'] == self.item_id:
                return item

    def gather_item_category(self):
        for cat in csv_read('item_categories.csv'):
            if cat['id'] == self.base['category_id']:
                return cat['identifier'], cat['pocket_id']

    def gather_item_flags(self):
        flags = {flag['id']: flag['identifier'] for flag in csv_read('item_flags.csv')}

        usability = []
        for item in csv_read('item_flag_map.csv'):
            if item['item_id'] == self.item_id:
                usability.append(flags[item['item_flag_id']])
            if item['item_id'] == str(int(self.item_id)+1):
                break
        return usability

    def gather_pocket_slot(self):
        for x in csv_read('item_pocket_names.csv'):
            if x['item_pocket_id'] == self.pocket_id:
                return x['name']

    def gather_item_prose(self):
        ## Item long description is here
        for item in csv_read('item_prose.csv'):
            if item['item_id'] == self.item_id:
                return item['short_effect']


if __name__ == '__main__':
    Main()