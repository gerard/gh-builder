builder_root        = "/home/gerard/builder"
git_cmd             = "git"
workspace_dir       = "_workspace"
logs_dir            = "log"

allowed_users_default_config = {
    "builds_per_day"    : 30,
    "build_systems"     : ["android"],
    "max_build_time"    : 300,
}

allowed_users                   = {}
allowed_users["mkd"]            = allowed_users_default_config
allowed_users["marcostong17"]   = allowed_users_default_config
allowed_users["mataanin"]       = allowed_users_default_config
allowed_users["quelcom"]        = allowed_users_default_config
allowed_users["jush"]           = allowed_users_default_config
allowed_users["hleinone"]       = allowed_users_default_config
allowed_users["AndroidAalto"]   = allowed_users_default_config
allowed_users["gerard"]         = allowed_users_default_config

allowed_users["gerard"]["build_systems"] += "make"
