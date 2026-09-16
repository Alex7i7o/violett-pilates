from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        pass
        
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        # Force email as username just in case internal allauth logic needs a "username" concept 
        # (even though our model doesn't have the field)
        if commit:
            user.save()
        return user
