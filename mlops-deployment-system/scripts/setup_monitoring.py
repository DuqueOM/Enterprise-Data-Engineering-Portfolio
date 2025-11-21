"""Setup script for monitoring infrastructure."""

import os
import subprocess
import time

import requests


def wait_for_service(url, timeout=60):
    """Wait for a service to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


def setup_grafana_dashboard():
    """Import dashboard to Grafana."""
    grafana_url = "http://admin:admin@localhost:3000"
    dashboard_path = "monitoring/grafana-dashboard.json"

    if not os.path.exists(dashboard_path):
        print(f"Dashboard file not found: {dashboard_path}")
        return False

    try:
        with open(dashboard_path) as f:
            dashboard_json = f.read()

        response = requests.post(
            f"{grafana_url}/api/dashboards/db",
            headers={"Content-Type": "application/json"},
            data=dashboard_json,
        )

        if response.status_code == 200:
            print("✅ Grafana dashboard imported successfully")
            return True
        else:
            print(f"❌ Failed to import Grafana dashboard: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error importing Grafana dashboard: {e}")
        return False


def main():
    print("🚀 Setting up MLOps monitoring infrastructure...")

    # Check if Docker Compose is running
    try:
        subprocess.run(["docker-compose", "ps"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(
            "❌ Docker Compose services not running. Start with: docker-compose up -d"
        )
        return

    print("⏳ Waiting for services to be ready...")

    services = {
        "API": "http://localhost:8080/health",
        "MLflow": "http://localhost:5000",
        "Prometheus": "http://localhost:9090/-/healthy",
        "Grafana": "http://localhost:3000/api/health",
    }

    for service_name, health_url in services.items():
        print(f"  Checking {service_name}...")
        if wait_for_service(health_url):
            print(f"  ✅ {service_name} is ready")
        else:
            print(f"  ❌ {service_name} failed to start")

    # Setup Grafana dashboard
    print("\n📊 Setting up Grafana dashboard...")
    setup_grafana_dashboard()

    print("\n🎉 Monitoring setup complete!")
    print("\n📈 Access your services:")
    print("  • API: http://localhost:8080")
    print("  • MLflow: http://localhost:5000")
    print("  • Prometheus: http://localhost:9090")
    print("  • Grafana: http://localhost:3000 (admin/admin)")
    print("  • Prefect: http://localhost:4200")


if __name__ == "__main__":
    main()
