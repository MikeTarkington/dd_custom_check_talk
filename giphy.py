# the following try/except block will make the custom check compatible with any Agent version
try:
    # first, try to import the base class from old versions of the Agent...
    from checks import AgentCheck
    # we will be playing with a metric derived from command line output so we're going to also import a class that will help us run sub process (bash) commands through the python runtime of the agent
    # https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks.utils.html#module-datadog_checks.base.utils.subprocess_output
    from datadog_checks.utils.subprocess_output import get_subprocess_output
except ImportError:
    # ...if the above failed, the check is running in Agent version 6 or later
    from datadog_checks.base.checks import AgentCheck
    from datadog_checks.utils.subprocess_output import get_subprocess_output

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"

class Giphy(AgentCheck):
    def check(self, instance):
        # using the agents get_subprocess_output() function, run the `pgrep` bash command
        # to get all process IDs matching a particular name
        pgrep_chrome, err, retcode = get_subprocess_output(
            ["pgrep", instance['process_name']], self.log, raise_on_empty_output=True)
        uni_pids = pgrep_chrome.split('\n') # get cleaned version of response without new line commands
        pids = []
        for pid in uni_pids: # change encoding of each process ID from the bash unicode to utf8 strings
            pids.append(pid.encode('utf8'))
        
        # for each ID found from `pgrep`, use `ps -p <pid> -o %mem` to collect mem usage for each and store
        # them as keys for a dict. if given key is valid (longer than 1), assign the value, otherwise assign 0
        mem_pcts = {}
        for id in pids:
            process_mem, err, retcode = get_subprocess_output(["ps", "-p", id, "-o", "%mem"], self.log, raise_on_empty_output=False)
            if len(process_mem.split('\n')) > 1:
                mem_pcts.update({id:float(process_mem.split('\n')[1].encode('utf8'))})
            else:
                mem_pcts.update({id:0})

        # sum the percentages for the mem usage for submission as the metric value
        total_mem_pct = sum(mem_pcts.values())
        tags = mem_pcts.keys()
        tags.append(instance['process_name'])
        self.gauge("{}.mem_pct".format(instance['process_name']), total_mem_pct, tags=tags)
