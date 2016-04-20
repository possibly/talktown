import random
import heapq
import datetime
from corpora import Names
import event
from name import Name
from personality import Personality
from mind import Mind
import occupation
from face import Face
from routine import Routine
from whereabouts import Whereabouts
from relationship import Acquaintance
from evidence import Reflection, Observation, Lie, Statement
from belief import *
import face


class Person(object):
    """A person living in a city of a gameplay instance."""

    def __init__(self, game, birth):
        """Initialize a Person object."""
        # Set location and gameplay instance
        self.game = game
        self.id = self.game.current_person_id
        self.game.current_person_id += 1
        self.type = "person"
        self.birth = birth
        if birth:
            self.city = self.birth.city
            if self.city:
                self.city.residents.add(self)
            # Set parents
            self.biological_mother = birth.biological_mother
            self.mother = birth.mother
            self.biological_father = birth.biological_father
            self.father = birth.father
            self.parents = {self.mother, self.father}
            # Set date of birth
            self.birth_year = birth.year
            self.birthday = (birth.month, birth.day)  # This gets added to Game.birthdays by Birth.__init__(0
            # Set attributes pertaining to age
            self.age = 0
            self.adult = False
            self.ready_to_work = False
        else:  # PersonExNihilo
            self.city = None
            self.biological_mother = None
            self.mother = None
            self.biological_father = None
            self.father = None
            self.parents = set()
            self.birth_year = None  # Gets set by PersonExNihilo.__init__()
            self.birthday = (None, None)  # Gets set by PersonExNihilo.get_random_day_of_year()
            # Set attributes pertaining to age
            self.age = None  # Will get initialized by PersonExNihilo.__init__()
            self.adult = True if self.age >= 18 else False
            self.ready_to_work = (
                True if self.age >= self.game.config.age_people_start_working(year=self.game.year) else False
            )
        # Set sex
        self.male, self.female = (True, False) if random.random() < 0.5 else (False, True)
        self.tag = ''  # Allows players to tag characters with arbitrary strings
        # Set misc attributes
        self.alive = True
        self.death_year = None
        self.home = None  # Must come before setting routine
        # Set biological characteristics
        self.infertile = self._init_fertility(male=self.male, config=self.game.config)
        self.attracted_to_men, self.attracted_to_women = (
            self._init_sexuality()
        )
        # Set face
        self.face = Face(person=self)
        # Set personality
        self.personality = Personality(person=self)
        # Set mental attributes (just memory currently)
        self.mind = Mind(person=self)
        # Set daily routine
        self.routine = Routine(person=self)
        # Prepare Whereabouts object, which tracks a person's whereabouts at every
        # timestep of their life
        self.whereabouts = Whereabouts(person=self)
        # Prepare name attributes that get set by event.Birth._name_baby() (or PersonExNihilo._init_name())
        self.first_name = None
        self.middle_name = None
        self.last_name = None
        self.suffix = None
        self.maiden_name = None
        self.named_for = (None, None)  # From whom first and middle name originate, respectively
        # Prepare familial attributes that get populated by self.init_familial_attributes()
        self.ancestors = set()  # Biological only
        self.descendants = set()  # Biological only
        self.immediate_family = set()
        self.extended_family = set()
        self.greatgrandparents = set()
        self.grandparents = set()
        self.aunts = set()
        self.uncles = set()
        self.siblings = set()
        self.full_siblings = set()
        self.half_siblings = set()
        self.brothers = set()
        self.full_brothers = set()
        self.half_brothers = set()
        self.sisters = set()
        self.full_sisters = set()
        self.half_sisters = set()
        self.cousins = set()
        self.kids = set()
        self.sons = set()
        self.daughters = set()
        self.nephews = set()
        self.nieces = set()
        self.grandchildren = set()
        self.grandsons = set()
        self.granddaughters = set()
        self.greatgrandchildren = set()
        self.greatgrandsons = set()
        self.greatgranddaughters = set()
        self.bio_parents = set()
        self.bio_grandparents = set()
        self.bio_siblings = set()
        self.bio_full_siblings = set()
        self.bio_half_siblings = set()
        self.bio_brothers = set()
        self.bio_full_brothers = set()
        self.bio_half_brothers = set()
        self.bio_sisters = set()
        self.bio_full_sisters = set()
        self.bio_half_sisters = set()
        self.bio_immediate_family = set()
        self.bio_greatgrandparents = set()
        self.bio_uncles = set()
        self.bio_aunts = set()
        self.bio_cousins = set()
        self.bio_nephews = set()
        self.bio_nieces = set()
        self.bio_ancestors = set()
        self.bio_extended_family = set()
        # Set familial attributes; update those of family members
        self._init_familial_attributes()
        self._init_update_familial_attributes_of_family_members()
        # Prepare attributes representing this person's romantic relationships
        self.spouse = None
        self.widowed = False
        self.relationships = {}
        self.sexual_partners = set()
        # Prepare attributes representing this person's social relationships
        self.acquaintances = set()
        self.friends = set()
        self.enemies = set()
        self.neighbors = set()
        self.former_neighbors = set()
        self.coworkers = set()
        self.former_coworkers = set()
        self.best_friend = None
        self.worst_enemy = None
        self.love_interest = None
        self.significant_other = None
        self.charge_of_best_friend = 0.0  # These get used to track changes to a person's major relationships
        self.charge_of_worst_enemy = 0.0
        self.spark_of_love_interest = 0.0
        self.talked_to_this_year = set()
        self.befriended_this_year = set()
        self.salience_of_other_people = {}  # Maps potentially every other person to their salience to this person
        self._init_salience_values()
        # Prepare attributes pertaining to pregnancy
        self.pregnant = False
        self.impregnated_by = None
        self.conception_year = None  # Year of conception
        self.due_date = None  # Actual ordinal date 270 days from conception (currently)
        # Prepare attributes representing events in this person's life
        self.birth = birth
        self.adoption = None
        self.marriage = None
        self.marriages = []
        self.divorces = []
        self.adoptions = []
        self.moves = []  # From one home to another
        self.lay_offs = []  # Being laid off by a company that goes out of business
        self.name_changes = []
        self.building_commissions = set()  # Constructions of houses or buildings that they commissioned
        self.home_purchases = []
        self.retirement = None
        self.departure = None  # Leaving the city, i.e., leaving the simulation
        self.death = None
        # Set and prepare attributes pertaining to business affairs
        self.money = self._init_money()
        self.occupation = None
        self.occupations = []
        self.former_contractors = set()
        self.retired = False
        # Prepare attributes pertaining to education
        self.college_graduate = False
        # Prepare attributes pertaining to dynamic emotional considerations
        self.grieving = False  # After spouse dies
        # Prepare attribute pertaining to exact location for the current timestep; this
        # will always be modified by self.go_to()
        self.location = None
        # Prepare attributes pertaining to this person's knowledge
        self.all_belief_facets = set()  # Used to make batch calls to Facet.decay_strength()
        # Miscellaneous attributes pertaining to artifacts this person is wearing
        self.wedding_ring_on_finger = None
        # Currently, whether a character is the player is only considered by Conversation
        # objects (when deciding whether to elicit a dialogue move from the player)
        self.player = False

    def __str__(self):
        """Return string representation."""
        if self.present:
            return "{}, {} years old".format(self.name, self.age)
        elif self.departure:
            return "{}, left city in {}".format(self.name, self.departure.year)
        else:
            return "{}, {}-{}".format(self.name, self.birth_year, self.death_year)

    @staticmethod
    def _init_fertility(male, config):
        """Determine whether this person will be able to reproduce."""
        x = random.random()
        if male and x < config.male_infertility_rate:
            infertile = True
        elif not male and x < config.female_infertility_rate:
            infertile = True
        else:
            infertile = False
        return infertile

    def _init_sexuality(self):
        """Determine this person's sexuality."""
        config = self.game.config
        x = random.random()
        if x < config.homosexuality_incidence:
            # Homosexual
            if self.male:
                attracted_to_men = True
                attracted_to_women = False
            else:
                attracted_to_men = False
                attracted_to_women = True
        elif x < config.homosexuality_incidence+config.bisexuality_incidence:
            # Bisexual
            attracted_to_men = True
            attracted_to_women = True
        elif x < config.homosexuality_incidence+config.bisexuality_incidence+config.asexuality_incidence:
            # Asexual
            attracted_to_men = True
            attracted_to_women = True
        else:
            # Heterosexual
            if self.male:
                attracted_to_men = False
                attracted_to_women = True
            else:
                attracted_to_men = True
                attracted_to_women = False
        return attracted_to_men, attracted_to_women

    def _init_familial_attributes(self):
        """Populate lists representing this person's family members."""
        self._init_immediate_family()
        self._init_biological_immediate_family()
        self._init_extended_family()
        self._init_biological_extended_family()

    def _init_immediate_family(self):
        """Populate lists representing this person's (legal) immediate family."""
        self.grandparents = self.father.parents | self.mother.parents
        self.siblings = self.father.kids | self.mother.kids
        self.full_siblings = self.father.kids & self.mother.kids
        self.half_siblings = self.father.kids ^ self.mother.kids
        self.brothers = self.father.sons | self.mother.sons
        self.full_brothers = self.father.sons & self.mother.sons
        self.half_brothers = self.father.sons ^ self.mother.sons
        self.sisters = self.father.daughters | self.mother.daughters
        self.full_sisters = self.father.daughters & self.mother.daughters
        self.half_sisters = self.father.daughters ^ self.mother.daughters
        self.immediate_family = self.grandparents | self.parents | self.siblings

    def _init_biological_immediate_family(self):
        """Populate lists representing this person's immediate."""
        self.bio_parents = {self.biological_mother, self.biological_father}
        self.bio_grandparents = self.biological_father.parents | self.biological_mother.parents
        self.bio_siblings = self.biological_father.kids | self.biological_mother.kids
        self.bio_full_siblings = self.biological_father.kids & self.biological_mother.kids
        self.bio_half_siblings = self.biological_father.kids ^ self.biological_mother.kids
        self.bio_brothers = self.biological_father.sons | self.biological_mother.sons
        self.bio_full_brothers = self.biological_father.sons & self.biological_mother.sons
        self.bio_half_brothers = self.biological_father.sons ^ self.biological_mother.sons
        self.bio_sisters = self.biological_father.daughters | self.biological_mother.daughters
        self.bio_full_sisters = self.biological_father.daughters & self.biological_mother.daughters
        self.bio_half_sisters = self.biological_father.daughters ^ self.biological_mother.daughters
        self.bio_immediate_family = self.bio_grandparents | self.bio_parents | self.bio_siblings

    def _init_extended_family(self):
        """Populate lists representing this person's (legal) extended family."""
        self.greatgrandparents = self.father.grandparents | self.mother.grandparents
        self.uncles = self.father.brothers | self.mother.brothers
        self.aunts = self.father.sisters | self.mother.sisters
        self.cousins = self.father.nieces | self.father.nephews | self.mother.nieces | self.mother.nephews
        self.nephews = self.father.grandsons | self.mother.grandsons
        self.nieces = self.father.granddaughters | self.mother.granddaughters
        self.ancestors = self.father.ancestors | self.mother.ancestors | self.parents
        self.extended_family = (
            self.greatgrandparents | self.immediate_family | self.uncles | self.aunts |
            self.cousins | self.nieces | self.nephews
        )

    def _init_biological_extended_family(self):
        """Populate lists representing this person's (legal) extended family."""
        self.bio_greatgrandparents = self.father.grandparents | self.mother.grandparents
        self.bio_uncles = self.father.brothers | self.mother.brothers
        self.bio_aunts = self.father.sisters | self.mother.sisters
        self.bio_cousins = self.father.nieces | self.father.nephews | self.mother.nieces | self.mother.nephews
        self.bio_nephews = self.father.grandsons | self.mother.grandsons
        self.bio_nieces = self.father.granddaughters | self.mother.granddaughters
        self.bio_ancestors = self.father.ancestors | self.mother.ancestors | self.parents
        self.bio_extended_family = (
            self.bio_greatgrandparents | self.bio_immediate_family | self.bio_uncles | self.bio_aunts |
            self.bio_cousins | self.bio_nieces | self.bio_nephews
        )

    def _init_update_familial_attributes_of_family_members(self):
        """Update familial attributes of myself and family members."""
        config = self.game.config
        for member in self.immediate_family:
            member.immediate_family.add(self)
            member.update_salience_of(
                entity=self, change=config.salience_increment_from_relationship_change["immediate family"]
            )
        for member in self.extended_family:
            member.extended_family.add(self)
            member.update_salience_of(
                entity=self, change=config.salience_increment_from_relationship_change["extended family"]
            )
        # Update for gender-specific familial attributes
        if self.male:
            for g in self.greatgrandparents:
                g.greatgrandsons.add(self)
            for g in self.grandparents:
                g.grandsons.add(self)
            for p in self.parents:
                p.sons.add(self)
            for u in self.uncles:
                u.nephews.add(self)
            for a in self.aunts:
                a.nephews.add(self)
            for b in self.full_brothers:
                b.full_brothers.add(self)
                b.brothers.add(self)
            for s in self.full_sisters:
                s.full_brothers.add(self)
                s.brothers.add(self)
            for b in self.half_brothers:
                b.half_brothers.add(self)
                b.brothers.add(self)
            for s in self.half_sisters:
                s.half_brothers.add(self)
                s.brothers.add(self)
        elif self.female:
            for g in self.greatgrandparents:
                g.greatgranddaughters.add(self)
            for g in self.grandparents:
                g.granddaughters.add(self)
            for p in self.parents:
                p.daughters.add(self)
            for u in self.uncles:
                u.nieces.add(self)
            for a in self.aunts:
                a.nieces.add(self)
            for b in self.full_brothers:
                b.full_sisters.add(self)
                b.sisters.add(self)
            for s in self.full_sisters:
                s.full_sisters.add(self)
                s.sisters.add(self)
            for b in self.half_brothers:
                b.half_sisters.add(self)
                b.sisters.add(self)
            for s in self.half_sisters:
                s.half_sisters.add(self)
                s.sisters.add(self)
        # Update for non-gender-specific familial attributes
        for a in self.ancestors:
            a.descendants.add(self)
        for g in self.greatgrandparents:
            g.greatgrandchildren.add(self)
        for g in self.grandparents:
            g.grandchildren.add(self)
        for p in self.parents:
            p.kids.add(self)
        for fs in self.full_siblings:
            fs.siblings.add(self)
            fs.full_siblings.add(self)
        for hs in self.half_siblings:
            hs.siblings.add(self)
            hs.half_siblings.add(self)
        for c in self.cousins:
            c.cousins.add(self)

    def _init_salience_values(self):
        """Determine an initial salience value for every other person associated with this newborn."""
        config = self.game.config
        for person in self.ancestors:
            self.update_salience_of(
                entity=person, change=config.salience_increment_from_relationship_change["ancestor"]
            )
        for person in self.extended_family:
            self.update_salience_of(
                entity=person, change=config.salience_increment_from_relationship_change["extended family"]
            )
        for person in self.immediate_family:
            self.update_salience_of(
                entity=person, change=config.salience_increment_from_relationship_change["immediate family"]
            )
        self.update_salience_of(
            entity=self, change=config.salience_increment_from_relationship_change["self"]
        )

    def _init_money(self):
        """Determine how much money this person has to start with."""
        return 0

    @property
    def subject_pronoun(self):
        """Return the appropriately gendered third-person singular subject pronoun."""
        return 'he' if self.male else 'she'

    @property
    def object_pronoun(self):
        """Return the appropriately gendered third-person singular object pronoun."""
        return 'him' if self.male else 'her'

    @property
    def possessive_pronoun(self):
        """Return appropriately gendered possessive subject_pronoun."""
        return 'his' if self.male else 'her'

    @property
    def reflexive_pronoun(self):
        """Return appropriately gendered reflexive subject_pronoun."""
        return 'himself' if self.male else 'herself'

    @property
    def honorific(self):
        """Return the correct honorific (e.g., 'Mr.') for this person."""
        if self.male:
            return 'Mr.'
        elif self.female:
            if self.spouse:
                return 'Mrs.'
            else:
                return 'Ms.'

    @property
    def full_name(self):
        """Return a person's full name."""
        if self.suffix:
            full_name = "{0} {1} {2} {3}".format(
                self.first_name, self.middle_name, self.last_name, self.suffix
            )
        else:
            full_name = "{0} {1} {2}".format(
                self.first_name, self.middle_name, self.last_name
            )
        return full_name

    @property
    def full_name_without_suffix(self):
        """Return a person's full name sans suffix.

        This is used to determine whether a child has the same full name as their parent,
        which would necessitate them getting a suffix of their own to disambiguate.
        """
        full_name = "{0} {1} {2}".format(
            self.first_name, self.middle_name, self.last_name
        )
        return full_name

    @property
    def name(self):
        """Return a person's name."""
        if self.suffix:
            name = "{0} {1} {2}".format(self.first_name, self.last_name, self.suffix)
        else:
            name = "{0} {1}".format(self.first_name, self.last_name)
        return name

    @property
    def nametag(self):
        """Return a person's name, appended with their tag, if any."""
        if self.tag:
            nametag = "{0} {1}".format(self.name, self.tag)
        else:
            nametag = self.name
        return nametag

    @property
    def dead(self):
        """Return whether this person is dead."""
        if not self.alive:
            return True
        else:
            return False

    @property
    def queer(self):
        """Return whether this person is not heterosexual."""
        if self.male and self.attracted_to_men:
            queer = True
        elif self.female and self.attracted_to_women:
            queer = True
        elif not self.attracted_to_men and not self.attracted_to_women:
            queer = True
        else:
            queer = False
        return queer

    @property
    def present(self):
        """Return whether the person is alive and in the city."""
        if self.alive and not self.departure:
            return True
        else:
            return False

    @property
    def next_of_kin(self):
        """Return next of kin.

        A person's next of kin will make decisions about their estate and
        so forth upon the person's eeath.
        """
        if self.spouse and self.spouse.present:
            next_of_kin = self.spouse
        elif self.mother and self.mother.present:
            next_of_kin = self.mother
        elif self.father and self.father.present:
            next_of_kin = self.father
        elif any(k for k in self.kids if k.adult and k.present):
            next_of_kin = next(k for k in self.kids if k.adult and k.present)
        elif any(f for f in self.siblings if f.adult and f.present):
            next_of_kin = next(f for f in self.siblings if f.adult and f.present)
        elif any(f for f in self.extended_family if f.adult and f.present):
            next_of_kin = next(f for f in self.extended_family if f.adult and f.present)
        elif any(f for f in self.friends if f.adult and f.present):
            next_of_kin = next(f for f in self.friends if f.adult and f.present)
        else:
            next_of_kin = random.choice(
                [r for r in self.city.residents if r.adult and r.present]
            )
        return next_of_kin

    @property
    def nuclear_family(self):
        """Return this person's nuclear family."""
        nuclear_family = {self}
        if self.spouse and self.spouse.present:
            nuclear_family.add(self.spouse)
        for kid in self.spouse.kids & self.kids if self.spouse else self.kids:
            if kid.home is self.home and kid.present:
                nuclear_family.add(kid)
        return nuclear_family

    @property
    def kids_at_home(self):
        """Return kids of this person that live with them, if any."""
        kids_at_home = {k for k in self.kids if k.home is self.home and k.present}
        return kids_at_home

    @property
    def life_events(self):
        """Return the major events of this person's life."""
        events = [self.birth, self.adoption]
        events += self.moves
        events += self.lay_offs
        events += [job.hiring for job in self.occupations]
        events += self.marriages
        events += [kid.birth for kid in self.kids]
        events += self.divorces
        events += self.name_changes
        events += self.home_purchases
        events += list(self.building_commissions)
        if self.retirement:
            events.append(self.retirement)
        events += [self.departure, self.death]
        while None in events:
            events.remove(None)
        events.sort(key=lambda ev: ev.event_number)  # Sort chronologically
        return events

    @property
    def year_i_moved_here(self):
        """Return the year this person moved to this city."""
        return self.moves[0].year

    @property
    def age_and_gender_description(self):
        """Return a string broadly capturing this person's age."""
        if self.age < 1:
            return 'an infant boy' if self.male else 'an infant girl'
        elif self.age < 4:
            return 'a boy toddler' if self.male else 'a girl toddler'
        elif self.age < 10:
            return 'a young boy' if self.male else 'a young girl'
        elif self.age < 13:
            return 'a preteen boy' if self.male else 'a preteen girl'
        elif self.age < 20:
            return 'a teenage boy' if self.male else 'a teenage girl'
        elif self.age < 25:
            return 'a young man' if self.male else 'a young woman'
        elif self.age < 45:
            return 'a man' if self.male else 'a woman'
        elif self.age < 65:
            return 'a middle-aged man' if self.male else 'a middle-aged woman'
        elif self.age < 75:
            return 'an older man' if self.male else 'an older woman'
        else:
            return 'an elderly man' if self.male else 'an elderly woman'

    @property
    def basic_appearance_description(self):
        """Return a string broadly capturing this person's basic appearance."""
        features = []
        if self.face.distinctive_features.tattoo == 'yes':
            features.append('a prominent tattoo')
        if self.face.distinctive_features.scar == 'yes':
            features.append('a visible scar')
        if self.face.distinctive_features.birthmark == 'yes':
            features.append('a noticeable birthmark')
        if self.face.distinctive_features.freckles == 'yes':
            features.append('freckles')
        if self.face.distinctive_features.glasses == 'yes':
            features.append('glasses')
        if self.face.hair.length == 'bald':
            features.append('a bald head')
        else:
            features.append('{} {} hair'.format(
                'medium-length' if self.face.hair.length == 'medium' else self.face.hair.length,
                'blond' if self.male and self.face.hair.color == 'blonde' else self.face.hair.color
            )
            )
        if self.face.facial_hair.style == 'sideburns' and self.male and self.age > 14:
            features.append('sideburns')
        elif self.face.facial_hair.style != 'none' and self.male and self.age > 14:
            features.append('a {}'.format(str(self.face.facial_hair.style)))
        if len(features) > 2:
            return '{}, and {}'.format(', '.join(feature for feature in features[:-1]), features[-1])
        else:
            return ' and '.join(features)

    @property
    def description(self):
        """Return a basic description of this person."""
        broader_skin_color = {
            'black': 'dark', 'brown': 'dark',
            'beige': 'light', 'pink': 'light',
            'white': 'light'
        }
        # Cut off the article ('a' or 'an') at the beginning of the
        # age_and_gender_description so that we can prepend a
        # skin-color tidbit
        age_and_gender_description = ' '.join(self.age_and_gender_description.split()[1:])
        return "a {broad_skin_color}-skinned {age_and_gender} with {prominent_features}{deceased}".format(
            broad_skin_color=broader_skin_color[self.face.skin.color],
            age_and_gender=age_and_gender_description,
            prominent_features=self.basic_appearance_description,
            deceased=' (deceased)' if self.dead else ''
        )

    def get_feature(self, feature_type):
        """Return this person's feature of the given type."""
        # Sex
        if feature_type == "sex":
            return 'm' if self.male else 'f'
        # Status
        if feature_type == "status":
            if self.present:
                return "alive"
            elif self.dead:
                return "dead"
            elif self.departure:
                return "departed"
        elif feature_type == "departure year":
            return 'None' if not self.departure else str(self.departure.year)
        elif feature_type == "marital status":
            if self.spouse:
                return 'married'
            elif not self.marriages:
                return 'single'
            elif self.widowed:
                return 'widowed'
            else:
                return 'divorced'
        # Age
        elif feature_type == "birth year":
            return str(self.birth_year)
        elif feature_type == "death year":
            return str(self.death_year)
        elif feature_type == "approximate age":
            return '{}0s'.format(self.age/10)
        # Name
        elif feature_type == "first name":
            return self.first_name
        elif feature_type == "middle name":
            return self.middle_name
        elif feature_type == "last name":
            return self.last_name
        elif feature_type == "suffix":
            return self.suffix if self.suffix else 'None'  # Because '' reserve for forgettings
        elif feature_type == "surname ethnicity":
            return self.last_name.ethnicity
        elif feature_type == "hyphenated surname":
            return 'yes' if self.last_name.hyphenated else 'no'
        # Occupation
        elif feature_type == "workplace":
            return "None" if not self.occupations else self.occupations[-1].company.name  # Name of company
        elif feature_type == "job title":
            return "None" if not self.occupations else self.occupations[-1].vocation
        elif feature_type == "job shift":
            return "None" if not self.occupations else self.occupations[-1].shift
        elif feature_type == "workplace address":
            return "None" if not self.occupations else self.occupations[-1].company.address
        elif feature_type == "workplace block":
            return "None" if not self.occupations else self.occupations[-1].company.block
        elif feature_type == "job status":
            if self.occupation:
                return "employed"
            elif self.retired:
                return "retired"
            else:
                return "unemployed"
        # Home
        elif feature_type == "home":
            return self.home.name
        elif feature_type == "home address":
            return self.home.address
        elif feature_type == "home block":
            return self.home.block
        # Appearance
        elif feature_type == "skin color":
            return self.face.skin.color
        elif feature_type == "head size":
            return self.face.head.size
        elif feature_type == "head shape":
            return self.face.head.shape
        elif feature_type == "hair length":
            return self.face.hair.length
        elif feature_type == "hair color":
            return self.face.hair.color
        elif feature_type == "eyebrow size":
            return self.face.eyebrows.size
        elif feature_type == "eyebrow color":
            return self.face.eyebrows.color
        elif feature_type == "mouth size":
            return self.face.mouth.size
        elif feature_type == "ear size":
            return self.face.ears.size
        elif feature_type == "ear angle":
            return self.face.ears.angle
        elif feature_type == "nose size":
            return self.face.nose.size
        elif feature_type == "nose shape":
            return self.face.nose.shape
        elif feature_type == "eye size":
            return self.face.eyes.size
        elif feature_type == "eye shape":
            return self.face.eyes.shape
        elif feature_type == "eye color":
            return self.face.eyes.color
        elif feature_type == "eye horizontal settedness":
            return self.face.eyes.horizontal_settedness
        elif feature_type == "eye vertical settedness":
            return self.face.eyes.vertical_settedness
        elif feature_type == "facial hair style":
            return self.face.facial_hair.style
        elif feature_type == "freckles":
            return self.face.distinctive_features.freckles
        elif feature_type == "birthmark":
            return self.face.distinctive_features.birthmark
        elif feature_type == "scar":
            return self.face.distinctive_features.scar
        elif feature_type == "tattoo":
            return self.face.distinctive_features.tattoo
        elif feature_type == "glasses":
            return self.face.distinctive_features.glasses
        elif feature_type == "sunglasses":
            return self.face.distinctive_features.sunglasses
        # Have to do special thing for whereabouts, because they are indexed by date;
        # specifically, we parse the feature type, which will look something like
        # 'whereabouts 723099-1'
        elif 'whereabouts' in feature_type:
            timestep = feature_type[12:]
            ordinal_date, day_or_night = timestep.split('-')
            whereabout_object = self.whereabouts.date[(int(ordinal_date), int(day_or_night))]
            return whereabout_object.location.name

    def get_knowledge_about_person(self, other_person, feature_type):
        """Return this person's knowledge about another person's feature of the given type."""
        if other_person not in self.mind.mental_models:
            return None
        # Status
        elif feature_type == "status":
            return self.mind.mental_models[other_person].status.status
        # Name
        elif feature_type == "first name":
            return self.mind.mental_models[other_person].name.first_name
        elif feature_type == "middle name":
            return self.mind.mental_models[other_person].name.middle_name
        elif feature_type == "last name":
            return self.mind.mental_models[other_person].name.last_name
        # Occupation
        elif feature_type == "workplace":
            return (self.mind.mental_models[other_person].occupation.company if  # Name of company
                    self.mind.mental_models[other_person].occupation.company else None)
        elif feature_type == "job title":
            return self.mind.mental_models[other_person].occupation.job_title
        elif feature_type == "job shift":
            return self.mind.mental_models[other_person].occupation.shift
        elif feature_type == "workplace address":
            if (self.mind.mental_models[other_person].occupation.company and
                    self.mind.mental_models[other_person].occupation.company.mental_model):
                return self.mind.mental_models[other_person].occupation.company.mental_model.address
            else:
                return None
        elif feature_type == "workplace block":
            if (self.mind.mental_models[other_person].occupation.company and
                    self.mind.mental_models[other_person].occupation.company.mental_model):
                return self.mind.mental_models[other_person].occupation.company.mental_model.block
            else:
                return None
        # Home
        elif feature_type == "home":
            return (str(self.mind.mental_models[other_person].home) if  # Name of residence
                    self.mind.mental_models[other_person].home else None)
        elif feature_type == "home address":
            if (self.mind.mental_models[other_person].home and
                    self.mind.mental_models[other_person].home.mental_model):
                return self.mind.mental_models[other_person].home.mental_model.address
            else:
                return None
        elif feature_type == "home block":
            if (self.mind.mental_models[other_person].home and
                    self.mind.mental_models[other_person].home.mental_model):
                return self.mind.mental_models[other_person].home.mental_model.block
            else:
                return None
        # Appearance
        elif feature_type == "skin color":
            return self.mind.mental_models[other_person].face.skin.color
        elif feature_type == "head size":
            return self.mind.mental_models[other_person].face.head.size
        elif feature_type == "head shape":
            return self.mind.mental_models[other_person].face.head.shape
        elif feature_type == "hair length":
            return self.mind.mental_models[other_person].face.hair.length
        elif feature_type == "hair color":
            return self.mind.mental_models[other_person].face.hair.color
        elif feature_type == "eyebrow size":
            return self.mind.mental_models[other_person].face.eyebrows.size
        elif feature_type == "eyebrow color":
            return self.mind.mental_models[other_person].face.eyebrows.color
        elif feature_type == "mouth size":
            return self.mind.mental_models[other_person].face.mouth.size
        elif feature_type == "ear size":
            return self.mind.mental_models[other_person].face.ears.size
        elif feature_type == "ear angle":
            return self.mind.mental_models[other_person].face.ears.angle
        elif feature_type == "nose size":
            return self.mind.mental_models[other_person].face.nose.size
        elif feature_type == "nose shape":
            return self.mind.mental_models[other_person].face.nose.shape
        elif feature_type == "eye size":
            return self.mind.mental_models[other_person].face.eyes.size
        elif feature_type == "eye shape":
            return self.mind.mental_models[other_person].face.eyes.shape
        elif feature_type == "eye color":
            return self.mind.mental_models[other_person].face.eyes.color
        elif feature_type == "eye horizontal settedness":
            return self.mind.mental_models[other_person].face.eyes.horizontal_settedness
        elif feature_type == "eye vertical settedness":
            return self.mind.mental_models[other_person].face.eyes.vertical_settedness
        elif feature_type == "facial hair style":
            return self.mind.mental_models[other_person].face.facial_hair.style
        elif feature_type == "freckles":
            return self.mind.mental_models[other_person].face.distinctive_features.freckles
        elif feature_type == "birthmark":
            return self.mind.mental_models[other_person].face.distinctive_features.birthmark
        elif feature_type == "scar":
            return self.mind.mental_models[other_person].face.distinctive_features.scar
        elif feature_type == "tattoo":
            return self.mind.mental_models[other_person].face.distinctive_features.tattoo
        elif feature_type == "glasses":
            return self.mind.mental_models[other_person].face.distinctive_features.glasses
        elif feature_type == "sunglasses":
            return self.mind.mental_models[other_person].face.distinctive_features.sunglasses

    def get_knowledge_about_place(self, place, feature_type):
        """Return this person's knowledge about this place's feature of the given type."""
        if place not in self.mind.mental_models:
            return None
        elif feature_type == "home is apartment":
            return "yes" if self.mind.mental_models[place].apartment else "no"
        elif feature_type == "business block":
            return self.mind.mental_models[place].block
        elif feature_type == "business address":
            return self.mind.mental_models[place].address
        elif feature_type == "home block":
            return self.mind.mental_models[place].block
        elif feature_type == "home address":
            return self.mind.mental_models[place].address

    def belief(self, entity, feature_type):
        """Return this person's currently held belief facet about entity's feature_type.

        If this person does not hold a belief about entity's feature type (or entity at
        all), return None.
        """
        if entity is None:  # E.g., if querying p.accurate_belief(p.father, 'first name'), but p is a PersonExNihilo
            return None
        elif entity not in self.mind.mental_models:
            return None
        elif entity.type == 'person':
            return self.get_knowledge_about_person(other_person=entity, feature_type=feature_type)
        elif entity.type == 'residence' or entity.type == 'business':
            return self.get_knowledge_about_place(place=entity, feature_type=feature_type)

    def accurate_belief(self, entity, feature_type):
        """Return a boolean indicating whether this person has an *accurate* belief about entity's feature_type."""
        belief_facet = self.belief(entity=entity, feature_type=feature_type)
        if belief_facet and belief_facet.accurate:
            return True
        else:
            return False

    def inaccurate_belief(self, entity, feature_type):
        """Return a boolean indicating whether this person has an *inaccurate* belief about entity's feature_type.

        If this person has no such belief, False is returned.
        """
        belief_facet = self.belief(entity=entity, feature_type=feature_type)
        if belief_facet and not belief_facet.accurate:
            return True
        else:
            return False

    def sources(self, entity, feature_type=None):
        """Return this person's sources, in order of most informative to least, for their
        knowledge pertaining entity's feature_type (or to the entity in general, if
        None is passed).
        """
        all_my_sources = []
        if feature_type:
            all_my_relevant_beliefs = [
                f for f in self.all_belief_facets if f.subject is entity and f.feature_type == feature_type
            ]
        else:  # Just collect all facets pertaining to entity
            all_my_relevant_beliefs = [f for f in self.all_belief_facets if f.subject is entity]
        for facet in all_my_relevant_beliefs:
            for piece in facet.evidence:
                if piece.source:
                    all_my_sources.append(piece.source)
        all_my_sources.sort(key=lambda source: all_my_sources.count(source), reverse=True)
        return all_my_sources

    def top_source(self, entity, feature_type=None):
        """Return this person's *top* source for their knowledge pertaining entity's
        feature_type (or to the entity in general, if None is passed).
        """
        try:
            return self.sources(entity=entity, feature_type=feature_type)[0]
        except IndexError:  # No sources for this information
            return None

    def _common_familial_relation_to_me(self, person):
        """Return the immediate common familial relation to the given person, if any.

        This method gets called by decision-making methods that get executed often,
        since it runs much more quickly than known_relation_to_me, which itself is much
        richer in the number of relations it checks for. Basically, this method
        is meant for quick decision making, and known_relation_to_me for dialogue generation.
        """
        if person is self.spouse:
            return 'husband' if person.male else 'wife'
        if person is self.father:
            return 'father'
        elif person is self.mother:
            return 'mother'
        elif person in self.brothers:
            return 'brother'
        elif person in self.sisters:
            return 'sister'
        elif person in self.aunts:
            return 'aunt'
        elif person in self.uncles:
            return 'uncle'
        elif person in self.sons:
            return 'son'
        elif person in self.daughters:
            return 'daughter'
        elif person in self.cousins:
            return 'cousin'
        elif person in self.nephews:
            return 'nephew'
        elif person in self.nieces:
            return 'niece'
        elif person in self.greatgrandparents:
            return 'greatgrandfather' if person.male else 'greatgrandmother'
        elif person in self.grandparents:
            return 'grandfather' if person.male else 'grandmother'
        elif person in self.grandchildren:
            return 'grandson' if person.male else 'granddaughter'
        else:
            return None

    def relation_to_me(self, person):
        """Return the primary relation of another person to me, if any.

        This method is much richer than _common_familial_relation_to_me
        in the number of relationships that it checks for. While the former is meant
        for quick character decision making, this method should be used for things
        like dialogue generation, where performance is much less important than
        richness and expressivity. Because this method is meant to be used to generate
        dialogue, it won't return specific relationships like 'first cousin, once removed',
        because everyday people don't know or reference these relationships.
        """
        if person is self:
            return 'self'
        elif person in self.greatgrandparents:
            return 'greatgrandfather' if person.male else 'greatgrandmother'
        elif person in self.grandparents:
            return 'grandfather' if person.male else 'grandmother'
        elif person is self.father:
            return 'father'
        elif person is self.mother:
            return 'mother'
        elif person in self.aunts:
            return 'aunt'
        elif person in self.uncles:
            return 'uncle'
        elif person in self.brothers:
            return 'brother'
        elif person in self.sisters:
            return 'sister'
        elif person in self.cousins:
            return 'cousin'
        elif person in self.sons:
            return 'son'
        elif person in self.daughters:
            return 'daughter'
        elif person in self.nephews:
            return 'nephew'
        elif person in self.nieces:
            return 'niece'
        elif person is self.spouse:
            return 'husband' if person.male else 'wife'
        elif self.divorces and any(d for d in self.divorces if person in d.subjects):
            return 'ex-husband' if person.male else 'ex-wife'
        elif self.widowed and any(m for m in self.marriages if person in m.subjects and m.terminus is person.death):
            return 'deceased husband' if person.male else 'deceased wife'
        elif person.spouse in self.siblings or self.spouse in person.siblings:
            return 'brother in law' if person.male else 'sister in law'
        elif self.father and any(d for d in self.father.divorces if person in d.subjects):
            return "father's ex-{}".format('husband' if person.male else 'wife')
        elif self.mother and any(d for d in self.mother.divorces if person in d.subjects):
            return "mother's ex-{}".format('husband' if person.male else 'wife')
        elif any(s for s in self.brothers if any(d for d in s.divorces if person in d.subjects)):
            return "brother's ex-{}".format('husband' if person.male else 'wife')
        elif any(s for s in self.sisters if any(d for d in s.divorces if person in d.subjects)):
            return "sister's ex-{}".format('husband' if person.male else 'wife')
        elif any(s for s in self.brothers if any(
                m for m in s.marriages if person in m.subjects and m.terminus is person.death)):
            return "brother's deceased {}".format('husband' if person.male else 'wife')
        elif any(s for s in self.sisters if any(
                m for m in s.marriages if person in m.subjects and m.terminus is person.death)):
            return "sister's deceased {}".format('husband' if person.male else 'wife')
        elif any(s for s in self.brothers if any(
                m for m in s.marriages if person in m.subjects and m.terminus is s.death)):
            return "deceased brother's former {}".format('husband' if person.male else 'wife')
        elif any(s for s in self.sisters if any(
                m for m in s.marriages if person in m.subjects and m.terminus is s.death)):
            return "deceased sister's former {}".format('husband' if person.male else 'wife')
        elif person.spouse in self.kids:
            return 'son in law' if person.male else 'daughter in law'
        elif self.spouse and person in self.spouse.parents:
            return 'father in law' if person.male else 'mother in law'
        elif self.spouse and person in self.spouse.sons:
            return 'stepson'
        elif self.spouse and person in self.spouse.daughters:
            return 'stepdaughter'
        elif self.mother and person is self.mother.spouse:
            return 'stepfather' if person.male else 'stepmother'
        elif self.father and person is self.father.spouse:
            return 'stepfather' if person.male else 'stepmother'
        elif self.greatgrandparents & person.greatgrandparents:
            return 'second cousin'
        elif self.greatgrandparents & person.siblings:
            return 'great uncle' if person.male else 'great aunt'
        elif person is self.best_friend:
            return 'best friend'
        elif person is self.worst_enemy:
            return 'worst enemy'
        elif person is self.significant_other:
            return 'boyfriend' if person.male else 'girlfriend'
        # elif person is self.love_interest:  # Commented out because no one would say this
        #     return 'love interest'
        elif person in self.coworkers:
            return 'coworker'
        elif person in self.neighbors:
            return 'neighbor'
        elif person in self.enemies:
            return 'enemy'
        elif any(p for p in self.parents if person is p.significant_other):
            p = next(p for p in self.parents if person is p.significant_other)
            return "{}'s {}".format(
                'father' if p.male else 'mother', 'boyfriend' if person.male else 'girlfriend'
            )
        elif any(k for k in self.kids if person is k.significant_other):
            k = next(k for k in self.kids if person is k.significant_other)
            return "{}'s {}".format(
                'son' if k.male else 'daughter', 'boyfriend' if person.male else 'girlfriend'
            )
        elif any(s for s in self.siblings if person is s.significant_other):
            s = next(s for s in self.siblings if person is s.significant_other)
            return "{}'s {}".format(
                'brother' if s.male else 'sister', 'boyfriend' if person.male else 'girlfriend'
            )
        elif self.spouse and person is self.spouse.best_friend:
            return "{}'s best friend".format('husband' if self.spouse.male else 'wife')
        elif self.mother and person is self.mother.best_friend:
            return "mother's best friend"
        elif self.father and person is self.father.best_friend:
            return "father's best friend"
        elif any(s for s in self.siblings if person is s.best_friend):
            s = next(s for s in self.siblings if person is s.best_friend)
            return "{}'s best friend".format('brother' if s.male else 'sister')
        elif any(k for k in self.kids if person is k.best_friend):
            k = next(k for k in self.kids if person is k.best_friend)
            return "{}'s best friend".format('son' if k.male else 'daughter')
        elif self.spouse and person in self.spouse.coworkers:
            return "{}'s coworker".format('husband' if self.spouse.male else 'wife')
        elif self.mother and person in self.mother.coworkers:
            return "mother's coworker"
        elif self.father and person in self.father.coworkers:
            return "father's coworker"
        elif person in self.friends:
            return 'friend'
        elif self.spouse and person in self.spouse.friends:
            return "{}'s friend".format('husband' if self.spouse.male else 'wife')
        elif self.mother and person in self.mother.friends:
            return "mother's friend"
        elif self.father and person in self.father.friends:
            return "father's friend"
        elif any(k for k in self.kids if person in k.friends):
            k = next(k for k in self.kids if person in k.friends)
            return "{}'s friend".format('son' if k.male else 'daughter')
        elif any(s for s in self.siblings if person in s.friends):
            s = next(s for s in self.siblings if person in s.friends)
            return "{}'s friend".format('brother' if s.male else 'sister')
        elif person in self.acquaintances:
            return 'acquaintance'
        else:
            return None

    def known_relation_to_me(self, person):
        """Return the primary relations of another person to me that are grounded in my knowledge, if any,
        as well as the hinge in our relationship, if any.

        An example of a hinge: if someone is my wife's friend, then my wife is the hinge.
        """
        # TODO ADD FURTHER PRECONDITIONS ON SOME, E.G., YOU MUST KNOW WHERE YOUR MOM WORKS
        relations = []
        if person is self:
            relation = 'self'
            hinge = None
            relations.append((relation, hinge))
        if person in self.greatgrandparents:
            relation = 'greatgrandfather' if person.male else 'greatgrandmother'
            hinge = None
            relations.append((relation, hinge))
        if person in self.grandparents:
            relation = 'grandfather' if person.male else 'grandmother'
            hinge = None
            relations.append((relation, hinge))
        if person is self.father:
            relation = 'father'
            hinge = None
            relations.append((relation, hinge))
        if person is self.mother:
            relation = 'mother'
            hinge = None
            relations.append((relation, hinge))
        if person in self.aunts:
            relation = 'aunt'
            hinge = None
            relations.append((relation, hinge))
        if person in self.uncles:
            relation = 'uncle'
            hinge = None
            relations.append((relation, hinge))
        if person in self.brothers:
            relation = 'brother'
            hinge = None
            relations.append((relation, hinge))
        if person in self.sisters:
            relation = 'sister'
            hinge = None
            relations.append((relation, hinge))
        if person in self.cousins:
            relation = 'cousin'
            hinge = None
            relations.append((relation, hinge))
        if person in self.sons:
            relation = 'son'
            hinge = None
            relations.append((relation, hinge))
        if person in self.daughters:
            relation = 'daughter'
            hinge = None
            relations.append((relation, hinge))
        if person in self.nephews:
            relation = 'nephew'
            hinge = None
            relations.append((relation, hinge))
        if person in self.nieces:
            relation = 'niece'
            hinge = None
            relations.append((relation, hinge))
        if person is self.spouse:
            relation = 'husband' if person.male else 'wife'
            hinge = None
            relations.append((relation, hinge))
        if self.divorces and any(d for d in self.divorces if person in d.subjects):
            relation = 'ex-husband' if person.male else 'ex-wife'
            hinge = None
            relations.append((relation, hinge))
        if self.widowed and any(m for m in self.marriages if person in m.subjects and m.terminus is person.death):
            relation = 'deceased husband' if person.male else 'deceased wife'
            hinge = None
            relations.append((relation, hinge))
        if person.spouse in self.siblings:
            relation = "{}'s {}".format(
                'sister' if person.spouse.female else 'brother', 'husband' if person.male else 'wife'
            )
            hinge = person.spouse
            relations.append((relation, hinge))
        if self.spouse in person.siblings:
            relation = "{}'s {}".format(
                'husband' if self.spouse.male else 'wife', 'brother' if person.male else 'sister'
            )
            hinge = self.spouse
            relations.append((relation, hinge))
        if self.father and any(d for d in self.father.divorces if person in d.subjects):
            relation = "father's ex-{}".format('husband' if person.male else 'wife')
            hinge = self.father
            relations.append((relation, hinge))
        if self.mother and any(d for d in self.mother.divorces if person in d.subjects):
            relation = "mother's ex-{}".format('husband' if person.male else 'wife')
            hinge = self.mother
            relations.append((relation, hinge))
        if any(s for s in self.brothers if any(d for d in s.divorces if person in d.subjects)):
            relation = "brother's ex-{}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.brothers if any(d for d in s.divorces if person in d.subjects)
            )
            relations.append((relation, hinge))
        if any(s for s in self.sisters if any(d for d in s.divorces if person in d.subjects)):
            relation = "sister's ex-{}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.sisters if any(d for d in s.divorces if person in d.subjects)
            )
            relations.append((relation, hinge))
        if any(s for s in self.brothers if any(
                m for m in s.marriages if person in m.subjects and m.terminus is person.death and
                person is not s)):
            relation = "brother's deceased {}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.brothers if any(
                    m for m in s.marriages if person in m.subjects and m.terminus is person.death)
            )
            relations.append((relation, hinge))
        if any(s for s in self.sisters if any(
                m for m in s.marriages if person in m.subjects and m.terminus is person.death and
                person is not s)):
            relation = "sister's deceased {}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.sisters if any(
                    m for m in s.marriages if person in m.subjects and m.terminus is person.death)
            )
            relations.append((relation, hinge))
        if any(s for s in self.brothers if any(
                m for m in s.marriages if person in m.subjects and m.terminus is s.death and
                person is not s)):
            relation = "deceased brother's former {}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.brothers if any(
                    m for m in s.marriages if person in m.subjects and m.terminus is s.death)
            )
            relations.append((relation, hinge))
        if any(s for s in self.sisters if any(
                m for m in s.marriages if person in m.subjects and m.terminus is s.death and
                person is not s)):
            relation = "deceased sister's former {}".format('husband' if person.male else 'wife')
            hinge = next(
                s for s in self.sisters if any(
                    m for m in s.marriages if person in m.subjects and m.terminus is s.death)
            )
            relations.append((relation, hinge))
        if person.spouse in self.kids:
            relation = "{}'s {}".format(
                "son" if person.spouse.male else "daughter", "husband" if person.male else "wife"
            )
            hinge = person.spouse
            relations.append((relation, hinge))
        if self.spouse and person in self.spouse.parents:
            relation = "{}'s {}".format(
                "husband" if self.spouse.male else "wife", "father" if person.male else "mother"
            )
            hinge = self.spouse
            relations.append((relation, hinge))
        if self.spouse and person in self.spouse.sons and person not in self.sons:
            relation = 'stepson'
            hinge = None
            relations.append((relation, hinge))
        if self.spouse and person in self.spouse.daughters and person not in self.daughters:
            relation = 'stepdaughter'
            hinge = None
            relations.append((relation, hinge))
        if self.mother and person is self.mother.spouse and person is not self.father:
            relation = 'stepfather' if person.male else 'stepmother'
            hinge = None
            relations.append((relation, hinge))
        if self.father and person is self.father.spouse and person is not self.mother:
            relation = 'stepfather' if person.male else 'stepmother'
            hinge = None
            relations.append((relation, hinge))
        if self.greatgrandparents & person.greatgrandparents and person not in self.siblings | self.cousins | {self}:
            relation = 'second cousin'
            hinge = None
            relations.append((relation, hinge))
        if self.greatgrandparents & person.siblings:
            relation = 'great uncle' if person.male else 'great aunt'
            hinge = None
            relations.append((relation, hinge))
        if person is self.best_friend:
            relation = 'best friend'
            hinge = None
            relations.append((relation, hinge))
        if person is self.worst_enemy:
            relation = 'worst enemy'
            hinge = None
            relations.append((relation, hinge))
        if person is self.significant_other and person is not self.spouse:
            relation = 'boyfriend' if person.male else 'girlfriend'
            hinge = None
            relations.append((relation, hinge))
        if person is self.love_interest:
            relation = 'love interest'
            hinge = None
            relations.append((relation, hinge))
        if person in self.coworkers:
            relation = 'coworker'
            hinge = None
            relations.append((relation, hinge))
        if person in self.former_coworkers:
            relation = 'former coworker'
            hinge = None
            relations.append((relation, hinge))
        if person in self.neighbors:
            relation = 'neighbor'
            hinge = None
            relations.append((relation, hinge))
        if person in self.former_neighbors:
            relation = 'former neighbor'
            hinge = None
            relations.append((relation, hinge))
        if person in self.former_contractors:
            relation = 'former contractor'
            hinge = None
            relations.append((relation, hinge))
        if person in self.enemies:
            relation = 'enemy'
            hinge = None
            relations.append((relation, hinge))
        if any(p for p in self.parents if person is p.significant_other and person is not p.spouse):
            p = next(p for p in self.parents if person is p.significant_other)
            relation = "{}'s {}".format(
                'father' if p.male else 'mother', 'boyfriend' if person.male else 'girlfriend'
            )
            hinge = p
            relations.append((relation, hinge))
        if any(k for k in self.kids if person is k.significant_other and person is not k.spouse):
            k = next(k for k in self.kids if person is k.significant_other)
            relation = "{}'s {}".format(
                'son' if k.male else 'daughter', 'boyfriend' if person.male else 'girlfriend'
            )
            hinge = k
            relations.append((relation, hinge))
        if any(s for s in self.siblings if person is s.significant_other and person is not s.spouse):
            s = next(s for s in self.siblings if person is s.significant_other)
            relation = "{}'s {}".format(
                'brother' if s.male else 'sister', 'boyfriend' if person.male else 'girlfriend'
            )
            hinge = s
            relations.append((relation, hinge))
        if self.spouse and person is self.spouse.best_friend:
            relation = "{}'s best friend".format('husband' if self.spouse.male else 'wife')
            hinge = self.spouse
            relations.append((relation, hinge))
        if self.mother and person is self.mother.best_friend:
            relation = "mother's best friend"
            hinge = self.mother
            relations.append((relation, hinge))
        if self.father and person is self.father.best_friend:
            relation = "father's best friend"
            hinge = self.father
            relations.append((relation, hinge))
        if any(s for s in self.siblings if person is s.best_friend):
            s = next(s for s in self.siblings if person is s.best_friend)
            relation = "{}'s best friend".format('brother' if s.male else 'sister')
            hinge = s
            relations.append((relation, hinge))
        if any(k for k in self.kids if person is k.best_friend):
            k = next(k for k in self.kids if person is k.best_friend)
            relation = "{}'s best friend".format('son' if k.male else 'daughter')
            hinge = k
            relations.append((relation, hinge))
        if self.spouse and person in self.spouse.coworkers:
            relation = "{}'s coworker".format('husband' if self.spouse.male else 'wife')
            hinge = self.spouse
            relations.append((relation, hinge))
        if self.mother and person in self.mother.coworkers:
            relation = "mother's coworker"
            hinge = self.mother
            relations.append((relation, hinge))
        if self.father and person in self.father.coworkers:
            relation = "father's coworker"
            hinge = self.father
            relations.append((relation, hinge))
        if person in self.friends:
            relation = 'friend'
            hinge = None
            relations.append((relation, hinge))
        if self.spouse and person in self.spouse.friends:
            relation = "{}'s friend".format('husband' if self.spouse.male else 'wife')
            hinge = self.spouse
            relations.append((relation, hinge))
        if self.mother and person in self.mother.friends:
            relation = "mother's friend"
            hinge = self.mother
            relations.append((relation, hinge))
        if self.father and person in self.father.friends:
            relation = "father's friend"
            hinge = self.father
            relations.append((relation, hinge))
        if any(k for k in self.kids if person in k.friends):
            k = next(k for k in self.kids if person in k.friends)
            relation = "{}'s friend".format('son' if k.male else 'daughter')
            hinge = k
            relations.append((relation, hinge))
        if any(s for s in self.siblings if person in s.friends):
            s = next(s for s in self.siblings if person in s.friends)
            relation = "{}'s friend".format('brother' if s.male else 'sister')
            hinge = s
            relations.append((relation, hinge))
        if person in self.acquaintances:
            relation = 'acquaintance'
            hinge = None
            relations.append((relation, hinge))
        # Throw out any for which hinge in not in my mental model
        keepers = []
        for relation, hinge in relations:
            if not hinge or hinge in self.mind.mental_models:
                keepers.append((relation, hinge))
        return keepers

    def change_name(self, new_last_name, reason):
        """Change this person's (official) name."""
        lawyer = self.contract_person_of_certain_occupation(occupation_in_question=occupation.Lawyer)
        if lawyer:
            lawyer.occupation.file_name_change(person=self, new_last_name=new_last_name, reason=reason)
        else:
            event.NameChange(subject=self, new_last_name=new_last_name, reason=reason, lawyer=None)

    def have_sex(self, partner, protection):
        """Have sex with partner."""
        config = self.game.config
        self.sexual_partners.add(partner)
        partner.sexual_partners.add(self)
        # TODO modify spark between these people
        if self.male != partner.male and not self.pregnant and not partner.pregnant:
            if (not protection) or random.random() < config.chance_protection_does_not_work:
                self._determine_whether_pregnant(partner=partner)

    def _determine_whether_pregnant(self, partner):
        """Determine whether self or partner is now pregnant."""
        config = self.game.config
        # Determine whether child is conceived
        female_partner = self if self.female else partner
        chance_of_conception = config.function_to_determine_chance_of_conception(
            female_age=female_partner.age
        )
        if random.random() < chance_of_conception:
            female_partner.impregnated_by = self if female_partner is partner else partner
            female_partner.conception_year = self.game.year
            female_partner.due_date = self.game.ordinal_date + 270
            female_partner.pregnant = True

    def marry(self, partner):
        """Marry partner."""
        # assert(self.present and partner.present), (
        #     "{0} tried to marry {1}, but one of them is dead or departed.".format(self.id, partner.id)
        # )
        # TODO weird bug going on here
        if self.present and partner.present:
            event.Marriage(subjects=(self, partner))

    def divorce(self, partner):
        """Divorce partner."""
        assert(self.alive and partner.alive), "{0} tried to divorce {1}, but one of them is dead."
        assert(partner is self.spouse and partner.spouse is self), (
            "{0} tried to divorce {1}, whom they are not married to.".format(self.name, partner.name)
        )
        # The soon-to-be divorcees will decide together which lawyer to hire, because they are
        # technically still married (and spouses are considered as part of this method call)
        lawyer = self.contract_person_of_certain_occupation(occupation_in_question=occupation.Lawyer)
        lawyer.occupation.file_divorce(clients=(self, partner,))

    def give_birth(self):
        """Select a doctor and go to the hospital to give birth."""
        doctor = self.contract_person_of_certain_occupation(occupation_in_question=occupation.Doctor)
        if doctor:
            doctor.occupation.deliver_baby(mother=self)
        else:
            event.Birth(mother=self, doctor=None)

    def die(self, cause_of_death):
        """Die and get interred at the local cemetery."""
        mortician = self.next_of_kin.contract_person_of_certain_occupation(occupation_in_question=occupation.Mortician)
        if mortician:
            mortician.occupation.inter_body(deceased=self, cause_of_death=cause_of_death)
        else:  # This is probably the mortician themself dying
            event.Death(subject=self, mortician=None, cause_of_death=cause_of_death)

    def look_for_work(self):
        """Attempt to find a job at a local business.

        This method has every business in town that had potential job vacancies
        rate this person as a candidate for those vacancies. The person then
        gets hired by the company who has rated them highest, assuming they
        qualify for any positions at all.
        """
        # If a family member owns a company, and you're employable at that position,
        # try to get hired by that company for one of their supplemental positions
        if any(f for f in self.extended_family if f.occupation and f.occupation.company.owner is f.occupation):
            self._find_job_at_the_family_company()
        else:
            # Try to get hired by any company in town for one of their supplemental positions
            scores = self._get_scored_as_job_candidate_by_all_companies()
            # If this person qualified for any position, have them be hired to the one
            # for which they were scored mostly highly
            if scores:
                company, position, shift = max(scores, key=scores.get)
                company.hire(
                    occupation_of_need=position, shift=shift, to_replace=None,
                    fills_supplemental_job_vacancy=True, selected_candidate=self
                )

    def _find_job_at_the_family_company(self):
        """Try to get hired by a company that your family member owns."""
        must_add_supplemental_position = False
        # First, see if your father or mother owns a company
        family_companies = self._assemble_family_companies()
        for family_company in family_companies:
            if family_company.supplemental_vacancies['day']:
                position, shift = family_company.supplemental_vacancies['day'][0], 'day'
            elif family_company.supplemental_vacancies['night']:
                position, shift = family_company.supplemental_vacancies['night'][0], 'night'
            # If its your parent, they will accommodate and add another supplemental position
            elif family_company.owner.person in self.parents:
                must_add_supplemental_position = True
                initial_job_vacancies = self.game.config.initial_job_vacancies
                if self.game.config.initial_job_vacancies[family_company.__class__]['day']:
                    position, shift = (
                        initial_job_vacancies[family_company.__class__]['day'][0], 'day'
                    )
                elif self.game.config.initial_job_vacancies[family_company.__class__]['night']:
                    position, shift = (
                        initial_job_vacancies[family_company.__class__]['night'][0], 'night'
                    )
                elif self.game.config.initial_job_vacancies[family_company.__class__]['supplemental day']:
                    position, shift = (
                        initial_job_vacancies[family_company.__class__]['supplemental day'][0], 'day'
                    )
                else:
                    position, shift = (
                        initial_job_vacancies[family_company.__class__]['supplemental night'][0], 'night'
                    )
            else:
                # Nothing can be done in this circumstance, so move on to the next
                # family company
                break
            i_am_qualified_for_this_position = (
                family_company.check_if_person_is_qualified_for_the_position(
                    candidate=self, occupation_of_need=position
                )
            )
            if i_am_qualified_for_this_position:
                if must_add_supplemental_position:
                    family_company.supplemental_vacancies[shift].append(position)
                family_company.hire(
                    occupation_of_need=position, shift=shift, to_replace=None,
                    fills_supplemental_job_vacancy=True, selected_candidate=self,
                    hired_as_a_favor=must_add_supplemental_position
                )
                break

    def _assemble_family_companies(self):
        """Assemble all the companies in town owned by a family member of yours."""
        family_companies = []
        # If one of your parents owns a company, put that one first in the list
        # of family companies you'll try to get hired by
        if any(p for p in self.parents if p.occupation and p.occupation.company.owner is p.occupation):
            parent_who_owns_a_company = next(
                p for p in self.parents if p.occupation and p.occupation.company.owner is p.occupation
            )
            family_companies.append(parent_who_owns_a_company.occupation.company)
        else:
            family_members_who_own_companies = (
                f for f in self.extended_family if f.occupation and f.occupation.company.owner is f.occupation
            )
            for relative in family_members_who_own_companies:
                family_companies.append(relative.occupation.company)
        return family_companies

    def _get_scored_as_job_candidate_by_all_companies(self):
        """Get scored as a job candidate by all companies in town for all their supplemental positions."""
        scores = {}
        # Assemble scores of this person as a job candidate from all companies
        # in town for all of their open positions, day- or night-shift
        for company in self.city.companies:
            for shift in ('day', 'night'):
                for position in company.supplemental_vacancies[shift]:
                    i_am_qualified_for_this_position = (
                        company.check_if_person_is_qualified_for_the_position(
                            candidate=self, occupation_of_need=position
                        )
                    )
                    if i_am_qualified_for_this_position:
                        score = company.rate_job_candidate(person=self)
                        # The open positions are listed in order of priority, so
                        # penalize this position if its not the company's top priority
                        priority = company.supplemental_vacancies[shift].index(position)
                        score /= priority+1
                        scores[(company, position, shift)] = score
        return scores

    def move_out_of_parents(self):
        """Move out of parents' house."""
        home_to_move_into = self.secure_home()
        if home_to_move_into:
            self.move(new_home=home_to_move_into, reason=None)
        else:
            self.depart_city()

    def move(self, new_home, reason):
        """Move to an apartment or home."""
        event.Move(subjects=tuple(self.nuclear_family), new_home=new_home, reason=reason)

    def go_to(self, destination, occasion=None):
        """Go to destination and spend this timestep there."""
        if self.location:  # People just being instantiated won't have a location yet
            self.location.people_here_now.remove(self)
        self.location = destination
        if destination and self.alive:  # 'destination' will be None for Departures, and dead people go_to cemetery
            destination.people_here_now.add(self)
            # Update this person's whereabouts
            self.whereabouts.record(occasion=occasion)

    def pay(self, payee, amount):
        """Pay someone (for services rendered)."""
        if self.spouse:
            self.marriage.money -= amount
        else:
            self.money -= amount
        payee.money += amount

    def retire(self):
        """Retire from an occupation."""
        event.Retirement(subject=self)

    def depart_city(self, forced_nuclear_family=set()):
        """Depart the city (and thus the simulation), never to return.

        forced_nuclear_family is reserved for Marriage events in which the newlyweds
        cannot find housing in the city and so depart, potentially with their entire
        new mixed family. In this case, a special procedure (_move_spouses_and_any_kids_
        in_together) determines which stepchildren will move with them; because this
        procedure returns a different set of people than self.nuclear_family does, we
        need to allow the assertion of a forced nuclear family for Marriage-related
        Departures.
        """
        event.Departure(subject=self)
        nuclear_family = forced_nuclear_family if forced_nuclear_family else self.nuclear_family
        for person in nuclear_family - {self}:
            if person in self.city.residents:
                event.Departure(subject=person)

    def contract_person_of_certain_occupation(self, occupation_in_question):
        """Find a person of a certain occupation.

        Currently, a person scores all the potential hires in town and then selects
        one of the top three. TODO: Probabilistically select from all potential hires
        using the scores to derive likelihoods of selecting each.
        """
        if self.city:
            pool = list(self.city.workers_of_trade(occupation_in_question))
        else:  # PersonExNihilo who backstory is currently being retconned
            pool = []
        if pool:
            # If you or your spouse practice this occupation, DIY
            if isinstance(self.occupation, occupation_in_question):
                choice = self
            elif self.spouse and isinstance(self.spouse.occupation, occupation_in_question):
                choice = self.spouse
            # Otherwise, pick from the various people in town who do practice this occupation
            else:
                potential_hire_scores = self._rate_all_potential_contractors_of_certain_occupation(pool=pool)
                if len(potential_hire_scores) >= 3:
                    # Pick from top three
                    top_three_choices = heapq.nlargest(3, potential_hire_scores, key=potential_hire_scores.get)
                    if random.random() < 0.6:
                        choice = top_three_choices[0]
                    elif random.random() < 0.9:
                        choice = top_three_choices[1]
                    else:
                        choice = top_three_choices[2]
                else:
                    choice = max(potential_hire_scores)
        else:
            # This should only ever happen at the very beginning of a city's history where all
            # business types haven't been built in town yet
            choice = None
        return choice

    def _rate_all_potential_contractors_of_certain_occupation(self, pool):
        """Score all potential hires of a certain occupation."""
        scores = {}
        for person in pool:
            scores[person] = self._rate_potential_contractor_of_certain_occupation(person=person)
        return scores

    def _rate_potential_contractor_of_certain_occupation(self, person):
        """Score a potential hire of a certain occupation, with preference to family, friends, former hires.

        TODO: Have this be affected by personality (beyond what being a friend captures).
        """
        score = 0
        # Rate according to social reasons
        if self.spouse:
            people_involved_in_this_decision = (self, self.spouse)
        else:
            people_involved_in_this_decision = (self,)
        for decision_maker in people_involved_in_this_decision:
            if person in decision_maker.immediate_family:
                score += decision_maker.game.config.preference_to_contract_immediate_family
            elif person in decision_maker.extended_family:  # elif because immediate family is subset of extended family
                score += decision_maker.game.config.preference_to_contract_extended_family
            if person in decision_maker.friends:
                score += decision_maker.game.config.preference_to_contract_friend
            elif person in decision_maker.acquaintances:
                score += decision_maker.game.config.preference_to_contract_acquaintance
            if person in decision_maker.enemies:
                score += decision_maker.game.config.dispreference_to_hire_enemy
            if person in decision_maker.former_contractors:
                score += decision_maker.game.config.preference_to_contract_former_contract
        # Multiply score according to this person's experience in this occupation
        score *= person.game.config.function_to_derive_score_multiplier_bonus_for_experience(
            years_experience=person.occupation.years_experience
        )
        return score

    def purchase_home(self, purchasers, home):
        # TEMP THING DUE TO CIRCULAR DEPENDENCY -- SEE RESIDENCE.PY -- TODO
        event.HomePurchase(subjects=purchasers, home=home, realtor=None)

    def secure_home(self):
        """Find a home to move into.

        The person (and their spouse, if any) will decide between all the vacant
        homes and vacant lots (upon which they would build a new home) in the city.
        """
        chosen_home_or_lot = self._choose_vacant_home_or_vacant_lot()
        if chosen_home_or_lot:
            if chosen_home_or_lot in self.city.vacant_lots:
                # A vacant lot was chosen, so build
                home_to_move_into = self._commission_construction_of_a_house(lot=chosen_home_or_lot)
            elif chosen_home_or_lot in self.city.vacant_homes:
                # A vacant home was chosen
                home_to_move_into = self._purchase_home(home=chosen_home_or_lot)
            else:
                raise Exception(
                    "{} has secured a lot or home that is not known to be vacant.".format(self.name)
                )
        else:
            home_to_move_into = None  # The city is full; this will spark a departure
        return home_to_move_into

    def _commission_construction_of_a_house(self, lot):
        """Build a house to move into."""
        # Try to find an architect -- if you can't, you'll have to build it yourself
        architect = self.contract_person_of_certain_occupation(occupation_in_question=occupation.Architect)
        architect = None if not architect else architect.occupation
        if self.spouse:
            clients = (self, self.spouse,)
        else:
            clients = (self,)
        return event.HouseConstruction(subjects=clients, architect=architect, lot=lot).house

    def _purchase_home(self, home):
        """Purchase a house or apartment unit, with the help of a realtor."""
        # Try to find a realtor -- if you can't, you'll just deal directly with the person
        realtor = self.contract_person_of_certain_occupation(occupation_in_question=occupation.Realtor)
        realtor = None if not realtor else realtor.occupation
        if self.spouse:
            clients = (self, self.spouse,)
        else:
            clients = (self,)
        return event.HomePurchase(subjects=clients, home=home, realtor=realtor).home

    def _choose_vacant_home_or_vacant_lot(self):
        """Choose a vacant home to move into or a vacant lot to build on.

        Currently, a person scores all the vacant homes/lots in town and then selects
        one of the top three. TODO: Probabilistically select from all homes/lots using the
        scores to derive likelihoods of selecting each.
        """
        home_and_lot_scores = self._rate_all_vacant_homes_and_vacant_lots()
        if len(home_and_lot_scores) >= 3:
            # Pick from top three
            top_three_choices = heapq.nlargest(3, home_and_lot_scores, key=home_and_lot_scores.get)
            if random.random() < 0.6:
                choice = top_three_choices[0]
            elif random.random() < 0.9:
                choice = top_three_choices[1]
            else:
                choice = top_three_choices[2]
        elif home_and_lot_scores:
            choice = list(home_and_lot_scores)[0]
        else:
            choice = None
        return choice

    def _rate_all_vacant_homes_and_vacant_lots(self):
        """Rate all vacant homes and vacant lots."""
        scores = {}
        for home in self.city.vacant_homes:
            my_score = self.rate_potential_lot(lot=home.lot)
            if self.spouse:
                spouse_score = self.spouse.rate_potential_lot(lot=home.lot)
            else:
                spouse_score = 0
            scores[home] = my_score + spouse_score
        for lot in self.city.vacant_lots:
            my_score = self.rate_potential_lot(lot=lot)
            if self.spouse:
                spouse_score = self.spouse.rate_potential_lot(lot=lot)
            else:
                spouse_score = 0
            scores[lot] = (
                (my_score + spouse_score) * self.game.config.penalty_for_having_to_build_a_home_vs_buying_one
            )
        return scores

    def rate_potential_lot(self, lot):
        """Rate the desirability of living at the location of a lot.

        By this method, a person appraises a vacant home or lot in the city for
        how much they would like to move or build there, given considerations to the people
        that live nearby it (this reasoning via self.score_potential_home_or_lot()). There is
        a penalty that makes people less willing to build a home on a vacant lot than to move
        into a vacant home.
        """
        config = self.game.config
        pull_to_live_near_that_relation = config.pull_to_live_near_family
        pull_to_live_near_a_friend = config.pull_to_live_near_a_friend
        desire_to_live_near_family = self._determine_desire_to_move_near_family()
        # Score home for its proximity to family (either positively or negatively, depending); only
        # consider family members that are alive, in town, and not living with you already (i.e., kids)
        relatives_in_town = {f for f in self.extended_family if f.present and f.home is not self.home}
        score = 0
        for relative in relatives_in_town:
            relation_to_me = self._common_familial_relation_to_me(person=relative)
            pull_toward_someone_of_that_relation = pull_to_live_near_that_relation.get(relation_to_me, 0.0)
            dist = self.city.distance_between(relative.home.lot, lot) + 1.0  # To avoid ZeroDivisionError
            score += (desire_to_live_near_family * pull_toward_someone_of_that_relation) / dist
        # Score for proximity to friends (only positively)
        for friend in self.friends:
            dist = self.city.distance_between(friend.home.lot, lot) + 1.0
            score += pull_to_live_near_a_friend / dist
        # Score for proximity to workplace (only positively) -- will be only criterion for person
        # who is new to the city (and thus accurate_belief no one there yet)
        if self.occupation:
            dist = self.city.distance_between(self.occupation.company.lot, lot) + 1.0
            score += config.pull_to_live_near_workplace / dist
        return score

    def _determine_desire_to_move_near_family(self):
        """Decide how badly you want to move near/away from family.

        Currently, this relies on immutable personality traits, but eventually
        this desire could be made dynamic according to life events, etc.
        """
        config = self.game.config
        # People with personality C-, O+ most likely to leave home (source [1])
        base_desire_to_live_near_family = config.desire_to_live_near_family_base
        desire_to_live_near_family = self.personality.conscientiousness
        desire_to_live_away_from_family = self.personality.openness_to_experience
        final_desire_to_live_near_family = (
            base_desire_to_live_near_family + desire_to_live_near_family - desire_to_live_away_from_family
        )
        if final_desire_to_live_near_family < config.desire_to_live_near_family_floor:
            final_desire_to_live_near_family = config.desire_to_live_near_family_floor
        elif final_desire_to_live_near_family > config.desire_to_live_near_family_cap:
            final_desire_to_live_near_family = config.desire_to_live_near_family_cap
        return final_desire_to_live_near_family

    def implant_knowledge(self):
        """Implant knowledge into this person to simulate knowledge
        acquisition during the low-fidelity simulation.
        """
        # TODO INJECT KNOWLEDGE ABOUT PLACES
        all_the_people_i_should_know_about = set(self.relationships) | set(self.salience_of_other_people)
        for person in all_the_people_i_should_know_about:
            if person in self.relationships:
                total_interactions = self.relationships[person].total_interactions
            else:
                total_interactions = 0.0
            if person in self.salience_of_other_people:
                salience_of_subject = self.salience_of_other_people[person]
            else:
                salience_of_subject = 0.0
            if person in self.relationships or self.known_relation_to_me(person):
                salience_of_subject += 1.0
            implant_will_happen = False
            if person in self.immediate_family or person in self.friends or person is self:
                implant_will_happen = True
            elif salience_of_subject > 0.0:
                salience_of_subject = max(1.01, salience_of_subject)  # Needed to make the next line work
                chance_implant_even_happens = 1.0 - (1.0/salience_of_subject)
                # If the person died before I was born and is not in my immediate family,
                # alter the chance of me caring by my interest in history
                if person.death_year and person.death_year < self.birth_year and person not in self.immediate_family:
                    interest_in_history_multiplier = 1.0 + self.personality.interest_in_history
                    chance_implant_even_happens *= interest_in_history_multiplier
                if random.random() < chance_implant_even_happens:
                    implant_will_happen = True
            if self.age < 4:
                implant_will_happen = False
            if implant_will_happen:
                implant = Implant(
                    subject=person, source=self, total_interactions=total_interactions,
                    salience_of_subject=salience_of_subject
                )
                PersonMentalModel(owner=self, subject=person, observation_or_reflection=None, implant=implant)

    def reflect(self):
        """Reflect on one's own features."""
        reflection = Reflection(subject=self, source=self)
        if self not in self.mind.mental_models:
            PersonMentalModel(
                owner=self, subject=self, observation_or_reflection=reflection
            )
        else:
            self.mind.mental_models[self].build_up(new_observation_or_reflection=reflection)

    def observe(self):
        """Observe the place one is at and the people there."""
        for thing in {self.location} | self.location.people_here_now - {self}:
            if random.random() < self.game.config.chance_someone_observes_nearby_entity:
                self._form_or_build_up_mental_model(subject=thing)

    def _form_or_build_up_mental_model(self, subject):
        """Instantiate (or further fill in) a mental model of a person or place."""
        observation = Observation(subject=subject, source=self)
        if subject not in self.mind.mental_models:
            if subject.type == "person":
                PersonMentalModel(owner=self, subject=subject, observation_or_reflection=observation)
            elif subject.type == "residence":
                DwellingPlaceModel(owner=self, subject=subject, observation=observation)
            elif subject.type == "business":
                BusinessMentalModel(owner=self, subject=subject, observation=observation)
        else:
            self.mind.mental_models[subject].build_up(new_observation_or_reflection=observation)

    def socialize(self, missing_timesteps_to_account_for=1):
        """Socialize with nearby people."""
        if not self.location:
            raise Exception("{} tried to socialize, but they have no location currently.".format(self.name))
        for person in list(self.location.people_here_now):
            if self._decide_to_instigate_social_interaction(other_person=person):
                if person not in self.relationships:
                    Acquaintance(owner=self, subject=person, preceded_by=None)
                if not self.relationships[person].interacted_this_timestep:
                    # Make sure they didn't already interact this timestep
                    self.relationships[person].progress_relationship(
                        missing_days_to_account_for=missing_timesteps_to_account_for
                    )
                    # If this is being called by the full-fidelity simulation,
                    # have these two people exchange information with each other
                    if missing_timesteps_to_account_for == 1:
                        self._exchange_information(interlocutor=person)
        # Also cheat to simulate socializing between people that live together,
        # regardless of where they are truly located (otherwise have things like
        # a kid who has never met his mother, because she works the night shift)
        for person in list(self.home.residents-{self}):
            if person not in self.relationships:
                Acquaintance(owner=self, subject=person, preceded_by=None)
            if not self.relationships[person].interacted_this_timestep:
                # Make sure they didn't already interact this timestep
                self.relationships[person].progress_relationship(
                    missing_days_to_account_for=missing_timesteps_to_account_for
                )
                # If this is being called by the full-fidelity simulation,
                # have these two people exchange information with each other
                if missing_timesteps_to_account_for == 1:
                    self._exchange_information(interlocutor=person)

    def _exchange_information(self, interlocutor):
        config = self.game.config
        # Decide how many people they'll talk about -- this depends on both parties'
        # extroversion personality components and how good of friends they are
        how_many_people_we_talk_about = int(
            self.personality.extroversion +
            interlocutor.personality.extroversion +
            2 if interlocutor in self.friends else 0 +
            2 if self in interlocutor.friends else 0 +
            1 if interlocutor is self.best_friend else 0 +
            1 if self is interlocutor.best_friend else 0
        )
        if how_many_people_we_talk_about < config.amount_of_people_people_talk_about_floor:
            how_many_people_we_talk_about = config.amount_of_people_people_talk_about_floor
        # Figure out the N most salient people, where N = how_many_people_we_talk_about (or
        # the how many total people these guys know about, if that's less)
        all_the_people_we_know_about = set(self.mind.mental_models) | set(interlocutor.mind.mental_models)
        my_salience_of_other_people = self.salience_of_other_people  # Attribute accessing is slow -- make local vars
        interlocutor_salience_of_other_people = interlocutor.salience_of_other_people
        salience_scores = {
            # Using .get(entity, 0.0) means 0.0 will be returned if entity is not in that dictionary -- i.e.,
            # it creates a default salience value of 0.0 for cases where a person has no salience value for someone
            entity: my_salience_of_other_people.get(entity, 0.0)+interlocutor_salience_of_other_people.get(entity, 0.0)
            for entity in all_the_people_we_know_about if entity.type == "person"
        }
        people_we_will_talk_about = (
            heapq.nlargest(how_many_people_we_talk_about, salience_scores, key=salience_scores.get)
        )
        for subject_of_conversation in people_we_will_talk_about:
            self._exchange_information_about_a_person(
                interlocutor=interlocutor,
                person_in_question=subject_of_conversation,
                total_salience_of_that_person=salience_scores[subject_of_conversation]
            )

    def _exchange_information_about_a_person(self, interlocutor, person_in_question, total_salience_of_that_person):
        """Exchange information about a person."""
        # TODO HAVE SALIENCE OF THIS PERSON TO THE TALKERS AFFECT HOW MUCH THEY SAY ABOUT THEM
        config = self.game.config
        if person_in_question not in self.mind.mental_models:
            PersonMentalModel(owner=self, subject=person_in_question, observation_or_reflection=None)
        if person_in_question not in interlocutor.mind.mental_models:
            PersonMentalModel(owner=interlocutor, subject=person_in_question, observation_or_reflection=None)
        for me_or_interlocutor in (self, interlocutor):
            talker = me_or_interlocutor
            listener = self if talker is not self else interlocutor
            statement = Statement(subject=person_in_question, source=talker, recipient=listener)
            declaration = Declaration(subject=person_in_question, source=talker, recipient=listener)
            # Potentially have someone eavesdrop -- TODO maybe affect this by whether eavesdropper accurate_belief subject
            people_in_earshot = self.location.people_here_now - {talker, listener}
            eavesdropper = None if not people_in_earshot else random.choice(list(people_in_earshot))
            if eavesdropper and random.random() < config.chance_someone_eavesdrops_statement_or_lie:
                eavesdropping = Eavesdropping(
                    subject=person_in_question, source=talker, recipient=listener, eavesdropper=eavesdropper
                )
                if person_in_question not in eavesdropper.mind.mental_models:
                    PersonMentalModel(owner=eavesdropper, subject=person_in_question, observation_or_reflection=None)
            else:
                eavesdropping = None
            for feature_type, prob in config.chance_someones_feature_comes_up_in_conversation_about_them:
                if random.random() < prob:
                    # Have talker convey information about feature_type of person_in_question
                    if talker.get_knowledge_about_person(other_person=person_in_question, feature_type=feature_type):
                        talker_belief_facet = (
                            talker.mind.mental_models[person_in_question].get_facet_to_this_belief_of_type(
                                feature_type=feature_type
                            )
                        )
                        # Have the listener consider the new evidence
                        listener.mind.mental_models[person_in_question].consider_new_evidence(
                            feature_type=feature_type, feature_value=str(talker_belief_facet),
                            feature_object_itself=talker_belief_facet.object_itself, new_evidence=statement
                        )
                        # Have the talker reinforce their own belief by virtue of having just conveyed it
                        talker.mind.mental_models[person_in_question].consider_new_evidence(
                            feature_type=feature_type, feature_value=str(talker_belief_facet),
                            feature_object_itself=talker_belief_facet.object_itself, new_evidence=declaration
                        )
                        # If someone is eavesdropping, have them consider the new evidence
                        if eavesdropping:
                            eavesdropper.mind.mental_models[person_in_question].consider_new_evidence(
                                feature_type=feature_type, feature_value=str(talker_belief_facet),
                                feature_object_itself=talker_belief_facet.object_itself, new_evidence=eavesdropping
                            )

    def _decide_to_instigate_social_interaction(self, other_person):
        """Decide whether to instigate a social interaction with another person."""
        config = self.game.config
        if other_person is self or other_person.age < 5:
            chance = 0.0
        else:
            extroversion_component = self._get_extroversion_component_to_chance_of_social_interaction()
            # If this person accurate_belief other_person, we look at their relationship to determine
            # how its strength will factor into the decision; if they don't know this person,
            # we then factor in this person's openness to experience instead
            if other_person not in self.relationships:
                friendship_or_openness_component = self._get_openness_component_to_chance_of_social_interaction()
            else:
                friendship_or_openness_component = self._get_friendship_component_to_chance_of_social_interaction(
                    other_person=other_person
                )
            chance = extroversion_component + friendship_or_openness_component
            if chance < config.chance_someone_instigates_interaction_with_other_person_floor:
                chance = config.chance_someone_instigates_interaction_with_other_person_floor
            elif chance > config.chance_someone_instigates_interaction_with_other_person_cap:
                chance = config.chance_someone_instigates_interaction_with_other_person_cap
        if random.random() < chance:
            return True
        else:
            return False

    def _get_extroversion_component_to_chance_of_social_interaction(self):
        """Return the effect of this person's extroversion on the chance of instigating social interaction."""
        config = self.game.config
        extroversion_component = self.personality.extroversion
        if extroversion_component < config.chance_of_interaction_extroversion_component_floor:
            extroversion_component = config.chance_of_interaction_extroversion_component_floor
        elif extroversion_component > config.chance_of_interaction_extroversion_component_cap:
            extroversion_component = config.chance_of_interaction_extroversion_component_cap
        return extroversion_component

    def _get_openness_component_to_chance_of_social_interaction(self):
        """Return the effect of this person's openness on the chance of instigating social interaction."""
        config = self.game.config
        openness_component = self.personality.openness_to_experience
        if openness_component < config.chance_of_interaction_openness_component_floor:
            openness_component = config.chance_of_interaction_openness_component_floor
        elif openness_component > config.chance_of_interaction_openness_component_cap:
            openness_component = config.chance_of_interaction_openness_component_cap
        return openness_component

    def _get_friendship_component_to_chance_of_social_interaction(self, other_person):
        """Return the effect of an existing friendship on the chance of instigating social interaction."""
        config = self.game.config
        friendship_component = 0.0
        if other_person in self.friends:
            friendship_component += config.chance_of_interaction_friendship_component
        if other_person is self.best_friend:
            friendship_component += config.chance_of_interaction_best_friend_component
        return friendship_component

    def grow_older(self):
        """Check if it's this persons birth day; if it is, age them."""
        config = self.game.config
        consider_leaving_town = False
        self.age = age = self.game.true_year - self.birth_year
        if age == config.age_people_start_working(year=self.game.year):
            self.ready_to_work = True
            consider_leaving_town = True
        if age == 18:
            self.adult = True
        # If you haven't in a while (in the logarithmic sense, rather than absolute
        # sense), update all relationships you have to reflect the new age difference
        # between you and the respective other person
        if age in (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18,
            20, 23, 26, 29, 33, 37, 41, 45, 50, 55, 60,
            65, 70, 75, 80, 85, 90, 95, 100
        ):
            for other_person in self.relationships:
                self.relationships[other_person].update_spark_and_charge_increments_for_new_age_difference()
        # Potentially have your hair turn gray (or white, if it's already gray) -- TODO MAKE THIS HERITABLE
        if age > config.age_when_people_start_graying:
            if random.random() < config.chance_someones_hair_goes_gray_or_white:
                new_color_str = 'gray' if self.face.hair.color != 'gray' else 'white'
                # Maintain the same face.Feature attributes as the original Feature had, but
                # create a new Feature object with the updated string -- TODO is this still inheritance?
                variant_id = self.face.hair.color.variant_id
                inherited_from = self.face.hair.color.inherited_from
                exact_variant_inherited = self.face.hair.color.exact_variant_inherited
                self.face.hair.color = face.Feature(
                    value=new_color_str, variant_id=variant_id, inherited_from=inherited_from,
                    exact_variant_inherited=exact_variant_inherited
                )
        # Potentially go bald, if male -- TODO MAKE THIS HERITABLE
        if self.male and age > config.age_when_men_start_balding:
            if random.random() < config.chance_someones_loses_their_hair_some_year:
                # Maintain the same face.Feature attributes as the original Feature had, but
                # create a new Feature object with the updated string -- TODO is this still inheritance?
                variant_id = self.face.hair.length.variant_id
                inherited_from = self.face.hair.length.inherited_from
                exact_variant_inherited = self.face.hair.length.exact_variant_inherited
                self.face.hair.length = face.Feature(
                    value='bald', variant_id=variant_id, inherited_from=inherited_from,
                    exact_variant_inherited=exact_variant_inherited
                )
        if consider_leaving_town and random.random() < config.chance_a_new_adult_decides_to_leave_town:
            self.depart_city()

    def update_salience_of(self, entity, change):
        """Increment your salience value for entity by change."""
        # TODO EXPLORE WHY SOME PEOPLE ARE INDEXING OTHERS WITH
        # NEGATIVE SALIENCE VALUES -- the max() is duct tape right now
        self.salience_of_other_people[entity] = (
            max(0.0, self.salience_of_other_people.get(entity, 0.0) + change)
        )

    def people_i_believe_work_at(self, company):
        """Return a list of people, ordered by their salience, that this person believes works at the given company."""
        if company not in self.mind.mental_models:
            return []
        else:
            people_i_believe_work_at_this_company = [
                mental_model.subject for mental_model in self.mind.mental_models[company].employees
            ]
            people_i_believe_work_at_this_company.sort(
                key=lambda p: self.salience_of_other_people.get(p, 0.0), reverse=True
            )
            return people_i_believe_work_at_this_company

    def most_salient_person_i_believe_works_at(self, company):
        """Return the single most salient person that this person believes works at the given company."""
        people_i_believe_work_at_this_company = self.people_i_believe_work_at(company=company)
        if people_i_believe_work_at_this_company:
            return people_i_believe_work_at_this_company[0]
        else:
            return None

    def people_i_believe_are_named(self, first_name=None, last_name=None, sex=None):
        """Return a list of people who this person believes have features with the given values."""
        matches = [p for p in self.mind.mental_models if p.subject.type == 'person']
        if first_name:
            matches = [p for p in matches if self.belief(p, 'first name') == first_name]
        if last_name:
            matches = [p for p in matches if self.belief(p, 'last name') == last_name]
        if sex:
            if sex == 'm':
                matches = [p for p in matches if p.male]
            elif sex == 'f':
                matches = [p for p in matches if p.female]
        return matches

    def connection_to_place(self):
        pass

    def connection_to_person(self):
        pass


class PersonExNihilo(Person):
    """A person who is generated from nothing, i.e., who has no parents.

    This is a subclass of Person whose objects are people that enter the simulation
    from outside the city, either as city founders or as new hires for open positions
    that could not be filled by anyone currently in the city. Because these people don't
    have parents, a subclass is needed to override any attributes or methods that rely
    on inheritance. Additionally, a family (i.e., a PersonExNihilo spouse and possibly Person
    children) may be generated for a person of this class.
    """

    def __init__(self, game, job_opportunity_impetus, spouse_already_generated):
        super(PersonExNihilo, self).__init__(game, birth=None)
        # Potentially overwrite sex set by Person.__init__()
        if spouse_already_generated:
            self.male, self.female = self._override_sex(spouse=spouse_already_generated)
            self.attracted_to_men, self.attracted_to_women = self._override_sexuality(spouse=spouse_already_generated)
        elif job_opportunity_impetus:
            # Make sure you have the appropriate sex for the job position you are coming
            # to town to accept; if you don't, swap your sex and
            if not self.game.config.employable_as_a[job_opportunity_impetus](applicant=self):
                self.male, self.female = self.female, self.male
                self.attracted_to_men, self.attracted_to_women = (False, True) if self.male else (True, False)
        # Overwrite birth year set by Person.__init__()
        job_level = self.game.config.job_levels[job_opportunity_impetus]
        self.birth_year = self._init_birth_year(job_level=job_level)
        # Set age given birth year that was attributed
        self.age = self.game.true_year - self.birth_year
        if self.age >= 18:
            self.adult = True
        # Determine a random birthday and add it to the game's listing of all characters' birthdays
        self.birthday = self._get_random_birthday()
        try:
            game.birthdays[self.birthday].add(self)
        except KeyError:
            game.birthdays[self.birthday] = {self}
        # Since they don't have a parent to name them, generate a name for this person (if
        # they get married outside the city, this will still potentially change, as normal)
        self.first_name, self.middle_name, self.last_name, self.suffix = (
            self._init_name()
        )
        self.maiden_name = self.last_name
        self.named_for = None
        # If this person is being hired for a high job level, retcon that they have
        # a college education -- do the same for the city founder
        if (job_opportunity_impetus and
                job_opportunity_impetus in self.game.config.occupations_requiring_college_degree):
            self.college_graduate = True
        # Potentially generate and retcon a family that this person will have had prior
        # to moving into the city; if the person is moving here to be a farmer, force that
        # a family be retconned (mostly to ensure that at least some people in the present
        # day will have roots in the town going back to its early foundations when it
        # comprised a handful of farms)
        self._init_potentially_retcon_family(
            spouse_already_generated=spouse_already_generated,
            job_opportunity_impetus=job_opportunity_impetus
        )

    def _get_random_birthday(self):
        """Return a randomly chosen birthday.

        Note: In a rare example of me not oversimulating, this method wrongly assumes a
        uniform distribution of birthdays and will never return a February 29 birthday
        (due to the attendant trouble of having to then make sure the person was indeed
        born on a leap year).
        """
        month, day, _ = self.game.get_random_day_of_year(year=self.birth_year)
        birthday = (month, day)
        return birthday

    @staticmethod
    def _override_sex(spouse):
        """Assign the sex of this person to ensure compatibility with their spouse.."""
        if spouse.attracted_to_men:
            male, female = True, False
        else:
            male, female = False, True
        return male, female

    @staticmethod
    def _override_sexuality(spouse):
        """Assign the sex of this person to ensure compatibility with their spouse.."""
        if spouse.male:
            attracted_to_men, attracted_to_women = True, False
        else:
            attracted_to_men, attracted_to_women = False, True
        return attracted_to_men, attracted_to_women

    def _init_name(self):
        """Generate a name for a primordial person who has no parents."""
        if self.male:
            first_name_rep = Names.a_masculine_name(year=self.birth_year)
            middle_name_rep = Names.a_masculine_name(year=self.birth_year)
        else:
            first_name_rep = Names.a_feminine_name(year=self.birth_year)
            middle_name_rep = Names.a_feminine_name(year=self.birth_year)
        first_name = Name(value=first_name_rep, progenitor=self, conceived_by=(), derived_from=())
        middle_name = Name(value=middle_name_rep, progenitor=self, conceived_by=(), derived_from=())
        last_name = Name(value=Names.any_surname(), progenitor=self, conceived_by=(), derived_from=())
        suffix = ''
        return first_name, middle_name, last_name, suffix

    def _init_birth_year_of_the_founder(self):
        """Generate a birth year for the founder of the city."""
        config = self.game.config
        age_at_current_year_of_sim = config.age_of_city_founder
        birth_year = self.game.true_year - age_at_current_year_of_sim
        return birth_year

    def _init_birth_year(self, job_level):
        """Generate a birth year for this person that is consistent with the job level they/spouse will get."""
        config = self.game.config
        age_at_current_year_of_sim = config.function_to_determine_person_ex_nihilo_age_given_job_level(
            job_level=job_level
        )
        birth_year = self.game.true_year - age_at_current_year_of_sim
        return birth_year

    def _init_familial_attributes(self):
        """Do nothing because a PersonExNihilo has no family at the time of being generated.."""
        pass

    def _init_update_familial_attributes_of_family_members(self):
        """Do nothing because a PersonExNihilo has no family at the time of being generated.."""
        pass

    def _init_money(self):
        """Determine how much money this person has to start with."""
        return self.game.config.amount_of_money_generated_people_from_outside_city_start_with

    def _init_potentially_retcon_family(self, spouse_already_generated, job_opportunity_impetus):
        """Potentially generate and retcon a family that this person will have had prior
        to entering into the simulation.
        """
        if not spouse_already_generated:
            chance_of_having_family = (
                self.game.config.function_to_determine_chance_person_ex_nihilo_starts_with_family(
                    city_pop=self.game.city.population
                )
            )
            if random.random() < chance_of_having_family or job_opportunity_impetus.__name__ == 'Farmer':
                self._init_generate_family(job_opportunity_impetus=job_opportunity_impetus)

    def _init_generate_family(self, job_opportunity_impetus):
        """Generate and retcon a family that this person will take with them into the city."""
        spouse = PersonExNihilo(
            game=self.game, job_opportunity_impetus=job_opportunity_impetus, spouse_already_generated=self
        )
        self._init_retcon_marriage(spouse=spouse)
        self._init_retcon_births_of_children()
        self.game.year = self.game.true_year

    def _init_retcon_marriage(self, spouse):
        """Jump back in time to instantiate a marriage that began outside the city."""
        config = self.game.config
        # Change actual game year to marriage year, instantiate a Marriage object
        marriage_date = self.birth_year + (
            random.normalvariate(
                config.person_ex_nihilo_age_at_marriage_mean, config.person_ex_nihilo_age_at_marriage_sd
            )
        )
        if (
            # Make sure spouses aren't too young for marriage and that marriage isn't slated
            # to happen after the city has been founded
            marriage_date - self.birth_year < config.person_ex_nihilo_age_at_marriage_floor or
            marriage_date - spouse.birth_year < config.person_ex_nihilo_age_at_marriage_floor or
            marriage_date >= self.game.true_year
        ):
            # If so, don't bother regenerating -- just set marriage year to last year and move on
            marriage_date = self.game.true_year - 1
        self.game.year = int(round(marriage_date))
        self.marry(spouse)

    def _init_retcon_births_of_children(self):
        """Simulate from marriage to the present day for children potentially being born."""
        config = self.game.config
        # Simulate sex (and thus potentially birth) in marriage thus far
        for year in xrange(self.marriage.year, self.game.true_year+1):
            # If someone is pregnant and due this year, have them give birth
            if self.pregnant or self.spouse.pregnant:
                pregnant_one = self if self.pregnant else self.spouse
                if pregnant_one.conception_year < year:
                    pregnant_one.give_birth()
            self.game.year = year
            chance_they_are_trying_to_conceive_this_year = (
                config.function_to_determine_chance_married_couple_are_trying_to_conceive(
                    n_kids=len(self.marriage.children_produced)
                )
            )
            if random.random() < chance_they_are_trying_to_conceive_this_year:
                self.have_sex(partner=self.spouse, protection=False)
            else:
                self.have_sex(partner=self.spouse, protection=True)

    def move_into_the_city(self, hiring_that_instigated_move):
        """Move into the city in which gameplay takes place."""
        self.city = self.game.city
        self.city.residents.add(self)
        new_home = self.secure_home()
        if not new_home:
            someone_elses_home = random.choice(list(self.city.dwelling_places))
            self.move(new_home=someone_elses_home, reason=hiring_that_instigated_move)
        if new_home:
            self.move(new_home=new_home, reason=hiring_that_instigated_move)
        else:
            # Have the closest apartment complex to downtown expand to add
            # another unit for this person to move into
            apartment_complexes_in_town = [
                # Check if they have units first -- have had the weird case of someone
                # trying to build a complex right downtown and then not being able to
                # expand that very complex itself to move into it, because it currently
                # has no units, and thus no unit number to give the expansion unit
                ac for ac in self.city.businesses_of_type('ApartmentComplex') if ac.units
            ]
            if len(apartment_complexes_in_town) > 3:
                complexes_closest_to_downtown = heapq.nlargest(
                    3, apartment_complexes_in_town,
                    key=lambda ac: self.city.distance_between(ac.lot, self.city.downtown)
                )
                complex_that_will_expand = random.choice(complexes_closest_to_downtown)
            else:
                complex_that_will_expand = min(
                    apartment_complexes_in_town,
                    key=lambda ac: self.city.distance_between(ac.lot, self.city.downtown)
                )
            complex_that_will_expand.expand()  # This will add two new units to this complex
            self.move(
                new_home=complex_that_will_expand.units[-2],
                reason=hiring_that_instigated_move
            )