import re
import os
import fnmatch
import string, random
from shutil import copy2


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def getParameterINI(PathToSearch):
    print(PathToSearch)

    PathToSearch = PathToSearch.replace("\\", "/")

    # remove mt-nas02.nuance.com from link
    end_path = re.search(r"EMEA.*$", PathToSearch)

    # add mounted drive to link
    path_folder = "/media/datapack/DP_Test_Results/" + str(end_path.group())
    print(path_folder)

    # find Parameter*.used in the path
    for root, dirnames, filenames in os.walk(path_folder):
        for filename in fnmatch.filter(filenames, "Parameter*.used"):
            param_file_on_media = os.path.join(root, filename)

    print(param_file_on_media)
    filename = id_generator() + ".txt"
    dst = "/usr/local/Reporting/upload/parameters_ini/" + filename
    copy2(param_file_on_media, dst)
    url = "/reports/media/parameters_ini/" + filename
    print(url)
    return url


def get_upload_to(instance, filename) -> str:
    return f"Nuance/{instance.environment}/core/languages/{instance.datapack.topic}/{instance.datapack.language}/{instance.datapack.version}/{instance.testing_type.name}/{filename}"
