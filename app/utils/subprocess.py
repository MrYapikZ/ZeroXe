import subprocess
import time
import threading

class SubprocessServices:
    @staticmethod
    def run_command(command: list):
        subprocess.run(command, check=True)

    @staticmethod
    def popen_command(command: list):
        process = subprocess.Popen(command, start_new_session=True)
    
    @staticmethod
    def popen_command_with_callback(command: list, callback=None):
        def monitor_process():
            process = subprocess.Popen(command, start_new_session=True)
            while process.poll() is None:
                time.sleep(1)
            if callback:
                callback()
        thread = threading.Thread(target=monitor_process, daemon=True)
        thread.start()