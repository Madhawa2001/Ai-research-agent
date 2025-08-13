from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from .models import CompanyAnalysis, ResearchState, CompanyInfo
from .prompts import DeveloperToolsPrompts
from .firecrawl import FirecrawlService

class ResearchWorkflow(StateGraph):
    """Workflow for researching developer tools and technologies"""

    def __init__(self):
        self.firecrawl_service = FirecrawlService()
        self.llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
        )
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._create_workflow()
    
    def _create_workflow(self):
        """Define the workflow steps"""
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_step)
        graph.add_node("analyze", self._analyze_step)
        graph.set_entry_point("extract_tools")
        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        """Extract tools from articles using LLM"""
        print(f"Finding articles about {state.query}...")

        article_query = f"{state.query} tools comparison best alternatives"
        search_results = self.firecrawl_service.search_companies(article_query, num_results=3)

        all_content = ""
        for result in search_results.data:
            url = result.get("url", "")
            scraped = self.firecrawl_service.scrape_company_pages(url)
            if scraped:
                all_content + scraped.markdown[:1500] + "\n\n"

        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]

        try:
            response = self.llm.invoke(messages)
            tool_names = [
                name.strip()
                for name in response.content.strip().split("\n")
                if name.strip()
            ]
            print(f'Extracted tools: {', '.join(tool_names[:5])}')
            return {"extracted_tools": tool_names}
        except Exception as e:
            print(f"Error during tool extraction: {e}")
            return {"extracted_tools": []}
        
    def _analyze_company_content(self, company_name: str, content: str) -> CompanyAnalysis:
        """Analyze company content to extract developer-relevant information"""
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)

        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, content))
        ]

        try:
            raw = structured_llm.invoke(messages)
            # Manually coerce string types to expected formats if needed
            def parse_bool(value):
                if isinstance(value, bool) or value is None:
                    return value
                return value.lower() == "true"

            def parse_list(value):
                if isinstance(value, list):
                    return value
                if isinstance(value, str):
                    try:
                        parsed = eval(value)  # assuming it's a stringified list like "[]"
                        if isinstance(parsed, list):
                            return parsed
                    except:
                        pass
                return []

            return CompanyAnalysis(
                pricing_model=raw.pricing_model,
                is_open_source=parse_bool(raw.is_open_source),
                tech_stack=parse_list(raw.tech_stack),
                description=raw.description,
                api_available=parse_bool(raw.api_available),
                language_support=parse_list(raw.language_support),
                integration_capabilities=parse_list(raw.integration_capabilities)
            )
        except Exception as e:
            print(f"Error during company analysis: {e}")
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[]
            )

        
    def _research_step(self, state: ResearchState) -> Dict[str, Any]:
        """Main research step to analyze tools and companies"""
        
        extracted_tools = getattr(state, 'extracted_tools', [])
        if not extracted_tools:
            print("No tools extracted, skipping research step.")
            search_results = self.firecrawl_service.search_companies(state.query, num_results=4)
            tool_names = [
                result.get("metadata", {}).get("title", "Unknown")
                for result in search_results.data
            ]
        else:
            tool_names = extracted_tools[:4]

        print(f"Researching specific tools: {', '.join(tool_names)}")

        companies = []
        for tool in tool_names:
            tool_search_results = self.firecrawl_service.search_companies(tool + " official site", num_results=1)

            if tool_search_results:
                result = tool_search_results.data[0]
                url = result.get("url", "")

                company = CompanyInfo(
                    name = tool,
                    description = result.get("markdown", ""),
                    website = url,
                    tech_stack = [],
                    competitors= [],
                )

                scraped = self.firecrawl_service.scrape_company_pages(url)
                if scraped:
                    content = scraped.markdown
                    analysis = self._analyze_company_content(company.name, content)

                    company.pricing_model = analysis.pricing_model
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities
                
                companies.append(company)
    
        return {"companies": companies}
    
    def _analyze_step(self, state: ResearchState) -> Dict[str, Any]:
        """Analyze the research results and provide recommendations"""
        print("Analyzing research results...")

        company_data = ", ".join([
            company.json() for company in state.companies
        ])

        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
        ]

        response = self.llm.invoke(messages)
        return {"analysis": response.content}
    
    def run(self, initial_query: str) -> ResearchState:
        """Run the entire research workflow"""
        initial_state = ResearchState(query=initial_query)
        final_state = self.workflow.invoke(initial_state)
        return ResearchState(**final_state)

        