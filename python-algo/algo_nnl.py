import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    
        

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defense
        if game_state.turn_number < 3:
            self.build_defences(game_state)
        if game_state.turn_number > 3:
            self.build_reactive_defense(game_state)

        early_spawn_location_options = [[5, 8], [23, 9]]
        
        if game_state.turn_number < 8:
            the_spawn_location_options = early_spawn_location_options
        else:
			the_spawn_location_options = early_spawn_location_options
            #Every 4th turn, 
            if game_state.turn_number % 4 == 1:

                # Now let's analyze the enemy base to see where their defenses are concentrated.
                # If they have many units in the front we can build a line for our EMPs to attack them at long range.
                go_all_out = game_state.get_resource(BITS)/game_state.type_cost(EMP)[BITS] >= 4:
                if go_all_out:
                    if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                        if game_state.turn_number > 8:
                            # pick a side with the least amount of ENCRYPTORS and DESTRUCTORS:
                            if self.pick_spawn_point_side(game_state, unit_type=None, valid_x=None, valid_y=[14, 27]) == 0:
                                #spawn left side
                                game_state.attempt_spawn(EMP, the_spawn_location_options[1], 10)
                            else:
                                #spawn right side
                                game_state.attempt_spawn(EMP, the_spawn_location_options[2], 10)
                    else:
                        # They don't have many units in the front so lets figure out their least defended area and send Pings there.     
                        # pick a side with the least amount of ENCRYPTORS and DESTRUCTORS:
                        if self.pick_spawn_point_side(game_state, unit_type=None, valid_x=None, valid_y=[14, 27]) == 0:
                            #spawn left side
                            # Sending more at once is better since attacks can only hit a single ping at a time
                            game_state.attempt_spawn(PING, the_spawn_location_options[1], 4)
                        else:
                            #spawn right side
                            # Sending more at once is better since attacks can only hit a single ping at a time
                            game_state.attempt_spawn(PING, the_spawn_location_options[2], 4)
                # Lastly, if we have spare cores, let's build some Encryptors to boost our Pings' health.
            #encryptor_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
            #game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)

    def pick_spawn_point_side(self,game_state,unit_type=None, valid_x = None, valid_y = None):
        """
        Checking enemy side and atributing points to each defensive unit for starting strat.

        FILTERs do not count (EMPs will rek them)
        ENCRYPTORS=2
        DESTRUCTORS=3
        
        Splitting field into two: every point with x=[0:13] is in left_side, every point with x=[14:27] is in right_side 
        
        Default: Spawn on Left-side = 0
        """
        units_left_side = 0
        units_right_side = 0
        
        result=0

        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        if location[0] in range(0,13):
                            if unit.unit_type == ENCRYPTOR:
                                left_side += 2
                            if unit.unit_type == DESTRUCTOR:
                                left_side += 3   
                        else:
                            if unit.unit_type == ENCRYPTOR:
                                right_side += 2
                            if unit.unit_type == DESTRUCTOR:
                                right_side += 3 

        if units_right_side <= units_left_side:
            result = 1
        return result
     

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
                # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
                        # More community tools available at: https://terminal.c1games.com/rules#Download

                                # Place destructors that attack enemy units
		destructor_locations = [[4, 12], [13, 12], [23, 12], [5, 11], [22, 11]]
		destructor_left_locations = [[4, 12], [5, 11]]
		destructor_right_locations = [[23, 12], [22, 11]]
		game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
		# Place filters in front of destructors to soak up damage for them
		filter_locations = [[0, 13], [2, 13], [3, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [14,13],[15, 13], [16, 13], [17, 13], [18, 13], [19, 13], [20, 13],[21, 13], [24, 13], [25, 13], [27, 13], [1, 13], [12, 13], [13, 13], [26, 13]]
		game_state.attempt_spawn(FILTER, filter_locations)

        # Place destructors that attack enemy units
        #self.destructor_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        #self.destructor_left_locations = [[4, 12], [5, 11]]
        #self.destructor_right_locations = [[23, 12], [22, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        #game_state.attempt_spawn(DESTRUCTOR, self.destructor_locations)

        # Place filters in front of destructors to soak up damage for them
        #filter_locations = [[8, 12], [19, 12]]
        #game_state.attempt_spawn(FILTER, filter_locations)
        # upgrade filters so they soak more damage
        #game_state.attempt_upgrade(filter_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        left = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6], [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0]]
        right = [[27, 13], [26, 12], [25, 11], [24, 10], [23, 9], [22, 8], [21, 7], [20, 6], [19, 5], [18, 4], [17, 3], [16, 2], [15, 1], [14, 0]]

        for location in self.scored_on_locations:
            # Build destructor one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]]
            if build_location in left:
                #coord = random.choices(self.destructor_left_locations,k=1)
                game_state.attempt_upgrade(self.destructor_left_locations)
                #print(coord)
            if build_location in right:
#                coord = random.choices(self.destructor_right_locations,k=1)
                #print(coord)
                game_state.attempt_upgrade(self.destructor_right_locations)
            else:
                self.encryptor_logic(game_state)
        

    def encryptor_logic(self, game_state):
        '''
        This function will spawn initial encryptors one side at a time. 
        This function will then be replaced by the adaptable encryptor
        function around mid game
        '''
        encryptor_locations_left = [[4,9],[5,10],[4,10],[4,10]] 
        encryptor_locations_right = [[24,10],[23,10],[24,11],[24,11]]
        en_loc_tempy =  encryptor_locations_left + encryptor_locations_right

        coordinates = random.choices(en_loc_tempy, k=6)
        game_state.attempt_spawn(ENCRYPTOR,coordinates)


    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own firewalls 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining bits to spend lets send out scramblers randomly.
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            """
            We don't have to remove the location since multiple information 
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False

            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
