import json
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict, Optional

class InterparkCrawler:
    """인터파크 도서 리뷰 크롤러 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        self.logger = logging.getLogger(__name__)

    def get_reviews(self, url: str) -> List[Dict]:
        """
        주어진 URL에서 도서 리뷰를 수집합니다.
        
        Args:
            url (str): 인터파크 도서 상세 페이지 URL
            
        Returns:
            List[Dict]: 수집된 리뷰 목록
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            review_elements = soup.select('div.reviewList')
            
            reviews = []
            for element in review_elements:
                review = {
                    'content': element.select_one('div.reviewContent').text.strip(),
                    'rating': float(element.select_one('div.reviewScore img')['alt'].split()[0]),
                    'date': element.select_one('div.reviewDate').text.strip(),
                    'author': element.select_one('div.reviewId').text.strip()
                }
                reviews.append(review)
                
            return reviews
            
        except requests.RequestException as e:
            self.logger.error(f"리뷰 수집 중 오류 발생: {str(e)}")
            return []
            
    def save_reviews(self, reviews: List[Dict], output_file: str) -> bool:
        """
        수집된 리뷰를 JSON 파일로 저장합니다.
        
        Args:
            reviews (List[Dict]): 저장할 리뷰 목록
            output_file (str): 저장할 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            self.logger.info(f"리뷰가 성공적으로 저장되었습니다: {output_file}")
            return True
            
        except IOError as e:
            self.logger.error(f"리뷰 저장 중 오류 발생: {str(e)}")
            return False

def crawl_interpark_reviews(url, output_file):
    crawler = InterparkCrawler()
    reviews = crawler.get_reviews(url)
    crawler.save_reviews(reviews, output_file)
    return reviews 