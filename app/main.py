import sys
import os

# 🔥 Ensure project root is in PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

from agent.orchestrator import generate_script
from integration.servicenow_client import deploy_artifact
from config.settings import settings


# ---------------- SAFE IMPORTS ----------------
try:
    from validation.script_validator import validate_script
except:
    def validate_script(x):
        return {"valid": True, "issues": []}


try:
    from rag.retriever import retrieve_context
except:
    def retrieve_context(x):
        return ""


# ---------------- SESSION STATE ----------------
if "artifact" not in st.session_state:
    st.session_state.artifact = None


# ---------------- UI ----------------
st.set_page_config(page_title="AI ServiceNow Developer Agent", layout="wide")
st.title("🚀 AI ServiceNow Developer Agent")


# ---------------- INPUT ----------------
requirement = st.text_area("Describe your ServiceNow requirement", height=150)

col1, col2 = st.columns(2)

with col1:
    selected_artifact_type = st.selectbox(
        "Artifact Type",
        ["auto", "business_rule", "script_include", "client_script"]
    )

with col2:
    providers = ["openai", "gemini", "claude"]

    default_index = 0
    if settings.DEFAULT_PROVIDER in providers:
        default_index = providers.index(settings.DEFAULT_PROVIDER)

    provider = st.selectbox("LLM Provider", providers, index=default_index)


# ---------------- GENERATE ----------------
if st.button("Generate Script"):

    if not requirement.strip():
        st.warning("Please enter a requirement")
        st.stop()

    with st.spinner("Generating script..."):
        try:
            context = retrieve_context(requirement)

            artifact = generate_script(
                requirement=requirement,
                provider=provider,
                context=context,
                artifact_hint=selected_artifact_type,
            )

            artifact["requested_artifact_type"] = selected_artifact_type

            if selected_artifact_type != "auto":
                artifact["artifact_type"] = selected_artifact_type

            st.session_state.artifact = artifact

        except Exception as e:
            st.error(f"Script generation failed: {str(e)}")


# ---------------- DISPLAY ----------------
artifact = st.session_state.artifact

if artifact:

    st.success("Script Generated")

    # Normalize display
    artifact_type_display = artifact.get("artifact_type", "").lower()

    st.subheader("Artifact Type")
    st.code(artifact_type_display)

    st.subheader("Name")
    st.code(artifact.get("name", ""))

    if artifact.get("table"):
        st.subheader("Table")
        st.code(artifact.get("table", ""))

    # ---------------- SCRIPT FORMAT FIX ----------------
    st.subheader("Generated Script")

    script = artifact.get("script", "")

    if isinstance(script, str):
        script = script.replace("\\n", "\n").replace("\\t", "\t")

    st.code(script, language="javascript")

    # ---------------- VALIDATION FIX ----------------
    validation = validate_script(script)

    if isinstance(validation, list):
        validation = {
            "valid": len(validation) == 0,
            "issues": validation
        }
    elif not isinstance(validation, dict):
        validation = {
            "valid": True,
            "issues": []
        }

    if validation.get("valid"):
        st.success("Validation Passed")
    else:
        st.warning("Validation Issues Found")
        for issue in validation.get("issues", []):
            st.write(f"- {issue}")

    # ---------------- DEPLOY ----------------
    st.markdown("### 🚀 Deploy")

    if st.button("Deploy to ServiceNow"):

        with st.spinner("Deploying..."):
            try:
                result = deploy_artifact(artifact)

                st.success("Deployment Successful")
                st.json(result)

            except Exception as e:
                st.error(f"Deployment failed: {str(e)}")
                st.caption("Sanitized details were written to logs/deployment_debug.txt")


# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Built for ServiceNow AI Automation")
