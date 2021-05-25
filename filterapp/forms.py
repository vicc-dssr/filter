from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django import forms
from django.forms import ModelForm
from filterapp.models import Profile, FilterUser, Code, Institution


class FilterUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = FilterUser
        fields = ('first_name', 'last_name', 'email')


# class FilterUserForm(ModelForm):
#     class Meta:
#         model = FilterUser
#         fields = ('first_name', 'last_name', 'email')


# class InstitutionWidget(s2forms.ModelSelect2Widget):
#     search_fields = [
#         "name__icontains",
#     ]


class FilterProfileForm(ModelForm):
    race = forms.ModelChoiceField(label='Race', queryset=Code.objects.filter(code_class='RACE').order_by('code_order').order_by('code_label'), empty_label='Please select', required=False)
    ethnicity = forms.ModelChoiceField(queryset=Code.objects.filter(code_class='ETHNICITY').order_by('code_order').order_by('code_label'), empty_label='Please select', required=False)
    onco_modality = forms.ModelChoiceField(label='Oncologist modality specialty', queryset=Code.objects.filter(code_class='ONCO_MODALITY').order_by('code_order').order_by('code_label'), empty_label='Please select', required=False)
    onco_population = forms.ModelChoiceField(label='Oncologist population specialty', queryset=Code.objects.filter(code_class='ONCO_POPULATION').order_by('code_order').order_by('code_label'), empty_label='Please select', required=False)

    class Meta:
        model = Profile
        fields = (
            'institution', 'inst_other', 'race', 'ethnicity', 'onco_modality', 'modality_other', 'onco_population')
        labels = {
            'inst_other': 'If not found, type institution name here ',
            'modality_other': 'If not found, type modality specialty here ',
        }

    def __init__(self, *args, **kwards):
        super().__init__(*args, **kwards)
        self.fields['institution'].queryset = Institution.objects


class UserForgotPasswordForm(PasswordResetForm):
    """User forgot password, check via email form."""
    email = forms.EmailField(
        label='Email address',
        max_length=254,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email address',
                'type': 'text',
                'id': 'email_address'
            }))