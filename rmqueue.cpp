#include <iostream>
#include <fstream>
#include <vector>
using namespace std;

const char *QUEUEPATH = "/path/to/the/project/process_queue.que";

int main(int argc, char *args[]) {

    int target_id = stoi(args[1]);
    ifstream ifile(QUEUEPATH);
    string line;
    vector<string> scripts;
    bool removed = false;

    // TODO: Implement the functionality to remove a running script from the queue.
    if(ifile.is_open()){
        while(getline(ifile, line)){
            int id = stoi(line.substr(0, 3));
            if(id != target_id){
                scripts.push_back(line);
            }else{
                removed = true;
            }
        }
    }else{
        cout << "Failed to open file." << endl;
        return 1;
    }

    if(!removed){
        cout << "Cannot find script with id " << target_id << " in queue." << endl;
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

    cout << "Removed script with id " << target_id << " from queue." << endl;

    return 0;
}