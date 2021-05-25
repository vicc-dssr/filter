from rest_framework import serializers
from filterapp.models import *
from django.contrib.auth.models import User


class DomainCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = DomainCategory
        fields = '__all__'


class DomainSerializer(serializers.ModelSerializer):
    categories = DomainCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    # player1_games = serializers.StringRelatedField(many=True, read_only=True)
    # player2_games = serializers.StringRelatedField(many=True, read_only=True)
    # player1_games = GameSerializer(many=True, read_only=True)
    # player2_games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = '__all__'


class GameSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    player1 = PatientSerializer()
    player2 = PatientSerializer()

    class Meta:
        model = Game
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    # games = serializers.StringRelatedField(many=True)
    games = GameSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'games']


class UserGameActionSerializer(serializers.ModelSerializer):
    # user = UserSerializer()
    # game = GameSerializer()
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserGameAction
        fields = '__all__'


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = '__all__'
