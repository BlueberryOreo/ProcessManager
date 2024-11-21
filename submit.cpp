#include "utils.h"

int main(int argc, char *args[]) {

    char cwd[PATH_MAX];
    if(getcwd(cwd, sizeof(cwd)) == nullptr){
        perror("getcwd() error");
        return 1;
    }

    string QUEUEPATH = PROJECTPATH + (PROJECTPATH.back() == '/' ? "" : "/") + "process_queue.que";

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
    stringstream time_str, script_str; 
    time_str << put_time(localtime(&now), "%Y-%m-%d_%H:%M:%S");
    script_str << script_path;
    for(auto &arg : args_vec){
        script_str << " " << arg;
    }

    Script script{
        last_id + 1,
        time_str.str(),
        cwd_str,
        script_str.str(),
        "waiting"
    };

    if(ofile.is_open()){
        ofile << script << endl;
        ofile.close();
    }
    cout << "Added script " << script_path << " to queue." << endl;

    return 0;
}