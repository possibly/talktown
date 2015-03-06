import random


class DwellingPlace(object):
    """A dwelling place in a city."""
    counter = 0
    def __init__(self, lot, owners):
        """Initialize a DwellingPlace object.

        @param lot: A Lot object representing the lot this building is on.
        """
        self.id = DwellingPlace.counter
        DwellingPlace.counter += 1
        self.type = "residence"
        self.city = lot.city
        self.city.dwelling_places.add(self)
        self.lot = lot
        if self.house:
            self.address = self.lot.address
        elif self.apartment:
            self.address = ""  # Gets set by Apartment._init_generate_address()
        self.residents = set()
        self.former_residents = set()
        self.transactions = []
        self.move_ins = []
        self.move_outs = []
        self.owners = set()  # Gets set via self._init_ownership()
        self.former_owners = set()
        self._init_ownership(initial_owners=owners)
        self.people_here_now = set()  # People at home on a specific time step (either a resident or visitor)

    def __str__(self):
        """Return string representation."""
        return "{0}, {1}".format(self.name, self.address)

    @property
    def name(self):
        """Return the name of this residence."""
        owner_surnames = set([o.last_name for o in self.owners])
        name = "{0} Residence".format('-'.join(owner_surnames))
        return name

    def _init_ownership(self, initial_owners):
        """Set the initial owners of this dwelling place."""
        # I'm doing this klugey thing for now because of circular-dependency issue
        list(initial_owners)[0].purchase_home(purchasers=initial_owners, home=self)
        # HomePurchase(subjects=initial_owners, home=self, realtor=None)

    def get_feature(self, feature_type):
        """Return this person's feature of the given type."""
        features = {
            "home is apartment": "yes" if self.apartment else "no",
            "home block": str(self.lot.block_address_is_on),
            "home address": self.address,
        }
        return features[feature_type]


class Apartment(DwellingPlace):
    """An individual apartment unit in an apartment building in a city."""

    def __init__(self, apartment_complex, lot, unit_number):
        self.apartment, self.house = True, False
        self.complex = apartment_complex
        self.unit_number = unit_number
        super(Apartment, self).__init__(lot, owners=(apartment_complex.owner.person,))
        self.address = self._init_generate_address()

    def _init_generate_address(self):
        """Generate an address, given the lot building is on."""
        return "{0} (Unit #{1})".format(self.lot.address, self.unit_number)


class House(DwellingPlace):
    """A house in a city.

    @param lot: A Lot object representing the lot this building is on.
    @param construction: A BusinessConstruction object holding data about
                         the construction of this building.
    """

    def __init__(self, lot, construction):
        self.apartment, self.house = False, True
        super(House, self).__init__(lot, owners=construction.subjects)
        self.construction = construction
        self.lot.building = self
        self.city.houses.add(self)