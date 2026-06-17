from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile

User = get_user_model()

# ---------------------------------------------------------------------------
# Existing MVP form (kept)
# ---------------------------------------------------------------------------

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    display_name = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['email', 'display_name', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


# ---------------------------------------------------------------------------
# G2 — Step 1: Sign-up form
# ---------------------------------------------------------------------------

class SignUpForm(forms.Form):
    email = forms.EmailField(label='Email address')
    password = forms.CharField(label='Password', min_length=10, widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise forms.ValidationError(e.messages)
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            self.add_error('password_confirm', 'Passwords do not match.')
        return cleaned


# ---------------------------------------------------------------------------
# G2 — Step 2: Profile setup form (three sections)
# ---------------------------------------------------------------------------

COUNTRY_CHOICES = [
    ('', '— Select country —'),
    ('AF', 'Afghanistan'), ('AL', 'Albania'), ('DZ', 'Algeria'), ('AO', 'Angola'),
    ('AR', 'Argentina'), ('AU', 'Australia'), ('AT', 'Austria'), ('BE', 'Belgium'),
    ('BJ', 'Benin'), ('BW', 'Botswana'), ('BR', 'Brazil'), ('BG', 'Bulgaria'),
    ('BF', 'Burkina Faso'), ('BI', 'Burundi'), ('CM', 'Cameroon'), ('CA', 'Canada'),
    ('CF', 'Central African Republic'), ('TD', 'Chad'), ('CL', 'Chile'), ('CN', 'China'),
    ('CO', 'Colombia'), ('CG', 'Congo'), ('CD', 'Congo (DRC)'), ('CI', "Côte d'Ivoire"),
    ('HR', 'Croatia'), ('CZ', 'Czech Republic'), ('DK', 'Denmark'), ('DJ', 'Djibouti'),
    ('EG', 'Egypt'), ('GQ', 'Equatorial Guinea'), ('ER', 'Eritrea'), ('ET', 'Ethiopia'),
    ('FI', 'Finland'), ('FR', 'France'), ('GA', 'Gabon'), ('GM', 'Gambia'),
    ('GH', 'Ghana'), ('DE', 'Germany'), ('GR', 'Greece'), ('GN', 'Guinea'),
    ('GW', 'Guinea-Bissau'), ('HU', 'Hungary'), ('IN', 'India'), ('ID', 'Indonesia'),
    ('IE', 'Ireland'), ('IL', 'Israel'), ('IT', 'Italy'), ('JM', 'Jamaica'),
    ('JP', 'Japan'), ('JO', 'Jordan'), ('KE', 'Kenya'), ('KR', 'Korea (South)'),
    ('LS', 'Lesotho'), ('LR', 'Liberia'), ('LY', 'Libya'), ('MG', 'Madagascar'),
    ('MW', 'Malawi'), ('MY', 'Malaysia'), ('ML', 'Mali'), ('MR', 'Mauritania'),
    ('MU', 'Mauritius'), ('MX', 'Mexico'), ('MD', 'Moldova'), ('MA', 'Morocco'),
    ('MZ', 'Mozambique'), ('MM', 'Myanmar'), ('NA', 'Namibia'), ('NL', 'Netherlands'),
    ('NZ', 'New Zealand'), ('NE', 'Niger'), ('NG', 'Nigeria'), ('NO', 'Norway'),
    ('PK', 'Pakistan'), ('PA', 'Panama'), ('PY', 'Paraguay'), ('PE', 'Peru'),
    ('PH', 'Philippines'), ('PL', 'Poland'), ('PT', 'Portugal'), ('RO', 'Romania'),
    ('RW', 'Rwanda'), ('SA', 'Saudi Arabia'), ('SN', 'Senegal'), ('SL', 'Sierra Leone'),
    ('SO', 'Somalia'), ('ZA', 'South Africa'), ('SS', 'South Sudan'), ('ES', 'Spain'),
    ('SD', 'Sudan'), ('SZ', 'Eswatini'), ('SE', 'Sweden'), ('CH', 'Switzerland'),
    ('TZ', 'Tanzania'), ('TH', 'Thailand'), ('TG', 'Togo'), ('TT', 'Trinidad and Tobago'),
    ('TN', 'Tunisia'), ('TR', 'Turkey'), ('UG', 'Uganda'), ('UA', 'Ukraine'),
    ('GB', 'United Kingdom'), ('US', 'United States'), ('UY', 'Uruguay'),
    ('VE', 'Venezuela'), ('VN', 'Vietnam'), ('YE', 'Yemen'), ('ZM', 'Zambia'),
    ('ZW', 'Zimbabwe'),
]


class ProfileSetupForm(forms.Form):

    # Section 1 — Personal Details
    title = forms.ChoiceField(
        choices=[('', '—')] + UserProfile.TITLE_CHOICES,
        required=False,
    )
    full_name = forms.CharField(max_length=255, label='Full names')
    phone_number = forms.CharField(max_length=30, required=False, label='Phone number')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    country = forms.ChoiceField(choices=COUNTRY_CHOICES)
    id_number = forms.CharField(
        max_length=100, required=False,
        label='Identity number / Passport',
        help_text='Stored encrypted. Never shared.',
    )
    date_of_birth = forms.DateField(
        required=False,
        label='Date of birth',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    gender = forms.ChoiceField(
        choices=[('', '—')] + UserProfile.GENDER_CHOICES,
        required=False,
    )
    marital_status = forms.ChoiceField(
        choices=[('', '—')] + UserProfile.MARITAL_CHOICES,
        required=False,
    )

    # Section 2 — Qualifications, Gifts & Skills
    occupation = forms.CharField(max_length=255, required=False, label='Occupation / Profession')
    education = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False,
        label='Education / Highest qualification',
    )
    interests = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False,
        label='Interests / Hobbies',
    )
    gifts_skills = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False,
        label='Gifts & Skills',
        help_text='List your spiritual gifts, skills, and talents.',
    )

    # Section 3 — Existing Christian
    PATHWAY_CHOICES = [
        ('beginners', 'I am new to this, or exploring faith'),
        ('reconditioning', 'I am already part of a church or faith community'),
    ]
    induction_pathway = forms.ChoiceField(
        choices=PATHWAY_CHOICES,
        widget=forms.RadioSelect,
        label='Which best describes you?',
    )
    accepted_christ = forms.NullBooleanField(
        required=False,
        label='Have you accepted Jesus Christ as your personal Saviour?',
        widget=forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
    )
    church_member = forms.NullBooleanField(
        required=False,
        label='Do you currently belong to a church or ministry?',
        widget=forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')]),
    )
    church_name = forms.CharField(max_length=255, required=False, label='Name of church / ministry')
    referee_1_name = forms.CharField(max_length=255, required=False, label='First referee (full name)')
    referee_2_name = forms.CharField(max_length=255, required=False, label='Second referee (full name)')
    referee_letter_1 = forms.FileField(
        required=False, label='Referee letter 1 (PDF or Word)',
        help_text='Upload a letter from your first referee.',
    )
    referee_letter_2 = forms.FileField(
        required=False, label='Referee letter 2 (PDF or Word)',
        help_text='Upload a letter from your second referee.',
    )

    # Consent
    terms_accepted = forms.BooleanField(
        label='I agree to the Terms & Conditions and Privacy Policy',
        error_messages={'required': 'You must accept the terms to continue.'},
    )

    def clean_country(self):
        country = self.cleaned_data.get('country', '').strip()
        if not country:
            raise forms.ValidationError('Please select your country.')
        return country

    def clean_full_name(self):
        return self.cleaned_data.get('full_name', '').strip()
