import subprocess

class SubprocessServices:
    @staticmethod
    def run_command(command: list):
        subprocess.run(command, check=True)

    @staticmethod
    def popen_command(command: list):
        subprocess.Popen(command, start_new_session=True)