#include <iostream>
#include <fstream>
#include <iomanip>
using namespace std;

const char *QUEUEPATH = "/data/sjy/process_man/process_queue.que";

int main(){

    ifstream file(QUEUEPATH);
    string line;
    cout << left << setw(3) << "id" << '\t'
         << left << setw(25) << "submit_time"
         << setw(60) << "cwd"
         << setw(60) << "script" << "\t" << "status" << endl;
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