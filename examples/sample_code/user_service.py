"""用户服务模块 - 包含多种故意写下的技术债"""


class UserService:
    def __init__(self, db, cache, logger, metrics, notifier, config):
        self.db = db
        self.cache = cache
        self.logger = logger
        self.metrics = metrics
        self.notifier = notifier
        self.config = config

    def process_user_registration(self, user_data):
        # TODO: add email validation
        name = user_data.get("name", "")
        email = user_data.get("email", "")
        age = user_data.get("age", 0)
        role = user_data.get("role", "user")

        if name:
            if len(name) > 2:
                if email:
                    if "@" in email:
                        if age:
                            if age > 0:
                                if age < 150:
                                    if role:
                                        user_id = self.db.insert(
                                            "users",
                                            {"name": name, "email": email, "age": age, "role": role},
                                        )
                                        self.cache.set(f"user:{user_id}", user_data)
                                        self.notifier.send("welcome", email)
                                        self.metrics.increment("registrations")
                                        self.logger.info(f"User {user_id} registered")
                                        return user_id
        return None

    def get_user(self, user_id):
        cached = self.cache.get(f"user:{user_id}")
        if cached:
            return cached
        user = self.db.query("SELECT * FROM users WHERE id = ?", [user_id])
        if user:
            self.cache.set(f"user:{user_id}", user)
        return user

    def delete_user(self, user_id):
        try:
            self.db.execute("DELETE FROM users WHERE id = ?", [user_id])
            self.cache.delete(f"user:{user_id}")
            self.logger.info(f"User {user_id} deleted")
        except:
            pass

    def update_user_profile(self, user_id, profile_data):
        # FIXME: this is broken for nested fields
        self.db.execute("UPDATE users SET profile = ? WHERE id = ?",
                        [str(profile_data), user_id])
        self.cache.delete(f"user:{user_id}")

    def get_all_active_users(self):
        users = self.db.query("SELECT * FROM users WHERE active = 1")
        result = []
        for u in users:
            result.append(u)
        return result

    def get_users_by_role(self, role):
        users = self.db.query("SELECT * FROM users WHERE role = ?", [role])
        return users

    def search_users(self, query):
        # FIXME: SQL injection risk
        sql = "SELECT * FROM users WHERE name LIKE '%" + query + "%'"
        return self.db.query(sql)
