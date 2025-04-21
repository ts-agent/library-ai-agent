from django.core.management.base import BaseCommand
from data_analysis.utils.interpark_crawler import crawl_interpark_reviews
import os

class Command(BaseCommand):
    help = '인터파크 공연의 리뷰를 크롤링합니다.'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help='크롤링할 인터파크 공연 URL')
        parser.add_argument('--output', type=str, help='결과를 저장할 JSON 파일 경로', 
                          default='reviews.json')

    def handle(self, *args, **options):
        url = options['url']
        output_file = options['output']

        self.stdout.write(f"크롤링 시작: {url}")
        reviews = crawl_interpark_reviews(url, output_file)
        self.stdout.write(f"크롤링 완료: {len(reviews)}개의 리뷰가 {output_file}에 저장되었습니다.") 