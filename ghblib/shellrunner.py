import subprocess
import threading
import time

class ShellRunnerTimeout(Exception):
    def __init__(self, cmd):
        self.cmd = ' '.join(cmd)

class ShellRunnerFailed(Exception):
    def __init__(self, cmd, retval):
        self.cmd = ' '.join(cmd)
        self.retval = retval

class ShellRunner(object):
    def __init__(self, cmd, logfile):
        self.cmd = cmd
        self.logfile = logfile
        self.process = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(self.cmd, stdout=self.logfile, stderr=subprocess.STDOUT, close_fds=True)
            self.process.wait()

        start_time = time.time()
        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
            raise ShellRunnerTimeout(self.cmd)

        # TODO: Get the return code and raise if != 0

        # Return the remaining time
        return timeout - (time.time() - start_time)
