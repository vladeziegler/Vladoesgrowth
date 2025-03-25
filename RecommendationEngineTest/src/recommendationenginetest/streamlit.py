import streamlit as st
import json
import pandas as pd
import os
from crew import AgenticRagExample, AgentObjectList, AgentObject
import streamlit as st

st.set_page_config(
    page_title="AI Recommendation Engine",
    page_icon="🤖",
    layout="wide"
)

def format_agent_object(agent_obj):
    """Format an AgentObject for display"""
    cols = st.columns([2, 1])
    
    with cols[0]:
        st.subheader(f"Role: {agent_obj.role}")
        st.write(f"**Company Activity:** {agent_obj.company_activity}")
        st.write(f"**Task:** {agent_obj.task}")
        st.write(f"**Location:** {agent_obj.location}")
        
        # Market info (if available)
        if any([agent_obj.market_category, agent_obj.market_size, agent_obj.market_growth]):
            st.markdown("---")
            st.write("### Market Information")
            if agent_obj.market_category:
                st.write(f"**Market Category:** {agent_obj.market_category}")
            if agent_obj.market_size:
                st.write(f"**Market Size:** ${agent_obj.market_size:,.2f}")
            if agent_obj.market_growth:
                st.write(f"**Market Growth:** {agent_obj.market_growth}%")
            if agent_obj.market_challenges:
                st.write(f"**Market Challenges:** {agent_obj.market_challenges}")
            if agent_obj.market_notes:
                st.write(f"**Market Notes:** {agent_obj.market_notes}")
    
    with cols[1]:
        # Value metrics
        st.metric(
            label="Hours Saved", 
            value=f"{agent_obj.hours_saved:,.1f} hrs"
        )
        st.metric(
            label="Money Saved", 
            value=f"${agent_obj.money_saved:,.2f}"
        )
        
        # Calculate ROI if both values are present
        if agent_obj.hours_saved and agent_obj.money_saved:
            hourly_value = agent_obj.money_saved / agent_obj.hours_saved
            st.metric(
                label="Value per Hour", 
                value=f"${hourly_value:,.2f}/hr"
            )

def display_investment_thesis(thesis_file="report_INVESTMENT_THESES.md"):
    """Display the investment thesis report"""
    if os.path.exists(thesis_file):
        with open(thesis_file, 'r') as f:
            thesis_content = f.read()
        st.markdown(thesis_content)
    else:
        st.warning(f"Investment thesis file not found: {thesis_file}")

def run_query(query):
    """Run the query through the crew and return results"""
    with st.spinner('Processing your query... This may take several minutes.'):
        try:
            inputs = {"query": query}
            crew_instance = AgenticRagExample().crew()
            result = crew_instance.kickoff(inputs=inputs)
            
            # Try to find the AgentObjectList from the results or tasks
            agent_list = None
            
            # Check if we got an AgentObjectList directly
            if isinstance(result, AgentObjectList):
                agent_list = result
            
            # If result is not an AgentObjectList, look for output files
            file_paths = [
                "report_INVESTMENT_THESES.md",  # Final report
                "report_MARKET_ANALYSIS.md",     # Market analysis report
                os.path.join(os.getcwd(), "report_INVESTMENT_THESES.md"),
                os.path.join(os.getcwd(), "report_MARKET_ANALYSIS.md")
            ]
            
            # Check for files
            found_files = [fp for fp in file_paths if os.path.exists(fp)]
            
            # If no AgentObjectList but we have report files, we'll show those
            if not agent_list and found_files:
                st.success("Analysis completed! Displaying investment thesis report.")
                return {"files": found_files, "type": "report"}
            
            # Try to extract from crew's task outputs
            if not agent_list and hasattr(crew_instance, "tasks"):
                for task in crew_instance.tasks:
                    if hasattr(task, "output") and isinstance(task.output, AgentObjectList):
                        agent_list = task.output
                        break
            
            if agent_list:
                return {"agent_list": agent_list, "type": "agents"}
            else:
                st.warning("Unable to extract recommendations from the crew output.")
                return None
            
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            return None

def main():
    st.title("AI Recommendation Engine")
    st.markdown("""
    This tool helps you find AI use cases and opportunities by analyzing your specific query.
    Enter a question about AI applications to get personalized recommendations.
    """)
    
    with st.form("query_form"):
        query = st.text_area(
            "Enter your query:",
            placeholder="e.g., 'roles where voice agents are most prevalent?' or 'Which tasks can be automated in healthcare?'",
            height=100
        )
        submitted = st.form_submit_button("Get Recommendations")
    
    if submitted and query:
        result = run_query(query)
        
        if result:
            if result["type"] == "agents" and "agent_list" in result:
                agent_list = result["agent_list"]
                st.success(f"Found {len(agent_list.agents)} recommendations!")
                
                # Show summary metrics
                if len(agent_list.agents) > 0:
                    total_hours = sum(agent.hours_saved for agent in agent_list.agents)
                    total_money = sum(agent.money_saved for agent in agent_list.agents)
                    
                    metrics_cols = st.columns(3)
                    metrics_cols[0].metric("Total Recommendations", len(agent_list.agents))
                    metrics_cols[1].metric("Total Hours Saved", f"{total_hours:,.1f} hrs")
                    metrics_cols[2].metric("Total Money Saved", f"${total_money:,.2f}")
                
                # Display each recommendation
                for i, agent_obj in enumerate(agent_list.agents):
                    st.markdown("---")
                    st.markdown(f"## Recommendation {i+1}")
                    format_agent_object(agent_obj)
                    
                # Add export options
                st.markdown("---")
                st.subheader("Export Results")
                
                # Convert to JSON for download
                agent_dicts = [json.loads(agent.json()) for agent in agent_list.agents]
                json_str = json.dumps({"agents": agent_dicts}, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="recommendations.json",
                    mime="application/json",
                    key="download_json"
                )
                
                # Create DataFrame for CSV export
                df = pd.DataFrame([{
                    "Role": agent.role,
                    "Company Activity": agent.company_activity,
                    "Task": agent.task,
                    "Location": agent.location,
                    "Hours Saved": agent.hours_saved,
                    "Money Saved": agent.money_saved,
                    "Market Category": agent.market_category,
                    "Market Size": agent.market_size,
                    "Market Growth": agent.market_growth
                } for agent in agent_list.agents])
                
                st.download_button(
                    label="Download CSV",
                    data=df.to_csv(index=False),
                    file_name="recommendations.csv",
                    mime="text/csv",
                    key="download_csv"
                )
            
            elif result["type"] == "report" and "files" in result:
                # Display report files
                st.success("Analysis completed successfully!")
                
                # Find the first occurrence of each type of report
                investment_thesis_file = None
                market_analysis_file = None
                
                for file_path in result["files"]:
                    if "INVESTMENT_THESES" in file_path and not investment_thesis_file:
                        investment_thesis_file = file_path
                    elif "MARKET_ANALYSIS" in file_path and not market_analysis_file:
                        market_analysis_file = file_path
                
                # Display Investment Thesis (once)
                if investment_thesis_file:
                    st.markdown("## Investment Theses")
                    display_investment_thesis(investment_thesis_file)
                
                # Display Market Analysis (once)
                if market_analysis_file:
                    st.markdown("## Market Analysis")
                    with open(market_analysis_file, 'r') as f:
                        st.markdown(f.read())
                
                # Add download section
                st.markdown("---")
                st.subheader("Download Reports")
                
                # Add download buttons for the reports
                for i, file_path in enumerate(result["files"]):
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                        file_name = os.path.basename(file_path)
                        st.download_button(
                            label=f"Download {file_name}",
                            data=file_content,
                            file_name=file_name,
                            mime="text/markdown",
                            key=f"download_report_{i}"
                        )
        else:
            st.warning("No recommendations found. Try a different query.")

if __name__ == "__main__":
    main() 