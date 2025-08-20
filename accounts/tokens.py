from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, profile, timestamp):
        return str(profile.id) + str(timestamp)


account_activation_token = AccountActivationTokenGenerator()