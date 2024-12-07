# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import os
import unittest

import requests
unittest.TestLoader.sortTestMethodsUsing = None
#unittest.TestLoader.sortTestMethodsUsing = lambda self, a, b: (a < b) - (a > b)
class RunCmd:

    def run(self, cmd):
        import subprocess

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        #print("Command exit status/return code : ", p_status)
        return p_status, output

class ProfileUtility:

  def __init__(self):
    #self.servicename = service_name
    self.docker_name = ""
    self.start_profile_func = None 
    self.stop_profile_func = None 
    return

  def set_profile_funcs(self,  docker_name):
    if docker_name == "vllm-service":
        self.docker_name = docker_name
        self.start_profile_func = self.vllm_start_profile 
        self.stop_profile_func = self.vllm_stop_profile
        self.get_profile_result_func = self.vllm_get_profile_result
    else:
        self.start_profile_func = None 
        self.stop_profile_func = None
        self.docker_name = ""

  def vllm_start_profile(self, ip, port, data):
      print("vllm_start_profile")
      # Send out test request
      endpoint = ip + ':' + port + '/' + "start_profile"
      data.pop("messages")
      print(data)
      response = requests.post(
          url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
      )
      return

  def vllm_stop_profile(self, ip, port, data):
      print("vllm_stop_profile")
      endpoint = ip + ':' + port + '/' + "stop_profile"
      data.pop("messages")
      print(data)
      response = requests.post(
          url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
      )
      return

  def vllm_get_profile_result(self, result_folder):
      print("vllm_get_profile_result")
      result_folder_path = "./" + result_folder
      cmd = "docker cp " + self.docker_name + ":/mnt " + result_folder_path
      status, output = RunCmd().run(cmd)

      pattern = r".*\.pt.trace.json.gz $"  # Match all files ending with ".txt"
      files_list = []
      for filename in os.listdir(result_folder_path):
        if re.search(pattern, filename):
            print(filename)
            files_list.append(filename)
      return files_list

class TriageUtility:

  def __init__(self, filename):
    self.class_name = filename.split('.')[0]
    self.filename = filename #self.__class__.__name__
    self.prof_utils = ProfileUtility()
    return

  def load_input_data(self,  service):
    class_name = self.class_name
    with open(self.filename, "r") as file:
        try:
            data = json.load(file)
        except:
            print("json load failed: " + self.filename)
            pass
    for i in data[class_name]:
        #print(i["service"])
        #print(service)
        if i["service"] == service:
            i.pop("service")
            port = i.pop("port")
            endpoint = i.pop("endpoint")
            output = i.pop("output")
            return i, port, endpoint, output
    return None

  def service_health_check(self, ip, port, triage_report, triage_level):
    # Health Check
    if triage_level < 1:
        return
    endpoint = ip + ':' + port + "/v1/health_check"
    response = requests.get(
        url=endpoint, headers={"Content-Type": "application/json"}, proxies={"http": None}
    )
    triage_report.update_docker_report(port, "Health", response.status_code == 200)
    return response.status_code

  def service_test(self, ip, port, endpoint_name, data, triage_report, triage_level):
    if triage_level < 2:
        return

    # Start Profiling
    docker_name = triage_report.get_docker_name(port)
    self.prof_utils.set_profile_funcs(docker_name)
    if triage_level > 2 and self.prof_utils.start_profile_func != None:
        print("start profiling")
        tmp_data = data.copy()
        self.prof_utils.start_profile_func(ip, port, tmp_data)

    # Send out test request
    endpoint = ip + ':' + port + '/' + endpoint_name
    response = requests.post(
        url=endpoint, json=data, headers={"Content-Type": "application/json"}, proxies={"http": None}
    )

    # End Profiling
    if triage_level > 2 and self.prof_utils.stop_profile_func != None:
        print("end profiling")
        tmp_data = data.copy()
        self.prof_utils.stop_profile_func(ip, port, tmp_data)
        # Save Profile results
        profile_files_list = self.prof_utils.get_profile_result_func(triage_report.result_folder_name)
        if profile_files_list != []:
            triage_report.update_docker_report(port, "Profile", profile_files_list[0])

    triage_report.update_docker_report(port, "Test", response.status_code == 200)
    log_fname = triage_report.dump_docker_logs(port)     
    triage_report.update_docker_report(port, "Log", log_fname)
    return response.status_code

  def service_statistics(self, ip, port, triage_report, triage_level):
    # statistics
    if triage_level < 1:
        return
    endpoint = ip + ':' + port + "/v1/statistics"
    response = requests.get(
        url=endpoint, headers={"Content-Type": "application/json"}, proxies={"http": None}
    )
    triage_report.update_docker_report(port, "Stats", response.status_code == 200)
    return response.status_code


class TriageReport:
  def __init__(self, name):
    self.name = name
    self.env_vars_df = None
    self.system_info_df = None
    self.docker_ps = ''
    self.docker_ps_df = None
    self.docker_report_df = None
    import datetime
    d = datetime.datetime.now()
    dateinfo = d.strftime("%m-%d_%H-%M")
    self.result_folder_name = self.name + '_' + dateinfo
    import os
    if not os.path.exists(self.result_folder_name):
        os.makedirs(self.result_folder_name)

  def parse_docker_ps_to_df(self, output):
    lines = []
    columns = []
    rows = []
    for line in output.splitlines():
        line= str(line)[2:-1]
        row = line.split()
        if columns != []:
            #print(row)
            row.pop(1)
            if len(row) > 3:
                for i in range(len(row)):
                    if i >= 1 and i < (len(row) -1):
                        pr = row.pop(2)
            row[1] = row[1].split("->")[0]
            row[1] = row[1].split(':')[-1]
            rows.append(row)
        else:
            columns = row

    import pandas as pd
    df = pd.DataFrame(rows,columns=columns )
    #print(df)
    self.docker_ps_df = df 
    return

  def init_docker_report(self):

      df = self.docker_ps_df.copy()
      #print(df.shape[0])
      new_col = [''] * df.shape[0]
      df['Health'] = new_col
      df['Test'] = new_col
      df['Stats'] = new_col
      df['Log'] = new_col
      df['Profile'] = new_col
      #print(df)
      self.docker_report_df = df

  def update_docker_report(self, port, key, value):

    df = self.docker_report_df
    #docker_index = df.loc[df['PORTS'] == port]
    index_list = df.index[df['PORTS'] == port].tolist()
    #print("\n update index:" + index_list)
    df.at[index_list[0], key] = value
    #print(df)
    return

  def get_docker_name(self, port):

    df =self.docker_ps_df 
    docker_name = df.loc[df['PORTS'] == port,"NAMES"].values[0]
    return docker_name

  def dump_docker_logs(self, port):

    df =self.docker_ps_df 
    docker_name = df.loc[df['PORTS'] == port,"NAMES"].values[0]

    cmd = "docker logs " + docker_name
    status, output = RunCmd().run(cmd)
    output = output.decode('utf-8')
    filename = docker_name + "_docker_log.txt"
    self.dump_log_to_file(output, filename)
    return filename

  def dump_log_to_file(self, output, filename):
    #print(filename)
    filepath = self.result_folder_name + os.sep + filename
    fd = open(filepath, "w")  # append mode
    fd.write(output)
    fd.close()
    return
  def generate_triage_report(self):
    import os
    import re
    print(" Example Name:" + self.name)
    print(" ### ENV Variables###")
    print(self.env_vars_df)
    print(" ### System Info###")
    print(self.system_info_df)
    self.docker_ps_df = None
    print(" ### Servces Status###")
    print(self.docker_report_df)

    report_name = self.name + '.html'
    
    report_path = self.result_folder_name + os.sep + report_name

    # Log Files

    docker_log_html_content = ''
    pattern = r".*\_docker_log.txt$"  # Match all files ending with ".txt"
    for filename in os.listdir(self.result_folder_name):
        if re.search(pattern, filename):
            html_content = " \n\n <h2>" + filename +"</h2>\n" + "<iframe src=" + '"' + filename + '"' + " width=" + '"' + "1000" + '"' + "height=" + '"' + "300" + '"' +"></iframe>"
            docker_log_html_content = docker_log_html_content + html_content



    with open(report_path, 'w') as hfile:
        hfile.write(
                "\n\n <h1>1. Servces Status</h1>\n\n"
                + self.docker_report_df.to_html()
                + "\n\n <h1>2. System Info</h1>\n\n"
                + self.system_info_df.head().to_html()
                + "\n\n <h1>3. Environment Variables</h1>\n\n"
                + self.env_vars_df.head().to_html()
                + "\n\n <h1>4. Docker Log Files</h1>\n\n"
                + docker_log_html_content)

    print("\nReport File is : " + report_path)
    import shutil
    shutil.make_archive(self.result_folder_name, 'zip', self.result_folder_name)
    return


class ChatQnA(unittest.TestCase):
    def setUp(self):
        self.triage_level = triage_level
        self.triage_report = triage_report
        self.ip = "http://0.0.0.0"
        #print(command_line_param)
        #print(self.config)
        self.datafile = DataJsonFileName
        self.classname = DataJsonFileName.split('.')[0]
        self.utils = TriageUtility(self.datafile)
        return

    def tearDown(self):
        return

    def test_1_env_vars(self):
        EmptyVar = False

        service_name = "env"
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        rows = []
        from os import environ
        for key, val in data.items():
            var = environ.get(key)
            row = [ key, var, val]
            rows.append(row)
            if val is True:
                if var == None:
                    EmptyVar = True
        import pandas as pd
        columns = ['env','value','required']
        df = pd.DataFrame(rows,columns=columns )
        #print(df)
        self.triage_report.env_vars_df = df
        self.assertEqual(EmptyVar, False)

    def test_2_system(self):

        import socket
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)

        import platform

        system_info = platform.uname()

        import pandas as pd
        rows = []
        columns = ['info','value']
        rows.append(['hostname', hostname])
        rows.append(['ip', IPAddr])
        rows.append(['system', system_info.system])
        rows.append(['node', system_info.node])
        rows.append(['release', system_info.release])
        rows.append(['version', system_info.version])
        rows.append(['machine', system_info.machine])
        rows.append(['processor', system_info.processor])
        df = pd.DataFrame(rows,columns=columns )
        #print(df)
        self.triage_report.system_info_df = df

        #status, output = RunCmd().run("docker ps")
        status, output = RunCmd().run("docker ps --format '"'table {{.Image}}\t{{.Ports}}\t{{.Names}}'"'")
        self.triage_report.parse_docker_ps_to_df(output)
        self.triage_report.docker_ps = output

        self.triage_report.init_docker_report() 

        self.assertEqual(False, False)



    def test_3_embed(self):

        service_name = "embed"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

    def test_4_dataprep(self):

        service_name = "dataprep"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Health Check
        response_status_code = self.utils.service_health_check(self.ip, port, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

        # Testing
        #response_status_code  = utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        #self.assertEqual(response_status_code, 200)

        # Statistic
        response_status_code = self.utils.service_statistics(self.ip, port, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)


    def test_5_retrival(self):
        service_name = "retrieval"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        import random
        embedding = [random.uniform(-1, 1) for _ in range(768)]
        data = {"text": '"text":"test","embedding":${embedding}'}
        self.assertNotEqual(data, None)

        # Health Check
        response_status_code = self.utils.service_health_check(self.ip, port, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

        # Statistic
        response_status_code = self.utils.service_statistics(self.ip, port, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

    def test_6_rerank(self):

        service_name = "rerank"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

    def test_7_nginx(self):

        service_name = "nginx"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

    def test_8_llm(self):

        service_name = "llm"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

    def test_9_mega(self):

        service_name = "mega"
        #Get configs/data
        data, port, endpoint_name, output = self.utils.load_input_data(service_name)
        self.assertNotEqual(data, None)

        # Health Check
        response_status_code = self.utils.service_health_check(self.ip, port, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)

        # Testing
        response_status_code  = self.utils.service_test(self.ip, port, endpoint_name, data, self.triage_report, self.triage_level)
        self.assertEqual(response_status_code, 200)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise IndexError("Please provide data json file.") 
    triage_level = 2 # low, medium, high
    DataJsonFileName = sys.argv[1]  #"ChatQnA_Xeon.json"
    triage_report = TriageReport(DataJsonFileName)
    test_loader = unittest.TestLoader()
    #test_loader.sortTestMethodsUsing = lambda self, a, b: (a < b) - (a > b)
    suite = test_loader.loadTestsFromTestCase(ChatQnA)
    unittest.TextTestRunner(verbosity=3).run(suite)
    triage_report.generate_triage_report()
