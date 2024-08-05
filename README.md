# ARK-server-voter
Automatic voter for servers in ARK for unofficial servers with rewards
The script is setup to vote (and also claim rewards) for the unnoficial ARK Ascended servers of MenAtWorkGaming cluster, but can be easily modified to vote for other servers.


## Setup
1. Clone the repository with `git clone `
2. Install the required packages with `pip install -r requirements.txt`
3. Create a file '.env' in the root directory of the project and add the following:
```env
STEAM_USERNAME=<your_steam_username>
STEAM_PASSWORD=<your_steam_password>
```
4. Change the `servers` list in `.server_ids.txt` to the servers you want to vote for
5. Run the script with `python main.py` and follow the instructions

