import re
import pandas as pd

# all the comparison handlers below accept a list of reports as input
# by the time that these functions are called in ReportsView,
# we know that the reports in the input list:
# 1. all belong to the same datapack type (e.g. eng-USA-GEN)
# 2. all belong to the same testing type (e.g. accuracy 8k)
# 3. all have a test result file that was uploaded during submission

def compare_accuracy(reports):
    res = []
    report_files = [report.file_report.path for report in reports]

    # accuracy tests produce a "result.txt" file
    # the metric of interest for comparison is the WER difference
    # i.e. the number at the end of the file
    # therefore, we go through the uploaded files one by one and get the WER difference

    for report_file in report_files:
        with open(report_file, "r") as f:
            content = f.readlines()
            result_line = content[2]
            WER_diff = result_line.split(" ")[-1].replace("\n", "")
            res.append(WER_diff)

    return res

def compare_travel_corpus(reports):
    report_files = [report.file_report.path for report in reports]

    # travel corpus tests produce a "console_output_Obfuscated.txt"
    # in the file, each block of text corresponds to one test case

    # within each block, there is a line that starts with "response:"
    # the # of times we encounter a line that starts with "response:" == the # of test cases

    # errors will be of the following format:
    #
    #   mine : mill quatre cent seize
    #   yours: quatre cent seize
    #
    # where mine == expected and yours == actual

    # therefore, the number of failed test cases is equal to the number of times
    # a sentence with "mine :" is encountered

    # there are different types of failures
    # one type of failure we're particularly interested in is intent failure
    # everytime we encounter a sentence with "mine :", we see if it's an intent failure

    results_of_reports = []
    for report_file in report_files:
        with open(report_file, "r") as f:
            n_test_cases = 0
            n_fails = 0
            n_intent_fails = 0
            fails = []
            expected = []

            while True:
                line = f.readline()
                if not line:
                    break

                if re.search("^response:", line):
                    n_test_cases += 1
                elif re.search("mine :", line):
                    n_fails += 1
                    fails.append(line.strip())
                    if re.search("[A-Z]{1,}_[A-Z]{1,}", line):
                        n_intent_fails += 1
                elif re.search("yours:", line):
                    expected.append(line.strip())

            results_of_reports.append({
                "n_test_cases": n_test_cases,
                "n_fails": n_fails,
                "n_intent_fails": n_intent_fails,
                "fail_rate": n_fails/n_test_cases if n_test_cases else 0,
                "intent_fail_rate": n_intent_fails/n_test_cases if n_test_cases else 0,
                "fails_and_expected": zip(fails, expected),
            })

    return results_of_reports

def compare_NTE5(reports):
    # NTE5 testing type tests various "features" for their functionality (to see if they work)
    # there will be multiple test cases for each feature
    # a feature is deemed to be functional if at least one of its test cases passes

    # NTE5 test produces a csv file
    # each line corresponds to a single test case
    # for example:
    #
    # TestCase, Verdict, Description, WorkProduct, TestType, TestMethod, Tags, TestInput, TestOutput, TestClass
    # test001_2_formatting_scheme_date, Pass,, , Functional, Automated,, , , test_dp_deu_deu_h2h_exp.DatapackTest
    # test001_3_formatting_scheme_date, Fail,, , Functional, Automated,, , , test_dp_deu_deu_h2h_exp.DatapackTest
    # ...
    #
    # only the "TestCase" and "Verdict" columns are of interest

    report_files = [report.file_report.path for report in reports]

    # read all the csv files into dataframes
    dataframes = []
    for report_file in report_files:
        df = pd.read_csv(report_file)
        dataframes.append(df)

    # for each csv file, get all the test cases and their verdicts
    results_per_report = []
    # results_per_report = [
    # {
    #   file_1_testcase_1: result,
    #   file_1_testcase_2: result,
    #   file_1_testcase_3: result,
    #   ...
    # },
    # {
    #   file_2_testcase_1: result,
    #   file_2_testcase_2: result,
    #   file_2_testcase_3: result,
    #   ...
    # },
    # ...
    # ]
    for df in dataframes:
        res = {}
        for ind in df.index:
            res[df["TestCase"][ind]] = df["Verdict"][ind]
        results_per_report.append(res)

    # for the NTE5 comparison, we would like to compare results of features
    # since the comparison will be done between datapacks of the same type
    # most of the time, the features tested (and the test cases) will be the same
    # however, there may have been added/removed features (and test cases)

    # all unique test cases
    all_test_cases = set()
    # all unique features
    all_features = set()
    feature_results_per_report = []
    # feature_results_per_report = [
    # {
    #   file_1_feature_1: result,
    #   file_1_feature_2: result,
    #   file_1_feature_3: result,
    #   ...
    # },
    # {
    #   file_2_feature_1: result,
    #   file_2_feature_2: result,
    #   file_2_feature_3: result,
    #   ...
    # },
    # ...
    # ]
    for results in results_per_report:
        res = {}
        for test_case, result in results.items():
            all_test_cases.add(test_case)

            # determine which feature a test case is for (the feature is in the test case name)
            # test case names are one of two formats:
            # 1. test001_2_formatting_scheme_date
            #   - feature is "formatting_scheme_date"
            # 2. test_exp_11_2_3_1_opt_censor_full_words_censor_profanities
            #   - feature is "opt_censor_full_words_censor_profanities"
            prefix, rest = test_case.split("_", 1)
            if prefix == "test":
                feature = rest.split("_", 5)[5]
            else:
                feature = ""
                rest_split = rest.split("_")
                for i, chunk in enumerate(rest_split):
                    if not chunk.isdigit():
                        feature = "_".join(rest_split[i:])
                        break
            all_features.add(feature)
            if feature not in res:
                # change "Error" => "Fail"
                res[feature] = result if result != "Error" else "Fail"
            # a feature is functional if even 1 test case passes
            elif res[feature] == "Fail" and result == "Pass":
                res[feature] = "Pass"
        feature_results_per_report.append(res)

    features_and_results = {}
    # features_and_results = {
    #   feature_1: [ file_1_result, file_2_result, file_3_result, ... ],
    #   feature_2: [ file_1_result, file_2_result, file_3_result, ... ],
    #   feature_3: [ file_1_result, file_2_result, file_3_result, ... ],
    #   ...
    # }
    for feature in all_features:
        res = []
        for feature_results in feature_results_per_report:
            if feature in feature_results:
                res.append(feature_results[feature])
            else:
                res.append(None)
        features_and_results[feature] = res

    test_cases_w_diff_results = {}
    # test_cases_w_diff_results = {
    #   testcase_1: [ file_1_result, file_2_result, file_3_result, ... ],
    #   testcase_2: [ file_1_result, file_2_result, file_3_result, ... ],
    #   testcase_3: [ file_1_result, file_2_result, file_3_result, ... ],
    #   ...
    # }
    common_failed_test_cases = []
    common_passed_test_cases = []
    for test_case in all_test_cases:
        results_for_tc = []
        for results in results_per_report:
            if test_case in results:
                results_for_tc.append(results[test_case])
            else:
                results_for_tc.append(None)
        if len(set(results_for_tc)) == 1:
            if results_for_tc[0] == "Pass":
                common_passed_test_cases.append(test_case)
            else:
                common_failed_test_cases.append(test_case)
        else:
            test_cases_w_diff_results[test_case] = results_for_tc

    return {
        "test_cases_w_diff_results": test_cases_w_diff_results,
        "common_failed_test_cases": common_failed_test_cases,
        "common_passed_test_cases": common_passed_test_cases,
        "features_and_results": features_and_results,
    }

def compare_load(reports):
    report_files = [report.file_report.path for report in reports]

    res = {
        "preloaded_dlm": [],
        "no_dlm": [],
        "dynamic_dlm_100_oovs": [],
        "dynamic_dlm_1000_oovs": [],
        "dynamic_dlm_10000_oovs": [],
    }
    for report_file in report_files:
        df = pd.read_excel(report_file)
        ##############################################
        # a string of the following format is expected:
        #    krypton distribution:   sequential preloaded (18 kryptons) - parallel noDLM/dynamic  (15 kryptons - i.e. 2/4/5/4 kr)
        ##############################################
        first_row = df.iloc[0, 0]
        substrings_bw_brackets = re.findall(r'\(.*?\)', first_row)
        preloaded_dlm = re.findall('\d+', substrings_bw_brackets[0])[0]
        no_dlm = re.findall('\d+', substrings_bw_brackets[1])[1]
        dynamic_dlm_100_oovs = re.findall('\d+', substrings_bw_brackets[1])[2]
        dynamic_dlm_1000_oovs = re.findall('\d+', substrings_bw_brackets[1])[3]
        dynamic_dlm_10000_oovs = re.findall('\d+', substrings_bw_brackets[1])[4]

        res["preloaded_dlm"].append(preloaded_dlm)
        res["no_dlm"].append(no_dlm)
        res["dynamic_dlm_100_oovs"].append(dynamic_dlm_100_oovs)
        res["dynamic_dlm_1000_oovs"].append(dynamic_dlm_1000_oovs)
        res["dynamic_dlm_10000_oovs"].append(dynamic_dlm_10000_oovs)

    return res


# Input: a file pointer to a load test with the extension ".txt"
# Parses the entire contents of a load test file, test-by-test
# Returns: a dictionary with the following format:
# {
# "loadTest100_oov-20221129-221043-19ch": {
#     "kryptons": "19",
#     "stats": {
#         "audio": result,
#         "audiotx": result,
#         "lag": result,
#         "rec": result,
#         "conf": result,
#         "latency": result,
#         "cpl": result
#     },
#     "monitors": [
#         {
#             "host": result,
#             "cpu": result,
#             "mem": result
#         }, ...
#     ],
#     "calls": result,
#     "recognitions": result,
#     "success": result
# }, ...
def parse_load_test_txt(load_test):
    testHeader = re.compile("^loadTest.*ch:")
    testNameIndexMap = {}
    testMap = {}
    index = 0
    loadTestLines = load_test.read().splitlines()

    for line in loadTestLines:
        match = testHeader.search(line)

        if match:  # encountered novel test
            testName = match.group(0)[:-1]
            testNameIndexMap[str(index)] = testName
        index += 1

    breakPoints = []
    for key in testNameIndexMap:
        breakPoints.append(int(key))

    n = len(loadTestLines)
    breakPoints.append(n)
    startLine = breakPoints[0]

    for bp in breakPoints[1:]:
        testNameKey = None
        for i in range(startLine, bp):
            # parse inner lines of this test case
            if str(i) in testNameIndexMap:
                testNameKey = testNameIndexMap[str(i)]
                testMap[testNameKey] = {}
                testMap[testNameKey]["kryptons"] = loadTestLines[i].split(
                    "-")[-1].split("ch")[0]
                testMap[testNameKey]["stats"] = {}
                testMap[testNameKey]["monitors"] = []
                testMap[testNameKey]["errors"] = []
                continue
            if " calls" in loadTestLines[i]:
                numCalls = loadTestLines[i].split()[0]
                testMap[testNameKey]["calls"] = numCalls
                continue
            if " recognitions:" in loadTestLines[i]:
                numRecognitions = loadTestLines[i].split()[0]
                testMap[testNameKey]["recognitions"] = numRecognitions
                continue
            if " Success" in loadTestLines[i]:
                numSuccess = loadTestLines[i].split()[0]
                testMap[testNameKey]["success"] = numSuccess

                # parse errors below success until stats
                errInd = i +1
                while "stats" not in loadTestLines[errInd]:
                    testMap[testNameKey]["errors"].append(loadTestLines[errInd].strip())
                    errInd += 1
                continue
            if "stats:" in loadTestLines[i]:
                j = i+1
                while "monitors" not in loadTestLines[j]:
                    if "latency " in loadTestLines[j]:
                        latency = loadTestLines[j].split()
                        testMap[testNameKey]["stats"]["avg_latency"] = latency[1][:-1]
                        testMap[testNameKey]["stats"]["95%_latency"] = latency[-1]
                    elif "cpl " in loadTestLines[j]:
                        cpl = loadTestLines[j].split()
                        testMap[testNameKey]["stats"]["avg_cpl"] = cpl[1][:-1]
                        testMap[testNameKey]["stats"]["95%_cpl"] = cpl[-1]
                    else:
                        statLineArr = loadTestLines[j].split()
                        testMap[testNameKey]["stats"][statLineArr[0]
                                                        ] = statLineArr[1]
                    j += 1
                continue
            if "monitors:" in loadTestLines[i]:
                j = i+2
                while "loadTest" not in loadTestLines[j]:
                    monitorData = loadTestLines[j].split()
                    testMap[testNameKey]["monitors"].append(
                        {"host": monitorData[2], "cpu": monitorData[0], "mem": monitorData[1]})
                    j += 1
                continue

        if bp != n:
            startLine = bp
    return testMap

# Input: a string in the format "loadTestx-xxxxxxxx-xxxxxx-xch"
# Returns: a string corresponding to the test type of the header
def get_subtest_type(test_header):
    if "100_oov_dynamic-" in test_header:
        return "dynamic_dlm_100_oovs"
    elif "1000_oov_dynamic-" in test_header:
        return "dynamic_dlm_1000_oovs"
    elif "10000_oov_dynamic-" in test_header:
        return "dynamic_dlm_10000_oovs"
    elif "noDLM-" in test_header:
        return "no_dlm"
    elif "100_oov-" in test_header:
        return "preloaded_dlm_100_oovs"
    elif "1000_oov-" in test_header:
        return "preloaded_dlm_1000_oovs"
    elif "10000_oov-" in test_header:
        return "preloaded_dlm_10000_oovs"
    else:
        return ""


# Input: a single level dictionary
# Returns: a string separating the dictionary elements by newline characters
def dict_to_str(data_dict):
    res = ""
    for key in data_dict:
        res += f"{key}: {data_dict[key]}\n"
    return res

def str_to_dict(dict_str):
    res = {}
    newlines_removed = dict_str.split("\n")
    for keyval in newlines_removed:
        tmp = keyval.split(":")
        res[tmp[0]] = tmp[1].strip()
    return res


# Input: the parsed test data from a load test file, and the stats which are
#        not to be discarded during filtering
# Returns: the parsed test data with the stats filtered
def filter_stats_func(parsed_data, checked_stats):
    for test in parsed_data:
        stats_filtered = {}
        for stat in parsed_data[test]["stats"]:
            if stat in checked_stats:
                stats_filtered[stat] = parsed_data[test]["stats"][stat]
        parsed_data[test]["stats"] = stats_filtered
    return parsed_data


# Input: an array of 2 report models (corresponding to load tests) to be compared
# Returns: a dictionary of compared data between 2 reports
def compare_load_advanced(reports, discard_singleton=False, convert_dict=True):
    report_files = [report.file_report.path for report in reports]

    compared_data = ["stats", "monitors", "calls",
                         "recognitions", "success", "kryptons", "errors"]
    res = {}
    for key in compared_data:
        res[key] = {
            "preloaded_dlm_100_oovs": [],
            "preloaded_dlm_1000_oovs": [],
            "preloaded_dlm_10000_oovs": [],
            "no_dlm": [],
            "dynamic_dlm_100_oovs": [],
            "dynamic_dlm_1000_oovs": [],
            "dynamic_dlm_10000_oovs": []
        }

    for report_file in report_files:
        fp = open(report_file)
        parsed_test_data = parse_load_test_txt(fp)
        subtest_seen_map = {
            "preloaded_dlm_100_oovs": False,
            "preloaded_dlm_1000_oovs": False,
            "preloaded_dlm_10000_oovs": False,
            "no_dlm": False,
            "dynamic_dlm_100_oovs": False,
            "dynamic_dlm_1000_oovs": False,
            "dynamic_dlm_10000_oovs": False
        }

        for test_name in parsed_test_data:
            subtest_type = get_subtest_type(test_name)
            # if subtest already seen -> ignore
            if subtest_seen_map[subtest_type] is False:
                for data_type in compared_data:
                    res[data_type][subtest_type].append(parsed_test_data[test_name][data_type])
                subtest_seen_map[subtest_type] = True
    
    
    if discard_singleton:
        for data_type in res:
            for subtest in res[data_type]:
                if len(res[data_type][subtest]) != len(report_files):
                    # clear subarray within dictionary
                    res[data_type][subtest] = []

    if convert_dict:
        #convert dictionaries (stats) on topmost level
        for test_type in res["stats"]:
            stat_strs = []
            for stat in res["stats"][test_type]:
                stat_strs.append(dict_to_str(stat))
            res["stats"][test_type] = stat_strs
        
        for test_type in res["monitors"]:
            monitors_strs = []
            for monitors in res["monitors"][test_type]:
                single_monitor_str = ""
                for monitor in monitors:
                    single_monitor_str += dict_to_str(monitor)
                    single_monitor_str += "\n "
                monitors_strs.append(single_monitor_str)
            res["monitors"][test_type] = monitors_strs

        for test_type in res["errors"]:
            errs = []
            for errArr in res["errors"][test_type]:
                if len(errArr) == 0:
                    errs.append("No Errors")
                else:
                    errJoined = ""
                    for errStr in errArr:
                        errJoined += f"{errStr}\n"
                    errs.append(errJoined)
            res["errors"][test_type] = errs
    res["accuracy"] = [report.accuracy for report in reports]
                    
    return res