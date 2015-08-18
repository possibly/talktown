class PieceOfEvidence(object):
    """A superclass that all evidence subclasses inherit from."""

    def __init__(self, subject, source):
        """Initialize a PieceOfEvidence object."""
        self.type = self.__class__.__name__.lower()
        self.location = source.location
        self.time = source.game.date
        self.ordinal_date = source.game.ordinal_date
        # Also request and attribute an event number, so that we can later
        # determine the precise ordering of events that happen on the same timestep
        self.event_number = source.game.assign_event_number()
        self.subject = subject
        self.source = source
        self.recipient = None  # Will get overwritten in case of Lie, Statement, Declaration, Eavesdropping
        self.eavesdropper = None  # Will get overwritten in case of Eavesdropping
        self.attribute_transferred = None  # Will get overwritten in case of Transference
        self.beliefs_evidenced = set()  # Gets added to by Belief.Facet.__init__()
        # Adjusted strength gets set by Belief.Facet.adjust_strength_of_forgotten_evidence() when
        # a piece of evidence is forgotten, or more precisely, is supplanted by a piece of evidence
        # with a deterioration type. It's used to adjust the strength of the total evidence of a
        # forgotten belief facet so that its strength is equal to the strength of the new Facet supported
        # by some kind of deterioration. This allows a character to temporarily forget something but
        # later, upon encountering new evidence supporting the forgotten belief, remember that they had
        # previously believed it and then reinstate it again.
        self.adjusted_strength = None

    def __str__(self):
        """Return string representation."""
        location_and_time = "at {} on the {}".format(
            self.location.name, self.time[0].lower()+self.time[1:]
        )
        if self.type == 'eavesdropping':
            return "{}'s eavesdropping of {}'s statement to {} about {} {}".format(
                self.eavesdropper.name, self.source.name, self.recipient.name,
                self.subject.name, location_and_time
            )
        elif self.type == 'statement':
            return "{}'s statement to {} about {} {}".format(
                self.source.name, self.recipient.name, self.subject.name,
                location_and_time
            )
        elif self.type == 'declaration':
            return "{}'s own statement (declaration) to {} about {} {}".format(
                self.source.name, self.recipient.name, self.subject.name,
                location_and_time
            )
        elif self.type == 'lie':
            return "{}'s lie to {} about {} {}".format(
                self.source.name, self.recipient.name, self.subject.name,
                location_and_time
            )
        elif self.type == 'reflection':
            return "{}'s reflection about {} {}".format(
                self.subject.name, self.subject.reflexive, location_and_time
            )
        elif self.type == 'observation':
            return "{}'s observation of {} {}".format(
                self.source.name, self.subject.name, location_and_time
            )
        elif self.type == 'confabulation':
            return "{}'s confabulation about {} {}".format(
                self.source.name, self.subject.name, location_and_time
            )
        elif self.type == 'mutation':
            return "{}'s mutation of {} mental model of {} {}".format(
                self.source.name, self.source.possessive, self.subject.name, location_and_time
            )
        elif self.type == 'transference':
            return "{}'s transference from {} mental model of {} to {} mental model of {} {}".format(
                self.source.name, self.source.possessive, self.attribute_transferred.subject.name,
                self.source.possessive, self.subject.name, location_and_time
            )
        elif self.type == 'forgetting':
            return "{}'s forgetting of knowledge about {} {}".format(
                self.source.name, self.subject.name, location_and_time
            )


class Reflection(PieceOfEvidence):
    """A reflection by which one person perceives something about themself."""

    def __init__(self, subject, source):
        """Initialize a Reflection object."""
        super(Reflection, self).__init__(subject=subject, source=source)
        assert subject is source, "{} attempted to reflect about {}, who is not themself.".format(
            source.name, subject.name
        )


class Observation(PieceOfEvidence):
    """An observation by which one person perceives something about another person."""

    def __init__(self, subject, source):
        """Initialize an Observation object."""
        super(Observation, self).__init__(subject=subject, source=source)
        if subject.type == 'person':
            assert source.location is subject.location, (
                "{} attempted to observe {}, who is in a different location.".format(
                    source.name, subject.name
                )
            )
        else:  # Subject is home or business
            assert source.location is subject, (
                "{} attempted to observe {}, but they are not located there.".format(
                    source.name, subject.name
                )
            )


class Confabulation(PieceOfEvidence):
    """A confabulation by which a person unintentionally concocts new false knowledge (i.e., changes an
    attribute's value from None to something).

    Note: There is only two ways a confabulation can happen: when a person modifies a mental model of
    a person they have never met (i.e., they hear things about this person from someone,
    but then concoct other things about this person that no one told them), or when they confabulate
    a new value for an attribute whose true value they had forgotten.
    """

    def __init__(self, subject, source):
        """Initialize a Confabulation object."""
        super(Confabulation, self).__init__(subject=subject, source=source)


class Lie(PieceOfEvidence):
    """A lie by which one person invents and conveys knowledge about someone that they know is false."""

    def __init__(self, subject, source, recipient):
        """Initialize a Lie object."""
        super(Lie, self).__init__(subject=subject, source=source)
        self.recipient = recipient
        # This dictionary maps feature types that come up during a lie to
        # the teller's perceived strength of belief, at time of the lie,
        # i.e., how strongly they sold the lie
        self.teller_belief_strength = {}


class Statement(PieceOfEvidence):
    """A statement by which one person conveys knowledge about someone that they believe is true."""

    def __init__(self, subject, source, recipient):
        """Initialize a Statement object."""
        super(Statement, self).__init__(subject=subject, source=source)
        self.recipient = recipient
        # This dictionary maps feature types that come up during a statement to the teller's
        # strength of belief, at time of the statement, regarding that feature type
        self.teller_belief_strength = {}


class Declaration(PieceOfEvidence):
    """A declaration by which one person delivers a statement and comes to believe its information even more.

    See source [6] for evidence that this is realistic.
    """

    def __init__(self, subject, source, recipient):
        """Initialize a Declaration object."""
        super(Declaration, self).__init__(subject=subject, source=source)
        self.recipient = recipient


class Eavesdropping(PieceOfEvidence):
    """An eavesdropping by which one person overhears the information being conveyed by a statement or lie."""

    def __init__(self, subject, source, recipient, eavesdropper):
        """Initialize an Eavesdropping object."""
        super(Eavesdropping, self).__init__(subject=subject, source=source)
        self.recipient = recipient
        self.eavesdropper = eavesdropper
        # This dictionary maps feature types that come up during a statement to the teller's
        # strength of belief, at time of the statement, regarding that feature type
        self.teller_belief_strength = {}


class Mutation(PieceOfEvidence):
    """A mutation by which a person misremembers knowledge from time passing (i.e., changes an attribute's value)."""

    def __init__(self, subject, source, mutated_belief_str):
        """Initialize a Mutation object."""
        super(Mutation, self).__init__(subject=subject, source=source)
        self.mutated_belief_str = mutated_belief_str


class Transference(PieceOfEvidence):
    """A transference by which a person unintentionally transposes another person's attribute onto their model
    of someone else."""

    def __init__(self, subject, source, belief_facet_transferred_from):
        """Initialize a Transference object.

        @param subject: The person to whom this knowledge pertains.
        @param source: The person doing the transference.
        @param belief_facet_transferred_from: The believed attribute of *another* person that mistakenly
                                      gets transferred as a believed attribute about subject.
        """
        super(Transference, self).__init__(subject=subject, source=source)
        self.attribute_transferred = belief_facet_transferred_from


class Forgetting(PieceOfEvidence):
    """A forgetting by which a person forgets knowledge.

    A forgetting represents an ultimate terminus of a particular information item -- they
    should only be attributed as evidence to Belief.Facets that are represented as an empty
    string.
    """

    def __init__(self, subject, source):
        """Initialize a Forgetting object.

        @param subject: The person to whom this knowledge pertains.
        @param source: The person doing the forgetting.
        """
        super(Forgetting, self).__init__(subject=subject, source=source)