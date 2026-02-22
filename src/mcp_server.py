import json
import re
from pathlib import Path
from mcp.server.fastmcp import FastMCP

BASE_DIR = Path(__file__).parent.parent

mcp = FastMCP("ai-tour-concierge")

def _load_schedule() -> str:
    return (BASE_DIR / "data/schedule-london.md").read_text()

def _load_faq() -> str:
    return (BASE_DIR / "data/faq.md").read_text()

@mcp.tool()
def get_schedule(query: str = "") -> str:
    """Search the AI Tour London session schedule. Pass a time (e.g. '2pm'), topic, speaker, or session title."""
    content = _load_schedule()
    if not query:
        return content

    query_lower = query.lower()
    sections = re.split(r"(?=###)", content)

    if "first session" in query_lower:
        session_times = []
        for s in sections:
            match = re.search(r"###\s*(\d{1,2}:\d{2}am|pm)", s)
            if match:
                time_str = match.group(1)
                # Convert to 24hr int for sorting
                hour, minute = map(int, re.findall(r"\d{1,2}", time_str))
                am_pm = "am" if "am" in time_str else "pm"
                if am_pm == "pm" and hour != 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0
                total_minutes = hour * 60 + minute
                session_times.append((total_minutes, s.strip()))
        if session_times:
            session_times.sort()
            return session_times[0][1]
        return "No sessions found for 'first session'."

    matches = [s.strip() for s in sections if query_lower in s.lower()]

    if matches:
        return "\n\n".join(matches)
    return f"No sessions found matching '{query}'. Try a different time, topic, or speaker name."

@mcp.tool()
def get_faq(query: str = "") -> str:
    """Search the AI Tour London FAQ for information about venue, registration, food, WiFi, and logistics."""
    content = _load_faq()
    if not query:
        return content

    query_lower = query.lower()
    lines = content.split("\n")
    results = []
    capture = False
    for line in lines:
        if query_lower in line.lower():
            capture = True
        if capture:
            results.append(line)
            if line.startswith("##") and results and len(results) > 1:
                break

    if results:
        return "\n".join(results).strip()
    return f"No FAQ entry found for '{query}'. Please ask event staff for help."

if __name__ == "__main__":
    mcp.run(transport="stdio")
