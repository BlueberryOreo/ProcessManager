#include <iostream>
#include <fstream>
#include <unistd.h>
#include <limits.h>
#include <vector>
#include <iomanip>
#include <ctime>
#include <sstream>
using namespace std;

const char *QUEUEPATH = "/abspath/to/the/project/process_queue.que";

int main(int argc, char *args[]) {

    char cwd[PATH_MAX];
    if(getcwd(cwd, sizeof(cwd)) == nullptr){
        perror("getcwd() error");
        return 1;
    }

    ifstream ifile(QUEUEPATH);
    string line;
    int last_id = -1;
    if(ifile.is_open()){
        while(getline(ifile, line)){
            last_id = stoi(line.substr(0, line.find(" ")));
        }
        ifile.close();
    }else{
        cout << "Failed to open file." << endl;
        return 1;
    }

    ofstream ofile(QUEUEPATH, ios::app);
    string script_path = args[1];
    vector<string> args_vec;
    for(int i = 2; i < argc; i++){
        args_vec.push_back(args[i]);
    }

    string cwd_str = cwd;

    if (script_path[0] == '/') {
        // cout << "The script path is an absolute path." << endl;
    } else {
        // cout << "The script path is not an absolute path." << endl;
        if(script_path[0] == '.'){
            script_path = script_path.substr(2);
        }
        script_path = cwd_str + "/" + script_path;
    }

    time_t now = time(0);
    stringstream time_str; 
    time_str << put_time(localtime(&now), "%Y-%m-%d_%H:%M:%S");
    if(ofile.is_open()){
        ofile << right << setw(3) << setfill('0') << last_id + 1 << '\t';
        ofile << left << setw(25) << setfill(' ') << time_str.str();
        ofile << left << setw(60) << setfill(' ') << cwd_str;
        ofile << left << setw(60) << script_path;
        for(auto &arg : args_vec){
            ofile << " " << arg;
        }
        ofile << "\t" << "waiting" << endl;
        ofile.close();
    }
    cout << "Added script " << script_path << " to queue." << endl;

    return 0;
}