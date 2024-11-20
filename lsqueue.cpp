#include <iostream>
#include <fstream>
#include <iomanip>
using namespace std;

const char *QUEUEPATH = "/abspath/to/the/project/process_queue.que";

int main(){

    ifstream file(QUEUEPATH);
    string line;
    cout << left << setw(3) << "id" << '\t'
         << left << setw(25) << "submit_time"
         << setw(60) << "cwd"
         << setw(60) << "script" << "\t" << "status" << endl;
    if(file.is_open()){
        int line_num = 0;
        while(getline(file, line)){
            cout << line << endl;
            line_num ++;
        }
        file.close();
        cout << "Total process: " << line_num << endl;
    }else{
        cout << "Failed to open file." << endl;
    }

    return 0;
}