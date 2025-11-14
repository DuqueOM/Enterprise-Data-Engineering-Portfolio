#!/usr/bin/env python3
"""Complete project validation script."""

import os
import sys
import ast
import json
import yaml
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath}")
        return False

def check_python_syntax(filepath):
    """Check Python file syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        print(f"✅ Python syntax valid: {filepath}")
        return True
    except SyntaxError as e:
        print(f"❌ Python syntax error in {filepath}: {e}")
        return False

def check_yaml_syntax(filepath):
    """Check YAML file syntax."""
    try:
        with open(filepath, 'r') as f:
            yaml.safe_load_all(f)
        print(f"✅ YAML syntax valid: {filepath}")
        return True
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error in {filepath}: {e}")
        return False

def check_json_syntax(filepath):
    """Check JSON file syntax."""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        print(f"✅ JSON syntax valid: {filepath}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON syntax error in {filepath}: {e}")
        return False

def check_directory_structure():
    """Check project directory structure."""
    print("\n📁 Checking directory structure...")
    
    required_dirs = [
        "space",
        "scripts", 
        "tests",
        "k8s",
        "monitoring",
        ".github/workflows"
    ]
    
    all_good = True
    for dirname in required_dirs:
        if os.path.isdir(dirname):
            print(f"✅ Directory exists: {dirname}/")
        else:
            print(f"❌ Directory missing: {dirname}/")
            all_good = False
    
    return all_good

def check_core_files():
    """Check core project files."""
    print("\n📄 Checking core files...")
    
    core_files = {
        "requirements.txt": "Python dependencies",
        "Dockerfile": "Docker image definition", 
        ".env.example": "Environment variables template",
        ".gitignore": "Git ignore rules",
        "README.md": "Project documentation",
        "LICENSE": "License file"
    }
    
    all_good = True
    for filepath, description in core_files.items():
        if not check_file_exists(filepath, description):
            all_good = False
    
    return all_good

def check_python_files():
    """Check all Python files."""
    print("\n🐍 Checking Python files...")
    
    python_files = list(Path(".").rglob("*.py"))
    all_good = True
    
    for py_file in python_files:
        if not check_python_syntax(str(py_file)):
            all_good = False
    
    return all_good

def check_config_files():
    """Check configuration files."""
    print("\n⚙️ Checking configuration files...")
    
    config_files = {
        "k8s/deployment.yaml": "Kubernetes deployment",
        "monitoring/prometheus.yml": "Prometheus config",
        "monitoring/grafana-dashboard.json": "Grafana dashboard",
        "docker-compose.yml": "Docker Compose stack"
    }
    
    all_good = True
    for filepath, description in config_files.items():
        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            if not check_yaml_syntax(filepath):
                all_good = False
        elif filepath.endswith('.json'):
            if not check_json_syntax(filepath):
                all_good = False
        else:
            if not check_file_exists(filepath, description):
                all_good = False
    
    return all_good

def check_executable_scripts():
    """Check executable scripts."""
    print("\n🔧 Checking executable scripts...")
    
    scripts = [
        "rollback.sh",
        "scripts/deploy_canary.sh"
    ]
    
    all_good = True
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"✅ Script executable: {script}")
            else:
                print(f"⚠️ Script not executable: {script} (run: chmod +x {script})")
        else:
            print(f"❌ Script missing: {script}")
            all_good = False
    
    return all_good

def main():
    """Run complete project validation."""
    print("🔍 Validating MLOps Auto-Retrain Pipeline...")
    print("=" * 50)
    
    results = {
        "Directory Structure": check_directory_structure(),
        "Core Files": check_core_files(), 
        "Python Files": check_python_files(),
        "Config Files": check_config_files(),
        "Executable Scripts": check_executable_scripts()
    }
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for category, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{category:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Project is ready for deployment.")
        print("\n🚀 Next steps:")
        print("1. Copy .env.example to .env and configure your credentials")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run smoke test: python train.py --max_steps 10")
        print("4. Start stack: docker-compose up -d")
        print("5. Setup monitoring: python scripts/setup_monitoring.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
