from configparser import ConfigParser

config = ConfigParser()

config.add_section("main")

config.set("main", "CLIENT_ID", "")
config.set("main", "REDIRECT_URL", "")
config.set("main", "JSON_PATH", "")
config.set("main", "ACCOUNT_NUMBER", "")

# w = write  w+ mean to establish the config file

with open("configs/configs.ini", "w") as f:
    config.write(f)
