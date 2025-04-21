from utils.interpark_crawler import InterparkCrawler

def main():
    # 크롤링할 인터파크 도서 URL
    url = "https://book.interpark.com/product/BookDisplay.do?_method=detail&sc.prdNo=355301712"
    
    # 크롤러 인스턴스 생성
    crawler = InterparkCrawler()
    
    # 리뷰 크롤링 실행
    print("리뷰 크롤링을 시작합니다...")
    reviews = crawler.crawl_reviews(url)
    
    # 결과 저장
    if reviews:
        output_file = "data/interpark_reviews.json"
        crawler.save_reviews(reviews, output_file)
    else:
        print("크롤링된 리뷰가 없습니다.")

if __name__ == "__main__":
    main() 