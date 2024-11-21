#include "utils.h"

int main(int argc, char *args[]) {

    // int target_id = stoi(args[1]);
    set<int> target_ids = {};
    for(int i = 1; i < argc; i++){
        target_ids.insert(stoi(args[i]));
    }
    ifstream ifile(QUEUEPATH);
    string line;
    vector<Script> scripts;
    vector<int> ids;

    // TODO: Implement the functionality to remove a running script from the queue.
    if(ifile.is_open()){
        while(getline(ifile, line)){
            Script tmp(line);
            if(target_ids.find(tmp.id) != target_ids.end()){
                target_ids.erase(tmp.id);
                ids.push_back(tmp.id);
                if(tmp.status == "running"){
                    tmp.status = "terminating";
                }else{
                    tmp.status = "0";
                }
            }
            if(tmp.status != "0"){
                scripts.push_back(tmp);
            }
        }
    }else{
        cout << "Failed to open file." << endl;
        return 1;
    }

    if(target_ids.size() > 0){
        cout << "Cannot find script(s) with id ";
        for(auto id : target_ids){
            cout << id << " ";
        }
        cout << "in queue." << endl;
        return 0;
    }

    ofstream ofile(QUEUEPATH);
    if(ofile.is_open()){
        for(auto script : scripts){
            ofile << script << endl;
        }
        ofile.close();
    }else{
        cout << "Failed to open file." << endl;
        return 1;
    }

    cout << "Removed script(s) with id ";
    for(auto id : ids){
        cout << id << " ";
    }
    cout << "from queue." << endl;

    return 0;
}