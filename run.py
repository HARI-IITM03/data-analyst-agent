#!/usr/bin/env python3
"""
Startup script for Data Analyst Agent API
Handles different deployment scenarios and environments
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import pandas
        import matplotlib
        import duckdb
        import boto3
        logger.info("✅ All required packages are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def get_port():
    """Get port from environment or default to 8000"""
    return int(os.environ.get("PORT", 8000))

def get_host():
    """Get host from environment or default to 0.0.0.0"""
    return os.environ.get("HOST", "0.0.0.0")

def main():
    """Main startup function"""
    logger.info("🚀 Starting Data Analyst Agent API...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get configuration
    host = get_host()
    port = get_port()
    
    logger.info(f"📡 Server will run on {host}:{port}")
    
    # Import and run the app
    try:
        import uvicorn
        from main import app
        
        # Configure uvicorn
        config = {
            "app": app,
            "host": host,
            "port": port,
            "log_level": "info",
            "access_log": True,
        }
        
        # Add reload in development
        if os.environ.get("ENVIRONMENT") == "development":
            config["reload"] = True
            config["reload_dirs"] = ["."]
        
        logger.info("🎯 API endpoints:")
        logger.info(f"   POST {host}:{port}/api/")
        logger.info(f"   GET  {host}:{port}/health")
        
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()