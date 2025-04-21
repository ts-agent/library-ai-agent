import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

class InterparkCrawler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

    def get_reviews(self, url: str) -> List[Dict[str, Any]]:
        """
        인터파크 도서의 리뷰를 수집합니다.
        
        Args:
            url (str): 도서 URL
            
        Returns:
            List[Dict[str, Any]]: 수집된 리뷰 목록
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            reviews = []
            
            review_elements = soup.select('.reviewList')
            
            for element in review_elements:
                review = {
                    'content': element.select_one('.reviewContent').text.strip(),
                    'rating': float(element.select_one('.reviewRating').text.strip()),
                    'date': element.select_one('.reviewDate').text.strip(),
                    'author': element.select_one('.reviewAuthor').text.strip()
                }
                reviews.append(review)
                
            self.logger.info(f"{len(reviews)}개의 리뷰를 수집했습니다.")
            return reviews
            
        except requests.RequestException as e:
            self.logger.error(f"리뷰 수집 중 오류 발생: {str(e)}")
            return []
            
    def save_reviews(self, reviews: List[Dict[str, Any]], output_path: str) -> bool:
        """
        수집된 리뷰를 JSON 파일로 저장합니다.
        
        Args:
            reviews (List[Dict[str, Any]]): 저장할 리뷰 목록
            output_path (str): 저장할 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            self.logger.info(f"리뷰가 {output_path}에 저장되었습니다.")
            return True
        except Exception as e:
            self.logger.error(f"리뷰 저장 중 오류 발생: {str(e)}")
            return False 