import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from agent.orchestrator import generate_script
from integration.servicenow_client import deploy_artifact
from validation.script_validator import validate_script
from rag.retriever import retrieve_context


st.title("🚀 AI ServiceNow Developer Agent")


provider = st.selectbox(
    "Select AI Provider",
    ["openai", "gemini", "claude"]
)


requirement = st.text_area(
    "Describe your ServiceNow requirement",
    height=150
)


if st.button("Show RAG Context"):

    context = retrieve_context(requirement)

    st.subheader("Retrieved Context")

    st.code(context)


if st.button("Generate Script"):

    artifact = generate_script(requirement, provider)

    st.session_state["artifact"] = artifact


artifact = st.session_state.get("artifact")


if artifact:

    st.subheader("Artifact Type")

    st.write(artifact.artifact_type)

    st.subheader("Generated Script")

    st.code(artifact.script, language="javascript")

    issues = validate_script(artifact.script)

    if issues:
        st.warning(f"Potential issues: {issues}")

    if st.button("Deploy to ServiceNow"):

        result = deploy_artifact(artifact.model_dump())

        st.subheader("Deployment Result")

        st.json(result)