#!/usr/bin/env python3
"""
Supervisor script for the Telegram worker.
Monitors the worker process and restarts it automatically on failure.
"""

import subprocess
import sys
import time
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] SUPERVISOR %(levelname)s %(message)s'
)

MAX_RESTARTS = int(os.getenv("SUPERVISOR_MAX_RESTARTS", "100"))
RESTART_DELAY = int(os.getenv("SUPERVISOR_RESTART_DELAY", "10"))
WORKER_SCRIPT = os.getenv("WORKER_SCRIPT", "python ingest.py")

restart_count = 0
last_restart_time = None

def run_worker():
    """Run the worker process."""
    global restart_count, last_restart_time
    
    logging.info(f"Starting worker (attempt {restart_count + 1}/{MAX_RESTARTS})")
    last_restart_time = datetime.now()
    
    try:
        # Run the worker
        process = subprocess.Popen(
            WORKER_SCRIPT.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream output
        for line in process.stdout:
            print(line, end='')
        
        # Wait for process to complete
        return_code = process.wait()
        
        if return_code == 0:
            logging.info("Worker exited normally")
            return True
        else:
            logging.error(f"Worker exited with code {return_code}")
            return False
            
    except KeyboardInterrupt:
        logging.info("Supervisor interrupted by user")
        if 'process' in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        return True
    except Exception as e:
        logging.error(f"Error running worker: {e}", exc_info=True)
        return False

def main():
    """Main supervisor loop."""
    global restart_count
    
    logging.info("=" * 80)
    logging.info("Telegram Worker Supervisor")
    logging.info("=" * 80)
    logging.info(f"Max restarts: {MAX_RESTARTS}")
    logging.info(f"Restart delay: {RESTART_DELAY}s")
    logging.info(f"Worker script: {WORKER_SCRIPT}")
    logging.info("=" * 80)
    
    while restart_count < MAX_RESTARTS:
        success = run_worker()
        
        if success:
            # Worker exited normally (likely shutdown signal)
            break
        
        restart_count += 1
        
        if restart_count >= MAX_RESTARTS:
            logging.error(f"Max restarts ({MAX_RESTARTS}) reached. Exiting.")
            sys.exit(1)
        
        logging.warning(f"Restarting worker in {RESTART_DELAY} seconds...")
        time.sleep(RESTART_DELAY)
    
    logging.info("Supervisor exiting")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Supervisor stopped by user")
        sys.exit(0)

