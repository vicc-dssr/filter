from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _
import logging


logger = logging.getLogger(__name__)


class FilterUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class FilterUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = FilterUserManager()

    def __str__(self):
        return self.email


class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    domain_name = models.CharField(max_length=200)
    probability_without_entry = models.DecimalField(max_digits=3, decimal_places=2)
    order_by = models.IntegerField()

    def __str__(self):
        return '%s (%s)' % (self.domain_name, self.probability_without_entry)


class DomainCategory(models.Model):
    id = models.AutoField(primary_key=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='categories')
    category_name = models.CharField(max_length=200)

    def __str__(self):
        return 'domain_name: %s; category_name: %s' % (self.domain.domain_name, self.category_name)

    class Meta:
        db_table = 'filterapp_domain_category'


class PatientCategory(models.Model):
    id = models.AutoField(primary_key=True)
    patient_id = models.IntegerField
    domainCategory = models.ForeignKey(DomainCategory, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.domainCategory.category_name

    class Meta:
        db_table = 'filterapp_patient_category'


class Patient(models.Model):
    domain1 = models.CharField(max_length=500, null=True, blank=True)
    domain2 = models.CharField(max_length=500, null=True, blank=True)
    domain3 = models.CharField(max_length=500, null=True, blank=True)
    domain4 = models.CharField(max_length=500, null=True, blank=True)
    domain5 = models.CharField(max_length=500, null=True, blank=True)
    domain6 = models.CharField(max_length=500, null=True, blank=True)
    domain7 = models.CharField(max_length=500, null=True, blank=True)
    domain8 = models.CharField(max_length=500, null=True, blank=True)
    domain9 = models.CharField(max_length=500, null=True, blank=True)
    current_ranking = models.IntegerField(null=True, blank=True)
    latest_game_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    status_date = models.DateTimeField(null=True, blank=True)
    is_playing = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return '%d: %s-%s-%s-%s-%s-%s-%s-%s' % (self.id, self.domain1, self.domain2,
                                                self.domain3, self.domain4,
                                                self.domain5, self.domain6,
                                                self.domain7, self.domain8)

    class Meta:
        db_table = 'filterapp_patient'
        managed = True


class Game(models.Model):
    player1 = models.ForeignKey(Patient, db_column='player1',
                                related_name='player1_games', on_delete=models.CASCADE)
    player2 = models.ForeignKey(Patient, db_column='player2',
                                related_name='player2_games', on_delete=models.CASCADE)
    result = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    pre_game_ranking1 = models.IntegerField(null=True, blank=True)
    pre_game_ranking2 = models.IntegerField(null=True, blank=True)
    post_game_ranking1 = models.IntegerField(null=True, blank=True)
    post_game_ranking2 = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)
    status_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey('filterapp.FilterUser', related_name='games', on_delete=models.SET_NULL, db_column='user_id',
                             null=True, blank=True)
    batch_cnt = models.IntegerField(null=True, blank=True)
    k_factor = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return '%d: pre - %s > post - %s; %d: pre - %s > post - %s' % \
               (self.player1.id, self.pre_game_ranking1, self.post_game_ranking1, self.player2.id,
                self.pre_game_ranking2, self.post_game_ranking2)


class UserGameAction(models.Model):
    user = models.ForeignKey('filterapp.FilterUser', related_name='user_actions', on_delete=models.SET_NULL, null=True, blank=True)
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, related_name='game_actions', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, related_name='patient_actions', null=True,
                                blank=True)
    action_type = models.CharField(max_length=200, null=True)
    time_stamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'filterapp_user_action'


class Institution(models.Model):
    name = models.CharField(max_length=2000, blank=False, null=False)
    status = models.CharField(max_length=100, blank=True, null=True, default='ACTIVE')
    status_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return u'{0}'.format(self.name)


class Code(models.Model):
    code_class = models.CharField(max_length=500, blank=False, null=False)
    code_value = models.CharField(max_length=500, blank=False, null=False)
    code_label = models.CharField(max_length=500, blank=True, null=True)
    code_order = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True, default='ACTIVE')
    status_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return u'{0}'.format(self.code_label)


class Profile(models.Model):
    user = models.OneToOneField(FilterUser, on_delete=models.CASCADE, primary_key=True,)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    inst_other = models.CharField(max_length=500, blank=True, null=True)
    race = models.ForeignKey(Code, on_delete=models.SET_NULL, blank=True, null=True, related_name='race')
    ethnicity = models.ForeignKey(Code, on_delete=models.SET_NULL, blank=True, null=True, related_name='ethnicity')
    onco_modality = models.ForeignKey(Code, on_delete=models.SET_NULL, blank=True, null=True, related_name='onco_modality')
    modality_other = models.CharField(max_length=500, blank=True, null=True)
    onco_population = models.ForeignKey(Code, on_delete=models.SET_NULL, blank=True, null=True, related_name='onco_pupulation')

    def clean(self):
        if self.institution is None and self.inst_other is None:
            raise ValidationError('Must select or enter an institution.')
        if self.institution is not None and self.inst_other is not None:
            self.inst_other = ''


@receiver(post_save, sender=FilterUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=FilterUser)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        logger.info("no profile exists")





