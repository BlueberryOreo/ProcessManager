#include <iostream>
#include <fstream>
#include <iomanip>
using namespace std;

const char *QUEUEPATH = "/path/to/the/project/process_queue.que";

int main(){

    ifstream file(QUEUEPATH);
    string line;
    cout << left << setw(3) << "id" << '\t'
         << left << setw(25) << "submit_time"
         << setw(30) << "cwd"
         << setw(50) << "script" << "\t" << "status" << endl;
    if(file.is_open()){
        while(getline(file, line)){
            cout << line << endl;
        }
        file.close();
    }else{
        cout << "Failed to open file." << endl;
    }

    return 0;
}