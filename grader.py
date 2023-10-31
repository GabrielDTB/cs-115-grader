from shutil import rmtree
from shutil import copy
from os import mkdir
from os import scandir
from os.path import basename
from os import chdir
import subprocess
from zipfile import ZipFile
import sys

TIMEOUT = 60

working_directory = "autograder"
submissions_directory = working_directory+"/submissions"
testing_directory = working_directory+"/testing"

def init_directories():
    def make_directories():
        mkdir(working_directory)
        mkdir(submissions_directory)
        mkdir(testing_directory)
        
    try:
        make_directories()
    except FileExistsError:
        rmtree(working_directory)
        make_directories()


def test_submission():
    pass
        

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Provide a istarting and terminating string with the file call")
        exit()
    starter = sys.argv[1]
    terminator = sys.argv[2]
    init_directories()
    for filename in scandir("required"):
        if not filename.is_file():
            continue
        filename = basename(filename)
        copy("required/" + filename, testing_directory + "/" + filename)
    with ZipFile("submissions.zip") as submissions:
        submissions.extractall(path=submissions_directory)
        
    for prospective in scandir("."):
        if "test" in basename(prospective) and prospective.is_file():
            copy(prospective, testing_directory+"/test.py")
    target_name = None
    with open(testing_directory+"/test.py") as test:
        for line in test:
            if "from" in line and "import" in line:
                line = line.split("from")[1]
                line = line.split("import")[0]
                target_name = line.strip()
            if "import" in line and "as" in line:
                line = line.split("import")[1]
                line = line.split("as")[0]
                target_name = line.strip()
            if "import" in line:
                line = line.split("import")[1]
                target_name = line.strip()

    if target_name is None:
        print("target name not found")
        exit()

    results = {}
    for filename in sorted(scandir(submissions_directory), key=lambda a: a.name):
        if not filename.is_file():
            continue
        filename = basename(filename)
        if filename <= starter or filename >= terminator:
            continue
        pledge = "Missing?"
        # TODO Scan file for name (is this possible?)
        copy(submissions_directory + "/" + filename, testing_directory + "/" + target_name + ".py")

        try:
            with open(testing_directory + "/" + target_name + ".py") as submission:
                for line in submission:
                    if line.casefold().find("I pledge my honor that I have abided by the Stevens Honor System".casefold()):
                        pledge = "Good"
                        break
                    
                if pledge == "Missing?":
                    for line in submission:
                        if all([x in line for x in ["pledge, honor", "abid", "steven", "honor"]]):
                            pledge = "Almost"
                            break

                if pledge == "Missing?":
                    for line in submission:
                        if any([x in line for x in ["pledge, honor", "abid", "steven", "honor"]]):
                            peldge = "Weird"
                            break
        except:
            pledge = "error"

        results[filename] = {}
        results[filename]["pledge"] = pledge
        try:
            output = subprocess.run("python test.py", shell=True, cwd=testing_directory, capture_output=True, timeout=TIMEOUT).stderr.decode("utf-8")
            results[filename]["output"] = output
        except Exception as e:
            results[filename]["output"] = e

    with open("results.txt", 'w') as file:
        for key, value in sorted(results.items()):
            filename = key
            pledge = value["pledge"]
            output = value["output"]
            file.write("{}\nPledge: {}\n{}\n{line}\n".format(filename, pledge, output, line='#'*80))
    rmtree(working_directory)
