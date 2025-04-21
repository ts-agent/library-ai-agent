import argparse
import logging
from interpark_crawler import InterparkCrawler

def setup_logging():
    """로깅 설정을 초기화합니다."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='인터파크 도서 리뷰 크롤러')
    parser.add_argument('url', help='도서 URL')
    parser.add_argument('-o', '--output', help='저장할 파일 경로', default='reviews.json')
    
    args = parser.parse_args()
    
    setup_logging()
    crawler = InterparkCrawler()
    
    reviews = crawler.get_reviews(args.url)
    if reviews:
        crawler.save_reviews(reviews, args.output)

if __name__ == '__main__':
    main() 