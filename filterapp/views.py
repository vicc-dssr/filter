from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from smtplib import SMTPException
from django.http import JsonResponse, HttpResponseRedirect
from django.db import connection
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.urls import reverse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, get_user_model
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework import permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from filterapp.constants import *
from filterapp.serializers import *
from decimal import Decimal
import random
import math
import logging
import time
from django.utils import timezone
from filterapp.forms import *
from django.db import transaction

logger = logging.getLogger(__name__)


@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == "GET":
        user_form = FilterUserCreationForm()
        profile_form = FilterProfileForm()
        return render(
            request, "registration/signup.html",
            {
                'user_form': user_form,
                'profile_form': profile_form,
            }
        )
    elif request.method == "POST":
        user_form = FilterUserCreationForm(request.POST)
        profile_form = FilterProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.refresh_from_db()
            profile = Profile(**profile_form.cleaned_data)
            user.profile = profile
            user.is_active = False
            user.save()

            # send account activation email to user email
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = user_form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            try:
                email.send()
                return render(request, "registration/acc_active_email_sent.html")
            except SMTPException as e:
                logger.error('Error sending signup email: ', e)
                return render(request, "registration/acc_request_received.html")

        return render(
            request, "registration/signup.html",
            {
                'user_form': user_form,
                'profile_form': profile_form,
            }
        )


def activate(request, uidb64, token):
    try:
        UserModel = get_user_model()
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "registration/acc_active_confirmed.html")
    else:
        return render(request, "registration/acc_active_denied.html")


def deactivate(request):
    user = request.user
    user.is_active = False
    user.save()
    return render(request, "registration/deactivate_confirmed.html")


def deactivate_account(request):
    return render(request, "registration/deactivate_account.html")


def password_reset(request):
    """User forgot password form view."""
    if request.method == "POST":
        password_reset_form = UserForgotPasswordForm(request.POST)
        if password_reset_form.is_valid():
            UserModel = get_user_model()
            email = request.POST.get('email')
            queryset = UserModel.objects.filter(email=email)
            if len(queryset) > 0:
                user = queryset[0]
                user.is_active = False  # User needs to be inactive for the reset password duration
                user.save()

                # send account activation email to user email
                current_site = get_current_site(request)
                mail_subject = 'Reset Password'
                message = render_to_string('registration/password_reset_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                email_send = EmailMessage(
                    mail_subject, message, to=[email]
                )
                email_send.send()

            return render(request, "registration/password_reset_done.html")

    return render(request, 'registration/password_reset_form.html', {'password_reset_form': UserForgotPasswordForm})


def reset(request, uidb64, token):
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                user.is_active = True
                user.save()
                return render(request, "registration/password_reset_complete.html")
        else:
            form = SetPasswordForm(user)
    else:
        validlink = False
        form = None
    context = {
        'form': form,
        'validlink': validlink,
    }

    return render(request, 'registration/password_reset_confirm.html', context)


class DomainList(generics.ListCreateAPIView):

    queryset = Domain.objects.all().order_by("order_by")
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        start_time = time.time()
        response = generics.ListCreateAPIView.list(self, request, *args, **kwargs)
        logger.info(f"get domain list takes: {time.time() - start_time} seconds")
        return response


class PatientList(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]


class PatientDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]


class GameList(generics.ListCreateAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # p1 = serializer.validated_data.get('player1', None).id
        # p2 = serializer.validated_data.get('player2', None).id
        db_game = serializer.save(user=self.request.user)
        # do_ranking_calculation2(db_game.player1, db_game)
        # do_ranking_calculation2(db_game.player2, db_game)
        do_ranking_calculation3(db_game)


class GameDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    # permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    permission_classes = [permissions.IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        game = self.get_object()
        data = request.data
        if data.get('result') is None:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            game.result = data.get('result')
            game.user = self.request.user
        player1 = game.player1
        player2 = game.player2
        game.pre_game_ranking1 = player1.current_ranking
        game.pre_game_ranking2 = player2.current_ranking
        do_ranking_calculation4(game)
        # diffuse PHASE II if there is any
        do_diffusion()
        serializer = GameSerializer(game, partial=True)
        return Response(serializer.data)


class UserList(generics.ListAPIView):
    queryset = FilterUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserDetail(generics.RetrieveAPIView):
    queryset = FilterUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserGameActionList(generics.ListCreateAPIView):
    queryset = UserGameAction.objects.all()
    serializer_class = UserGameActionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        db_action = serializer.save(user=self.request.user)


class UserGameActionDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserGameAction.objects.all()
    serializer_class = UserGameActionSerializer
    permission_classes = [permissions.IsAuthenticated]


class InstitutionList(generics.ListCreateAPIView):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        institution = request.data["name"]
        db_object = Institution.objects.filter(name__iexact=institution).first()
        if db_object:
            serializer = InstitutionSerializer(db_object)
            return Response(serializer.data, status=status.HTTP_303_SEE_OTHER)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(status=STATUS_ACTIVE, status_date=timezone.now())


@api_view(['GET'])
@login_required(login_url='/login/')
def gen_patient(request):
    db_pt = do_gen_patient()
    serializer = PatientSerializer(db_pt)
    return Response(serializer.data)


# 1. return empty game if exists
# 2. if no empty games left, check existence of pointer
# 3. if no pointer, get a PHASE I case, assign pointer and batch gen games
# 4. if pointer points to PHASE I case, update status from PHASE I -> PHASE III, move pointer to
#  phase II case, and batch gen games, go to step 1
# 5. if pointer points to PHASE II case, update status from PHASE II -> PHASE III, move pointer
# to the next phase II case, batch gen games, go to step 1
# 6. if no more PHASE II case, do PHASE III/diffusion, and update status from PHASE III -> EXISTING,
# go to step 3
#
@api_view(['GET'])
def gen_game(request, user_id):
    game = get_pre_gen_game(user_id)
    if game is not None:
        return serialize_game(game)
    # no more pre generated games for the user,
    cnt = Game.objects.filter(Q(post_game_ranking1__isnull=True)
                              & (Q(status=STATUS_PHASE_I)
                                 | Q(status=STATUS_PHASE_II))).count()
    # there are pre-gen games, but all are skipped
    # create game with new cases.
    if cnt > 0:
        game = gen_game_extra()
        return serialize_game(game)
    # no more pre-gen games. Move through the phases
    reset_pointer()
    phase = check_phase()
    if phase == STATUS_INIT:
        init_game_board()
        gen_game_phase_i()
    elif phase == STATUS_PHASE_II:
        gen_game_phase_ii()
    elif phase == STATUS_PHASE_III:
        gen_game_phase_iii()
    else:
        gen_game_phase_i()
    game = get_pre_gen_game(user_id)
    if game is None:
        game = gen_game_extra()
    return serialize_game(game)


@api_view(['GET'])
def gen_game2(request, user_id):
    game = get_pre_gen_game(user_id)
    if game is None:
        gen_batch_games2(None)
        game = get_pre_gen_game(user_id)
        # in case the user skipped too many cases
        # instead of running recursively through existing cases, create a new case instead
        if game is None:
            game = gen_game_extra()
    return serialize_game(game)


@api_view(['GET'])
def init_game_board(request):
    cnt = Patient.objects.count()
    if cnt == 0:
        for i in range(NO_OF_DOMAINS):
            do_gen_patient()
    return Response('')


def get_pre_gen_game(user_id):
    start_time = time.time()
    ex_games = UserGameAction.objects.filter(user=user_id).values_list('game__id', flat=True).distinct()
    ex_patients = UserGameAction.objects.filter(user=user_id).values_list('patient__id', flat=True).distinct()
    game = Game.objects.filter(post_game_ranking1__isnull=True)
    if len(ex_patients) > 0 and ex_patients[0] is not None:
        game = game.exclude(player1__in=ex_patients).exclude(player2__in=ex_patients)
    if len(ex_games) > 0 and ex_games[0] is not None:
        game = game.exclude(id__in=ex_games)
    # print(f"query to get pre-gen game: {game.query}")
    game = game.order_by('?').first()
    # print(f"calling get_pre_gen_game takes {time.time() - start_time} ms")
    return game


def check_phase():
    cnt = Patient.objects.count()
    if cnt == 0:
        return STATUS_INIT
    phase_ii_cases = Patient.objects.filter(status=STATUS_PHASE_II)
    if phase_ii_cases.exists():
        return STATUS_PHASE_II
    phase_iii_cases = Patient.objects.filter(status=STATUS_PHASE_III)
    if phase_iii_cases.exists():
        return STATUS_PHASE_III
    phase_i_cases = Patient.objects.filter(status=STATUS_PHASE_I)
    if phase_i_cases.exists():
        return STATUS_PHASE_I
    return STATUS_EXISTING


def gen_game_phase_i_ii():
    return Patient.objects.filter(Q(is_playing__isnull=True)
                                     & (Q(status=STATUS_PHASE_I)
                                        | Q(status=STATUS_PHASE_II)))\
        .order_by('?').first()


#  gen game with two new cases
def gen_game_extra():
    player1 = do_gen_patient()
    player2 = do_gen_patient()
    game = Game.objects.create(player1=player1, player2=player2, status_date=timezone.now(), status=STATUS_PHASE_EXTRA)
    # since they are all new cases, just return instead of calling get_pre_gen_game
    return game


# call this only when there is no cases in PHASE II or PHASE III, and no pre gen games
def gen_game_phase_i():
    case = Patient.objects.filter(status=STATUS_PHASE_I).order_by('?').first()
    if case is None:
        case = do_gen_patient()
    gen_batch_games(case)


# call only when there are cases in PHASE II. Three scenarios:
# 1. no un-played game against PHASE I
# 2. no un-played game against PHASE II case
# 3. no un-played game against PHASE II case, but no more PHASE II case
def gen_game_phase_ii():
    case = Patient.objects.filter(status=STATUS_PHASE_II).first()
    if case is None:
        gen_game_phase_i()
    else:
        gen_batch_games(case)


# call method when there is no un-played games, and no PHASE II cases, but PHASE III cases
def gen_game_phase_iii():
    do_diffusion()
    gen_game_phase_i()


# gen batch games for case in either PHASE I or Phase II
def gen_batch_games2(case):
    if case is None:
        case = Patient.objects.filter(Q(is_playing__isnull=True)&(Q(status=STATUS_PHASE_I)|Q(status=STATUS_PHASE_II)))\
            .order_by('?').first()
    if case is None:
        case = do_gen_patient()
    # opponent should exclude:
    # already played against as player1 or player2
    # self
    # case in PHASE III
    player1_list = Game.objects.filter(player1=case).values_list('player2__id', flat=True)
    player2_list = Game.objects.filter(player2=case).values_list('player1__id', flat=True)
    opponents = Patient.objects.filter(~Q(id=case.id) & ~Q(status='PHASE III')) \
        .exclude(id__in=player1_list).exclude(id__in=player2_list).order_by('?')
    # print(f"query to get eligible opponents: {opponents.query}")
    cnt = opponents.count()
    # a PHASE I/II case has played against all other cases, mark as EXISTING
    # and move on to the next case
    if cnt == 0:
        case.is_playing = None
        case.status = STATUS_EXISTING
        case.save()
        gen_batch_games2(None)
    else:
        case.is_playing = '1'
        case.save()
        limit = round(math.log(cnt, 2))
        limit = 1 if limit < 1 else limit
        opponents_with_limit = opponents[0:limit]
        for opponent in opponents_with_limit:
            Game.objects.create(player1=case, player2=opponent, status_date=timezone.now(), status=case.status, batch_cnt=limit)


def gen_batch_games(case):
    case.is_playing = '1'
    case.save()
    # opponent should exclude:
    # already played against as player1 or player2
    # self
    # case in PHASE III
    player1_list = Game.objects.filter(player1=case).values_list('player2__id', flat=True)
    player2_list = Game.objects.filter(player2=case).values_list('player1__id', flat=True)
    opponents = Patient.objects.filter(~Q(id=case.id) & ~Q(status='PHASE III'))\
        .exclude(id__in=player1_list).exclude(id__in=player2_list).order_by('?')
    cnt = opponents.count()
    if cnt == 0:
        opponent = do_gen_patient()
        Game.objects.create(player1=case, player2=opponent, status_date=timezone.now(), status=case.status)
        opponent.is_playing = '2'
        opponent.save()
    else:
        limit = round(math.log(cnt, 2))
        limit = 1 if limit < 1 else limit
        opponents_with_limit = opponents[0:limit]
        for opponent in opponents_with_limit:
            Game.objects.create(player1=case, player2=opponent, status_date=timezone.now(), status=case.status)
            opponent.is_playing = '2'
            opponent.save()


# remove existing pointer, and promote to PHASE III
# mark new case as is_playing=1
def reset_pointer():
    with connection.cursor() as cursor:
        cursor.execute("UPDATE filterapp_patient SET is_playing=null, status=%s, status_date=sysdate() WHERE is_playing='1'", [STATUS_PHASE_III])


@api_view(['GET'])
@login_required(login_url='/login/')
def games_cnt_by_user(request, user_id):
    cnt = Game.objects.filter(user_id=user_id).count()
    return Response(cnt)


@api_view(['GET'])
@login_required(login_url='/login/')
def games_cnt(request):
    queryset = Game.objects.values('user__id').annotate(cnt=Count('id')).order_by('-cnt')[:5]
    return JsonResponse(list(queryset), safe=False)


# deprecated
@api_view(['GET'])
@login_required(login_url='/login/')
def match_patient(request):
    cnt = Patient.objects.all().count()
    # no patient yet, generate two and return
    if cnt == 0:
        pt1 = do_gen_patient()
        pt2 = do_gen_patient()
        return serialize_match(pt1, pt2)
    elif cnt == 1:
        pt1 = do_gen_patient()
        pt2 = Patient.objects.first()
        return serialize_match(pt1, pt2)
    #  2 or more existing patients
    else:
        # iterate phase i patients
        pt1, pt2 = get_pts_from_f1_f2(STATUS_PHASE_I)
        if pt1 is not None and pt2 is not None:
            return serialize_match(pt1, pt2)
        else:
            # iterate PHASE II patients
            pt1, pt2 = get_pts_from_f1_f2(STATUS_PHASE_II)
            if pt1 is not None and pt2 is not None:
                return serialize_match(pt1, pt2)
            else:
                # # do phase III: diffusion. All phase III nodes will be updated to EXISTING
                do_diffusion()
                # should only have EXISTING caseS, generate PHASE I and get random from EXISTING
                pt1 = do_gen_patient()
                pt2 = Patient.objects.filter(status=STATUS_EXISTING).order_by('?').first()
                # return serialize_match(pt1, pt2)
                return serialize_match(pt1, pt2)


def do_gen_patient():
    domains = Domain.objects.all()
    domain_dict = {}

    for d in domains:
        serializer = DomainSerializer(d)
        domain_dict[d.id] = serializer.data

    choice_dict = {}

    for i in domain_dict:
        domain = domain_dict[i]
        p_none = Decimal(domain.get('probability_without_entry'))
        domain_name = domain.get('domain_name')
        categories = [d['category_name'] for d in domain.get('categories')]
        # print(categories)
        no_of_cat = len(categories)
        categories.append(None)
        p_rest = float(round((1 - p_none) / no_of_cat, 2))
        p_tuple = (p_rest,) * no_of_cat
        # print(p_tuple)
        p_tuple = p_tuple + (float(p_none),)
        choices = random.choices(categories, weights=p_tuple, k=1)
        if choices is not None:
            # choice = (domain_name + ": " if domain_name is not None else "") \
            #          + choices[0] if choices[0] is not None else ""
            choice = choices[0] if choices[0] is not None else ""
        else:
            choice = None
        choice_dict['domain' + str(i)] = choice
    db_pt = Patient.objects.filter(**choice_dict)
    # case doesn't exist, create new
    if len(db_pt) == 0:
        choice_dict['status'] = STATUS_PHASE_I
        choice_dict['status_date'] = timezone.now()
        choice_dict['current_ranking'] = ELO_DEFAULT_RANKING
        db_pt = Patient.objects.create(**choice_dict)
        return db_pt
    # otherwise try again
    else:
        return do_gen_patient()


# if player.status = PHASE I, check number of games played where other player is in PHASE II
# if player.status = PHASE II, check number of games played where other player is in PHASE III
def has_enough_games(patient):
    pts_cnt = Patient.objects.count()
    next_status = get_next_status(patient.status)
    pts_against = Game.objects.filter(Q(player1=patient.id) & Q(player2__status=next_status)
                                      | Q(player2=patient.id) & Q(player1__status=next_status))
    # print(f"inside has_enough_games: {pts_against.query}")
    if pts_against.count() <= math.log(pts_cnt, 2):
        return False
    return True


def get_next_status(status):
    if status == STATUS_PHASE_I:
        return STATUS_PHASE_II
    elif status == STATUS_PHASE_II:
        return STATUS_PHASE_III
    elif status == STATUS_PHASE_III:
        return STATUS_EXISTING
    else:
        return None


def get_pts_from_f1_f2(phase):
    next_phase = get_next_status(phase)
    played_games = Game.objects.filter((Q(player1__status=phase) & Q(player2__status=next_phase))
                                       | (Q(player2__status=phase) & Q(player1__status=next_phase)))
    # print(f"played_games query: {played_games.query}")
    # phase I or phase II has started playing games, get those cases first
    if played_games.exists():
        for g in played_games:
            if g.player1.status == phase:
                pt1 = g.player1
            elif g.player2.status == phase:
                pt1 = g.player2
            if pt1 is not None:
                pt2 = get_opponent(pt1, phase)
            if pt1 is not None and pt2 is not None:
                if pt1.status != STATUS_PHASE_I and pt1.status != STATUS_PHASE_II:
                    logger.error("pt1 status issue")
                return pt1, pt2
    # no games has been played among cases in the current phase
    pts_in_phase = Patient.objects.filter(status=phase)
    for pt1 in pts_in_phase:
        pt2 = get_opponent(pt1, phase)
        if pt1 is not None and pt2 is not None:
            return pt1, pt2
    return None, None


def get_opponent(pt1, phase):
    # can play with existing or cases in the same phase
    enough_games = has_enough_games(pt1)
    pt2 = None
    if not enough_games:
        pts_can_against = Patient.objects.filter((Q(status='EXISTING') | Q(status=phase)) & ~Q(id=pt1.id)).order_by('?')
        if pts_can_against:
            pt2 = pts_can_against.first()
    return pt2


def do_diffusion():
    pts_p3 = Patient.objects.filter(Q(status=STATUS_PHASE_III) | (Q(status=STATUS_EXISTING) & Q(is_playing='2')))
    pts_others = Patient.objects.exclude(id__in=pts_p3.values_list('id', flat=True))
    # for each patient in PHASE III, update all existing nodes based on PHASE III algorithm
    # once each PHASE III is done, update all nodes to be EXISTING
    # as a result, the same node will be calculated multiple times.
    for pt1 in pts_p3:
        # diffuse to other cases
        # for pt2 in pts_others:
        #     None
        pt1.status = STATUS_EXISTING
        pt1.is_playing = None
        pt1.save()


def serialize_match(pt1, pt2):
    if pt1.status != STATUS_PHASE_I and pt1.status != STATUS_PHASE_II:
        logger.error(f"pt1 not in correct status")
    serializer_pt1 = PatientSerializer(pt1)
    serializer_pt2 = PatientSerializer(pt2)
    return Response([serializer_pt1.data, serializer_pt2.data])


def serialize_game(game):
    return Response(GameSerializer(game, partial=True).data)


# for each patient, get all games without ranking assigned
# if games count >= log2n, calculate ranking per game
# for opponent, update ranking
# for node in focus, accumulate ranking, and update both game and patient at the end
def do_ranking_calculation(pt, last_game):
    game_total = Game.objects.count()
    games = Game.objects \
        .filter(Q(post_game_ranking1__isnull=True) | Q(post_game_ranking2__isnull=True)) \
        .filter(Q(player1=pt.id) | Q(player2=pt.id))
    # print(games.query)
    game_cnt = games.count()
    # if game_cnt < math.log(2, game_total):
    #     return
    k_factor = 20 / (game_cnt if game_cnt > 0 else 1) + 3
    pt_score_change = 0
    for game in games:
        prob1 = 1 / (1 + math.pow(10, (game.pre_game_ranking2 - game.pre_game_ranking1) / 400))
        prob2 = 1 / (1 + math.pow(10, (game.pre_game_ranking1 - game.pre_game_ranking2) / 400))
        score_change1 = k_factor * (float(game.result) - prob1)
        score_change2 = k_factor * (float(game.result) - prob2)
        # pt == player1
        if game.player1.id == pt.id:
            pt_score_change = pt_score_change + score_change1
            pt2 = game.player2
            # save pt2 ranking after each game
            game.post_game_ranking2 = game.pre_game_ranking2 + score_change2
            game.save()
            pt2.current_ranking = game.post_game_ranking2
            pt2.latest_game_id = game.id
            pt2.save()
        # pt == player2
        if game.player2.id == pt.id:
            pt_score_change = pt_score_change + score_change2
            pt2 = game.player1
            # save pt2 ranking after each game
            game.post_game_ranking1 = game.pre_game_ranking1 + score_change1
            game.save()
            pt2.current_ranking = game.post_game_ranking1
            pt2.latest_game_id = game.id
            pt2.save()
    # after all games, calculate pt ranking and update pt and game
    pt.current_ranking = pt.current_ranking if pt.current_ranking is not None else 0 + pt_score_change
    pt.last_game_id = last_game.id
    pt.save()
    Game.objects.filter(player1=pt).update(post_game_ranking1=pt.current_ranking)
    Game.objects.filter(player2=pt).update(post_game_ranking2=pt.current_ranking)


# save ranking in game without accumulating
# update patient current ranking with accumulated value
def do_ranking_calculation2(pt, last_game):
    game_total = Game.objects.count()
    games = Game.objects \
        .filter(Q(post_game_ranking1__isnull=True) | Q(post_game_ranking2__isnull=True)) \
        .filter(Q(player1=pt.id) | Q(player2=pt.id))
    # print(games.query)
    game_cnt = games.count()
    # if game_cnt < math.log(2, game_total):
    #     return
    if game_cnt > 0:
        k_factor = 20 / game_cnt + 3
        pt_score_change = 0
        for game in games:
            prob1 = 1 / (1 + math.pow(10, (game.pre_game_ranking2 - game.pre_game_ranking1) / 400))
            prob2 = 1 / (1 + math.pow(10, (game.pre_game_ranking1 - game.pre_game_ranking2) / 400))
            score_change1 = k_factor * (float(game.result) - prob1)
            score_change2 = k_factor * (abs(float(game.result) - 1) - prob2)
            game.post_game_ranking1 = game.pre_game_ranking1 + score_change1
            game.post_game_ranking2 = game.pre_game_ranking2 + score_change2
            game.save()
            # pt == player1
            if game.player1.id == pt.id:
                pt_score_change = pt_score_change + score_change1
                pt2 = game.player2
                # save pt2 ranking after each game
                pt2.current_ranking = game.post_game_ranking2
                pt2.latest_game_id = game.id
                pt2.save()
            # pt == player2
            if game.player2.id == pt.id:
                pt_score_change = pt_score_change + score_change2
                pt2 = game.player1
                # save pt2 ranking after each game
                pt2.current_ranking = game.post_game_ranking1
                pt2.latest_game_id = game.id
                pt2.save()
        # after all games, calculate pt ranking and update pt and game
        pt.current_ranking = (pt.current_ranking if pt.current_ranking is not None else 0) + pt_score_change
        pt.last_game_id = last_game.id
        pt.save()


def do_ranking_calculation3(game):
    prob1 = 1 / (1 + math.pow(10, (game.pre_game_ranking2 - game.pre_game_ranking1) / 400))
    prob2 = 1 / (1 + math.pow(10, (game.pre_game_ranking1 - game.pre_game_ranking2) / 400))
    score_change1 = K_FACTOR * (float(game.result) - prob1)
    score_change2 = K_FACTOR * (abs(float(game.result) - 1) - prob2)
    game.post_game_ranking1 = game.pre_game_ranking1 + score_change1
    game.post_game_ranking2 = game.pre_game_ranking2 + score_change2
    game.save()
    pt1 = game.player1
    pt2 = game.player2
    pts_cnt = Patient.objects.count()
    if pts_cnt == 2:
        pt1.status = STATUS_EXISTING
        pt2.status = STATUS_EXISTING
    # if pt1 == PHASE I, opponent can be existing or phase I, change to PHASE II
    elif pt1.status == STATUS_PHASE_I:
        if has_enough_games(pt1):
            pt1.status = STATUS_PHASE_III
        pt2.status = STATUS_PHASE_II
    # if pt1 = PHASE II, opponent can be PHASE II or PHASE III
    elif pt1.status == STATUS_PHASE_II:
        if has_enough_games(pt1):
            pt1.status = STATUS_PHASE_III
        pt2.status = STATUS_PHASE_III
    else:
        logger.error(f"Players are not in the correct status: {game.player1.status} : {game.player2.status}")
    pt1.current_ranking = game.post_game_ranking1
    pt1.latest_game_id = game.id
    pt1.save()
    pt2.current_ranking = game.post_game_ranking2
    pt2.latest_game_id = game.id
    pt2.save()


@transaction.atomic
def do_ranking_calculation4(game):
    prob1 = 1 / (1 + math.pow(10, (game.pre_game_ranking2 - game.pre_game_ranking1) / 400))
    prob2 = 1 / (1 + math.pow(10, (game.pre_game_ranking1 - game.pre_game_ranking2) / 400))
    batch_cnt = 1 if game.batch_cnt is None else game.batch_cnt
    k_factor = int(round(20/batch_cnt + 3))
    logger.info('k_factor: %s' %  (k_factor))
    score_change1 = k_factor * (float(game.result) - prob1)
    score_change2 = k_factor * (abs(float(game.result) - 1) - prob2)
    game.post_game_ranking1 = game.pre_game_ranking1 + score_change1
    game.post_game_ranking2 = game.pre_game_ranking2 + score_change2
    game.k_factor = k_factor
    game.status_date = timezone.now()
    game.save()
    # post game status update
    pt1 = game.player1
    pt2 = game.player2
    if pt2.status == STATUS_EXISTING:
        if game.status == STATUS_PHASE_I:
            pt2.status = STATUS_PHASE_II
        elif game.status == STATUS_PHASE_II:
            pt2.status = STATUS_PHASE_III
    # promote playing cases if all pre-gen games are finished
    if pt1.is_playing == '1':
        cnt = Game.objects.filter(player1=pt1, post_game_ranking1__isnull=True).count()
        if cnt == 0:
            pt1.is_playing = None
            pt1.status = STATUS_PHASE_III
    pt1.current_ranking = game.post_game_ranking1
    pt1.latest_game_id = game.id
    pt1.status_date = timezone.now()
    pt1.save()
    pt2.current_ranking = game.post_game_ranking2
    pt2.latest_game_id = game.id
    pt2.status_date = timezone.now()
    pt2.save()


def update_patient_ranking(self, patient_id, ranking, game):
    cursor = connection.cursor()
    cursor.execute("update test_patient set current_ranking=%s, latest_game_id=%s where id=%s",
                   [ranking, game.id, patient_id])
    row = cursor.fetchall()
    return row
