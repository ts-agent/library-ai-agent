from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import date, timedelta
from django.urls import reverse
from .models import (
    Performance, SeatGrade, Actor, Casting, Review,
    SalesData, SettlementData, MarketingCalendar,
    MarketingEvent, CrawlingTarget
)
import json

class PerformanceTests(TestCase):
    def setUp(self):
        self.performance_data = {
            'name': '테스트 공연',
            'venue': '테스트 공연장',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31),
            'age_limit': '전체관람가',
            'running_time': '120분'
        }

    def test_performance_crud(self):
        # Create
        performance = Performance.objects.create(**self.performance_data)
        self.assertEqual(performance.name, '테스트 공연')

        # Read
        saved_performance = Performance.objects.get(id=performance.id)
        self.assertEqual(saved_performance.venue, '테스트 공연장')

        # Update
        performance.name = '수정된 공연명'
        performance.save()
        updated_performance = Performance.objects.get(id=performance.id)
        self.assertEqual(updated_performance.name, '수정된 공연명')

        # Delete
        performance.delete()
        self.assertEqual(Performance.objects.count(), 0)

class SeatGradeTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.seat_grade_data = {
            'performance': self.performance,
            'name': 'VIP',
            'price': 100000
        }

    def test_seat_grade_crud(self):
        # Create
        seat_grade = SeatGrade.objects.create(**self.seat_grade_data)
        self.assertEqual(seat_grade.name, 'VIP')

        # Read
        saved_seat_grade = SeatGrade.objects.get(id=seat_grade.id)
        self.assertEqual(saved_seat_grade.price, 100000)

        # Update
        seat_grade.price = 120000
        seat_grade.save()
        updated_seat_grade = SeatGrade.objects.get(id=seat_grade.id)
        self.assertEqual(updated_seat_grade.price, 120000)

        # Delete
        seat_grade.delete()
        self.assertEqual(SeatGrade.objects.count(), 0)

class ActorTests(TestCase):
    def setUp(self):
        self.actor_data = {
            'name': '홍길동'
        }

    def test_actor_crud(self):
        # Create
        actor = Actor.objects.create(**self.actor_data)
        self.assertEqual(actor.name, '홍길동')

        # Read
        saved_actor = Actor.objects.get(id=actor.id)
        self.assertEqual(saved_actor.name, '홍길동')

        # Update
        actor.name = '김철수'
        actor.save()
        updated_actor = Actor.objects.get(id=actor.id)
        self.assertEqual(updated_actor.name, '김철수')

        # Delete
        actor.delete()
        self.assertEqual(Actor.objects.count(), 0)

class CastingTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.actor = Actor.objects.create(name='홍길동')
        self.casting_data = {
            'performance': self.performance,
            'actor': self.actor,
            'role_name': '주인공'
        }

    def test_casting_crud(self):
        # Create
        casting = Casting.objects.create(**self.casting_data)
        self.assertEqual(casting.role_name, '주인공')

        # Read
        saved_casting = Casting.objects.get(id=casting.id)
        self.assertEqual(saved_casting.actor.name, '홍길동')

        # Update
        casting.role_name = '조연'
        casting.save()
        updated_casting = Casting.objects.get(id=casting.id)
        self.assertEqual(updated_casting.role_name, '조연')

        # Delete
        casting.delete()
        self.assertEqual(Casting.objects.count(), 0)

class ReviewTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.review_data = {
            'performance': self.performance,
            'rating': 5,
            'title': '최고의 공연',
            'content': '정말 재미있었습니다.',
            'nickname': '관객1',
            'sentiment': 'positive'
        }

    def test_review_crud(self):
        # Create
        review = Review.objects.create(**self.review_data)
        self.assertEqual(review.title, '최고의 공연')

        # Read
        saved_review = Review.objects.get(id=review.id)
        self.assertEqual(saved_review.rating, 5)

        # Update
        review.rating = 4
        review.save()
        updated_review = Review.objects.get(id=review.id)
        self.assertEqual(updated_review.rating, 4)

        # Delete
        review.delete()
        self.assertEqual(Review.objects.count(), 0)

class SalesDataTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.test_file = SimpleUploadedFile(
            "test_sales.csv",
            b"file_content",
            content_type="text/csv"
        )
        self.sales_data = {
            'performance': self.performance,
            'file': self.test_file,
            'description': '1월 판매현황'
        }

    def test_sales_data_crud(self):
        # Create
        sales_data = SalesData.objects.create(**self.sales_data)
        self.assertEqual(sales_data.description, '1월 판매현황')

        # Read
        saved_sales_data = SalesData.objects.get(id=sales_data.id)
        self.assertEqual(saved_sales_data.description, '1월 판매현황')

        # Update
        sales_data.description = '2월 판매현황'
        sales_data.save()
        updated_sales_data = SalesData.objects.get(id=sales_data.id)
        self.assertEqual(updated_sales_data.description, '2월 판매현황')

        # Delete
        sales_data.delete()
        self.assertEqual(SalesData.objects.count(), 0)

class MarketingCalendarTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.calendar_data = {
            'performance': self.performance,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 12, 31)
        }

    def test_marketing_calendar_crud(self):
        # Create
        calendar = MarketingCalendar.objects.create(**self.calendar_data)
        self.assertEqual(calendar.performance.name, '테스트 공연')

        # Read
        saved_calendar = MarketingCalendar.objects.get(id=calendar.id)
        self.assertEqual(saved_calendar.start_date, date(2025, 1, 1))

        # Update
        calendar.end_date = date(2026, 1, 1)
        calendar.save()
        updated_calendar = MarketingCalendar.objects.get(id=calendar.id)
        self.assertEqual(updated_calendar.end_date, date(2026, 1, 1))

        # Delete
        calendar.delete()
        self.assertEqual(MarketingCalendar.objects.count(), 0)

class MarketingEventTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.calendar = MarketingCalendar.objects.create(
            performance=self.performance,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        self.event_data = {
            'calendar': self.calendar,
            'start_date': date(2025, 2, 1),
            'end_date': date(2025, 2, 28),
            'title': '온라인 이벤트',
            'description': '인스타그램 이벤트',
            'tag': '이벤트',
            'color': '#FF0000'
        }

    def test_marketing_event_crud(self):
        # Create
        event = MarketingEvent.objects.create(**self.event_data)
        self.assertEqual(event.title, '온라인 이벤트')

        # Read
        saved_event = MarketingEvent.objects.get(id=event.id)
        self.assertEqual(saved_event.tag, '이벤트')

        # Update
        event.title = '수정된 이벤트'
        event.save()
        updated_event = MarketingEvent.objects.get(id=event.id)
        self.assertEqual(updated_event.title, '수정된 이벤트')

        # Delete
        event.delete()
        self.assertEqual(MarketingEvent.objects.count(), 0)

class CrawlingTargetTests(TestCase):
    def setUp(self):
        self.performance = Performance.objects.create(
            name='테스트 공연',
            venue='테스트 공연장',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            age_limit='전체관람가'
        )
        self.target_data = {
            'performance': self.performance,
            'platform': '인터파크티켓',
            'url': 'https://tickets.interpark.com/test',
            'is_active': True
        }

    def test_crawling_target_crud(self):
        # Create
        target = CrawlingTarget.objects.create(**self.target_data)
        self.assertEqual(target.platform, '인터파크티켓')

        # Read
        saved_target = CrawlingTarget.objects.get(id=target.id)
        self.assertEqual(saved_target.url, 'https://tickets.interpark.com/test')

        # Update
        target.is_active = False
        target.save()
        updated_target = CrawlingTarget.objects.get(id=target.id)
        self.assertEqual(updated_target.is_active, False)

        # Delete
        target.delete()
        self.assertEqual(CrawlingTarget.objects.count(), 0)

class CrawlingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_target = CrawlingTarget.objects.create(
            platform='nol_ticket',
            url='https://www.nolticket.com/test',
            title='테스트 공연',
            description='테스트 설명'
        )

    def test_add_crawling_target(self):
        url = reverse('add_crawling_target')
        data = {
            'platform': 'youtube',
            'url': 'https://www.youtube.com/watch?v=test'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CrawlingTarget.objects.filter(url=data['url']).exists())

    def test_update_crawling_target(self):
        url = reverse('update_crawling_target', args=[self.test_target.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        updated_target = CrawlingTarget.objects.get(id=self.test_target.id)
        self.assertIsNotNone(updated_target.last_crawled)

    def test_invalid_platform(self):
        url = reverse('add_crawling_target')
        data = {
            'platform': 'invalid_platform',
            'url': 'https://example.com'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_url(self):
        url = reverse('add_crawling_target')
        data = {
            'platform': 'youtube'
        }
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
