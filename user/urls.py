from django.urls import path
from .views import *
from account_app.views import GoogleLogin,FacebookLogin

urlpatterns =  [
    path('auth/signup',SignUpView.as_view(),name='signup'),
    path('auth/google/', GoogleLogin.as_view(), name='google-login'),
    path('auth/facebook/', FacebookLogin.as_view(), name='facebook-login'),
    path('auth/verifyotp',UserVerifyOtpView.as_view(),name='verifyotp'),
    path('auth/resendotp',UserResendOtpView.as_view(),name='resendotp'),
    path('auth/login',LoginView.as_view(),name='login'),
    path("auth/refresh-token", UserTokenRefreshView.as_view(), name="user_token_refresh"),
    path('forgot-password/',UserForgotPasswordView.as_view(),name='user-forgot-password'),
    path('reset-password/',UserResetPasswordView.as_view(),name='reset-password'),
    path('profile/',UserProfileView.as_view(),name='profile'),
    path('profile/edit/', UserProfileEditView.as_view(), name='edit-user-profile'),
    path('trainers/available/', AvailableTrainerAPIView.as_view(), name='available-trainers'),
    path('trainers/<int:trainer_id>/courses/', TrainerCoursesAPIView.as_view(), name='trainer-courses'),
    path('courses/<int:course_id>/', CourseDetailAPIView.as_view(), name='course-detail'),
    path('stadiums/nearby/', NearbyStadiumsAPIView.as_view(), name='nearby_stadiums_api'),
    path('stadiums/<int:pk>/', StadiumDetailAPIView.as_view(), name='stadium-detail'),
    path('stadiums/<int:stadium_id>/available-slots/', AvailableUpcomingSlotsAPIView.as_view(), name='available_slots'),
    path('stadiums/<int:stadium_id>/slots/book/', BookSlotsAPIView.as_view(), name='book_slots'),
    path('logout/',UserLogoutView.as_view()),
    path('live-sessions/', UserLiveSessionsView.as_view(), name='user-live-sessions'),
    path('sessions/<int:session_id>/join/', UserJoinSessionView.as_view(), name='user-join-session'),
    path('enrolled-courses/', UserEnrolledCoursesView.as_view(), name='user-enrolled-courses'),
    path('enrolled-courses/<int:id>/cancel/', CancelCourseEnrollmentView.as_view(), name='cancel-course-enrollment'),
    path('past-courses/', PastCoursesView.as_view(), name='past-courses'),
    path('upcoming-slots/', UserUpcomingSlotBookingsAPI.as_view(), name='user-upcoming-slot-bookings'),
    path('current-next/', UserCurrentAndNextSlotBookingsAPI.as_view(), name='user-current-next-slots'),
    path('slots/past/', UserPastSlotBookingsAPI.as_view(), name='user-past-slots'),
    path('bookings/<int:booking_id>/cancel/', CancelSlotBookingView.as_view(), name='cancel-slot-booking'),
]