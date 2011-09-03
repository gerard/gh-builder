builder_root        = "/home/gerard/builder"
git_cmd             = "git"
workspace_dir       = "_workspace"
logs_dir            = "log"

def define_user(user, builds_per_day=30, build_systems=["android"], build_time=300):
    return { user:
                {
                    "builds_per_day"    : builds_per_day,
                    "build_systems"     : build_systems,
                    "max_build_time"    : build_time,
                }
            }

allowed_users  = []
allowed_users += define_user("mkd")
allowed_users += define_user("marcostong17")
allowed_users += define_user("mataanin")
allowed_users += define_user("quelcom")
allowed_users += define_user("jush")
allowed_users += define_user("hleinone")
allowed_users += define_user("AndroidAalto")

allowed_users += define_user("gerard", builds_per_day=300, build_systems=["android", "make"])
