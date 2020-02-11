# Class to store champion names in one location
class Champion:
    """Champions in Paladins"""
    DAMAGES = ["Cassie", "Kinessa", "Drogoz", "Bomb King", "Viktor", "Sha Lin", "Tyra", "Willo", "Lian", "Strix",
               "Vivian", "Dredge", "Imani", "Tiberius"]
    FLANKS = ["Skye", "Buck", "Evie", "Androxus", "Maeve", "Lex", "Zhin", "Talus", "Moji", "Koga"]
    TANKS = ["Barik", "Fernando", "Ruckus", "Makoa", "Torvald", "Inara", "Ash", "Terminus", "Khan", "Atlas", "Raum"]
    SUPPORTS = ["Grohk", "Grover", "Ying", "Mal Damba", "Seris", "Jenos", "Furia", "Pip"]

    # Returns a number for indexing in a list
    def get_champ_class(self, champ_name: str):
        champ_name = champ_name.title()
        if champ_name in self.DAMAGES:
            return 0
        elif champ_name in self.FLANKS:
            return 1
        elif champ_name in self.TANKS:
            return 2
        elif champ_name in self.SUPPORTS:
            return 3
        else:
            return -1
