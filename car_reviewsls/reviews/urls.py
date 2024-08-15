from django.urls import path
from .views import ReviewList, PositiveChevroletReviews, PositiveToyotaReviews, PositiveVolkswagenReviews, NegativeChevroletReviews, NegativeToyotaReviews, NegativeVolkswagenReviews, chevroletReviews, toyotaReviews, volkswagenReviews, NonSpecificVolkswagenReviews, NonSpecificToyotaReviews, NonSpecificChevroletReviews

urlpatterns = [
    path('reviews/', ReviewList.as_view(), name='review-list'),
    path('reviews/positiveChevrolet/', PositiveChevroletReviews.as_view(), name='positive-chevrolet-reviews'),
    path('reviews/positiveToyota/', PositiveToyotaReviews.as_view(), name='positive-toyota-reviews'),
    path('reviews/positiveVolkswagen/', PositiveVolkswagenReviews.as_view(), name='positive-volkswagen-reviews'),
    path('reviews/negativeChevrolet/', NegativeChevroletReviews.as_view(), name='negative-chevrolet-reviews'),
    path('reviews/negativeToyota/', NegativeToyotaReviews.as_view(), name='negative-toyota-reviews'),
    path('reviews/negativeVolkswagen/', NegativeVolkswagenReviews.as_view(), name='negative-volkswagen-reviews'),
    path('reviews/chevrolet/', chevroletReviews.as_view(), name='chevrolet-reviews'),
    path('reviews/toyota/', toyotaReviews.as_view(), name='toyota-reviews'),
    path('reviews/volkswagen/', volkswagenReviews.as_view(), name='volkswagen-reviews'),
    path('reviews/nonSpecificReviewsChevrolet/', NonSpecificChevroletReviews.as_view(), name='Non-specific-chevrolet-reviews'),
    path('reviews/nonSpecificReviewsToyota/', NonSpecificToyotaReviews.as_view(), name='Non-specific-toyota-reviews'),
    path('reviews/nonSpecificReviewsVolkswagen/', NonSpecificVolkswagenReviews.as_view(), name='Non-specific-volkswagen-reviews'),
]
