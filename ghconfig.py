class User(object):
    def __init__(self, name):
        self.name           = name
        self.build_systems  = ["android"]
        self.builds_per_day = 30
        self.max_build_time = 300

class UserList(object):
    def __init__(self):
        self.users = {}

    def __getitem__(self, key):
        return self.users[key]

    def __contains__(self, key):
        return key in self.users

    def add_user(self, name):
        self.users[name] = User(name)
        return self.users[name]


# Configuration starts here
builder_root        = "/home/gerard/builder"
git_cmd             = "git"
workspace_dir       = "_workspace"
logs_dir            = "log"

# User configurations
allowed_users = UserList()
allowed_users.add_user("mkd")
allowed_users.add_user("marcostong17")
allowed_users.add_user("mataanin")
allowed_users.add_user("quelcom")
allowed_users.add_user("jush")
allowed_users.add_user("hleinone")
allowed_users.add_user("AndroidAalto")
allowed_users.add_user("gerard")

# User configurations: modifications from the default user
allowed_users["gerard"].build_systems += ["make"]
