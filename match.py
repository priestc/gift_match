from __future__ import print_function
from collections import defaultdict

class TubeSet(object):
    """
    Class for mixing items from a set into a one dimentional list so that no two
    objects of the same type are next to each other.
    
    in: set('aaaaaXXXX')
    out: ['a', 'X', 'a', 'X', 'a', 'X', 'a', 'X', 'a']
    (no a's are next to each other, no x's are next to each other...)
    
    """
    def __init__(self, set_of_items):
        self.length_of_total = len(set_of_items)
        self.tubes = defaultdict(lambda: [])
        self.output = []
        for item in set_of_items:
            key = self.differentiator(item)
            self.tubes[key].append(item)
    
    def pop_rejects(self):
        """
        Remove all rejects from the tubes. a 'reject' is someone who is part of
        a group that represents more than half of the total objects.
        """
        largest_tube_key = self.get_tube_key(highest=True)
        largest_tube = self.tubes[largest_tube_key]
        largest_tube_length = len(largest_tube)
        
        others = self.length_of_total - largest_tube_length
        number_of_rejects = largest_tube_length - (others + 1)

        if number_of_rejects > 0:
            # there will be rejects if any one tube makes up for more than half
            # of all items
            rejects = []
            for i in xrange(number_of_rejects):
                reject = largest_tube.pop()
                rejects.append(reject)
            return rejects
        
        return [] # no rejects
        
    def differentiator(self, obj):
        # must be defined in a subclass
        raise NotImplementedError
    
    def tubes_are_filled(self):
        """
        Returns whether there are still items in any tube.
        """
        for tube in self.tubes.iteritems():
            if len(tube) > 0:
                return True
        return False
    
    def remove_empty_tubes(self):
        new_tubes = {}
        for key, tube in self.tubes.iteritems():
            if not len(tube) == 0:
                new_tubes[key] = tube
        
        self.tubes = new_tubes
    
    def get_tube_key(self, highest=True):
        """
        Looks at all tubes, and returns either the the key of the tube with the
        most items, -OR- a tube key that is NOT the highest.
        (depending on the 'highest' kwarg)
        """
        tube_lens = {}
        for key, tube in self.tubes.iteritems():
            length = len(tube)
            tube_lens[key] = length

        highest_key = max(tube_lens, key=lambda x: tube_lens[x])

        if highest:
            return highest_key
        else:
            non_highest = set(tube_lens.keys()) - set(highest_key)
            return non_highest.pop()
    
    def _pop_from(self, highest):
        if highest:
            highest = self.get_tube_key(highest=True)
            return self.tubes[highest].pop()
        else:
            any_tube = self.get_tube_key(highest=False)
            return self.tubes[any_tube].pop()
    
    def pop(self):
        if not self.output:
            previous_highest = False
        else:
            previous = self.output[-1]
            previous_key = self.differentiator(previous)
            previous_highest = previous_key == self.get_tube_key()
        
        return self._pop_from(highest=not previous_highest)
    
    def get_output(self):
        rejects = self.pop_rejects()
        while self.tubes_are_filled():
            item = self.pop()
            self.remove_empty_tubes()
            self.output.append(item)        
        return {'rejects': rejects, 'sorted': self.output}

class CountryTubeSet(TubeSet):
    def differentiator(self, obj):
        return obj.country

class User(object):
    def __init__(self, id, country, international):
        self.id = id
        self.country = country
        self.international = international
        self.is_reject = False

    def set_reject(self):
        self.is_reject = True

    def __repr__(self):
        r = ''
        if self.is_reject:
            r = ' (REJECT)'
        return "%s %s %s%s" % (self.id, self.letter(), self.country, r)

    def letter(self):
        if self.international:
            return 'I'
        return 'D'

class GiftLink(object):
    """
    Represents a link between two users where a gift flows.
    """
    
    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2
    
    def as_list(self):
        return '[%s -> %s]' % (self.user1.__repr__(), self.user2.__repr__())
        
class Circle(object):
    """
    Represents a group of people in a circle. The circle will be 'rotated' which
    will match people up with other people to send gifts to.
    """
    
    def add_to_circle(self, users):
        """
        Adds a list of users tot he circle.
        """
        self.userlist.extend(users)
    
    def rotate(self):
        """
        Match each item in the list with the item next to it:
        
        [a, b, c, d, e, f] -> [ab, bc, cd, de, ef, fa]
        
        """
        if not self.userlist:
            return []
        giftlinks = []
        prev_user = first_user = self.userlist.pop()
        
        for user in self.userlist:
            gl = GiftLink(prev_user, user)
            giftlinks.append(gl)
            prev_user = user
        
        last_link = GiftLink(prev_user, first_user)
        giftlinks.append(last_link)
        
        return giftlinks

class DomesticCircle(Circle):
    def __init__(self, country, userlist):
        self.country = country
        # automatically filter by the country being represented.
        self.userlist = [user for user in userlist if user.country == country]
    
    def get_rejects(self):
        rejects = []
        if len(self.userlist) == 1:
            # if there is only one user in the circle, the circle is invalid
            # and its only user is considered a reject.
            rejects = self.userlist
            [user.set_reject() for user in rejects]
            self.userlist = []
        return rejects
    
    def __repr__(self):
        return "<Domestic Circle: %s (%s users)>" % (self.country, len(self.userlist))
    
class InternationalCircle(Circle):
    def __init__(self, userlist):
        """
        Construct the userlist by sorting the list of users in the circle so that
        no users of the same country are next to each other.
        """

        result = CountryTubeSet(userlist).get_output()
        self.userlist = result['sorted']
        self.rejects = result['rejects']

    def get_rejects(self):
        """
        Find all the rejects of this circle, and return them. We also set the
        is_reject attribute of the user object before we send them off.
        """
        rejects = []
        if len(self.userlist) == 1:
            # if there is only one user in the circle, the circle is invalid
            # and its only user is considered a reject.
            rejects = self.userlist
            self.userlist = []
        
        if self.rejects:
            # output from the TubeSort algorithm called in __init__
            rejects = self.rejects
        
        [user.set_reject() for user in rejects]
        return rejects

    def __repr__(self):
        return "<International Circle: (%s users)>" % len(self.userlist)

def add_international_rejects_to_domestic_circle(rejects, domestic_circles):
    """
    Given a group of international rejects (users who want to match up with other
    international users, but can't because they belong to a country that makes up
    more than 50% of total international circle users)

    Add these users to the domestic appropriate circle.
    """
    # the country where all international rejects come from
    reject_country = rejects[0].country

    found = False
    for circle in domestic_circles:
        # go through each domestic circle, until we find the right one, and
        # add all users to that circle.
        if circle.country == reject_country:
            circle.add_to_circle(rejects)
            found = True

    if not found:
        # for some reason, a domestic circle does not exist for the international
        # rejects, create one.
        circle = DomesticCircle(reject_country, rejects)
        circles.append(circle)

    return circles

def to_userlist(input):
    """
    Converts input list into a list of User objects.
    """
    
    users = []
    for item in input:
        id = item[0]
        country = item[1]
        international = item[2]
    
        user = User(id, country, international)
        users.append(user)

    return users

if __name__ == '__main__':

    class TestTubeSet(TubeSet):
        def differentiator(self, obj):
            return obj

    ts = TestTubeSet('aXaaaaaaaaaaaaaaaaaaaaaaaaaa')
    rejects = ts.pop_rejects()
    assert len(rejects) == 25

    ts = TestTubeSet('aXaaaaa')
    rejects = ts.pop_rejects()
    assert len(rejects) == 4

    ts = TestTubeSet('aXaXaXaXaa')
    rejects = ts.pop_rejects()
    assert len(rejects) == 1

    ts = TestTubeSet('aXaXaXaXa')
    rejects = ts.pop_rejects()
    assert len(rejects) == 0

    input_ = [
        (1, 'usa', True),
        (2, 'usa', True),
        (3, 'usa', True),
        (4, 'usa', True),
        (5, 'usa', True),
        (6, 'usa', True),
        (7, 'usa', True),
        (8, 'usa', True),
        (9, 'usa', False),
        (10, 'ca', True),
        (11, 'ca', True),
        (12, 'ca', True),
        (13, 'ca', True),
        (14, 'ca', True),
        (15, 'ca', True),
        (16, 'ch', False),
        (17, 'ch', False),
        (18, 'ch', False),
        (19, 'ch', True),
        (20, 'ch', True),
        (21, 'in', True),
        (22, 'in', True),
        (23, 'in', True),
        (24, 'zb', True),
        (25, 'zb', True),
        (26, 'de', True),
        (27, 'de', False),
        (28, 'de', False),
        (29, 'de', True),
        (30, 'de', True),
        (31, 'de', True),
        (32, 'de', True),
        (33, 'de', True),
    ]
    
    userlist = to_userlist(input_)
    
    # all users who can ship internationally, put them into their own circle
    international_users = [user for user in userlist if user.international]
    international_circle = InternationalCircle(international_users)
    
    # all users who can only ship domestically, put them into seperate circles,
    # one for each unique country
    domestic_users = [user for user in userlist if not user.international]
    
    # all countries that make up the domestic users
    domestic_circles = []
    domestic_rejects = []
    countries = set([user.country for user in domestic_users])
    for country in countries:
        circle = DomesticCircle(country, domestic_users)
        domestic_rejects.extend(circle.get_rejects())
        domestic_circles.append(circle)
    
    # collect all international circle rejects, and add them to their country's
    # domestic circle. (international rejects are always from the same country)
    international_rejects = international_circle.get_rejects()
    if international_rejects:
        domestic_circles = add_international_rejects_to_domestic_circle(international_rejects, domestic_circles)
    
    for circle in domestic_circles:
        print("--Domestic Circle %s--" % circle.country)
        [print(x.as_list()) for x in circle.rotate()] or print("[No one]")
    
    # all domestic rejects have no choice but to be added to the international circle.
    international_circle.add_to_circle(domestic_rejects)

    print("--International Circle--")
    [print(x.as_list()) for x in international_circle.rotate()]