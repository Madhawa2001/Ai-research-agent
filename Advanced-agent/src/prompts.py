
class DeveloperToolsPrompts:
    """Collection of prompts for analyzing developer tools and technologies"""

    # Tool extraction prompts
    TOOL_EXTRACTION_SYSTEM = """You are a tech researcher. Extract specific tool, library, platform, or service names from articles.
                            Focus on actual products/tools that developers can use, not general concepts or features."""

    @staticmethod
    def tool_extraction_user(query: str, content: str) -> str:
        return f"""Query: {query}
    Article Content: {content}

    Your task is to extract a list of **tools, libraries, SDKs, platforms, or services** specifically relevant to the query: "{query}".

    Rules:
    - Only include actual, named developer tools (e.g., SDKs, libraries, platforms).
    - Do NOT include general terms (e.g., "database", "backend").
    - Prefer tools built **for** or commonly **used with** {query}.
    - Include both open source and commercial tools.
    - Do NOT include tools that are unrelated or only indirectly connected to {query}.
    - Return a list of max 5 relevant tools — each on a separate line, no descriptions.

    Output format:
    ToolOne
    ToolTwo
    ToolThree
    ToolFour
    ToolFive
    """


    # Company/Tool analysis prompts
    TOOL_ANALYSIS_SYSTEM = """You are analyzing developer tools and programming technologies. 
Focus on extracting information relevant to programmers and software developers.

You must return a **valid Python dictionary** in the exact format below. 
Strictly follow these rules:
- Boolean fields (like `api_available` and `is_open_source`) must be **true, false, or null** (unquoted).
- List fields (like `tech_stack`, `language_support`, and `integration_capabilities`) must be **actual lists**, not strings.
- Do not wrap booleans or lists in strings. Do not return any extra text outside the dictionary.

Example format:
{
  "pricing_model": "Freemium",
  "is_open_source": true,
  "tech_stack": ["NoSQL", "Realtime DB", "Cloud Functions"],
  "description": "Firebase provides cloud services and APIs for mobile and web developers.",
  "api_available": true,
  "language_support": ["JavaScript", "Dart"],
  "integration_capabilities": ["GitHub", "Google Cloud"]
}

Only include developer-relevant information like APIs, SDKs, programming languages, integrations, dev workflows, etc.
"""

    @staticmethod
    def tool_analysis_user(company_name: str, content: str) -> str:
        return f"""Company/Tool: {company_name}
                Website Content: {content[:2500]}

                Analyze this content from a developer's perspective and provide:
                - pricing_model: One of "Free", "Freemium", "Paid", "Enterprise", or "Unknown"
                - is_open_source: true if open source, false if proprietary, null if unclear
                - tech_stack: List of programming languages, frameworks, databases, APIs, or technologies supported/used
                - description: Brief 1-sentence description focusing on what this tool does for developers
                - api_available: true if REST API, GraphQL, SDK, or programmatic access is mentioned
                - language_support: List of programming languages explicitly supported (e.g., Python, JavaScript, Go, etc.)
                - integration_capabilities: List of tools/platforms it integrates with (e.g., GitHub, VS Code, Docker, AWS, etc.)

                Focus on developer-relevant features like APIs, SDKs, language support, integrations, and development workflows."""

    # Recommendation prompts
    RECOMMENDATIONS_SYSTEM = """You are a senior software engineer providing quick, concise tech recommendations. 
                            Keep responses brief and actionable - maximum 3-4 sentences total."""

    @staticmethod
    def recommendations_user(query: str, company_data: str) -> str:
        return f"""Developer Query: {query}
                Tools/Technologies Analyzed: {company_data}

                Provide a brief recommendation (3-4 sentences max) covering:
                - Which tool is best and why
                - Key cost/pricing consideration
                - Main technical advantage

                Be concise and direct - no long explanations needed."""