# Setup: 
# Windows:
1. Clone the repository to your local machine.
2. Install supported PY version for your IDE (for VSCode >= PY 3.9)
3. Install necessary libraries:
    * py -m pip install "pyyaml"
    * py -m pip install "aiohttp"
    * py -m pip install "asyncio"
4. A launch.json file has been included for VSCode by default that contains valid launch options.
5. Run via F5, and provide the full path to the YAML file in the prompt (ex: C:\VSProjects\Fetch\sre-take-home-exercise-python-main\sre-take-home-exercise-python-main\sample.yaml)

# Issue List
1. When the YAML entry didn't contain a Method field, a NoneType exception was throw. To fix, a method was introduced with a ternary check to default to GET in the case the value was missing.
- def get_method(endpoint):
     valFromFile = endpoint.get('method')
     # if no value in the file, we can assume that the correct method is GET
     return valFromFile if valFromFile != None else 'GET'

2. The domain parsing wasn't configured to handle possible port numbers in the URL. To fix, we added an extra call to the split method to remove any port inclusion.
- domain = endpoint["url"].split("//")[-1].split("/")[0].split(":")[0]

3. When calling a non-existent endpoint, too much time was consumed by the application. To resolve, a timeout value was added to the request parameters.
- async with session.request(method, url, headers=headers, json=body, timeout=1) as response:

4. To ensure that a check was performed every 15 seconds, and to increase the performance of checking indivdual endpoints in bulk, the system had to be refactored to be asynchronous and send requests in parallel. 
- Run the loop async: asyncio.run(monitor_loop_async(config))
- Dispatch each endpoint check and wait for them to complete: await asyncio.gather(*(endpoint_check_async(endpoint, session, domain_stats) for endpoint in yamlConfig))

5. When using new aiohttp ClientSession to call the provided endpoints, a ClientConnectorCertificateError exception was thrown. To fix, we bypassed ssl verification in the ClientSession object by providing a TCPConnector with ssl validation set to False.
- async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:

6. New aiohttp ClientSession request method doesn't track the elapsed time like the original request library, so this had to be calculated manually using the datetime library.
- startTime = datetime.datetime.now()
  elapsed = datetime.datetime.now() - startTime
  if 200 <= response.status < 300 and elapsed.microseconds <= 500000: