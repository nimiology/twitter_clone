import pytz
from django.db.models import Case, When, Value
from django.forms import BooleanField
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView, get_object_or_404, \
    RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from art.models import Artist
from art.serializers import FollowingArtistSerializer
from artist.serializers import ArtistSerializer
from notification.models import Notification
from users.serializers import MyUserSerializer, FollowingUserSerializer
from users.models import MyUser


class UserSearch(ListAPIView):
    serializer_class = FollowingUserSerializer
    filterset_fields = {'first_name': ['icontains'],
                        'username': ['icontains'],
                        }
    ordering_fields = [
        'id',
        'username',
        'first_name',
        'verify',
        'date_joined'
        'following',
    ]

    def get_queryset(self):
        queryset = MyUser.objects.all()
        user = self.request.user

        # Add a boolean field 'following' to each user in the queryset based on whether the current user follows them or not
        if user.is_authenticated:
            queryset = queryset.annotate(
                following=Case(When(followers=user, then=Value(True)), default=Value(False)))

            # Order the queryset so that users with 'following=True' come first
            queryset = queryset.order_by('-following')

        return queryset


class GetUser(RetrieveAPIView):
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.all()
    lookup_field = 'username'


class FollowUserAPI(GenericAPIView):
    serializer_class = FollowingUserSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        profile = request.user
        username = kwargs['username']
        following = get_object_or_404(MyUser, username=username)
        if following != profile:
            user_following = profile.followings.all()
            if following in user_following:
                profile.followings.remove(following)
            else:
                profile.followings.add(following)
                Notification.objects.create(owner=following,
                                            type='f',
                                            object_id=profile.username)
            return Response(self.get_serializer(following).data)

        else:
            raise ValidationError('You cant follow yourself')


class FollowArtistAPI(GenericAPIView):
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        profile = request.user
        pk = kwargs['pk']
        following = get_object_or_404(Artist, pk=pk)
        user_artist_following = profile.following_artists.all()
        if following in user_artist_following:
            profile.following_artists.remove(following)
        else:
            profile.following_artists.add(following)
        return Response(self.get_serializer(following).data)


class FollowingAPI(ListAPIView):
    serializer_class = FollowingUserSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(MyUser, username=username)
        followings = profile.followings.all()
        return followings


class FollowersAPI(ListAPIView):
    serializer_class = FollowingUserSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(MyUser, username=username)
        followings = MyUser.objects.filter(followings__in=[profile])
        return followings


class ArtistFollowingAPI(ListAPIView):
    serializer_class = FollowingArtistSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        profile = get_object_or_404(MyUser, username=username)
        followings = profile.following_artists.all()
        return followings


class MyUsersAPI(RetrieveUpdateAPIView):
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.all()
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


timezones = [{'id': str(number), 'timezone': pytz.all_timezones[number]} for number in
             range(0, len(pytz.all_timezones))]


class GetAllTimeZonesAPI(APIView):
    def get(self, request, *args, **kwargs):
        return Response(timezones)