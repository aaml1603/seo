import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os 
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI


class SEOAnalyzer:
    """
    Professional SEO Analysis System
    
    Combines AI-powered website analysis with real-time search volume data
    to provide comprehensive keyword insights and SEO recommendations.
    
    Features:
    - Website content extraction and analysis
    - AI-powered keyword generation using OpenAI GPT
    - Real-time search volume data from DataForSEO
    - Advanced SEO metrics calculation
    - Professional reporting and insights
    
    Attributes:
        website_url (str): Target website URL for analysis
        openai_client (OpenAI): OpenAI API client instance
        dataforseo_client (RestClient): DataForSEO API client instance
    """

    def __init__(self):
        """
        Initialize the SEO Analyzer with API credentials and configuration.
        
        Loads environment variables and sets up API clients for OpenAI and DataForSEO.
        Validates credentials and initializes logging.
        
        Raises:
            ValueError: If required API credentials are missing
            ConnectionError: If API clients cannot be initialized
        """
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Load environment configuration
        load_dotenv()
        self._load_configuration()
        
        # Initialize API clients
        self._initialize_openai_client()
        self._initialize_dataforseo_client()
        
        self.logger.info("SEO Analyzer initialized successfully")
    
    def _load_configuration(self) -> None:
        """Load and validate environment configuration."""
        self.website_url = os.getenv("SAAS_URL")
        self.openai_api_key = os.getenv("OPENAI_KEY")
        self.dataforseo_login = os.getenv("DATAFORSEO_LOGIN")
        self.dataforseo_password = os.getenv("DATAFORSEO_PASSWORD")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_KEY in your .env file.")
        
        if not self.website_url:
            self.logger.warning("No website URL provided. Set SAAS_URL in your .env file.")
    
    def _initialize_openai_client(self) -> None:
        """Initialize OpenAI client with error handling."""
        try:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise ConnectionError(f"OpenAI initialization failed: {str(e)}")
    
    def _initialize_dataforseo_client(self) -> None:
        """Initialize DataForSEO client with error handling."""
        if self.dataforseo_login and self.dataforseo_password:
            try:
                from client import RestClient
                self.dataforseo_client = RestClient(self.dataforseo_login, self.dataforseo_password)
                self.logger.info("DataForSEO client initialized successfully")
            except Exception as e:
                self.logger.warning(f"DataForSEO client initialization failed: {str(e)}")
                self.dataforseo_client = None
        else:
            self.logger.warning("DataForSEO credentials not provided. Search volume data will be unavailable.")
            self.dataforseo_client = None

    def extract_website_content(self, url: Optional[str] = None) -> str:
        """
        Extract and clean text content from a website.
        
        Args:
            url (Optional[str]): Website URL to analyze. Uses configured URL if not provided.
            
        Returns:
            str: Cleaned text content from the website
            
        Raises:
            requests.RequestException: If website cannot be accessed
            ValueError: If no URL is provided or configured
        """
        target_url = url or self.website_url
        if not target_url:
            raise ValueError("No URL provided for content extraction")
        
        try:
            self.logger.info(f"Extracting content from: {target_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(target_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Extract and clean text content
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_content = ' '.join(chunk for chunk in chunks if chunk)
            
            self.logger.info(f"Successfully extracted {len(cleaned_content)} characters of content")
            return cleaned_content
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch website content: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Content extraction failed: {str(e)}")
            raise

    def fetch_search_volume_data(self, keywords: List[str], location_code: int = 2840, 
                                date_from: str = "2021-08-01") -> Optional[Dict[str, Any]]:
        """
        Fetch search volume data for keywords using DataForSEO API.
        
        Args:
            keywords (List[str]): List of keywords to analyze
            location_code (int): Geographic location code (default: 2840 for USA)
            date_from (str): Start date for historical data
            
        Returns:
            Optional[Dict[str, Any]]: Search volume data or None if unavailable
        """
        if not self.dataforseo_client:
            self.logger.warning("DataForSEO client not available - search volume data unavailable")
            return None
            
        post_data = {
            0: {
                "location_code": location_code,
                "keywords": keywords,
                "date_from": date_from,
                "search_partners": True
            }
        }
        
        try:
            self.logger.info(f"Fetching search volume data for {len(keywords)} keywords")
            
            response = self.dataforseo_client.post("/v3/keywords_data/google_ads/search_volume/live", post_data)
            response_json = response.json()
            
            if response_json["status_code"] == 20000:
                self.logger.info("Search volume data retrieved successfully")
                return response_json
            else:
                error_msg = f"DataForSEO API Error - Code: {response_json['status_code']}, Message: {response_json['status_message']}"
                self.logger.error(error_msg)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve search volume data: {str(e)}")
            return None

    def _format_keyword_analytics(self, keyword_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format keyword data with comprehensive SEO analytics.
        
        Args:
            keyword_data (Dict[str, Any]): Raw keyword data from DataForSEO
            
        Returns:
            Dict[str, Any]: Formatted keyword analytics with SEO metrics
        """
        return {
            "keyword": keyword_data.get("keyword", "Unknown"),
            "search_volume": keyword_data.get("search_volume") or 0,
            "competition": keyword_data.get("competition", "UNKNOWN"),
            "competition_index": keyword_data.get("competition_index") or 0,
            "cpc": keyword_data.get("cpc") or 0,
            "difficulty_score": self._calculate_difficulty_score(keyword_data),
            "opportunity_score": self._calculate_opportunity_score(keyword_data),
            "seo_insights": self._generate_seo_insights(keyword_data)
        }

    def _calculate_difficulty_score(self, keyword_data: Dict[str, Any]) -> int:
        """
        Calculate keyword difficulty score based on competition and search volume.
        
        Args:
            keyword_data (Dict[str, Any]): Keyword metrics from DataForSEO
            
        Returns:
            int: Difficulty score from 0-100 (higher = more difficult)
        """
        competition_index = keyword_data.get("competition_index") or 0
        search_volume = keyword_data.get("search_volume") or 0
        
        # Base difficulty from competition
        if competition_index >= 80:
            base_difficulty = 85
        elif competition_index >= 60:
            base_difficulty = 65
        elif competition_index >= 40:
            base_difficulty = 45
        else:
            base_difficulty = 25
        
        # Adjust for search volume (high volume = more competitive)
        if search_volume > 10000:
            base_difficulty += 10
        elif search_volume > 1000:
            base_difficulty += 5
        
        return min(100, base_difficulty)

    def _calculate_opportunity_score(self, keyword_data: Dict[str, Any]) -> float:
        """
        Calculate opportunity score combining search volume and competition.
        
        Args:
            keyword_data (Dict[str, Any]): Keyword metrics from DataForSEO
            
        Returns:
            float: Opportunity score from 0-100 (higher = better opportunity)
        """
        search_volume = keyword_data.get("search_volume") or 0
        competition_index = keyword_data.get("competition_index") or 0
        
        # Higher volume = more opportunity (max 50 points)
        volume_score = min(50, search_volume / 200)
        
        # Lower competition = more opportunity (max 50 points)
        competition_score = 50 - (competition_index / 2)
        
        return round(volume_score + competition_score, 1)

    def _generate_seo_insights(self, keyword_data: Dict[str, Any]) -> List[str]:
        """
        Generate actionable SEO insights based on keyword metrics.
        
        Args:
            keyword_data (Dict[str, Any]): Keyword metrics from DataForSEO
            
        Returns:
            List[str]: List of SEO insights and recommendations
        """
        insights = []
        
        search_volume = keyword_data.get("search_volume") or 0
        competition_index = keyword_data.get("competition_index") or 0
        cpc = keyword_data.get("cpc") or 0
        
        # Traffic potential insights
        if search_volume > 5000:
            insights.append("High search volume - excellent traffic potential")
        elif search_volume > 1000:
            insights.append("Good search volume - solid traffic opportunity")
        else:
            insights.append("Low search volume - niche targeting opportunity")
        
        # Competition insights
        if competition_index < 50:
            insights.append("Low competition - favorable ranking conditions")
        elif competition_index < 80:
            insights.append("Medium competition - moderate SEO effort required")
        else:
            insights.append("High competition - intensive SEO strategy needed")
        
        # Commercial value insights
        if cpc > 5:
            insights.append("High commercial value - strong monetization potential")
        elif cpc > 1:
            insights.append("Medium commercial value - decent revenue opportunity")
        else:
            insights.append("Low commercial value - primarily informational intent")
        
        return insights

    def generate_comprehensive_analysis(self, website_content: str) -> Dict[str, Any]:
        """
        Generate comprehensive SEO analysis combining AI insights with search volume data.
        
        Args:
            website_content (str): Cleaned website text content
            
        Returns:
            Dict[str, Any]: Complete SEO analysis with recommendations
        """
        try:
            # Generate AI analysis
            ai_analysis = self._generate_ai_insights(website_content)
            
            # Extract keywords and enrich with search data
            keywords = ai_analysis.get("Keywords", []) or ai_analysis.get("keywords", [])
            
            if not keywords:
                self.logger.warning("No keywords generated from AI analysis")
                return {"ai_analysis": ai_analysis, "enhanced_keywords": [], "recommendations": []}
            
            # Enrich with search volume data if available
            if self.dataforseo_client:
                return self._create_enhanced_analysis(ai_analysis, keywords)
            else:
                self.logger.info("Returning basic analysis - DataForSEO not configured")
                return {"ai_analysis": ai_analysis, "keywords": keywords, "enhanced_analysis": False}
                
        except Exception as e:
            self.logger.error(f"Analysis generation failed: {str(e)}")
            raise
    
    def _generate_ai_insights(self, website_content: str) -> Dict[str, Any]:
        """
        Generate AI-powered website insights using OpenAI.
        
        Args:
            website_content (str): Website text content
            
        Returns:
            Dict[str, Any]: AI analysis results
        """
        system_prompt = (
            "You are a professional SEO analyst with expertise in keyword research "
            "and content strategy. Analyze websites with precision and provide "
            "actionable insights."
        )
        
        user_prompt = f"""
        Analyze this website content and provide a comprehensive SEO assessment:
        
        Required JSON format:
        {{
            "Name": "Website/Company name",
            "Description": "Professional description (2-3 sentences)",
            "Niche": "Primary business category/industry",
            "Keywords": ["list", "of", "relevant", "SEO", "keywords"]
        }}
        
        Focus on:
        - High-value commercial keywords
        - Long-tail keyword opportunities
        - Industry-specific terminology
        - User intent alignment
        
        Website content:
        {website_content}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            self.logger.info("AI analysis completed successfully")
            
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {str(e)}")
            raise
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse and clean AI response to extract JSON data.
        
        Args:
            ai_response (str): Raw AI response
            
        Returns:
            Dict[str, Any]: Parsed analysis data
        """
        try:
            # Clean the response
            clean_response = ai_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            return json.loads(clean_response)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            # Return a basic structure if parsing fails
            return {
                "Name": "Unknown",
                "Description": "Analysis parsing failed",
                "Niche": "Unknown",
                "Keywords": []
            }

    def _create_enhanced_analysis(self, ai_analysis: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """
        Create enhanced analysis with search volume data and professional insights.
        
        Args:
            ai_analysis (Dict[str, Any]): Basic AI analysis results
            keywords (List[str]): List of keywords to analyze
            
        Returns:
            Dict[str, Any]: Enhanced analysis with search metrics
        """
        search_volume_data = self.fetch_search_volume_data(keywords)
        
        if not search_volume_data or not search_volume_data["tasks"][0]["result"]:
            self.logger.warning("Search volume data unavailable")
            return {"ai_analysis": ai_analysis, "keywords": keywords, "enhanced_analysis": False}
        
        # Process and enrich keywords
        enriched_keywords = []
        for keyword_result in search_volume_data["tasks"][0]["result"]:
            enriched_keyword = self._format_keyword_analytics(keyword_result)
            enriched_keywords.append(enriched_keyword)
        
        # Sort by opportunity score
        enriched_keywords.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        # Generate professional report
        self._display_professional_report(ai_analysis, enriched_keywords)
        
        # Calculate summary metrics
        total_searches = sum(kw["search_volume"] for kw in enriched_keywords)
        avg_cpc = sum(kw["cpc"] for kw in enriched_keywords) / len(enriched_keywords) if enriched_keywords else 0
        
        return {
            "website_analysis": ai_analysis,
            "enriched_keywords": enriched_keywords,
            "top_recommendations": enriched_keywords[:5],
            "summary_metrics": {
                "total_monthly_searches": total_searches,
                "average_cpc": round(avg_cpc, 2),
                "keywords_analyzed": len(enriched_keywords),
                "high_opportunity_keywords": len([k for k in enriched_keywords if k["opportunity_score"] > 70])
            },
            "enhanced_analysis": True
        }

    def _display_professional_report(self, ai_analysis: Dict[str, Any], enriched_keywords: List[Dict[str, Any]]) -> None:
        """
        Display a professional SEO analysis report.
        
        Args:
            ai_analysis (Dict[str, Any]): Basic website analysis
            enriched_keywords (List[Dict[str, Any]]): Keywords with SEO metrics
        """
        print("\\n" + "═" * 80)
        print("🔍 PROFESSIONAL SEO ANALYSIS REPORT")
        print("═" * 80)
        
        # Website overview
        print(f"\\n📋 WEBSITE OVERVIEW")
        print(f"{'─' * 50}")
        print(f"Company: {ai_analysis.get('Name', 'N/A')}")
        print(f"Industry: {ai_analysis.get('Niche', 'N/A')}")
        print(f"Description: {ai_analysis.get('Description', 'N/A')}")
        
        # Keywords analysis
        print(f"\\n📊 KEYWORD OPPORTUNITY ANALYSIS")
        print(f"{'─' * 50}")
        print(f"Total keywords analyzed: {len(enriched_keywords)}")
        
        high_opportunity = len([k for k in enriched_keywords if k["opportunity_score"] > 70])
        print(f"High-opportunity keywords (>70 score): {high_opportunity}")
        
        total_volume = sum(k["search_volume"] for k in enriched_keywords)
        print(f"Combined monthly search volume: {total_volume:,}")
        
        print(f"\\n🎯 DETAILED KEYWORD ANALYSIS")
        print(f"{'─' * 80}")
        
        for idx, keyword in enumerate(enriched_keywords, 1):
            status_emoji = "🟢" if keyword["opportunity_score"] > 70 else "🟡" if keyword["opportunity_score"] > 50 else "🔴"
            
            print(f"\\n{status_emoji} {idx}. {keyword['keyword'].upper()}")
            print(f"   📈 Monthly Searches: {keyword['search_volume']:,}")
            print(f"   💵 Cost Per Click: ${keyword['cpc']:.2f}")
            print(f"   ⚔️  Competition: {keyword['competition']} ({keyword['competition_index']}/100)")
            print(f"   📊 Difficulty Score: {keyword['difficulty_score']}/100")
            print(f"   ⭐ Opportunity Score: {keyword['opportunity_score']}/100")
            print(f"   💡 Strategic Insights:")
            for insight in keyword['seo_insights']:
                print(f"      • {insight}")
        
        # Top recommendations
        top_keywords = enriched_keywords[:3]
        print(f"\\n🏆 TOP 3 STRATEGIC RECOMMENDATIONS")
        print(f"{'─' * 50}")
        for i, kw in enumerate(top_keywords, 1):
            print(f"{i}. {kw['keyword'].title()} (Opportunity Score: {kw['opportunity_score']}/100)")
            print(f"   → {kw['search_volume']:,} monthly searches, ${kw['cpc']:.2f} CPC")
        
        print(f"\\n{'═' * 80}")
        print("📈 Analysis completed successfully")
        print(f"{'═' * 80}\\n")


def main():
    """
    Main execution function for SEO analysis.
    """
    try:
        # Initialize the SEO analyzer
        analyzer = SEOAnalyzer()
        
        # Extract website content
        content = analyzer.extract_website_content()
        
        # Generate comprehensive analysis
        results = analyzer.generate_comprehensive_analysis(content)
        
        return results
        
    except Exception as e:
        logging.error(f"SEO analysis failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()