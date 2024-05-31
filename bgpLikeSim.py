class Route:
    def __init__(self, neigh, p, plen, path):
        self.neighbor = neigh
        self.prefix = p
        self.prefix_len = plen
        self.path = path 

    def __str__(self):
        return self.prefix + "/" + str(self.prefix_len) + "- ASPATH: " + str(self.path) + ", neigh: " + self.neighbor

    def pfx_str(self):
        return self.prefix + "/" + str(self.prefix_len)


class Router:
    def __init__(self):
        self.rib = {}

    def printRIB(self):
        for pfx in self.rib.keys():
            for route in self.rib[pfx]:
                print(route)

    def update(self, rt):
        prefix_key = rt.pfx_str()
        if prefix_key in self.rib:
            for idx, existing_route in enumerate(self.rib[prefix_key]):
                if existing_route.neighbor == rt.neighbor:
                    self.rib[prefix_key][idx] = rt
                    return
            self.rib[prefix_key].append(rt)
        else:
            self.rib[prefix_key] = [rt]
        return

    def withdraw(self, rt):
        prefix_key = rt.pfx_str()
        if prefix_key in self.rib:
            self.rib[prefix_key] = [r for r in self.rib[prefix_key] if r.neighbor != rt.neighbor]
            if not self.rib[prefix_key]:
                del self.rib[prefix_key]
        return

    def convertToBinaryString(self, ip):
        vals = ip.split(".")
        a = format(int(vals[0]), 'b').zfill(8)
        b = format(int(vals[1]), 'b').zfill(8)
        c = format(int(vals[2]), 'b').zfill(8)
        d = format(int(vals[3]), 'b').zfill(8)
        return a + b + c + d

    def next_hop(self, ipaddr):
        binary_ip = self.convertToBinaryString(ipaddr)
        best_match_len = -1
        best_route = None

        for prefix_key in self.rib:
            try:
                prefix_ip, prefix_len = prefix_key.split('/')
                prefix_len = int(prefix_len)
                binary_prefix = self.convertToBinaryString(prefix_ip)[:prefix_len]

                if binary_ip.startswith(binary_prefix):
                    if prefix_len > best_match_len:
                        best_match_len = prefix_len
                        best_route = min(self.rib[prefix_key], key=lambda r: len(r.path))
            except ValueError:
                continue  # Skip prefixes that are incorrectly formatted

        if best_route:
            return best_route.neighbor
        return None

# Test cases as provided
def test_cases():
    rtr = Router()

    # Test that withdrawing a non-existent route works
    rtr.withdraw(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))

    # Test updates work - same prefix, two neighbors
    rtr.update(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))
    rtr.update(Route("2.2.2.2", "10.0.0.0", 24, [1, 2]))

    print("RIB")
    rtr.printRIB()

    # Test updates work - overwriting an existing route from a neighbor
    rtr.update(Route("2.2.2.2", "10.0.0.0", 24, [1, 22, 33, 44]))

    print("RIB")
    rtr.printRIB()

    # Test updates work - an overlapping prefix (this case, a shorter prefix)
    rtr.update(Route("2.2.2.2", "10.0.0.0", 22, [4, 5, 7, 8]))

    # Test updates work - completely different prefix
    rtr.update(Route("2.2.2.2", "12.0.0.0", 16, [4, 5]))
    rtr.update(Route("1.1.1.1", "12.0.0.0", 16, [1, 2, 30]))

    print("RIB")
    rtr.printRIB()

    # Should Fail
    nh = rtr.next_hop("10.2.0.13")
    assert nh == None

    # Should match
    nh = rtr.next_hop("10.0.0.13")
    assert nh == "1.1.1.1"

    # Test withdraw - withdraw the route from 1.1.1.1 that we just matched
    rtr.withdraw(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))

    # Should match something different
    nh = rtr.next_hop("10.0.0.13")
    assert nh == "2.2.2.2"

    # Re-announce - so, 1.1.1.1 would now be best route
    rtr.update(Route("1.1.1.1", "10.0.0.0", 24, [3, 4, 5]))

    rtr.update(Route("2.2.2.2", "10.0.0.0", 22, [4, 5, 7, 8]))
    # Should match 10.0.0.0/22 (next hop 2.2.2.2) but not 10.0.0.0/24 (next hop 1.1.1.1)
    nh = rtr.next_hop("10.0.1.77")
    assert nh == "2.2.2.2"

    # Test a different prefix
    nh = rtr.next_hop("12.0.12.0")
    assert nh == "2.2.2.2"

    rtr.update(Route("1.1.1.1", "20.0.0.0", 16, [4, 5, 7, 8]))
    rtr.update(Route("2.2.2.2", "20.0.0.0", 16, [44, 55]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "2.2.2.2"

    rtr.update(Route("1.1.1.1", "20.0.12.0", 24, [44, 55, 66, 77, 88]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "1.1.1.1"

    # Remember to delete the entry from the RIB, not just removing the specific route
    # That is, when you withdraw, remove the route for the prefix, and if there are 0 routes, remove the prefix from the RIB
    rtr.withdraw(Route("1.1.1.1", "20.0.12.0", 24, [44, 55, 66, 77, 88]))
    nh = rtr.next_hop("20.0.12.0")
    assert nh == "2.2.2.2"

if __name__ == "__main__":
    test_cases()
