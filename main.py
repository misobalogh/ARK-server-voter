from vote import Voter

if __name__ == "__main__":
    # mawg_voter = Voter(".mawg_servers.txt", "steam_cookies.pkl", "mawg_cookies.pkl", [34652, 46586, 42078], 5)
    # mawg_voter.vote_and_claim()
    arklegends_voter = Voter(".arklegends_servers.txt", "steam_cookies.pkl", "zoznam.sk", 5)
    arklegends_voter.vote_only()