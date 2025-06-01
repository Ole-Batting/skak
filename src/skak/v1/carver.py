
UD = u'\u2551'
UR = u'\u255a'
LRD = u'\u2566'
URD = u'\u2560'
LR = u'\u2550'


def _viz(tree, x, b, linename):
    if len(tree.children) == 0:
        print(f"1/{fraction(tree.ratio):.0f} {linename}", end="")
    else:
        for i, (lan, child) in enumerate(tree.children.items()):
            next_linename = child.opening_name or linename
            san = child.san
            if child.opening_name is None:
                next_linename += f",{san}"
            san = padsan(san)
            if i != 0:
                c = b+(1<<x)
                print("\n", end="")
                for j in range(x + 1):
                    if (c >> j) & 0x1:
                        print(pad(UD), end="")
                    else:
                        print(pad(), end="")
                print()
                for j in range(x):
                    if (c >> j) & 0x1:
                        print(pad(UD), end="")
                    else:
                        print(pad(), end="")
            if len(tree.children) == 1:
                print(f"{LR}{san}", end="")
            elif i == 0:
                print(f"{LRD}{san}", end="")
            elif i == len(tree.children)-1:
                print(f"{UR}{san}", end="")
            else:
                print(f"{URD}{san}", end="")
            _viz(child, x+1, b+(int(i!=len(tree.children)-1)<<x), next_linename)


def viz(tree):
    _viz(tree, 0, 0, "")
    print()


def fraction(ratio: float):
    return round(1 / ratio, 0)


def pad(s=""):
    return s + " "*(6-len(s))


def padsan(san):
    return san + LR*(5-len(san))

