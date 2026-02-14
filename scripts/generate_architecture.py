"""Generate GCP architecture diagrams with official GCP icons.

Produces two diagrams:
1. Runtime Architecture: normal app usage flow
2. Development Architecture: CI/CD with Google AntiGravity
"""
import os

# Ensure Graphviz is on PATH
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")

from diagrams import Diagram, Cluster, Edge

# GCP nodes
from diagrams.gcp.compute import Run
from diagrams.gcp.database import Firestore
from diagrams.gcp.storage import GCS
from diagrams.gcp.ml import AIPlatform
from diagrams.gcp.analytics import PubSub
from diagrams.gcp.devtools import Tasks
from diagrams.gcp.operations import Logging
from diagrams.gcp.security import KeyManagementService

# Generic / custom nodes
from diagrams.generic.storage import Storage as GenericStorage
from diagrams.onprem.client import Users, Client
from diagrams.onprem.vcs import Github

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "docs")

# ── Styling ─────────────────────────────────────────────────────
GRAPH_ATTR = {
    "fontsize": "18",
    "fontname": "Segoe UI",
    "bgcolor": "white",
    "pad": "0.6",
    "nodesep": "0.7",
    "ranksep": "0.9",
}
EDGE_ATTR = {"fontsize": "10", "fontname": "Segoe UI"}
NODE_ATTR = {"fontsize": "11", "fontname": "Segoe UI"}


def generate_runtime_architecture():
    """Diagram 1: Runtime Architecture (app usage)."""
    outpath = os.path.join(OUTPUT_DIR, "architecture_runtime")

    with Diagram(
        "DocuAlign AI - Runtime Architecture",
        filename=outpath,
        outformat="png",
        show=False,
        direction="TB",
        graph_attr=GRAPH_ATTR,
        edge_attr=EDGE_ATTR,
        node_attr=NODE_ATTR,
    ):
        user = Users("Admin User\n(Browser)")

        with Cluster("Google Cloud Platform"):

            with Cluster("Application Layer"):
                cloud_run = Run("Streamlit App\n(Cloud Run)")

            with Cluster("AI / ML Engine"):
                gemini = AIPlatform("Gemini 2.0 Flash\n(Vertex AI)")

            with Cluster("Data & Storage"):
                firestore = Firestore("Firestore\n(Results/Feedback\n/Audit)")
                gcs = GCS("Cloud Storage\n(Documents)")

            with Cluster("Async Processing & Events"):
                cloud_tasks = Tasks("Cloud Tasks\n(Async Scan)")
                pubsub = PubSub("Pub/Sub\n(Notifications)")

            with Cluster("Operations & Security"):
                logging = Logging("Cloud Logging")
                secret_mgr = KeyManagementService("Secret Manager")

            with Cluster("External Google APIs"):
                drive = GenericStorage("Google Drive\nAPI")
                docs = GenericStorage("Google Docs\nAPI")

        # User -> App
        user >> Edge(label="HTTPS") >> cloud_run

        # App -> AI
        cloud_run >> Edge(label="text/image analysis") >> gemini

        # App -> Data
        cloud_run >> Edge(label="read/write") >> firestore
        cloud_run >> Edge(label="store docs") >> gcs

        # App -> Async
        cloud_run >> Edge(label="scan request") >> cloud_tasks
        cloud_run >> Edge(label="alerts") >> pubsub

        # App -> Ops
        cloud_run >> Edge(label="logs") >> logging
        cloud_run >> Edge(label="secrets") >> secret_mgr

        # App -> APIs
        cloud_run >> Edge(label="fetch") >> drive
        cloud_run >> Edge(label="read") >> docs

        # Cloud Tasks -> App (async callback)
        cloud_tasks >> Edge(label="async callback", style="dashed") >> cloud_run

    print(f"Generated: {outpath}.png")


def generate_dev_architecture():
    """Diagram 2: Development Architecture (with AntiGravity)."""
    outpath = os.path.join(OUTPUT_DIR, "architecture_development")

    with Diagram(
        "DocuAlign AI - Development Architecture",
        filename=outpath,
        outformat="png",
        show=False,
        direction="TB",
        graph_attr=GRAPH_ATTR,
        edge_attr=EDGE_ATTR,
        node_attr=NODE_ATTR,
    ):
        developer = Client("Developer")

        with Cluster("Development Environment"):
            antigravity = Client("Google\nAntiGravity\n(AI Coding)")
            vscode = Client("VS Code")

        with Cluster("Source Control"):
            github = Github("GitHub\nRepository")

        with Cluster("Google Cloud Platform"):

            with Cluster("CI/CD"):
                cloud_build = Run("Cloud Build")

            with Cluster("Application"):
                cloud_run = Run("Cloud Run\n(Staging / Prod)")

            with Cluster("AI / ML"):
                gemini = AIPlatform("Gemini 2.0 Flash\n(Vertex AI)")

            with Cluster("Data & Storage"):
                firestore = Firestore("Firestore")
                gcs = GCS("Cloud Storage")

            with Cluster("Operations"):
                logging = Logging("Cloud Logging")
                secret_mgr = KeyManagementService("Secret Manager")

            with Cluster("Async / Events"):
                pubsub = PubSub("Pub/Sub")
                cloud_tasks = Tasks("Cloud Tasks")

            with Cluster("External APIs"):
                drive = GenericStorage("Google Drive API")

        # Dev workflow
        developer >> Edge(label="AI-assisted coding") >> antigravity
        antigravity >> Edge(label="code generation", style="dashed") >> vscode
        developer >> Edge(label="edit") >> vscode

        # CI/CD flow
        vscode >> Edge(label="git push") >> github
        github >> Edge(label="trigger build") >> cloud_build
        cloud_build >> Edge(label="deploy") >> cloud_run

        # Runtime connections
        cloud_run >> gemini
        cloud_run >> firestore
        cloud_run >> gcs
        cloud_run >> logging
        cloud_run >> secret_mgr
        cloud_run >> pubsub
        cloud_run >> cloud_tasks
        cloud_run >> drive

    print(f"Generated: {outpath}.png")


if __name__ == "__main__":
    generate_runtime_architecture()
    generate_dev_architecture()
    print("Done!")
