# Create a streamlit app
import streamlit as st
import sys
import os
from pathlib import Path

# Add the parent directory to Python path to make imports work properly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from QuoteManagement import quote_management_crew

def main():
    st.set_page_config(
        page_title="Insurance Claim Analysis",
        page_icon="📋",
        layout="wide"
    )

    st.title("📋 Insurance Claim Analysis")
    
    # Simple button to start the crew
    if st.button("Start Claim Analysis"):
        with st.spinner("Running claim analysis..."):
            try:
                # Create containers for each report
                claim_container = st.empty()
                claim_reviewed_container = st.empty()
                decision_container = st.empty()
                
                st.subheader("Analysis Progress")
                
                # Run the crew
                with st.expander("Detailed Analysis Log", expanded=True):
                    st.write("Starting crew execution...")
                    result = quote_management_crew.kickoff()
                    
                # Display the reports from the output files
                st.subheader("Analysis Reports")
                
                try:
                    with open("Claim.md", "r") as f:
                        with st.expander("Initial Claim Report", expanded=True):
                            st.markdown(f.read())
                except FileNotFoundError:
                    st.warning("Initial claim report not found")
                
                try:
                    with open("Claim_reviewed.md", "r") as f:
                        with st.expander("Policy Coverage Analysis", expanded=True):
                            st.markdown(f.read())
                except FileNotFoundError:
                    st.warning("Policy coverage analysis not found")
                
                try:
                    with open("Claim_decision.md", "r") as f:
                        with st.expander("Final Claim Decision", expanded=True):
                            st.markdown(f.read())
                except FileNotFoundError:
                    st.warning("Final claim decision not found")
                
                # Display final result
                st.subheader("Final Result")
                st.code(result)
                
            except Exception as e:
                st.error(f"An error occurred during analysis: {str(e)}")
                st.error("Check the detailed log above for more information")

if __name__ == "__main__":
    main()


