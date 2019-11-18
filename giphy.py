# the following try/except block will make the custom check compatible with any Agent version
try:
    import json
    import requests
    import random
    import time
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

    @staticmethod
    def giph_search(key, search_term):
        offset = random.randint(0, 100)
        url = 'http://api.giphy.com/v1/gifs/search?q={}&api_key={}&limit=1&rating=g&offset={}'.format(search_term, key, offset)
        r = requests.get(url)
        json_r = json.loads(r.text)
        return json_r['data'][0]['images']['original']['url']

    def check(self, instance):
        # access instance level configs by throught he `instance` object so they can used throughout
        process_name = instance['process_name'] 
        # using the agents get_subprocess_output() function, run the `pgrep` bash command
        # to get all process IDs matching a particular name
        pgrep_chrome, err, retcode = get_subprocess_output(
            ["pgrep", process_name], self.log, raise_on_empty_output=True)
        uni_pids = pgrep_chrome.split('\n')
        mem_pcts = {}
        for pid in uni_pids:
            id = pid.encode('utf8') # change unicode from bash response to utf8
            # for each id, use subprocess function to run `ps -p <pid> -o %mem` to get its
            # percent of memory usage
            process_mem, err, retcode = get_subprocess_output(
                ["ps", "-p", id, "-o", "%mem"], self.log, raise_on_empty_output = False)
            # if the key (pid) has a value (pct memory), add it to the mem_pcts dictionary
            # with the value in utf8 encoding and stored as a float
            if len(process_mem.split('\n')) > 1:
                mem_pcts.update({id:float(process_mem.split('\n')[1].encode('utf8'))})
            else:
                mem_pcts.update({id:0})
            pid_tag = "{}_pid:{}".format(process_name, id)
            self.gauge("{}.mem_pct".format(process_name), mem_pcts[id], tags=[pid_tag, process_name])
            

        # make tags list from the process IDs, convert them to kv pairs with `pid` as the key,
        # add the general tag for the overall process name
        tags = mem_pcts.keys()        
        for i, tag in enumerate(tags):
            tags[i] = "{}_pid:{}".format(process_name, tag)
        tags.append(process_name)

        # sum the percentages for the mem usage for submission as the metric value
        total_mem_pct = sum(mem_pcts.values())

        self.gauge("{}.mem_pct.total".format(process_name), total_mem_pct, tags=[process_name])

        giph_url = self.giph_search(self.init_config['giphy_key'], instance['giphy_term'])

        event_dict = {
            "timestamp": time.time(),
            "event_type": "Giph from {}".format(process_name),
            "api_key": self.init_config['dd_api_key'],
            "msg_title": "Giph from {}".format(process_name),
            "msg_text": "![{}]({})".format(process_name, giph_url),
            "tags": ["giphy_check", "process:{}".format(process_name)]
        }

        self.event(event_dict)
