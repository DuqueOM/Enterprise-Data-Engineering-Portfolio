#!/usr/bin/env python3
"""
Setup script for PYME QA Dataset DataOps project.
Automates project initialization and configuration.
"""
import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, check=True, capture_output=False):
    """Run shell command and handle errors."""
    logger.info(f"Running: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        if capture_output:
            return result.stdout.strip()
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if capture_output:
            return e.stderr.strip()
        return False

def check_prerequisites():
    """Check if required tools are installed."""
    logger.info("Checking prerequisites...")
    
    required_tools = {
        'python': 'python --version',
        'git': 'git --version',
        'pip': 'pip --version'
    }
    
    missing_tools = []
    
    for tool, command in required_tools.items():
        if not run_command(command, check=False, capture_output=True):
            missing_tools.append(tool)
        else:
            logger.info(f"✅ {tool} found")
    
    if missing_tools:
        logger.error(f"Missing required tools: {missing_tools}")
        logger.info("Please install missing tools and run setup again.")
        return False
    
    return True

def create_directories():
    """Create necessary project directories."""
    logger.info("Creating project directories...")
    
    directories = [
        'data/raw',
        'data/processed',
        'data/annotation',
        'models',
        'reports',
        'metrics',
        'plots',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created {directory}")

def install_dependencies():
    """Install Python dependencies."""
    logger.info("Installing Python dependencies...")
    
    if not run_command("pip install --upgrade pip"):
        logger.error("Failed to upgrade pip")
        return False
    
    if not run_command("pip install -r requirements.txt"):
        logger.error("Failed to install dependencies")
        return False
    
    logger.info("✅ Dependencies installed successfully")
    return True

def setup_dvc(remote_type="local", remote_path="/tmp/dvc-storage"):
    """Initialize DVC and configure remote storage."""
    logger.info("Setting up DVC...")
    
    # Check if DVC is already initialized
    if Path(".dvc").exists():
        logger.info("DVC already initialized")
    else:
        if not run_command("dvc init"):
            logger.error("Failed to initialize DVC")
            return False
        logger.info("✅ DVC initialized")
    
    # Configure remote
    remote_name = "storage"
    
    if remote_type == "local":
        remote_url = remote_path
        Path(remote_path).mkdir(parents=True, exist_ok=True)
    elif remote_type == "s3":
        remote_url = f"s3://{remote_path}"
    elif remote_type == "gdrive":
        remote_url = f"gdrive://{remote_path}"
    else:
        logger.error(f"Unsupported remote type: {remote_type}")
        return False
    
    # Add remote (check if already exists)
    if not run_command(f"dvc remote add -d {remote_name} {remote_url}", check=False):
        logger.info("Remote already exists or failed to add")
    else:
        logger.info(f"✅ DVC remote configured: {remote_url}")
    
    return True

def setup_gitignore():
    """Update .gitignore file."""
    logger.info("Updating .gitignore...")
    
    gitignore_entries = [
        "# Data files",
        "data/raw/",
        "data/processed/*.jsonl",
        "data/annotation/",
        "",
        "# Model files",
        "models/*.pkl",
        "models/*.joblib",
        "",
        "# Metrics and reports",
        "metrics/*.json",
        "reports/*.html",
        "",
        "# DVC",
        ".dvc/cache/",
        "",
        "# Python",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        "",
        "# Environment",
        "venv/",
        "env/",
        ".env",
        "",
        "# IDE",
        ".vscode/",
        "*.swp",
        "*.swo",
        "",
        "# OS",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    gitignore_path = Path(".gitignore")
    
    # Read existing .gitignore
    existing_entries = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_entries = set(line.strip() for line in f if line.strip() and not line.startswith('#'))
    
    # Add new entries
    with open(gitignore_path, 'a') as f:
        for entry in gitignore_entries:
            if entry.strip() and entry.strip() not in existing_entries:
                f.write(f"{entry}\n")
    
    logger.info("✅ .gitignore updated")

def create_environment_file():
    """Create .env file with environment variables."""
    logger.info("Creating environment file...")
    
    env_content = """# PYME QA Dataset Environment Variables

# Label Studio Configuration
LABEL_STUDIO_URL=http://localhost:8080
LABEL_STUDIO_API_KEY=your-api-key-here
LABEL_STUDIO_PROJECT_ID=1

# DVC Remote Configuration
DVC_REMOTE_URL=/tmp/dvc-storage

# Logging Configuration
LOG_LEVEL=INFO

# Model Configuration
MODEL_PERFORMANCE_THRESHOLD=0.7
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_content)
        logger.info("✅ .env file created")
        logger.info("⚠️  Please update .env with your actual configuration values")
    else:
        logger.info(".env file already exists")

def run_initial_pipeline():
    """Run the initial data pipeline."""
    logger.info("Running initial pipeline...")
    
    # Check if we have sample data URLs configured
    ingest_script = Path("scripts/ingest.py")
    if ingest_script.exists():
        logger.info("Running data ingestion...")
        if run_command("python scripts/ingest.py"):
            logger.info("✅ Data ingestion completed")
        else:
            logger.warning("Data ingestion failed - you may need to configure URLs")
    
    # Run data cleaning
    if Path("data/processed/faqs.jsonl").exists():
        logger.info("Running data cleaning...")
        if run_command("python scripts/clean.py"):
            logger.info("✅ Data cleaning completed")
        
        # Run validation
        logger.info("Running data validation...")
        if run_command("python scripts/validate_schema.py"):
            logger.info("✅ Data validation completed")
    
    # Run tests
    logger.info("Running tests...")
    if run_command("pytest tests/ -v", check=False):
        logger.info("✅ Tests completed")
    else:
        logger.warning("Some tests failed - this is expected if no data is available")

def setup_git_repo():
    """Initialize git repository if not already done."""
    logger.info("Setting up git repository...")
    
    if not Path(".git").exists():
        if run_command("git init"):
            logger.info("✅ Git repository initialized")
            
            # Add initial files
            run_command("git add .")
            run_command('git commit -m "Initial commit: DataOps project setup"')
            logger.info("✅ Initial commit created")
        else:
            logger.error("Failed to initialize git repository")
    else:
        logger.info("Git repository already exists")

def print_next_steps():
    """Print next steps for the user."""
    logger.info("\n🎉 Setup completed successfully!")
    logger.info("\n📋 Next steps:")
    logger.info("1. Review and update .env file with your configuration")
    logger.info("2. Configure data sources in scripts/ingest.py")
    logger.info("3. Run the pipeline: dvc repro")
    logger.info("4. View quality report: open reports/quality_report.html")
    logger.info("5. Set up GitHub repository for CI/CD")
    logger.info("6. Configure DVC remote for cloud storage if needed")
    
    logger.info("\n📚 Useful commands:")
    logger.info("- Run full pipeline: dvc repro")
    logger.info("- Check pipeline status: dvc status")
    logger.info("- View pipeline DAG: dvc dag")
    logger.info("- Run tests: pytest tests/ -v")
    logger.info("- Push data to remote: dvc push")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup PYME QA Dataset DataOps project")
    parser.add_argument("--dvc-remote", choices=["local", "s3", "gdrive"], default="local",
                       help="Type of DVC remote storage")
    parser.add_argument("--remote-path", default="/tmp/dvc-storage",
                       help="Path for DVC remote storage")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    
    args = parser.parse_args()
    
    logger.info("🚀 Starting PYME QA Dataset DataOps project setup...")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # Setup DVC
    if not setup_dvc(args.dvc_remote, args.remote_path):
        sys.exit(1)
    
    # Setup git
    setup_git_repo()
    
    # Update .gitignore
    setup_gitignore()
    
    # Create environment file
    create_environment_file()
    
    # Run initial pipeline
    run_initial_pipeline()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
