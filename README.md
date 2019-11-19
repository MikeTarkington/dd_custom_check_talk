<h2>Custom Agent Check 101</h2>

<h3>General Points</h3>

- Custom checks are typically used to submit custom events or metrics

- Agent runs checks using a python3 interpreter included with the agent itself

- Checks are just code that is run by the agent and can do pretty much anything the programmer wants within the permissions granted to the agent

- Every check needs to have a corresponding yaml file for configuration and every yaml needs to have at least one instance in it

- Default frequency for check runs is 15 seconds but this can be adjusted to a longer time frame by setting a higher number of seconds for the `min_collection_interval: <int>`.  This can be used to control the frequency of events/metric points sent to the platform

- All agent checks use the base class to access configuration properties set by the yaml:
https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks.checks.html#base

- Functions of the base class are used to send various metric types or events and to control various details such as check related metadata

- A good general reference tool that isn't particularly visible: https://github.com/DataDog/datadog-agent/blob/6.2.x/docs/dev/checks/python/check_api.md

<h3>Getting Started - Practice Check</h3>

1. Install/update the Datadog agent (for our exercise please install the Mac agent locally as we will use the browser GUI for convenience and certain commands used expect Unix/Mac)
https://app.datadoghq.com/account/settings#agent/mac

2. Go to the Giphy API docs quick start guide:

    - https://developers.giphy.com/docs/api/#quick-start-guide
    - Open "Create an An App" in a new browser tab
    - Create an account to login and get logged in
    - Create an app named `Giphy Check`
    - Description can be `Datadog testing with Giphy API data.`
    - Only check the box for using the API, we do not need the SDK and click ok to the prompt
    - Completing the above should then provide an API key, copy this and set it aside for now



3. Locate the following directories and create their respective files:
    
    Configuration file directory:
    
    ```bash
    cd /opt/datadog-agent/etc/conf.d
    mkdir giphy.d; touch giphy.d/giphy.yaml
    ```

    Custom check code:
    
    ```bash
    cd /opt/datadog-agent/etc/checks.d
    touch giphy.py
    ```

4. For the time being, in order to have the initial aspects of the check run at all as we begin to test, there needs to be some bare bones configuration in the corresponding yaml file
   
    ```bash
    # open it with a code editor like VS Code
    code /opt/datadog-agent/etc/conf.d/giphy.yaml
    ```

    Paste and save the following (note:keep the file open b/c we'll come back for edits):

    ```yaml
    init_config:

    instances:
      - min_collection_interval: 30
    
    ```

5. Begin with the code of the check file and start by adding import calls to give our check access to the `AgentCheck` class functions for sending events and metrics etc.

    ```bash
    # open it with a code editor like VS Code
    code /opt/datadog-agent/etc/conf.d/giphy.d/giphy.yaml
    ```

    ``` python
    # the following try/except block will make the custom check compatible with any Agent version
    try:
    # first, try to import the base class from old versions of the Agent...
        from checks import AgentCheck
    except ImportError:
    # ...if the above failed, the check is running in Agent version 6 or later
        from datadog_checks.checks import AgentCheck

    # content of the special variable __version__ will be shown in the Agent status page
    __version__ = "1.0.0"

    # import a class that will help us run sub process (bash) commands through the python runtime of the agent
    # https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks.utils.html#module-datadog_checks.base.utils.subprocess_output
    from datadog_checks.utils.subprocess_output import get_subprocess_output

    ```

6. To validate things are wired up correctly so far, start with a very basic test to check setup and add the code sample from our docs to the check file `giphy.py`.

    ```python
        class Giphy(AgentCheck):
            def check(self, instance):
                self.gauge('giphy.test', 1, tags=['TAG_KEY_1:TAG_VALUE', 'TAG_KEY_2:VALUE_2'])
    ```
    Notes about the sample code:
    - `giphy.test` is a string argument for how we've decided to name this metric
    - The `1` is just a hard coded value that will be submitted for the test but normally that would be a variable value
    - The third argument is just an array of tags we want added to this metric. Typically the keys/values would be some interpolated variable from the code logic rather than a hard coded value.  If handled irresponsibly, this can cause issues with high tag cardinality
    - Restart the agent and check status to see if the check ran
        - In Mac one can run `datadog-agent check giphy` to run that check exclusively, `datadog-agent status` or check the GUI via the dog bone icon from system tray
        - For good measure, check your personal DD account to get something like this in metric explorer/summary https://share.getcloudapp.com/kpud8l0K
        https://share.getcloudapp.com/4gu7rRDd

7. Having verified the fundamentals are in place, start building out more code in the check:

    - The agent gives us an `AgentCheck` class that we've imported so we're going to start by using that in order to gain access to the configurations carried in through the yaml file and fuctions for performing actions like metric or event submission.

```python
class Giphy(AgentCheck):

    @staticmethod
    def giph_search(key, search_term):
	offset = random.randint(0, 100)
	url = 'http://api.giphy.com/v1/gifs/search?q={}&api_key={}&limit=1&rating=g&offset={}'.format(search_term, key, offset)
	r = requests.get(url)
	json_r = json.loads(r.text)
	return json_r['data'][0]['images']['original']['url']

    def check(self, instance):
	print(instance)
	print(self.init_config)

	process_name = instance['process_name'] 
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
```

8. Now lets try to run this code before we go through and examine it more detail.  We can use the following command to run an individual check file through the agent as a mere test that won't actually submit data to Datadog.  This saves you from having to restart the agent and run the status/info command in order to debug your latest modifications to the check.  In Mac OS it looks like this but might have some variation depending on your system (documented [here](https://docs.datadoghq.com/developers/write_agent_check/?tab=agentv6#verifying-your-check)):

    `datadog-agent check <check name>`

    - At this point you've probably gotten an error.  Why is that?
    ![https://a.cl.ly/lluwLwZL](https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/lluwLwZL/Image+2019-11-18+at+3.33.37+PM.png?v=e37b1d46f22c4c314bb3071a296a4298)
    - The code sample uses values that are set in the yaml configuration file and includes them in each unique **instance** of the class when the agent runs this code.  Since the only value we've added to our yaml so far is `min_collection_interval`, we're going to need to go back and make sure we're providing the necessary configs.
    - Note the print statements which show the two raw python dictionary objects produced via `instance` and `self.init_config`
    - `self.init_config` will carry configurations used globally regarldess of the unique instace configurations, while `instance` is carrying configs specific to that particular run of the check
    - Return to your yaml file and add the following:
    ```yaml
    init_config:
        dd_api_key: <your_dd_api_key>
        giphy_key: <your_giphy_api_key>

    instances:
        - process_name: Google Chrome
          min_collection_interval: 30
          giphy_term: pro googler
        
        - process_name: Slack Helper
          min_collection_interval: 40
          giphy_term: slack master
    ```
    - Now that we've made those config changes lets run our check test again to get a look at the "massive gains":

    https://a.cl.ly/6quDlLkm
    ![https://a.cl.ly/6quDlLkm](https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/6quDlLkm/Image+2019-11-18+at+4.13.47+PM.png?v=8163677d730df1b4ff253ed009bf10a1)
    
    - NOTE: After configuring the giphy events properly, you might still occasionally get an error like the one below when running the check verification test command.  I believe this is due to  API call limits from Giphy that will cause an error response.  This should not be a problem in the actual check at the collection interval we're using.
    https://a.cl.ly/NQue0ddP
    - Having made those changes, we have a working custom agent check that sends events to Datadog so we could restart our agent with the dog bone icon in the Mac system tray. Shortly after doing so, check the event stream for those events.
    
    ![https://a.cl.ly/JruwR7gA](https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/JruwR7gA/Image+2019-11-18+at+4.22.25+PM.png?v=04c58580e66dd4044e399e7accd9681f)

9. With a working custom check that submits events using the result of data from an external API call, we reveal a power in the agent that rivals that of our crawler based integrations. They use third party APIs to schedule data collection and transmission to DD on our customers behalf.  This check has a schedule based on agent collection interval and can do pretty much anything python can do.  Lets break down the code so far block by block.
    - The first block under our check class is defining a function that extends the capability of the check class.  The `@staticmethod` declaration is used to help us define a class level method/that could be used for reducing code by consilidating helpful steps one might need to repeat into one function rather than relying on sequential repeats of that code in the script.  In this case, we're using the function to make an API call that accepts dynamic paramenters from the configuration file.  We didn't have to make it into a function but it's worth demonstrating that point in case you're writing blocks that would be reusable in the check.
    
    ```python
    @staticmethod
    def giph_search(key, search_term):
        offset = random.randint(0, 100)
        url = 'http://api.giphy.com/v1/gifs/search?q={}&api_key={}&limit=1&rating=g&offset={}'.format(search_term, key, offset)
        r = requests.get(url)
        json_r = json.loads(r.text)
        return json_r['data'][0]['images']['original']['url']
    ```
    - We call this function later and use `self.init_config['giphy_key']` and `instance['giphy_term]` to read specific config values from the two objects we printed earler and apply them as `key` and `search_term` arguments for the function:

    ```python
    giph_url = self.giph_search(
            self.init_config['giphy_key'], instance['giphy_term']) 
    ```
    - Those values are in turn used by the function to build the `url` variable necessary for making an accepted call to the Giphy API search endpoint.
    - This function calls for a single gif randomly selected from the results using the `randint()` and then parses the json response looking for the direct link URL attribute to return.  We then use that `giph_url` value in the `msg_text` string argument that we pass for events. Finally, we use the built in `AgentCheck` class function `self.event(event_dict)` to send the `event_dict` object info to DD.

```python
	event_dict = {
		"timestamp": time.time(),
		"event_type": "Giph from {}".format(process_name),
		"api_key": self.init_config['dd_api_key'],
		"msg_title": "Giph from {}".format(process_name),
		"msg_text": "![{}]({})".format(process_name, giph_url),
		"tags": ["giphy_check", "process:{}".format(process_name)]
	}
	self.event(event_dict)
```

10. Having covered an example of event submission and using an API within a check, lets now take a look at submitting metrics and additionally, a metric that is derived from command line capabilities on the system rather than just python itself.  Note the this example should reinfoce some of the possiblities we should consider for doing a variety of things like making metrics out of database calls by entering its respective shell and tracking the response to queries, or perhaps other levels of infrastructure in tracking results of thing like network activity or Docker/Kube commands. The general theme is that if Datadog doesn't already do it for our customers, there's a reasonable chance there's a way to get it done via custom agent check.

11. Before we start modifying the check, lets take a look at the actual source of the Data that the check will be utilizing.
    - If we go to terminal and run `top`, we'll see a great deal of info about real time processes and their resource consumption.  This gives us a sense of the processes that are presently running on our host (your Mac), listing them by ID and sorting them by info like what perecentage of memory or CPU they're using.
    - If you're currently running a Chrome browser, you'll likely see a number of process IDs for Chrome, some of those are for individual open tabs, or extensions running, and a few are baseline processes for the browser.
    - Our next steps will be to create metrics that collect the memory for a given process distinguishing them both by ID and by their total consumption required to support running the overall application.  We're going to do this for both Google Chrome and for Slack.

12. Hit `control + c` to exit the `top` process that was running in terminal and now run `pgrep Google Chrome`
    - This returns a list of process IDs sharing that process name
    - Grab one of the IDs for a Chrome process and run `ps -p <pid> -o %mem` which will return the percentage value of system memory consumed by that process at the time the command was run
    - These values will be used for our memory consumption metrics as we essentially recreate our own mini version of the core agent [process check](https://docs.datadoghq.com/integrations/process/)

13. The key parts of this are exemplified in our documentation [here](https://docs.datadoghq.com/developers/write_agent_check/?tab=agentv6#writing-checks-that-run-command-line-programs) and there's a good example of how to create a metric out of a count of files within a local directory.  With a little creative thinking, consider that one might also access the contents of such files and produce metrics by analyzing them.  For example, one could use code to analyze a series of log files to produce metrics based on values of their attributes if pipelines, faceting, and log analytics would somewhow not meet their use case.
    - This supporting documentation has more thorough reference material for the available functions included in the `AgentCheck` class and its utilities:
        - The base class has a number of methods but will be focused on the `guage()` method for metric submission as it is very common: https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks.checks.html#base
        - The key utility function we're going to be using is `get_subprocess_output()` https://datadog-checks-base.readthedocs.io/en/latest/datadog_checks.utils.html#module-datadog_checks.base.utils.subprocess_output

14. With these factors in mind, edit the check file to include the following thus completing our check that will include process memory metrics and giphy events.  Append the following to your check file and correct for indentation such that it's in line with `self.event(event_dict)` where we left off: 

    ```python
    # using the agents get_subprocess_output() function, run the `pgrep` bash command
    # to get all process IDs matching a particular name
    pgrep_chrome, err, retcode = get_subprocess_output(
        ["pgrep", process_name], self.log, raise_on_empty_output=True)
    uni_pids = pgrep_chrome.split('\n')
    mem_pcts = {}
    for pid in uni_pids:
        # change unicode from bash response to utf8
        id = pid.encode('utf8')
        # for each id, use subprocess function to run `ps -p <pid> -o %mem` to get its
        # percent of memory usage
        process_mem, err, retcode = get_subprocess_output(
            ["ps", "-p", id, "-o", "%mem"], self.log, raise_on_empty_output=False)
        # if the key (pid) has a value (pct memory), add it to the mem_pcts dictionary
        # with the value in utf8 encoding and stored as a float
        if len(process_mem.split('\n')) > 1:
            mem_pcts.update(
                {id: float(process_mem.split('\n')[1].encode('utf8'))})
        else:
            mem_pcts.update({id: 0})
        # create a tag string out of the process name and id values currently run 
        # in the loop and then use self.guage() to submit a unique tagged metric
        # for each process
        pid_tag = "{}_pid:{}".format(process_name, id)
        self.gauge("{}.mem_pct".format(process_name),
                    mem_pcts[id], tags=[pid_tag, process_name])

    # make tags list from the process IDs, convert them to kv pairs with `pid` as the key,
    # add the general tag for the overall process name
    tags = mem_pcts.keys()
    for i, tag in enumerate(tags):
        tags[i] = "{}_pid:{}".format(process_name, tag)
    tags.append(process_name)

    # sum the percentages for the mem usage for submission as the metric value
    total_mem_pct = sum(mem_pcts.values())

    self.gauge("{}.mem_pct.total".format(process_name),
                total_mem_pct, tags=[process_name])
    ```

    - The comments in the code explain each step taken
    - Restart the agent and begin looking for your custom metrics with metric explorer or a dashboard
    - Look at metric summary for your `Google_Chrome.mem_pct` metric and notice the number of "distinct metrics" and total tag count for the metric (this will vary depending on how many tabs/extensions running and how many different processes there have been).  It's valuable to recognize this as one potential way a customer could apply tags in a fashion that causes high cardinality and potentially unqueryable metrics if they looped through thousands of PIDs for example, submitted the metric from multiple hosts, etc, these could have multiplicative effects on the number of distinct metrics/unique timeseries as we have to enable them to query based on every possible tag combination.
    ![https://a.cl.ly/OAuxXq9W](https://p-qKFgO2.t2.n0.cdn.getcloudapp.com/items/OAuxXq9W/Image+2019-11-18+at+7.52.55+PM.png?v=1feb2b666f777b07f76fd671cdeeca2b)
